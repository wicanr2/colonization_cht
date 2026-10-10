"""規格041：在固定Docker工具鏈組裝Linux AppImage，不改遊戲或啟動參數。"""

import copy
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

TOOLS = {
    'appimagetool.AppImage': 'a6d71e2b6cd66f8e8d16c37ad164658985e0cf5fcaa950c90a482890cb9d13e0',
    'runtime-x86_64': '1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf',
}
APPIMAGETOOL_1_9_0 = '46fdd785094c7f6e545b61afcfb0f3d98d8eab243f644b4b17698c01d06083d1'
NOTICES = ['AppImage-runtime-LICENSE.txt', 'libfuse-LGPL-2.1.txt', 'squashfuse-LICENSE.txt',
           'musl-COPYRIGHT.txt', 'mimalloc-LICENSE.txt', 'zstd-LICENSE.txt', 'zlib-LICENSE.txt']
ARCHIVES = ['type2-runtime-75849dc.tar.gz', 'fuse-3.15.0.tar.xz', 'squashfuse-0.5.2.tar.gz']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_appimage(files, manifest, repo, top, tools=Path('/opt/appimage-tools')):
    """沿既有payload及manifest建置；成功才回傳封包，不寫正式交付目錄。"""
    actual_tools = {}
    for name, expected in TOOLS.items():
        accepted = {expected}
        if name == 'appimagetool.AppImage':
            accepted.add(APPIMAGETOOL_1_9_0)
        if not (tools / name).is_file() or digest(tools / name) not in accepted:
            raise ValueError('AppImage工具指紋不同：' + name)
        actual_tools[name] = digest(tools / name)
    assets = repo / 'tools/release/appimage-runtime'
    source_files = json.loads((assets / 'files.json').read_text())
    required = set(NOTICES + ARCHIVES + ['manifest.json', 'source.json'])
    if set(source_files) != required:
        raise ValueError('AppImage來源／授權清冊不完整')
    for name, expected in source_files.items():
        path = assets / name
        if digest(path) != expected['sha256'] or path.stat().st_size != expected['bytes']:
            raise ValueError('AppImage來源／授權指紋不同：' + name)
    payload = dict(files)
    payload.pop('MANIFEST.json', None)
    for name in NOTICES:
        payload['LICENSES/' + name] = ((assets / name).read_bytes(), 0o644)
    for name in ARCHIVES:
        payload['LICENSES/AppImage-sources/' + name] = ((assets / name).read_bytes(), 0o644)
    payload['LICENSES/AppImage-sources.json'] = ((assets / 'manifest.json').read_bytes(), 0o644)
    payload['AppRun'] = (b'#!/bin/sh\nset -eu\n'
                         b'app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                         b'exec "$app_dir/colonization-cht.sh" "$@"\n', 0o755)
    for name in ['colonization-cht.desktop', 'colonization-cht.svg']:
        payload[name] = ((repo / 'tools/release' / name).read_bytes(), 0o644)
    bundled = copy.deepcopy(manifest)
    bundled['format'] = 'AppImage-type2'
    bundled['system_runtime'] = ['Linux x86_64', 'X11', 'OpenGL', 'ALSA', 'glibc', 'bash']
    bundled['packaging_tools_sha256'] = actual_tools
    bundled['dependencies']['AppImage-runtime'] = {
        'version': '75849dc', 'sha256': TOOLS['runtime-x86_64'],
        'license_files': ['LICENSES/' + name for name in NOTICES],
        'source_archives': ['LICENSES/AppImage-sources/' + name for name in ARCHIVES],
    }
    bundled['files'] = {
        name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        for name, (data, _) in sorted(payload.items())
    }
    payload['MANIFEST.json'] = ((json.dumps(bundled, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode(), 0o644)
    with tempfile.TemporaryDirectory(prefix='colonization-appimage-') as temp:
        appdir = Path(temp) / 'Colonization.AppDir'
        appdir.mkdir()
        for name, (data, mode) in sorted(payload.items()):
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('非法包內路徑：' + name)
            path = appdir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(mode)
        for path in [*appdir.rglob('*'), appdir]:
            os.utime(path, (0, 0))
        package = Path(temp) / (top + '.AppImage')
        env = dict(os.environ, ARCH='x86_64', SOURCE_DATE_EPOCH='0')
        cmd = [str(tools / 'appimagetool.AppImage'), '--appimage-extract-and-run', '--no-appstream',
               '--runtime-file', str(tools / 'runtime-x86_64'), '--comp', 'zstd',
               '--mksquashfs-opt=-no-xattrs', '--mksquashfs-opt=-mem', '--mksquashfs-opt=256M',
               '--mksquashfs-opt=-processors', '--mksquashfs-opt=1', str(appdir), str(package)]
        if actual_tools['appimagetool.AppImage'] == APPIMAGETOOL_1_9_0:
            # 1.9.0 另傳時間參數，避免 mksquashfs 同時讀取環境變數而拒絕。
            env.pop('SOURCE_DATE_EPOCH', None)
            cmd[-2:-2] = ['--mksquashfs-opt=-mkfs-time', '--mksquashfs-opt=0',
                          '--mksquashfs-opt=-all-time', '--mksquashfs-opt=0']
        result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=180)
        if result.returncode:
            raise RuntimeError('AppImage建置失敗：\n' + result.stdout)
        data = package.read_bytes()
        if data[:4] != b'\x7fELF' or data[8:11] != b'AI\x02':
            raise ValueError('AppImage輸出不是type2 ELF')
        return data, bundled
