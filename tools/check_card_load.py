#!/usr/bin/env python3
"""核對目標077：原始 TXT → DOS 緩衝 → 就地整理 → 中間緩衝 → 執行期卡片字串。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_card_flow import BASELINE, verify as verify_card_flow

SOURCE_HASHES = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def byte_run(events, site, start, expected, first, last, field="linear"):
    rows = [row for row in events if row["site"] == site and first <= row["step"] <= last
            and start <= row[field] < start + len(expected)]
    rows.sort(key=lambda row: row[field])
    require([row[field] for row in rows] == list(range(start, start + len(expected))),
            "位址或長度不符：" + site)
    require(bytes(row["value"] for row in rows) == expected, "原文字節不符：" + site)
    return rows


def check_line(report, name, offset, source_address, compact_address, intermediate,
               target, text, file_step, compact_first, compact_last, parse_first,
               parse_last, target_step):
    reads = [row for row in report["file_reads"] if row["name"] == name
             and row["step"] == file_step and row.get("candidate_offset") == offset]
    require(len(reads) == 1, "沒有唯一的原版 DOS 候選讀取：" + name)
    file_read = reads[0]
    require(file_read["file_offset"] <= offset
            and offset + len(text) <= file_read["file_offset"] + file_read["got"]
            and file_read["candidate_linear"] == source_address
            and file_read["candidate_ram_match"]
            and file_read["candidate_ram_sha256"] == hashlib.sha256(text).hexdigest(),
            "檔案偏移、目的位址或讀後 RAM 位元組不符：" + name)
    require(file_step < compact_first <= compact_last < parse_first <= parse_last < target_step,
            "讀取／轉存時間序不符：" + name)
    byte_run(report["source_reads"], "0E2D:1F76", source_address, text,
             file_step, compact_last)
    byte_run(report["target_writes"], "0E2D:1F86", compact_address, text,
             compact_first, compact_last)
    byte_run(report["source_reads"], "0E2D:09F4", compact_address, text,
             parse_first, parse_last)
    byte_run(report["target_writes"], "0E2D:09F5", intermediate, text,
             parse_first, parse_last)
    target_rows = byte_run(report["target_writes"], "0E2D:11A5", target, text,
                           target_step, target_step)
    first_target = target_rows[0]
    regs, segments = first_target["regs"], first_target["segments"]
    require(segments[3] * 16 + regs[6] == intermediate
            and segments[0] * 16 + regs[7] == target,
            "最終搬運的 DS:SI／ES:DI 不指向已驗證的來源／目的：" + name)
    require(bytes.fromhex(report["target_title_hex" if name == "NAMES.TXT" else
                                 "target_subtitle_hex"]) == text,
            "最終 RAM 文字與原版候選不符：" + name)
    return {"file": name, "file_offset": offset, "dos_step": file_step,
            "dos_buffer": source_address, "compact_buffer": compact_address,
            "intermediate_buffer": intermediate, "runtime_target": target,
            "runtime_write_step": target_step}


def verify(inputs, first, second, flow_first, flow_second):
    raw_a, raw_b = first.read_bytes(), second.read_bytes()
    require(raw_a == raw_b, "兩次 dosgolem 載入收據不一致")
    report = json.loads(raw_a)
    require(report["version"] == "goal077-card-load-v4" and report["end"] == 32000000
            and not report["exited"] and not report["reads_truncated"]
            and not report["writes_truncated"], "探針版本、路徑或觀測截斷")
    require(report["input_sha256"] == hashlib.sha256(inputs.read_bytes()).hexdigest(),
            "玩家輸入與來源收據不一致")
    require(report["dos_address_space"] == "real-mode CS:IP and 20-bit linear RAM"
            and report["file_address_space"] == "DOS AH=3Fh file offset, DS:DX destination",
            "位址空間宣告不符")
    require(report["input_hashes"] == SOURCE_HASHES, "原版檔案指紋集合不符")
    for key, expected in BASELINE.items():
        require(report[key] == expected, "來源觀測改變原版狀態：" + key)
    candidates = {(row["name"], row["file_offset"]): row for row in report["candidates"]}
    for name, offset, text, target in (
        ("NAMES.TXT", 0xC0C, b"Discoverer", 0x4CC6A),
        ("GAME.TXT", 0xA26, b"Discoverer", 0x4CC6A),
        ("LABELS.TXT", 0x8A9, b"Easiest", 0x4DF90),
    ):
        candidate = candidates[(name, offset)]
        require(candidate["bytes_sha256"] == hashlib.sha256(text).hexdigest()
                and candidate["length"] == len(text)
                and candidate["runtime_target"] == target
                and candidate["source_sha256"] == report["input_hashes"][name],
                "候選原始檔指紋不符：" + name)
    title = check_line(report, "NAMES.TXT", 0xC0C, 176142, 176141, 149980,
                       0x4CC6A, b"Discoverer", 16208974, 16209091, 16209163,
                       16214310, 16214347, 16215523)
    subtitle = check_line(report, "LABELS.TXT", 0x8A9, 176299, 176283, 149980,
                          0x4DF90, b"Easiest", 18648994, 18650367, 18650415,
                          18681523, 18681548, 18682724)
    game_reads = [row for row in report["file_reads"] if row["name"] == "GAME.TXT"]
    require(game_reads and all(row["step"] > title["runtime_write_step"] for row in game_reads),
            "GAME.TXT 在稱號寫入前已被讀取；不能排除它")
    verify_card_flow(inputs, flow_first, flow_second)
    result = {"version": report["version"], "receipt_sha256": hashlib.sha256(raw_a).hexdigest(),
              "title": title, "subtitle": subtitle,
              "game_first_read_step": min(row["step"] for row in game_reads),
              "conclusion": "固定正常玩家路徑：NAMES.TXT 與 LABELS.TXT 來源載入邊已閉合；規格仍為 DRAFT"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--flow-first", type=Path, required=True)
    parser.add_argument("--flow-second", type=Path, required=True)
    args = parser.parse_args()
    verify(args.inputs, args.first, args.second, args.flow_first, args.flow_second)
