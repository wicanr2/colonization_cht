#!/usr/bin/env python3
"""由已驗真視窗難度頁前綴產生第三張卡片的受控滑鼠重播。"""

import argparse
import hashlib
import json
from pathlib import Path


BASELINE_SHA = "51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = args.baseline.read_bytes()
    if hashlib.sha256(original).hexdigest() != BASELINE_SHA:
        raise ValueError("真視窗難度頁前綴指紋不符")
    prefix = json.loads(original)["inputs"]
    if len(prefix) != 9 or prefix[-1] != {
        "step": 29800000, "kind": "move", "x": 16, "y": 16, "button": 0
    }:
        raise ValueError("難度頁前綴事件不符")
    args.out.mkdir(parents=True, exist_ok=True)
    # 第三張卡片在原版畫面的左下；座標由原版畫面確認，是否命中仍須探針驗證。
    hover = [
        {"step": 32000000, "kind": "move", "x": 55, "y": 145, "button": 0},
        {"step": 35000000, "kind": "move", "x": 16, "y": 16, "button": 0},
    ]
    click = [
        hover[0],
        {"step": 33000000, "kind": "press", "x": 0, "y": 0, "button": 0},
        {"step": 33800000, "kind": "release", "x": 0, "y": 0, "button": 0},
        hover[1],
    ]
    for name, extra in (("control", []), ("hover", hover), ("click", click)):
        payload = {"inputs": prefix + extra, "end": 40000000}
        (args.out / f"{name}.inputs.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print("目標120：固定無操作、僅移鼠及第三張卡片點擊三條重播")


if __name__ == "__main__":
    main()
