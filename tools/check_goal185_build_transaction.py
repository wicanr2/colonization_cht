#!/usr/bin/env python3
"""15項建造清單正常導航、回退與舊12項回歸驗收。"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import EXPECTED, read, sha

CHECKER_SHA = '0783347134c4c7bce80a8d9d7d97bf4f4aecf7e7d007e40dc78e2324963d9d2b'
INPUT_SHA = 'df243a8d39ff39edae3f2ffb4a1afc48163dbf5a98b619c8ab013f411cc6d99f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    for name, digest in EXPECTED.items():
        assert sha(args.game / name) == digest, name
    checker = args.reports / 'check_build_transaction_issue56_retained.py'
    assert sha(checker) == CHECKER_SHA, '私用原版收據檢查器指紋不符'
    assert sha(args.reports / 'build-transaction-formal-gui/gui.inputs.json') == INPUT_SHA
    with tempfile.TemporaryDirectory(prefix='colonization-build-transaction-') as temporary:
        output = args.output or Path(temporary) / 'review.json'
        subprocess.run([sys.executable, str(checker), '--reports', str(args.reports),
                        '--output', str(output)], check=True, timeout=90)
        result = read(output)
        assert result['status'] == 'PASS_BUILD_TRANSACTION_FORMAL'
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
