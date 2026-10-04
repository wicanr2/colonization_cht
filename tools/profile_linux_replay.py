#!/usr/bin/env python3
"""只在 Docker 中複製目前來源並加 CPU 採樣；採樣修改不進正式前端。"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--inputs', type=Path, required=True)
a = p.parse_args()
assert a.output.parent.stat().st_uid == os.getuid() and not a.output.exists()
a.output.mkdir()
source = a.output / 'source'
shutil.copytree(a.source, source)
w = source / 'window.go'
text = w.read_text().replace('"sync"', '"sync"\n "runtime/pprof"', 1)
entry = 'func runWindow(m *golem.Machine, d *golem.DOS, render func(string), out string) {'
assert entry in text
text = text.replace(entry, entry+'\n pf, errProfile := os.Create(out+".cpu.pprof"); must(errProfile); defer pf.Close(); must(pprof.StartCPUProfile(pf)); defer pprof.StopCPUProfile()', 1)
w.write_text(text)
binary = a.output / 'profile-window'
subprocess.run(['go', 'build', '-mod=readonly', '-o', str(binary), '.'], cwd=source, check=True)
root = Path(json.loads(Path('/repo/workplace/reports/goal183-release/packages-check.json').read_text())['appimage']['root'])
tokens = shlex.split(Path('/repo/tools/release/colonization-cht.sh').read_text().split('\nexec ', 1)[1].replace('\\\n', ' '))
(a.output / 'save').mkdir()
values = {'$m': str(root / 'masks'), '$t': str(root / 'text'), '$game': '/game', '$save': str(a.output / 'save')}
args = [str(binary)]
for token in tokens[1:-1]:
    for old, value in values.items():
        token = token.replace(old, value)
    assert '$' not in token
    args.append(token)
end = json.loads(a.inputs.read_text())['end']
args += ['--play=false', '--audio-mute', '--replay-inputs', str(a.inputs), '--window-steps', str(end), '--out', str(a.output / 'run')]
start = time.monotonic()
with (a.output / 'run.log').open('w') as log:
    subprocess.run(args, stdout=log, stderr=log, check=True, timeout=450)
(a.output / 'timing.json').write_text(json.dumps({'seconds': time.monotonic()-start, 'arguments': args}, indent=2)+'\n')
with (a.output / 'cpu-top.txt').open('w') as top:
    subprocess.run(['go', 'tool', 'pprof', '-top', str(binary), str(a.output / 'run.cpu.pprof')], stdout=top, check=True)
print((a.output / 'cpu-top.txt').read_text())
