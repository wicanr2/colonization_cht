#!/usr/bin/env python3
"""四國八頁介紹的可丟棄 Cubic 11 排版量測；不接正式顯示層。"""

import argparse
import csv
import hashlib
import json
import os
import platform
from pathlib import Path

import PIL
import fontTools
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, features

from check_goal102_preprint import NATIONS, require, sha, verify as verify_preprint
from validate_nation_introduction_corpus import check as check_catalog


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
PANEL = (32, 32, 1248, 768)  # 原版木紋頁內 (8,8)–(312,192) 四倍；不是互動矩形。
INNER = (48, 1232)            # 原版 @width=300，兩側再保留 4 個輸出像素。
PROHIBITED_LINE_START = set("，。；：、！？％%）】》」』，.、;:!?)]}")
PROHIBITED_LINE_END = set("（【《「『([{")
VARIANTS = (("matched", 0), ("compact", -4))


def groups(values):
    out = []
    for value in sorted(values):
        if not out or value > out[-1][-1] + 1:
            out.append([value])
        else:
            out[-1].append(value)
    return out


def choose_size(text, target_height, delta):
    measured = []
    for size in range(24, 49):
        font = ImageFont.truetype(str(text[0]), size)
        bbox = font.getbbox(text[1])
        measured.append((abs((bbox[3] - bbox[1]) - target_height), size,
                         bbox[3] - bbox[1]))
    _, exact_size, exact_height = min(measured)
    size = max(20, exact_size + delta)
    font = ImageFont.truetype(str(text[0]), size)
    bbox = font.getbbox(text[1])
    return font, size, exact_size, exact_height, bbox[3] - bbox[1]


def marked_chars(body):
    chars = []
    emphasis = False
    for char in body:
        if char == "{":
            require(not emphasis, "巢狀強調標記")
            emphasis = True
        elif char == "}":
            require(emphasis, "多餘強調標記")
            emphasis = False
        else:
            chars.append((char, emphasis))
    require(not emphasis, "強調標記未關閉")
    return chars


def wrap(chars, font, limit):
    lines = []
    current = []
    for item in chars:
        char = item[0]
        if not current or font.getlength("".join(c for c, _ in current) + char) <= limit:
            current.append(item)
            continue
        if char in PROHIBITED_LINE_START and len(current) > 1:
            carried = [current.pop(), item]
        else:
            carried = [item]
        # 連續 ASCII 英數字（年份、分數）整段換行，不在數字中間斷開。
        while len(current) > 1 and current[-1][0].isascii() and current[-1][0].isalnum() and \
                carried[0][0].isascii() and carried[0][0].isalnum():
            carried.insert(0, current.pop())
        while len(current) > 1 and current[-1][0] in PROHIBITED_LINE_END:
            carried.insert(0, current.pop())
        lines.append(current)
        current = carried
    if current:
        lines.append(current)
    # 不靠繪圖裁切；任何仍然超寬的行都使本候選不合格。
    widths = [font.getlength("".join(c for c, _ in line)) for line in lines]
    bad_breaks = [i for i, line in enumerate(lines)
                  if line[0][0] in PROHIBITED_LINE_START or
                  line[-1][0] in PROHIBITED_LINE_END]
    return lines, widths, bad_breaks


def draw_line(draw, line, font, x, baseline, normal, highlight, shadow):
    value = "".join(c for c, _ in line)
    draw.text((x + 4, baseline + 4), value, font=font, anchor="ls", fill=shadow)
    draw.text((x, baseline), value, font=font, anchor="ls", fill=normal)
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
        draw.text((x + round(font.getlength(prefix)), baseline), segment,
                  font=font, anchor="ls", fill=highlight)
        start = end


def palette_rgb(palette):
    require(len(palette) == 768 and max(palette) <= 63, "原版 DAC 色盤不符")
    return bytes((c << 2) | (c >> 4) for c in palette)


def original_image(canvas, palette):
    require(len(canvas) == 64000, "原版畫布長度不符")
    image = Image.frombytes("P", (320, 200), canvas)
    image.putpalette(palette_rgb(palette))
    return image.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)


def in_rect(box, safe):
    return box is not None and safe[0] <= box[0] < box[2] <= safe[2] and \
           safe[1] <= box[1] < box[3] <= safe[3]


