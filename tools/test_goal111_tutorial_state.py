#!/usr/bin/env python3
"""目標111收據的正例、缺原版與來源／狀態篡改反例。"""

import argparse
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_goal111_tutorial_state import FIXTURE_SHA, check


class Goal111ReceiptTests(unittest.TestCase):
    game: Path
    inputs: Path
    fixtures: Path
    reports: Path

    def test_fixed_receipt(self):
        self.assertEqual(check(self.game, self.inputs, self.fixtures,
                               self.reports)["result"], "PASS")

    def test_missing_original_skips(self):
        self.assertEqual(check(Path("/missing-goal111-original"), self.inputs,
                               self.fixtures, self.reports)["result"], "SKIP")

    def test_changed_event_fixture_fails(self):
        with tempfile.TemporaryDirectory(prefix="goal111-fixtures-") as name:
            copied = Path(name)
            for variant in FIXTURE_SHA:
                filename = f"goal111-{variant}.inputs.json"
                shutil.copyfile(self.fixtures / filename, copied / filename)
            target = copied / "goal111-tutorial-then-first-row.inputs.json"
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "玩家事件檔版本不符"):
                check(self.game, self.inputs, copied, self.reports)

    def test_changed_original_frame_fails(self):
        original = Path.read_bytes
        target = self.reports / "tutorial-then-first-row-explore.1375m.idx"

        def read_bytes(path):
            if path == target:
                return bytes(64000)
            return original(path)

        with patch.object(Path, "read_bytes", read_bytes):
            with self.assertRaisesRegex(ValueError, "原始 idx 不符"):
                check(self.game, self.inputs, self.fixtures, self.reports)

    def test_control_state_change_fails(self):
        original = Path.read_bytes
        target = self.reports / "first-row-only-control.json"
        altered = json.loads(target.read_bytes())
        altered["samples"]["1375m"]["memory_sha256"] = "0" * 64
        broken = json.dumps(altered).encode()

        def read_bytes(path):
            if path == target:
                return broken
            return original(path)

        with patch.object(Path, "read_bytes", read_bytes):
            with self.assertRaisesRegex(ValueError, "監看擾動"):
                check(self.game, self.inputs, self.fixtures, self.reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    Goal111ReceiptTests.game = args.game
    Goal111ReceiptTests.inputs = args.inputs
    Goal111ReceiptTests.fixtures = args.fixtures
    Goal111ReceiptTests.reports = args.reports
    return 0 if unittest.main(argv=[__file__], exit=False).result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
