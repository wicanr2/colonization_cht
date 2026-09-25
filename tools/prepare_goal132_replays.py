#!/usr/bin/env python3
"""由已錄製真玩家輸入產生選項標題的有界取樣前綴；只在容器執行。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


SOURCE_SHA = "dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not args.output.is_dir() or args.output.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    raw = args.source.read_bytes()
    receipt = json.loads(raw)
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA or receipt["end"] != 1350000000 or len(receipt["inputs"]) != 33:
        raise ValueError("來源不是已錄製的固定真玩家輸入")
    if any(a["step"] > b["step"] for a, b in zip(receipt["inputs"], receipt["inputs"][1:])):
        raise ValueError("輸入時序不符")
    for end in (1253500000, 1253700000, 1280000000):
        selected = [event for event in receipt["inputs"] if event["step"] <= end]
        expected_count = 32 if end == 1280000000 else 29
        expected_last = 1270600000 if end == 1280000000 else 1250600000
        if len(selected) != expected_count or selected[-1]["step"] != expected_last:
            raise ValueError("標題取樣前混入其他玩家事件")
        target = args.output / f"window-prefix-{end}.inputs.json"
        payload = json.dumps({"inputs": selected, "end": end}, ensure_ascii=False,
                             sort_keys=True, indent=2) + "\n"
        if target.exists() and target.read_text(encoding="utf-8") != payload:
            raise ValueError(f"既有前綴內容不同：{target}")
        if not target.exists():
            target.write_text(payload, encoding="utf-8")
        print(end, hashlib.sha256(target.read_bytes()).hexdigest())
    # 唯一合成負例：在已錄玩家前綴後新增一筆游標移動，不冒稱真實玩家錄製。
    cursor = [event for event in receipt["inputs"] if event["step"] <= 1280000000]
    cursor.append({"step": 1275000000, "kind": "move", "x": 90, "y": 50, "button": 0})
    target = args.output / "window-prefix-1280000000-title-cursor.inputs.json"
    payload = json.dumps({"inputs": cursor, "end": 1280000000}, ensure_ascii=False,
                         sort_keys=True, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != payload:
        raise ValueError(f"既有游標負例不同：{target}")
    if not target.exists():
        target.write_text(payload, encoding="utf-8")
    print("cursor-negative", hashlib.sha256(target.read_bytes()).hexdigest())
    returned = cursor + [{"step": 1277000000, "kind": "move", "x": 16, "y": 16, "button": 0}]
    target = args.output / "window-prefix-1280000000-title-cursor-return.inputs.json"
    payload = json.dumps({"inputs": returned, "end": 1280000000}, ensure_ascii=False,
                         sort_keys=True, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != payload:
        raise ValueError(f"既有游標移開負例不同：{target}")
    if not target.exists():
        target.write_text(payload, encoding="utf-8")
    print("cursor-return", hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
