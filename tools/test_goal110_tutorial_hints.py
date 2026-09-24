#!/usr/bin/env python3
"""目標110收據的缺原版、錯事件檔與損壞原始畫面負例。"""

import argparse
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_goal110_tutorial_hints import FIXTURE_SHA, check


class Goal110ReceiptTests(unittest.TestCase):
    game: Path
    inputs: Path
    fixtures: Path
    reports: Path

    def test_fixed_receipt(self):
        self.assertEqual(check(self.game, self.inputs, self.fixtures,
                               self.reports)["result"], "PASS")

    def test_missing_original_skips(self):
        self.assertEqual(check(Path("/missing-goal110-original"), self.inputs,
                               self.fixtures, self.reports)["result"], "SKIP")

    def test_changed_event_fixture_fails(self):
        with tempfile.TemporaryDirectory(prefix="goal110-fixtures-") as name:
            copied = Path(name)
            for filename in FIXTURE_SHA:
                shutil.copyfile(self.fixtures / filename, copied / filename)
            target = copied / "goal110-toggle-tutorial.inputs.json"
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "事件檔版本不符"):
                check(self.game, self.inputs, copied, self.reports)

    def test_changed_original_frame_fails(self):
        original = Path.read_bytes
        target = self.reports / "toggle-explore.1325m.idx"

        def read_bytes(path):
            if path == target:
                return bytes(64000)
            return original(path)

        with patch.object(Path, "read_bytes", read_bytes):
            with self.assertRaisesRegex(ValueError, "原始 idx 不符"):
                check(self.game, self.inputs, self.fixtures, self.reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    Goal110ReceiptTests.game = args.game
    Goal110ReceiptTests.inputs = args.inputs
    Goal110ReceiptTests.fixtures = args.fixtures
    Goal110ReceiptTests.reports = args.reports
    return 0 if unittest.main(argv=[__file__], exit=False).result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
