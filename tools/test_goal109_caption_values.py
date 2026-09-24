#!/usr/bin/env python3
"""字幕變數草稿的正反例；所有原版副本僅建立在容器暫存目錄。"""

import argparse
from pathlib import Path
import tempfile
import unittest

from check_goal109_caption_values import Invalid, check, load_rows, lookup


class CaptionValueTests(unittest.TestCase):
    game = None
    catalog = None
    reports = None
    england_reports = None

    def test_verified_four_nations(self):
        result = check(self.game, self.catalog, self.reports, self.england_reports)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["draft_rows"], 24)

    def test_missing_original_is_skip(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(check(Path(temp), self.catalog, self.reports,
                                   self.england_reports)["result"], "SKIP")

    def test_wrong_original_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "NAMES.TXT").write_bytes((self.game / "NAMES.TXT").read_bytes())
            original = (self.game / "GAME.TXT").read_bytes()
            (root / "GAME.TXT").write_bytes(bytes([original[0] ^ 1]) + original[1:])
            with self.assertRaisesRegex(Invalid, "版本不符"):
                check(root, self.catalog, self.reports, self.england_reports)

    def _alter_catalog(self, before, after):
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "values.tsv"
            source = self.catalog.read_text(encoding="utf-8")
            self.assertIn(before, source)
            candidate.write_text(source.replace(before, after, 1), encoding="utf-8")
            with self.assertRaises(Invalid):
                check(self.game, candidate, self.reports, self.england_reports)

    def test_wrong_nation_rejected(self):
        self._alter_catalog("france\t@BUILD2\t%STRING0", "spain\t@BUILD2\t%STRING0")

    def test_wrong_placeholder_rejected(self):
        self._alter_catalog("spain\t@BUILD2\t%STRING1", "spain\t@BUILD2\t%STRING9")

    def test_missing_row_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "values.tsv"
            lines = self.catalog.read_text(encoding="utf-8").splitlines()
            candidate.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(Invalid, "四國各六筆"):
                check(self.game, candidate, self.reports, self.england_reports)

    def test_observed_article_must_match_original_print(self):
        self._alter_catalog("\tNetherlands\tthe Netherlands\t荷蘭\t",
                            "\tNetherlands\tNetherlands\t荷蘭\t")

    def test_lookup_mismatch_returns_no_candidate(self):
        rows = load_rows(self.catalog)
        self.assertEqual(lookup(rows, "netherlands", "@BUILD4", "%STRING0",
                                "the Netherlands"), "荷蘭")
        for args in (("france", "@BUILD4", "%STRING0", "the Netherlands"),
                     ("netherlands", "@BUILD4", "%STRING0", "Netherlands"),
                     ("netherlands", "@BUILD4", "%STRING1", "the Netherlands"),
                     ("netherlands", "@BUILD8", "%STRING0", "the Netherlands")):
            self.assertIsNone(lookup(rows, *args))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--england-reports", type=Path, required=True)
    args = parser.parse_args()
    CaptionValueTests.game = args.game
    CaptionValueTests.catalog = args.catalog
    CaptionValueTests.reports = args.reports
    CaptionValueTests.england_reports = args.england_reports
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CaptionValueTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
