#!/usr/bin/env python3
"""Docker內核對並彙整三平台兩類完整版；可附同版建城影片，完整包只留本機。"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone

from package_release import ORIGINAL, VERSION


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def check_payload(read, names, mode, timestamp, platform, edition, version):
    manifest = json.loads(read('MANIFEST.json'))
    assert manifest['version'] == version and manifest['platform'] == platform
    assert manifest['private_only'] and manifest['bundled_original']
    assert manifest['manual_validation'] == 'pending' and manifest['edition'] == edition
    with_hd = edition == 'hd'
    assert manifest['hd_assets_included'] == with_hd
    assert manifest['graphics_modes'] == (['original', 'hd'] if with_hd else ['original'])
    assert names == set(manifest['files']) | {'MANIFEST.json'}
    for name, expected in manifest['files'].items():
        data = read(name)
        assert len(data) == expected['bytes'], name
        assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
    graphics = [name for name in names if name.startswith('graphics/')]
    assert len(graphics) == (387 if with_hd else 0)
    assert not any(PurePosixPath(name).suffix.lower() == '.sav' for name in names)
    original = json.loads(read('FULL-LOCAL-MANIFEST.json'))
    assert original['version'] == version and original['edition'] == edition and original['private_only']
    for name, expected in original['files'].items():
        assert name.startswith('game/') and name in names
        assert manifest['files'][name] == {'bytes': expected['bytes'], 'sha256': expected['sha256']}
        assert abs(timestamp(name) - expected['source_mtime_ns'] / 1_000_000_000) < 2.01, name
    for name, expected in ORIGINAL.items():
        assert manifest['files']['game/' + name]['sha256'] == expected
    assert hashlib.sha256(read('ui/NotoSansCJK-Regular.ttc')).hexdigest() == 'b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a'
    if platform == 'windows-x86_64':
        assert read('README.txt').startswith(b'\xef\xbb\xbf')
        assert b'\n' not in read('README.txt').replace(b'\r\n', b'')
        launcher = read('start.bat')
        launcher.decode('ascii')
        assert b'--game "%~dp0game"' in launcher and b'\r\n' in launcher
    elif platform == 'macos-universal':
        assert mode('start.command') & 0o111
        assert b'--game "$PWD/game"' in read('start.command')
        assert manifest['binary_validation']['status'] == 'PASS_MACOS_UNIVERSAL_SIGNATURE_STRUCTURE'
        subprocess.run(['bash', '-n'], input=read('colonization-cht.sh'), check=True)
    else:
        assert mode('AppRun') & 0o111
        assert b'--game "$app_dir/game"' in read('AppRun')
    return {'files': len(names), 'graphics_files': len(graphics), 'original_files': len(original['files']),
            'language_files': sum(name.startswith('languages/') for name in names),
            'edition': edition, 'platform': platform, 'manual_validation': 'pending'}


def inspect_package(path, platform, edition, version):
    if path.suffix == '.zip':
        with zipfile.ZipFile(path) as archive:
            members = {}
            for member in archive.infolist():
                relative = PurePosixPath(member.filename)
                assert not relative.is_absolute() and '..' not in relative.parts and len(relative.parts) >= 2
                assert relative.parts[0] == path.stem and not member.is_dir()
                assert stat.S_IFMT(member.external_attr >> 16) == stat.S_IFREG
                if any(ord(char) > 127 for char in member.filename):
                    assert member.flag_bits & 0x800
                name = PurePosixPath(*relative.parts[1:]).as_posix()
                assert name not in members
                members[name] = member
            def read(name):
                return archive.read(members[name])
            def mode(name):
                return members[name].external_attr >> 16
            def timestamp(name):
                return datetime(*members[name].date_time, tzinfo=timezone.utc).timestamp()
            return check_payload(read, set(members), mode, timestamp, platform, edition, version)
    assert path.suffix == '.AppImage'
    with tempfile.TemporaryDirectory(prefix='colonization-full-inventory-') as temp:
        subprocess.run([str(path), '--appimage-extract'], cwd=temp, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, timeout=180, check=True)
        root = Path(temp) / 'squashfs-root'
        icon = root / '.DirIcon'
        assert icon.is_symlink() and icon.readlink() == Path('colonization-cht.svg')
        names = set()
        for item in root.rglob('*'):
            if item == icon:
                continue
            assert not item.is_symlink()
            if item.is_file():
                names.add(item.relative_to(root).as_posix())
        if edition == 'original':
            assert not (root / 'graphics').exists()
        return check_payload(lambda name: (root / name).read_bytes(), names,
                             lambda name: (root / name).stat().st_mode,
                             lambda name: (root / name).stat().st_mtime,
                             platform, edition, version)


def append_promo(target, promo, version):
    """只新增已驗同版影片，既有封包及驗收檔不得改寫。"""
    assert target.is_dir() and not (target / 'promo').exists(), '禁止覆寫既有影片'
    sums_path = target / 'SHA256SUMS.json'
    assert (target.stat().st_uid, target.stat().st_gid) == (os.getuid(), os.getgid())
    assert (sums_path.stat().st_uid, sums_path.stat().st_gid) == (os.getuid(), os.getgid())
    sums = json.loads(sums_path.read_text())
    assert sums['version'] == version and sums['private_only'] and not sums['promo_included']
    packages = sums['packages']
    assert len([name for name in packages if name.endswith(('.zip', '.AppImage'))]) == 6
    for name, expected in packages.items():
        relative = PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        path = target / name
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == expected['bytes'] and digest(path) == expected['sha256'], name
    validation = json.loads((promo / 'validation.json').read_text())
    assert validation['version'] == version and validation['includes_first_colony']
    assert validation['result'] == 'PASS_GAMEPLAY_PROMO_DELIVERY'
    film = promo / f'colonization-cht-{version}-promo.mp4'
    assert digest(film) == validation['sha256']
    files = sorted(promo.rglob('*'))
    assert files and all(not path.is_symlink() for path in files)
    assert all(path.suffix.lower() in {'.mp4', '.png', '.json', '.log', '.srt', '.txt'}
               for path in files if path.is_file())
    shutil.copytree(promo, target / 'promo')
    for source in files:
        if not source.is_file():
            continue
        path = target / 'promo' / source.relative_to(promo)
        path.chmod(0o644)
        assert digest(path) == digest(source)
        packages[path.relative_to(target).as_posix()] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    sums['promo_included'] = True
    sums['delivery'] = 'three-platform-two-editions-and-first-colony-gameplay-promo'
    temp = sums_path.with_suffix('.json.tmp')
    assert not temp.exists()
    temp.write_text(json.dumps(sums, ensure_ascii=False, indent=2) + '\n')
    temp.replace(sums_path)
    print(json.dumps({'result': 'APPENDED_PROMO_EXISTING_PACKAGES_PRESERVED', 'version': version,
                      'directory': str(target), 'promo': str(target / 'promo' / film.name)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--staging', type=Path)
    parser.add_argument('--append-promo', action='store_true', help='只新增同版已驗影片，逐檔核對並保留既有六包及smoke')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--promo', type=Path, help='同版已驗建城影片')
    mode.add_argument('--packages-only', action='store_true', help='本輪只更新六包，不重製或冒用舊版影片')
    parser.add_argument('--output', type=Path, default=Path('/repo/dist-all'))
    args = parser.parse_args()
    assert VERSION.fullmatch(args.version)
    assert args.output.is_dir() and args.output.stat().st_uid == os.getuid()
    target = args.output / args.version
    if args.append_promo:
        assert args.promo and not args.packages_only and args.staging is None
        append_promo(target, args.promo, args.version)
        return
    assert args.staging is not None, '建立新版六包必須指定--staging'
    assert not target.exists(), '禁止覆寫既有版本'
    packages, checks = [], {}
    for directory, platform in [('linux', 'linux-x86_64'), ('windows', 'windows-x86_64'), ('macos', 'macos-universal')]:
        root = args.staging / directory / args.version
        sums = json.loads((root / 'SHA256SUMS.json').read_text())
        assert sums['version'] == args.version and sums['private_only']
        assert len(sums['packages']) == 2
        editions = set()
        for relative, expected in sums['packages'].items():
            path = root / relative
            assert path.is_file() and not path.is_symlink()
            assert PurePosixPath(relative).parts[0] == 'full-local' and '..' not in PurePosixPath(relative).parts
            assert path.stat().st_size == expected['bytes'] and digest(path) == expected['sha256']
            edition = expected['edition']
            assert edition in {'hd', 'original'} and edition not in editions
            editions.add(edition)
            checks[path.name] = inspect_package(path.resolve(), platform, edition, args.version)
            packages.append((path, relative, expected))
    assert len(packages) == 6
    validation, film = None, None
    if args.promo:
        validation = json.loads((args.promo / 'validation.json').read_text())
        assert validation['version'] == args.version and validation['includes_first_colony']
        assert validation['result'] == 'PASS_GAMEPLAY_PROMO_DELIVERY'
        film = args.promo / f'colonization-cht-{args.version}-promo.mp4'
        assert digest(film) == validation['sha256']
        promo_files = sorted(args.promo.rglob('*'))
        assert all(not path.is_symlink() for path in promo_files)
        assert all(path.suffix.lower() in {'.mp4', '.png', '.json', '.log', '.srt', '.txt'}
                   for path in promo_files if path.is_file())
    # 全部核對完成後才建立唯一現行交付根。
    target.mkdir()
    (target / 'full-local').mkdir()
    sums = {'version': args.version, 'private_only': True, 'manual_validation': 'pending',
            'delivery': 'three-platform-two-editions' + ('-and-first-colony-gameplay-promo' if args.promo else ''),
            'promo_included': bool(args.promo), 'packages': {}}
    for path, relative, expected in packages:
        destination = target / relative
        shutil.copyfile(path, destination)
        destination.chmod(0o755 if path.suffix == '.AppImage' else 0o644)
        assert digest(destination) == expected['sha256']
        sums['packages'][relative] = expected
    if args.promo:
        shutil.copytree(args.promo, target / 'promo')
        for path in (target / 'promo').rglob('*'):
            if path.is_file():
                sums['packages'][path.relative_to(target).as_posix()] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    verification = target / 'full-local' / 'verification.json'
    verification.write_text(json.dumps({
        'version': args.version, 'private_only': True, 'manual_validation': 'pending',
        'archive_inventory': checks, 'gameplay_capture': validation,
        'limits': ['本輪未執行全矩陣或原版精確對拍', 'Windows及macOS真機、未抽樣情境與人耳驗證由使用者完成']
    }, ensure_ascii=False, indent=2) + '\n')
    sums['packages']['full-local/verification.json'] = {'sha256': digest(verification), 'bytes': verification.stat().st_size}
    (target / 'SHA256SUMS.json').write_text(json.dumps(sums, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'result': 'DELIVERED_MANUAL_VALIDATION_PENDING', 'version': args.version,
                      'directory': str(target), 'full_packages': len(packages),
                      'promo': str(target / 'promo' / film.name) if film else None}, ensure_ascii=False))


if __name__ == '__main__':
    main()
