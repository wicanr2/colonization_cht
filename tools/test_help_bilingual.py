#!/usr/bin/env python3
"""不含原版文字的help語料欄位與控制碼回歸測試。"""

import tempfile
import unittest
from pathlib import Path

from build_help_bilingual import escape_text, read_tsv, translations, unescape_text


class HelpCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "translations.tsv"
        self.row = {
            "message_id": "TEST.TXT:@HELP1",
            "source_en": "^^Guide\\n^\\nUse {%STRING0} and {B}.",
        }

    def write(self, value):
        self.path.write_text("message_id\tzh_hant\nTEST.TXT:@HELP1\t" + value + "\n", encoding="utf-8")

    def test_controls_and_placeholder_preserved(self):
        self.write("^^說明\\n^\\n使用{%STRING0}及{B}。")
        result = translations([self.row.copy()], self.path, True)
        self.assertEqual(result[0]["zh_hant"], "^^說明\\n^\\n使用{%STRING0}及{B}。")

    def test_placeholder_changed_rejected(self):
        self.write("^^說明\\n^\\n使用{%STRING1}及{B}。")
        with self.assertRaisesRegex(ValueError, "占位符"):
            translations([self.row.copy()], self.path, True)

    def test_control_removed_rejected(self):
        self.write("^說明\\n^\\n使用{%STRING0}及{B}。")
        with self.assertRaisesRegex(ValueError, "控制碼"):
            translations([self.row.copy()], self.path, True)

    def test_duplicate_key_rejected(self):
        self.write("^^說明\\n^\\n使用{%STRING0}及{B}。")
        self.path.write_text(self.path.read_text() + self.path.read_text().splitlines()[1] + "\n")
        with self.assertRaisesRegex(ValueError, "重複"):
            translations([self.row.copy()], self.path, True)

    def test_bom_rejected(self):
        self.write("^^說明\\n^\\n使用{%STRING0}及{B}。")
        self.path.write_bytes(b"\xef\xbb\xbf" + self.path.read_bytes())
        with self.assertRaisesRegex(ValueError, "BOM"):
            read_tsv(self.path, ["message_id", "zh_hant"])

    def test_invalid_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, "跳脫"):
            unescape_text("bad\\x")

    def test_tab_round_trips_as_tsv_escape(self):
        source = "^\t\n{Row}"
        encoded = escape_text(source)
        self.assertEqual(encoded, "^\\t\\n{Row}")
        self.assertEqual(unescape_text(encoded), source)

    def test_tab_control_removed_rejected(self):
        row = {"message_id": "TEST.TXT:@HELP1", "source_en": "^\\t\\n{B}"}
        self.write("^\\n{B}")
        with self.assertRaisesRegex(ValueError, "控制碼"):
            translations([row], self.path, True)


if __name__ == "__main__":
    unittest.main()
