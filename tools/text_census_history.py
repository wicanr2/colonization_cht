#!/usr/bin/env python3
"""規格049：重驗可用收據，保留明確標示的歷史普查證據。"""
import argparse
import collections
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from text_census import LABELS, STATUSES
from verification_matrix import run_row

BASELINE_SHA = 'a2a7be55c47c3084527d6169627d80a9206970069170c830922d004a89999c3c'
METADATA_SHA = '7b1b8c10a523965333d7c6eedfbf16859fb85f552632f3e65c9bc3442495181e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    records = list(csv.DictReader(path.open(), delimiter='\t'))
    if len(records) != len({r['id'] for r in records}):
        raise ValueError('普查鍵重複')
    return {r['id']: r for r in records}


def merge(baseline, current, confirmed_unavailable=None):
    combined = {k: dict(v) for k, v in baseline.items()}
    current_shown = set()
    for key, record in current.items():
        if key not in combined:
            combined[key] = dict(record)
        if record['status'] == 'shown':
            combined[key] = dict(record)
            current_shown.add(key)
    for key in confirmed_unavailable or ():
        if key not in current or current[key]['reach'] != 'unreachable' or current[key]['status'] != 'unreachable':
            raise ValueError('已驗入口限制缺正確本輪分類：' + key)
        if key in baseline and baseline[key]['status'] == 'shown':
            raise ValueError('入口限制與歷史顯示衝突：' + key)
        combined[key] = dict(current[key])
        combined[key]['evidence'] = 'confirmed 正常類別入口限制'
    historical = set()
    for key, record in combined.items():
        if record['status'] == 'shown' and key not in current_shown:
            record['evidence'] = '歷史驗收：' + record['evidence']
            historical.add(key)
    return combined, current_shown, historical


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path('/repo'))
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    baseline_path = a.repo / 'docs/text-census-baseline.tsv'
    metadata_path = a.repo / 'docs/text-census-baseline.json'
    if sha(baseline_path) != BASELINE_SHA or sha(metadata_path) != METADATA_SHA:
        raise ValueError('歷史普查基準指紋不符')
    metadata = json.loads(metadata_path.read_text())
    for name, digest in metadata['originals'].items():
        if not (a.game / name).is_file():
            print('SKIP：缺合法原版輸入')
            return 77
        if sha(a.game / name) != digest:
            raise ValueError('原版版本不符：' + name)
    baseline = rows(baseline_path)
    if len(baseline) != metadata['baseline_rows'] or dict(collections.Counter(r['status'] for r in baseline.values())) != metadata['baseline_status']:
        raise ValueError('歷史普查列數或狀態不符')
    if not a.output.parent.is_dir() or a.output.parent.stat().st_uid != os.getuid():
        raise ValueError('輸出父目錄不存在或擁有者不符')
    a.output.mkdir(exist_ok=True)
    if a.output.stat().st_uid != os.getuid():
        raise ValueError('輸出目錄擁有者不符')
    config = json.loads((a.repo / 'tools/verification-matrix.json').read_text())
    historical_ids = set(metadata['historical_row_ids'])
    eligible = [r for r in config['rows'] if r['id'] not in historical_ids]
    checked = []
    for row in eligible:
        result = run_row(row, a)
        checked.append(result)
        print(row['id'] + ': ' + result['status'], file=sys.stderr, flush=True)
        if result['status'] != 'PASS':
            raise ValueError('本輪收據未通過：' + row['id'] + ' ' + result.get('error_tail', ''))
    # 既有五組同文來源仍受限；缺少來源查詢收據時，不能將模板鍵升為原始段落。
    protected = {cid: '強推論' for r in config['rows'] for cid in r.get('source_identity', {}).get('aliases', {}) if cid.startswith('PEDIA.TXT:')}
    eligible[0] = dict(eligible[0])
    eligible[0]['key_evidence'] = dict(eligible[0].get('key_evidence', {}), **protected)
    matrix = a.output / 'current-matrix.json'
    matrix.write_text(json.dumps({'rows': eligible}, ensure_ascii=False, indent=2) + '\n')
    current_path = a.output / 'current-census.tsv'
    command = [sys.executable, str(a.repo / 'tools/text_census.py'), '--game', str(a.game),
               '--text', str(a.repo / 'text'), '--reports', str(a.reports), '--matrix', str(matrix),
               '--map', str(a.repo / 'text/census-map.tsv'), '--census', str(current_path),
               '--report', str(a.output / 'current-census.md'), '--detail', str(a.output / 'current-detail.json')]
    proc = subprocess.run(command, capture_output=True, text=True)
    (a.output / 'current-command.json').write_text(json.dumps(command, indent=2) + '\n')
    (a.output / 'current-run.log').write_text(proc.stdout + proc.stderr)
    if proc.returncode != 0:
        raise ValueError(proc.stderr[-1800:] or proc.stdout[-1800:])
    current = rows(current_path)
    confirmed_unavailable = {key for row in checked
                             if row.get('census_scope', {}).get('unavailable_grade') == 'confirmed'
                             for key in row['census_scope'].get('unavailable_source_ids', [])}
    combined, current_shown, historical = merge(baseline, current, confirmed_unavailable)
    header = list(next(iter(baseline.values())))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(combined[key] for key in sorted(combined))
    target = a.output / 'text-census.tsv'
    target.write_text(buf.getvalue())
    totals = collections.Counter(r['status'] for r in combined.values())
    by = collections.defaultdict(collections.Counter)
    for record in combined.values():
        by[record['screen']][record['status']] += 1
    summary = {
        'result': 'PASS_CENSUS_HISTORY', 'matrix_rows': len(config['rows']), 'checked_rows': len(checked),
        'historical_rows': len(historical_ids), 'rows': len(combined), 'status': dict(totals),
        'current_shown': len(current_shown), 'historical_only_shown': len(historical),
        'new_shown': sorted(k for k, r in combined.items() if r['status'] == 'shown' and (k not in baseline or baseline[k]['status'] != 'shown')),
        'baseline_sha256': BASELINE_SHA, 'metadata_sha256': METADATA_SHA,
        'census_sha256': sha(target), 'current_census_sha256': sha(current_path),
        'matrix_sha256': sha(a.repo / 'tools/verification-matrix.json'),
        'confirmed_unavailable_ids': sorted(confirmed_unavailable),
    }
    lines = ['# 全可達文字普查', '',
             '由 `tools/text_census_history.py` 依規格049、歷史基準與本輪通過檢查器的收據產生；不要手改。', '',
             f'- 矩陣設定{summary["matrix_rows"]}列：本輪重驗PASS {summary["checked_rows"]}列；另{summary["historical_rows"]}列只保留歷史驗收，未宣稱全矩陣新PASS。',
             f'- 分母{len(combined)}項；已顯示{totals["shown"]}、待驗{totals["pending"]}、不可達{totals["unreachable"]}。',
             f'- 已顯示中，本輪可重驗{len(current_shown)}項；僅歷史證據{len(historical)}項。歷史證據在TSV的evidence欄明列。',
             f'- 本輪新增{len(summary["new_shown"])}項已驗欄位，不把容量、模板載入或同文TERRAIN23提高為原始來源完成。',
             '- 待驗表示尚無對應畫面證據，不能當成缺譯數。欄位範圍外的未套用診斷另保留在私用明細，不能單凭它宣稱玩家仍看到英文。', '',
             '| 畫面 | ' + ' | '.join(LABELS[s] for s in STATUSES) + ' |', '|---|' + '---:|' * len(STATUSES)]
    lines += ['| ' + screen + ' | ' + ' | '.join(str(by[screen][status]) for status in STATUSES) + ' |' for screen in sorted(by)]
    lines += ['', '## 證據入口', '',
              '- [歷史基準](text-census-baseline.tsv)與[完整來源指紋](text-census-baseline.json)。',
              '- [規格049](spec/049-census-history.md)及[目標185](goals/185-player-experience.md)。',
              f'- 原版像素、音訊、存檔、含原文明細與本輪{summary["checked_rows"]}列重驗結果只留workplace。', '']
    (a.output / 'text-census.md').write_text('\n'.join(lines))
    (a.output / 'checked-matrix.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2) + '\n')
    (a.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
