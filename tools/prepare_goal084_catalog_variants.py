#!/usr/bin/env python3
"""由真實譯稿逐欄產生缺鍵／重複鍵測試副本；只寫 workplace。"""

import argparse
import hashlib
import os
from pathlib import Path


CATALOG_SHA = "14b2cc51df1d42ccd938d8fab334c0b90b1cf63314746df19d80449c3865f3f1"
FIELDS = {
    "select": b"LABELS.TXT:0x000008D3\t",
    "power": b"LABELS.TXT:0x000008DB\t",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(args):
    if not args.output_dir.is_dir() or args.output_dir.stat().st_uid != os.getuid():
        raise ValueError("本機輸出目錄不存在或擁有者不符")
    source = args.catalog.read_bytes()
    if sha(source) != CATALOG_SHA:
        raise ValueError("真實 TSV 版本不符")
    lines = source.splitlines(keepends=True)
    if not lines[0].startswith(b"candidate_id\tsource_file\t"):
        raise ValueError("TSV 欄位結構不符")
    for label, prefix in FIELDS.items():
        indices = [i for i, line in enumerate(lines) if line.startswith(prefix)]
        if len(indices) != 1:
            raise ValueError("來源鍵不唯一：" + label)
        at = indices[0]
        for action, variant in (
            ("missing", lines[:at] + lines[at + 1:]),
            ("duplicate", lines[:at + 1] + [lines[at]] + lines[at + 1:]),
        ):
            path = args.output_dir / f"goal084-catalog-{action}-{label}.tsv"
            if path.exists():
                raise FileExistsError(path)
            path.write_bytes(b"".join(variant))
            print(f"{action}-{label} {sha(path.read_bytes())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    prepare(parser.parse_args())
