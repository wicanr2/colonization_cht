#!/usr/bin/env python3
"""獨立核對 Game Options 第四／七列與第一列的同焦點原版畫面。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA, SCREEN_SHA


FIXTURES = {
    "baseline": ("goal111-first-row-only.inputs.json", "86896d9d5444cd00fe9fd82ac35a9b33e944620d0dcb4e8f638c885c04d89a1c"),
    "fourth": ("goal117-fourth-then-first.inputs.json", "dbc4e0d7af8678e449c67808f10d367b91a58100e7d34ed8d42b2a5789fa5b83"),
    "seventh": ("goal117-seventh-then-first.inputs.json", "64b75c2c506e731c005e52f7745e2868c5834ce90b38492aafac01c6cae507ba"),
}
LABELS = ("1300m", "1325m", "1350m", "1375m", "1400m")
CANVAS_BEFORE = "c1a32b289c17f6db4a65983fa4dd9ed04fa7024cfbc82a709c7ee87732c0a23b"
OLD_LAST = "4e2735445a2f67aa7f001a6a4614474d06813875ebd291f21eb28c5512888778"
OLD_BASE = "6358700bc50ff2b348ba35ac4971932ef371c63cee88eba3ad81dbee1972444e"
EXPECTED_DELTA = {
    "fourth": [(73, 100, 47, 149), (74, 100, 47, 149),
               (73, 101, 47, 149), (74, 101, 47, 149)],
    "seventh": [(73, 136, 149, 47), (74, 136, 149, 47),
                (73, 137, 149, 47), (74, 137, 149, 47)],
}
MID_SCENES = {
    "baseline": (SCREEN_SHA, CANVAS_BEFORE),
    "fourth": ("10a1f17dff64c6f7a3923f43df70a5018e17ade3cdcf2dd60d59757880180f6d",
               "f4449d332ca089a9046fd5e0f1b41319d214d55318573846682e53514ff845ea"),
    "seventh": ("86b1b9699a7da2f6acf5013331fd20c6c7cf1f0219415cedbfe1b2c691d6a4d2",
                "3757ad82a7da771f7c2d0ca411345d83af735c96f780eb294f5659dd1935e50c"),
}
FINAL_SCENES = {
    "baseline": ("7b6bf011f389933ce5a09553f10a1f069a6d3bf5f26fe7978bf130897e80f450",
                 "b88bf062e32c968caeb6856a16b74b8f60924b232b322d3ad90a4502929bd008"),
    "fourth": ("2b00e6738d2b2ee5c1070e34938e795441015446c7745888f4f8e378ee7e0078",
               "34078312c32d8e075375a0ada607fd7d5d8b83dd42f9124f2bb6ce665ce93f54"),
    "seventh": ("164d845fd749fca9d14e607d1d46cb2cc1aced2c311a3f706e869d0ec795a82c",
                "475adf0108acb821cc615e8b8c7d0814fc39054a86cdc3f16e0b07007e6fc850"),
}
MID_DIFF_COUNTS = {"fourth": (3467, 1646, 1821, 95, 107),
                   "seventh": (3293, 1646, 1647, 131, 143)}
PALETTES = {"1375m": "94c4b1630d99483212fc8bd85dec3751ffd0d9423eedb395dc0004e9f823976b",
            "1400m": "898669705f7ec9ad40dd0bfa57eadd2a922a033478ee0a5d1a8ad602ddc2ce65"}


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
             f"{prefix.name}/{label}: {suffix} 原版位元組不符")
        result[suffix] = data
    return result


def changes(left, right):
    need(len(left) == len(right) == 64000, "原版畫布尺寸不符")
    return [(i % 320, i // 320, a, b)
            for i, (a, b) in enumerate(zip(left, right)) if a != b]


def check(game, inputs, fixtures, reports, old_reports):
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "正常玩家開局輸入版本不符")
    for filename, expected in FIXTURES.values():
        need(sha((fixtures / filename).read_bytes()) == expected,
             "玩家事件檔版本不符：" + filename)

    scenes = {}
    receipts = {}
    for branch, (_, fixture_sha) in FIXTURES.items():
        prefixes = [reports / f"{branch}-{variant}"
                    for variant in ("a", "b", "control")]
        first_bytes = Path(f"{prefixes[0]}.json").read_bytes()
        need(first_bytes == Path(f"{prefixes[1]}.json").read_bytes(),
             branch + ": 雙冷啟動收據不同")
        first = json.loads(first_bytes)
        control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
        for report, is_control in ((first, False), (control, True)):
            need(report["version"] == "goal112-game-options-source-v2" and
                 report["control"] is is_control and report["nation"] == "england" and
                 report["next_enter"] is True and
                 report["after_b"] == report["after_follow"] == "enter" and
                 report["follow_until"] == 1_400_000_000 and
                 report["input_sha256"] == INPUT_SHA and
                 report["game_inputs_sha256"] == fixture_sha and
                 report["input_hashes"]["MENU.TXT"] == MENU_SHA and
                 len(report["opened"]) == 94,
                 branch + ": 原版、探針或玩家路徑不符")
        need(not control["print_reads"] and not control["writers"] and
             not control["option_source_reads"], branch + ": 控制仍有監看")
        for field in ("route", "sources", "transfers", "samples", "opened",
                      "key_events", "game_inputs"):
            need(first[field] == control[field],
                 branch + ": 監看擾動原版狀態：" + field)
        need(first["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA and
             first["samples"]["1300m"]["canvas_sha256"] == CANVAS_BEFORE,
             branch + ": 選項視窗起點不符")
        scenes[branch] = {}
        for label in LABELS:
            sample = first["samples"][label]
            need(sample["step"] == int(label[:-1]) * 1_000_000,
                 branch + "/" + label + ": 步數不符")
            if label in ("1325m", "1350m", "1375m", "1400m"):
                indexed, canvas = (MID_SCENES if label in ("1325m", "1350m")
                                   else FINAL_SCENES)[branch]
                need(sample["indexed_sha256"] == indexed and
                     sample["canvas_sha256"] == canvas,
                     branch + "/" + label + ": 原版畫面指紋不符")
            if label in PALETTES:
                need(sample["palette_sha256"] == PALETTES[label],
                     branch + "/" + label + ": 色盤相位不符")
            for prefix in prefixes:
                actual = raw(prefix, label, sample)
                if prefix == prefixes[0]:
                    scenes[branch][label] = actual
        receipts[branch] = sha(first_bytes)

    base = scenes["baseline"]
    for branch in ("fourth", "seventh"):
        scene = scenes[branch]
        need(scene["1300m"] == base["1300m"], branch + ": 點擊前畫面不相同")
        need(scene["1375m"]["pal"] == base["1375m"]["pal"],
             branch + ": 同時點色盤不同")
        need(scene["1375m"]["idx"] == scene["1400m"]["idx"] and
             scene["1375m"]["canvas"] == scene["1400m"]["canvas"],
             branch + ": 終點畫面未穩定")
        need(base["1375m"]["idx"] == base["1400m"]["idx"] and
             base["1375m"]["canvas"] == base["1400m"]["canvas"],
             "基線終點畫面未穩定")
        mid = changes(base["1325m"]["canvas"], scene["1325m"]["canvas"])
        total, first_count, target_count, target_lo, target_hi = MID_DIFF_COUNTS[branch]
        need(len(mid) == total and
             sum(59 <= y < 71 for _, y, _, _ in mid) == first_count and
             sum(target_lo <= y < target_hi for _, y, _, _ in mid) == target_count,
             branch + ": 暫態差分越出第一列及被點列")

    old_prefix = old_reports / "tutorial-then-first-row-explore"
    old_bytes = Path(f"{old_prefix}.json").read_bytes()
    need(sha(old_bytes) == OLD_LAST, "既有末列收據版本不符")
    old = json.loads(old_bytes)
    old_frame = raw(old_prefix, "1375m", old["samples"]["1375m"])
    old_baseline = old_reports / "first-row-only-explore"
    old_base_bytes = Path(f"{old_baseline}.json").read_bytes()
    need(sha(old_base_bytes) == OLD_BASE, "既有第一列收據版本不符")
    old_baseline_report = json.loads(old_base_bytes)
    old_base_frame = raw(old_baseline, "1375m",
                         old_baseline_report["samples"]["1375m"])
    last_delta = changes(old_base_frame["idx"], old_frame["idx"])
    need(last_delta == [(73, 148, 47, 149), (74, 148, 47, 149),
                        (73, 149, 47, 149), (74, 149, 47, 149)],
         "既有末列同焦點四點收據不符")

    result = {"result": "PASS", "receipt_sha256": receipts,
              "old_last_receipt_sha256": sha(old_bytes), "differences": {}}
    for branch in ("fourth", "seventh"):
        scene = scenes[branch]["1375m"]
        delta = changes(base["1375m"]["canvas"], scene["canvas"])
        idx_delta = changes(base["1375m"]["idx"], scene["idx"])
        need(delta == idx_delta == EXPECTED_DELTA[branch],
             branch + ": 同焦點差異不只在原版核取圖示四點")
        result["differences"][branch] = {"canvas": delta, "indexed": idx_delta}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--old-reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures,
                       args.reports, args.old_reports)
    except (OSError, KeyError, IndexError, TypeError, ValueError) as exc:
        parser.exit(1, f"FAIL：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
