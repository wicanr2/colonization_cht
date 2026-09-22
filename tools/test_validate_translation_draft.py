#!/usr/bin/env python3
"""純合成來源的控制碼回歸，不需要或攜帶原版文字。"""
import hashlib
import tempfile
import unittest
from pathlib import Path

from validate_translation_draft import Invalid, validate_sources


class HotkeyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = b"~A %STRING0 {item}"
        raw = source + b"\r\n"
        (self.root / "TEST.TXT").write_bytes(raw)
        self.row = {
            "candidate_id": "TEST.TXT:0x00000000", "source_file": "TEST.TXT",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "byte_offset": "0x00000000", "source_byte_length": str(len(source)),
            "source_bytes_sha256": hashlib.sha256(source).hexdigest(),
            "zh_hant": "測試（~A）%STRING0 {項目}",
        }

    def test_preserves_ascii_marker(self):
        self.assertEqual(validate_sources([self.row], self.root), 1)

    def test_changed_ascii_marker_rejected(self):
        self.row["zh_hant"] = self.row["zh_hant"].replace("~A", "~B")
        with self.assertRaisesRegex(Invalid, "熱鍵 ASCII"):
            validate_sources([self.row], self.root)

    def test_chinese_marker_rejected(self):
        self.row["zh_hant"] = self.row["zh_hant"].replace("~A", "~中")
        with self.assertRaisesRegex(Invalid, "熱鍵 ASCII"):
            validate_sources([self.row], self.root)

    def test_marker_case_preserved(self):
        self.row["zh_hant"] = self.row["zh_hant"].replace("~A", "~a")
        with self.assertRaisesRegex(Invalid, "熱鍵 ASCII"):
            validate_sources([self.row], self.root)

    def test_missing_control_rejected(self):
        self.row["zh_hant"] = self.row["zh_hant"].replace("~A", "A")
        with self.assertRaisesRegex(Invalid, "控制符號"):
            validate_sources([self.row], self.root)

    def test_hash_format_marker_preserved(self):
        source = b"Zoom# ~Z"
        raw = source + b"\r\n"
        (self.root / "TEST.TXT").write_bytes(raw)
        self.row.update(
            candidate_id="TEST.TXT:0x00000000",
            source_sha256=hashlib.sha256(raw).hexdigest(),
            source_bytes_sha256=hashlib.sha256(source).hexdigest(),
            source_byte_length=str(len(source)),
            zh_hant="縮放# ~Z",
        )
        self.assertEqual(validate_sources([self.row], self.root), 1)
        self.row["zh_hant"] = "縮放 ~Z"
        with self.assertRaisesRegex(Invalid, "控制符號"):
            validate_sources([self.row], self.root)

    def test_compound_placeholder_preserved(self):
        source = b"Denounce %Fs Mission"
        raw = source + b"\r\n"
        (self.root / "TEST.TXT").write_bytes(raw)
        self.row.update(
            candidate_id="TEST.TXT:0x00000000",
            source_sha256=hashlib.sha256(raw).hexdigest(),
            source_bytes_sha256=hashlib.sha256(source).hexdigest(),
            source_byte_length=str(len(source)),
            zh_hant="譴責 %Fs 傳教所的異端",
        )
        self.assertEqual(validate_sources([self.row], self.root), 1)

    def test_compound_placeholder_suffix_rejected(self):
        source = b"Denounce %Fs Mission"
        raw = source + b"\r\n"
        (self.root / "TEST.TXT").write_bytes(raw)
        self.row.update(
            candidate_id="TEST.TXT:0x00000000",
            source_sha256=hashlib.sha256(raw).hexdigest(),
            source_bytes_sha256=hashlib.sha256(source).hexdigest(),
            source_byte_length=str(len(source)),
            zh_hant="譴責 %Ft 傳教所的異端",
        )
        with self.assertRaisesRegex(Invalid, "變數占位符"):
            validate_sources([self.row], self.root)

    def test_changed_indentation_rejected(self):
        self.row["zh_hant"] = "  " + self.row["zh_hant"]
        with self.assertRaisesRegex(Invalid, "前置縮排"):
            validate_sources([self.row], self.root)


if __name__ == "__main__":
    unittest.main()
