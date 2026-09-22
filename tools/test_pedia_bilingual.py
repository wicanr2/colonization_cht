"""不含原版文字的百科語料欄位與控制碼回歸測試。"""

import tempfile
import unittest
from pathlib import Path

from build_pedia_bilingual import translations


class PediaCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "translations.tsv"
        self.row = {
            "message_id": "PEDIA.TXT:@FATHER0",
            "source_en": "^{Name}\\n{Effect: %Fs 50%%.}",
        }

    def write(self, value):
        self.path.write_text("message_id\tzh_hant\nPEDIA.TXT:@FATHER0\t" + value + "\n", encoding="utf-8")

    def test_controls_placeholder_and_percent_preserved(self):
        self.write("^{名稱}\\n{效果：%Fs 增加50%%。}")
        result = translations([self.row.copy()], self.path, True)
        self.assertEqual(result[0]["zh_hant"], "^{名稱}\\n{效果：%Fs 增加50%%。}")

    def test_percent_escape_rejected(self):
        self.write("^{名稱}\\n{效果：%Fs 增加50%。}")
        with self.assertRaisesRegex(ValueError, "百分比"):
            translations([self.row.copy()], self.path, True)

    def test_compound_placeholder_rejected(self):
        self.write("^{名稱}\\n{效果：%Ft 增加50%%。}")
        with self.assertRaisesRegex(ValueError, "占位符"):
            translations([self.row.copy()], self.path, True)


if __name__ == "__main__":
    unittest.main()
