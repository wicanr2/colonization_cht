#!/usr/bin/env python3
"""回合結束重印背景、原版彈窗外框與長建造回歸驗收。"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import EXPECTED, read, sha

CHECKER_SHA = 'd28477eb7e86c6198f3df10b3edc7044175a05bf7edaf7a9054897512a13c816'
INPUT_SHA = '0c7732fb37d511df234028a3801b439067000ebc61c40120468984879be24e01'


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
    checker = args.reports / 'check_reprint_frame_formal.py'
    assert sha(checker) == CHECKER_SHA, '本機原版驗收腳本指紋不符'
    assert sha(args.reports / 'reprint-status-formal-gui/gui.inputs.json') == INPUT_SHA
    with tempfile.TemporaryDirectory(prefix='colonization-reprint-background-') as temporary:
        output = args.output or Path(temporary) / 'review.json'
        subprocess.run([sys.executable, str(checker), '--reports', str(args.reports),
                        '--output', str(output)], check=True, timeout=120)
        assert read(output)['status'] == 'PASS_REPRINT_FRAME_FORMAL'
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
