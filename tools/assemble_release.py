#!/usr/bin/env python3
"""Docker內彙整已驗三平台封包與影片，可另建只留本機的自帶資料包。"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import zipfile
from datetime import datetime, timezone

p = argparse.ArgumentParser()
p.add_argument('--version', required=True)
p.add_argument('--staging', type=Path, required=True)
p.add_argument('--promo', type=Path, required=True)
p.add_argument('--smoke', type=Path, required=True)
p.add_argument('--output', type=Path, default=Path('/repo/dist-all'))
p.add_argument('--full-game', type=Path)
p.add_argument('--full-only', action='store_true', help='只補尚不存在的私用包，不覆寫公開交付')
a = p.parse_args()
sha = lambda data: hashlib.sha256(data).hexdigest()
assert a.output.is_dir() and a.output.stat().st_uid == os.getuid()
assert (a.output / a.version).is_dir() if a.full_only else not (a.output / a.version).exists()
packages = sorted(a.staging.glob(f'*/{a.version}/patch/*'))
assert len(packages) == 3 and {x.suffix for x in packages} == {'.AppImage', '.zip'}
for package in packages:
    source = json.loads((package.parent.parent / 'SHA256SUMS.json').read_text())
    entry = source['packages']['patch/' + package.name]
    assert entry == {'sha256': sha(package.read_bytes()), 'bytes': package.stat().st_size}
film = a.promo / f'colonization-cht-{a.version}-promo.mp4'
video_check = json.loads((a.promo / 'validation.json').read_text())
assert video_check['sha256'] == sha(film.read_bytes()) and video_check['visual_sampling'] == 'PASS_EIGHT_FRAMES'
checks = json.loads((a.smoke / 'summary.json').read_text())
assert checks['result'] == 'PASS_RELEASE_SMOKE_WITH_MACOS_LIMITATION'
root = a.output / a.version
if not a.full_only:
    root.mkdir()
    (root / 'patch').mkdir()
    shutil.copytree(a.promo, root / 'promo')
    shutil.copytree(a.smoke, root / 'smoke', ignore=shutil.ignore_patterns('wine-prefix'))
public = {}
for package in packages:
    dst = root / 'patch' / package.name
    if a.full_only:
        assert dst.read_bytes() == package.read_bytes()
    else:
        shutil.copyfile(package, dst)
        dst.chmod(0o755 if dst.suffix == '.AppImage' else 0o644)
    public['patch/' + dst.name] = {'bytes': dst.stat().st_size, 'sha256': sha(dst.read_bytes())}
public['promo/' + film.name] = {'bytes': film.stat().st_size, 'sha256': video_check['sha256']}
if not a.full_only:
    (root / 'SHA256SUMS.json').write_text(json.dumps({'version': a.version, 'packages': public}, ensure_ascii=False, indent=2) + '\n')
if a.full_game:
    from package_release import ORIGINAL
    for name, expected in ORIGINAL.items():
        assert sha((a.full_game / name).read_bytes()) == expected
    local = root / 'full-local'
    local.mkdir()
    # Private game files only; never propagate a user's save or symlink.
    game = {str(p.relative_to(a.full_game)): p.read_bytes() for p in sorted(a.full_game.rglob('*'))
            if p.is_file() and not p.is_symlink() and p.suffix.lower() != '.sav'}
    game_mtime = {'game/' + name: (a.full_game / name).stat().st_mtime_ns for name in game}
    records = {}
    for package in packages:
        platform = 'linux-x86_64' if package.suffix == '.AppImage' else 'windows-x86_64' if 'windows' in package.name else 'macos-universal'
        files = {f'game/{k}': (v, 0o644) for k, v in game.items()}
        if platform == 'linux-x86_64':
            files[package.name] = (package.read_bytes(), 0o755)
            files['start.sh'] = (('#!/bin/bash\nset -e\ncd -- "$(dirname -- "$0")"\nexec "./' + package.name + '" --appimage-extract-and-run --game "$PWD/game" "$@"\n').encode(), 0o755)
        else:
            with zipfile.ZipFile(package) as z:
                for member in z.infolist():
                    if member.is_dir():
                        continue
                    relative = Path(*Path(member.filename).parts[1:])
                    assert '..' not in relative.parts
                    files[str(relative)] = (z.read(member), (member.external_attr >> 16) & 0o777)
            if platform == 'windows-x86_64':
                files['start.bat'] = (b'@echo off\r\nsetlocal DisableDelayedExpansion\r\ncall "%~dp0colonization-cht.bat" --game "%~dp0game" %*\r\n', 0o644)
            else:
                files['start.command'] = (b'#!/bin/bash\nset -e\ncd -- "$(dirname -- "$0")"\nexec ./colonization-cht.sh --game "$PWD/game" "$@"\n', 0o755)
        notice = {'version': a.version, 'platform': platform, 'private_only': True,
                  'notice': '使用者本機合法原版資料；不得提交Git、上傳或公開散布。存檔不隨包。',
                  'files': {k: {'bytes': len(v), 'sha256': sha(v), **({'mtime_ns': game_mtime[k]} if k in game_mtime else {})}
                            for k, (v, mode) in files.items()}}
        files['FULL-LOCAL-MANIFEST.json'] = ((json.dumps(notice, ensure_ascii=False, indent=2) + '\n').encode(), 0o644)
        top = f'colonization-cht-{a.version}-full-local-{platform}'
        buffer = io.BytesIO()
        if platform == 'linux-x86_64':
            with tarfile.open(fileobj=buffer, mode='w', format=tarfile.PAX_FORMAT) as t:
                for name, (data, mode) in sorted(files.items()):
                    info = tarfile.TarInfo(top + '/' + name)
                    info.size, info.mode, info.mtime = len(data), mode, 0
                    if name in game_mtime:
                        info.mtime = game_mtime[name] / 1000000000
                    t.addfile(info, io.BytesIO(data))
            zipped = io.BytesIO()
            with gzip.GzipFile(fileobj=zipped, mode='wb', filename='', mtime=0) as g:
                g.write(buffer.getvalue())
            data, suffix = zipped.getvalue(), '.tar.gz'
        else:
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for name, (data, mode) in sorted(files.items()):
                    timestamp = (1980, 1, 1, 0, 0, 0)
                    if name in game_mtime:
                        d = datetime.fromtimestamp(game_mtime[name] / 1000000000, timezone.utc)
                        timestamp = (max(1980, d.year), d.month, d.day, d.hour, d.minute, d.second)
                    info = zipfile.ZipInfo(top + '/' + name, timestamp)
                    info.create_system, info.external_attr, info.compress_type = 3, (0o100000 | mode) << 16, zipfile.ZIP_DEFLATED
                    z.writestr(info, data)
            data, suffix = buffer.getvalue(), '.zip'
        path = local / (top + suffix)
        path.write_bytes(data)
        # Verify every payload from the actual resulting archive.
        if suffix == '.zip':
            with zipfile.ZipFile(path) as z:
                extracted = {Path(*Path(n).parts[1:]).as_posix(): z.read(n) for n in z.namelist()}
        else:
            with tarfile.open(path) as t:
                extracted = {Path(*Path(n.name).parts[1:]).as_posix(): t.extractfile(n).read() for n in t.getmembers()}
        assert extracted == {k: v for k, (v, mode) in files.items()}
        records[path.name] = {'bytes': len(data), 'sha256': sha(data), 'verified_files': len(files)}
    (local / 'SHA256SUMS.json').write_text(json.dumps({'version': a.version, 'private_only': True, 'packages': records}, indent=2) + '\n')
print(root)
