#!/usr/bin/env python3
"""目標082：從固定原版收據製作第二張難度卡片的可丟棄 Ebitengine 預覽。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from prototype_overlay import cmap_coverage
from validate_translation_draft import read_catalog, validate_sources


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
FIELDS = (
    ("title", "NAMES.TXT:0x00000C18", "NAMES.TXT", 0xC18, b"Explorer",
     "EXPLORER:", (247, 44, 287, 51), (250, 45, 283, 49), 134, 21, (69, 19), (1034, 180)),
    ("subtitle", "LABELS.TXT:0x000008B2", "LABELS.TXT", 0x8B2, b"Easy",
     "Easy", (256, 52, 279, 60), (260, 53, 275, 58), 55, 25, (54, 23), (1043, 212)),
)
SOURCES = {
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def prepare(args):
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "本機輸出目錄不存在或擁有者不符")
    p = args.reports
    load_a, load_b = ((p / f"load-{letter}.json").read_bytes() for letter in "ab")
    trace_a, trace_b = ((p / f"trace-v3{letter}.json").read_bytes() for letter in "ab")
    require(load_a == load_b and trace_a == trace_b, "雙次原版收據不一致")
    load, trace = json.loads(load_a), json.loads(trace_a)
    require(load["version"] == "goal081-second-card-load-v1" and
            trace["version"] == "goal081-second-card-v3" and
            not load["reads_truncated"] and not load["writes_truncated"] and
            trace["difficulty_art_opened"], "原版收據不完整")
    indexed = (p / "click.final.idx").read_bytes()
    palette = (p / "click.final.pal").read_bytes()
    require(len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63 and
            sha(indexed) == trace["state"]["indexed_sha256"] and
            sha(palette) == trace["state"]["palette_sha256"], "原始畫面或色盤不符")
    require((p / "window-second-card.final.idx").read_bytes() == indexed and
            (p / "window-second-card-control.final.idx").read_bytes() == indexed,
            "真視窗與受控原版畫面不一致")
    click = json.loads((p / "click.inputs.json").read_text())
    require(click["end"] == 40000000 and len(click["inputs"]) == 13 and
            click["inputs"][-1]["kind"] == "move" and
            (click["inputs"][-1]["x"], click["inputs"][-1]["y"]) == (16, 16),
            "第二張卡片固定重播終點不符")
    rows = read_catalog(args.catalog)
    validate_sources(rows, args.game)
    source_data = {name: (args.game / name).read_bytes() for name in SOURCES}
    require(all(sha(source_data[name]) == expected for name, expected in SOURCES.items()),
            "原始 TXT 指紋不符")
    font_bytes = args.font.read_bytes()
    require(sha(font_bytes) == FONT_SHA, "Cubic 11 字型指紋不符")
    coverage = cmap_coverage(font_bytes)
    layers = []
    for name, key, source_name, offset, original, display, safe, ink_bbox, pixels, size, expected, position in FIELDS:
        matches = [row for row in rows if row["candidate_id"] == key]
        require(len(matches) == 1 and matches[0]["status"] == "draft" and
                matches[0]["zh_hant"], "譯文鍵缺失、重複或狀態不符：" + key)
        row = matches[0]
        require(row["source_file"] == source_name and int(row["byte_offset"], 0) == offset and
                source_data[source_name][offset:offset + len(original)] == original and
                row["source_sha256"] == SOURCES[source_name] and
                row["source_bytes_sha256"] == sha(original) and
                int(row["source_byte_length"]) == len(original), "譯文來源不符：" + key)
        require(all(ord(char) in coverage for char in row["zh_hant"]), "字型缺字：" + key)
        before = (p / f"trace-v3a.before-{name}-ink.canvas").read_bytes()
        after = (p / f"trace-v3a.after-{name}-ink.canvas").read_bytes()
        require(len(before) == len(after) == 64000 and
                rect_bytes(after, safe) == rect_bytes(indexed, safe) and
                len(set(rect_bytes(before, safe))) == 65, "畫布快照、終點或紋理底圖不符：" + key)
        changed = [(i % 320, i // 320) for i, (a, b) in enumerate(zip(before, after)) if a != b]
        require(len(changed) == pixels and
                (min(x for x, _ in changed), min(y for _, y in changed),
                 max(x for x, _ in changed), max(y for _, y in changed)) == ink_bbox and
                all(safe[0] <= x < safe[2] and safe[1] <= y < safe[3] for x, y in changed),
                "原版墨跡或安全矩形不符：" + key)
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(row["zh_hant"])
        width, height = right - left, bottom - top
        require((width, height) == expected and
                abs(height - (ink_bbox[3] - ink_bbox[1] + 1) * 4) <= 1,
                "候選字級或譯文墨跡變動：" + key)
        x, y = position
        require(x == (safe[0] + safe[2]) * 2 - width // 2 and y == ink_bbox[1] * 4 and
                safe[0] * 4 + 4 <= x and x + width <= safe[2] * 4 - 4 and
                safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
                "中文字形位置、置中或四邊內距不符：" + key)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), row["zh_hant"], font=font, fill=255)
        layers.append({"name": name, "candidate_id": key, "display": display,
                       "safe": safe, "original_ink_bbox": ink_bbox,
                       "original_ink_height_scaled": (ink_bbox[3] - ink_bbox[1] + 1) * 4,
                       "font_size": size, "ink_width": width, "ink_height": height,
                       "position": position, "translation_sha256": sha(row["zh_hant"].encode()),
                       "background_palette_indices": len(set(rect_bytes(before, safe))),
                       "background": base64.b64encode(rect_bytes(before, safe)).decode(),
                       "mask": base64.b64encode(mask.tobytes()).decode()})
    payload = {"prototype": True, "source_receipt_sha256": sha(trace_a),
               "source_load_receipt_sha256": sha(load_a),
               "catalog_sha256": sha(args.catalog.read_bytes()), "font_sha256": FONT_SHA,
               "indexed": base64.b64encode(indexed).decode(),
               "palette": base64.b64encode(palette).decode(), "layers": layers}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"prototype": True, "source_receipt_sha256": sha(trace_a),
                      "layers": [{k: v for k, v in layer.items() if k not in ("background", "mask")}
                                 for layer in layers]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())
