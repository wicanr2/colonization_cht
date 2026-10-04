#!/usr/bin/env python3
"""規格043：macOS 通用檔、臨時簽章、啟動器與 ZIP 封裝。"""
import copy
import hashlib
import io
import json
import stat
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def need(ok, message):
    if not ok:
        raise ValueError(message)


def slices(data):
    need(len(data) >= 48, '通用檔太短')
    magic, count = struct.unpack_from('>II', data)
    need(magic == 0xcafebabe and count == 2, '需要兩個 universal 切片')
    result, spans = {}, []
    for i in range(count):
        cpu, subtype, start, size, align = struct.unpack_from('>5I', data, 8 + 20*i)
        need(cpu in (0x1000007, 0x100000c) and cpu not in result, '切片架構不同或重複')
        need(align <= 30 and start >= 48 and start % (1 << align) == 0 and size >= 32
             and start + size <= len(data), '切片範圍或對齊錯誤')
        thin = data[start:start+size]
        need(struct.unpack_from('<III', thin) == (0xfeedfacf, cpu, subtype), '切片標頭不同')
        result[cpu] = thin
        spans.append((start, start+size))
    spans.sort()
    need(spans[0][1] <= spans[1][0], '切片重疊')
    need(spans[-1][1] == len(data) and not any(data[48:spans[0][0]])
         and not any(data[spans[0][1]:spans[1][0]]), '切片外有非預期資料')
    return result


def inspect_thin(data, cpu):
    header = struct.unpack_from('<8I', data)
    need(header[0] == 0xfeedfacf and header[1] == cpu and header[3] == 2, '非預期 Mach-O executable')
    count, total = header[4:6]
    need(32 + total <= len(data), '載入命令越界')
    pos, signatures, dylibs, segments, versions = 32, [], [], {}, []
    for _ in range(count):
        need(pos + 8 <= 32 + total, '載入命令標頭越界')
        cmd, size = struct.unpack_from('<II', data, pos)
        need(size >= 8 and pos + size <= 32 + total, '載入命令越界')
        if cmd == 0x1d:
            need(size == 16, '簽章命令長度不同')
            signatures.append(struct.unpack_from('<II', data, pos+8))
        elif cmd == 0x19:
            need(size >= 72, '段落命令太短')
            name = data[pos+8:pos+24].split(b'\0')[0].decode('ascii')
            need(name not in segments, '重複段落')
            segments[name] = struct.unpack_from('<QQ', data, pos+40)
        elif cmd in (0xc, 0x18 | 0x80000000, 0x1f | 0x80000000):
            need(size >= 24, '函式庫命令太短')
            offset, = struct.unpack_from('<I', data, pos+8)
            need(24 <= offset < size and b'\0' in data[pos+offset:pos+size], '函式庫名稱越界')
            name = data[pos+offset:pos+size].split(b'\0')[0].decode('utf-8')
            need(name.startswith(('/usr/lib/', '/System/Library/Frameworks/')), '非系統函式庫：'+name)
            dylibs.append(name)
        elif cmd == 0x32:
            need(size >= 24, '版本命令太短')
            platform, minimum, sdk, ntools = struct.unpack_from('<4I', data, pos+8)
            need(platform == 1 and size >= 24+ntools*8, '非 macOS 版本命令')
            versions.append((minimum, sdk))
        elif cmd == 0x24:
            need(size == 16, '版本命令長度不同')
            versions.append(struct.unpack_from('<II', data, pos+8))
        pos += size
    need(pos == 32+total and len(signatures) == 1 and len(versions) == 1, '缺簽章或版本命令')
    start, size = signatures[0]
    need(size >= 20 and start >= 32+total and start+size == len(data), '簽章範圍不同')
    link_start, link_size = segments.get('__LINKEDIT', (0, 0))
    need(link_start <= start and start+size <= link_start+link_size, '簽章不在 LINKEDIT')
    sb = data[start:start+size]
    need(struct.unpack_from('>III', sb) == (0xfade0cc0, size, 1), '非單一 CodeDirectory 臨時簽章')
    slot, offset = struct.unpack_from('>II', sb, 12)
    need(slot == 0 and 20 <= offset <= size-88, 'CodeDirectory 索引不同')
    cd = sb[offset:]
    magic, length, version, flags, hashes, ident, special, slots, limit = struct.unpack_from('>9I', cd)
    hash_size, hash_type, spare, bits = struct.unpack_from('>4B', cd, 36)
    need(magic == 0xfade0c02 and length == len(cd) and version == 0x20400, 'CodeDirectory 格式不同')
    need(flags == 0x20002 and special == 0 and limit == start and hash_size == 32
         and hash_type == 2 and spare == 0 and bits == 12, '簽章模式或頁條件不同')
    need(88 <= ident < hashes and b'\0' in cd[ident:hashes], '簽章識別字越界')
    identifier = cd[ident:hashes].split(b'\0')[0].decode('utf-8')
    need(bool(identifier), '空簽章識別字')
    need(slots == (limit+4095)//4096 and hashes+slots*32 == length, '簽章頁數不同')
    need(cd[40:64] == bytes(24), '非預期的特殊簽章欄位')
    base, exec_limit, exec_flags = struct.unpack_from('>QQQ', cd, 64)
    need((base, exec_limit) == segments.get('__TEXT') and exec_flags == 1, '可執行段落簽章不同')
    for i in range(slots):
        expected = hashlib.sha256(data[i*4096:min((i+1)*4096, limit)]).digest()
        need(cd[hashes+32*i:hashes+32*(i+1)] == expected, '簽署頁雜湊不同：'+str(i))
    v = lambda n: f'{n>>16}.{(n>>8)&255}.{n&255}'
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'load_version': {'minimum': v(versions[0][0]), 'sdk': v(versions[0][1])},
            'signature': {'kind': 'adhoc-linker-signed', 'identifier': identifier,
                          'code_directory_sha256': hashlib.sha256(cd).hexdigest(),
                          'signed_pages': slots, 'page_bytes': 4096, 'all_page_hashes_match': True},
            'system_libraries': sorted(dylibs)}


