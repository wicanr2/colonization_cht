#!/usr/bin/env python3
"""從目標082真視窗輸入衍生難度完成區的可重播反例。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


SOURCE_SHA = "34d8ec6046830793b2e336ed41a638b533bb0782f5634263d0a1c338adda0f4b"
CLICK_SHA = "bb86566b14d73136e27a096b35ba6b1e2e84ef011122ac817dd989dd7727e550"
END = 60_000_000
BASE = 40_000_000
FINISH = (55, 83)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    variants_group = parser.add_mutually_exclusive_group()
    variants_group.add_argument("--hover", action="store_true", help="從已驗點擊收據產生國家標題游標進出反例")
    variants_group.add_argument("--f1", action="store_true", help="從已驗點擊收據產生原版 F1 說明鍵反例")
    args = parser.parse_args()
    expected = CLICK_SHA if args.hover or args.f1 else SOURCE_SHA
    if hashlib.sha256(args.source.read_bytes()).hexdigest() != expected:
        raise ValueError("輸入來源版本不符")
    if not args.output_dir.is_dir() or args.output_dir.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    original = json.loads(args.source.read_text())
    inputs = original["inputs"]
    if args.hover or args.f1:
        if len(inputs) != 16 or inputs[-1] != {
            "step": 43_000_000, "kind": "move", "x": 16, "y": 16, "button": 0
        }:
            raise ValueError("難度完成點擊尾端不符")
        if args.hover:
            end = 68_000_000
            variants = {
                "hover-select": [
                    {"step": 60_000_000, "kind": "move", "x": 55, "y": 40, "button": 0},
                    {"step": 64_000_000, "kind": "move", "x": 16, "y": 16, "button": 0},
                ],
                "hover-power": [
                    {"step": 60_000_000, "kind": "move", "x": 55, "y": 53, "button": 0},
                    {"step": 64_000_000, "kind": "move", "x": 16, "y": 16, "button": 0},
                ],
            }
        else:
            end = 80_000_000
            variants = {"f1-control": [],
                        "f1-nation": [{"step": 60_000_000, "kind": "f1", "x": 0, "y": 0,
                                       "button": 0}]}
    else:
        if len(inputs) != 12 or inputs[-1] != {
            "step": 35_200_000, "kind": "move", "x": 16, "y": 16, "button": 0
        }:
            raise ValueError("既有輸入尾端與已驗收狀態不同")
        end = END
        variants = {
            "control": [],
            "move-only": [{"step": BASE, "kind": "move", "x": FINISH[0], "y": FINISH[1], "button": 0}],
            "click": [
                {"step": BASE, "kind": "move", "x": FINISH[0], "y": FINISH[1], "button": 0},
                {"step": 41_000_000, "kind": "press", "x": 0, "y": 0, "button": 0},
                {"step": 42_000_000, "kind": "release", "x": 0, "y": 0, "button": 0},
                {"step": 43_000_000, "kind": "move", "x": 16, "y": 16, "button": 0},
            ],
        }
    for name, additions in variants.items():
        path = args.output_dir / f"{name}.inputs.json"
        if path.exists():
            raise FileExistsError(path)
        path.write_text(json.dumps({"inputs": inputs + additions, "end": end}, indent=2) + "\n")
        print(f"{name} {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
