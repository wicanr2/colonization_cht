#!/usr/bin/env python3
"""獨立核對 Game Options 第一／末列真實點擊的細相位原版收據。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA, SCREEN_SHA
from check_goal117_same_focus import CANVAS_BEFORE


PHASES = (1302000001, 1302001000, 1302100000, 1302500000,
          1303000001, 1303001000, 1303100000, 1303500000,
          1304000000, 1305000000, 1310000000, 1320000000)
LABELS = ("1300m",) + tuple(f"phase-{i:02d}" for i in range(len(PHASES))) + ("1325m", "1350m")
FIXTURES = {
    "first": ("goal119-first-row-click.inputs.json", "c7c5d91e67c3c49b3e3727f6b9275738bee4b8b1794a0e8ac40a325132ff0971"),
    "eighth": ("goal110-toggle-tutorial.inputs.json", "5ffad69f2e31e8c46cec86b543455331a4da432ce289d150846e4b1b682ff1a8"),
}
RECEIPTS = {"first": "314e538b0a4abbafe7278d7c2cbc2377c50c6997f9554c90726031cb87974235",
            "eighth": "cd3528d3fe144e89d4958fa177bd8de26d75ffda99311644918f381b54f8fa41"}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def differences(before, after):
    need(len(before) == len(after) == 64000, "原版畫布尺寸不符")
    return [(i % 320, i // 320, old, new)
            for i, (old, new) in enumerate(zip(before, after)) if old != new]


def frame(prefix, label, sample):
    out = {}
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == size and sha(data) == sample[field],
             f"{prefix.name}/{label}: 原版 {suffix} 收據不符")
        out[suffix] = data
    return out


def check_visual(scenes):
    first, eighth = scenes["first"], scenes["eighth"]
    need(first["1300m"] == eighth["1300m"], "兩分支點擊前原版畫面不同")
    for branch, scene in scenes.items():
        start = scene["1300m"]["canvas"]
        for label in ("phase-00", "phase-01"):
            need(scene[label]["canvas"] == start,
                 branch + "/" + label + ": 按下後過早推論底圖已重繪")
        first_change = differences(start, scene["phase-02"]["canvas"])
        x0, y0, x1, y1 = ((71, 111, 171, 154) if branch == "first" else
                          (66, 60, 254, 154))
        need(len(first_change) == (1136 if branch == "first" else 2782) and
             all(x0 <= x < x1 and y0 <= y < y1 for x, y, _, _ in first_change),
             branch + ": 按下後第一個有界畫布變化不符")
        second_change = differences(scene["phase-02"]["canvas"],
                                    scene["phase-03"]["canvas"])
        x0, y0, x1, y1 = ((71, 111, 171, 154) if branch == "first" else
                          (66, 111, 254, 155))
        need(len(second_change) == (1136 if branch == "first" else 2893) and
             all(x0 <= x < x1 and y0 <= y < y1 for x, y, _, _ in second_change),
             branch + ": 按下後第二個有界畫布變化不符")
        need(scene["phase-03"]["canvas"] == scene["phase-04"]["canvas"] ==
             scene["phase-05"]["canvas"] == scene["phase-06"]["canvas"],
             branch + ": 放開後即刻的底層畫布不符")
        icon_y = 64 if branch == "first" else 148
        expected_xy = {(73, icon_y), (74, icon_y), (73, icon_y + 1), (74, icon_y + 1)}
        old, new = ((149, 47) if branch == "first" else (47, 149))
        for suffix in ("canvas", "idx"):
            diff = differences(scene["phase-06"][suffix], scene["phase-07"][suffix])
            need(len(diff) == 4 and {(x, y) for x, y, _, _ in diff} == expected_xy and
                 all((before, after) == (old, new) for _, _, before, after in diff),
                 branch + ": 放開後核取中心四點或差分區域不符：" + suffix)
        for label in ("phase-08", "phase-09", "phase-10", "phase-11", "1325m", "1350m"):
            need(scene[label]["canvas"] == scene["phase-07"]["canvas"],
                 branch + "/" + label + ": 放開後底層畫布非固定抽樣")
    for label in LABELS:
        need(first[label]["pal"] == eighth[label]["pal"],
             label + ": 同時點色盤分歧")
    need(first["phase-00"]["pal"] != first["phase-09"]["pal"],
         "跨時間色盤變化被忽略")


def check(game, inputs, fixtures, reports):
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "正常玩家開局輸入版本不符")
    scenes = {}
    observations = {}
    for branch, (filename, fixture_sha) in FIXTURES.items():
        need(sha((fixtures / filename).read_bytes()) == fixture_sha,
             "玩家事件檔版本不符：" + filename)
        prefixes = [reports / f"{branch}-{variant}" for variant in ("a", "b", "control")]
        a_bytes = Path(f"{prefixes[0]}.json").read_bytes()
        need(a_bytes == Path(f"{prefixes[1]}.json").read_bytes(),
             branch + ": 雙冷啟動原版收據不一致")
        need(sha(a_bytes) == RECEIPTS[branch], branch + ": 固定原版收據指紋不符")
        observed = json.loads(a_bytes)
        control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
        for report, is_control in ((observed, False), (control, True)):
            need(report["version"] == "goal119-options-phase-v1" and
                 report["control"] is is_control and report["nation"] == "england" and
                 report["input_sha256"] == INPUT_SHA and
                 report["game_inputs_sha256"] == fixture_sha and
                 report["input_hashes"]["MENU.TXT"] == MENU_SHA and
                 report["option_phase_steps"] == list(PHASES) and
                 report["follow_until"] == 1_350_000_000 and len(report["opened"]) == 94,
                 branch + ": 固定版本、輸入或取樣條件不符")
        need(not control["print_reads"] and not control["writers"] and
             not control["option_source_reads"], branch + ": 控制組仍安裝觀測")
        for field in ("route", "sources", "transfers", "samples", "opened",
                      "key_events", "game_inputs"):
            need(observed[field] == control[field],
                 branch + ": 觀測擾動原版狀態：" + field)
        need(observed["game_inputs"][7:9] ==
             [{"step": 1302000000, "kind": "press", "X": 140,
               "Y": 65 if branch == "first" else 149, "Button": 0},
              {"step": 1303000000, "kind": "release", "X": 140,
               "Y": 65 if branch == "first" else 149, "Button": 0}],
             branch + ": 原版按下／放開事件不符")
        scene = {}
        for i, label in enumerate(LABELS):
            sample = observed["samples"][label]
            step = (1_300_000_000 if label == "1300m" else
                    1_325_000_000 if label == "1325m" else
                    1_350_000_000 if label == "1350m" else PHASES[i - 1])
            need(sample["step"] == step and sample["opened_count"] == 94,
                 branch + "/" + label + ": 取樣步數或開檔不符")
            for prefix in prefixes:
                raw = frame(prefix, label, sample)
                if prefix == prefixes[0]:
                    scene[label] = raw
        need(observed["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA and
             observed["samples"]["1300m"]["canvas_sha256"] == CANVAS_BEFORE,
             branch + ": 點擊前原版畫面指紋不符")
        scenes[branch] = scene
        observations[branch] = {"json_sha256": sha(a_bytes),
                                "press_change_bracket": [PHASES[1], PHASES[2]],
                                "release_icon_bracket": [PHASES[6], PHASES[7]]}
    need(scenes["first"]["1300m"] == scenes["eighth"]["1300m"],
         "兩分支原版共同起點不符")
    check_visual(scenes)
    return {"result": "PASS", "observations": observations,
            "limits": "只證固定兩列與取樣窗口；不能推完整八列每幀或啟用語意"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    receipt = check(args.game, args.inputs, args.fixtures, args.reports)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 77 if receipt["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
