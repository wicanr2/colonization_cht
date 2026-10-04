#!/usr/bin/env python3
"""Docker內從本機自帶資料包啟動正常輸入重播；任何產物禁止公開。"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

platform = sys.argv[1]
assert platform in {'linux', 'windows', 'macos'}
version = os.environ.get('COLONIZATION_RELEASE_VERSION', 'v.1.0.0-20261005')
repo = Path('/repo')
base = Path(os.environ.get('COLONIZATION_RELEASE_WORK', '/repo/workplace/reports/goal183-release'))
delivery = repo / 'dist-all' / version
package = next((delivery / 'full-local').glob('*-' + platform + '-*' + ('.tar.gz' if platform == 'linux' else '.zip')))
out = base / (sys.argv[2] if len(sys.argv) == 3 else 'full-local-smoke') / platform
assert not out.exists()
out.mkdir(parents=True)
if platform == 'linux':
    with tarfile.open(package) as t:
        assert all(not p.name.startswith('/') and '..' not in Path(p.name).parts and p.isfile() for p in t.getmembers())
        t.extractall(out)
else:
    with zipfile.ZipFile(package) as z:
        assert all(not p.filename.startswith('/') and '..' not in Path(p.filename).parts for p in z.infolist())
        z.extractall(out)
        for p in z.infolist():
            (out / p.filename).chmod((p.external_attr >> 16) & 0o777)
root = next(p for p in out.iterdir() if p.is_dir())
manifest = json.loads((root / 'FULL-LOCAL-MANIFEST.json').read_text())
assert manifest['private_only'] and manifest['version'] == version
for key, info in manifest['files'].items():
    path = root / key
    assert info['bytes'] == path.stat().st_size and info['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    if 'mtime_ns' in info:
        # Python's ZipFile.extract does not restore ZIP timestamps; real archive
        # tools do. Restore the input's recorded timestamp before the DOS probe.
        os.utime(path, ns=(info['mtime_ns'], info['mtime_ns']))
(out / 'save').mkdir()
env = dict(os.environ, COLONIZATION_CHT_SAVE=str(out / 'save'))
extra = ['--play=false', '--audio-mute', '--window-steps', '50000000', '--replay-inputs', str(base / 'smoke/windows/run.inputs.json'), '--out', str(out / 'run')]
if platform == 'linux':
    args = [str(root / 'start.sh')] + extra
elif platform == 'windows':
    win = lambda x: 'Z:' + str(x).replace('/', '\\')
    env['COLONIZATION_CHT_SAVE'] = win(out / 'save')
    args = ['wine', 'cmd.exe', '/d', '/c', 'call', win(root / 'start.bat')] + [win(x) if x.startswith('/') else x for x in extra]
else:
    subprocess.run(['bash', '-n', str(root / 'start.command')], check=True)
    subprocess.run(['bash', '-n', str(root / 'colonization-cht.sh')], check=True)
    result = {'platform': platform, 'result': 'PASS_PRIVATE_ARCHIVE_AND_SHELL_ONLY', 'macos_runtime': '未真機'}
    (out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)
with (out / 'run.log').open('w') as log:
    subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
data = json.loads((out / 'run.json').read_text())
baseline = json.loads((base / 'smoke/windows/run.json').read_text())
assert data['state'] == baseline['state']
result = {'platform': platform, 'result': 'PASS_PRIVATE_BUNDLE_NORMAL_INPUTS', 'state_equal': True,
          'memory_sha256': data['state']['memory_sha256'], 'files': len(manifest['files'])}
(out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
