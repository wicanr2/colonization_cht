"""純合成來源的受限單行譯稿建立器測試。"""

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from build_translation_draft import PROPOSAL_FIELDS, build_rows
from validate_translation_draft import FIELDS, Invalid


class TranslationDraftBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.game.mkdir()
        self.data = b"Existing\r\n~A Action#\r\nData, 1\r\n@COMMAND\r\n; note\r\n"
        (self.game / "TEST.TXT").write_bytes(self.data)
        self.catalog = self.root / "catalog.tsv"
        self.proposals = self.root / "proposal.tsv"
        existing = b"Existing"
        row = {
            "candidate_id": "TEST.TXT:0x00000000",
            "source_file": "TEST.TXT",
            "source_sha256": hashlib.sha256(self.data).hexdigest(),
            "byte_offset": "0x00000000",
            "source_bytes_sha256": hashlib.sha256(existing).hexdigest(),
            "source_byte_length": str(len(existing)),
            "zh_hant": "既有",
            "status": "draft",
            "notes": "合成既有候選",
        }
        with self.catalog.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerow(row)

    def write_proposal(self, offset, text="~A 動作#"):
        with self.proposals.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=PROPOSAL_FIELDS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerow({
                "source_file": "TEST.TXT",
                "byte_offset": f"0x{offset:08X}",
                "zh_hant": text,
                "notes": "合成獨立單行候選",
            })

    def test_builds_only_independent_line(self):
        offset = self.data.index(b"~A Action#")
        self.write_proposal(offset)
        rows = build_rows(self.game, self.catalog, self.proposals)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["candidate_id"], f"TEST.TXT:0x{offset:08X}")
        self.assertEqual(rows[-1]["zh_hant"], "~A 動作#")

    def test_rejects_composite_data(self):
        self.write_proposal(self.data.index(b"Data, 1"), "資料")
        with self.assertRaisesRegex(Invalid, "逗號複合資料"):
            build_rows(self.game, self.catalog, self.proposals)

    def test_rejects_directive(self):
        self.write_proposal(self.data.index(b"@COMMAND"), "命令")
        with self.assertRaisesRegex(Invalid, "註解或指令"):
            build_rows(self.game, self.catalog, self.proposals)

    def test_rejects_missing_hash_marker(self):
        self.write_proposal(self.data.index(b"~A Action#"), "~A 動作")
        with self.assertRaisesRegex(Invalid, "控制符號"):
            build_rows(self.game, self.catalog, self.proposals)


if __name__ == "__main__":
    unittest.main()
