#!/usr/bin/env python3
"""路線2、第三／四目的地及選項列的正常GUI、同狀態與回退驗證。"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_tutorial_cargo import TRADE_FIELDS_BINARY, SEA_CITY_BINARY, ISSUE56_BINARY, source_audit, current_source_binary

TITLE = [127, 4, 194, 11]
GRID = [[10, 68, 83, 76], [9, 88, 83, 96], [9, 108, 46, 115], [9, 128, 83, 136]]
ONE = [76, 102, 254, 114]
CHOICES = [76, 90, 254, 126]


def changes_allowed():
    allowed = {name: [ONE] for name in ['trade-create-1', 'trade-create-2',
                                       'trade-second-destination-1', 'trade-second-destination-2']}
    allowed.update({name: [TITLE] + GRID for name in [
        'trade-editor-2', 'trade-third-cancel', 'trade-third-london',
        'trade-fourth-jamestown', 'trade-fourth-deleted', 'trade-fourth-restored']})
    allowed.update({name: [TITLE] + GRID + [CHOICES] for name in [
        'trade-third-choice', 'trade-third-reopen', 'trade-fourth-choice',
        'trade-delete-choice', 'trade-delete-hover', 'trade-fourth-reopen']})
    return allowed


def retained(reports, prefix, accepted_name, gui_name, count):
    current, accepted, gui = reports / prefix, reports / accepted_name, reports / gui_name
    assert sha(Path(read(current / 'command.json')[0])) == TRADE_FIELDS_BINARY
    assert read(current / 'run.json')['state'] == read(accepted / 'run.json')['state']
    for name in ['run.memory', 'raw.wav']:
        assert (current / name).read_bytes() == (accepted / name).read_bytes(), (prefix, name)
    assert {p.name: sha(p) for p in (current / 'save').glob('*.SAV')} == {
        p.name: sha(p) for p in (accepted / 'save').glob('*.SAV')}
    shots = [line.split() for line in (gui / 'gui.shots').read_text().splitlines()]
    assert len(shots) == count
    for _, step in shots:
        for ext in ['idx', 'pal']:
            name = 'run.cp-' + step + '.' + ext
            assert (current / name).read_bytes() == (accepted / name).read_bytes()
        name = 'run.cp-' + step + '.png'
        assert pixels(current / name) == pixels(accepted / name)
    return {'samples': count, 'unchanged': True}


def check(game, reports, repo):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    audit = source_audit(repo, reports)
    assert audit.name in ['trade-fields-connection-audit', 'issue56-source-connection-audit']
    if audit.name == 'issue56-source-connection-audit':
        current = reports / 'issue56-trade-regression'
        accepted = reports / 'trade-fields-formal-zh'
        assert sha(Path(read(current / 'command.json')[0])) == ISSUE56_BINARY
        assert read(current / 'run.json')['state'] == read(accepted / 'run.json')['state']
        for name in ['run.memory', 'raw.wav']:
            assert (current / name).read_bytes() == (accepted / name).read_bytes()
        assert {p.name: sha(p) for p in (current / 'save').glob('*.SAV')} == {
            p.name: sha(p) for p in (accepted / 'save').glob('*.SAV')}
        for line in (reports / 'trade-fields-formal-gui/gui.shots').read_text().splitlines():
            _, step = line.split()
            for ext in ['idx', 'pal', 'png']:
                name = 'run.cp-' + step + '.' + ext
                if ext == 'png':
                    assert pixels(current / name) == pixels(accepted / name)
                else:
                    assert (current / name).read_bytes() == (accepted / name).read_bytes()
    build = reports / 'trade-fields-formal'
    assert sha(build / 'colonization-window') == TRADE_FIELDS_BINARY
    tests = [json.loads(line) for line in (build / 'test-results.jsonl').read_text().splitlines()]
    assert not any(e['Action'] in ['fail', 'skip'] for e in tests)
    assert any(e['Action'] == 'pass' and e.get('Test') == 'TestTradeSecondTitleAndDestinationRoles' for e in tests)
    assert sha(reports / 'trade-fields-candidate-review.json') == '7a7ea64e750bddc3b9d498b5263ac6cedb83b3a6a3178b438d92f211b896a327'
    peers = {mode: reports / ('trade-fields-formal-' + mode)
             for mode in ['zh', 'control', 'missing', 'baseline']}
    gui = reports / 'trade-fields-formal-gui'
    for mode, directory in peers.items():
        expected_binary = SEA_CITY_BINARY if mode == 'baseline' else TRADE_FIELDS_BINARY
        assert sha(Path(read(directory / 'command.json')[0])) == expected_binary
    assert sha(Path(read(gui / 'session.json')['binary'])) == TRADE_FIELDS_BINARY
    data = {mode: read(directory / 'run.json') for mode, directory in peers.items()}
    gui_data = read(gui / 'gui.json')
    assert len({json.dumps(j['state'], sort_keys=True) for j in [gui_data] + list(data.values())}) == 1
    for filename in ['run.memory', 'raw.wav']:
        paths = [p / filename for p in peers.values()] + [gui / ('gui.memory' if filename == 'run.memory' else filename)]
        assert len({sha(path) for path in paths}) == 1, filename
    assert len({json.dumps(j['opened']) for j in data.values()}) == 1
    assert len({json.dumps(j['input_hashes'], sort_keys=True) for j in data.values()}) == 1
    saves = [{p.name: sha(p) for p in (directory / 'save').glob('*.SAV')}
             for directory in list(peers.values()) + [gui]]
    assert all(values == saves[0] for values in saves) and 'COLONY01.SAV' in saves[0]
    points = {mode: {p['step']: p for p in j['checkpoints']} for mode, j in data.items()}
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines())
                if r.get('aligned')}
    allowed = changes_allowed()
    changes = []
    for line in (gui / 'gui.shots').read_text().splitlines():
        name, step = line.split()
        step = int(step)
        stem = 'run.cp-' + str(step)
        assert pixels(gui / ('gui.' + name + '.png')) == pixels(peers['zh'] / (stem + '.png')), (name, 'GUI')
        assert captures[name]['frame_step'] == step
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png')), (name, 'fallback')
        for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({p[step][key] for p in points.values()}) == 1, (name, key)
        for ext in ['idx', 'pal']:
            assert len({sha(p / (stem + '.' + ext)) for p in peers.values()}) == 1
        new = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        old = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(new, old)
        assert bool(diff.getbbox()) == (name in allowed), (name, diff.getbbox())
        mask = Image.new('L', new.size)
        drawing = ImageDraw.Draw(mask)
        for x0, y0, x1, y1 in allowed.get(name, []):
            drawing.rectangle((x0 * 4, y0 * 4, x1 * 4 - 1, y1 * 4 - 1), fill=255)
        assert ImageChops.multiply(diff, ImageChops.invert(mask).convert('RGB')).getbbox() is None, (name, 'outside-safe')
        changes.append({'name': name, 'bbox': diff.getbbox(), 'safe': allowed.get(name, [])})
    assert len(changes) == 34
    events = [e for e in data['zh']['events'] if e.get('stage') == 'source']
    fields = []
    for shown, field, size, safe in [
        ('EDIT TRADE ROUTE 2', 'STRING:template:route-editor-title', 22, TITLE),
        ('3.  London', 'STRING:route-grid-colony', 22, GRID[2]),
        ('4.  Jamestown', 'STRING:route-grid-colony', 22, GRID[3]),
        ('Jamestown', 'STRING:voyage-ports', 30, ONE),
        ('London (England) Jamestown (Delete Destination)', 'STRING:voyage-ports+list', 30, CHOICES),
    ]:
        found = [e for e in events if e.get('shown') == shown and e['candidate_id'] == field
                 and e['font_px'] == size and e['safe'] == safe]
        assert found, shown
        fields.append(found[0])
    regressions = [retained(reports, 'trade-fields-tutorial-regression', 'sea-city-tutorial-regression',
                            'tutorial6-current-formal-gui', 13),
                   retained(reports, 'trade-fields-build-regression', 'sea-city-build-regression',
                            'build-transaction-formal-gui', 31)]
    return {'result': 'PASS', 'status': 'PASS_TRADE_FIELDS_FORMAL', 'binary_sha256': TRADE_FIELDS_BINARY,
            'current_binary_sha256': current_source_binary(audit),
            'samples': len(changes), 'changed': sum(bool(r['bbox']) for r in changes), 'changes': changes,
            'verified_fields': fields, 'inputs_sha256': sha(gui / 'gui.inputs.json'),
            'final_step': gui_data['state']['steps'], 'final_memory_sha256': gui_data['state']['memory_sha256'],
            'save_sha256': saves[0], 'retained': regressions,
            'limitations': ['正常範圍為路線1／2、第三London與第四Jamestown；未推定最大路線數或自動跑商規則。',
                           '346組城市名只驗容量，不算正常命中；此檢查只驗列明的貿易欄位。']}


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