def layout(title, body, font_path, original, delta):
    """只計算版面：字級、換行、標題與各正文行的基線位置；預覽與正式字模共用。"""
    title_font, title_size, title_exact_size, title_exact_height, title_height = \
        choose_size((font_path, title), original["title_height"] * 4, delta)
    body_font, body_size, body_exact_size, body_exact_height, body_height = \
        choose_size((font_path, "國"), original["body_height"] * 4, delta)
    # 右界預留真實墨跡與 4px 陰影，不能只讓字的前進寬度剛好貼邊。
    text_width = INNER[1] - INNER[0] - 12
    lines, widths, bad_breaks = wrap(marked_chars(body), body_font, text_width)
    line_advance = max(body_height + 5, original["body_line_advance"] * 4)
    gap = min(48, max(20, original["title_body_gap"] * 4))
    total_height = title_height + gap + (len(lines) - 1) * line_advance + body_height + 4
    title_top = (PANEL[1] + PANEL[3] - total_height) // 2
    body_top = title_top + title_height + gap
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    title_bbox = probe.textbbox((0, 0), title, font=title_font, anchor="ls")
    ref_bbox = probe.textbbox((0, 0), "國", font=body_font, anchor="ls")
    title_x = (PANEL[0] + PANEL[2] - round(title_font.getlength(title))) // 2
    placed = [([(c, False) for c in title], title_font, title_x, title_top - title_bbox[1])]
    placed += [(line, body_font, INNER[0], body_top + i * line_advance - ref_bbox[1])
               for i, line in enumerate(lines)]
    return {"title_font": title_font, "body_font": body_font, "placed": placed,
            "title_size": title_size, "body_size": body_size,
            "title_exact_size": title_exact_size, "body_exact_size": body_exact_size,
            "title_exact_height": title_exact_height, "body_exact_height": body_exact_height,
            "text_width": text_width, "lines": lines, "widths": widths, "bad_breaks": bad_breaks,
            "line_advance": line_advance, "gap": gap, "total_height": total_height,
            "title_top": title_top, "body_top": body_top}


def render(background, title, body, font_path, original, palette, delta):
    plan = layout(title, body, font_path, original, delta)
    lines, widths, bad_breaks = plan["lines"], plan["widths"], plan["bad_breaks"]
    title_top, body_top = plan["title_top"], plan["body_top"]
    title_layer = Image.new("RGBA", background.size)
    body_layer = Image.new("RGBA", background.size)
    rgb = palette_rgb(palette)
    normal = tuple(rgb[68 * 3:68 * 3 + 3]) + (255,)
    highlight = tuple(rgb[149 * 3:149 * 3 + 3]) + (255,)
    shadow = tuple(rgb[47 * 3:47 * 3 + 3]) + (255,)
    title_draw = ImageDraw.Draw(title_layer)
    body_draw = ImageDraw.Draw(body_layer)
    for index, (line, font, x, baseline) in enumerate(plan["placed"]):
        draw_line(title_draw if index == 0 else body_draw, line, font, x, baseline,
                  normal, highlight, shadow)
    title_ink = title_layer.getbbox()
    body_ink = body_layer.getbbox()
    title_safe = (INNER[0], title_top - 4, INNER[1], body_top - 8)
    body_safe = (INNER[0], body_top - 4, INNER[1], PANEL[3] - 8)
    fits = (plan["total_height"] <= PANEL[3] - PANEL[1] - 16 and
            max(widths) <= plan["text_width"] and not bad_breaks and
            in_rect(title_ink, title_safe) and in_rect(body_ink, body_safe) and
            in_rect(title_ink, PANEL) and in_rect(body_ink, PANEL) and
            title_ink[3] < body_ink[1])
    image = background.convert("RGBA")
    image.alpha_composite(title_layer)
    image.alpha_composite(body_layer)
    return image.convert("RGB"), {
        "title_font_px": plan["title_size"], "body_font_px": plan["body_size"],
        "title_size_matching_original": plan["title_exact_size"],
        "body_size_matching_original": plan["body_exact_size"],
        "original_title_height_scaled": original["title_height"] * 4,
        "original_body_height_scaled": original["body_height"] * 4,
        "title_reference_height": plan["title_exact_height"],
        "body_reference_height": plan["body_exact_height"],
        "title_ink_bbox_px": title_ink, "body_ink_bbox_px": body_ink,
        "title_safe_rect_px": title_safe, "body_safe_rect_px": body_safe,
        "panel_safe_rect_px": PANEL, "line_advance_px": plan["line_advance"],
        "title_body_gap_px": plan["gap"], "line_count": len(lines),
        "max_line_advance_px": round(max(widths, default=0), 2),
        "line_texts": ["".join(c for c, _ in line) for line in lines],
        "bad_breaks": bad_breaks, "fits_without_clipping": fits,
        "overflow_policy": "候選不合格即維持原文；不裁切、不省略譯文",
    }


