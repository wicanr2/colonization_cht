#!/usr/bin/env python3
"""唯讀校對既有譯稿與字型；只輸出本機報告，不批准術語或覆蓋鍵。"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import PIL
import fontTools
from fontTools.ttLib import TTFont
from PIL import ImageFont, features

from validate_translation_draft import read_catalog, validate_sources, PLACEHOLDER


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parents[1] / "text/draft.zh-Hant.tsv")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = read_catalog(args.catalog)
    if any(not (args.game / row["source_file"]).is_file() for row in rows):
        print("SKIP：缺少原版來源")
        return 77
    validate_sources(rows, args.game)
    if len(rows) != 50:
        raise ValueError("本輪範圍固定50筆，請重新審查新增內容")
    if digest(args.font) != FONT_SHA:
        raise ValueError("字型版本指紋不符")
    font = ImageFont.truetype(str(args.font), 24)
    with TTFont(args.font) as tt:
        cmap = tt.getBestCmap()
        coverage = {cp for cp, name in cmap.items() if tt.getGlyphID(name) != 0}
    reviewed = []
    for row in rows:
        text = row["zh_hant"]
        # 僅記錄原樣模板；變數替換與樣式控制碼解析仍屬執行期責任。
        bbox = list(font.getbbox(text))
        width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        missing = sorted({f"U+{ord(c):04X}" for c in text if ord(c) not in coverage})
        mask = font.getmask(text)
        entry = {
            "candidate_id": row["candidate_id"],
            "source_sha256": row["source_sha256"],
            "source_bytes_sha256": row["source_bytes_sha256"],
            "source_validation": "passed",
            "draft_text": text,
            "placeholder_sequence": PLACEHOLDER.findall(text),
            "missing_codepoints": missing,
            "font_bbox": bbox,
            "width_px": width,
            "height_px": height,
            "advance_px": font.getlength(text),
            "raster_mask_bbox": mask.getbbox(),
            "measurement_scope": "未展開變數的原樣模板" if PLACEHOLDER.search(text) else "目前譯文單行墨跡與前進寬度",
            "safe_rectangle_status": "unknown",
            "geometry_accepted": None,
        }
        if row["candidate_id"] == "GAME.TXT:0x000001B0":
            entry.update(safe_rectangle_status="規格009已知單一原型安全矩形",
                         safe_rectangle_px=[344, 428, 928, 456],
                         geometry_accepted=width <= 584 and height <= 28,
                         placement_rule="對齊墨跡左上角；繪字座標需扣除bbox前兩值",
                         fits_without_truncation=width <= 584 and height <= 28)
        reviewed.append(entry)
    report = {
        "scope": "Goal056既有50筆草稿第二輪校對；不是正式詞彙、覆蓋鍵或完整介面驗收",
        "catalog_sha256": digest(args.catalog),
        "font_sha256": FONT_SHA,
        "font_size_px": 24,
        "font_metrics": font.getmetrics(),
        "tools": {"python": platform.python_version(), "pillow": PIL.__version__,
                  "freetype": features.version_module("freetype2"), "fonttools": fontTools.__version__},
        "summary": {"source_and_placeholder_passed": len(reviewed),
                    "rows_with_missing_glyphs": sum(bool(r["missing_codepoints"]) for r in reviewed),
                    "rows_with_known_geometry": sum(r["geometry_accepted"] is not None for r in reviewed),
                    "runtime_variable_expansion_verified": False,
                    "terminology_approved": False},
        "limitations": ["49筆尚無各自安全矩形，不把字型量測當成場景版面通過。",
                        "變數實值、反白、重繪及連續播放不在此工具驗證範圍。",
                        "cmap由fontTools獨立解析，不依賴原型的自製cmap解析器。",
                        "工具不自動判定語意；語言校對意見由同輪人工檢閱另行追加。"],
        "rows": reviewed,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
