#!/usr/bin/env python3
"""獨立核對相鄰國家旗卡兩則原文字節至原版畫布；原始收據只留 workplace。"""

import argparse
import hashlib
import json
from pathlib import Path


INPUT_HASHES = {
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
}
CASES = (
    ("NAMES.TXT", 0x906, b"France", 0x2B108, 0x2B0FA, 0x4CBC6,
     15_500_000, 15_560_000, b"FRANCE:\0", (242, 15, 267, 19), 118),
    ("LABELS.TXT", 0x8FF, b"Cooperation", 0x2B101, 0x2B0E8, 0x4DFDD,
     18_070_000, 18_140_000, b"Cooperation\0", (235, 87, 275, 92), 150),
)


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(args):
    if not args.game.is_dir():
        print("SKIP：合法 DOS 原版不存在")
        return 77
    p = args.reports
    flow_paths = [p / f"full-flow-{x}.json" for x in "cd"]
    paint_paths = [p / f"observed-{x}.json" for x in "ef"]
    require(all(path.is_file() for path in flow_paths + paint_paths +
                [p / "control-v2.json", args.prior_buffers]), "原版收據不完整")
    require(flow_paths[0].read_bytes() == flow_paths[1].read_bytes(), "雙次 RAM 收據不一致")
    require(paint_paths[0].read_bytes() == paint_paths[1].read_bytes(), "雙次畫布收據不一致")
    flow, paint, control = load(flow_paths[0]), load(paint_paths[0]), load(p / "control-v2.json")
    buffers = load(args.prior_buffers)
    require(flow["flow"] and not flow["control"] and
            not paint["flow"] and not paint["control"] and control["control"], "觀測模式不符")
    require(not flow["ram_truncated"] and not flow["read_truncated"] and
            not paint["read_truncated"] and not paint["write_truncated"], "原版事件遭截斷")
    require(flow["state"] == paint["state"] == control["state"] and
            flow["opened"] == paint["opened"] == control["opened"] and
            flow["samples"] == paint["samples"] == control["samples"], "原版與無監看控制不同狀態")
    require(flow["input_sha256"] == paint["input_sha256"] == buffers["input_sha256"],
            "真玩家輸入來源不一致")
    events = flow["ram_events"]
    lookup = {}
    for index, item in enumerate(events):
        key = (item["kind"], item["site"], item["linear"], item["value"])
        lookup.setdefault(key, []).append((item["step"], index))

    def event(kind, site, address, value, low, high, after=-1):
        matches = [(step, index) for step, index in lookup.get((kind, site, address, value), [])
                   if low <= step < high and index > after]
        require(matches, f"缺原版 {site} {kind} RAM 0x{address:X} 值 {value}")
        return matches[0]

    summary = []
    for name, offset, original, raw, normalized, resident, lo, hi, printed, bbox, paint_count in CASES:
        source = (args.game / name).read_bytes()
        require(sha(source) == INPUT_HASHES[name] and
                source[offset:offset + len(original)] == original, "原始 TXT 版本或位元組不符：" + name)
        transfer = next((x for x in buffers["transfers"] if x["name"] == name and
                         x["file_offset"] <= offset and
                         offset + len(original) <= x["file_offset"] + x["got"]), None)
        require(transfer and transfer["got"] == 512 and transfer["candidate_match"],
                "DOS AH=3Fh 同區塊傳輸未證實：" + name)
        actual_raw = transfer["destination_seg"] * 16 + transfer["destination_off"] + offset - transfer["file_offset"]
        require(actual_raw == raw, "DOS 目的位址／檔案位移計算不符：" + name)
        for index, byte in enumerate(original):
            raw_write = event("write", "0080:0400", raw + index, byte, lo, hi)
            normalized_read = event("read", "0E2D:1F76", raw + index, byte, lo, hi, raw_write[1])
            normalized_write = event("write", "0E2D:1F86", normalized + index, byte,
                                     lo, hi, normalized_read[1])
            parse_read = event("read", "0E2D:09F4", normalized + index, byte,
                               lo, hi, normalized_write[1])
            parse_write = event("write", "0E2D:09F5", 0x249DC + index, byte,
                                lo, hi, parse_read[1])
            require(raw_write < normalized_read < normalized_write < parse_read < parse_write,
                    "DOS 緩衝至解析緩衝的順序不符：" + name)
            if name == "NAMES.TXT":
                copy_read = event("read", "9320:0171", 0x249DC + index, byte,
                                  lo, hi, parse_write[1])
                copy_write = event("write", "9320:0173", 0x26C58 + index, byte,
                                   lo, hi, copy_read[1])
                resident_read = event("read", "0E2D:11A5", 0x26C58 + index, byte,
                                      lo, hi, copy_write[1])
                resident_write = event("write", "0E2D:11A5", resident + index, byte,
                                       lo, hi, resident_read[1])
                require(parse_write < copy_read < copy_write < resident_read < resident_write,
                        "國名中間複製／常駐順序不符")
            else:
                site = "0E2D:11A1" if index == 0 else "0E2D:11A5"
                resident_read = event("read", site, 0x249DC + index, byte,
                                      lo, hi, parse_write[1])
                resident_write = event("write", site, resident + index, byte,
                                       lo, hi, resident_read[1])
                require(parse_write < resident_read < resident_write,
                        "副標解析至常駐順序不符")
        display_lo, display_hi = ((44_120_000, 44_130_000) if name == "NAMES.TXT"
                                  else (44_130_000, 44_143_000))
        for index, byte in enumerate(original):
            resident_output = event("read", "0E2D:11CF", resident + index, byte,
                                    display_lo, display_hi)
            require(resident_output[0] > hi, "輸出早於原始載入")
        for index, byte in enumerate(printed):
            formatted = event("write", "0E2D:11A5", 0x2A716 + index, byte,
                              display_lo, display_hi)
            print_reads = [x for x in paint["reads"] if x["site"] == "0D21:00C6" and
                           x["linear"] == 0x2A716 + index and x["value"] == byte and
                           display_lo <= x["step"] < display_hi]
            require(len(print_reads) == 2 and formatted[0] < print_reads[0]["step"],
                    "格式字串沒有逐字輸出兩次：" + name)
        target = [x for x in paint["writes"] if x["region"] == "other-text" and
                  (x["y"] < 50) == (name == "NAMES.TXT")]
        require(len(target) == paint_count and all(x["site"] == "0D21:012C" for x in target),
                "文字畫布寫入點／次數不符：" + name)
        actual_bbox = (min(x["x"] for x in target), min(x["y"] for x in target),
                       max(x["x"] for x in target), max(x["y"] for x in target))
        require(actual_bbox == bbox and {x["value"] for x in target} == {0, 9},
                "文字畫布範圍或色號不符：" + name)
        require(min(x["step"] for x in target) >
                min(x["step"] for x in paint["reads"] if x["site"] == "0D21:00C6" and
                    display_lo <= x["step"] < display_hi), "畫布寫入早於讀字：" + name)
        summary.append({"source": f"{name}:0x{offset:X}", "source_sha256": sha(source),
                        "fragment_sha256": sha(original), "dos_linear": f"0x{raw:X}",
                        "normalized_linear": f"0x{normalized:X}", "resident_linear": f"0x{resident:X}",
                        "print_linear": "0x2A716", "canvas_bbox_inclusive": bbox,
                        "canvas_write_count": paint_count, "canvas_colors": [0, 9]})
    cleared = {side: [x for x in paint["writes"] if x["region"] == side] for side in ("upper", "lower")}
    require(len(cleared["upper"]) == 188 and len(cleared["lower"]) == 221 and
            max(x["step"] for x in cleared["upper"] + cleared["lower"]) <
            min(x["step"] for x in paint["reads"]), "舊卡清除與新卡讀字順序不符")
    result = {"result": "PASS", "scope": "相鄰右上旗卡兩處來源與原版畫布；非正式中文覆蓋",
              "sources": summary, "load_report_sha256": sha(args.prior_buffers.read_bytes()),
              "flow_report_sha256": sha(flow_paths[0].read_bytes()),
              "paint_report_sha256": sha(paint_paths[0].read_bytes()),
              "control_state_equal": True, "dual_cold_boot_equal": True,
              "old_card_erased_before_new_text": True}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--prior-buffers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args()))
