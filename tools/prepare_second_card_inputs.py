#!/usr/bin/env python3
"""從已驗證的真視窗難度頁路徑製作第二張卡片的可丟棄滑鼠輸入變體。"""

import argparse
import hashlib
import json
from pathlib import Path


INPUT_SHA = "51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.baseline.read_bytes()
    if hashlib.sha256(source).hexdigest() != INPUT_SHA:
        raise ValueError("真視窗輸入指紋不符")
    baseline = json.loads(source)
    inputs = baseline["inputs"]
    if len(inputs) != 9 or inputs[-1] != {"step": 29800000, "kind": "move", "x": 16, "y": 16, "button": 0}:
        raise ValueError("難度頁基準事件不符")
    args.out.mkdir(parents=True, exist_ok=False)
    variants = {
        "control": [],
        "hover": [{"step": 32000000, "kind": "move", "x": 265, "y": 55, "button": 0},
                  {"step": 35000000, "kind": "move", "x": 16, "y": 16, "button": 0}],
        "click": [{"step": 32000000, "kind": "move", "x": 265, "y": 55, "button": 0},
                  {"step": 33000000, "kind": "press", "x": 0, "y": 0, "button": 0},
                  {"step": 33800000, "kind": "release", "x": 0, "y": 0, "button": 0},
                  {"step": 35000000, "kind": "move", "x": 16, "y": 16, "button": 0}],
    }
    for name, extra in variants.items():
        (args.out / f"{name}.inputs.json").write_text(
            json.dumps({"inputs": inputs + extra, "end": 40000000}, ensure_ascii=False, indent=2) + "\n")
    print("已產生固定三組受控輸入：原文控制、移入移出、點擊移出；全部只供研究")


if __name__ == "__main__":
    main()
