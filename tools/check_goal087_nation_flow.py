#!/usr/bin/env python3
"""獨立核對第 087 輪私有原始收據；不輸出原版素材。"""

import argparse
import hashlib
import json
from pathlib import Path


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
SOURCES = (
    ("NAMES.TXT", 0x8EA, b"England", 0x2B0EC, 15504395),
    ("LABELS.TXT", 0x8F2, b"Immigration", 0x2B0F4, 18077763),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def byte_run(events, kind, site, base, data, low, high):
    """核對同一個原版指令在指定時間窗逐字讀／寫的位元組。"""
    times = []
    for index, value in enumerate(data):
        matches = [event["step"] for event in events
                   if event["kind"] == kind and event["site"] == site
                   and event["linear"] == base + index
                   and event["value"] == value and low <= event["step"] < high]
        require(matches, f"缺少 {kind} {site} {base + index:05X} {value:02X}")
        times.append(min(matches))
    require(times == sorted(times), f"逐字事件次序錯誤：{site} {base:05X}")
    return times[0], times[-1]


def before(first, second, label):
    require(first[1] < second[0], f"資料流順序錯誤：{label}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    args = parser.parse_args()
    if not args.game.is_dir():
        print("SKIP：合法 DOS 原版目錄不存在")
        return
    for name, offset, value, _, _ in SOURCES:
        raw = (args.game / name).read_bytes()
        require(raw[offset:offset + len(value)] == value,
                f"原版位元組不符：{name}:{offset:X}")

    report_paths = [args.reports / f"{stem}.json" for stem in
                    ("buffers-a", "buffers-b", "flow5-a", "flow5-b", "flow5-control")]
    for path in report_paths:
        require(path.is_file(), f"缺少收據：{path.name}")
    buffer_a, buffer_b, flow_a, flow_b, control = map(load, report_paths)
    require(digest(report_paths[0].read_bytes()) == digest(report_paths[1].read_bytes()),
            "兩次 DOS 載入收據不一致")
    require(digest(report_paths[2].read_bytes()) == digest(report_paths[3].read_bytes()),
            "兩次 RAM 讀寫收據不一致")
    require(buffer_a["version"] == "goal087-buffer-inventory-v1", "DOS 清冊版本不符")
    require(flow_a["version"] == "goal087-nation-flow-v5-compact-source", "RAM 探針版本不符")
    require(control["version"] == flow_a["version"] and control["control"], "無觀測控制組不符")
    require(not flow_a["control"] and not flow_a["events_truncated"] and flow_a["events"],
            "事件空白或已截斷")
    require(not control["events"] and not control["events_truncated"], "控制組應無事件")
    require(all(not shot["hits_truncated"] for shot in buffer_a["snapshots"]), "RAM 快照已截斷")
    for report in (buffer_a, flow_a, control):
        require(report["input_sha256"] == INPUT_SHA, "真視窗輸入指紋不符")
        require(report["input_hashes"] == buffer_a["input_hashes"], "原版指紋清冊不一致")
        require(report["state"] == control["state"], "同輸入 CPU／RAM／畫面／色盤／時間不一致")
        require(report["opened"] == control["opened"], "開檔序列不一致")
    require(control["state"]["steps"] == 43000000, "終點不是第一張旗卡")
    for name, _, _, _, _ in SOURCES:
        require(digest((args.game / name).read_bytes()) == buffer_a["input_hashes"][name],
                f"原版檔案雜湊不符：{name}")

    transfers = buffer_a["transfers"]
    require(len(transfers) == 3, "候選 DOS 讀取數量意外變動")
    for name, offset, value, destination, step in SOURCES:
        matches = [item for item in transfers if item["name"] == name
                   and item["candidate_offset"] == offset and item["step"] == step]
        require(len(matches) == 1, f"DOS 載入邊不唯一：{name}")
        item = matches[0]
        require(item["handle"] == 6 and item["file_offset"] == 0x800
                and item["got"] == 512 and item["candidate_linear"] == destination
                and item["candidate_match"] and item["candidate_sha256"] == digest(value),
                f"DOS 載入內容／位址不符：{name}")
        require(item["destination_seg"] * 16 + item["destination_off"]
                + offset - item["file_offset"] == destination, f"DOS 位址換算不符：{name}")

    events = flow_a["events"]
    # 原始檔字元 → 共用讀入緩衝 → 就地去 CR 整理 → 解析字串。
    for name, _, value, original, read_step in SOURCES:
        if name == "NAMES.TXT":
            compact, parse, compact_at, compact_window, parse_window = (
                0x2B0DF, 0x249DC, (15506000, 15507000),
                (15540500, 15540700), (15540500, 15540700))
        else:
            compact, parse, compact_at, compact_window, parse_window = (
                0x2B0DC, 0x249DC, (18079000, 18081000),
                (18124380, 18124500), (18124380, 18124500))
        raw_read = byte_run(events, "read", "0E2D:1F76", original, value, *compact_at)
        compact_write = byte_run(events, "write", "0E2D:1F86", compact, value, *compact_at)
        parsed_read = byte_run(events, "read", "0E2D:09F4", compact, value, *compact_window)
        parsed_write = byte_run(events, "write", "0E2D:09F5", parse, value, *parse_window)
        require(read_step < raw_read[0], f"DOS 載入晚於來源讀取：{name}")
        # 原版逐字讀後寫會交錯，檢查整段窗口先後與每字都被觀測。
        before(compact_write, parsed_read, f"整理→解析 {name}")
        before(parsed_write, (15541700, 15541700) if name == "NAMES.TXT"
               else (18125600, 18125600), f"解析→常駐 {name}")

    shared_name = byte_run(events, "read", "9320:0171", 0x249DC, b"England",
                           15541700, 15542000)
    middle_name = byte_run(events, "write", "9320:0173", 0x26C58, b"England",
                           15541700, 15542000)
    require(shared_name[0] < middle_name[0], "國名中間複製的首字順序錯誤")
    middle_read = byte_run(events, "read", "0E2D:11A5", 0x26C58, b"England\0",
                           15542600, 15542700)
    persistent_name = byte_run(events, "write", "0E2D:11A5", 0x4CBBE, b"England\0",
                               15542600, 15542700)
    before(middle_name, middle_read, "國名中間→常駐")
    require(middle_read[0] == persistent_name[0], "國名常駐複製指令不一致")
    label_parse_read = byte_run(events, "read", "0E2D:1194", 0x249DC,
                                b"Immigration\0", 18125600, 18125700)
    label_persistent = byte_run(events, "write", "0E2D:11A5", 0x4DFD2,
                                b"mmigration", 18125600, 18125700)
    label_first = byte_run(events, "write", "0E2D:11A1", 0x4DFD1, b"I",
                           18125600, 18125700)
    require(label_parse_read[0] <= label_first[0] < label_persistent[0],
            "副標解析→常駐的讀寫次序錯誤")

    # 旗卡出現時，兩個不同常駐來源先後進同一個重用緩衝。
    name_runtime = byte_run(events, "read", "0E2D:11CF", 0x4CBBE,
                            b"England\0", 42859700, 42859800)
    name_source = byte_run(events, "write", "0E2D:11EB", 0x2A74A,
                           b"England\0", 42859700, 42859800)
    name_format = byte_run(events, "write", "0E2D:11A5", 0x2A6AE,
                           b"ENGLAND:", 42860300, 42860400)
    name_print = byte_run(events, "read", "0D21:00C6", 0x2A6AE,
                          b"ENGLAND:", 42860400, 42868000)
    before(name_source, name_format, "國名來源→格式化")
    before(name_format, name_print, "國名格式化→印字")
    label_runtime = byte_run(events, "read", "0E2D:11CF", 0x4DFD1,
                             b"Immigration\0", 42870500, 42870600)
    label_first_copy = byte_run(events, "write", "0E2D:11E7", 0x2A74A,
                                b"I", 42870500, 42870600)
    label_rest_copy = byte_run(events, "write", "0E2D:11EB", 0x2A74B,
                               b"mmigration", 42870500, 42870600)
    label_format = byte_run(events, "write", "0E2D:11A5", 0x2A6AE,
                            b"Immigration", 42871000, 42871100)
    label_print = byte_run(events, "read", "0D21:00C6", 0x2A6AE,
                           b"Immigration", 42871100, 42881000)
    before(name_print, label_runtime, "國名先於副標")
    require(name_runtime[0] < name_source[0] and label_runtime[0] < label_first_copy[0]
            and label_first_copy[0] < label_rest_copy[0], "常駐來源複製次序錯誤")
    before(label_rest_copy, label_format, "副標來源→格式化")
    before(label_format, label_print, "副標格式化→印字")
    require(not any(event["kind"] == "read" and 42850000 <= event["step"] < 42890000
                    and 0x21ACA <= event["linear"] < 0x21AD2 for event in events),
            "替代同文國名地址在印字期間被讀取，負例失效")

    # 畫布像素由前一輪同輸入的原版探針驗證；此處再綁定同檔指紋與寫入場域。
    old = load(args.reports.parent / "goal085-nation-card" / "goal085-a.json")
    require(old["version"] == "goal085-nation-card-probe-v1"
            and old["input_sha256"] == INPUT_SHA
            and not old["read_truncated"] and not old["write_truncated"],
            "前一輪原版畫布收據不符")
    for field, count in (("upper/0D21:012C", 144), ("lower/0D21:012C", 172)):
        require(old["write_sites"][field]["count"] == count, f"原版畫布寫入數不符：{field}")
    print("PASS：兩次冷啟動一致、同輸入控制組同狀態；兩欄 TXT→DOS→RAM→格式化→畫布來源鏈成立")


if __name__ == "__main__":
    main()
