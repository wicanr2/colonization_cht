#!/usr/bin/env python3
"""容器內實際Wine批次檔啟動；參數經subprocess傳遞。"""
import json
from pathlib import Path
import subprocess
import sys

b, d = map(Path, sys.argv[1:])
root = Path(json.loads((b / 'packages-check.json').read_text())['windows-zip']['root'])
win = lambda p: 'Z:' + str(p).replace('/', '\\')
version = subprocess.check_output(['wine', win(root / 'bin/colonization-window.exe'), '--version'], text=True)
(d / 'version.json').write_text(version)
args = ['wine', 'cmd.exe', '/d', '/c', 'call', win(root / 'colonization-cht.bat'), '--game', 'Z:\\game',
        '--play=false', '--audio-mute', '--window-steps', '50000000', '--audio-wav', win(d / 'original.wav'), '--out', win(d / 'run')]
(d / 'arguments.json').write_text(json.dumps(args, indent=2) + '\n')
subprocess.run(args, check=True, timeout=180)
