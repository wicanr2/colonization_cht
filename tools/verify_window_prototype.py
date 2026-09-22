#!/usr/bin/env python3
"""容器內獨立核對真實視窗、逐指令重播與英文控制。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, default=Path('/out'))
a = p.parse_args()
names = ['goal058-window', 'goal058-window-replay', 'goal058-window-control']
receipts = [json.loads((a.out / (n + '.json')).read_text()) for n in names]
assert all(r['state'] == receipts[0]['state'] for r in receipts)
inputs = json.loads((a.out / 'goal058-window.inputs.json').read_text())
assert inputs['end'] == receipts[0]['state']['steps']
assert any(e['kind'] == 'move' and (e['x'], e['y']) == (128, 110) for e in inputs['inputs'])
assert sum(e['kind'] == 'press' for e in inputs['inputs']) >= 2
assert sum(e['kind'] == 'press' for e in inputs['inputs']) == sum(e['kind'] == 'release' for e in inputs['inputs'])
assert 'DIFFICUL.PIK' in receipts[0]['opened']
for index in range(5):
    assert any(f['lines'][index]['applied'] for f in receipts[0]['frames'])
pairs = [('goal058-window.menu.png', 'goal057-live-zh.menu-clear.png'),
         ('goal058-window.difficulty.png', 'goal058-window.final.png')]
images = []
for actual, reference in pairs:
    x = Image.open(a.out / actual).convert('RGB')
    y = Image.open(a.out / reference).convert('RGB')
    assert x.size == y.size == (1280, 800)
    assert ImageChops.difference(x, y).getbbox() is None
    images.append({'actual': actual, 'reference': reference, 'pixels_equal': True,
                   'sha256': hashlib.sha256((a.out / actual).read_bytes()).hexdigest()})
result = {'scope': 'Linux/Xvfb有限原型，不含完整鍵盤、音訊、正式速度或存讀檔',
          'state_equal': True, 'state': receipts[0]['state'], 'images': images,
          'input_count': len(inputs['inputs']), 'frame_count': len(receipts[0]['frames'])}
(a.out / 'goal058-window-receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
