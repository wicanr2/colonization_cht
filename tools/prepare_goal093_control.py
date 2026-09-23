#!/usr/bin/env python3
"""將目標093固定原版索引與色盤交給 Ebitengine 繪製本機控制圖。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(args):
    if not args.output.parent.is_dir() or args.output.parent.stat().st_uid != os.getuid():
        raise ValueError("控制圖資料輸出目錄不存在或擁有者不符")
    report_raw = args.report.read_bytes()
    report = json.loads(report_raw)
    if report["version"] != "goal093-name-v1" or report["input_sha256"] != INPUT_SHA:
        raise ValueError("原版收據版本或正常玩家輸入不符")
    sample = report["samples"].get(args.sample)
    if sample is None:
        raise ValueError("原版收據沒有指定取樣")
    prefix = args.report.with_suffix("")
    indexed = Path(str(prefix) + f".{args.sample}.idx").read_bytes()
    palette = Path(str(prefix) + f".{args.sample}.pal").read_bytes()
    if (len(indexed) != 64000 or len(palette) != 768 or max(palette) > 63 or
            sha(indexed) != sample["indexed_sha256"] or
            sha(palette) != sample["palette_sha256"]):
        raise ValueError("原版索引或色盤與收據不符")
    payload = {
        "prototype": True, "layers": [],
        "source_receipt_sha256": sha(report_raw),
        "scenario": report["scenario"], "sample": args.sample,
        "step": sample["step"],
        "indexed": base64.b64encode(indexed).decode(),
        "palette": base64.b64encode(palette).decode(),
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("indexed", "palette")},
                     ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample", choices=("49m", "55m", "57m", "65m"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())
