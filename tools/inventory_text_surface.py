#!/usr/bin/env python3
"""以唯讀方式盤點DOS文字檔的粗略資料行；不輸出原文。"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    files = sorted(args.game.glob('*.TXT'))
    if not files:
        print('SKIP：沒有合法原版TXT輸入')
        return 77
    result = []
    for path in files:
        if not path.is_file():
            raise ValueError('文字輸入不是一般檔案：' + path.name)
        data = path.read_bytes()
        if len(data) > 16 * 1024 * 1024:
            raise ValueError('文字輸入超過盤點上限：' + path.name)
        lines = data.split(b'\r\n')
        if lines[-1] == b'':
            lines.pop()
        if b'\n' in b''.join(lines) or b'\r' in b''.join(lines):
            raise ValueError('存在非CRLF換行：' + path.name)
        data_lines = [line for line in lines if line and not line.startswith((b';', b'@'))]
        result.append({
            'file': path.name,
            'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data),
            'physical_lines': len(lines),
            'rough_data_lines': len(data_lines),
            'at_directives': sum(line.startswith(b'@') for line in lines),
            'high_bit_bytes': sum(byte > 127 for byte in data),
            'data_lines_with_percent': sum(b'%' in line for line in data_lines),
            'data_lines_with_caret': sum(b'^' in line for line in data_lines),
            'data_lines_with_tilde': sum(b'~' in line for line in data_lines),
        })
    report = {'files': result, 'file_count': len(result),
              'rough_data_lines': sum(item['rough_data_lines'] for item in result),
              'caution': '粗略資料行不是玩家顯示訊息數；未計EXE及靜態圖文，也未處理跨行整則語意'}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'file_count': report['file_count'],
                      'rough_data_lines': report['rough_data_lines']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
