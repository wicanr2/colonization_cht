#!/usr/bin/env python3
"""容器內重播目標056；文字位移搜尋僅候選，不冒稱載入來源資料流。"""
import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='goal056-lifecycle')
    parser.add_argument('--compare', help='另一次已完成的收據前綴，只比對不覆寫它')
    args = parser.parse_args()
    if any(not value.startswith('goal056-') or '/' in value or '\\' in value
           for value in [args.prefix, args.compare] if value is not None):
        raise SystemExit('輸出前綴必須是 goal056- 開頭的單一檔名')
    game, source, out = Path('/game'), Path('/dosgolem'), Path('/out')
    expected = {
        'OPENING.EXE': '3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39',
        'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
        'GAME.TXT': '67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a',
    }
    for name, sha in expected.items():
        if not (game / name).is_file():
            print('SKIP 缺原版輸入：' + name)
            raise SystemExit(77)
        if digest((game / name).read_bytes()) != sha:
            raise SystemExit('版本不符：' + name)
    assert (out.stat().st_uid, out.stat().st_gid) == (os.getuid(), os.getgid())
    assert all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid())
               for p in out.glob(args.prefix + '*'))
    commit = '22664265ea7d55ea8706448149908c79d3f0897b'
    with tempfile.TemporaryDirectory(prefix='colonization-lifecycle-') as temp:
        # 由固定提交建立容器暫存樹；不受後續工作樹變更影響。
        work = Path(temp) / 'source'
        work.mkdir()
        archive = subprocess.check_output(['git', '-C', str(source), 'archive', commit])
        subprocess.run(['tar', '-x', '-C', str(work)], input=archive, check=True)
        probe = work / 'cmd/lifecycle'
        probe.mkdir()
        shutil.copyfile('/repo/tools/trace_menu_lifecycle.go', probe / 'main.go')
        binary = str(Path(temp) / 'probe')
        subprocess.run(['go', 'build', '-o', binary, './cmd/lifecycle'], cwd=work, check=True, timeout=120)
        prefix = out / args.prefix
        command = [binary, '-root', str(game), '-out', str(prefix)]
        subprocess.run(command, check=True, timeout=120)
    record = json.loads(Path(str(prefix) + '.json').read_text())
    originals = {p.name: p.read_bytes() for p in game.iterdir()
                 if p.is_file() and p.suffix.upper() in ('.TXT', '.EXE')}
    for event in record['events'] or []:
        needle = bytes.fromhex(event['source_hex'])
        candidates = []
        if needle:
            for name, data in originals.items():
                start = 0
                while (offset := data.find(needle, start)) >= 0:
                    candidates.append({'file': name, 'offset': hex(offset), 'file_sha256': digest(data),
                                       'level': 'candidate-byte-match-only'})
                    start = offset + 1
        event['source_candidates'] = candidates
        after = Path(event['capture'] + '.after').read_bytes()
        event['visibility'] = []
        changes = event['changed_indices'] or []
        for frame in record['frames']:
            if frame['step'] < event['return_step']:
                continue
            image = Path(frame['prefix'] + '.idx').read_bytes()
            same = sum(image[i] == after[i] for i in changes)
            event['visibility'].append({'frame': frame['label'], 'matching_changed_pixels': same,
                                        'changed_pixels': len(changes),
                                        'all_changed_pixels_survive': bool(changes) and same == len(changes)})
    record['dosgolem_commit'] = commit
    record['input_hashes'] = expected
    record['probe_source_sha256'] = digest(Path('/repo/tools/trace_menu_lifecycle.go').read_bytes())
    record['limitations'] = ['入口僅937C:0538；沒有命中不代表沒有文字',
                            '候選檔案位移僅原始bytes相等，未完成載入來源追蹤',
                            'changed-pixel存續不是全部背景或整則訊息可見性的充分證據']
    # 第一則輸出後來的重繪，逐像素比較安全區，區分背景與墨跡。
    region = [y * 320 + x for y in range(107, 114) for x in range(86, 232)]
    first = next((e for e in record['events'] or [] if e['source'] == '6F16:00DF'), None)
    if first:
        first_before = Path(first['capture'] + '.before').read_bytes()
        first_after = Path(first['capture'] + '.after').read_bytes()
        ink = set(first['changed_indices'] or [])
        record['first_line_lifecycle'] = []
        for e in record['events']:
            if e['source'] != first['source'] or e['source_sha256'] != first['source_sha256']:
                continue
            before = Path(e['capture'] + '.before').read_bytes()
            after = Path(e['capture'] + '.after').read_bytes()
            record['first_line_lifecycle'].append({
                'entry_step': e['entry_step'], 'return_step': e['return_step'],
                'before_safe_rect_changed_from_initial': sum(before[i] != first_before[i] for i in region),
                'after_safe_rect_changed_from_initial': sum(after[i] != first_after[i] for i in region),
                'old_ink_pixels_remaining_at_entry': sum(before[i] == first_after[i] for i in ink),
                'non_ink_background_changed': sum(before[i] != first_before[i] for i in region if i not in ink),
                'draw_colors': e['changed_colors'], 'entry_sp': e['entry_sp'], 'return_sp': e['return_sp'],
            })
    Path(str(prefix) + '-analysis.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    if args.compare:
        other_prefix = out / args.compare
        other = json.loads(Path(str(other_prefix) + '-analysis.json').read_text())
        def normalized(value, prefix):
            return json.dumps(value, ensure_ascii=False, sort_keys=True).replace(str(prefix), '<PREFIX>')
        comparisons = {}
        for path in out.glob(args.prefix + '.*'):
            if path.suffix == '.json':
                continue
            peer = Path(str(other_prefix) + str(path)[len(str(prefix)):])
            comparisons[str(path)[len(str(prefix)):]] = peer.is_file() and path.read_bytes() == peer.read_bytes()
        comparison = {'normalized_receipts_equal': normalized(record, prefix) == normalized(other, other_prefix),
                      'binary_outputs_equal': comparisons, 'source_sha256': record['probe_source_sha256']}
        Path(str(prefix) + '-comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')
        if not comparison['normalized_receipts_equal'] or not comparisons or not all(comparisons.values()):
            raise SystemExit('雙次重播收據不一致')
    for i, event in enumerate(record['events'] or []):
        print(i, event['entry_step'], repr(bytes.fromhex(event['source_hex'])),
              event['bbox_inclusive'], len(event['changed_indices'] or []), event['near_return_candidate'])


if __name__ == '__main__':
    main()
