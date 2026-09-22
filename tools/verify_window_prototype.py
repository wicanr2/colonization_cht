#!/usr/bin/env python3
"""容器內獨立核對真實視窗、逐指令重播與英文控制。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, default=Path('/out'))
p.add_argument('--prefix', default='goal058-window', help='本機收據前綴；各輪不可覆寫舊收據')
a = p.parse_args()
assert '/' not in a.prefix and a.prefix not in ('.', '..')
names = [a.prefix, a.prefix + '-replay', a.prefix + '-control']
receipts = [json.loads((a.out / (n + '.json')).read_text()) for n in names]
assert all(r['state'] == receipts[0]['state'] for r in receipts)
inputs = json.loads((a.out / (a.prefix + '.inputs.json')).read_text())
assert inputs['end'] == receipts[0]['state']['steps']
assert any(e['kind'] == 'move' and (e['x'], e['y']) == (128, 110) for e in inputs['inputs'])
assert sum(e['kind'] == 'press' for e in inputs['inputs']) >= 2
assert sum(e['kind'] == 'press' for e in inputs['inputs']) == sum(e['kind'] == 'release' for e in inputs['inputs'])
assert 'DIFFICUL.PIK' in receipts[0]['opened']
for index in range(5):
    assert any(f['lines'][index]['applied'] for f in receipts[0]['frames'])
new_keys = {'LABELS.TXT:0x00000888', 'LABELS.TXT:0x00000890'}
has_difficulty = any(r['candidate_id'] in new_keys for f in receipts[0]['frames'] for r in f['lines'])
if has_difficulty:
    assert all(any(r['candidate_id'] == key and r['applied']
                   for f in receipts[0]['frames'] for r in f['lines']) for key in new_keys)
    assert all(any(e.get('candidate_id') == key and e.get('accepted')
                   for e in receipts[0]['events']) for key in new_keys)
pairs = [(a.prefix + '.menu.png', 'goal057-live-zh.menu-clear.png'),
         (a.prefix + '.difficulty.png', a.prefix + '.final.png')]
images = []
for actual, reference in pairs:
    x = Image.open(a.out / actual).convert('RGB')
    y = Image.open(a.out / reference).convert('RGB')
    assert x.size == y.size == (1280, 800)
    assert ImageChops.difference(x, y).getbbox() is None
    images.append({'actual': actual, 'reference': reference, 'pixels_equal': True,
                   'sha256': hashlib.sha256((a.out / actual).read_bytes()).hexdigest()})
if has_difficulty:
    chinese = Image.open(a.out / (a.prefix + '.difficulty.png')).convert('RGB')
    original = Image.open(a.out / (a.prefix + '-control.final.png')).convert('RGB')
    assert chinese.size == original.size == (1280, 800)
    changed = {key: 0 for key in new_keys}
    bounds = [('LABELS.TXT:0x00000888', (39*4, 14*4, 76*4, 26*4)),
              ('LABELS.TXT:0x00000890', (20*4, 27*4, 96*4, 40*4))]
    for y in range(800):
        for x in range(1280):
            if chinese.getpixel((x, y)) == original.getpixel((x, y)):
                continue
            hit = next((key for key, (left, top, right, bottom) in bounds
                        if left <= x < right and top <= y < bottom), None)
            assert hit is not None, f'安全矩形外畫面變更：{x},{y}'
            changed[hit] += 1
    assert all(n > 0 for n in changed.values())
    images.append({'actual': a.prefix + '.difficulty.png',
                   'reference': a.prefix + '-control.final.png',
                   'only_two_difficulty_rectangles_changed': True,
                   'changed_pixels_by_candidate': changed})
result = {'scope': 'Linux/Xvfb有限原型，不含完整鍵盤、音訊、正式速度或存讀檔',
          'state_equal': True, 'state': receipts[0]['state'], 'images': images,
          'input_count': len(inputs['inputs']), 'frame_count': len(receipts[0]['frames'])}
(a.out / (a.prefix + '-receipt.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
