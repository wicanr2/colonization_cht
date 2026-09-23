#!/usr/bin/env python3
"""以固定原版收據準備右側旗卡的本機 Ebitengine 可丟棄預覽。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from check_goal091_neighbor_background import FIELDS, check, rect_bytes
from validate_nation_card_fragments import validate


KEYS = {"upper": "NAMES.TXT:0x00000906", "lower": "LABELS.TXT:0x000008FF"}
SIZES = {"faithful": {"upper": (21, (69, 19)), "lower": (25, (54, 23))},
         "readable": {"upper": (25, (81, 23)), "lower": (29, (62, 27))}}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare(args):
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "本機輸出目錄不存在或擁有者不符")
    source = check(args.reports)
    rows = {row["candidate_id"]: row for row in validate(args.catalog, args.game, args.font)}
    indexed = (args.reports / "goal091-a.final.idx").read_bytes()
    palette = (args.reports / "goal091-a.final.pal").read_bytes()
    require(sha(indexed) == source["indexed_sha256"]
            and sha(palette) == source["palette_sha256"]
            and palette[9 * 3:9 * 3 + 3] == bytes((1, 34, 56))
            and palette[:3] == b"\0\0\0", "右側原版前景／陰影色盤不符")
    layers = []
    for name, safe, bbox in FIELDS:
        field = source["fields"][name]
        require(tuple(safe) == tuple(field["safe"]) and
                tuple(bbox) == tuple(field["original_bbox"]),
                "獨立背景收據與欄位預期不符：" + name)
        before = (args.reports / f"goal091-a.before-{name}.canvas").read_bytes()
        background = rect_bytes(before, safe)
        require(sha(background) == field["background_sha256"], "可逆底圖雜湊不符：" + name)
        text = rows[KEYS[name]]["zh_hant"] + ("：" if name == "upper" else "")
        size, expected_ink = SIZES[args.variant][name]
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(text)
        width, height = right - left, bottom - top
        require((width, height) == expected_ink and
                abs(height - (bbox[3] - bbox[1] + 1) * 4) <=
                (1 if args.variant == "faithful" else 4),
                "逐欄字級／原版墨跡高度不符：" + name)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), text, font=font, fill=255)
        x, y = 1020 - width // 2, bbox[1] * 4
        require(safe[0] * 4 + 4 <= x and x + width + 4 <= safe[2] * 4 - 4
                and safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
                "字模或右移一原版像素陰影超出安全內距：" + name)
        layers.append({"name": name, "candidate_id": KEYS[name], "safe": safe,
                       "original_ink_bbox": bbox,
                       "original_ink_height_scaled": (bbox[3] - bbox[1] + 1) * 4,
                       "original_changed_pixels": field["changed_pixels"],
                       "background_palette_indices": field["background_palette_indices"],
                       "font_size": size, "ink_width": width, "ink_height": height,
                       "position": [x, y], "color_index": 9, "shadow_index": 0,
                       "shadow_dx": 4, "translation_sha256": sha(text.encode()),
                       "background": base64.b64encode(background).decode(),
                       "mask": base64.b64encode(mask.tobytes()).decode()})
    payload = {"prototype": True, "variant": args.variant,
               "source_receipt_sha256": source["source_receipt_sha256"],
               "control_receipt_sha256": source["control_receipt_sha256"],
               "catalog_sha256": sha(args.catalog.read_bytes()),
               "font_sha256": sha(args.font.read_bytes()),
               "indexed": base64.b64encode(indexed).decode(),
               "palette": base64.b64encode(palette).decode(), "layers": layers}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"prototype": True, "variant": args.variant,
                      "layers": [{k: v for k, v in layer.items()
                                  if k not in ("background", "mask")} for layer in layers]},
                     ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=tuple(SIZES), default="faithful")
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
