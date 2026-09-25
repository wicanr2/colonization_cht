#!/usr/bin/env python3
"""以目標102貼近原版版式，為國家介紹頁烘製陰影／一般／強調三層本機字模；只輸出本機研究產物。"""

import argparse
import base64
import csv
import hashlib
import json
import os
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

from check_goal102_preprint import NATIONS, require, sha, verify as verify_preprint
from preview_goal102_nation_intro import FONT_SHA, PANEL, layout, measure_writer
from validate_nation_introduction_corpus import check as check_catalog


# 使用者 2026-09-25 選定貼近原版字高：標題 34px／正文 38px（delta 0）。
SIZES = (34, 38)


def draw_masks(plan):
    """與 draw_line 同序：陰影為整行 +4／+4，一般為整行，強調為 {} 片段。"""
    size = (PANEL[2] - PANEL[0], PANEL[3] - PANEL[1])
    shadow, normal, highlight = (Image.new("L", size) for _ in range(3))
    layers = [ImageDraw.Draw(image) for image in (shadow, normal, highlight)]
    for line, font, x, baseline in plan["placed"]:
        x, baseline = x - PANEL[0], baseline - PANEL[1]
        value = "".join(c for c, _ in line)
        layers[0].text((x + 4, baseline + 4), value, font=font, anchor="ls", fill=255)
        layers[1].text((x, baseline), value, font=font, anchor="ls", fill=255)
        start = 0
        while start < len(line):
            if not line[start][1]:
                start += 1
                continue
            end = start + 1
            while end < len(line) and line[end][1]:
                end += 1
            prefix = "".join(c for c, _ in line[:start])
            segment = "".join(c for c, _ in line[start:end])
            layers[2].text((x + round(font.getlength(prefix)), baseline), segment,
                           font=font, anchor="ls", fill=255)
            start = end
    return shadow, normal, highlight


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--old", type=Path, required=True, help="目標101原版收據目錄")
    p.add_argument("--reports", type=Path, required=True, help="目標102印前底圖收據目錄")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--nation", choices=NATIONS, required=True)
    args = p.parse_args()
    if not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未產生字模")
        return 77
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(), "輸出目錄不存在或擁有者不符")
    require(sha(args.font.read_bytes()) == FONT_SHA, "Cubic 11 原始字型 SHA-256 不符")
    verify_preprint(args.old, args.reports)
    check_catalog(args.game / "GAME.TXT", args.catalog)
    with TTFont(args.font) as tt:
        cmap = tt.getBestCmap()
        coverage = {code for code, name in cmap.items() if tt.getGlyphID(name) != 0}
    with args.catalog.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    index = NATIONS.index(args.nation)
    report = json.loads((args.reports / f"{args.nation}.json").read_bytes())
    for phase, part in (("A", "first"), ("B", "second")):
        key = f"GAME.TXT:@NATION{index}{phase}"
        matches = [row for row in rows if row["message_id"] == key]
        require(len(matches) == 1, f"{key}: 譯稿缺鍵或重複")
        draft = matches[0]["zh_hant_draft"]
        title, body = draft.split("\\n", 1)
        visible = title + body.replace("{", "").replace("}", "")
        require(all(ord(char) in coverage for char in visible), f"{key}: Cubic 11 缺字，不產生部分字模")
        plan = layout(title, body, args.font, measure_writer(report["writers"][f"{part}/0D21:012C"]), 0)
        require((plan["title_size"], plan["body_size"]) == SIZES, f"{key}: 字級不是使用者選定的 34／38px")
        require(not plan["bad_breaks"] and max(plan["widths"]) <= plan["text_width"] and
                plan["total_height"] <= PANEL[3] - PANEL[1] - 16, f"{key}: 版面超界，不裁切")
        shadow, normal, highlight = draw_masks(plan)
        require(all(image.getbbox() is None or
                    image.getbbox()[2] <= image.width and image.getbbox()[3] <= image.height
                    for image in (shadow, normal, highlight)) and normal.getbbox() is not None,
                f"{key}: 字模沒有墨跡或越界")
        receipt = {"message_id": key, "section_sha256": matches[0]["section_sha256"],
                   "catalog_sha256": sha(args.catalog.read_bytes()),
                   "translation_sha256": sha(draft.encode()), "font_sha256": FONT_SHA,
                   "title_font_px": plan["title_size"], "body_font_px": plan["body_size"],
                   "line_count": len(plan["lines"]), "panel": list(PANEL),
                   "width": shadow.width, "height": shadow.height,
                   "shadow": base64.b64encode(shadow.tobytes()).decode(),
                   "normal": base64.b64encode(normal.tobytes()).decode(),
                   "highlight": base64.b64encode(highlight.tobytes()).decode(),
                   "scope": "local-only；衍生字模不加入 Git 或散布包"}
        target = args.output / f"{key.replace(':', '-')}.json"
        target.write_text(json.dumps(receipt, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"本機字模已產生：{key}，{len(plan['lines'])} 行，{plan['title_size']}／{plan['body_size']}px")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
