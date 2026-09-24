#!/usr/bin/env python3
"""目標112原版來源收據的正例與檔案、輸出、畫面負例。"""

import argparse
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from check_goal112_options_source import check, verify_observed


class Goal112SourceTests(unittest.TestCase):
    game: Path
    inputs: Path
    fixture: Path
    reports: Path

    @classmethod
    def setUpClass(cls):
        cls.record = json.loads((cls.reports / "source-v2-a.json").read_bytes())
        cls.game_data = (cls.game / "GAME.TXT").read_bytes()
        cls.indexed = (cls.reports / "source-v2-a.1300m.idx").read_bytes()

    def test_fixed_replay(self):
        self.assertEqual(check(self.game, self.inputs, self.fixture, self.reports)["result"], "PASS")

    def test_missing_original_skips(self):
        self.assertEqual(check(Path("/missing-goal112-original"), self.inputs,
                               self.fixture, self.reports)["result"], "SKIP")

    def test_changed_dos_transfer_fails(self):
        altered = copy.deepcopy(self.record)
        item = next(item for item in altered["transfers"] if item["file_offset"] == 0x566 and
                    item["step"] == 1253314011)
        item["match"] = False
        with self.assertRaisesRegex(ValueError, "DOS 目的緩衝不符"):
            verify_observed(altered, self.game_data, self.indexed)

    def test_changed_parser_read_fails(self):
        altered = copy.deepcopy(self.record)
        item = next(item for item in altered["option_source_reads"] if
                    item["cs_ip"] == "0E2D:1F76")
        item["value"] ^= 1
        with self.assertRaisesRegex(ValueError, "原版解析常式"):
            verify_observed(altered, self.game_data, self.indexed)

    def test_changed_print_fails(self):
        altered = copy.deepcopy(self.record)
        altered["print_reads"] = [item for item in altered["print_reads"]
                                  if item["step"] < 1253400000]
        with self.assertRaisesRegex(ValueError, "原版印字未依序顯示"):
            verify_observed(altered, self.game_data, self.indexed)

    def test_changed_original_frame_fails(self):
        with self.assertRaisesRegex(ValueError, "原版選項索引畫面不符"):
            verify_observed(self.record, self.game_data, bytes(64000))

    def test_control_state_change_fails(self):
        target = self.reports / "source-v2-control.json"
        altered = json.loads(target.read_bytes())
        altered["samples"]["1300m"]["memory_sha256"] = "0" * 64
        original = Path.read_bytes

        def read_bytes(path):
            return json.dumps(altered).encode() if path == target else original(path)

        with patch.object(Path, "read_bytes", read_bytes):
            with self.assertRaisesRegex(ValueError, "原版狀態受監看擾動"):
                check(self.game, self.inputs, self.fixture, self.reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    for name in ("game", "inputs", "fixture", "reports"):
        setattr(Goal112SourceTests, name, getattr(args, name))
    result = unittest.main(argv=[__file__], exit=False).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
