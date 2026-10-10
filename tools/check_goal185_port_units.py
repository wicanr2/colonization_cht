#!/usr/bin/env python3
"""港口船隻頂列及三列選項的來源、正常GUI、同狀態與回退驗證。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

INPUT = 'f647c7cdb57ebd5c8e1df282b100f294c5232c96e8e70bbb8a703de875071527'
BINARY = 'd392c602de2e31177a25abf6420ba8dbeb3d379a6332345757209e9914eb2a44'
BASELINE = '11fe199fe13106f145cdb3c4aab2c22018a7a49007d507c425d0cc257aeee9f6'
SEED = {'COLONY00.SAV': 'a777d2fb1b98e57abe6c94de8e37225077f984d814d394d80f106c98cb2e3343',
        'COLONY03.SAV': 'd3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'}
OPTION_ID = 'GAME.TXT:@EUROPESHIPOPTIONS:0x00009B3D#4+list'


def check(game, reports):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    raw = (game / 'GAME.TXT').read_bytes()[0x9B3D:0x9B3D + 75]
    assert hashlib.sha256(raw).hexdigest() == '9f32942301758e884038362e26a03eebf1bbd02076aedc5d5b07983875e1d370'
    full = raw.decode('cp437').strip().split('\r\n')
    assert len(full) == 4
    selected = [full[i] for i in (0, 1, 3)]
    gui = reports / 'port-unit-formal-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    original = read(gui / 'gui.json')
    peers = {m: reports / ('port-unit-formal-' + m) for m in ('zh', 'control', 'missing', 'baseline')}
    data = {m: read(p / 'run.json') for m, p in peers.items()}
    for mode, root in peers.items():
        assert data[mode]['state'] == original['state']
        assert (root / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes()
        assert (root / 'raw.wav').read_bytes() == (gui / 'raw.wav').read_bytes()
        assert data[mode]['input_hashes'] == original['input_hashes']
        assert {p.name: sha(p) for p in (root / 'save').glob('COLONY*.SAV')} == SEED
        command = read(root / 'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(gui / 'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
    assert {p.name: sha(p) for p in (gui / 'save').glob('COLONY*.SAV')} == SEED
    shots = [line.split() for line in (gui / 'gui.shots').read_text().splitlines()]
    assert len(shots) == len({name for name, step in shots}) == 11
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {m: {c['label']: c for c in r['checkpoints']} for m, r in data.items()}
    changes = []
    menu_shots = {'ship-selected', 'hover-first', 'hover-second', 'hover-third'}
    for name, step in shots:
        actual = pixels(gui / f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        stem = 'run.cp-' + step
        assert actual == pixels(peers['zh'] / (stem + '.png'))
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for mode, root in peers.items():
            for key in ('memory_sha256', 'raw_sha256', 'palette_sha256'):
                assert cps[mode]['cp-' + step][key] == cps['control']['cp-' + step][key]
            for suffix in ('idx', 'pal'):
                assert (root / (stem + '.' + suffix)).read_bytes() == (peers['control'] / (stem + '.' + suffix)).read_bytes()
        with Image.open(peers['zh'] / (stem + '.png')) as im:
            zh = im.convert('RGB')
        with Image.open(peers['baseline'] / (stem + '.png')) as im:
            baseline = im.convert('RGB')
        diff = ImageChops.difference(zh, baseline)
        regions = [[464, 0, 812, 32], [324, 360, 828, 504]] if name in menu_shots else []
        outside = diff.copy()
        for region in regions:
            outside.paste((0, 0, 0), region)
        assert not outside.getbbox(), (name, outside.getbbox())
        assert bool(diff.getbbox()) == (name in menu_shots), name
        if diff.getbbox():
            changes.append({'name': name, 'safe_regions': regions, 'difference': list(diff.getbbox())})
    events = data['zh']['events']
    headers = [e for e in events if e.get('stage') == 'source' and e.get('candidate_id') == 'STRING:port-ship-header']
    options = [e for e in events if e.get('stage') == 'source' and e.get('candidate_id') == OPTION_ID]
    assert headers and all(e['font_px'] == 22 and e['safe'] == [116, 0, 203, 8] for e in headers)
    assert options and all(e['font_px'] == 30 and e['safe'] == [81, 90, 207, 126] and e['items'] == selected for e in options)
    assert any(e.get('candidate_id') == OPTION_ID and e.get('stage') == 'active' for e in events)
    assert not data['zh'].get('string_misses')
    assert not any(' '.join(selected) in k for k in data['zh'].get('dialog_misses', {}))
    fields = [{'candidate_id': e['candidate_id'], 'shown': e['shown'], 'safe': e['safe']} for e in headers]
    fields = list({(f['candidate_id'], f['shown'], tuple(f['safe'])): f for f in fields}.values())
    return {'result': 'PASS', 'status': 'PASS_PORT_UNITS_FORMAL', 'samples': len(shots), 'changes': changes,
            'inputs_sha256': INPUT, 'binary_sha256': BINARY,
            'final_step': original['state']['steps'], 'final_memory_sha256': original['state']['memory_sha256'],
            'original_state': original['state'], 'verified_fields': fields,
            'partial_option_sources': [{'candidate_id': OPTION_ID, 'safe': e['safe'], 'displayed_rows': [1, 2, 4],
                                        'font_px': e['font_px']} for e in options],
            'census_limit': '三列子集不提升完整四列EUROPESHIPOPTIONS來源；其他船型的容量投影不計正常命中。'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if any(not (a.game / name).is_file() for name in EXPECTED):
        print('SKIP：缺合法原版輸入')
        return 77
    result = check(a.game, a.reports)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
