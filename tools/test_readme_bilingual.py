"""不含原版文字的 README 雙語語料欄位與操作字面值回歸測試。"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from build_readme_bilingual import (
    SOURCE_MEMBER,
    digest,
    digest_file,
    source_rows,
    translations,
    validate_spans,
)


class ReadmeCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "translations.tsv"
        self.row = {
            "message_id": "README.TXT:CHEAT_COLONY",
            "source_en": "T = add\\nS = change\\n$ = gold\\n% = goods\\n^ = remove\\n! = buildings\\nSpace = turn\\n\\tcontinued",
        }

    def write(self, value):
        serialized = value.replace("\t", "\\t").replace("\n", "\\n")
        self.path.write_text(
            "message_id\tzh_hant\nREADME.TXT:CHEAT_COLONY\t" + serialized + "\n",
            encoding="utf-8",
        )

    def test_operation_literals_and_tab_preserved(self):
        self.write("T = 加入\nS = 變更\n$ = 金幣\n% = 貨物\n^ = 移除\n! = 建築\nSpace = 回合\n\t續行")
        result = translations([self.row.copy()], self.path, True)
        self.assertIn("Space =", result[0]["zh_hant"])

    def test_operation_literal_reordered_rejected(self):
        self.write("S = 變更\nT = 加入\n$ = 金幣\n% = 貨物\n^ = 移除\n! = 建築\nSpace = 回合\n\t續行")
        with self.assertRaisesRegex(ValueError, "操作按鍵"):
            translations([self.row.copy()], self.path, True)

    def test_symbol_removed_rejected(self):
        self.write("T = 加入\nS = 變更\n$ = 金幣\n貨物\n^ = 移除\n! = 建築\nSpace = 回合\n\t續行")
        with self.assertRaisesRegex(ValueError, "操作按鍵或符號"):
            translations([self.row.copy()], self.path, True)

    def test_tab_removed_rejected(self):
        self.write("T = 加入\nS = 變更\n$ = 金幣\n% = 貨物\n^ = 移除\n! = 建築\nSpace = 回合\n續行")
        with self.assertRaisesRegex(ValueError, "Tab"):
            translations([self.row.copy()], self.path, True)

    def test_overlapping_spans_rejected(self):
        with self.assertRaisesRegex(ValueError, "範圍"):
            validate_spans([("A", 0, 4), ("B", 3, 5)])

    def test_synthetic_zip_needs_matching_fingerprints(self):
        archive = Path(self.temp.name) / "source.zip"
        payload = b"A\r\n" * 3000
        with zipfile.ZipFile(archive, "w") as result:
            result.writestr(SOURCE_MEMBER, payload)
        rows = source_rows(archive, digest_file(archive), digest(payload))
        self.assertEqual(len(rows), 7)
        with self.assertRaisesRegex(ValueError, "成員SHA"):
            source_rows(archive, digest_file(archive), "0" * 64)


if __name__ == "__main__":
    unittest.main()
