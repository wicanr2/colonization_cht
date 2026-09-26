#!/usr/bin/env python3
"""由固定原始 Cubic 11 與真實旗卡片段直接烘製旗卡 A 版字模（預設第一張兩欄；--rest 為其餘三張六欄）。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate_nation_card_fragments import FONT_SHA, validate


FIELDS = (
    ("NAMES.TXT:0x000008EA", 21, (69, 19), (590, 60), (125, 12, 190, 24), True),  # 目標157：「英國：」，維持兩欄共同中心 x=624（.5 進位，同法國旗卡）
    ("LABELS.TXT:0x000008F2", 25, (54, 23), (597, 348), (125, 83, 190, 96), False),
)

# 規格022目標140：其餘三張旗卡，與第一張同為上欄21px、下欄25px，各欄以旗卡中線置中。
REST_FIELDS = (
    ("NAMES.TXT:0x00000906", 21, (69, 19), (986, 60), (225, 12, 290, 24), True),
    ("LABELS.TXT:0x000008FF", 25, (54, 23), (993, 348), (225, 83, 290, 96), False),
    ("NAMES.TXT:0x00000921", 21, (92, 19), (578, 424), (125, 103, 190, 115), True),
    ("LABELS.TXT:0x0000090C", 25, (54, 23), (597, 712), (125, 174, 190, 187), False),
    ("NAMES.TXT:0x0000093D", 21, (69, 19), (986, 424), (225, 103, 290, 115), True),
    ("LABELS.TXT:0x00000916", 25, (54, 23), (993, 712), (225, 174, 290, 187), False),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bake(args):
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(),
            "本機輸出目錄不存在或擁有者不符")
    require(args.font.is_file(), "固定 Cubic 11 原始字型不存在")
    rows = {row["candidate_id"]: row for row in validate(args.catalog, args.game, args.font)}
    outputs = []
    for key, size, expected_ink, position, safe, suffix_colon in (REST_FIELDS if getattr(args, "rest", False) else FIELDS):
        path = args.output / (key.replace(":", "-") + ".json")
        require(not path.exists(), "拒絕覆寫既有本機字模：" + key)
        text = rows[key]["zh_hant"] + ("：" if suffix_colon else "")
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(text)
        width, height = right - left, bottom - top
        require((width, height) == expected_ink, "字型或字級墨跡與規格021不符：" + key)
        x, y = position
        require(safe[0] * 4 + 4 <= x and x + width + 4 <= safe[2] * 4 - 4 and
                safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
                "字模或陰影超出安全內距：" + key)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), text, font=font, fill=255)
        payload = {"candidate_id": key,
                   "translation_sha256": sha(text.encode("utf-8")),
                   "font_sha256": FONT_SHA,
                   "font_size": size,
                   "width": width, "height": height,
                   "alpha": base64.b64encode(mask.tobytes()).decode("ascii"),
                   "local_only": True}
        outputs.append((path, payload))
    for path, payload in outputs:
        path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{payload['candidate_id']}：{payload['width']}×{payload['height']}，"
              f"{payload['font_size']}px；直接由固定 TTF 烘製")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rest", action="store_true", help="烘其餘三張旗卡六欄")
    args = parser.parse_args()
    if not args.game.is_dir() or any(not (args.game / name).is_file()
                                     for name in ("NAMES.TXT", "LABELS.TXT")):
        print("SKIP：缺少合法原版 NAMES.TXT／LABELS.TXT，未產生字模")
        return 77
    bake(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
