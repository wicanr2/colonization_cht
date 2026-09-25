#!/usr/bin/env python3
"""只在忽略版控的工作區產生標題缺譯、重複鍵及溢出測試語料。"""

import argparse
import csv
import hashlib
import os
from pathlib import Path


KEY = "GAME.TXT:0x000004CD"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not args.output.is_dir() or args.output.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    with args.source.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fields, rows = reader.fieldnames, list(reader)
    matching = [row for row in rows if row["candidate_id"] == KEY]
    if len(matching) != 1 or matching[0]["zh_hant"] != "遊戲選項設定":
        raise ValueError("正式標題鍵或譯文變更，需重新審查")
    for variant in ("blank", "duplicate", "overflow"):
        target = args.output / f"goal132-catalog-{variant}.tsv"
        if target.exists():
            raise FileExistsError(target)
        altered = [dict(row) for row in rows]
        if variant == "blank":
            next(row for row in altered if row["candidate_id"] == KEY)["zh_hant"] = ""
        elif variant == "duplicate":
            altered.append(dict(matching[0]))
        else:
            next(row for row in altered if row["candidate_id"] == KEY)["zh_hant"] = "遊戲選項設定" * 8
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(altered)
        print(variant, hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