def measure_writer(writer):
    row_groups = groups(int(y) for y in writer["rows"])
    require(len(row_groups) >= 2 and len(row_groups[0]) == 8,
            "原版標題與正文列無法分離")
    body_groups = row_groups[1:]
    require(all(5 <= len(group) <= 9 for group in body_groups),
            "原版正文列高與預期不符")
    starts = [group[0] for group in body_groups]
    steps = [b - a for a, b in zip(starts, starts[1:])]
    advance = sorted(steps)[len(steps) // 2] if steps else 10
    return {"title_rows": [row_groups[0][0], row_groups[0][-1]],
            "body_rows": [body_groups[0][0], body_groups[-1][-1]],
            "body_original_line_count": len(body_groups),
            "title_height": len(row_groups[0]),
            "body_height": max(len(group) for group in body_groups),
            "body_line_advance": advance,
            "title_body_gap": body_groups[0][0] - row_groups[0][-1] - 1,
            "original_writer_bbox": writer["bbox"]}


def contact(pages, output, phase, font_path, gallery=None):
    # 每列一國，每欄依序原版／按原字高／較緊湊，僅供私有視覺審查。
    canvas = Image.new("RGB", (1440, 1280), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    label_font = ImageFont.truetype(str(font_path), 18)
    country_names = ("英格蘭", "法國", "西班牙", "荷蘭")
    labels = ("原版", "按原字高", "較緊湊")
    for i, nation in enumerate(NATIONS):
        for j, label in enumerate(("original", "matched", "compact")):
            image = pages[(nation, phase, label)].resize((480, 300), Image.Resampling.NEAREST)
            x, y = j * 480, i * 320 + 20
            canvas.paste(image, (x, y))
            draw.text((x + 8, y - 18), f"{country_names[i]} {phase.upper()}／{labels[j]}",
                      font=label_font, fill="white")
    canvas.save(output / f"contact-{phase}.png")
    if gallery is not None:
        canvas.save(gallery / f"nation-intro-layout-draft-{phase}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gallery", type=Path,
                        help="已核對為私有儲存庫時，另存供使用者審查的對照圖")
    args = parser.parse_args()
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(),
            "輸出目錄不存在或擁有者不符")
    if args.gallery is not None:
        require(args.gallery.is_dir() and args.gallery.stat().st_uid == os.getuid(),
                "私有截圖目錄不存在或擁有者不符")
    require(sha(args.font.read_bytes()) == FONT_SHA, "Cubic 11 原始字型 SHA-256 不符")
    verify_preprint(args.old, args.reports)
    check_catalog(args.game / "GAME.TXT", args.catalog)
    with TTFont(args.font) as tt:
        cmap = tt.getBestCmap()
        coverage = {codepoint for codepoint, name in cmap.items() if tt.getGlyphID(name) != 0}
    with args.catalog.open(encoding="utf-8", newline="") as handle:
        catalog = {row["message_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    require(len(catalog) == 8, "不是八節固定譯稿")
    pages = {}
    results = []
    for index, nation in enumerate(NATIONS):
        report = json.loads((args.reports / f"{nation}.json").read_bytes())
        for phase, sample in (("a", "60m"), ("b", "70m")):
            key = f"GAME.TXT:@NATION{index}{phase.upper()}"
            title, body = catalog[key]["zh_hant_draft"].split("\\n", 1)
            visible = title + body.replace("{", "").replace("}", "")
            missing = sorted({f"U+{ord(char):04X}" for char in visible
                              if ord(char) not in coverage})
            require(not missing, f"{key}: Cubic 11 缺字 {missing}")
            part = "first" if phase == "a" else "second"
            before = (args.reports / f"{nation}.{part}.pre.canvas").read_bytes()
            after = (args.reports / f"{nation}.{sample}.canvas").read_bytes()
            palette = (args.reports / f"{nation}.{sample}.pal").read_bytes()
            background = original_image(before, palette)
            original = original_image(after, palette)
            pages[(nation, phase, "original")] = original
            original.save(args.output / f"{nation}-{phase}-original.png")
            source_geometry = measure_writer(report["writers"][f"{part}/0D21:012C"])
            variants = {}
            for name, delta in VARIANTS:
                preview, metric = render(background, title, body, args.font,
                                         source_geometry, palette, delta)
                pages[(nation, phase, name)] = preview
                preview.save(args.output / f"{nation}-{phase}-{name}.png")
                variants[name] = metric
            results.append({"message_id": key, "nation": nation, "phase": phase,
                            "source_sha256": catalog[key]["section_sha256"],
                            "translation_sha256": sha(catalog[key]["zh_hant_draft"].encode()),
                            "preprint_canvas_sha256": sha(before),
                            "original_canvas_sha256": sha(after),
                            "palette_sha256": sha(palette),
                            "original_geometry": source_geometry,
                            "missing_codepoints": missing, "variants": variants})
    for phase in ("a", "b"):
        contact(pages, args.output, phase, args.font, args.gallery)
    report = {"status": "DRAFT 原型，不是正式中文覆蓋或玩家路徑驗收",
              "font_sha256": FONT_SHA, "catalog_sha256": sha(args.catalog.read_bytes()),
              "game_sha256": sha((args.game / "GAME.TXT").read_bytes()),
              "source": "dosgolem 四國八頁正常玩家路徑的首字印前畫布與穩定畫布",
              "versions": {"python": platform.python_version(), "pillow": PIL.__version__,
                           "freetype": features.version_module("freetype2"),
                           "fonttools": fontTools.__version__},
              "page_count": len(results), "pages": results}
    (args.output / "layout.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DRAFT：四國八節，按原字高可容納",
          sum(page["variants"]["matched"]["fits_without_clipping"] for page in results),
          "/8；較緊湊可容納",
          sum(page["variants"]["compact"]["fits_without_clipping"] for page in results), "/8")


if __name__ == "__main__":
    main()
