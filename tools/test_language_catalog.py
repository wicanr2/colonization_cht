"""以現行13份真實語料驗證規格053的資料隔離與完整性。"""

import copy
import csv
import unittest

import language_catalog as catalog


class LanguageCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = catalog.BaseCatalog()
        cls.rows = [{"locale": "zh-Hans", **{key: entry[key] for key in ("catalog", "key", "base_sha256", "text")},
                     "status": "translated" if entry["text"] else "omitted", "notes": "test fixture"}
                    for entry in cls.base.entries.values()]

    def load(self, rows, partial=False):
        return catalog.load_translation(self.base, catalog.write_tsv(catalog.FIELDS, rows), "zh-Hans", partial)

    def test_all_real_rows_and_unchanged_source_metadata(self):
        entries, missing = self.load(self.rows)
        self.assertEqual((len(entries), missing), (2006, []))
        original = catalog.make_views(self.base, {}, "zh-Hant")
        views = catalog.make_views(self.base, entries, "zh-Hans")
        self.assertEqual(len(views), 13)
        for table, header, resolved, data in self.base.tables:
            self.assertEqual(original[table["file"]], data)
            _, actual = catalog.read_tsv(views[table["file"]], header)
            self.assertEqual(actual, [entry["row"] for entry in resolved])

    def test_partial_does_not_become_complete_or_compile(self):
        partial = self.rows[:-1]
        with self.assertRaisesRegex(ValueError, "譯稿缺少"):
            self.load(partial)
        entries, missing = self.load(partial, True)
        self.assertEqual(len(missing), 1)
        with self.assertRaisesRegex(ValueError, "不完整"):
            catalog.make_views(self.base, entries, "zh-Hans")

    def test_stale_duplicate_orphan_wrong_language_and_empty(self):
        for mutate in (lambda rows: rows.append(rows[0].copy()),
                       lambda rows: rows[0].update(key="unknown"),
                       lambda rows: rows[0].update(locale="ja"),
                       lambda rows: rows[0].update(base_sha256="0" * 64),
                       lambda rows: rows[0].update(text=""),
                       lambda rows: rows[0].update(status="omitted", text="", notes="test")):
            rows = copy.deepcopy(self.rows)
            mutate(rows)
            with self.assertRaises(ValueError):
                self.load(rows)

    def test_lost_slots_markup_and_invalid_utf8_are_rejected(self):
        for original, changed in (("%STRING0 %NUMBER1", "%STRING0"), ("{w1} {n1}", "{w1}"),
                                  (r"^{標題}\\n正文", r"^{見出し}正文"), ("~開始", "開始"),
                                  ("版本 %% %s", "版 %s")):
            with self.assertRaises(ValueError):
                catalog.check_translation(original, changed, "translated", "", False)
        for original, changed in (("{person}的", "{人物}の"), ("{SHIFT}鍵", "{シフト}キー"),
                                  ("%COUNTRY", "%C"), ("%Fs", "%F")):
            with self.assertRaises(ValueError):
                catalog.check_translation(original, changed, "translated", "", False)
        with self.assertRaisesRegex(ValueError, "排版控制"):
            catalog.check_translation(r"{w1}\u3000{n1}", "{w1} {n1}", "translated", "", False)
        original = self.base.entries["templates", "port-title"]["text"]
        self.assertEqual(original.count(chr(0x3000)), 3)
        with self.assertRaisesRegex(ValueError, "排版控制"):
            catalog.check_translation(original, original.replace(chr(0x3000), r"\u3000"), "translated", "", False)
        for data in (b"\xff", b"locale\tlocale\na\tb\n", b"one\ttwo\nvalue\n"):
            with self.assertRaises((ValueError, UnicodeDecodeError)):
                catalog.read_tsv(data)

    def test_reordered_slots_and_translated_highlights_are_valid(self):
        catalog.check_translation("{w1}的{n1}個{殖民地}", "{殖民地}の{n1}個の{w1}", "translated", "", False)
        catalog.check_translation("", "", "omitted", "省略冠詞", False)
        with self.assertRaises(ValueError):
            catalog.check_translation("", "", "omitted", "", False)

    def test_legacy_quotes_are_limited_to_pinned_baseline(self):
        data = b'key\ttext\nitem\t"a"b\n'
        with self.assertRaises(csv.Error):
            catalog.read_tsv(data)
        self.assertEqual(catalog.read_tsv(data, legacy=True)[1][0]["text"], 'ab')

    def test_compile_rechecks_changed_binding(self):
        entries, _ = self.load(self.rows)
        changed = copy.deepcopy(entries)
        next(iter(changed.values()))["base_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "來源綁定"):
            catalog.make_views(self.base, changed, "zh-Hans")

    def test_real_compound_fields_preserve_numbers_and_command_codes(self):
        cases = []
        for entry in self.base.entries.values():
            if entry["catalog"] != "corpus" or entry["row"].get("source_file") != "NAMES.TXT":
                continue
            parts = entry["text"].split(",")
            for index, part in enumerate(parts[1:], 1):
                if catalog.re.fullmatch(r"[-+]?\d+|[A-Z]|-", part.strip()):
                    cases.append((entry, parts, index))
                    break
        self.assertGreater(len(cases), 150)
        for entry, parts, index in cases:
            changed = parts.copy()
            changed[index] = "99999"
            row = {"text": ",".join(changed), "status": "translated", "notes": "test"}
            with self.assertRaisesRegex(ValueError, "數值或命令"):
                catalog.check_row_translation(entry, row, False)
            row["text"] = ",".join(parts[:-1])
            with self.assertRaisesRegex(ValueError, "項目數"):
                catalog.check_row_translation(entry, row, False)


if __name__ == "__main__":
    unittest.main()
