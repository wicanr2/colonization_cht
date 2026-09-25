#!/usr/bin/env python3
"""依規格026目標141，從唯一譯稿、英格蘭字幕變數值與固定字型烘製 @BUILD2～10 本機字模；不得加入 Git。"""

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from prototype_overlay import FONT_SHA, cmap_coverage
from validate_translation_draft import read_catalog, validate_sources


# 字幕 → 譯稿鍵（依原版行序）。原版字高 9 邏輯像素，沿 @BUILD1 A 取 38px。
CAPTIONS = {
    "@BUILD2": ("GAME.TXT:0x0001542B", "GAME.TXT:0x00015457"),
    "@BUILD3": ("GAME.TXT:0x00015482",),
    "@BUILD4": ("GAME.TXT:0x000154CB",),
    "@BUILD5": ("GAME.TXT:0x00015522",),
    "@BUILD6": ("GAME.TXT:0x0001555D",),
    "@BUILD7": ("GAME.TXT:0x00015597",),
    "@BUILD8": ("GAME.TXT:0x000155F5",),
    "@BUILD9": ("GAME.TXT:0x0001563F",),
    "@BUILD10": ("GAME.TXT:0x00015695",),
}
FONT_SIZE = 38
LINE_PITCH = 40  # 原版兩行字幕行距 10 邏輯像素
MAX_WIDTH = 1180 - 8  # 安全區 [12,307) 四倍寬，扣左右內距與陰影
VALUES_FIELDS = ["nation", "caption", "placeholder", "source_file", "source_file_sha256", "byte_offset",
                 "source_byte_length", "source_bytes_sha256", "source_text", "observed_text", "zh_hant",
                 "status", "evidence"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def values_for(path, game, caption):
    rows = list(csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8")), delimiter="\t", strict=True))
    require(rows and list(rows[0]) == VALUES_FIELDS, "字幕變數 TSV 欄位不符")
    out = {}
    for row in rows:
        if row["nation"] != "england" or row["caption"] != caption:
            continue
        require(row["placeholder"] not in out, "字幕變數重複：" + caption + row["placeholder"])
        source = (game / row["source_file"]).read_bytes()
        offset, length = int(row["byte_offset"], 0), int(row["source_byte_length"])
        require(sha(source) == row["source_file_sha256"] and
                source[offset:offset + length] == row["source_text"].encode("ascii") and
                row["observed_text"] == row["source_text"] and row["zh_hant"] and row["status"] == "draft",
                "字幕變數來源不符：" + caption + row["placeholder"])
        out[row["placeholder"]] = row["zh_hant"]
    return out


def lines_for(rows, values, keys):
    lines = []
    for key in keys:
        matches = [row for row in rows if row["candidate_id"] == key]
        require(len(matches) == 1, "譯稿缺鍵或重複：" + key)
        text = matches[0]["zh_hant"]
        require(text.startswith("^^") and "^" not in text[2:], "字幕控制碼不符：" + key)
        text = text[2:]
        for name in re.findall(r"%STRING\d", text):
            require(name in values, "字幕變數缺值：" + key + name)
        text = re.sub(r"%STRING\d", lambda m: values[m.group(0)], text)
        require(text and "%" not in text, "字幕譯文展開不完整：" + key)
        lines.append(text)
    return lines


def ink(font, text):
    left, top, right, bottom = font.getbbox(text)
    full = Image.new("L", (right - left, bottom - top))
    ImageDraw.Draw(full).text((-left, -top), text, fill=255, font=font)
    box = full.getbbox()
    require(box is not None, "字幕字模沒有可見墨跡")
    return full.crop(box)


def bake(args):
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(), "本機輸出目錄不存在或擁有者不符")
    rows = read_catalog(args.catalog)
    validate_sources(rows, args.game)
    font_bytes = args.font.read_bytes()
    require(sha(font_bytes) == FONT_SHA, "Cubic 11 指紋不符")
    coverage = cmap_coverage(font_bytes)
    font = ImageFont.truetype(str(args.font), FONT_SIZE)
    catalog_sha, values_sha = sha(args.catalog.read_bytes()), sha(args.values.read_bytes())
    for caption, keys in CAPTIONS.items():
        lines = lines_for(rows, values_for(args.values, args.game, caption), keys)
        require(all(ord(c) in coverage for line in lines for c in line), "字幕譯文有缺字：" + caption)
        masks = [ink(font, line) for line in lines]
        width = max(m.width for m in masks)
        require(width <= MAX_WIDTH, "字幕譯文超出安全寬度：" + caption)
        height = LINE_PITCH * (len(masks) - 1) + masks[-1].height
        canvas = Image.new("L", (width, height))
        for i, m in enumerate(masks):
            # 各行以共同中線置中，頂端對齊原版行距。
            canvas.paste(m, ((width - m.width) // 2, LINE_PITCH * i))
        text = "\n".join(lines)
        payload = {"candidate_id": keys[0], "caption": caption, "keys": list(keys),
                   "translation_sha256": sha(text.encode("utf-8")), "catalog_sha256": catalog_sha,
                   "values_sha256": values_sha, "font_sha256": FONT_SHA, "font_size": FONT_SIZE,
                   "width": width, "height": height, "alpha": base64.b64encode(canvas.tobytes()).decode(),
                   "scope": "local-only；衍生字模不加入 Git 或散布包"}
        path = args.output / (keys[0].replace(":", "-") + ".json")
        path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{caption}：{width}×{height}，{len(lines)} 行；{' / '.join(lines)}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/draft.zh-Hant.tsv"))
    p.add_argument("--values", type=Path, default=Path("/repo/text/build-caption-values.zh-Hant.tsv"))
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "GAME.TXT").is_file() or not (args.game / "NAMES.TXT").is_file():
        print("SKIP：缺少合法原版，未產生字模")
        return 77
    bake(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
