#!/usr/bin/env python3
"""完整兩行職業標題分流：正常切換十四張GUI／四側及既有回歸。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY = '7236f28bd489acbe80b25116c0aef9640317dc000bc8884d6954e3d705520008'
BASELINE = '4cf2b7d30672794cdfc3e2c924f391a632b2e09f96397bfc59d8e8c4353a87f1'
INPUT = 'c23d2c88fa9fdde4e07d917d972a3bdc8a21faafdfe00d0e3cc09b3324ec0878'
CID = 'STRING:profession-title'

def check(game, reports):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest
    gui = reports / 'profession-family-formal-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    original = read(gui / 'gui.json')
    peers = {m: reports / ('profession-family-formal-' + m) for m in ['zh', 'control', 'missing', 'baseline']}
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
    assert len(shots) == 14
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {m: {c['label']: c for c in d['checkpoints']} for m, d in data.items()}
    changes = []
    for name, step in shots:
        stem = 'run.cp-' + step
        actual = pixels(gui / ('gui.' + name + '.png'))
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        assert actual == pixels(peers['zh'] / (stem + '.png'))
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({cps[m]['cp-' + step][key] for m in peers}) == 1
        for ext in ['idx', 'pal']:
            assert len({(p / (stem + '.' + ext)).read_bytes() for p in peers.values()}) == 1
        a = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        b = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(a, b)
        outside = diff.copy()
        if name == 'profession-sugar-0':
            outside.paste((0, 0, 0), (260, 64, 1016, 132))
        assert not outside.getbbox() and bool(diff.getbbox()) == (name == 'profession-sugar-0'), (name, diff.getbbox())
        if diff.getbbox():
            changes.append({'name': name, 'difference': diff.getbbox()})
    source = [e for e in data['zh']['events'] if e.get('stage') == 'source' and e.get('candidate_id') == CID]
    assert len(source) == 2
    expected = {'Select a Profession for Veteran Soldiers(Statesman):': 174822, 'Select a Profession for Veteran Soldiers(Sugar Planter):': 174818}
    assert {e['shown']: e['source_linear'] for e in source} == expected
    assert all(e['safe'] == [65, 16, 254, 33] and e['font_px'] == 22 and e['entry_ip'] == '0D21:00C6' for e in source)
    regressions = []
    for fresh_name, gui_name, old_name in [('profession-family-previous-regression', 'profession-formal-gui', 'profession-formal-zh'), ('profession-family-farmer-regression', 'profession-variants-gui-v2', None)]:
        fresh, prior_gui = reports / fresh_name, reports / gui_name
        d, g = read(fresh / 'run.json'), read(prior_gui / 'gui.json')
        assert d['state'] == g['state']
        assert (fresh / 'run.memory').read_bytes() == (prior_gui / 'gui.memory').read_bytes()
        assert (fresh / 'raw.wav').read_bytes() == (prior_gui / 'raw.wav').read_bytes()
        assert {f.name: sha(f) for f in (fresh / 'save').glob('*.SAV')} == {f.name: sha(f) for f in (prior_gui / 'save').glob('*.SAV')}
        command = read(fresh / 'command.json')
        assert sha(Path(command[0])) == BINARY
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(prior_gui / 'gui.inputs.json')
        count = 0
        for name, step in [l.split() for l in (prior_gui / 'gui.shots').read_text().splitlines()]:
            stem = 'run.cp-' + step
            assert pixels(fresh / (stem + '.png')) == pixels(prior_gui / ('gui.' + name + '.png'))
            if old_name:
                old = reports / old_name
                assert pixels(fresh / (stem + '.png')) == pixels(old / (stem + '.png'))
                for ext in ['idx', 'pal']:
                    assert (fresh / (stem + '.' + ext)).read_bytes() == (old / (stem + '.' + ext)).read_bytes()
            count += 1
        regressions.append({'gui': gui_name, 'samples': count})
    return {'result': 'PASS', 'status': 'PASS_PROFESSION_FAMILY_FORMAL', 'samples': len(shots), 'changes': changes, 'source': source, 'regressions': regressions, 'inputs_sha256': INPUT, 'binary_sha256': BINARY, 'original_state': original['state'], 'final_step': original['state']['steps'], 'final_memory_sha256': original['state']['memory_sha256'], 'verified_fields': [{'candidate_id': CID, 'shown': e['shown'], 'safe': e['safe']} for e in source], 'scope': '兩行模板分流、兩種正常折行與農夫單行回歸；其他職業組合的正常命中不外推。'}

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
