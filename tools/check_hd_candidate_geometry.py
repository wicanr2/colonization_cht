#!/usr/bin/env python3
"""首座HD建築候選的透明輪廓檢查；只量測，不修改或輸出圖像。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from PIL import Image, __version__ as pillow_version

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4"
INDEXED_SHA = "d74c97554fc556cdb21899b7f720f2af79d2047cd3e11d57a38c99aa696246e2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["original", "decoded", "candidate", "metadata", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file(), "請在Docker內執行")
    if not args.original.is_file() or not args.decoded.is_file():
        print("SKIP：缺合法原版或來源圖，未製作替代圖")
        return 77
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists(), "需新的workplace輸出檔")
    need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出父目錄擁有者不符")
    need(sha(args.original.read_bytes()) == SOURCE_SHA, "BUILDING.SS指紋不符")
    metadata = json.loads(args.metadata.read_text())
    need(metadata["output"]["sha256"] == sha(args.candidate.read_bytes()), "候選與生成紀錄指紋不符")
    with Image.open(args.decoded) as source:
        need(source.mode == "P" and source.size == (23, 27), "原版解碼形狀不符")
        indexed = source.tobytes()
        need(sha(indexed) == INDEXED_SHA, "原版第032幀索引指紋不符")
        native = source.convert("RGBA").getchannel("A")
        need(list(native.getdata()) == [0 if v == 253 else 255 for v in indexed], "原版透明索引不符")
        native = native.resize((92, 108), Image.Resampling.NEAREST)
    with Image.open(args.candidate) as candidate:
        need(candidate.mode == "RGBA" and list(candidate.size) == metadata["output"]["size"], "候選形狀或透明通道不符")
        alpha_bbox = candidate.getchannel("A").getbbox()
        # 目的畫布的alpha抽樣只作量測，不修改／輸出候選圖片。
        alpha = candidate.getchannel("A").resize((92, 108), Image.Resampling.NEAREST)
        candidate_size = candidate.size
    pairs = list(zip(native.getdata(), alpha.getdata()))
    native_count = sum(a != 0 for a, b in pairs)
    art_count = sum(b >= 128 for a, b in pairs)
    overlap = sum(a != 0 and b >= 128 for a, b in pairs)
    holes = sum(a != 0 and b < 128 for a, b in pairs)
    outside = sum(a == 0 and b >= 128 for a, b in pairs)
    result = {"result": "MEASURED_CANDIDATE_GEOMETRY_NOT_PRODUCTION_APPROVAL",
              "source": {"file": "BUILDING.SS", "ordinal": 32, "native_size": [23, 27], "destination_size": [92, 108],
                         "original_sha256": SOURCE_SHA, "indexed_sha256": INDEXED_SHA},
              "candidate": {"size": candidate_size, "alpha_bbox": alpha_bbox, "sha256": sha(args.candidate.read_bytes()),
                            "metadata_sha256": sha(args.metadata.read_bytes())},
              "measurement": {"alpha_cutoff": 128, "native_opaque_pixels": native_count, "candidate_opaque_pixels": art_count,
                              "overlap_pixels": overlap, "uncovered_native_pixels": holes, "outside_native_pixels": outside,
                              "native_coverage": overlap / native_count, "alpha_iou": overlap / (native_count + art_count - overlap)},
              "tools": {"python": sys.version.split()[0], "pillow": pillow_version, "script_sha256": sha(Path(__file__).read_bytes())},
              "limitations": ["Alpha coverage is a geometry measurement, not a quality score or confidence threshold.",
                              "No image pixels are modified; no gameplay, animation or production HD completion credit."]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["result"], result["measurement"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
