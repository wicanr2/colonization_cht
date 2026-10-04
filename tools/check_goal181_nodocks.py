#!/usr/bin/env python3
"""Docker內驗收正常職業清單選漁夫的未建碼頭提示。"""
import argparse
import json
from pathlib import Path

from check_goal178_ship import ORIGINALS
from check_goal181_purchase import verify as verify_flow

EVIDENCE_SHA = '574bac53bd0b5e55ee46a977789153571e03550ee9e15324b5fac6e522732e25'


def verify(game, root, evidence):
    return verify_flow(game, root, evidence, evidence_sha=EVIDENCE_SHA, field_count=1, shot_count=8,
                       require_purchase_layout=False,
                       scope='僅正常COLONY03進城、職業清單選漁夫的NODOCKS提示與關閉；不外推拖曳、其他工作者或單位選項')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'reports', 'evidence'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if any(not (args.game / name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版，不宣稱未建碼頭驗收通過')
        return 77
    try:
        result = verify(args.game, args.reports, args.evidence)
    except (ValueError, OSError, AssertionError, KeyError, TypeError, IndexError) as error:
        print('FAIL：' + str(error))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