def check(binary):
    thin = slices(Path(binary).read_bytes())
    reports, dependencies = {}, []
    with tempfile.TemporaryDirectory() as directory:
        for cpu, arch in ((0x1000007, 'amd64'), (0x100000c, 'arm64')):
            data = thin[cpu]
            report = inspect_thin(data, cpu)
            path = Path(directory)/arch
            path.write_bytes(data)
            metadata = subprocess.run(['go', 'version', '-m', str(path)], check=True,
                                      capture_output=True, text=True).stdout
            lines = [line.split() for line in metadata.splitlines()[1:]]
            build = dict(line.strip().split(None, 1)[1].split('=', 1) for line in metadata.splitlines()[1:]
                         if line.strip().startswith('build\t') and '=' in line)
            need(metadata.splitlines()[0].split()[-1] == 'go1.26.7', 'Go 版本不同')
            need(build.get('GOOS') == 'darwin' and build.get('GOARCH') == arch
                 and build.get('CGO_ENABLED') == '1', '建置平台不同')
            deps = [line[1:] for line in lines if line and line[0] == 'dep']
            need(['github.com/hajimehoshi/ebiten/v2', 'v2.9.9'] in [line[:2] for line in deps], '前端依賴版本不同')
            report['go_build'] = build
            report['dependencies'] = deps
            reports[arch] = report
            dependencies.append(deps)
    need(dependencies[0] == dependencies[1], '兩側依賴不同')
    need(reports['amd64']['system_libraries'] == reports['arm64']['system_libraries'], '兩側系統依賴不同')
    return {'status': 'PASS_MACOS_UNIVERSAL_SIGNATURE_STRUCTURE', 'slices': reports,
            'sha256': hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
            'limits': ['未執行 macOS 二進位', '未驗真機、Gatekeeper 或最低系統相容性',
                       '臨時簽章不含 Developer ID 或 Apple 公證']}


def macos_notices(binary, repo, notice_reader):
    """逐切片讀取實際依賴授權，不以 fat 檔第一側推定另一側。"""
    report = check(binary)
    thin = slices(Path(binary).read_bytes())
    results = []
    with tempfile.TemporaryDirectory() as directory:
        for cpu, arch in ((0x1000007, 'amd64'), (0x100000c, 'arm64')):
            path = Path(directory)/arch
            path.write_bytes(thin[cpu])
            results.append(notice_reader(path, repo, ('darwin', arch)))
    need(results[0] == results[1], '兩側依賴或授權內容不同')
    return *results[0], report


def macos_launcher(source):
    old = 'save=${COLONIZATION_CHT_SAVE:-${XDG_DATA_HOME:-$HOME/.local/share}/colonization-cht/save}'
    need(source.startswith('#!/usr/bin/env bash\n') and source.count(old) == 1
         and source.count('"${args[@]}"') == 1, '共用啟動器結構已改變')
    return source.replace('#!/usr/bin/env bash', '#!/bin/bash', 1).replace(
        old, 'save=${COLONIZATION_CHT_SAVE:-$HOME/Library/Application Support/colonization-cht/save}').replace(
        '~/.local/share/colonization-cht/save', '~/Library/Application Support/colonization-cht/save').replace(
        '"${args[@]}"', '${args[@]+"${args[@]}"}')


def build_macos_zip(files, manifest, top, linux_launcher):
    payload = dict(files)
    payload.pop('MANIFEST.json', None)
    payload['colonization-cht.sh'] = (macos_launcher(linux_launcher).encode(), 0o755)
    bundled = copy.deepcopy(manifest)
    bundled['format'] = 'macOS-ZIP'
    bundled['launcher_source_sha256'] = hashlib.sha256(linux_launcher.encode()).hexdigest()
    bundled['zip_timestamp'] = '1980-01-01T00:00:00'
    bundled['files'] = {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                        for name, (data, mode) in sorted(payload.items())}
    payload['MANIFEST.json'] = ((json.dumps(bundled, ensure_ascii=False, indent=1, sort_keys=True)+'\n').encode(), 0o644)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, (data, mode) in sorted(payload.items()):
            path = PurePosixPath(name)
            need(not path.is_absolute() and '..' not in path.parts, '非法包內路徑：'+name)
            entry = zipfile.ZipInfo(top+'/'+name, date_time=(1980,1,1,0,0,0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | mode) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data, compresslevel=9)
    return output.getvalue(), bundled


if __name__ == '__main__':
    import sys
    print(json.dumps(check(sys.argv[1]), ensure_ascii=False, indent=1))
