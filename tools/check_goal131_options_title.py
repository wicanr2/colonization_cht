#!/usr/bin/env python3
"""獨立驗證遊戲選項標題的原版逐幀可見時點與 ESC 失效。"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA, SCREEN_SHA


GAME_INPUT_SHA = "7ea15e5d4b7d86f3ffae32e62a6dda49975d56caf9a8749728bb66a0c70ea774"
WINDOW_CANVAS = "c1a32b289c17f6db4a65983fa4dd9ed04fa7024cfbc82a709c7ee87732c0a23b"
EXIT_CANVAS = "70bba2a713389fb94001d13685a99d044b4cc54eb9ccaa313ea4bf965bb9068c"
PHASES = ((1253010000, "absent"), (1253505000, "canvas-only"),
          (1253670000, "visible"), (1351020000, "absent"))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_audit(audit):
    need(audit["reference_sha256"] == WINDOW_CANVAS and
         audit["safe"] == [65, 44, 253, 59] and
         audit["frames"] == 891 and audit["canvas_match_frames"] == 591 and
         audit["vga_match_frames"] == 590 and
         audit["first_canvas_step"] == PHASES[1][0] and
         audit["first_vga_step"] == PHASES[2][0] and
         audit["last_vga_step"] == 1350855000 and
         audit["phase_at_end"] == "absent", "標題原版逐幀計數或相位不符")
    transitions = audit["transitions"]
    need(len(transitions) == len(PHASES) and
         [(item["step"], item["phase"]) for item in transitions] == list(PHASES) and
         [item["frame"] for item in transitions] == [7594, 7597, 7598, 8188] and
         all(item["mode"] == 19 for item in transitions) and
         transitions[2]["canvas_sha256"] == WINDOW_CANVAS and
         transitions[3]["canvas_sha256"] == EXIT_CANVAS,
         "標題畫布、真 VGA 或 ESC 失效轉移不符")


def validate_reports(observed, control):
    for report, is_control in ((observed, False), (control, True)):
        need(report["version"] == "goal131-options-title-screen-v1" and
             report["control"] is is_control and report["nation"] == "england" and
             report["after_b"] == report["after_follow"] == "enter" and
             report["follow_until"] == 1_400_000_000 and
             report["input_sha256"] == INPUT_SHA and
             report["game_inputs_sha256"] == GAME_INPUT_SHA and
             report["input_hashes"]["MENU.TXT"] == MENU_SHA and
             len(report["opened"]) == 94,
             "原版版本、輸入或路徑不符")
        validate_audit(report["option_title_screen_audit"])
    for field in ("route", "sources", "transfers", "samples", "opened",
                  "key_events", "game_inputs", "option_title_screen_audit"):
        need(observed[field] == control[field], "監看擾動原版狀態或逐幀畫面：" + field)
    need(not control["print_reads"] and not control["writers"] and
         not control["option_source_reads"] and not control["option_preprint"],
         "無監看控制仍記錄原版讀寫")
    first = observed["option_preprint"]["option-before-00"]
    need(first == {"canvas_sha256": "97c79b840a51d8b7de3841600871ed9bd2cfddbb52983073a8dcb7b97ca7ac8f",
                   "safe": [65, 44, 253, 59], "step": 1253411390,
                   "writer_ip": "0D21:012C", "writes": 319} and
         len(observed["option_source_reads"]) == 327 and
         len(observed["option_print_writes"]) == 157,
         "原版標題來源或當次印字前底圖不符")
    need(observed["samples"]["1300m"]["canvas_sha256"] == WINDOW_CANVAS and
         observed["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA and
         observed["samples"]["1375m"]["canvas_sha256"] == EXIT_CANVAS,
         "穩定選項視窗或 ESC 離頁畫面不符")


def checked_file(prefix, label, field, suffix, size, sample):
    data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
    need(len(data) == size and sha(data) == sample[field],
         f"{prefix.name}/{label}: 原版 {suffix} 檔案與收據不符")


def check(game, inputs, fixture, reports):
    if not inputs.is_file() or not fixture.is_file() or not all(
            (game / name).is_file() for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA and
         sha(fixture.read_bytes()) == GAME_INPUT_SHA, "正常玩家輸入不符")
    paths = [reports / name for name in ("a", "b", "control")]
    raw_a = Path(f"{paths[0]}.json").read_bytes()
    need(raw_a == Path(f"{paths[1]}.json").read_bytes(), "雙次冷啟動收據不同")
    observed = json.loads(raw_a)
    control = json.loads(Path(f"{paths[2]}.json").read_bytes())
    validate_reports(observed, control)
    for prefix in paths:
        for label in ("1300m", "1350m", "1375m", "1400m"):
            sample = observed["samples"][label]
            for field, suffix, size in (("indexed_sha256", "idx", 64000),
                                        ("canvas_sha256", "canvas", 64000),
                                        ("palette_sha256", "pal", 768)):
                checked_file(prefix, label, field, suffix, size, sample)
    return {"result": "PASS", "receipt_sha256": sha(raw_a),
            "first_canvas_step": PHASES[1][0], "first_vga_step": PHASES[2][0],
            "exit_step": PHASES[3][0]}


def self_test(observed, control):
    for title, edit in (
        ("提前宣稱可見", lambda obj: obj["option_title_screen_audit"].update(first_vga_step=1253505000)),
        ("漏掉 VGA 落後畫格", lambda obj: obj["option_title_screen_audit"].update(vga_match_frames=591)),
        ("漏掉 ESC 失效", lambda obj: obj["option_title_screen_audit"]["transitions"].pop()),
        ("錯原版來源", lambda obj: obj["option_preprint"]["option-before-00"].update(writes=318)),
    ):
        mutated = copy.deepcopy(observed)
        edit(mutated)
        try:
            validate_reports(mutated, control)
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
    if result["result"] == "PASS" and args.self_test:
        observed = json.loads((args.reports / "a.json").read_bytes())
        control = json.loads((args.reports / "control.json").read_bytes())
        self_test(observed, control)
    return 0 if result["result"] == "PASS" else 77


if __name__ == "__main__":
    raise SystemExit(main())
