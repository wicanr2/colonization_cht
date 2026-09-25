#!/usr/bin/env python3
"""只在容器內組裝可撤回的 Ebitengine 前端；固定來源，不改寫 Go 程式。"""
import argparse
import hashlib
import os
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, default=Path('/repo'))
p.add_argument('--output', type=Path, default=Path('/out/window-prototype'))
p.add_argument('--reference', type=Path, default=Path('/reference'))
a = p.parse_args()
if not a.output.parent.is_dir() or a.output.parent.stat().st_uid != os.getuid():
    raise ValueError('輸出父目錄不存在或擁有者不符')
s = (a.repo / 'tools/live_menu.go').read_bytes()
if hashlib.sha256(s).hexdigest() != 'b3be863fb67f8229a66f6fb304cf8be5cb7f6f24bf94c20b8b72e025797f1f81':
    raise ValueError('適配器來源不同，需重新審查')
if b'frontendRunner(m, d, render, *out)' not in s or b'frontendFrameSink(output, rec)' not in s:
    raise ValueError('視窗接線不符')
a.output.mkdir(exist_ok=True)
if a.output.stat().st_uid != os.getuid():
    raise ValueError('輸出目錄擁有者不符')
(a.output / 'adapter.go').write_bytes(s)
(a.output / 'window.go').write_bytes((a.repo / 'tools/window_prototype.go').read_bytes())
(a.output / 'window_test.go').write_bytes((a.repo / 'tools/window_prototype_test.go').read_bytes())
(a.output / 'go.mod').write_text('module colonization-window-prototype\n\ngo 1.24.0\n\nrequire github.com/hajimehoshi/ebiten/v2 v2.9.9\n')
(a.output / 'go.sum').write_bytes((a.reference / 'go.sum').read_bytes())
(a.output / 'go.work').write_text('go 1.24.0\nuse .\nuse /dosgolem\n')
print(a.output)
