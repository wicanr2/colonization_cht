#!/usr/bin/env python3
"""Docker/Xvfb：重播正常百科 GUI 輸入，對照原版狀態與缺圖集回退。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--gui', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
if not Path('/game/OPENING.EXE').is_file():
    raise SystemExit(77)
a.output.mkdir()
inputs = a.gui / 'gui-pedia.inputs.json'
steps = [int(s.split()[1]) for s in (a.gui / 'gui-pedia.shots').read_text().splitlines()]
end = json.loads(inputs.read_text())['end']
masks = Path(json.loads(Path('/repo/workplace/reports/goal183-release/packages-check.json').read_text())['appimage']['root']) / 'masks'
seed = Path('/repo/workplace/reports/goal178-orders/codex-audit/load-route-v2/scratch/COLONY00.SAV')
for name in ('zh', 'en', 'missing'):
    run = a.output / name
    run.mkdir()
    save = run / 'save'
    save.mkdir()
    shutil.copy2(seed, save / seed.name)
    atlas = run / 'absent.json' if name == 'missing' else masks / 'string-atlas.json'
    args = [str(a.binary), '--window', '--root', '/game', '--scratch', str(save),
            '--all-menu', '--catalog', '/repo/text/draft.zh-Hant.tsv', '--font-dir', str(masks / 'menu'),
            '--sea-status-a', '--sea-atlas', str(masks / 'sea-atlas.json'),
            '--dialog-a', '--dialog-atlas', str(masks / 'dialog-atlas.json'),
            '--string-a', '--string-atlas', str(atlas),
            '--string-templates', '/repo/text/string-templates.zh-Hant.tsv',
            '--play=false', '--replay-inputs', str(inputs), '--window-steps', str(end),
            '--checkpoint-steps', ','.join(map(str, steps)), '--out', str(run / 'run')]
    if name == 'en':
        args.append('--control')
    with (run / 'run.log').open('w') as log:
        subprocess.run(args, stdout=log, stderr=log, check=True, timeout=150)
    (run / 'args.json').write_text(json.dumps(args, indent=2) + '\n')
print(a.output)
