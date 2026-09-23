#!/usr/bin/env python3
"""驗證目標075固定玩家路徑的來源→緩衝→字形→像素雙次收據。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path


BASELINE = {
    "memory_sha256": "09e9fbf961b8b50115fa0c8b707d4a220cf7f12b3e2a359311073f85786ad109",
    "canvas_sha256": "08edaac74a54263b8e093010d8cbc97d3f9820c3c151f28d80beded5c5a8a650",
    "indexed_sha256": "6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae",
    "palette_sha256": "762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82",
}
CANVAS = 0x2CAE0


def require(ok, message):
    if not ok:
        raise ValueError(message)


def byte_run(events, step, site, start, expected):
    rows = sorted((row for row in events if row["step"] == step and row["site"] == site), key=lambda row: row["linear"])
    require([row["linear"] for row in rows] == list(range(start, start + len(expected))), "位址不連續：" + site)
    require(bytes(row["value"] for row in rows) == expected, "位元組不符：" + site)


def difference(a, b):
    require(len(a) == len(b) == 64000, "原始畫布大小不符")
    return [(i % 320, i // 320) for i in range(64000) if a[i] != b[i]]


def bbox(points):
    return (min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points), max(y for _, y in points))


def verify(inputs, first, second):
    a = json.loads(first.read_text(encoding="utf-8"))
    b = json.loads(second.read_text(encoding="utf-8"))
    require(a == b, "兩次 dosgolem 事件與狀態不一致")
    require(a["version"] == "goal075-card-flow-v5" and a["end"] == 32000000 and not a["exited"], "探針版本或正常路徑狀態不符")
    require(a["input_sha256"] == hashlib.sha256(inputs.read_bytes()).hexdigest(), "玩家輸入 SHA-256 不符")
    require(a["difficulty_art_opened"] and not a["writes_truncated"], "難度圖未開啟或寫入 trace 截斷")
    for name, expected in BASELINE.items():
        require(a[name] == expected, "觀測改變原版最終狀態：" + name)

    reads, writes = a["reads"], a["writes"]
    byte_run(reads, 29797568, "0E2D:11CF", 0x4CC6A, b"Discoverer\x00")
    byte_run(reads, 29813172, "0E2D:11CF", 0x4DF90, b"Easiest\x00")
    byte_run(writes, 29797579, "0E2D:11EB", 0x2A74C, b"Discoverer")
    byte_run(writes, 29813183, "0E2D:11EB", 0x2A74C, b"Easiest\x00")
    byte_run(reads, 29798246, "0E2D:11A5", 0x2A74C, b"DISCOVERER:")
    byte_run(reads, 29813648, "0E2D:11A5", 0x2A74C, b"Easiest\x00")
    byte_run(writes, 29798246, "0E2D:11A5", 0x2A6B0, b"DISCOVERER:\x00")
    byte_run(writes, 29813648, "0E2D:11A5", 0x2A6B0, b"Easiest\x00")

    glyph = [row for row in reads if row["site"] == "0D21:00C6" and 0x2A6B0 <= row["linear"] <= 0x2A6BB]
    first_glyph = [row for row in glyph if row["step"] < 29813140]
    second_glyph = [row for row in glyph if row["step"] >= 29813140]
    require(bytes(row["value"] for row in first_glyph) == b"DISCOVERER:\x00" * 2, "稱號沒有完整走過字形迴圈兩次")
    require(bytes(row["value"] for row in second_glyph) == b"Easiest\x00" * 2, "副標沒有完整走過字形迴圈兩次")

    entries = [row for row in a["steps"] if row["site"] == "0D21:000C"]
    anchors = [(row["step"], row["regs"][0], row["regs"][2]) for row in entries]
    require(anchors == [(29798206, 142, 45), (29805679, 141, 45),
                        (29813608, 151, 53), (29816824, 150, 53)], "兩行雙次繪製錨點不符")

    card_writes = [row for row in writes if row["site"] == "0D21:012C" and CANVAS <= row["linear"] < CANVAS + 64000]
    first_writes = [row for row in card_writes if row["step"] < 29813172]
    second_writes = [row for row in card_writes if row["step"] > 29813172]
    xy = lambda row: ((row["linear"] - CANVAS) % 320, (row["linear"] - CANVAS) // 320)
    require(len(first_writes) == 192 and bbox([xy(row) for row in first_writes]) == (141, 45, 182, 49), "稱號逐像素寫入不符")
    require(len(second_writes) == 100 and bbox([xy(row) for row in second_writes]) == (150, 53, 174, 58), "副標逐像素寫入不符")

    snapshots = {name: base64.b64decode(data, validate=True) for name, data in a["snapshots"].items()}
    require(snapshots["after-first"] == snapshots["before-second"], "兩行之間的原始畫布不穩定")
    for name, canvas, rect in (
        ("稱號", snapshots["before-first"], (138, 44, 186, 51)),
        ("副標", snapshots["before-second"], (146, 52, 180, 60)),
    ):
        x0, y0, x1, y1 = rect
        colors = {canvas[y * 320 + x] for y in range(y0, y1) for x in range(x0, x1)}
        require(len(colors) > 50, name + "底圖不應誤判成單色")
    for name, left, right, count, bounds in (
        ("稱號", snapshots["before-first"], snapshots["after-first"], 164, (141, 45, 182, 49)),
        ("副標", snapshots["before-second"], snapshots["after-second"], 83, (150, 53, 174, 58)),
    ):
        changed = difference(left, right)
        require(len(changed) == count and bbox(changed) == bounds, name + "畫布差分不符")
        require(all(128 <= x < 196 and 40 <= y < 64 for x, y in changed), name + "差分超出卡片區")
    print("PASS：兩次同狀態；原文→共用緩衝→局部副本→逐字字形→兩行畫布像素皆可回查")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    args = parser.parse_args()
    verify(args.inputs, args.first, args.second)


if __name__ == "__main__":
    main()
