#!/usr/bin/env python3
"""將固定原版索引與色盤收據交給 Ebitengine 繪製本機控制圖。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare(args):
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "輸出目錄不存在或擁有者不符")
    report_raw = args.report.read_bytes()
    report = json.loads(report_raw)
    require(report["version"] == "goal092-neighbor-runtime-v1" and
            report["input_sha256"] ==
            "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" and
            args.sample in report["samples"], "目標092原版收據或取樣名稱不符")
    prefix = args.report.with_suffix("")
    indexed = Path(str(prefix) + f".{args.sample}.idx").read_bytes()
    palette = Path(str(prefix) + f".{args.sample}.pal").read_bytes()
    sample = report["samples"][args.sample]
    require(len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63
            and sha(indexed) == sample["indexed_sha256"]
            and sha(palette) == sample["palette_sha256"],
            "原版索引／色盤與收據不符")
    payload = {"prototype": True, "layers": [],
               "source_receipt_sha256": sha(report_raw), "scenario": report["scenario"],
               "sample": args.sample, "step": sample["step"],
               "indexed": base64.b64encode(indexed).decode(),
               "palette": base64.b64encode(palette).decode()}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("indexed", "palette")},
                     ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
