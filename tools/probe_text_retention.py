#!/usr/bin/env python3
"""Docker 內的 DRAFT：保留已觀測印字，不修改原版 CPU 或記憶體。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
shutil.copytree(a.source, a.output)
path = a.output / 'strings.go'
s = path.read_text()
old = '''		case it.phase == "waiting-screen" && now-it.complete > screenWait:
			changes = append(changes, [3]any{it, "expired", "screen-sync-timeout"})
			continue
'''
assert s.count(old) == 1
s = s.replace(old, '')
start = s.index('\t\tscreenWait := uint64(2000000)')
end = s.index('\t\tsame := stringSame(canvas, it, cursor)', start)
s = s[:start] + s[end:]
path.write_text(s)
path = a.output / 'adapter.go'
s = path.read_text()
anchor = '\t\t\t\tev := map[string]any{"candidate_id": it.id, "stage": ch[1], "step": m.Steps, "shown": it.text}'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '\n\t\t\t\tev["wait_steps"] = m.Steps - it.complete')
anchor = '\t\t\toutput, results, e = overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, layers)'
assert s.count(anchor) == 1
replacement = '''			// DRAFT：只清除已驗證主選單列上的游標，中文合成後還原游標像素。
			clean := indexed
			cur := cursorBox(int(d.Mouse.X), int(d.Mouse.Y))
			for _, l := range lines {
				if l.patch == nil || len(l.afterSafe) != l.safe().Dx()*l.safe().Dy() {
					continue
				}
				box := cur.Intersect(l.safe())
				if box.Empty() { continue }
				if &clean[0] == &indexed[0] { clean = bytes.Clone(indexed) }
				for y := box.Min.Y; y < box.Max.Y; y++ {
					for x := box.Min.X; x < box.Max.X; x++ {
						clean[y*320+x] = l.afterSafe[(y-l.safe().Min.Y)*l.safe().Dx()+x-l.safe().Min.X]
					}
				}
			}
			output, results, e = overlay.ComposeLayers(clean, m.DAC[:], 320, 200, 4, layers)
			for y := max(0, cur.Min.Y); y < min(200, cur.Max.Y); y++ {
				for x := max(0, cur.Min.X); x < min(320, cur.Max.X); x++ {
					i := y*320+x
					if indexed[i] == clean[i] { continue }
					p := int(indexed[i])*3
					c := color.RGBA{m.DAC[p]<<2|m.DAC[p]>>4, m.DAC[p+1]<<2|m.DAC[p+1]>>4, m.DAC[p+2]<<2|m.DAC[p+2]>>4, 255}
					draw.Draw(output, image.Rect(x*4,y*4,x*4+4,y*4+4), image.NewUniform(c), image.Point{}, draw.Src)
				}
			}'''
s = s.replace(anchor, replacement)
path.write_text(s)
(a.output / 'prototype.json').write_text(json.dumps({
    'status': 'DRAFT',
    'source': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in a.source.glob('*.go')},
    'candidate': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output.glob('*.go')},
    'scope': '輸出層文字等待及主選單游標合成；原版 CPU、RAM、輸入與音訊不變',
}, ensure_ascii=False, indent=2) + '\n')
print(a.output)
