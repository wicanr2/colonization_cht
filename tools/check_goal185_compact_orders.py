#!/usr/bin/env python3
"""精簡ORDERS六列正常GUI、色層、取消與原文回退驗收。"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import EXPECTED, read, sha

CHECKER_SHA = 'fbb825b7a0de1060260ab4e4113f2bd67f8a4c4ea0cb6e976f30b877c03088ff'
INPUT_SHA = 'f30ad4a12957619cb73b1f05097fa40705653ac4610b5c695280ab88b2c1b80b'
MENU_SHA = '5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    expected = dict(EXPECTED, **{'MENU.TXT': MENU_SHA})
    if not all((a.game / name).is_file() for name in expected):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    for name, digest in expected.items():
        assert sha(a.game / name) == digest, name
    checker = a.reports / 'check_orders_compact_issue56_retained.py'
    assert sha(checker) == CHECKER_SHA, '私用原版收據檢查器指紋不符'
    assert sha(a.reports / 'orders-compact-formal-gui/gui.inputs.json') == INPUT_SHA
    with tempfile.TemporaryDirectory(prefix='colonization-compact-orders-') as temporary:
        output = a.output or Path(temporary) / 'review.json'
        subprocess.run([sys.executable, str(checker), '--reports', str(a.reports),
                        '--output', str(output)], check=True, timeout=120)
        assert read(output)['status'] == 'PASS_COMPACT_ORDERS_FORMAL'
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
