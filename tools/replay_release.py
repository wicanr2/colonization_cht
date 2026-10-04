#!/usr/bin/env python3
"""容器內使用正式Linux封包重播正式Wine的正常輸入。Xvfb由呼叫端管理。"""
import json
import os
from pathlib import Path
import subprocess

b = Path('/repo/workplace/reports/goal183-release')
root = Path(json.loads((b / 'packages-check.json').read_text())['appimage']['root'])
out = b / 'smoke/shared-linux'
assert not out.exists()
out.mkdir()
(out / 'save').mkdir()
env = dict(os.environ, COLONIZATION_CHT_SAVE=str(out / 'save'))
args = [str(root / 'AppRun'), '--game', '/game', '--play=false', '--audio-mute', '--window-steps', '50000000',
        '--replay-inputs', str(b / 'smoke/windows/run.inputs.json'), '--audio-wav', str(out / 'original.wav'), '--out', str(out / 'run')]
with (out / 'run.log').open('w') as log:
    subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
(out / 'arguments.json').write_text(json.dumps(args, indent=2) + '\n')
