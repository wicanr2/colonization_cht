#!/usr/bin/env python3
"""教學6貨物／城市變數：目前來源、正常GUI與原文回退。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY = '24b7816beef942ae685fa367204ddae88454aa65073be5c38346016cafa24a6d'
COMPACT_BINARY = 'cc0ec453a4f7490ea0e095fc4b9e6b0e0d84f370c350c8e812d5520e9cb6e3f7'
SEA_CITY_BINARY = '8e22e0743f26677f16695fafc7dabf3c06676e999368d2c7990637d2df164bac'
TRADE_FIELDS_BINARY = '0484e99b5a03456b9910eca55fb27c384857b162c25b9ba364d68d3f63c93a27'
ISSUE56_BINARY = '73d863baa358dce354bf2d13b232735c2e9109a48d1b1c15a61d88df031e4ee2'
BASELINE = '6c3f916e3ab102bb78187fa4052de28722112bd3a4b200ad53ea41c147131a12'
SOURCE_PAIRS = [('adapter.go', 'live_menu.go'), ('dialog.go', 'dialog_overlay.go'),
                ('strings.go', 'string_overlay.go')]
VARIABLES_SHA = '37b1c775a1c1fc375c8c99edcc094cdc247845ff51afcbc65adb1e4ed553b1c9'
CITY_VALUES_SHA = 'fedeb07bf949bfc740967d5fd5e446045652da72c0c672d9a686e221783007ab'
FIELD = 'GAME.TXT:@TUTORIAL6'
SAFE = [52, 113, 271, 157]


def without_approved_city_extension(source):
    start = source.find('\t\t} else if ((hit.id == "GAME.TXT:0x00001447"')
    if start < 0:
        return source
    end = source.index('\t\t} else if hit.id == "GAME.TXT:@TUTORIAL6"', start)
    addition = source[start:end]
    assert hashlib.sha256(addition.encode()).hexdigest() in {
        '2b525423827d968dce6600bf405adccbf8e7181b94f398eb4c4c220767597f70',
        '0308e0cba9e4a0a0fe16b762c18b03331783503898f16708ba752a47f89cb17b'}
    return source[:start] + source[end:]


def current_source_binary(audit):
    return {'unit-caption-city-connection-audit': BINARY,
            'orders-compact-connection-audit': COMPACT_BINARY,
            'sea-city-variable-connection-audit': SEA_CITY_BINARY,
            'trade-fields-connection-audit': TRADE_FIELDS_BINARY,
            'issue56-source-connection-audit': ISSUE56_BINARY}[audit.name]


def source_audit(repo, reports):
    frozen = reports / 'unit-caption-city-formal'
    assert sha(frozen / 'colonization-window') == BINARY
    generations = [(reports / 'unit-caption-city-connection-audit', frozen, BINARY),
                   (reports / 'orders-compact-connection-audit', reports / 'orders-compact-formal', COMPACT_BINARY),
                   (reports / 'sea-city-variable-connection-audit', reports / 'sea-city-variable-formal', SEA_CITY_BINARY),
                   (reports / 'trade-fields-connection-audit', reports / 'trade-fields-formal', TRADE_FIELDS_BINARY),
                   (reports / 'issue56-source-connection-audit', reports / 'issue56-source-connection-audit', ISSUE56_BINARY)]
    matching = [(audit, build, digest) for audit, build, digest in generations
                if all((audit / local).is_file() and (build / local).is_file()
                       and (audit / local).read_bytes() == (build / local).read_bytes()
                       and (build / local).read_bytes() == (repo / 'tools' / source).read_bytes()
                       for local, source in SOURCE_PAIRS)]
    assert len(matching) == 1, '缺目前正式來源的完整接線審查'
    audit, build, digest = matching[0]
    assert sha(build / 'colonization-window') == digest
    for local, source in SOURCE_PAIRS:
        assert (build / local).read_bytes() == (repo / 'tools' / source).read_bytes(), source
        assert (audit / local).read_bytes() == (build / local).read_bytes(), local
    # 保存既有教學及肖像欄位的驗收；新MENU前綴不能改變其來源、變數或排版。
    def function(source, signature):
        start = source.index(signature)
        end = source.find('\nfunc ', start + len(signature))
        return source[start:end if end >= 0 else len(source)].strip()
    old = (frozen / 'dialog.go').read_text()
    present = (build / 'dialog.go').read_text()
    for signature in ['func makeDialogTemplate(', 'func (c *dialogCatalog) addDraft(',
                      'func (cat *dialogCatalog) addCorpus(', 'func (c *dialogCatalog) matchIn(',
                      'func (d *dialogRuntime) unitCaptionChoices(',
                      'func (c *dialogCatalog) dialogMasks(', 'func (c *dialogCatalog) lineLayerMasks(']:
        actual = function(present, signature)
        if signature == 'func (c *dialogCatalog) matchIn(':
            actual = without_approved_city_extension(actual)
        assert function(old, signature) == actual, signature
    if digest in [COMPACT_BINARY, SEA_CITY_BINARY, TRADE_FIELDS_BINARY, ISSUE56_BINARY]:
        current = reports / ('issue56-tutorial-regression' if digest == ISSUE56_BINARY
                             else 'trade-fields-tutorial-regression' if digest == TRADE_FIELDS_BINARY
                             else 'sea-city-tutorial-regression' if digest == SEA_CITY_BINARY
                             else 'orders-compact-tutorial-regression')
        accepted = reports / 'tutorial6-current-formal-zh'
        assert sha(Path(read(current / 'command.json')[0])) == digest
        assert read(current / 'run.json')['state'] == read(accepted / 'run.json')['state']
        for name in ['run.memory', 'raw.wav']:
            assert (current / name).read_bytes() == (accepted / name).read_bytes(), name
        assert {p.name: sha(p) for p in (current / 'save').glob('*.SAV')} == {
            p.name: sha(p) for p in (accepted / 'save').glob('*.SAV')}
        shots = (reports / 'tutorial6-current-formal-gui/gui.shots').read_text().splitlines()
        assert len(shots) == 13
        for line in shots:
            _, step = line.split()
            for ext in ['idx', 'pal']:
                name = 'run.cp-' + step + '.' + ext
                assert (current / name).read_bytes() == (accepted / name).read_bytes()
            name = 'run.cp-' + step + '.png'
            assert pixels(current / name) == pixels(accepted / name)
    for filename, digest in {
        'tutorial-all-variables.json': VARIABLES_SHA,
        'tutorial6-city-values.json': CITY_VALUES_SHA,
        'tutorial_all_variables_test.go': 'a2baba5e9cdf7e2b2254e0c6104e7cdd8b0dd4675a5681fa6efcc41b6603c540',
        'tutorial6_test.go': 'e646dc702f6c7789a0fe7745b4a3a23a93dc471286e67cc977fc9b695a7ab996',
        'real_catalog_test.go': '35dd5b9188f753becb39d19875dc41e6f9e44ce0007898da31ccadb53244bc87',
        'tutorial6_layout_test.go': '1f0644a8c33d1e961f1aa091b0d814bf791d76009df20d266beb812211913081',
        'tutorial6-layout.json': '221942aedae3a207c4f4ef6a9570b8a77dc2644a54b99907b513719fde353c74',
    }.items():
        assert sha(audit / filename) == digest, filename
    required = {'TestTutorialAndWoodcutConnectionAudit', 'TestSixStartupSectionsConnection',
                'TestAllTutorialVariableBindings', 'TestTutorial6CitySource',
                'TestCargoTutorialCitySlotIsolation', 'TestUnitCaptionRoleAndGeometryGuards'}
    for directory, filename in [(build, 'test-results.jsonl'), (audit, 'source-test-results.jsonl')]:
        tests = [json.loads(s) for s in (directory / filename).read_text().splitlines()]
        assert not any(e['Action'] in ['fail', 'skip'] for e in tests), filename
        assert any(e['Action'] == 'pass' and 'Test' not in e for e in tests), filename
        if directory == audit:
            assert required <= {e.get('Test') for e in tests if e['Action'] == 'pass'}
    assert not (build / 'vet.log').read_text().strip()
    layout_tests = [json.loads(s) for s in (audit / 'cargo-layout-test-results.jsonl').read_text().splitlines()]
    assert not any(e['Action'] in ['fail', 'skip'] for e in layout_tests)
    assert any(e['Action'] == 'pass' and e.get('Test') == 'TestActualTutorialCargoLayout' for e in layout_tests)
    values = read(audit / 'tutorial-all-variables.json')
    loaded = read(audit / 'start-connection-audit.json')['tutorial_ids']
    assert len(values) == 21 and {v['id'] for v in values} == set(loaded)
    assert all(v['zh'] and '%STRING' not in v['zh'] for v in values)
    cities = read(audit / 'tutorial6-city-values.json')
    assert {v['city'] for v in cities} == {'Jamestown', 'My Colony'}
    for value in cities:
        name = '詹姆斯敦（Jamestown）' if value['city'] == 'Jamestown' else 'My Colony'
        assert value['zh'].count(name) == 2 and '錯誤術語' not in value['zh']
        assert '毛皮' in value['zh'] and '倫敦' in value['zh']
    return audit


def sample_set(reports, gui_name, prefix, binary, baseline, expected, current_gui=True, gui_binary=None):
    """沿實際frame_step核對四側；expected指定唯一允許改變的矩形。"""
    gui = reports / gui_name
    original = read(gui / 'gui.json')
    peers = {m: reports / (prefix + '-' + m) for m in ['zh', 'control', 'missing', 'baseline']}
    data = {m: read(p / 'run.json') for m, p in peers.items()}
    assert sha(Path(read(gui / 'session.json')['binary'])) == (gui_binary or (binary if current_gui else baseline))
    for mode, path in peers.items():
        command = read(path / 'command.json')
        assert sha(Path(command[0])) == (baseline if mode == 'baseline' else binary)
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(gui / 'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
        assert data[mode]['state'] == original['state'], (gui_name, mode)
        assert data[mode]['input_hashes'] == original['input_hashes'], (gui_name, mode)
        assert (path / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes()
        assert (path / 'raw.wav').read_bytes() == (gui / 'raw.wav').read_bytes()
        assert {p.name: sha(p) for p in (path / 'save').glob('*.SAV')} == {
            p.name: sha(p) for p in (gui / 'save').glob('*.SAV')}
    shots = [line.split() for line in (gui / 'gui.shots').read_text().splitlines()]
    captures = {e['name']: e for e in map(json.loads,
                (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if e.get('aligned')}
    points = {m: {c['label']: c for c in j['checkpoints']} for m, j in data.items()}
    changes = []
    for name, step in shots:
        stem = 'run.cp-' + step
        image = gui / ('gui.' + name + '.png')
        side = 'zh' if current_gui else 'baseline'
        assert pixels(image) == pixels(peers[side] / (stem + '.png')), (gui_name, name, 'GUI')
        assert captures[name]['frame_step'] == int(step)
        assert hashlib.sha256(pixels(image)).hexdigest() == captures[name]['capture_rgba_sha256']
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({points[m]['cp-' + step][key] for m in peers}) == 1, (name, key)
        for ext in ['idx', 'pal']:
            assert len({(p / (stem + '.' + ext)).read_bytes() for p in peers.values()}) == 1
        new = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        old = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(new, old)
        if name in expected:
            assert diff.getbbox(), name
            outside = diff.copy()
            outside.paste((0, 0, 0), tuple(v * 4 for v in expected[name]))
            assert not outside.getbbox(), (name, diff.getbbox())
            changes.append({'name': name, 'safe': expected[name], 'difference': diff.getbbox()})
        else:
            assert not diff.getbbox(), (name, diff.getbbox())
    assert {c['name'] for c in changes} == set(expected)
    return {'samples': len(shots), 'changes': changes, 'inputs_sha256': sha(gui / 'gui.inputs.json'),
            'final_step': original['state']['steps'],
            'final_memory_sha256': original['state']['memory_sha256']}, data


def check(game, reports, repo):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    audit = source_audit(repo, reports)
    result, data = sample_set(reports, 'tutorial6-current-formal-gui', 'tutorial6-current-formal',
                              BINARY, BASELINE, {'economy-cycle-8': SAFE})
    assert result['samples'] == 13
    sources = [e for e in data['zh']['events'] if e.get('candidate_id') == FIELD and e.get('stage') == 'source']
    assert len(sources) == 1
    event = sources[0]
    assert event['safe'] == SAFE and event['font_px'] == 30
    assert event['source_linear'] == 174958 and event['entry_ip'] == '0D21:00C6'
    assert event['shown'].count('Jamestown') == 2 and '100 Furs' in event['shown'] and 'London' in event['shown']
    assert any(e.get('candidate_id') == FIELD and e.get('stage') == 'active' for e in data['zh']['events'])
    return {'result': 'PASS', 'status': 'PASS_TUTORIAL_CARGO_FORMAL', 'binary_sha256': BINARY,
            'current_binary_sha256': current_source_binary(audit),
            **result, 'verified_fields': [event], 'tutorial_variables_connected': 21,
            'variable_audit_sha256': sha(audit / 'tutorial-all-variables.json'),
            'limitations': ['21則是原始來源逐變數審查，正常本次命中僅教學6。',
                           '不改原版貨物、城市、母港、輸入、規則或存檔。']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if not all((a.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(a.game, a.reports, a.repo)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
