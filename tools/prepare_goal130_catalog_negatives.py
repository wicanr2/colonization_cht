#!/usr/bin/env python3
"""只在已忽略工作區產生首張字幕缺譯與重複鍵的測試語料。"""
import argparse
import csv
import hashlib
import os
from pathlib import Path


KEY = 'GAME.TXT:0x000153CC'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not args.output.is_dir() or args.output.stat().st_uid != os.getuid():
        raise ValueError('輸出目錄不存在或擁有者不符')
    raw = args.source.read_bytes()
    with args.source.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        fields, rows = reader.fieldnames, list(reader)
    matching = [row for row in rows if row['candidate_id'] == KEY]
    if len(matching) != 1 or matching[0]['zh_hant'] != '^^主後一千四百九十二年，':
        raise ValueError('正式測試鍵或譯稿已變更，需重新審查')
    for variant in ('blank', 'duplicate'):
        output = args.output / f'catalog-{variant}.tsv'
        if output.exists():
            raise FileExistsError(output)
        altered = [dict(row) for row in rows]
        if variant == 'blank':
            next(row for row in altered if row['candidate_id'] == KEY)['zh_hant'] = ''
        else:
            altered.append(dict(matching[0]))
        with output.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(altered)
        print(variant, hashlib.sha256(output.read_bytes()).hexdigest())
    print('現行語料 SHA-256', hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main()
