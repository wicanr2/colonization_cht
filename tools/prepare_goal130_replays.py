#!/usr/bin/env python3
"""由真 Ebitengine 錄製輸入衍生字幕逐幀驗收用的有界前綴；不合成輸入。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not args.output.is_dir() or args.output.stat().st_uid != os.getuid():
        raise ValueError('輸出目錄不存在或擁有者不符')
    raw = args.source.read_bytes()
    source = json.loads(raw)
    if hashlib.sha256(raw).hexdigest() != 'dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98' or \
            source['end'] != 1350000000 or len(source['inputs']) != 33:
        raise ValueError('非既有完整真視窗輸入')
    if any(a['step'] > b['step'] for a, b in zip(source['inputs'], source['inputs'][1:])):
        raise ValueError('輸入順序錯誤')
    for end in (82000000, 86000000, 88770000, 89760000, 120000000, 195000000, 196000000):
        selected = [event for event in source['inputs'] if event['step'] <= end]
        expected_count, expected_last = (24, 75200000) if end == 82000000 else (25, 85200000)
        if len(selected) != expected_count or selected[-1]['step'] != expected_last:
            raise ValueError('字幕前綴輸入數量或末項不符')
        output = args.output / f'window-prefix-{end}.inputs.json'
        payload = json.dumps({'inputs': selected, 'end': end}, ensure_ascii=False,
                             sort_keys=True, indent=2) + '\n'
        if output.exists():
            if output.read_text(encoding='utf-8') != payload:
                raise ValueError(f'既有前綴不符：{output}')
        else:
            output.write_text(payload, encoding='utf-8')
        print(end, hashlib.sha256(output.read_bytes()).hexdigest())
    # 唯一合成測試輸入：由真錄製前綴加一筆可辨識的游標移動，不當作真玩家收據。
    cursor = [event for event in source['inputs'] if event['step'] <= 82000000]
    cursor.append({'step': 81000000, 'kind': 'move', 'x': 160, 'y': 35, 'button': 0})
    output = args.output / 'window-prefix-82000000-cursor.inputs.json'
    payload = json.dumps({'inputs': cursor, 'end': 82000000}, ensure_ascii=False,
                         sort_keys=True, indent=2) + '\n'
    if output.exists():
        if output.read_text(encoding='utf-8') != payload:
            raise ValueError('既有游標負例輸入不符')
    else:
        output.write_text(payload, encoding='utf-8')
    print('cursor-negative', hashlib.sha256(output.read_bytes()).hexdigest())
    print('真視窗原始輸入 SHA-256', hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main()
