#!/usr/bin/env python3
"""獨立核對遊戲選項九欄的原版檔案、RAM 讀取、印字與畫面收據。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA


VERSION = "goal112-game-options-source-v2"
MENU_SHA = "5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702"
FIXTURE_SHA = "c4e462678323df8e1915ffcd363f7e7eb83cee4e85e09f618c9206418977e539"
SCREEN_SHA = "7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546"
SOURCES = (
    (0x4CD, b"Set Game Options", (67, 47, 147, 55)),
    (0x4E9, b"Show ~Indian Moves", (82, 61, 166, 68)),
    (0x4FD, b"Show ~Foreign Moves", (82, 73, 173, 81)),
    (0x512, b"Fast Piece ~Slide", (82, 85, 155, 93)),
    (0x525, b"~End of Turn", (83, 97, 133, 104)),
    (0x533, b"~Autosave", (83, 109, 123, 117)),
    (0x53E, b"~Combat Analysis", (83, 121, 158, 129)),
    (0x550, b"Water Color C~ycling", (82, 133, 171, 141)),
    (0x566, b"~Tutorial Hints", (84, 145, 144, 153)),
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_observed(record, game_data, indexed):
    need(record["version"] == VERSION and record["control"] is False,
         "來源探針版本或觀測模式不符")
    need(record["nation"] == "england" and record["after_b"] == "enter" and
         record["after_follow"] == "enter" and record["follow_until"] == 1300000000 and
         record["input_sha256"] == INPUT_SHA and record["game_inputs_sha256"] == FIXTURE_SHA,
         "正常玩家路徑或輸入不符")
    need(record["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA and
         len(indexed) == 64000 and digest(indexed) == SCREEN_SHA,
         "原版選項索引畫面不符")
    need(game_data[0x4A8:0x4B4] == b"@GAMEOPTIONS",
         "選項來源區標記不符")
    expected_sources = {(offset, text.decode("ascii")) for offset, text, _ in SOURCES}
    actual_sources = {(item["offset"], item["bytes"]) for item in record["sources"]
                      if item["name"] == "GAME.TXT" and item["offset"] in
                      {offset for offset, _, _ in SOURCES}}
    need(actual_sources == expected_sources, "九欄來源清單不完整")
    for offset, text, _ in SOURCES:
        need(game_data[offset:offset + len(text)] == text,
             f"GAME.TXT:{offset:#x} 原始 bytes 不符")
        matching = [item for item in record["transfers"]
                    if item["name"] == "GAME.TXT" and item["file_offset"] == offset and
                    item["step"] == 1253314011]
        need(len(matching) == 1 and matching[0]["match"] is True and
             matching[0]["read_pos"] == 1024 and matching[0]["got"] == 512 and
             matching[0]["candidate_linear"] == 0x2B0CF + offset - 0x4CD and
             matching[0]["prefix_sha256"] == digest(text),
             f"GAME.TXT:{offset:#x} DOS 目的緩衝不符")
    source_reads = [item for item in record["option_source_reads"]
                    if item["cs_ip"] == "0E2D:1F76"]
    expected_region = game_data[0x4CD:0x575]
    need(len(source_reads) == len(expected_region) == 168 and
         all(item["linear"] == 0x2B0CF + index
             for index, item in enumerate(source_reads)) and
         bytes(item["value"] for item in source_reads) == expected_region and
         1253314011 < source_reads[0]["step"] < source_reads[-1]["step"] < 1253400000,
         "原版解析常式未逐 byte 讀到完整九欄來源")
    printed = bytes(item["value"] for item in record["print_reads"]
                    if item["cs_ip"] == "0D21:00C6" and item["value"] != 0 and
                    1253400000 <= item["step"] < 1253600000)
    cursor = 0
    for _, text, _ in SOURCES:
        visible = text.replace(b"~", b"")
        found = printed.find(visible, cursor)
        need(found >= cursor, f"原版印字未依序顯示 {visible.decode('ascii')}")
        cursor = found + len(visible)
    for _, _, expected in SOURCES:
        x0 = 65 if expected[1] == 47 else 81
        points = [(x, y) for y in range(expected[1], expected[3])
                  for x in range(x0, 245)
                  if indexed[y * 320 + x] in (68, 47)]
        rect = (min(x for x, _ in points), min(y for _, y in points),
                max(x for x, _ in points) + 1, max(y for _, y in points) + 1)
        need(rect == expected, f"原版九欄墨跡矩形不符：{rect} != {expected}")
    return {"source_rows": len(SOURCES), "parsed_bytes": len(source_reads),
            "print_span": [1253400000, 1253600000], "screen_sha256": SCREEN_SHA}


def check(game, inputs, fixture, reports):
    if not inputs.is_file() or not fixture.is_file() or not all(
            (game / name).is_file() for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(digest((game / name).read_bytes()) == expected,
             f"原版版本不符：{name}")
    need(digest(inputs.read_bytes()) == INPUT_SHA and
         digest(fixture.read_bytes()) == FIXTURE_SHA,
         "正常玩家事件檔版本不符")
    raw_a = (reports / "source-v2-a.json").read_bytes()
    raw_b = (reports / "source-v2-b.json").read_bytes()
    need(raw_a == raw_b, "兩次冷啟動來源收據不一致")
    observed = json.loads(raw_a)
    control = json.loads((reports / "source-v2-control.json").read_bytes())
    need(control["version"] == VERSION and control["control"] is True and
         not control["option_source_reads"] and not control["print_reads"] and
         not control["writers"], "無監看控制模式不符")
    for field in ("route", "sources", "transfers", "samples", "opened", "key_events", "game_inputs"):
        need(observed[field] == control[field], f"原版狀態受監看擾動：{field}")
    indexed = (reports / "source-v2-a.1300m.idx").read_bytes()
    for name in ("source-v2-b", "source-v2-control"):
        need((reports / f"{name}.1300m.idx").read_bytes() == indexed,
             f"{name} 原版畫面不一致")
    return {"result": "PASS", **verify_observed(observed, (game / "GAME.TXT").read_bytes(), indexed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixture, args.reports)
    except (OSError, ValueError, KeyError, IndexError) as error:
        parser.exit(1, f"FAIL：{error}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
