#!/usr/bin/env python3
"""檢查目標184正常GUI、中英同狀態、缺圖集及滑鼠往返收據。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--reports', type=Path, required=True)
a = p.parse_args()
root = a.reports
gui = root / 'pedia-gui-formal'
runs = root / 'pedia-replays-formal'
read = lambda p: json.loads(p.read_text())
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
data = {n: read(runs / n / 'run.json') for n in ('zh', 'en', 'missing')}
assert data['zh']['state'] == data['en']['state'] == data['missing']['state'] == read(gui / 'gui-pedia.json')['state']
files = [p.name for p in (runs / 'zh').iterdir() if p.suffix in ('.idx', '.pal') or p.name == 'run.memory']
for f in files:
    assert len({digest(runs / n / f) for n in data}) == 1, f
saves = lambda path: {p.name: digest(p) for p in path.iterdir() if p.is_file()}
assert saves(gui / 'scratch') == saves(runs / 'zh' / 'save') == saves(runs / 'en' / 'save') == saves(runs / 'missing' / 'save')
fields = [(106, 4, 215, 11), (108, 12, 212, 20), (35, 44, 77, 52), (114, 44, 184, 52), (221, 44, 241, 52)]
rects = [tuple(x * 4 for x in r) for r in fields]
shots = dict(s.split() for s in (gui / 'gui-pedia.shots').read_text().splitlines())
base = Image.open(gui / 'gui-pedia.building-article-14.png').convert('RGB')
results = {}
cursor_positions = [(128, 6), (128, 14), (40, 47), (125, 47), (225, 47)]
for label, raw_step in shots.items():
    step = int(raw_step)
    if not any(k in label for k in ('article-14', 'hover-', 'away-')):
        continue
    img = Image.open(gui / ('gui-pedia.' + label + '.png')).convert('RGB')
    replay = Image.open(runs / 'zh' / ('run.cp-' + raw_step + '.png')).convert('RGB')
    en = Image.open(runs / 'en' / ('run.cp-' + raw_step + '.png')).convert('RGB')
    missing = Image.open(runs / 'missing' / ('run.cp-' + raw_step + '.png')).convert('RGB')
    pos = cursor_positions[int(label.rsplit('-', 1)[1])] if 'hover-' in label else None
    for rect in rects:
        assert img.crop(rect).tobytes() == replay.crop(rect).tobytes(), (label, rect, 'GUI/replay')
        assert missing.crop(rect).tobytes() == en.crop(rect).tobytes(), (label, rect, 'missing fallback')
        assert img.crop(rect).tobytes() != en.crop(rect).tobytes(), (label, rect, 'still English')
        l, t, r, b = rect
        for y in range(t, b):
            for x in range(l, r):
                if pos and pos[0]*4 <= x < (pos[0]+16)*4 and pos[1]*4 <= y < (pos[1]+16)*4:
                    continue
                assert base.getpixel((x, y)) == img.getpixel((x, y)), (label, x, y, 'mouse changed text')
    results[label] = {'step': step, 'gui_sha256': digest(gui / ('gui-pedia.' + label + '.png'))}
assert len(results) == 11
events = data['zh']['events']
sources = [e for e in events if e.get('stage') == 'source' and tuple(e.get('safe', [])) in fields]
article_step = int(shots['building-article-14'])
latest = {tuple(e['safe']): e for e in sources if e['step'] <= article_step}
assert set(latest) == set(fields)
for e in latest.values():
    assert e['font_px'] == 22 and e['entry_ip'] == '0D21:00C6'
    last = [x for x in events if x.get('shown') == e['shown'] and e['step'] < x.get('step', 0) <= article_step][-1]
    assert last['stage'] == 'active', last
menu = root / 'menu-gui-prototype'
menu_base = Image.open(menu / 'menu-before.png').convert('RGB')
menu_rects = [(344, y*4, 928, (y+7)*4) for y in (107, 115, 123, 131, 139)]
points = [(88,107),(160,107),(231,107),(128,115),(88,115),(160,123),(231,123),(88,131),(128,131),(160,139),(231,139),(86,146),(230,114),(128,130)]
checks = [('menu-hover', (128,110)), ('menu-after', None)] + [(f'sweep-{i:02d}-{k}', pt if k == 'hover' else None) for i, pt in enumerate(points) for k in ('hover','away')]
for name, pos in checks:
    img = Image.open(menu / (name + '.png')).convert('RGB')
    for l, t, r, b in menu_rects:
        for y in range(t, b):
            for x in range(l, r):
                if pos and pos[0]*4 <= x < (pos[0]+16)*4 and pos[1]*4 <= y < (pos[1]+16)*4:
                    continue
                assert img.getpixel((x,y)) == menu_base.getpixel((x,y)), (name,x,y)
ma, mb = root / 'menu-replay-formal', root / 'menu-control-v2'
assert read(ma / 'run.json')['state'] == read(mb / 'run.json')['state'] == read(menu / 'run.json')['state']
for f in ('run.memory', 'original.wav', 'run.final.idx', 'run.final.pal'):
    assert digest(ma / f) == digest(mb / f), f
summary = {
    'result': 'PASS_TEXT_RETENTION', 'scope': '同篇百科五欄及主選單游標分層',
    'gui_input_sha256': digest(gui / 'gui-pedia.inputs.json'),
    'menu_input_sha256': digest(menu / 'run.inputs.json'),
    'pedia_state': data['zh']['state'], 'original_files_equal': files,
    'fields': list(latest.values()), 'gui_checks': results, 'menu_checks': len(checks),
    'gui_saves': saves(gui / 'scratch'),
    'formal_sources': {p.name: digest(p) for p in (root / 'formal').glob('*.go')},
    'font': 'Cubic 11 v1.430', 'font_sha256': '8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c',
    'tools': {'Go': '1.26.7', 'dosgolem': 'c5953b9', 'Docker': 'colonization-verification:20260930-r1'},
}
(root / 'verification.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(summary['result'])
