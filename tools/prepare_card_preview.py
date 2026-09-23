#!/usr/bin/env python3
"""從固定原版收據製作本機卡片預覽資料；只供可丟棄 Ebitengine 原型。"""

import argparse
import base64
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from check_card_load import verify as verify_card_load
from prototype_overlay import cmap_coverage


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
PALETTE_SHA = "762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82"
FINAL_SHA = "6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae"
SOURCES = {
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
}
LINES = (
    ("title", "NAMES.TXT:0x00000C0C", (138, 44, 186, 51), (141, 45, 182, 49), 21, 20, "before-first"),
    ("subtitle", "LABELS.TXT:0x000008A9", (146, 52, 180, 60), (150, 53, 174, 58), 25, 24, "before-second"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def prepare(args):
    verify_card_load(args.inputs, args.load_first, args.load_second, args.first, args.second)
    replay = json.loads(args.inputs.read_text(encoding="utf-8"))
    cursor = None
    held = set()
    for event in replay["inputs"]:
        if event["kind"] == "move":
            cursor = (event["x"], event["y"])
        elif event["kind"] == "press":
            held.add(event["button"])
        elif event["kind"] == "release":
            held.discard(event["button"])
    check(cursor is not None and not held and not (112 <= cursor[0] < 212 and 24 <= cursor[1] < 80),
          "游標或按鍵狀態可能遮擋卡片，回退原文")
    first = args.first.read_bytes()
    second = args.second.read_bytes()
    check(first == second, "兩份原版收據不一致")
    report = json.loads(first)
    check(report["version"] == "goal075-card-flow-v5" and report["end"] == 32000000
          and report["difficulty_art_opened"] and not report["exited"] and not report["writes_truncated"],
          "原版收據不符合固定正常玩家路徑")
    snapshots = {k: base64.b64decode(v, validate=True) for k, v in report["snapshots"].items()}
    check(all(len(v) == 64000 for v in snapshots.values()), "畫布快照長度不符")
    check(snapshots["after-first"] == snapshots["before-second"], "兩行間畫布改變")
    final = args.indexed.read_bytes()
    palette = args.palette.read_bytes()
    font_data = args.font.read_bytes()
    check(len(final) == 64000 and sha(final) == FINAL_SHA, "同狀態原版畫面不符")
    check(len(palette) == 768 and sha(palette) == PALETTE_SHA and max(palette) <= 63, "原版色盤不符")
    check(sha(font_data) == FONT_SHA, "字型版本不符")
    coverage = cmap_coverage(font_data)
    check(report["palette_sha256"] == PALETTE_SHA and report["indexed_sha256"] == FINAL_SHA,
          "卡片收據與真視窗原版畫面不一致")
    catalog = {}
    with args.catalog.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            check(row["candidate_id"] not in catalog, "譯文鍵重複")
            catalog[row["candidate_id"]] = row
    source_data = {name: (args.game / name).read_bytes() for name in SOURCES}
    check(all(sha(source_data[name]) == want for name, want in SOURCES.items()), "原始 TXT 版本不符")
    layers = []
    for name, key, safe, ink_bbox, font_size, target_height, before_name in LINES:
        row = catalog[key]
        source = source_data[row["source_file"]]
        start = int(row["byte_offset"], 0)
        length = int(row["source_byte_length"])
        check(row["status"] == "draft" and row["source_sha256"] == SOURCES[row["source_file"]]
              and sha(source[start:start + length]) == row["source_bytes_sha256"] and row["zh_hant"],
              "譯文候選來源不符：" + key)
        check(all(ord(char) in coverage for char in row["zh_hant"]), "字型缺少譯文字形：" + name)
        before = snapshots[before_name]
        after = snapshots["after-first" if name == "title" else "after-second"]
        changed = [(i % 320, i // 320) for i in range(64000) if before[i] != after[i]]
        check(changed and (min(x for x, _ in changed), min(y for _, y in changed),
                           max(x for x, _ in changed), max(y for _, y in changed)) == ink_bbox,
              "原版文字墨跡位置不符：" + name)
        check(all(final[y * 320 + x] == snapshots["after-second"][y * 320 + x]
                  for y in range(safe[1], safe[3]) for x in range(safe[0], safe[2])),
              "後續畫面遮住卡片文字：" + name)
        check(len(set(rect_bytes(before, safe))) > 50, "卡片背景不可視為純色：" + name)
        font = ImageFont.truetype(str(args.font), font_size)
        left, top, right, bottom = font.getbbox(row["zh_hant"])
        width, height = right - left, bottom - top
        check(abs(height - target_height) <= 1 and 0 < width <= (safe[2] - safe[0]) * 4 - 8
              and height <= (safe[3] - safe[1]) * 4 - 4, "中文字級或安全矩形不符：" + name)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), row["zh_hant"], font=font, fill=255)
        x = (safe[0] + safe[2]) * 2 - width // 2
        y = ink_bbox[1] * 4
        check(x >= safe[0] * 4 + 4 and x + width <= safe[2] * 4 - 4
              and y >= safe[1] * 4 and y + height <= safe[3] * 4 - 4,
              "中文字形溢出或頂列不符：" + name)
        layers.append({"name": name, "candidate_id": key, "safe": safe,
                       "original_ink_bbox": ink_bbox, "original_ink_height_scaled": target_height,
                       "font_size": font_size, "ink_width": width, "ink_height": height,
                       "position": [x, y], "translation_sha256": sha(row["zh_hant"].encode()),
                       "background": base64.b64encode(rect_bytes(before, safe)).decode(),
                       "mask": base64.b64encode(mask.tobytes()).decode()})
    payload = {"prototype": True, "source_receipt_sha256": sha(first),
               "source_load_receipt_sha256": sha(args.load_first.read_bytes()),
               "catalog_sha256": sha(args.catalog.read_bytes()), "font_sha256": FONT_SHA,
               "indexed": base64.b64encode(final).decode(), "palette": base64.b64encode(palette).decode(),
               "layers": layers}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("indexed", "palette", "layers")}
                     | {"layers": [{k: v for k, v in layer.items() if k not in ("background", "mask")}
                                   for layer in layers]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--load-first", type=Path, required=True)
    parser.add_argument("--load-second", type=Path, required=True)
    parser.add_argument("--indexed", type=Path, required=True)
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())
