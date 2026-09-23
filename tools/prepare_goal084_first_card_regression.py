#!/usr/bin/env python3
"""把已驗第一張卡片真視窗輸入限縮至既有40M步回歸檢查點。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


SOURCE_SHA = "0b36f4d6ec016455364f535a648535f4f9159c023a72164dca2078b57bfec62b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.parent.is_dir() or args.output.parent.stat().st_uid != os.getuid():
        raise ValueError("本機輸出目錄不存在或擁有者不符")
    if args.output.exists():
        raise FileExistsError(args.output)
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("第一張卡片真視窗輸入版本不符")
    replay = json.loads(raw)
    if replay["end"] != 100_000_000 or len(replay["inputs"]) != 9 or any(
            item["step"] > 40_000_000 for item in replay["inputs"]):
        raise ValueError("玩家輸入超出舊回歸檢查點")
    replay["end"] = 40_000_000
    args.output.write_text(json.dumps(replay, ensure_ascii=False, indent=2) + "\n")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
