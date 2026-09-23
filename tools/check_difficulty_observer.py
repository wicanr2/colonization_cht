#!/usr/bin/env python3
"""驗證目標074兩次 dosgolem 探針收據與單一監看器契約。"""

import argparse
import hashlib
import json
import re
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_word(rows, step, address, start):
    selected = [row for row in rows if row["step"] == step and row["address"] == address]
    selected.sort(key=lambda row: row["linear"])
    require(selected and selected[0]["linear"] == start, "卡片原文讀取起點不符")
    require([row["linear"] for row in selected] == list(range(start, start + len(selected))), "卡片原文讀取不連續")
    return bytes(row["value"] for row in selected).rstrip(b"\x00")


def comparable(receipt):
    copy = dict(receipt)
    copy["checkpoints"] = {
        key: {field: value for field, value in checkpoint.items() if not field.endswith("_file")}
        for key, checkpoint in receipt["checkpoints"].items()
    }
    return copy


def verify(source, inputs, first, second):
    program = source.read_text(encoding="utf-8")
    for method in ("WatchWrites", "WatchReads"):
        count = len(re.findall(r"\bm\." + method + r"\(", program))
        require(count == 1, method + " 不是單一註冊")
    a = json.loads(first.read_text(encoding="utf-8"))
    b = json.loads(second.read_text(encoding="utf-8"))
    require(comparable(a) == comparable(b), "兩次正常玩家重播收據不一致")
    require(a["observer_version"] == "goal074-unified-watch-v1", "監看版本不符")
    require(a["input_sha256"] == hashlib.sha256(inputs.read_bytes()).hexdigest(), "玩家輸入雜湊不符")
    require(a["end"] == 32000000 and not a["exited"] and a["difficulty_art_opened"], "正常路徑結束狀態不符")
    require(a["write_sites"] and a["read_sites"], "標題／提示觀測被覆蓋")
    require(a["card_write_sites"] and a["card_read_sites"], "卡片觀測被覆蓋")
    require(source_word(a["card_reads"], 29797568, "0E2D:11CF", 0x4CC6A) == b"Discoverer", "卡片稱號原文不符")
    require(source_word(a["card_reads"], 29813172, "0E2D:11CF", 0x4DF90) == b"Easiest", "卡片副標原文不符")
    writes = a["card_text_writes"]
    require(len(writes) == a["card_write_sites"]["0D21:012C"]["count"], "卡片文字畫布寫入樣本不完整")
    require(all(row["address"] == "0D21:012C" and 141 <= row["x"] <= 182 and 45 <= row["y"] <= 58 for row in writes), "卡片文字畫布寫入位置不符")
    require(any(29797568 < row["step"] < 29813172 for row in writes), "稱號後沒有卡片文字寫入")
    require(any(row["step"] > 29813172 for row in writes), "副標後沒有卡片文字寫入")
    print("PASS：雙次收據一致；卡片原文兩段與畫布文字寫入均命中；標題／提示觀測仍在")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    args = parser.parse_args()
    verify(args.source, args.inputs, args.first, args.second)


if __name__ == "__main__":
    main()
