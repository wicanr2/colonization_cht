#!/usr/bin/env python3
"""容器內，重播正常主選單輸入後停留，錄取原版OPL音樂。需先啟動Xvfb。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--bundle', type=Path, required=True)
p.add_argument('--inputs', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--steps', type=int, default=300000000)
p.add_argument('--raw-control', action='store_true', help='原文控制側只錄音；須核對50M WAV前段一致')
a = p.parse_args()
assert a.output.parent.stat().st_uid == os.getuid() and not a.output.exists()
a.output.mkdir()
(a.output / 'save').mkdir()
source = json.loads(a.inputs.read_text())
assert source['end'] == 50000000
assert 50000000 <= a.steps <= 1100000000
extended = dict(source, end=a.steps)
replay = a.output / 'menu.inputs.json'
replay.write_text(json.dumps(extended) + '\n')
tokens = shlex.split(Path('/repo/tools/release/colonization-cht.sh').read_text().split('\nexec ', 1)[1].replace('\\\n', ' '))
assert tokens[-1] == '${args[@]}'
values = {'$m': str(a.bundle / 'masks'), '$t': str(a.bundle / 'text'), '$game': '/game', '$save': str(a.output / 'save')}
args = [str(a.binary)]
for token in tokens[1:-1]:
    for old, value in values.items():
        token = token.replace(old, value)
    assert '$' not in token
    args.append(token)
args += ['--window-steps', str(extended['end']), '--replay-inputs', str(replay), '--audio-mute',
         '--audio-wav', str(a.output / 'original.wav'), '--out', str(a.output / 'recording')]
if a.raw_control:
    args = [str(a.binary), '--window', '--root', '/game', '--audio', '--sb-digital', '--control', '--play',
            '--scratch', str(a.output / 'save'), '--window-steps', str(extended['end']), '--replay-inputs', str(replay),
            '--audio-mute', '--audio-wav', str(a.output / 'original.wav'), '--out', str(a.output / 'recording')]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {'method': '正常GUI輸入重播至主選單，其後不再輸入；只延長原版執行上限',
           'original_input_sha256': sha(a.inputs), 'extended_input_sha256': sha(replay),
           'binary_sha256': sha(a.binary), 'arguments': args,
           'dosgolem_commit': subprocess.check_output(['git', '-C', '/repo/workplace/dosgolem', 'rev-parse', 'HEAD'], text=True).strip()}
with (a.output / 'recording.log').open('w') as log:
    subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
receipt['wav_sha256'] = sha(a.output / 'original.wav')
if a.raw_control:
    import wave
    # Prefer the formal current release's same-input audio receipt.
    reference = Path('/repo/workplace/reports/goal183-release/smoke/shared-linux/original.wav')
    with wave.open(str(reference)) as ref, wave.open(str(a.output / 'original.wav')) as raw:
        assert raw.getparams()[:3] == ref.getparams()[:3]
        assert raw.readframes(ref.getnframes()) == ref.readframes(ref.getnframes())
    receipt['control_audio_prefix_equal_to_formal_50m'] = sha(reference)
(a.output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))
