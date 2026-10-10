#!/usr/bin/env python3
"""正常返航的教學7／15城市變數、原版同狀態與提示撤銷驗收。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_tutorial_cargo import without_approved_city_extension

BINARY = 'c30275a86d256dbb9cc1ccb424ebb50096e5a751b64af9ad99522608f21c720d'
BASELINE = '6ea4f982d2467421f42eeb00b2ea05060068bfe29d296e901187694fa7e0d394'
FIELDS = {
    'GAME.TXT:@TUTORIAL7': ([50, 32, 269, 166], 175056),
    'GAME.TXT:@TUTORIAL15': ([50, 103, 269, 157], 175218),
}
CHANGES = {'return-go-wait': 'GAME.TXT:@TUTORIAL15',
           'join-first-action': 'GAME.TXT:@TUTORIAL7'}


def check(game, reports):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    gui = reports / 'tutorial-city-formal-gui'
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    build = reports / 'tutorial-city-formal'
    for filename, digest in {
        'tutorial_city_test.go': '9bc3e38f186cb7ef86d048d034129de2c25ff38e24d6497431e158f4a6c9a8a7',
        'real_catalog_test.go': '35dd5b9188f753becb39d19875dc41e6f9e44ce0007898da31ccadb53244bc87',
        'tutorial-city-values.json': '46b16ae413ca121643c3ab8a5f160259eced87133c1818cbb80f2cf9dd5b853e',
    }.items():
        assert sha(build / filename) == digest, filename
    repo = Path(__file__).resolve().parents[1]
    frozen = (build / 'dialog.go').read_text()
    current = (repo / 'tools/dialog_overlay.go').read_text()
    # 本列保存兩則城市變數的已接受驗收。後續建造清單事務另有新正常GUI，
    # 不因同檔其他函式變更重開本列；模板載入、編譯與變數匹配仍須逐字相同。
    for signature in ['func (cat *dialogCatalog) addCorpus(', 'func makeDialogTemplate(',
                      'func (c *dialogCatalog) matchIn(']:
        def function(source):
            start = source.index(signature)
            end = source.find('\nfunc ', start + len(signature))
            return source[start:end if end >= 0 else len(source)]
        present = function(current)
        if signature == 'func (c *dialogCatalog) matchIn(':
            present = without_approved_city_extension(present)
            # 後續教學6只新增獨立的STRING1城市分支；7／12／15及其他匹配
            # 必須逐字保持原驗收。教學6由自己的正常GUI與21則變數審查驗證。
            addition = '''\t\t} else if hit.id == "GAME.TXT:@TUTORIAL6" && name == "%STRING1" {
\t\t\t// 規格035 READY：貨物提示中的名稱只沿既有城市顯示回呼。
\t\t\tif c.colonyValue == nil {
\t\t\t\treturn hit, "", "unverified-colony-name"
\t\t\t}
\t\t\tif strings.ContainsAny(v, "{}") {
\t\t\t\treturn hit, "", "unrenderable-variable"
\t\t\t}
\t\t\tv = c.colonyValue(v)
'''
            if addition in present:
                assert present.count(addition) == 1
                present = present.replace(addition, '')
        assert function(frozen) == present, signature
    tests = [json.loads(line) for line in (build / 'test-results.jsonl').read_text().splitlines()]
    assert not any(e['Action'] in ['fail', 'skip'] for e in tests)
    assert any(e['Action'] == 'pass' and 'Test' not in e for e in tests)
    source_tests = [json.loads(line) for line in (build / 'source-test-results.jsonl').read_text().splitlines()]
    assert not any(e['Action'] in ['fail', 'skip'] for e in source_tests)
    assert any(e['Action'] == 'pass' and e.get('Test') == 'TestActualTutorialCityVariables' for e in source_tests)
    values = read(build / 'tutorial-city-values.json')
    assert {(v['id'], v['name']) for v in values} == {
        (key, name) for key in ['GAME.TXT:@TUTORIAL7', 'GAME.TXT:@TUTORIAL12', 'GAME.TXT:@TUTORIAL15']
        for name in ['Jamestown', 'My Colony']}
    for value in values:
        expected = '詹姆斯敦（Jamestown）' if value['name'] == 'Jamestown' else 'My Colony'
        assert expected in value['zh'] and '錯誤術語' not in value['zh']
        if value['id'] == 'GAME.TXT:@TUTORIAL15':
            assert value['zh'].count(expected) == 2
    original = read(gui / 'gui.json')
    peers = {m: reports / ('tutorial-city-formal-' + m)
             for m in ['zh', 'control', 'missing', 'baseline']}
    data = {m: read(p / 'run.json') for m, p in peers.items()}
    for mode, path in peers.items():
        command = read(path / 'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(gui / 'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
        assert data[mode]['state'] == original['state'], mode
        assert data[mode]['input_hashes'] == original['input_hashes'], mode
        assert (path / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes(), mode
        assert (path / 'raw.wav').read_bytes() == (gui / 'raw.wav').read_bytes(), mode
        assert {f.name: sha(f) for f in (path / 'save').glob('*.SAV')} == {
            f.name: sha(f) for f in (gui / 'save').glob('*.SAV')}, mode
    sources = {}
    for key, (safe, address) in FIELDS.items():
        found = [e for e in data['zh']['events']
                 if e.get('candidate_id') == key and e.get('stage') == 'source']
        assert len(found) == 1, (key, found)
        event = found[0]
        assert event['safe'] == safe and event['font_px'] == 30
        assert event['source_linear'] == address and event['entry_ip'] == '0D21:00C6'
        assert 'Jamestown' in event['shown']
        assert any(e.get('candidate_id') == key and e.get('stage') == 'active'
                   for e in data['zh']['events'])
        assert any(e.get('candidate_id') == key and e.get('stage') == 'expired'
                   for e in data['zh']['events'])
        sources[key] = event
    shots = [line.split() for line in (gui / 'gui.shots').read_text().splitlines()]
    assert len(shots) == 17
    captures = {e['name']: e for e in map(json.loads,
                (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if e.get('aligned')}
    checkpoints = {mode: {c['label']: c for c in report['checkpoints']}
                   for mode, report in data.items()}
    changes = []
    for name, step in shots:
        stem = 'run.cp-' + step
        actual = pixels(gui / ('gui.' + name + '.png'))
        assert actual == pixels(peers['zh'] / (stem + '.png')), name
        capture = captures[name]
        assert capture['frame_step'] == int(step)
        assert hashlib.sha256(actual).hexdigest() == capture['capture_rgba_sha256']
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({checkpoints[m]['cp-' + step][key] for m in peers}) == 1, (name, key)
        for ext in ['idx', 'pal']:
            assert len({(p / (stem + '.' + ext)).read_bytes() for p in peers.values()}) == 1
        new = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        old = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(new, old)
        if name in CHANGES:
            area = tuple(v * 4 for v in FIELDS[CHANGES[name]][0])
            assert diff.getbbox(), name
            outside = diff.copy()
            outside.paste((0, 0, 0), area)
            assert not outside.getbbox(), (name, diff.getbbox())
            changes.append({'name': name, 'safe': FIELDS[CHANGES[name]][0],
                            'difference': diff.getbbox()})
        else:
            assert not diff.getbbox(), (name, diff.getbbox())
    return {'result': 'PASS', 'status': 'PASS_TUTORIAL_CITY_FORMAL',
            'samples': len(shots), 'changes': changes, 'sources': sources,
            'binary_sha256': BINARY, 'inputs_sha256': sha(gui / 'gui.inputs.json'),
            'original_state': original['state'],
            'final_step': original['state']['steps'],
            'final_memory_sha256': original['state']['memory_sha256'],
            'verified_fields': [{'candidate_id': key, 'shown': value['shown'],
                                 'safe': value['safe'], 'font_px': value['font_px']}
                                for key, value in sources.items()],
            'scope': '教學7／15正常返航城市變數與關閉回退；不代表教學6或完整#61完成。'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(args.game, args.reports)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
