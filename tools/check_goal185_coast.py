#!/usr/bin/env python3
"""G兩列目的地皆可選：正式GUI／四側及正常色層驗收。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_voyage import SOURCES, saves
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY = '54a1cf49e822558100bc503f11e37adf49e85dc447d91100addcc7fd9ad3a30f'
INPUT = 'db4377de8bd11270d17262df89d513160a41c68c03ca7b56032d13285acf6f99'
BASELINE = '07ba16de36ad8c68748ad3d9149d18f9e163b38317b36f39bfd507a24c601389'
CID = 'STRING:voyage-ports+list'


def check(game, reports):
    for name, digest in dict(EXPECTED, **SOURCES).items():
        assert sha(game / name) == digest
    gui = reports / 'coast-formal-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    original = read(gui / 'gui.json')
    peers = {m: reports / ('coast-formal-' + m) for m in ['zh', 'control', 'missing', 'baseline']}
    data = {m: read(p / 'run.json') for m, p in peers.items()}
    for mode, path in peers.items():
        assert data[mode]['state'] == original['state']
        assert (path / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes()
        assert (path / 'raw.wav').read_bytes() == (gui / 'raw.wav').read_bytes()
        assert data[mode]['input_hashes'] == original['input_hashes']
        assert saves(path / 'save') == saves(gui / 'save')
        command = read(path / 'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(gui / 'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
    shots = [l.split() for l in (gui / 'gui.shots').read_text().splitlines()]
    assert len(shots) == 10
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {m: {c['label']: c for c in r['checkpoints']} for m, r in data.items()}
    changed = {'go-to-coast', 'hover-0', 'hover-1'}
    for name, step in shots:
        stem = 'run.cp-' + step
        actual = pixels(gui / ('gui.' + name + '.png'))
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        assert actual == pixels(peers['zh'] / (stem + '.png'))
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for mode, path in peers.items():
            for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
                assert cps[mode]['cp-' + step][key] == cps['control']['cp-' + step][key]
            for ext in ['idx', 'pal']:
                assert (path / (stem + '.' + ext)).read_bytes() == (peers['control'] / (stem + '.' + ext)).read_bytes()
        a = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        b = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(a, b)
        outside = diff.copy()
        if name in changed:
            outside.paste((0, 0, 0), (304, 384, 628, 480))
            palette = (peers['zh'] / (stem + '.pal')).read_bytes()
            rgb = tuple((v << 2) | (v >> 4) for v in palette[68 * 3:68 * 3 + 3])
            assert list(a.crop((308, 436, 628, 480)).getdata()).count(rgb) > 300
        assert not outside.getbbox() and bool(diff.getbbox()) == (name in changed), name
    sources = [e for e in data['zh']['events'] if e.get('stage') == 'source' and e.get('candidate_id') == CID]
    assert sources and all(e['font_px'] == 27 and e['safe'] == [76, 96, 157, 120] and e['items'] == ['London (England)', 'Jamestown'] for e in sources)
    assert any(e.get('stage') == 'active' and e.get('candidate_id') == CID for e in data['zh']['events'])
    return {'result': 'PASS', 'status': 'PASS_COAST_FORMAL', 'samples': 10,
            'inputs_sha256': INPUT, 'binary_sha256': BINARY, 'original_state': original['state'],
            'final_step': original['state']['steps'], 'final_memory_sha256': original['state']['memory_sha256'],
            'verified_fields': [{'candidate_id': CID, 'shown': sources[0]['shown'], 'safe': sources[0]['safe']}],
            'scope': '只增加已觀測兩列的第二列68色；灰色8回歸另核，其他目的地形狀／名稱不外推。'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if any(not (a.game / n).is_file() for n in dict(EXPECTED, **SOURCES)):
        print('SKIP：缺合法原版輸入')
        return 77
    result = check(a.game, a.reports)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
