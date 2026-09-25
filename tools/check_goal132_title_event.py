#!/usr/bin/env python3
"""獨立核對標題當次讀字、畫布寫入與真 VGA 同步；原版缺失回 SKIP。"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA, SCREEN_SHA
from check_goal131_options_title import (GAME_INPUT_SHA, WINDOW_CANVAS,
                                         EXIT_CANVAS, validate_audit)


SOURCE = b"Set Game Options"
PREPRINT_SHA = "97c79b840a51d8b7de3841600871ed9bd2cfddbb52983073a8dcb7b97ca7ac8f"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_event(event, before):
    need(event["source_file_offset"] == 0x4CD and
         event["source_sha256"] == sha(SOURCE) and
         event["read_ip"] == "0D21:00C6" and
         event["source_linear"] == [0x2AC78, 0x2AC79] and
         event["read_start_step"] == 1253411339 and
         event["read_end_step"] == 1253428948 and
         event["read_count"] == 2 * len(SOURCE) and
         event["read_mismatches"] == 0 and
         event["first_read_canvas_sha256"] ==
         event["first_write_canvas_sha256"] == sha(before) == PREPRINT_SHA,
         "標題來源鍵、當次讀字或印前底圖不符")
    reads = event["read_operands"]
    need(len(reads) == 2 * len(SOURCE), "標題讀字筆數不足")
    previous = 0
    for i, read in enumerate(reads):
        addr = 0x2AC78 + i % 2
        value = SOURCE[i // 2] if i % 2 == 0 else 0
        need(read["step"] > previous and
             event["read_start_step"] <= read["step"] <= event["read_end_step"] and
             read["linear"] == read["ss_bx_linear"] ==
             read["ss"] * 16 + read["bx"] == addr and read["value"] == value,
             f"標題第{i}筆 SS:BX 讀字不符")
        previous = read["step"]
    need(reads[0]["step"] == event["read_start_step"] and
         reads[-1]["step"] == event["read_end_step"] and
         event["writer_ip"] == "0D21:012C" and
         event["write_first_step"] == 1253411390 and
         event["write_last_step"] == 1253428790 and
         event["write_count"] == 319 and
         event["write_bbox"] == [67, 47, 147, 56] and
         event["write_colors"] == {"68": 146, "47": 103, "128": 70},
         "標題當次畫布寫入筆數、矩形或色號不符")


def validate_reports(observed, control, before):
    for report, is_control in ((observed, False), (control, True)):
        need(report["version"] == "goal131-options-title-screen-v1" and
             report["control"] is is_control and report["nation"] == "england" and
             report["after_b"] == report["after_follow"] == "enter" and
             report["follow_until"] == 1_400_000_000 and
             report["input_sha256"] == INPUT_SHA and
             report["game_inputs_sha256"] == GAME_INPUT_SHA and
             report["input_hashes"]["MENU.TXT"] == MENU_SHA and
             len(report["opened"]) == 94,
             "原版版本、輸入或正常玩家路徑不符")
        validate_audit(report["option_title_screen_audit"])
    for field in ("route", "sources", "transfers", "samples", "opened",
                  "key_events", "game_inputs"):
        need(observed[field] == control[field], "監看擾動原版狀態：" + field)
    for field, value in observed["option_title_screen_audit"].items():
        if field != "event":
            need(control["option_title_screen_audit"][field] == value,
                 "監看擾動畫格或相位：" + field)
    need(not control["print_reads"] and not control["writers"] and
         not control["option_source_reads"] and not control["option_preprint"] and
         control["option_title_screen_audit"]["event"]["read_count"] == 0 and
         control["option_title_screen_audit"]["event"]["write_count"] == 0,
         "無監看控制仍觀測原版讀寫")
    validate_event(observed["option_title_screen_audit"]["event"], before)
    first = observed["option_preprint"]["option-before-00"]
    need(first["step"] == 1253411390 and first["safe"] == [65, 44, 253, 59] and
         first["writes"] == 319 and first["canvas_sha256"] == sha(before),
         "首字畫布寫入與印前圖不一致")
    need(observed["samples"]["1300m"]["canvas_sha256"] == WINDOW_CANVAS and
         observed["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA and
         observed["samples"]["1375m"]["canvas_sha256"] == EXIT_CANVAS,
         "原版視窗完成或 ESC 離頁畫面不符")


def check(game, inputs, fixture, reports):
    if not inputs.is_file() or not fixture.is_file() or not all(
            (game / name).is_file() for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或正常玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA and
         sha(fixture.read_bytes()) == GAME_INPUT_SHA,
         "正常玩家輸入版本不符")
    prefixes = [reports / name for name in ("a", "b", "control")]
    raw_a = Path(f"{prefixes[0]}.json").read_bytes()
    need(raw_a == Path(f"{prefixes[1]}.json").read_bytes(),
         "雙冷啟動報告不同")
    observed = json.loads(raw_a)
    control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
    before = Path(f"{prefixes[0]}.option-before-00.canvas").read_bytes()
    need(len(before) == 64000 and
         before == Path(f"{prefixes[1]}.option-before-00.canvas").read_bytes(),
         "兩次標題印前原版畫布不同")
    validate_reports(observed, control, before)
    for prefix in prefixes:
        for label in ("1300m", "1350m", "1375m", "1400m"):
            sample = observed["samples"][label]
            for field, suffix, size in (("indexed_sha256", "idx", 64000),
                                        ("canvas_sha256", "canvas", 64000),
                                        ("palette_sha256", "pal", 768)):
                data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
                need(len(data) == size and sha(data) == sample[field],
                     f"{prefix.name}/{label}: 原版{suffix}收據與實檔不同")
    return {"result": "PASS", "receipt_sha256": sha(raw_a),
            "read_count": len(observed["option_title_screen_audit"]["event"]["read_operands"]),
            "write_count": 319, "first_vga_step": 1253670000}


def self_test(observed, control, before):
    changes = (
        ("來源讀字", lambda x: x["option_title_screen_audit"]["event"]["read_operands"][9].update(value=1)),
        ("SS:BX運算元", lambda x: x["option_title_screen_audit"]["event"]["read_operands"][0].update(bx=0)),
        ("原版寫入色號", lambda x: x["option_title_screen_audit"]["event"]["write_colors"].update({"68": 145})),
        ("提早顯示", lambda x: x["option_title_screen_audit"].update(first_vga_step=1253505000)),
        ("ESC後殘留", lambda x: x["option_title_screen_audit"]["transitions"].pop()),
        ("無監看控制分歧", lambda x: x["samples"]["1300m"].update(memory_sha256="wrong")),
    )
    for title, mutate in changes:
        changed = copy.deepcopy(observed)
        mutate(changed)
        try:
            validate_reports(changed, control, before)
        except ValueError:
            print("PASS：拒絕" + title)
        else:
            raise AssertionError("未拒絕" + title)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = check(args.game, args.inputs, args.fixture, args.reports)
    print(json.dumps(result, ensure_ascii=False))
    if args.self_test and result["result"] == "PASS":
        self_test(json.loads((args.reports / "a.json").read_bytes()),
                  json.loads((args.reports / "control.json").read_bytes()),
                  (args.reports / "a.option-before-00.canvas").read_bytes())
    return 0 if result["result"] == "PASS" else 77


if __name__ == "__main__":
    raise SystemExit(main())
