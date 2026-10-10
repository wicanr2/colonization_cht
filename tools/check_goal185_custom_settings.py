#!/usr/bin/env python3
"""自訂新世界三欄：六張正式GUI、四側同狀態及職業回歸。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY = '30464b5293d97a92ecd528f318a5be2eb52169fa7b791505161aafdbc0805a15'
BASELINE = '7236f28bd489acbe80b25116c0aef9640317dc000bc8884d6954e3d705520008'
INPUT = '964f2f5c7fc292abce1d914aae3a0797d1edd431776411fadc5b51a5aa6df14a'
FIELDS = {
    'CUSTOMIZE NEW WORLD': ('STRING:custom-settings-title', 30, [105, 3, 215, 13], 173986),
    'Moderate': ('STRING:custom-settings-moderate', 22, [29, 100, 63, 108], 173888),
    '(Click Here When Finished)': ('STRING:template:paren-term', 22, [115, 189, 206, 196], 173988),
}

def check(game, reports):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest
    gui = reports / 'custom-settings-formal-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    original = read(gui / 'gui.json')
    peers = {m: reports / ('custom-settings-formal-' + m) for m in ['zh', 'control', 'missing', 'baseline']}
    data = {m: read(p / 'run.json') for m, p in peers.items()}
    for mode, p in peers.items():
        assert data[mode]['state'] == original['state']
        assert (p / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes()
        assert (p / 'raw.wav').read_bytes() == (gui / 'raw.wav').read_bytes()
        assert data[mode]['input_hashes'] == original['input_hashes']
        assert {f.name: sha(f) for f in (p / 'save').glob('*.SAV')} == {f.name: sha(f) for f in (gui / 'save').glob('*.SAV')}
        command = read(p / 'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(gui / 'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
    shots = [l.split() for l in (gui / 'gui.shots').read_text().splitlines()]
    assert len(shots) == 6
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {m: {c['label']: c for c in d['checkpoints']} for m, d in data.items()}
    areas = [(420, 12, 860, 52), (116, 400, 252, 432), (460, 756, 824, 784)]
    changes = []
    for name, step in shots:
        stem = 'run.cp-' + step
        actual = pixels(gui / ('gui.' + name + '.png'))
        assert actual == pixels(peers['zh'] / (stem + '.png'))
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({cps[m]['cp-' + step][key] for m in peers}) == 1
        for ext in ['idx', 'pal']:
            assert len({(p / (stem + '.' + ext)).read_bytes() for p in peers.values()}) == 1
        a = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        b = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(a, b)
        outside = diff.copy()
        if name == 'custom-0':
            for area in areas:
                assert diff.crop(area).getbbox(), area
                outside.paste((0, 0, 0), area)
        assert not outside.getbbox() and bool(diff.getbbox()) == (name == 'custom-0'), (name, diff.getbbox())
        if diff.getbbox():
            changes.append({'name': name, 'difference': diff.getbbox()})
    source = [e for e in data['zh']['events'] if e.get('stage') == 'source' and e.get('shown') in FIELDS]
    assert len(source) == 3 and {e['shown'] for e in source} == set(FIELDS)
    for e in source:
        assert (e['candidate_id'], e['font_px'], e['safe'], e['source_linear']) == FIELDS[e['shown']]
        assert e['entry_ip'] == '0D21:00C6'
    fresh = reports / 'custom-settings-profession-regression'
    prior = reports / 'profession-family-formal-zh'
    prior_gui = reports / 'profession-family-formal-gui'
    d = read(fresh / 'run.json')
    assert d['state'] == read(prior / 'run.json')['state'] == read(prior_gui / 'gui.json')['state']
    assert (fresh / 'run.memory').read_bytes() == (prior / 'run.memory').read_bytes()
    assert (fresh / 'raw.wav').read_bytes() == (prior / 'raw.wav').read_bytes()
    assert {f.name: sha(f) for f in (fresh / 'save').glob('*.SAV')} == {f.name: sha(f) for f in (prior / 'save').glob('*.SAV')}
    command = read(fresh / 'command.json')
    assert sha(Path(command[0])) == BINARY
    assert Path(command[command.index('--replay-inputs') + 1]).samefile(prior_gui / 'gui.inputs.json')
    regression = [l.split() for l in (prior_gui / 'gui.shots').read_text().splitlines()]
    assert len(regression) == 14
    for name, step in regression:
        stem = 'run.cp-' + step
        assert pixels(fresh / (stem + '.png')) == pixels(prior / (stem + '.png')) == pixels(prior_gui / ('gui.' + name + '.png'))
        for ext in ['idx', 'pal']:
            assert (fresh / (stem + '.' + ext)).read_bytes() == (prior / (stem + '.' + ext)).read_bytes()
    return {'result': 'PASS', 'status': 'PASS_CUSTOM_SETTINGS_FORMAL', 'samples': len(shots), 'changes': changes, 'source': source, 'regression_samples': len(regression), 'inputs_sha256': INPUT, 'binary_sha256': BINARY, 'original_state': original['state'], 'final_step': original['state']['steps'], 'final_memory_sha256': original['state']['memory_sha256'], 'verified_fields': [{'candidate_id': e['candidate_id'], 'shown': e['shown'], 'safe': e['safe']} for e in source], 'scope': '只驗自訂頁三欄、其餘五頁不變與14張職業回歸；其他自訂設定值未增加正常命中。'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if not all((a.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(a.game, a.reports)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
