#!/usr/bin/env python3
"""僅在 workplace 產生 @BUILD1 單行字幕可丟棄對照；不接正式輸出層。"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
ORIGINAL = b"^^In the Year of Our Lord One Thousand Four Hundred Ninety-Two,"
KEY = "GAME.TXT:0x000153CC"
SOURCE = (0x153CC, 0x153CC + len(ORIGINAL))
ORIGINAL_BBOX = (16, 30, 303, 39)
SAFE = (12, 27, 307, 42)
DEFAULT_FONT_SIZE = 38


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rgb(palette, index):
    values = palette[index * 3:index * 3 + 3]
    return tuple((value << 2) | (value >> 4) for value in values)


def picture(canvas, palette):
    image = Image.frombytes("P", (320, 200), canvas)
    image.putpalette(bytes((value << 2) | (value >> 4) for value in palette))
    return image.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)


def main(args):
    need(args.output.is_dir() and args.output.stat().st_uid == os.getuid(),
         "輸出目錄不存在或擁有者不符")
    need(all(not (args.output / name).exists()
             for name in ("original.png", "candidate.png", "preview.json")),
         "拒絕覆寫既有樣本")
    game = (args.game / "GAME.TXT").read_bytes()
    font_bytes = args.font.read_bytes()
    before, after, palette = (path.read_bytes() for path in
                              (args.preprint, args.final, args.palette))
    need(sha(game) == GAME_SHA and game[slice(*SOURCE)] == ORIGINAL,
         "固定原版 GAME.TXT 或字幕來源不符")
    need(sha(font_bytes) == FONT_SHA, "固定 Cubic 11 字型不符")
    need(len(before) == len(after) == 64000 and len(palette) == 768 and
         max(palette) <= 63, "原版索引畫布或色盤形狀不符")
    changed = [(i % 320, i // 320, after[i]) for i in range(64000)
               if before[i] != after[i]]
    need(len(changed) == 1040 and
         (min(x for x, _, _ in changed), min(y for _, y, _ in changed),
          max(x for x, _, _ in changed) + 1,
          max(y for _, y, _ in changed) + 1) == ORIGINAL_BBOX and
         {value for _, _, value in changed} == {14, 47, 54},
         "原版字幕印前／印後墨跡或色號不符")
    with args.catalog.open(encoding="utf-8", newline="") as stream:
        rows = [row for row in csv.DictReader(stream, delimiter="\t")
                if row["candidate_id"] == KEY]
    need(len(rows) == 1, "字幕 TSV 鍵缺失或重複")
    row = rows[0]
    need(row["source_file"] == "GAME.TXT" and
         row["source_sha256"] == GAME_SHA and
         row["byte_offset"] == "0x000153CC" and
         row["source_byte_length"] == str(len(ORIGINAL)) and
         row["source_bytes_sha256"] == sha(ORIGINAL) and
         row["status"] == "draft" and row["zh_hant"].startswith("^^") and
         row["zh_hant"].count("^") == 2,
         "字幕來源、草稿狀態或控制碼不符")
    text = row["zh_hant"][2:]
    need(text and "\n" not in text and "\t" not in text,
         "本樣本僅支持無控制字元單行字幕")
    cmap = TTFont(args.font).getBestCmap()
    need(all(ord(char) in cmap for char in text), "固定字型缺少繁中字形")
    font = ImageFont.truetype(str(args.font), args.font_size)
    bounds = font.getbbox(text)
    font_width, font_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    need(font_width > 0 and font_height > 0, "字型框無效")
    mask = Image.new("L", (font_width, font_height), 0)
    ImageDraw.Draw(mask).text((-bounds[0], -bounds[1]), text, font=font, fill=255)
    ink = mask.getbbox()
    need(ink is not None, "字模沒有可見墨跡")
    mask = mask.crop(ink)
    width, height = mask.size
    need(abs(height - 4 * 9) <= 4, "中文字級明顯偏離原版四倍墨跡高")
    x = (ORIGINAL_BBOX[0] + ORIGINAL_BBOX[2]) * 2 - width // 2
    y = ORIGINAL_BBOX[1] * 4
    foreground = (x, y, x + width, y + height)
    shadow = (x + 4, y + 4, x + width + 4, y + height + 4)
    safe = tuple(value * 4 for value in SAFE)
    need(all(safe[0] <= box[0] < box[2] <= safe[2] and
             safe[1] <= box[1] < box[3] <= safe[3]
             for box in (foreground, shadow)),
         "中文墨跡或陰影超出字幕安全矩形")
    original = picture(after, palette)
    candidate = picture(before, palette)
    candidate.paste(rgb(palette, 47), (x + 4, y + 4), mask)
    candidate.paste(rgb(palette, 14), (x, y), mask)
    original.save(args.output / "original.png")
    candidate.save(args.output / "candidate.png")
    receipt = {
        "scope": "@BUILD1 單行字幕本機可丟棄樣本，非正式覆蓋",
        "source_key": KEY, "source_sha256": sha(ORIGINAL),
        "game_sha256": GAME_SHA, "font_sha256": FONT_SHA,
        "preprint_sha256": sha(before), "final_canvas_sha256": sha(after),
        "palette_sha256": sha(palette), "catalog_sha256": sha(args.catalog.read_bytes()),
        "translation_sha256": sha(row["zh_hant"].encode()),
        "original_ink_bbox": ORIGINAL_BBOX, "original_ink_height_scaled": 36,
        "candidate_ink_height_delta": height - 36,
        "safe_logical": SAFE, "safe_scaled": safe, "font_size": args.font_size,
        "font_bbox": bounds, "actual_mask_crop": ink,
        "candidate_ink_size": [width, height], "foreground_bbox": foreground,
        "shadow_bbox": shadow, "foreground_index": 14, "shadow_index": 47,
        "original_png_sha256": sha((args.output / "original.png").read_bytes()),
        "candidate_png_sha256": sha((args.output / "candidate.png").read_bytes()),
    }
    (args.output / "preview.json").write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(f"PASS：@BUILD1 {args.font_size}px 繁中樣本；墨跡／陰影在安全矩形內，未接正式視窗")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--preprint", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font-size", type=int, choices=(38, 42),
                        default=DEFAULT_FONT_SIZE)
    main(parser.parse_args())
