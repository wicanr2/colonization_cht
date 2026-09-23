#!/usr/bin/env python3
"""驗證已取證國家旗卡的顯示片段草稿；不建立正式執行期鍵。"""

import argparse
import csv
import hashlib
import io
from pathlib import Path

from prototype_overlay import cmap_coverage


FIELDS = ["candidate_id", "source_file", "source_sha256", "byte_offset",
          "source_bytes_sha256", "source_byte_length", "source_text",
          "zh_hant", "status", "notes"]
EXPECTED = {
    "NAMES.TXT:0x000008EA": ("NAMES.TXT", 0x8EA, b"England", "英格蘭"),
    "NAMES.TXT:0x00000906": ("NAMES.TXT", 0x906, b"France", "法國"),
    "LABELS.TXT:0x000008F2": ("LABELS.TXT", 0x8F2, b"Immigration", "移民"),
    "LABELS.TXT:0x000008FF": ("LABELS.TXT", 0x8FF, b"Cooperation", "合作"),
}
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def validate(catalog, game, font):
    raw_catalog = catalog.read_bytes()
    require(not raw_catalog.startswith(b"\xef\xbb\xbf"), "TSV 不接受 BOM")
    rows = list(csv.DictReader(io.StringIO(raw_catalog.decode("utf-8")),
                               delimiter="\t", strict=True))
    require(rows and list(rows[0]) == FIELDS and len(rows) == len(EXPECTED),
            "旗卡片段欄位或筆數不符")
    require(len({row["candidate_id"] for row in rows}) == len(rows), "來源鍵重複")
    for row in rows:
        key = row["candidate_id"]
        require(key in EXPECTED and None not in row and all(value is not None for value in row.values()),
                "來源鍵或欄數不符：" + str(key))
        name, offset, original, translated = EXPECTED[key]
        require(row["source_file"] == name and int(row["byte_offset"], 0) == offset
                and row["source_byte_length"] == str(len(original))
                and row["source_text"] == original.decode("ascii")
                and row["zh_hant"] == translated and row["status"] == "draft"
                and row["notes"].strip(), "片段資料不符：" + key)
        source = (game / name).read_bytes()
        require(sha(source) == row["source_sha256"]
                and source[offset:offset + len(original)] == original
                and sha(original) == row["source_bytes_sha256"],
                "原始檔案／片段指紋不符：" + key)
        require(source[offset - 2:offset] == b"\r\n", "不是原始行首：" + key)
        if name == "NAMES.TXT":
            section = source.rfind(b"@COUNTRY\r\n", 0, offset)
            require(source[offset + len(original):offset + len(original) + 1] == b","
                    and section >= 0 and source.rfind(b"@", 0, offset) == section,
                    "複合國名紀錄語境不符")
        else:
            require(source[offset + len(original):offset + len(original) + 2] == b"\r\n",
                    "副標不是完整原始行")
    font_data = font.read_bytes()
    require(sha(font_data) == FONT_SHA, "Cubic 11 字型指紋不符")
    coverage = cmap_coverage(font_data)
    require(all(ord(char) in coverage for char in "英格蘭：移民法國合作"), "Cubic 11 缺少預覽字形")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    args = parser.parse_args()
    if not args.game.is_dir() or not args.font.is_file():
        print("SKIP：合法原版或本機字型缺失")
        return 77
    validate(args.catalog, args.game, args.font)
    print("PASS：旗卡四筆顯示片段草稿、原始檔案指紋、複合行語境及字形覆蓋一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
