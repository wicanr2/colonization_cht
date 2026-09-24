#!/usr/bin/env python3
"""獨立核對遊戲選項純移鼠、既有實際點擊與 ESC 離頁相位。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA, SCREEN_SHA


FIXTURES = {
    "hover-first": "bfa4245372016e2a3a64e6e75e9bb553b27c6531085c12bff70e10670c36c9be",
    "hover-last": "a63a789b575dca90bfd1de86395d4cbc40e89be7a4ca73e8f257ea40a8364bff",
    "exit": "7ea15e5d4b7d86f3ffae32e62a6dda49975d56caf9a8749728bb66a0c70ea774",
}
INDEXED = {
    "hover-first": (SCREEN_SHA,
                    "30693fd751e4cf4a674fddf07d4c8e3993f77d2c223db74d8d3dc55847215cb6",
                    "d224047412ffdcae71c59a8d13a2b46b0a49af5194362965cf0c78cf93a5e5ed",
                    "d224047412ffdcae71c59a8d13a2b46b0a49af5194362965cf0c78cf93a5e5ed"),
    "hover-last": (SCREEN_SHA,
                   "dfc7fb83705e31a1ae6fb65d637dce98bfe008a21b80800069dada05a1fc001f",
                   "d224047412ffdcae71c59a8d13a2b46b0a49af5194362965cf0c78cf93a5e5ed",
                   "d224047412ffdcae71c59a8d13a2b46b0a49af5194362965cf0c78cf93a5e5ed"),
    "exit": (SCREEN_SHA,
             "d224047412ffdcae71c59a8d13a2b46b0a49af5194362965cf0c78cf93a5e5ed",
             "d224047412ffdcae71c59a8d13a2b46b0a49af5194362965cf0c78cf93a5e5ed",
             "e556a23e39370303c2d8b4a86cbb8d5e901b1a4f2cc36b9f9aebe53fe58ed9b0"),
}
LABELS = ("1300m", "1325m", "1350m", "1375m", "1400m")
WINDOW_CANVAS = "c1a32b289c17f6db4a65983fa4dd9ed04fa7024cfbc82a709c7ee87732c0a23b"
EXIT_CANVAS = "70bba2a713389fb94001d13685a99d044b4cc54eb9ccaa313ea4bf965bb9068c"
OLD_CLICK_INPUT = "49c1e006724bb8b51a1b0dff6786e696f01dc5b9b1491c282efb9965b13a9d93"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(prefix, label, sample):
    result = {}
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == size and sha(data) == sample[field],
             f"{prefix.name}/{label}: 原版 {suffix} 與收據不符")
        result[suffix] = data
    return result


def changed(before, after):
    need(len(before) == len(after) == 64000, "原版畫布尺寸不符")
    return [(index % 320, index // 320) for index, (a, b) in
            enumerate(zip(before, after)) if a != b]


def check(game, inputs, fixtures, reports, old_reports):
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "正常玩家開局輸入版本不符")
    for name, expected in FIXTURES.items():
        need(sha((fixtures / f"goal116-{name}.inputs.json").read_bytes()) == expected,
             "選項玩家輸入版本不符：" + name)

    scenes = {}
    receipts = {}
    for name, fixture_sha in FIXTURES.items():
        prefixes = [reports / f"{name}-{suffix}" for suffix in ("a", "b", "control")]
        observed_bytes = Path(f"{prefixes[0]}.json").read_bytes()
        need(observed_bytes == Path(f"{prefixes[1]}.json").read_bytes(),
             name + ": 雙次冷啟動收據不同")
        observed = json.loads(observed_bytes)
        control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
        for report, is_control in ((observed, False), (control, True)):
            need(report["version"] == "goal112-game-options-source-v2" and
                 report["control"] is is_control and report["nation"] == "england" and
                 report["next_enter"] is True and report["after_b"] ==
                 report["after_follow"] == "enter" and
                 report["follow_until"] == 1_400_000_000 and
                 report["input_sha256"] == INPUT_SHA and
                 report["game_inputs_sha256"] == fixture_sha and
                 report["input_hashes"]["MENU.TXT"] == MENU_SHA and
                 len(report["opened"]) == 94,
                 name + ": 原版、路徑或版本不符")
        need(not control["print_reads"] and not control["writers"] and
             not control["option_source_reads"], name + ": 控制仍有監看")
        for field in ("route", "sources", "transfers", "samples", "opened",
                      "key_events", "game_inputs"):
            need(observed[field] == control[field],
                 name + ": 監看擾動原版狀態：" + field)
        scenes[name] = {}
        for label in LABELS:
            sample = observed["samples"][label]
            need(sample["step"] == int(label[:-1]) * 1_000_000,
                 name + "/" + label + ": 步數不符")
            for prefix in prefixes:
                result = raw(prefix, label, sample)
                if prefix == prefixes[0]:
                    scenes[name][label] = result
        need(all(observed["samples"][label]["indexed_sha256"] == expected
                 for label, expected in zip(LABELS[:4], INDEXED[name])) and
             observed["samples"]["1400m"]["indexed_sha256"] == INDEXED[name][3],
             name + ": 畫面相位指紋不符")
        for label in LABELS:
            expected_canvas = (EXIT_CANVAS if name == "exit" and label in ("1375m", "1400m")
                               else WINDOW_CANVAS)
            need(observed["samples"][label]["canvas_sha256"] == expected_canvas,
                 name + "/" + label + ": 底層畫布不符")
        receipts[name] = sha(observed_bytes)

    first = scenes["hover-first"]
    last = scenes["hover-last"]
    leaving = scenes["exit"]
    need(first["1300m"]["idx"] == last["1300m"]["idx"] ==
         leaving["1300m"]["idx"], "三分支選項視窗起點不同")
    cursor = changed(first["1325m"]["idx"], last["1325m"]["idx"])
    need(len(cursor) == 160 and first["1325m"]["canvas"] ==
         last["1325m"]["canvas"] and first["1325m"]["pal"] ==
         last["1325m"]["pal"], "純移鼠不只改變游標合成畫面")
    for label in ("1350m", "1375m", "1400m"):
        need(first[label]["idx"] == last[label]["idx"] and
             first[label]["canvas"] == last[label]["canvas"] and
             first[label]["pal"] == last[label]["pal"],
             label + ": 移到框外後兩分支畫面未合流")
    need(leaving["1350m"]["idx"] == first["1350m"]["idx"] and
         leaving["1350m"]["canvas"] == first["1350m"]["canvas"],
         "ESC 前不是同一視窗畫面")
    exit_diff = changed(leaving["1350m"]["canvas"], leaving["1375m"]["canvas"])
    need(len(exit_diff) == 22885 and
         (min(x for x, _ in exit_diff), min(y for _, y in exit_diff),
          max(x for x, _ in exit_diff) + 1, max(y for _, y in exit_diff) + 1) ==
         (62, 41, 258, 159) and
         leaving["1375m"]["pal"] == first["1375m"]["pal"],
         "ESC 離頁畫布相位／同時點色盤不符")
    exit_report = json.loads((reports / "exit-a.json").read_bytes())
    after_escape = [event for event in exit_report["key_events"]
                    if event["step"] >= 1_351_000_000]
    need(any(event["pending"] == 1 for event in after_escape) and
         any(event["pending"] == 0 for event in after_escape) and
         exit_report["samples"]["1375m"]["key_pending"] == 0,
         "ESC 未經原版取走")

    old_names = ("tutorial-then-first-row-explore",
                 "tutorial-then-first-row-replay2",
                 "tutorial-then-first-row-control")
    old_prefixes = [old_reports / name for name in old_names]
    old_bytes = Path(f"{old_prefixes[0]}.json").read_bytes()
    need(old_bytes == Path(f"{old_prefixes[1]}.json").read_bytes(),
         "既有末列點擊雙重播不同")
    old = json.loads(old_bytes)
    old_control = json.loads(Path(f"{old_prefixes[2]}.json").read_bytes())
    need(old["version"] == old_control["version"] == "goal110-game-input-audit-v1"
         and old["control"] is False and old_control["control"] is True
         and old["input_sha256"] == old_control["input_sha256"] == INPUT_SHA
         and old["game_inputs_sha256"] == old_control["game_inputs_sha256"] == OLD_CLICK_INPUT
         and old["follow_until"] == old_control["follow_until"] == 1_400_000_000
         and old["route"] == old_control["route"] and
         old["opened"] == old_control["opened"] and
         old["samples"] == old_control["samples"] and
         old["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA,
         "既有末列實際點擊來源不符")
    clicked = raw(old_prefixes[0], "1325m", old["samples"]["1325m"])
    click_canvas_diff = changed(clicked["canvas"], last["1325m"]["canvas"])
    first_row = [(x, y) for x, y in click_canvas_diff if 59 <= y < 71]
    last_row = [(x, y) for x, y in click_canvas_diff if 143 <= y < 155]
    checkbox = [(x, y) for x, y in last_row if 68 <= x < 80]
    need(clicked["pal"] == last["1325m"]["pal"] and
         len(changed(clicked["idx"], last["1325m"]["idx"])) == 3390 and
         len(click_canvas_diff) == 3407 and len(first_row) == 1646 and
         len(last_row) == 1761 and len(checkbox) == 91,
         "點擊末列與純移鼠畫面差異不符")
    return {"result": "PASS", "hover_cursor_pixels": len(cursor),
            "hover_underlying_canvas_pixels": 0,
            "click_underlying_canvas_pixels": len(click_canvas_diff),
            "click_first_row_pixels": len(first_row),
            "click_last_row_pixels": len(last_row),
            "click_checkbox_region_pixels": len(checkbox),
            "esc_underlying_canvas_pixels": len(exit_diff),
            "esc_diff_bbox": [62, 41, 258, 159],
            "receipt_sha256": receipts,
            "old_click_receipt_sha256": sha(old_bytes)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--old-reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures, args.reports, args.old_reports)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        parser.exit(1, f"FAIL：{error}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
