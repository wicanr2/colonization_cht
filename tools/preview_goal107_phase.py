#!/usr/bin/env python3
"""將目標107原版索引檢查點輸出為本機檢視 PNG；不得提交原版畫素。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    if not args.output.is_dir() or args.output.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    report = json.loads(Path(f"{args.prefix}.json").read_bytes())
    if report["version"] != "goal107-post-caption-audit-v1":
        raise ValueError("收據版本不符")
    for label in args.labels:
        if label not in report["samples"]:
            raise ValueError(f"缺少檢查點：{label}")
        target = args.output / f"{label}.png"
        if target.exists():
            raise ValueError(f"拒絕覆寫既有 PNG：{target}")
        sample = report["samples"][label]
        indexed = Path(f"{args.prefix}.{label}.idx").read_bytes()
        palette = Path(f"{args.prefix}.{label}.pal").read_bytes()
        if (len(indexed) != 64000 or len(palette) != 768 or
                sha(indexed) != sample["indexed_sha256"] or
                sha(palette) != sample["palette_sha256"]):
            raise ValueError(f"原始索引畫面或色盤不符：{label}")
        frame = Image.frombytes("P", (320, 200), indexed)
        frame.putpalette(bytes((value << 2) | (value >> 4) for value in palette))
        frame.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST).save(target)
        print(f"本機檢視圖：{target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("labels", nargs="+", help="例如 1200m 1225m")
    main(parser.parse_args())
