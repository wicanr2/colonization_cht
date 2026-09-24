#!/usr/bin/env python3
"""獨立核對原版遊戲選項的來源讀取、中繼字元、印字緩衝與畫布。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal112_options_source import (FILE_SHA, FIXTURE_SHA, INPUT_SHA,
                                          MENU_SHA, SCREEN_SHA, SOURCES)


VERSION = "goal114-options-writer-v4"
PALETTE_SHA = "b81c99f3ef54dd7015107ece98b6770620b4c3472281172a92f0302f8ec6b4c9"
PREFIXES = (b"] ", b"] ", b"[ ", b"[ ", b"] ", b"] ", b"] ", b"[ ")
MATCHED_SOURCE_WRITES = 133
UNRESOLVED_SOURCE_STEP = 1253468919
RESIDENT_STARTS = (476096, 476140, 476186, 476233, 476278,
                   476318, 476355, 476399, 476447)


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(game, inputs, fixture, reports):
    if not inputs.is_file() or not fixture.is_file() or not all(
            (game / name).is_file() for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA and sha(fixture.read_bytes()) == FIXTURE_SHA,
         "正常玩家事件檔版本不符")
    raw_a = (reports / "writer-v4-a.json").read_bytes()
    need(raw_a == (reports / "writer-v4-b.json").read_bytes(), "兩次冷啟動收據不同")
    a = json.loads(raw_a)
    control = json.loads((reports / "writer-v4-control.json").read_bytes())
    need(a["version"] == control["version"] == VERSION and a["control"] is False
         and control["control"] is True and a["nation"] == "england"
         and a["follow_until"] == 1300000000 and
         a["input_sha256"] == control["input_sha256"] == INPUT_SHA and
         a["game_inputs_sha256"] == control["game_inputs_sha256"] == FIXTURE_SHA and
         not control["print_reads"] and not control["writers"] and
         not control["option_print_writes"] and not control["option_writer_reads"] and
         not control["option_intermediate_writes"] and not control["option_preprint"],
         "觀測版本、路徑或無監看控制不符")
    for key in ("route", "sources", "transfers", "samples", "opened", "key_events", "game_inputs"):
        need(a[key] == control[key], "監看擾動原版狀態：" + key)
    for variant in ("a", "b", "control"):
        need(sha((reports / f"writer-v4-{variant}.1300m.idx").read_bytes()) == SCREEN_SHA
             and sha((reports / f"writer-v4-{variant}.1300m.pal").read_bytes()) == PALETTE_SHA,
             "最終原版索引畫面或色盤不同：" + variant)
    need(len(a["option_preprint"]) == len(SOURCES) == 9,
         "九欄印前底圖缺失")
    for index in range(9):
        name = f"option-before-{index:02d}"
        before = (reports / f"writer-v4-a.{name}.canvas").read_bytes()
        need(len(before) == 64000 and before ==
             (reports / f"writer-v4-b.{name}.canvas").read_bytes() and
             sha(before) == a["option_preprint"][name]["canvas_sha256"],
             "印前畫布不同：" + name)
    game_data = (game / "GAME.TXT").read_bytes()
    for offset, source, _ in SOURCES:
        need(game_data[offset:offset + len(source)] == source,
             f"GAME.TXT:{offset:#x} 來源 bytes 不符")
    original_region = game_data[0x4CD:0x575]
    source_reads = [entry for entry in a["option_source_reads"]
                    if entry["cs_ip"] == "0E2D:1F76"]
    need(len(source_reads) == len(original_region) == 168 and
         all(entry["linear"] == 0x2B0CF + index and entry["value"] == value
             for index, (entry, value) in enumerate(zip(source_reads, original_region))),
         "原版解析讀取不再對應固定 GAME.TXT")
    visible = [entry for entry in a["print_reads"]
               if entry["cs_ip"] == "0D21:00C6" and
               1253400000 <= entry["step"] < 1253600000 and entry["value"]]
    expected = SOURCES[0][1] + b"".join(prefix + source.replace(b"~", b"")
                                       for prefix, (_, source, _) in zip(PREFIXES, SOURCES[1:]))
    need(len(visible) == len(expected) == 150 and
         bytes(entry["value"] for entry in visible) == expected,
         "九欄當次可見字元與原始文字／核取前綴不符")
    writes = a["option_print_writes"]
    reads = a["option_writer_reads"]
    intermediate = a["option_intermediate_writes"]
    need(len(writes) == 157 and len(reads) == 9021 and len(intermediate) == 205,
         "緩衝寫入／近端讀取事件數不符或已截斷")
    by_write = {(entry["step"], entry["linear"], entry["value"]): entry
                for entry in writes if entry["cs_ip"] == "0E2D:11A5"}
    near_reads = {(entry["step"], entry["linear"], entry["value"], entry["cs_ip"])
                  for entry in reads}
    for index, printed in enumerate(visible):
        writer = by_write.get((printed["step"] - 57, printed["linear"], printed["value"]))
        need(writer is not None and printed["linear"] ==
             (0x2ac78 if index < len(SOURCES[0][1]) else 0x2adde),
             f"第 {index} 個可見字元沒有同址57步前寫入")
        intermediate_address = 0x2acea if index < len(SOURCES[0][1]) else 0x2ae50
        need((writer["step"] - 7, intermediate_address, printed["value"], "0E2D:1194")
             in near_reads, f"第 {index} 個可見字元沒有中繼位址直接讀取")
    source_reads_at_formatter = [entry for entry in reads
                                 if entry["cs_ip"] == "8BDF:0567"]
    middle_writes = [entry for entry in intermediate
                     if entry["cs_ip"] == "8BDF:058E"]
    need(len(middle_writes) == 134, "原版格式常式寫入數不符")
    matched = [entry for entry in middle_writes if
               any(source["step"] == entry["step"] - 13 and
                   source["value"] == entry["value"]
                   for source in source_reads_at_formatter)]
    unresolved = [entry for entry in middle_writes if entry not in matched]
    need(len(matched) == MATCHED_SOURCE_WRITES and len(unresolved) == 1 and
         unresolved[0]["step"] == UNRESOLVED_SOURCE_STEP,
         "格式常式的上游讀取覆蓋率或已知缺口不符")
    local_copy = [entry for entry in intermediate
                  if entry["cs_ip"] == "0E2D:11EB" and
                  0x2ad70 <= entry["linear"] < 0x2ad81]
    need(len(local_copy) == 18 and all(
        any(source["step"] == entry["step"] and source["value"] == entry["value"]
            and source["cs_ip"] == "0E2D:11EB" and 0x2ad18 <= source["linear"] < 0x2ad30
            for source in reads) for entry in local_copy),
         "標題分段複製缺少同一步原版讀取")
    need(bytes(next(entry["value"] for entry in reads
                    if entry["cs_ip"] == "0E2D:1149" and entry["linear"] == 476096 + index)
               for index in range(len(SOURCES[0][1]))) == SOURCES[0][1],
         "標題高位址 RAM 讀取與原始 bytes 不符")
    resident_raw = (reports / "resident-a.json").read_bytes()
    need(resident_raw == (reports / "resident-b.json").read_bytes(),
         "高位址來源雙重播不一致")
    resident = json.loads(resident_raw)
    resident_control = json.loads((reports / "resident-control.json").read_bytes())
    need(resident["version"] == resident_control["version"] == "goal114-options-resident-v1"
         and resident["control"] is False and resident_control["control"] is True
         and len(resident["option_resident_writes"]) == 507
         and not resident_control["option_resident_writes"] and not resident["writers"],
         "高位址來源觀測版本、筆數或控制不符")
    for key in ("route", "sources", "transfers", "samples", "opened", "key_events", "game_inputs"):
        need(resident[key] == resident_control[key] == a[key],
             "高位址寫入監看擾動原版狀態：" + key)
    for variant in ("a", "b", "control"):
        need(sha((reports / f"resident-{variant}.1300m.idx").read_bytes()) == SCREEN_SHA
             and sha((reports / f"resident-{variant}.1300m.pal").read_bytes()) == PALETTE_SHA,
             "高位址觀測原版畫面或色盤不同：" + variant)
    resident_writes = resident["option_resident_writes"]
    for index, ((_, source, _), start) in enumerate(zip(SOURCES, RESIDENT_STARTS)):
        writer_ip = "0E2D:11A5" if index == 0 else "0E2D:11EB"
        for position, value in enumerate(source):
            matches = [entry for entry in resident_writes
                       if entry["cs_ip"] == writer_ip and
                       entry["linear"] == start + position and entry["value"] == value and
                       1253314011 < entry["step"] < 1253370000]
            need(len(matches) == 1,
                 f"GAME.TXT:{SOURCES[index][0]:#x} 第 {position} byte 未寫入高位址 RAM")
    return {"result": "PASS", "visible_chars": len(visible),
            "buffer_write_read_pairs": len(visible),
            "formatter_source_pairs": len(matched),
            "formatter_unresolved_step": UNRESOLVED_SOURCE_STEP,
            "title_local_copy_pairs": len(local_copy),
            "resident_source_bytes": sum(len(source) for _, source, _ in SOURCES),
            "screen_sha256": SCREEN_SHA,
            "receipt_sha256": sha(raw_a),
            "resident_receipt_sha256": sha(resident_raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixture, args.reports)
    except (OSError, ValueError, KeyError, IndexError, StopIteration) as error:
        parser.exit(1, f"FAIL：{error}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
