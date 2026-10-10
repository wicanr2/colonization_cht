#!/usr/bin/env python3
"""以完整不透明像素在真實原版索引畫面定位 SS 候選，輸出僅限 workplace。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SELECTED_SOURCES = {"BUILDING.SS", "ICONS.SS", "PHYS0.SS", "TERRAIN.SS"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def locate(pixels, width, height, transparent, frame):
    opaque = [(i % width, i // width, v) for i, v in enumerate(pixels) if v != transparent]
    if len(opaque) < 8 or len({v for _, _, v in opaque}) < 3:
        return [], "insufficient-distinct-source-pixels"
    # 選完整不透明的連續片段縮小候選；最終仍核對全部不透明像素。
    runs = []
    for y in range(height):
        x = 0
        while x < width:
            if pixels[y * width + x] == transparent:
                x += 1
                continue
            start = x
            while x < width and pixels[y * width + x] != transparent:
                x += 1
            runs.append((x - start, start, y))
    length, anchor_x, anchor_y = max(runs)
    anchor = pixels[anchor_y * width + anchor_x:anchor_y * width + anchor_x + length]
    matches, offset = [], 0
    while True:
        found = frame.find(anchor, offset)
        if found < 0:
            break
        offset = found + 1
        x, y = found % 320 - anchor_x, found // 320 - anchor_y
        if x < 0 or y < 0 or x + width > 320 or y + height > 200:
            continue
        if all(frame[(y + v) * 320 + x + u] == color for u, v, color in opaque):
            matches.append([x, y, x + width, y + height])
    return matches, "full-opaque-index-match" if matches else "not-fully-visible-or-not-present"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "workplace").resolve()) or output.exists() or not output.parent.is_dir():
        raise SystemExit("輸出須為workplace內尚不存在的檔案，且父目錄已存在")
    if output.parent.stat().st_uid != os.getuid():
        raise SystemExit("輸出父目錄擁有者不符")
    raw = args.frame.read_bytes()
    if len(raw) != 320 * 200:
        raise SystemExit("原版索引畫面須為320×200")
    inventory_bytes = args.inventory.read_bytes()
    inventory = json.loads(inventory_bytes)
    if inventory["failed_files"]:
        raise SystemExit("盤點含失敗檔案，拒絕沿用")
    records = []
    for source in inventory["files"]:
        for asset in source["frames"]:
            image_path = args.inventory.parent / f"{source['file']}.{asset['ordinal']:03}.png"
            if asset.get("empty") or source["file"] not in SELECTED_SOURCES:
                continue
            if not image_path.is_file():
                raise SystemExit(f"缺少盤點圖像：{image_path.name}")
            with Image.open(image_path) as image:
                pixels = image.tobytes()
                if image.mode != "P" or list(image.size) != asset["size"] or digest(pixels) != asset["decoded_indexed_sha256"]:
                    raise SystemExit(f"圖像與清冊失配：{image_path.name}")
            matches, reason = locate(pixels, *asset["size"], asset["transparency_index"], raw)
            records.append({"source": source["file"], "source_sha256": source["sha256"],
                            "ordinal": asset["ordinal"], "size": asset["size"],
                            "decoded_indexed_sha256": asset["decoded_indexed_sha256"],
                            "matches": matches, "reason": reason})
    result = {"kind": "research-full-visible-opaque-match-not-drawing-call-contract",
              "locator_script_sha256": digest(Path(__file__).read_bytes()),
              "frame_sha256": digest(raw), "inventory_sha256": digest(inventory_bytes),
              "frame": str(args.frame), "candidates": len(records),
              "matched_assets": sum(bool(row["matches"]) for row in records),
              "placements": sum(len(row["matches"]) for row in records), "assets": records,
              "limitations": "Exact visible pixels only. Does not establish source loader identity, draw order, clipping, palette remapping or animation. No partial-match thresholds."}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["candidates", "matched_assets", "placements"]}))


if __name__ == "__main__":
    main()
