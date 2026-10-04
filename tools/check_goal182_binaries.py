#!/usr/bin/env python3
"""Docker內檢查目標182的PE／Mach-O架構與建置來源；不代表實機驗收。"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def macho(data, expected_cpu):
    magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from('<8I', data)
    assert magic == 0xFEEDFACF and cpu == expected_cpu and kind == 2
    assert 32 + size <= len(data)
    pos, versions = 32, []
    version = lambda n: f'{n >> 16}.{(n >> 8) & 255}.{n & 255}'
    for _ in range(count):
        cmd, length = struct.unpack_from('<II', data, pos)
        assert length >= 8 and pos + length <= 32 + size
        if cmd == 0x32:
            platform, minimum, sdk, ntools = struct.unpack_from('<4I', data, pos + 8)
            assert platform == 1 and length >= 24 + 8 * ntools
            versions.append({'minimum': version(minimum), 'sdk': version(sdk)})
        elif cmd == 0x24:
            minimum, sdk = struct.unpack_from('<II', data, pos + 8)
            versions.append({'minimum': version(minimum), 'sdk': version(sdk)})
        pos += length
    assert pos == 32 + size and len(versions) == 1
    return {'cpu': hex(cpu), 'load_version': versions[0], 'bytes': len(data), 'sha256': digest(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    root = args.out
    win = (root / 'colonization-window.exe').read_bytes()
    assert win[:2] == b'MZ'
    pe = struct.unpack_from('<I', win, 0x3C)[0]
    assert win[pe:pe+4] == b'PE\0\0'
    machine, = struct.unpack_from('<H', win, pe + 4)
    optional, = struct.unpack_from('<H', win, pe + 24)
    assert machine == 0x8664 and optional == 0x20B
    binaries = {'windows-amd64': {'machine': hex(machine), 'format': 'PE32+',
                                 'bytes': len(win), 'sha256': digest(win)}}
    thin = {}
    for arch, cpu in (('amd64', 0x1000007), ('arm64', 0x100000C)):
        thin[cpu] = (root / f'colonization-window-macos-{arch}').read_bytes()
        binaries[f'macos-{arch}'] = macho(thin[cpu], cpu)
    fat = (root / 'colonization-window-macos-universal').read_bytes()
    magic, count = struct.unpack_from('>II', fat)
    assert magic == 0xCAFEBABE and count == 2
    spans, seen = [], set()
    for n in range(count):
        cpu, subtype, offset, size, align = struct.unpack_from('>5I', fat, 8 + n * 20)
        assert cpu in thin and cpu not in seen and align <= 30
        assert offset >= 8 + count * 20 and offset % (1 << align) == 0
        assert offset + size <= len(fat) and fat[offset:offset + size] == thin[cpu]
        spans.append((offset, offset + size))
        seen.add(cpu)
    spans.sort()
    assert spans[0][1] <= spans[1][0]
    binaries['macos-universal'] = {'architectures': ['x86_64', 'arm64'], 'bytes': len(fat),
                                 'sha256': digest(fat), 'slices_equal_to_thin': True}
    infos = {}
    for platform, goos, goarch in (('windows', 'windows', 'amd64'), ('macos-amd64', 'darwin', 'amd64'),
                                  ('macos-arm64', 'darwin', 'arm64')):
        path = root / f'{platform}-build-info.txt'
        text = path.read_text()
        assert ': go1.26.7\n' in text
        assert f'GOOS={goos}\n' in text and f'GOARCH={goarch}\n' in text
        assert 'github.com/hajimehoshi/ebiten/v2\tv2.9.9\t' in text
        infos[platform] = digest(path.read_bytes())
    files = sorted([*args.source.glob('*.go'), *args.source.glob('go.*')])
    assert files and (args.source / 'go.work') in files
    sources = {p.name: digest(p.read_bytes()) for p in files if p.is_file()}
    result = {'status': 'PASS_BUILD_STRUCTURE', 'binaries': binaries, 'build_info_sha256': infos,
              'source_files': sources, 'limits': ['未驗macOS真機', '未驗Windows真機',
                                                '非正式封包或全文中文化收據']}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
