#!/usr/bin/env python3
"""容器內驗正式封包可重現、清單、譯稿、授權與原版排除，展開後供啟動抽樣。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

p = argparse.ArgumentParser()
p.add_argument('--version', required=True)
p.add_argument('--batch', type=Path, default=Path('/repo/workplace/reports/goal183-release'))
p.add_argument('--extract-dir', type=Path)
a = p.parse_args()
b = a.batch
extract = a.extract_dir or b / 'extracted'
assert b.stat().st_uid == os.getuid() and not extract.exists()
extract.mkdir()
records = {}
sha = lambda data: hashlib.sha256(data).hexdigest()
for format in ['appimage', 'windows-zip', 'macos-zip']:
    one = next((b / 'packages-a' / format / a.version / 'patch').iterdir())
    two = next((b / 'packages-b' / format / a.version / 'patch').iterdir())
    assert one.read_bytes() == two.read_bytes(), format
    dst = extract / format
    dst.mkdir()
    if format == 'appimage':
        with (dst / 'extract.log').open('w') as log:
            subprocess.run([str(one), '--appimage-extract'], cwd=dst, stdout=log, stderr=subprocess.STDOUT, check=True)
        root = dst / 'squashfs-root'
    else:
        with zipfile.ZipFile(one) as z:
            assert z.testzip() is None
            assert all(x.date_time == (1980, 1, 1, 0, 0, 0) and '..' not in Path(x.filename).parts for x in z.infolist())
            z.extractall(dst)
            for x in z.infolist():
                if not x.is_dir():
                    (dst / x.filename).chmod((x.external_attr >> 16) & 0o777)
        root = next(p for p in dst.iterdir() if p.is_dir())
    manifest = json.loads((root / 'MANIFEST.json').read_text())
    assert manifest['version'] == a.version and all(v['Version'] == a.version for v in manifest['frontend_version'])
    links = {str(p.relative_to(root)): str(p.readlink()) for p in root.rglob('*') if p.is_symlink()}
    assert links == ({'.DirIcon': 'colonization-cht.svg'} if format == 'appimage' else {})
    files = {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
    assert set(files) == set(manifest['files']) | {'MANIFEST.json'}
    for name, info in manifest['files'].items():
        assert info == {'sha256': sha(files[name].read_bytes()), 'bytes': files[name].stat().st_size}, name
        assert files[name].stat().st_uid == os.getuid() and files[name].stat().st_gid == os.getgid()
        if name.startswith('text/'):
            assert files[name].read_bytes() == (Path('/repo') / name).read_bytes()
        assert Path(name).name.upper() not in manifest['requires_original']['files']
        assert not re.search(r'\.(sav|ttf|png|memory|idx|pal|ss|pik)$', name, re.I)
        assert not name.lower().endswith('.exe') or name == 'bin/colonization-window.exe'
    records[format] = {'result': 'PASS_REPRODUCIBLE_PACKAGE', 'files': len(files), 'sha256': sha(one.read_bytes()),
                       'bytes': one.stat().st_size, 'root': str(root), 'embedded_version': manifest['frontend_version'],
                       'original_files': False, 'exact_rebuild': True}
    if format == 'macos-zip':
        records[format]['binary_validation'] = manifest['binary_validation']
(b / 'packages-check.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: {q: v[q] for q in ['result', 'bytes', 'files', 'sha256']} for k, v in records.items()}))
