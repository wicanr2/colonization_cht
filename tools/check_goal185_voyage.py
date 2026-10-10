#!/usr/bin/env python3
"""返歐航程三欄與正常G兩列：正式GUI、同狀態、回退及區外不變。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY = '07ba16de36ad8c68748ad3d9149d18f9e163b38317b36f39bfd507a24c601389'
BASELINE = '8e27f92bc4a73ded8289f19e664e62b5eae1185b21bad3866c33c7e7a94af015'
INPUT = 'fc486050ad5747f9f6a4300ca12cb320a8eccf48c61f6b66ec00efbc4cea177e'
SOURCES = {
    'GAME.TXT': '67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a',
    'NAMES.TXT': '4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061',
    'LABELS.TXT': 'e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204',
}
SEED = {
    'COLONY03.SAV': 'd3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77',
    'COLONY09.SAV': 'f5982c9974e6b7e6d36e52d47a384503fcca148da58471d1f330217c692e40f0',
}
CHANGED = {'go-to-ports', 'london-route', 'europe'}
AREAS = {
    'go-to-ports': [[76, 96, 157, 120]],
    'london-route': [[101, 0, 218, 8], [241, 92, 286, 99]],
    'europe': [[92, 0, 227, 8]],
}


def saves(directory):
    return {p.name: sha(p) for p in directory.glob('COLONY*.SAV')}


def check(game, reports):
    for name, digest in dict(EXPECTED, **SOURCES).items():
        assert sha(game / name) == digest, name
    gui = reports / 'voyage-formal-gui'
    seed = reports.parent / 'goal181-colony-rest/cargo-messages-formal-gui-v153/scratch'
    assert saves(seed) == SEED
    assert set(read(gui / 'session.json')['initial_saves']) == set(SEED)
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    original = read(gui / 'gui.json')
    peers = {m: reports / ('voyage-formal-' + m) for m in ('zh', 'control', 'missing', 'baseline')}
    data = {m: read(p / 'run.json') for m, p in peers.items()}
    for mode, p in peers.items():
        assert data[mode]['state'] == original['state'], mode
        assert (p / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes(), mode
        assert (p / 'raw.wav').read_bytes() == (gui / 'raw.wav').read_bytes(), mode
        assert data[mode]['input_hashes'] == original['input_hashes'], mode
        assert saves(p / 'save') == saves(gui / 'save'), mode
        command = read(p / 'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs') + 1]).samefile(gui / 'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
    shots = [line.split() for line in (gui / 'gui.shots').read_text().splitlines()]
    assert len(shots) == len({n for n, s in shots}) == 14
    captures = {r['name']: r for r in map(json.loads, (gui / 'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {m: {c['label']: c for c in r['checkpoints']} for m, r in data.items()}
    changes = []
    for name, step in shots:
        stem = 'run.cp-' + step
        actual = pixels(gui / f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        assert actual == pixels(peers['zh'] / (stem + '.png'))
        assert pixels(peers['control'] / (stem + '.png')) == pixels(peers['missing'] / (stem + '.png'))
        for mode, p in peers.items():
            for key in ('memory_sha256', 'raw_sha256', 'palette_sha256'):
                assert cps[mode]['cp-' + step][key] == cps['control']['cp-' + step][key]
            for ext in ('idx', 'pal'):
                assert (p / (stem + '.' + ext)).read_bytes() == (peers['control'] / (stem + '.' + ext)).read_bytes()
        a = Image.open(peers['zh'] / (stem + '.png')).convert('RGB')
        b = Image.open(peers['baseline'] / (stem + '.png')).convert('RGB')
        diff = ImageChops.difference(a, b)
        outside = diff.copy()
        for box in AREAS.get(name, []):
            outside.paste((0, 0, 0), tuple(v * 4 for v in box))
        assert not outside.getbbox(), (name, outside.getbbox())
        assert bool(diff.getbbox()) == (name in CHANGED), name
        if name in CHANGED:
            changes.append({'name': name, 'difference': list(diff.getbbox()), 'approved_regions': AREAS[name]})
        if name == 'go-to-ports':
            palette = (peers['zh'] / (stem + '.pal')).read_bytes()
            rgb = lambda c: tuple((v << 2) | (v >> 4) for v in palette[c * 3:c * 3 + 3])
            row = list(a.crop((308, 436, 628, 480)).getdata())
            assert row.count(rgb(8)) > 300
            assert rgb(68) not in row and rgb(149) not in row
    sources = [e for e in data['zh']['events'] if e.get('stage') == 'source' and 'voyage' in e.get('candidate_id', '')]
    expected = {
        'Go To London': ('STRING:voyage-go-to', 22, [241, 92, 286, 99]),
        'English Caravel Sailing For London ': ('STRING:voyage-ship-header', 22, [101, 0, 218, 8]),
        'English Caravel Now Arriving In London ': ('STRING:voyage-ship-header', 22, [92, 0, 227, 8]),
        'London (England) Jamestown': ('STRING:voyage-ports+list', 27, [76, 96, 157, 120]),
    }
    fields = []
    for shown, (cid, size, safe) in expected.items():
        hits = [e for e in sources if e.get('shown') == shown and e.get('candidate_id') == cid]
        assert hits and all(e['font_px'] == size and e['safe'] == safe and e['entry_ip'] == '0D21:00C6' for e in hits), shown
        assert any(e.get('stage') == 'active' and e.get('candidate_id') == cid for e in data['zh']['events']), cid
        if cid.endswith('+list'):
            assert hits[0]['items'] == ['London (England)', 'Jamestown']
        fields.append({'candidate_id': cid, 'shown': shown, 'safe': safe})
    return {
        'result': 'PASS', 'status': 'PASS_VOYAGE_FORMAL', 'samples': 14, 'changes': changes,
        'inputs_sha256': INPUT, 'binary_sha256': BINARY, 'original_state': original['state'],
        'final_step': original['state']['steps'], 'final_memory_sha256': original['state']['memory_sha256'],
        'verified_fields': fields,
        'scope': '三個航程欄位與London／Jamestown兩列；灰色保留。其他名稱、目的地數量及192組容量不算正常命中。',
    }


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
