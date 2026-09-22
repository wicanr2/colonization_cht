#!/usr/bin/env python3
"""唯讀核對既有正常路徑的五列證據；輸出只含定位與量測，不含原版素材。"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(report, directory):
    rows = []
    for source in ('6F16:00DF', '6F16:0111', '6F16:0141', '6F16:016D', '6F16:018F'):
        events = [e for e in report['events'] if e['source'] == source]
        if len(events) != 3:
            raise ValueError('每列必須有三次已完成事件：' + source)
        first = events[0]
        x, y = first['registers'][0], first['registers'][2]
        # 與已確認首列相同的 7 邏輯像素高候選；下方保留 1 像素列距。
        # 此為量測候選，不將腳本輸出自動升格為 READY 規格。
        safe = [x, y, 232, y + 7]
        region = [yy * 320 + xx for yy in range(y, y + 7) for xx in range(x, 232)]
        reference = None
        samples = []
        for event in events:
            prefix = directory / Path(event['capture']).name
            before = Path(str(prefix) + '.before').read_bytes()
            after = Path(str(prefix) + '.after').read_bytes()
            if len(before) != 64000 or len(after) != 64000:
                raise ValueError('畫布尺寸不符')
            if sha(before) != event['before_sha256'] or sha(after) != event['after_sha256']:
                raise ValueError('畫布指紋不符')
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            if changed != event['changed_indices'] or not changed:
                raise ValueError('事件差異不符')
            if not set(changed).issubset(region) or any(after[i] != 254 for i in changed):
                raise ValueError('墨跡越界或顏色不符')
            if event['entry_ip'] != '937C:0538' or event['return_ip'] != '937C:1D50':
                raise ValueError('入口／返回不符')
            if event['return_sp'] != event['entry_sp'] + 10 or not event['nul_terminated']:
                raise ValueError('堆疊／終止條件不符')
            current = (bytes(before[i] for i in region), bytes(after[i] for i in region))
            if reference is None:
                reference = current
            if current != reference:
                raise ValueError('重繪背景或墨跡變更')
            visible = {}
            for frame in report['frames']:
                if frame['step'] < event['return_step']:
                    continue
                data = (directory / (Path(frame['prefix']).name + '.idx')).read_bytes()
                visible[frame['label']] = bytes(data[i] for i in region) == current[1]
            samples.append({'entry_step': event['entry_step'], 'return_step': event['return_step'],
                            'pixels': len(changed), 'safe_visible': visible})
        rows.append({'source': source, 'source_sha256': first['source_sha256'],
                     'source_candidates': first['source_candidates'],
                     'bbox_inclusive': first['bbox_inclusive'], 'safe_candidate': safe,
                     'before_safe_sha256': sha(reference[0]), 'after_safe_sha256': sha(reference[1]),
                     'events': samples})
    return {'rows': rows, 'input_hashes': report['input_hashes'],
            'dosgolem_commit': report['dosgolem_commit'],
            'limitations': ['來源檔位移仍屬 bytes 對應；未新增載入器資料流證據',
                            '安全框為待審查候選；未證實五種選項分支可玩',
                            '此為既有收據再分析，不冒稱本輪重新執行原版']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    # 後續解析回填護欄：固定DOS映像／原始入口／新增來源對應規格012，舊規格009須有入口。
    repo = Path(__file__).resolve().parents[1]
    old_spec = (repo / 'docs/spec/009-first-text-overlay-draft.md').read_text()
    new_spec = (repo / 'docs/spec/012-five-menu-lines.md').read_text()
    if '後續解析回填' not in old_spec or '012-five-menu-lines.md' not in old_spec:
        raise ValueError('規格009缺少後續解析回填入口')
    for anchor in ['937C:0538', '937C:1D50', '6F16:0111', '6F16:0141', '6F16:016D', '6F16:018F']:
        if anchor not in new_spec:
            raise ValueError('規格012缺少原始定位：' + anchor)
    first = verify(json.loads((args.reports / 'goal056-lifecycle-analysis.json').read_text()), args.reports)
    second = verify(json.loads((args.reports / 'goal056-lifecycle-replay-analysis.json').read_text()), args.reports)
    if first != second:
        raise ValueError('兩次原版收據量測不一致')
    first['two_runs_equal'] = True
    first['analyzer_sha256'] = sha(Path(__file__).read_bytes())
    args.output.write_text(json.dumps(first, ensure_ascii=False, indent=2) + '\n')
    print('五列、每列三次重繪、雙次收據與安全區量測一致')


if __name__ == '__main__':
    main()
