#!/usr/bin/env python3
"""依規格017／019／020（及規格016第三張卡 A 版）產生難度卡片及國家標題逐欄本機字模；不得加入 Git。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from prototype_overlay import FONT_SHA, cmap_coverage
from validate_translation_draft import read_catalog, validate_sources


FIELDS = (
    ("NAMES.TXT:0x00000C0C", 21, (69, 19), (138, 44, 186, 51), (614, 180)),
    ("LABELS.TXT:0x000008A9", 25, (81, 23), (146, 52, 180, 60), (612, 212)),
    ("NAMES.TXT:0x00000C18", 21, (69, 19), (247, 44, 287, 51), (1034, 180)),
    ("LABELS.TXT:0x000008B2", 25, (54, 23), (256, 52, 279, 60), (1043, 212)),
    ("LABELS.TXT:0x000008D3", 38, (82, 35), (39, 35, 73, 46), (183, 144)),
    ("LABELS.TXT:0x000008DB", 38, (164, 35), (17, 48, 95, 59), (142, 196)),
)

# 規格016目標121／139：第三張卡 A 版，另烘到獨立目錄，不改前兩張卡的既有字模集。
THIRD_CARD_FIELDS = (
    ("NAMES.TXT:0x00000C22", 21, (69, 19), (29, 139, 84, 148), (192, 564)),
    ("LABELS.TXT:0x000008B8", 25, (54, 23), (38, 148, 76, 157), (201, 596)),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bake(args):
    if not args.output.is_dir() or args.output.stat().st_uid != os.getuid():
        raise ValueError("本機輸出目錄不存在或擁有者不符")
    rows = read_catalog(args.catalog)
    validate_sources(rows, args.game)
    font_bytes = args.font.read_bytes()
    if sha(font_bytes) != FONT_SHA:
        raise ValueError("Cubic 11 指紋不符")
    coverage = cmap_coverage(font_bytes)
    for key, size, expected_ink, safe, position in (THIRD_CARD_FIELDS if args.third_card else FIELDS):
        matches = [row for row in rows if row["candidate_id"] == key]
        if len(matches) != 1 or not matches[0]["zh_hant"]:
            raise ValueError("欄位 TSV 缺鍵或重複：" + key)
        text = matches[0]["zh_hant"]
        if any(ord(char) not in coverage for char in text):
            raise ValueError("欄位譯文有缺字：" + key)
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(text)
        width, height = right - left, bottom - top
        if (width, height) != expected_ink:
            raise ValueError("譯文或字級墨跡已變，需重新審查規格017／019：" + key)
        x, y = position
        if not (safe[0] * 4 + 4 <= x and x + width <= safe[2] * 4 - 4 and
                safe[1] * 4 <= y and y + height <= safe[3] * 4 - 4):
            raise ValueError("欄位字模超出內距：" + key)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), text, font=font, fill=255)
        payload = {"candidate_id": key, "translation_sha256": sha(text.encode()),
                   "font_sha256": FONT_SHA, "font_size": size,
                   "width": width, "height": height,
                   "alpha": base64.b64encode(mask.tobytes()).decode(),
                   "scope": "規格017／019／020本機字模；不得散布原版素材或字型"}
        path = args.output / (key.replace(":", "-") + ".json")
        path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{key}：{width}×{height}，{size}px；{path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("/repo/text/draft.zh-Hant.tsv"))
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--third-card", action="store_true", help="只烘第三張難度卡 A 版兩欄")
    bake(parser.parse_args())
