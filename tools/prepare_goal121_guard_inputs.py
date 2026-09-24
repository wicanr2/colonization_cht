#!/usr/bin/env python3
"""從目標120已驗輸入產生第三張難度卡的分欄滑鼠重播；只寫 workplace。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal120_third import INPUTS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = (args.reports / "click.inputs.json").read_bytes()
    if sha(source) != INPUTS["click"]:
        raise ValueError("目標120正常玩家輸入指紋不符")
    baseline = json.loads(source)
    if baseline["end"] != 40000000 or len(baseline["inputs"]) != 13 or [
        (event["step"], event["kind"], event["x"], event["y"])
        for event in baseline["inputs"][9:]
    ] != [(32000000, "move", 55, 145), (33000000, "press", 0, 0),
          (33800000, "release", 0, 0), (35000000, "move", 16, 16)]:
        raise ValueError("目標120滑鼠按放／移開事件不符")
    if not args.out.is_dir() or args.out.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    for name, y in (("title-cursor", 135), ("title-only", 132), ("subtitle-cursor", 151)):
        result = json.loads(source)
        result["inputs"][9]["y"] = y
        path = args.out / f"{name}.inputs.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(name, "滑鼠", (55, y), "輸入 SHA-256", sha(path.read_bytes()))


if __name__ == "__main__":
    main()
