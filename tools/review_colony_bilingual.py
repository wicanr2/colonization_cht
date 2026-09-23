#!/usr/bin/env python3
"""驗證殖民地名稱譯稿的固定來源與字型字元覆蓋；不決定顯示字級。"""

import argparse
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont

from build_colony_bilingual import source_rows, translations


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    if digest(args.font) != FONT_SHA:
        raise ValueError("字型版本指紋不符")
    rows = source_rows(args.archive)
    if rows is None:
        return 77
    rows = translations(rows, args.catalog, False)
    if len(rows) != args.expected_count:
        raise ValueError("語料筆數不符本輪預期範圍")
    with TTFont(args.font) as tt:
        cmap = tt.getBestCmap()
        coverage = {codepoint for codepoint, glyph in cmap.items() if tt.getGlyphID(glyph) != 0}
    reviewed = []
    for row in rows:
        missing = sorted({
            f"U+{ord(char):04X}"
            for char in row["zh_hant"]
            if not char.isspace() and ord(char) not in coverage
        })
        reviewed.append({
            "message_id": row["message_id"],
            "source_member_sha256": row["source_member_sha256"],
            "source_bytes_sha256": row["source_bytes_sha256"],
            "missing_codepoints": missing,
        })
    report = {
        "scope": "只核對固定來源、名稱格式與字型字元覆蓋；不設定或驗證全域中文字級、畫面事件或安全矩形",
        "catalog_sha256": digest(args.catalog),
        "font_sha256": FONT_SHA,
        "summary": {
            "source_and_format_passed": len(reviewed),
            "rows_with_missing_glyphs": sum(bool(row["missing_codepoints"]) for row in reviewed),
            "runtime_display_verified": False,
            "per_field_font_selection_verified": False,
        },
        "rows": reviewed,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
