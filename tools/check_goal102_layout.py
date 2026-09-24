#!/usr/bin/env python3
"""獨立核對國家介紹 DRAFT 對照圖的原版來源、字形邊界與可逆底圖。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops

from check_goal102_preprint import require, sha, verify as verify_preprint


def original_image(canvas, palette):
    require(len(canvas) == 64000 and len(palette) == 768 and max(palette) <= 63,
            "原版畫布或色盤長度不符")
    image = Image.frombytes("P", (320, 200), canvas)
    image.putpalette(bytes((c << 2) | (c >> 4) for c in palette))
    return image.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)


def inside(box, rect):
    return rect[0] <= box[0] < box[2] <= rect[2] and \
           rect[1] <= box[1] < box[3] <= rect[3]


def verify(args):
    preprint = verify_preprint(args.old, args.reports)
    require(preprint["result"] == "PASS", "印前原版收據未通過")
    layout_data = args.layout.read_bytes()
    layout = json.loads(layout_data)
    require(layout["page_count"] == len(layout["pages"]) == 8 and
            layout["status"].startswith("DRAFT") and
            layout["font_sha256"] ==
            "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c",
            "八頁或字型來源不符")
    seen = set()
    rows = []
    for page in layout["pages"]:
        nation, phase = page["nation"], page["phase"]
        key = (nation, phase)
        require(key not in seen and phase in ("a", "b"), "頁面重複或相位錯誤")
        seen.add(key)
        phase_name, sample = ("first", "60m") if phase == "a" else ("second", "70m")
        before = (args.reports / f"{nation}.{phase_name}.pre.canvas").read_bytes()
        after = (args.reports / f"{nation}.{sample}.canvas").read_bytes()
        palette = (args.reports / f"{nation}.{sample}.pal").read_bytes()
        require(sha(before) == page["preprint_canvas_sha256"] and
                sha(after) == page["original_canvas_sha256"] and
                sha(palette) == page["palette_sha256"] and
                not page["missing_codepoints"], f"{key}: 原版或字形資料不符")
        base = original_image(before, palette)
        expected_original = original_image(after, palette)
        actual_original = Image.open(args.output / f"{nation}-{phase}-original.png").convert("RGB")
        require(actual_original.size == (1280, 800) and
                ImageChops.difference(actual_original, expected_original).getbbox() is None,
                f"{key}: 原文對照圖不是 dosgolem 原始畫布")
        for variant in ("matched", "compact"):
            metric = page["variants"][variant]
            image = Image.open(args.output / f"{nation}-{phase}-{variant}.png").convert("RGB")
            title, body, panel = (metric["title_safe_rect_px"],
                                  metric["body_safe_rect_px"],
                                  metric["panel_safe_rect_px"])
            title_ink, body_ink = metric["title_ink_bbox_px"], metric["body_ink_bbox_px"]
            require(image.size == base.size and metric["fits_without_clipping"] and
                    metric["overflow_policy"].startswith("候選不合格即維持原文") and
                    not metric["bad_breaks"] and metric["line_count"] == len(metric["line_texts"]) and
                    metric["title_font_px"] != metric["body_font_px"] and
                    inside(title_ink, title) and inside(body_ink, body) and
                    inside(title_ink, panel) and inside(body_ink, panel) and
                    title_ink[3] < body_ink[1], f"{key}/{variant}: 欄位、字級或行界不符")
            diff = ImageChops.difference(base, image).convert("RGB")
            changed = diff.convert("L").point(lambda value: 255 if value else 0).histogram()[255]
            outside = diff.copy()
            outside.paste((0, 0, 0), tuple(title))
            outside.paste((0, 0, 0), tuple(body))
            require(changed > 0 and outside.getbbox() is None,
                    f"{key}/{variant}: 安全矩形外變更")
            rows.append({"message_id": page["message_id"], "variant": variant,
                         "title_px": metric["title_font_px"],
                         "body_px": metric["body_font_px"],
                         "line_count": metric["line_count"],
                         "changed_pixels": changed, "outside_safe_pixels": 0,
                         "preview_sha256": sha((args.output / f"{nation}-{phase}-{variant}.png").read_bytes())})
    require(len(seen) == 8 and len(rows) == 16, "不是四國八頁雙候選")
    for phase in ("a", "b"):
        local = (args.output / f"contact-{phase}.png").read_bytes()
        shared = (args.gallery / f"nation-intro-layout-draft-{phase}.png").read_bytes()
        require(local == shared and Image.open(args.gallery / f"nation-intro-layout-draft-{phase}.png").size ==
                (1440, 1280), f"{phase}: 私有對照圖不等於已驗本機輸出")
    return {"result": "PASS", "scope": "四國八節原文及兩套可丟棄中文排版；非 Ebitengine 正式顯示",
            "layout_sha256": sha(layout_data), "preprint_backgrounds": preprint["background_sha256s"],
            "missing_glyph_pages": 0, "outside_safe_pixels": 0,
            "gallery_a_sha256": sha((args.gallery / "nation-intro-layout-draft-a.png").read_bytes()),
            "gallery_b_sha256": sha((args.gallery / "nation-intro-layout-draft-b.png").read_bytes()),
            "variants": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--layout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gallery", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require(args.receipt.parent.is_dir() and args.receipt.parent.stat().st_uid == os.getuid(),
            "驗證收據輸出目錄不存在或擁有者不符")
    result = verify(args)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS：四國八頁雙候選、原版畫布與兩張私有對照圖；安全區外 0 像素")


if __name__ == "__main__":
    main()
