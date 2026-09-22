#!/usr/bin/env python3
"""報告譯稿與正常路徑顯示的不同分母；不輸出原文或原版畫面。"""
import argparse
import json
from pathlib import Path

from validate_translation_draft import read_catalog, validate_sources


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--menu-receipt', type=Path, required=True)
    p.add_argument('--lifecycle-receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    rows = read_catalog(args.catalog)
    missing = sorted({row['source_file'] for row in rows if not (args.game / row['source_file']).is_file()})
    if missing:
        print('SKIP：缺少合法原版：' + '、'.join(missing))
        return 77
    validate_sources(rows, args.game)
    menu = json.loads(args.menu_receipt.read_text())
    lifecycle = json.loads(args.lifecycle_receipt.read_text())
    catalog = {row['candidate_id'] for row in rows}
    events = menu['events']
    if menu.get('all_menu') is not True or not events:
        raise ValueError('需要已驗證的五列正常路徑收據')
    observed = {event['candidate_id'] for event in events if event['accepted']}
    if not observed.issubset(catalog):
        raise ValueError('已接受的執行事件有未建檔鍵')
    frame_keys = {line['candidate_id'] for frame in menu['frames'] for line in frame['lines']
                  if line['applied']}
    if not frame_keys.issubset(observed):
        raise ValueError('合成畫面含未觀測的文字鍵')
    source_hashes = {row['source_bytes_sha256'] for row in rows}
    unmatched = {event['source_sha256'] for event in lifecycle['events']
                 if event['source_sha256'] not in source_hashes}
    result = {
        'catalog_source_validated': len(rows),
        'catalog_translation_drafts': sum(bool(row['zh_hant'].strip()) for row in rows),
        'normal_route_accepted_keys': len(observed),
        'normal_route_translated_frame_keys': len(frame_keys),
        'normal_route_unmatched_source_fragments': len(unmatched),
        'catalog_without_this_route_hit': len(catalog - observed),
        'scope': '只涵蓋目前兩份固定正常路徑收據；未建立全遊戲文字分母',
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
