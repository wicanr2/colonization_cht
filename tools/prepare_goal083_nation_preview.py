#!/usr/bin/env python3
"""由國家標題固定原版證據建立可丟棄 Ebitengine 中英對照。"""

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
LABELS_SHA = "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204"
FIELDS = (
    ("select", "LABELS.TXT:0x000008D3", 0x8D3, b"Select", "Select",
     (39, 35, 73, 46), (42, 36, 69, 44), 120, 38, (82, 35), (183, 144)),
    ("power", "LABELS.TXT:0x000008DB", 0x8DB, b"European Power", "European Power",
     (17, 48, 95, 59), (20, 49, 91, 57), 270, 38, (164, 35), (142, 196)),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def prepare(args):
    p = args.reports
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "本機輸出目錄不存在或擁有者不符")
    verified = json.loads((p / "nation-evidence-verification.json").read_text())
    require(verified["result"] == "PASS" and verified["nation_art_opened"],
            "國家選擇頁證據尚未通過")
    trace_bytes = (p / "nation-evidence-a.json").read_bytes()
    load_bytes = (p / "label-load-a.json").read_bytes()
    require(sha(trace_bytes) == verified["trace_receipt_sha256"] and
            sha(load_bytes) == verified["load_receipt_sha256"], "固定原版收據已變")
    indexed = (p / "click.final.idx").read_bytes()
    palette = (p / "click.final.pal").read_bytes()
    require(len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63 and
            indexed == (p / "goal083-window.final.idx").read_bytes(),
            "原版索引畫面／色盤不符")
    source = (args.game / "LABELS.TXT").read_bytes()
    require(sha(source) == LABELS_SHA, "LABELS.TXT 版本不符")
    font_bytes = args.font.read_bytes()
    require(sha(font_bytes) == FONT_SHA, "Cubic 11 字型版本不符")
    coverage = cmap_coverage(font_bytes)
    rows = read_catalog(args.catalog)
    validate_sources(rows, args.game)
    layers = []
    for name, key, offset, original, display, safe, bbox, pixels, size, ink, position in FIELDS:
        matches = [row for row in rows if row["candidate_id"] == key]
        require(len(matches) == 1 and matches[0]["status"] == "draft" and
                matches[0]["zh_hant"], "譯文鍵缺失或重複：" + key)
        row = matches[0]
        require(row["source_file"] == "LABELS.TXT" and
                row["source_sha256"] == LABELS_SHA and
                int(row["byte_offset"], 0) == offset and
                int(row["source_byte_length"]) == len(original) and
                row["source_bytes_sha256"] == sha(original) and
                source[offset:offset + len(original)] == original,
                "譯文來源版本不符：" + key)
        require(all(ord(char) in coverage for char in row["zh_hant"]), "Cubic 11 缺字：" + key)
        before = (p / f"nation-evidence-a.before-{name}-source.canvas").read_bytes()
        after = (p / f"nation-evidence-a.after-{name}-ink.canvas").read_bytes()
        require(len(before) == len(after) == 64000 and
                rect_bytes(after, safe) == rect_bytes(indexed, safe),
                "畫布原文與底圖不符：" + key)
        changed = [(i % 320, i // 320) for i, (a, b) in enumerate(zip(before, after)) if a != b]
        require(len(changed) == pixels and
                (min(x for x, _ in changed), min(y for _, y in changed),
                 max(x for x, _ in changed), max(y for _, y in changed)) == bbox and
                all(safe[0] <= x < safe[2] and safe[1] <= y < safe[3] for x, y in changed),
                "原文墨跡不符：" + key)
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(row["zh_hant"])
        width, height = right - left, bottom - top
        require((width, height) == ink and
                abs(height - (bbox[3] - bbox[1] + 1) * 4) <= 1,
                "中文字級與原版墨跡高度不符：" + key)
        x, y = position
        require(x + width // 2 == 224 and y == bbox[1] * 4 and
                safe[0] * 4 + 4 <= x and x + width <= safe[2] * 4 - 4 and
                safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
                "中文字模未置中或超出四邊內距：" + key)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), row["zh_hant"], font=font, fill=255)
        layers.append({"name": name, "candidate_id": key, "display": display,
                       "safe": safe, "original_ink_bbox": bbox,
                       "original_ink_height_scaled": (bbox[3] - bbox[1] + 1) * 4,
                       "font_size": size, "ink_width": width, "ink_height": height,
                       "position": position, "translation_sha256": sha(row["zh_hant"].encode()),
                       "background_palette_indices": len(set(rect_bytes(before, safe))),
                       "background": base64.b64encode(rect_bytes(before, safe)).decode(),
                       "mask": base64.b64encode(mask.tobytes()).decode()})
    payload = {"prototype": True, "source_receipt_sha256": sha(trace_bytes),
               "source_load_receipt_sha256": sha(load_bytes),
               "catalog_sha256": sha(args.catalog.read_bytes()), "font_sha256": FONT_SHA,
               "indexed": base64.b64encode(indexed).decode(),
               "palette": base64.b64encode(palette).decode(), "layers": layers}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"prototype": True,
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
