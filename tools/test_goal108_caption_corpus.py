#!/usr/bin/env python3
"""目標108：真原版正例與隔離副本負例；原版缺失時明示 SKIP。"""

import argparse
import csv
import json
import pathlib
import tempfile
import unittest

from check_goal108_caption_corpus import GAME_SHA, check
from validate_translation_draft import Invalid


class CaptionCorpusTests(unittest.TestCase):
    game = None
    catalog = None
    reports = None

    def test_missing_original_is_skip(self):
        with tempfile.TemporaryDirectory() as name:
            self.assertEqual(check(pathlib.Path(name), self.catalog, self.reports)["result"], "SKIP")

    def test_real_source_and_prints(self):
        receipt = check(self.game, self.catalog, self.reports)
        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["caption_count"], 10)
        self.assertEqual(receipt["source_line_count"], 11)
        self.assertEqual(receipt["game_sha256"], GAME_SHA)

    def test_wrong_game_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            directory = pathlib.Path(name)
            original = (self.game / "GAME.TXT").read_bytes()
            (directory / "GAME.TXT").write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            with self.assertRaisesRegex(Invalid, "版本不符"):
                check(directory, self.catalog, self.reports)

    def test_wrong_font_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            font = pathlib.Path(name) / "wrong.ttf"
            font.write_bytes(b"not the fixed font")
            with self.assertRaisesRegex(Invalid, "字型版本不符"):
                check(self.game, self.catalog, self.reports, font)

    def catalog_variant(self, folder, change):
        with self.catalog.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            rows = list(reader)
            fields = reader.fieldnames
        rows = change(rows)
        output = folder / "draft.tsv"
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return output

    def test_missing_caption_line_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            path = self.catalog_variant(pathlib.Path(name), lambda rows: [
                row for row in rows if row["byte_offset"] != "0x00015457"])
            with self.assertRaisesRegex(Invalid, "譯稿缺行"):
                check(self.game, path, self.reports)

    def test_changed_placeholder_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            def change(rows):
                for row in rows:
                    if row["byte_offset"] == "0x000154CB":
                        row["zh_hant"] = row["zh_hant"].replace("%STRING1", "%STRING2")
                return rows
            path = self.catalog_variant(pathlib.Path(name), change)
            with self.assertRaisesRegex(Invalid, "變數占位符"):
                check(self.game, path, self.reports)

    def test_print_content_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            folder = pathlib.Path(name)
            for suffix in ("explore", "b", "control"):
                source = self.reports / f"england-no-extra-1350m-{suffix}.json"
                target = folder / source.name
                target.write_bytes(source.read_bytes())
            report = json.loads((folder / "england-no-extra-1350m-explore.json").read_text())
            first_caption = next(item for item in report["print_reads"]
                                 if item["cs_ip"] == "0D21:00C6" and
                                 item["step"] >= 88_689_021)
            first_caption["value"] ^= 1
            tampered = json.dumps(report).encode("utf-8")
            for suffix in ("explore", "b"):
                (folder / f"england-no-extra-1350m-{suffix}.json").write_bytes(tampered)
            with self.assertRaisesRegex(Invalid, "原版實際印字不符"):
                check(self.game, self.catalog, folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=pathlib.Path, required=True)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--reports", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if not (args.game / "GAME.TXT").is_file():
        print("SKIP：合法原版 GAME.TXT 缺失")
        return 77
    CaptionCorpusTests.game = args.game
    CaptionCorpusTests.catalog = args.catalog
    CaptionCorpusTests.reports = args.reports
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CaptionCorpusTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
