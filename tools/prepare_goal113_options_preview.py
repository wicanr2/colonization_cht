#!/usr/bin/env python3
"""核對九欄原版印前底圖，產生本機可丟棄的 Ebitengine 對照資料。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate_translation_draft import read_catalog, validate_sources


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
FIXTURE_SHA = "c4e462678323df8e1915ffcd363f7e7eb83cee4e85e09f618c9206418977e539"
SCREEN_SHA = "7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546"
PALETTE_SHA = "b81c99f3ef54dd7015107ece98b6770620b4c3472281172a92f0302f8ec6b4c9"
FIELDS = (
    (0x4CD, (65, 44, 253, 59), (67, 47, 147, 56), 319, 34, 38),
    (0x4E9, (80, 59, 252, 71), (82, 61, 166, 69), 338, 25, 28),
    (0x4FD, (80, 71, 252, 83), (82, 73, 173, 82), 349, 28, 32),
    (0x512, (80, 83, 252, 95), (82, 85, 155, 94), 283, 28, 32),
    (0x525, (80, 95, 252, 107), (82, 97, 133, 105), 186, 25, 28),
    (0x533, (80, 107, 252, 119), (82, 109, 123, 118), 172, 28, 32),
    (0x53E, (80, 119, 252, 131), (82, 121, 158, 130), 316, 28, 32),
    (0x550, (80, 131, 252, 143), (82, 133, 171, 142), 343, 27, 31),
    (0x566, (80, 143, 252, 155), (82, 145, 144, 154), 246, 28, 32),
)


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rect(canvas, safe):
    x0, y0, x1, y1 = safe
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def checked_receipt(reports):
    raw_a = (reports / "preprint-a.json").read_bytes()
    need(raw_a == (reports / "preprint-b.json").read_bytes(), "兩次冷啟動收據不相同")
    a = json.loads(raw_a)
    control = json.loads((reports / "preprint-control.json").read_bytes())
    need(a["version"] == control["version"] == "goal113-game-options-preprint-v1"
         and a["control"] is False and control["control"] is True
         and a["nation"] == "england" and a["follow_until"] == 1300000000
         and a["input_sha256"] == control["input_sha256"] == INPUT_SHA
         and a["game_inputs_sha256"] == control["game_inputs_sha256"] == FIXTURE_SHA
         and len(a["option_preprint"]) == len(FIELDS)
         and not a["option_print_writes"] and not control["option_preprint"]
         and not control["option_print_writes"] and not control["writers"],
         "原版觀測版本、輸入或無監看控制不符")
    for key in ("route", "sources", "transfers", "samples", "opened", "key_events", "game_inputs"):
        need(a[key] == control[key], "監看擾動原版狀態：" + key)
    final = (reports / "preprint-a.1300m.idx").read_bytes()
    palette = (reports / "preprint-a.1300m.pal").read_bytes()
    need(len(final) == 64000 and sha(final) == SCREEN_SHA
         and len(palette) == 768 and sha(palette) == PALETTE_SHA
         and a["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA
         and a["samples"]["1300m"]["palette_sha256"] == PALETTE_SHA,
         "原版1,300M畫布或色盤不符")
    for suffix in ("b", "control"):
        need((reports / f"preprint-{suffix}.1300m.idx").read_bytes() == final
             and (reports / f"preprint-{suffix}.1300m.pal").read_bytes() == palette,
             "原版最終狀態不同：" + suffix)
    return a, raw_a, final, palette


def prepare(args):
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "輸出目錄不存在或不是目前使用者擁有")
    if not (args.game / "GAME.TXT").is_file():
        print("SKIP：合法原版 GAME.TXT 缺失")
        return 77
    need(sha((args.game / "GAME.TXT").read_bytes()) == GAME_SHA, "原版 GAME.TXT 版本不符")
    need(sha(args.font.read_bytes()) == FONT_SHA, "固定 Cubic 11 字型不符")
    rows = {row["candidate_id"]: row for row in read_catalog(args.catalog)}
    keys = [f"GAME.TXT:0x{offset:08X}" for offset, *_ in FIELDS]
    need(all(key in rows for key in keys), "九欄真實 TSV 缺鍵")
    selected = [rows[key] for key in keys]
    validate_sources(selected, args.game)
    a, raw_a, final, palette = checked_receipt(args.reports)
    need(palette[68 * 3:68 * 3 + 3] != palette[47 * 3:47 * 3 + 3],
         "原版文字與陰影色盤相同")
    layers = []
    last_step = 0
    for index, (offset, safe, changed_box, count, faithful, readable) in enumerate(FIELDS):
        name = f"option-{index:02d}"
        stamp = f"option-before-{index:02d}"
        item = a["option_preprint"][stamp]
        before_a = (args.reports / f"preprint-a.{stamp}.canvas").read_bytes()
        before_b = (args.reports / f"preprint-b.{stamp}.canvas").read_bytes()
        need(len(before_a) == 64000 and before_a == before_b
             and sha(before_a) == item["canvas_sha256"]
             and item["safe"] == list(safe) and item["writer_ip"] == "0D21:012C"
             and item["writes"] == count and last_step < item["step"] < 1300000000,
             "原版印前底圖不穩定：" + name)
        last_step = item["step"]
        points = [(n % 320, n // 320) for n, (old, new) in enumerate(zip(before_a, final))
                  if old != new and safe[0] <= n % 320 < safe[2]
                  and safe[1] <= n // 320 < safe[3]]
        need(len(points) == count and
             (min(x for x, _ in points), min(y for _, y in points),
              max(x for x, _ in points) + 1, max(y for _, y in points) + 1) == changed_box,
             "原文印字差分或底圖相位不符：" + name)
        translated = rows[keys[index]]["zh_hant"].replace("~", "")
        need("~" not in translated and (index == 0 or "（" in translated),
             "預覽未保留可見 ASCII 快捷鍵：" + name)
        size = faithful if args.variant == "faithful" else readable
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(translated)
        width, height = right - left, bottom - top
        need(width > 0 and height > 0 and height <= (changed_box[3] - changed_box[1]) * 4 +
             (0 if args.variant == "faithful" else 5), "逐欄候選字高過大：" + name)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), translated, font=font, fill=255)
        x, y = changed_box[0] * 4, changed_box[1] * 4
        need(safe[0] * 4 + 4 <= x and x + width + 4 <= safe[2] * 4 - 4
             and safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
             "中文或陰影沒有安全內距：" + name)
        background = rect(before_a, safe)
        need(len(set(background)) >= 4, "原版底圖顏色過少：" + name)
        layers.append({"name": name, "candidate_id": keys[index], "safe": safe,
                       "original_changed_bbox": changed_box, "original_changed_pixels": count,
                       "original_ink_height_scaled": (changed_box[3] - changed_box[1]) * 4,
                       "font_size": size, "ink_width": width, "ink_height": height,
                       "position": [x, y], "color_index": 68, "shadow_index": 47,
                       "shadow_dx": 4, "translation_sha256": sha(translated.encode()),
                       "background_palette_indices": len(set(background)),
                       "background": base64.b64encode(background).decode(),
                       "mask": base64.b64encode(mask.tobytes()).decode()})
    payload = {"prototype": True, "variant": args.variant,
               "source_receipt_sha256": sha(raw_a), "catalog_sha256": sha(args.catalog.read_bytes()),
               "font_sha256": FONT_SHA, "indexed": base64.b64encode(final).decode(),
               "palette": base64.b64encode(palette).decode(), "layers": layers}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "variant": args.variant,
                      "layers": [{key: value for key, value in layer.items()
                                  if key not in ("background", "mask")}
                                 for layer in layers]}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("faithful", "readable"), required=True)
    args = parser.parse_args()
    try:
        return prepare(args)
    except (OSError, ValueError, KeyError, IndexError) as error:
        parser.exit(1, f"FAIL：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
