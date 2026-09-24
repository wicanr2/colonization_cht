#!/usr/bin/env python3
"""從已驗旗卡 A 輸入產生逐欄回退與滑鼠負例（僅本機 workplace）。"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path


BASE_INPUT_SHA = "0abcac16288c86e1a09b63452bd8069ea8b5e13b860883545a4b5bf05e86c464"
UPPER = "NAMES.TXT:0x000008EA"
LOWER = "LABELS.TXT:0x000008F2"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--fonts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.is_dir() and args.out.stat().st_uid == os.getuid(),
            "輸出目錄不存在或擁有者不符")
    require(hashlib.sha256(args.inputs.read_bytes()).hexdigest() == BASE_INPUT_SHA,
            "已驗第一張旗卡輸入不同")
    original = json.loads(args.inputs.read_text())
    require(original["end"] == 43_000_000 and len(original["inputs"]) == 15,
            "輸入終點或事件數不符")
    with args.catalog.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields, rows = reader.fieldnames, list(reader)
    require(len(rows) == 4 and len([row for row in rows if row["candidate_id"] == UPPER]) == 1
            and len([row for row in rows if row["candidate_id"] == LOWER]) == 1,
            "旗卡片段 TSV 不符")

    def write_catalog(name, selected):
        path = args.out / f"{name}.tsv"
        require(not path.exists(), "負例 TSV 已存在：" + name)
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            writer.writerows(selected)

    write_catalog("missing-upper", [row for row in rows if row["candidate_id"] != UPPER])
    write_catalog("duplicate-lower", rows + [next(row for row in rows if row["candidate_id"] == LOWER)])
    font_dir = args.out / "wrong-size-lower"
    require(not font_dir.exists(), "負例字模目錄已存在")
    font_dir.mkdir()
    for key in (UPPER, LOWER):
        filename = key.replace(":", "-") + ".json"
        mask = json.loads((args.fonts / filename).read_text())
        require(mask["candidate_id"] == key, "字模鍵不符")
        if key == LOWER:
            require(mask["font_size"] == 25, "原下欄字級不符")
            mask["font_size"] = 29
        (font_dir / filename).write_text(json.dumps(mask, ensure_ascii=False) + "\n")

    def write_inputs(name, end, additional):
        path = args.out / f"{name}.inputs.json"
        require(not path.exists(), "負例輸入已存在：" + name)
        events = original["inputs"] + additional
        require(all(43_000_000 < e["step"] <= end for e in additional), "負例步數不符")
        path.write_text(json.dumps({"inputs": events, "end": end},
                                   ensure_ascii=False, indent=2) + "\n")

    def mouse(step, kind, x=0, y=0):
        return {"step": step, "kind": kind, "x": x, "y": y, "button": 0}

    write_inputs("hover-upper", 43_500_000, [mouse(43_200_000, "move", 156, 18)])
    write_inputs("hover-lower", 43_500_000, [mouse(43_200_000, "move", 156, 90)])
    write_inputs("hover-clear", 44_000_000,
                 [mouse(43_200_000, "move", 156, 18), mouse(43_600_000, "move", 16, 16)])
    write_inputs("press-lower", 44_000_000,
                 [mouse(43_200_000, "move", 156, 90), mouse(43_400_000, "press")])
    write_inputs("switch-right", 46_000_000,
                 [mouse(43_200_000, "move", 255, 50), mouse(43_400_000, "press"),
                  mouse(43_600_000, "release"), mouse(43_800_000, "move", 16, 16)])
    write_inputs("leave-page", 49_000_000,
                 [mouse(43_200_000, "move", 65, 184), mouse(43_400_000, "press"),
                  mouse(43_600_000, "release"), mouse(43_800_000, "move", 16, 16)])
    print("第一張旗卡逐欄回退與滑鼠負例已產生")


if __name__ == "__main__":
    main()
