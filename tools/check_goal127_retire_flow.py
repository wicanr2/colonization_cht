#!/usr/bin/env python3
"""獨立核對退休框 DOS 來源、常駐字串、格式化與真印字的有界收據。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA


FIXTURE_SHA = "a2638a3de1d9b4ecb6499efee6e8a07722c9c0e6b4dce6d0630094310ad464f8"
SCREEN_SHA = "bef37e89eadc25fd4dd98e218f783b17672f6089c3e2dc2a153712c70b900060"
PALETTE_SHA = "89e4327fe36fbf93bdf6dce7ca82b5c1076a3550b6faa035fbd665ad819e4f36"
PARTS = ((0x122, 176420, 176396, 476096, b"Do you really want to quit?"),
         (0x141, 176451, 176425, 476148, b"Yes"),
         (0x146, 176456, 176429, 476176, b"No"))
COMMON = ("route", "sources", "transfers", "samples", "opened", "key_events", "game_inputs")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(game, inputs, fixture, reports):
    originals = {**FILE_SHA, "MENU.TXT": MENU_SHA}
    if not inputs.is_file() or not fixture.is_file() or not all(
            (game / name).is_file() for name in originals):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in originals.items():
        need(digest((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(digest(inputs.read_bytes()) == INPUT_SHA and
         digest(fixture.read_bytes()) == FIXTURE_SHA, "玩家事件版本不符")
    game_text = (game / "GAME.TXT").read_bytes()
    for offset, _, _, _, raw in PARTS:
        need(game_text[offset:offset + len(raw)] == raw,
             f"GAME.TXT:{offset:#x} 原文 bytes 不符")

    receipts = {}
    for mode in ("flow", "resident"):
        first = (reports / f"{mode}-a.json").read_bytes()
        need(first == (reports / f"{mode}-b.json").read_bytes(),
             mode + " 雙次冷啟動收據不一致")
        seen = json.loads(first)
        control = json.loads((reports / f"{mode}-control.json").read_bytes())
        version = f"goal127-retire-{mode}-v1"
        need(seen["version"] == control["version"] == version and
             seen["control"] is False and control["control"] is True and
             seen["nation"] == control["nation"] == "england" and
             seen["follow_until"] == control["follow_until"] == 1350000000 and
             seen["input_sha256"] == control["input_sha256"] == INPUT_SHA and
             seen["game_inputs_sha256"] == control["game_inputs_sha256"] == FIXTURE_SHA,
             mode + " 版本、原版路徑或控制模式不符")
        for key in COMMON:
            need(seen[key] == control[key], mode + " 監看擾動原版狀態：" + key)
        need(not control["print_reads"] and not control["writers"],
             mode + " 無監看控制仍有事件")
        for variant in ("a", "b", "control"):
            prefix = reports / f"{mode}-{variant}"
            sample = (seen if variant != "control" else control)["samples"]["1275m"]
            for suffix, field, length, fixed in (
                    ("idx", "indexed_sha256", 64000, SCREEN_SHA),
                    ("pal", "palette_sha256", 768, PALETTE_SHA)):
                data = Path(f"{prefix}.1275m.{suffix}").read_bytes()
                need(len(data) == length and digest(data) == sample[field] == fixed,
                     mode + "/" + variant + " 原版畫面或色盤不符")
        for offset, source, _, _, raw in PARTS:
            transfers = [item for item in seen["transfers"]
                         if item["name"] == "GAME.TXT" and
                         item["file_offset"] == offset and item["step"] == 1253245641]
            need(len(transfers) == 1 and transfers[0]["match"] is True and
                 transfers[0]["read_pos"] == 0 and transfers[0]["got"] == 512 and
                 transfers[0]["candidate_linear"] == source and
                 transfers[0]["prefix_sha256"] == digest(raw),
                 f"{mode} GAME.TXT:{offset:#x} 當次 DOS 讀入不符")
        receipts[mode] = (seen, control, digest(first))
    flow, flow_control, flow_sha = receipts["flow"]
    resident, resident_control, resident_sha = receipts["resident"]
    for key in COMMON:
        need(flow[key] == resident[key] == flow_control[key] == resident_control[key],
             "兩種互斥監看未取得同一原版狀態：" + key)
    reads = flow["retire_flow_reads"]
    writes = flow["retire_flow_writes"]
    high_writes = resident["retire_resident_writes"]
    need(flow["retire_flow_window"] == resident["retire_resident_window"] ==
         [1253240000, 1253355000] and len(reads) == 10303 and
         len(writes) == 2596 and len(high_writes) == 346 and
         not flow_control["retire_flow_reads"] and
         not flow_control["retire_flow_writes"] and
         not resident_control["retire_resident_writes"],
         "資料流時窗、事件數或無監看控制不符")
    read_index = {(entry["step"], entry["cs_ip"], entry["linear"], entry["value"])
                  for entry in reads}
    write_index = {(entry["step"], entry["cs_ip"], entry["linear"], entry["value"])
                   for entry in writes}

    parse_changed = 0
    for _, source, parsed, high, raw in PARTS:
        for position, value in enumerate(raw):
            hits = [entry for entry in reads if entry["cs_ip"] == "0E2D:1F76" and
                    entry["linear"] == source + position and entry["value"] == value and
                    1253245641 < entry["step"] < 1253250000]
            need(len(hits) == 1, "解析器未讀取固定來源字節")
            changed = ((hits[0]["step"] + 5, "0E2D:1F86", parsed + position, value)
                       in write_index)
            # WatchWrites 只通知值真的改變：問句第20字節 't' 原值相同。
            need(changed == (not (source == 176420 and position == 19)),
                 "解析器變更寫入數或已知同值缺口不同")
            parse_changed += changed
        high_raw = raw + b"\0"
        for position, value in enumerate(high_raw):
            ip = "0E2D:11A5" if high == 476096 else "0E2D:11EB"
            if high == 476176 and position == 2:
                ip = "0E2D:11EF"
            events = [entry for entry in high_writes if
                      entry["cs_ip"] == ip and entry["linear"] == high + position and
                      entry["value"] == value and 1253270000 < entry["step"] < 1253290000]
            need(len(events) == 1, "常駐字串缺少原版寫入")
            if ip != "0E2D:11EF":
                need(any(entry["step"] == events[0]["step"] and
                         entry["cs_ip"] == ip and entry["value"] == value and
                         entry["linear"] < 0x2b180 for entry in reads),
                     "常駐字串寫入缺少同一步低位址來源讀取")
    need(parse_changed == 31, "解析器已觀測變更寫入數不符")

    visible = [entry for entry in flow["print_reads"]
               if entry["cs_ip"] == "0D21:00C6" and entry["value"] and
               1253314000 <= entry["step"] < 1253355000]
    need(len(visible) == 31 and
         bytes(entry["value"] for entry in visible) == b"Do you reallywant to quit?YesNo" and
         [sum(entry["linear"] == address for entry in visible)
          for address in (175232, 175590)] == [26, 5],
         "退休框原版實際印字序列或分行不符")
    print_changed = 0
    for entry in visible:
        step, address, value = entry["step"] - 57, entry["linear"], entry["value"]
        middle = 175346 if address == 175232 else 175704
        need((step - 7, "0E2D:1194", middle, value) in read_index and
             (step, "0E2D:11A5", middle, value) in read_index and
             any(source["step"] == step - 180 and source["cs_ip"] == "8BDF:0567" and
                 source["value"] == value for source in reads),
             "實際印字缺格式化來源或近端讀取")
        changed = ((step, "0E2D:11A5", address, value) in write_index and
                   (step - 167, "8BDF:058E", middle, value) in write_index)
        need(changed == (entry["step"] != 1253325978),
             "實際印字變更寫入或已知同值缺口不同")
        print_changed += changed
    need(print_changed == 30, "印字緩衝已觀測變更寫入數不符")
    return {"result": "PASS", "source_bytes_read": 32,
            "parser_changed_writes": parse_changed,
            "resident_bytes_written": 35,
            "visible_glyph_reads": len(visible),
            "visible_changed_write_pairs": print_changed,
            "same_value_unobserved_byte_cases": 2,
            "flow_receipt_sha256": flow_sha,
            "resident_receipt_sha256": resident_sha}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixture, args.reports)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        parser.exit(1, f"FAIL：{error}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
