#!/usr/bin/env python3
"""只在容器內產生可撤回前端；固定適配器來源，不修改正式探針。"""
import argparse
import hashlib
import os
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, default=Path('/repo'))
p.add_argument('--output', type=Path, default=Path('/out/window-prototype'))
p.add_argument('--reference', type=Path, default=Path('/reference'))
a = p.parse_args()
assert a.output.parent.is_dir() and a.output.parent.stat().st_uid == os.getuid()
s = (a.repo / 'tools/live_menu.go').read_text()
assert hashlib.sha256(s.encode()).hexdigest() == 'a0ace7112811b99c92eb8956f7ca9a28a9f70b669325e9b61350c74cf858ea36', '適配器來源不同，需重新審查'
anchor = '\tphase, polls := 0, 0\n'
end = '\tmust(os.WriteFile(*out+".memory", m.Mem, 0644))'
assert s.count(anchor) == 1 and s.count(end) == 1
start, finish = s.index(anchor), s.index(end)
s = s[:start] + '\trunWindow(m, d, render, *out)\n\trender("final")\n' + s[finish:]
old = '\t\tif label == "" {\n\t\t\tframes = append(frames, rec)'
assert s.count(old) == 1
s = s.replace(old, '\t\tif label == "" {\n\t\t\tfrontendFrame(output, rec)\n\t\t\tframes = append(frames, rec)')
# 英文對照仍用原有獨立解碼，不加掛hook或中文合成器。
old = '\t\t\tif label != "" {\n\t\t\t\toutput = image.NewRGBA'
assert s.count(old) == 1
s = s.replace(old, '\t\t\tif true {\n\t\t\t\toutput = image.NewRGBA')
a.output.mkdir(exist_ok=True)
assert a.output.stat().st_uid == os.getuid()
(a.output / 'adapter.go').write_text(s)
(a.output / 'window.go').write_bytes((a.repo / 'tools/window_prototype.go').read_bytes())
(a.output / 'window_test.go').write_bytes((a.repo / 'tools/window_prototype_test.go').read_bytes())
(a.output / 'go.mod').write_text('module colonization-window-prototype\n\ngo 1.24.0\n\nrequire github.com/hajimehoshi/ebiten/v2 v2.9.9\n')
(a.output / 'go.sum').write_bytes((a.reference / 'go.sum').read_bytes())
(a.output / 'go.work').write_text('go 1.24.0\nuse .\nuse /dosgolem\n')
print(a.output)
