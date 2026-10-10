#!/usr/bin/env python3
"""碼頭灰色裝備欄：正常GUI、原版同狀態、灰色與缺字模回退。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_port_units import SEED

INPUT = '3e66ba5bc8f77d8c25220e1f488e1d9ff5968e8523eb82d1cfbdea461b4be7d8'
BINARY = '2f0fbafd16e677e12774e8bdc11d093e8f2e46f5fb6aa2b99d3f67afcb051dcd'
BASELINE = 'd392c602de2e31177a25abf6420ba8dbeb3d379a6332345757209e9914eb2a44'
TITLE = 'GAME.TXT:@EUROPEARM:0x0000983C'
OPTIONS = 'GAME.TXT:@ARMOPTIONS:0x000098AC#12+list'
MENUS = {'dock-queued', 'gray-hover', 'gray-click', 'dock-ready', 'no-change-hover'}


def palette_rgb(raw, index):
    return tuple((v << 2) | (v >> 4) for v in raw[index * 3:index * 3 + 3])


def check(game, reports):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest
    raw = (game / 'GAME.TXT').read_bytes()[0x98AC:0x98AC + 362]
    assert hashlib.sha256(raw).hexdigest() == '56d19f3e5b4344d1f6c5a4745ed009f6f0f251ed4e45032792da48ad66de45ed'
    gui = reports / 'port-dim-formal-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    original = read(gui / 'gui.json')
    peers = {m: reports / ('port-dim-formal-' + m) for m in ('zh', 'control', 'missing', 'baseline')}
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
    assert len(shots) == len({name for name, step in shots}) == 13
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {m: {c['label']: c for c in r['checkpoints']} for m, r in data.items()}
    changes, gray = [], []
    for name, step in shots:
        stem = 'run.cp-' + step
        actual = pixels(gui / f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
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
            old = im.convert('RGB')
        diff = ImageChops.difference(zh, old)
        outside = diff.copy()
        if name in MENUS:
            outside.paste((0, 0, 0), (324, 288, 944, 576))
        assert not outside.getbbox(), (name, outside.getbbox())
        assert bool(diff.getbbox()) == (name in MENUS), name
        if name in MENUS:
            pal = (peers['zh'] / (stem + '.pal')).read_bytes()
            disabled, normal, accent = [palette_rgb(pal, i) for i in (8, 68, 149)]
            counts = []
            for y in (85, 97, 109):
                values = list(zh.crop((328, y * 4, 936, (y + 9) * 4)).getdata())
                assert values.count(disabled) > 300
                assert normal not in values and accent not in values, name
                counts.append(values.count(disabled))
            gray.append({'name': name, 'palette_index': 8, 'foreground_pixels': counts})
            changes.append({'name': name, 'safe': [81, 72, 236, 144], 'difference': list(diff.getbbox())})
    events = data['zh']['events']
    options = [e for e in events if e.get('stage') == 'source' and e.get('candidate_id') == OPTIONS]
    titles = [e for e in events if e.get('stage') == 'source' and e.get('candidate_id') == TITLE]
    assert len(options) == 2 and all(e['font_px'] == 30 and e['safe'] == [81, 72, 236, 144] and len(e['items']) == 6 for e in options)
    assert len(titles) == 2 and all(e['font_px'] == 30 and e['safe'] == [62, 56, 265, 70] for e in titles)
    assert not any('next ship.' in k for k in data['zh'].get('dialog_misses', {}))
    fields = [{'candidate_id': titles[0]['candidate_id'], 'shown': titles[0]['shown'], 'safe': titles[0]['safe']}]
    return {'result': 'PASS', 'status': 'PASS_PORT_DIM_FORMAL', 'samples': len(shots), 'changes': changes,
            'gray_rows': gray, 'inputs_sha256': INPUT, 'binary_sha256': BINARY,
            'final_step': original['state']['steps'], 'final_memory_sha256': original['state']['memory_sha256'],
            'original_state': original['state'], 'verified_fields': fields,
            'partial_option_sources': [{'candidate_id': e['candidate_id'], 'safe': e['safe'], 'font_px': e['font_px'],
                                        'displayed_rows': 6} for e in options],
            'census_limit': '普查僅採完整標題；六列子集不提升完整12列ARMOPTIONS來源。'}


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
