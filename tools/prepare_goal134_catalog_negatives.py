#!/usr/bin/env python3
"""只在忽略版控的工作區產生八列缺譯、重複鍵、錯快捷鍵與缺快捷鍵測試語料。"""

import argparse
import csv
import hashlib
import os
from pathlib import Path


# 變體 → (被竄改的列鍵, 竄改方式)
VARIANTS = {
    "blank": "GAME.TXT:0x000004E9",
    "duplicate": "GAME.TXT:0x000004FD",
    "wrong-hotkey": "GAME.TXT:0x00000512",
    "no-hotkey": "GAME.TXT:0x00000525",
}


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
    for variant, key in VARIANTS.items():
        matching = [row for row in rows if row["candidate_id"] == key]
        if len(matching) != 1 or not matching[0]["zh_hant"].startswith("(~"):
            raise ValueError("正式列鍵或譯文格式變更，需重新審查")
        target = args.output / f"goal134-catalog-{variant}.tsv"
        if target.exists():
            raise FileExistsError(target)
        altered = [dict(row) for row in rows]
        row = next(r for r in altered if r["candidate_id"] == key)
        if variant == "blank":
            row["zh_hant"] = ""
        elif variant == "duplicate":
            altered.append(dict(matching[0]))
        elif variant == "wrong-hotkey":
            row["zh_hant"] = "(~X)" + row["zh_hant"][4:]
        else:
            row["zh_hant"] = row["zh_hant"][5:] + "（~" + row["zh_hant"][2] + "）"
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(altered)
        print(variant, key, hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
