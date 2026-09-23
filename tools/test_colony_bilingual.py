"""不含原版名稱的殖民地雙語語料欄位與格式回歸測試。"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from build_colony_bilingual import (
    NATIONS,
    SOURCE_MEMBER,
    digest,
    digest_file,
    parse_record,
    source_rows,
    translations,
)


class ColonyCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "translations.tsv"
        self.row = {
            "message_id": "COLONY.TXT:@ENGLISH:00",
            "source_name": "Sample",
            "source_year": "1607",
        }

    def write(self, value):
        self.path.write_text(
            "message_id\tzh_hant\nCOLONY.TXT:@ENGLISH:00\t" + value + "\n",
            encoding="utf-8",
        )

    def test_chinese_original_and_year_format_preserved(self):
        self.write("範例（Sample，1607）")
        result = translations([self.row.copy()], self.path, True)
        self.assertEqual(result[0]["zh_hant"], "範例（Sample，1607）")

    def test_changed_year_rejected(self):
        self.write("範例（Sample，1608）")
        with self.assertRaisesRegex(ValueError, "格式"):
            translations([self.row.copy()], self.path, True)

    def test_missing_original_rejected(self):
        self.write("範例（1607）")
        with self.assertRaisesRegex(ValueError, "格式"):
            translations([self.row.copy()], self.path, True)

    def test_missing_chinese_name_rejected(self):
        self.write("Sample（Sample，1607）")
        with self.assertRaisesRegex(ValueError, "中文"):
            translations([self.row.copy()], self.path, True)

    def test_record_parser_rejects_unknown_composite_data(self):
        self.assertEqual(parse_record(b"Sample,1607"), ("Sample,1607", "Sample", "1607"))
        with self.assertRaisesRegex(ValueError, "資料列"):
            parse_record(b"Sample,not-a-year")

    def test_synthetic_zip_needs_matching_fingerprints_and_counts(self):
        archive = Path(self.temp.name) / "source.zip"
        payload = b"".join(
            b"@" + nation.encode("ascii") + b"\r\nSample\r\n@STOP\r\n"
            for nation in NATIONS
        )
        with zipfile.ZipFile(archive, "w") as result:
            result.writestr(SOURCE_MEMBER, payload)
        expected = {nation: 1 for nation in NATIONS}
        rows = source_rows(archive, digest_file(archive), digest(payload), expected)
        self.assertEqual(len(rows), 4)
        with self.assertRaisesRegex(ValueError, "封存檔SHA"):
            source_rows(archive, "0" * 64, digest(payload), expected)


if __name__ == "__main__":
    unittest.main()
