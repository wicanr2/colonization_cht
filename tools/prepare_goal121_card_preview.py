#!/usr/bin/env python3
"""由目標120原版收據製作第三張難度卡片 A／B 可丟棄 Ebitengine 對照。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from check_goal120_third import load as load_original, validate as validate_original
from prototype_overlay import cmap_coverage
from validate_translation_draft import read_catalog, validate_sources


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
PALETTE_SHA = "762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82"
SOURCE_SHA = "d6e0772831ea71b3a99662478d70eb18b3dd9e0d478497bd4139dc6de1a7096f"
FIELDS = (
    {"name": "title", "key": "NAMES.TXT:0x00000C22", "source": "NAMES.TXT",
     "offset": 0xC22, "original": b"Conquistador", "display": "CONQUISTADOR:",
     "ink_bbox": (32, 141, 81, 145), "ink_count": 205,
     "safe": (29, 139, 84, 148), "before": "before-title-ink",
     "background_colors": 115, "sizes": {"faithful": 21, "readable": 25}},
    {"name": "subtitle", "key": "LABELS.TXT:0x000008B8", "source": "LABELS.TXT",
     "offset": 0x8B8, "original": b"Moderate", "display": "Moderate",
     "ink_bbox": (41, 149, 73, 154), "ink_count": 116,
     "safe": (38, 148, 76, 157), "before": "after-title-before-subtitle",
     "background_colors": 82, "sizes": {"faithful": 25, "readable": 29}},
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def changed(before, after):
    require(len(before) == len(after) == 64000, "原始畫布長度不符")
    pixels = [(i % 320, i // 320) for i in range(64000) if before[i] != after[i]]
    require(bool(pixels), "原版墨跡差分消失")
    return len(pixels), (min(x for x, _ in pixels), min(y for _, y in pixels),
                         max(x for x, _ in pixels), max(y for _, y in pixels))


def field_data(field, row, font_path, coverage, reports, final):
    text = row["zh_hant"]
    require(all(ord(char) in coverage for char in text), "固定字型缺字：" + field["name"])
    before = (reports / f"click-v3-a.{field['before']}.canvas").read_bytes()
    after = (reports / "click-v3-a.after-title-before-subtitle.canvas" if field["name"] == "title"
             else reports / "click-v3-a.after-second-ink.canvas").read_bytes()
    require(changed(before, after) == (field["ink_count"], field["ink_bbox"]),
            "原版墨跡與第三張卡片收據不符：" + field["name"])
    safe = field["safe"]
    background = rect_bytes(before, safe)
    require(len(set(background)) == field["background_colors"] and
            changed(before, final)[0] >= field["ink_count"] and
            rect_bytes(after, safe) == rect_bytes(final, safe),
            "印前紋理或穩定終點不符：" + field["name"])
    return text, background


def make_layer(field, text, background, font_path, style, coverage):
    safe = field["safe"]
    size = field["sizes"][style]
    font = ImageFont.truetype(str(font_path), size)
    left, top, right, bottom = font.getbbox(text)
    width, height = right - left, bottom - top
    original_scaled = (field["ink_bbox"][3] - field["ink_bbox"][1] + 1) * 4
    max_extra = 1 if style == "faithful" else 4
    require(0 < width and 0 < height and abs(height - original_scaled) <= max_extra,
            "逐欄中文字級與原版墨跡不相稱：" + field["name"])
    x = (safe[0] + safe[2]) * 2 - width // 2
    y = field["ink_bbox"][1] * 4
    shadow_dx = 4  # 原版兩行黑色索引 0 全在色墨索引 14 右方一個邏輯像素。
    require(safe[0] * 4 + 4 <= x and x + width + shadow_dx <= safe[2] * 4 - 4 and
            safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
            "中文字模／陰影越界或內距不足：" + field["name"])
    mask = Image.new("L", (width, height))
    ImageDraw.Draw(mask).text((-left, -top), text, font=font, fill=255)
    require(any(mask.tobytes()), "中文字模為空：" + field["name"])
    return {"name": field["name"], "candidate_id": field["key"], "display": field["display"],
            "safe": safe, "original_ink_bbox": field["ink_bbox"],
            "original_ink_height_scaled": original_scaled, "font_size": size,
            "ink_width": width, "ink_height": height, "position": [x, y],
            "padding": [x - safe[0] * 4, y - safe[1] * 4,
                        safe[2] * 4 - (x + width + shadow_dx), safe[3] * 4 - (y + height)],
            "overflow": "single-line; no truncation or wrap; fallback to original if out of bounds",
            "translation_sha256": sha(text.encode()), "background_palette_indices": len(set(background)),
            "color_index": 14, "shadow_index": 0, "shadow_dx": shadow_dx,
            "background": base64.b64encode(background).decode(),
            "mask": base64.b64encode(mask.tobytes()).decode()}


def prepare(args):
    rows, images, original, inputs = load_original(args.reports, args.game)
    validate_original(rows, images, original, inputs)
    require(sha((args.reports / "click-v3-a.json").read_bytes()) == SOURCE_SHA,
            "第三張卡片原版收據指紋不符")
    original_palette = args.palette.read_bytes()
    require(len(original_palette) == 768 and max(original_palette) <= 63 and
            sha(original_palette) == PALETTE_SHA == rows["click-v3-a"]["state"]["palette_sha256"],
            "同狀態原版色盤不符")
    indexed = (args.reports / "click-v3-a.away-settled.idx").read_bytes()
    require(len(indexed) == 64000 and sha(indexed) == rows["click-v3-a"]["state"]["indexed_sha256"],
            "同狀態原版索引畫面不符")
    final = (args.reports / "click-v3-a.away-settled.canvas").read_bytes()
    require(len(final) == 64000 and sha(final) == rows["click-v3-a"]["state"]["canvas_sha256"],
            "同狀態原版底層畫布不符")
    font_bytes = args.font.read_bytes()
    require(sha(font_bytes) == FONT_SHA, "Cubic 11 字型版本不符")
    coverage = cmap_coverage(font_bytes)
    catalog = read_catalog(args.catalog)
    chosen = []
    for field in FIELDS:
        matches = [row for row in catalog if row["candidate_id"] == field["key"]]
        require(len(matches) == 1 and matches[0]["status"] == "draft", "真譯稿缺鍵或重複：" + field["key"])
        row = matches[0]
        require(row["source_file"] == field["source"] and
                int(row["byte_offset"], 0) == field["offset"] and
                original[field["source"]][field["offset"]:field["offset"] + len(field["original"])] == field["original"] and
                row["source_bytes_sha256"] == sha(field["original"]), "原版譯文來源鍵不符：" + field["key"])
        chosen.append(row)
    validate_sources(chosen, args.game)
    args.out.mkdir(parents=True, exist_ok=True)
    require(args.out.stat().st_uid == os.getuid(), "輸出目錄擁有者不符")
    catalog_sha = sha(args.catalog.read_bytes())
    summary = {"prototype": True, "source_receipt_sha256": SOURCE_SHA,
               "input_sha256": rows["click-v3-a"]["input_sha256"],
               "indexed_sha256": sha(indexed), "palette_sha256": sha(original_palette),
               "font_sha256": FONT_SHA, "catalog_sha256": catalog_sha, "styles": {}}
    for style in ("faithful", "readable"):
        layers = []
        for field, row in zip(FIELDS, chosen):
            text, background = field_data(field, row, args.font, coverage, args.reports, final)
            layers.append(make_layer(field, text, background, args.font, style, coverage))
        require(layers[0]["safe"][3] == layers[1]["safe"][1], "兩欄安全矩形重疊或斷層")
        payload = {"prototype": True, "style": style, "source_receipt_sha256": SOURCE_SHA,
                   "catalog_sha256": catalog_sha, "font_sha256": FONT_SHA,
                   "indexed": base64.b64encode(indexed).decode(),
                   "palette": base64.b64encode(original_palette).decode(), "layers": layers}
        (args.out / f"{style}.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        summary["styles"][style] = [{k: v for k, v in layer.items() if k not in ("background", "mask")}
                                    for layer in layers]
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    try:
        prepare(parser.parse_args())
    except FileNotFoundError as exc:
        print("SKIP 77：缺合法原版或本機收據：", exc)
        raise SystemExit(77)


if __name__ == "__main__":
    main()
