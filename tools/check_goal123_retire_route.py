#!/usr/bin/env python3
"""獨立核對 Retire 確認框的 No／Yes／名人堂／DOS 結束玩家路徑。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA


EXTRA_FILES = {
    "WOODPANL.PIK": "0858856ad5b5dd0b6ab8e7a8f815fa602a9cf0237d8d323cd2b5ca141b32bc69",
    "CYCLE.DAT": "97d2506bcbab011ebaedc397fb06ed8bde8030160a1a129ddae897db05f72a2e",
}
BRANCHES = {
    "prompt": {"fixture": "goal111-retire-menu.inputs.json",
               "fixture_sha": "a2638a3de1d9b4ecb6499efee6e8a07722c9c0e6b4dce6d0630094310ad464f8",
               "first": ("goal111-help", "retire-menu-explore"),
               "second": ("goal123-retire", "no-click-b"),
               "control": ("goal123-retire", "no-click-control"),
               "sha": "182e815897b6f6f1ff2dd4f6bcad3ee7dcf0394dc3a59bdb99b5b400ef7f952a",
               "version": "goal110-game-input-audit-v1", "until": 1_350_000_000,
               "samples": 132, "opened": 94},
    "yes": {"fixture": "goal123-retire-yes.inputs.json",
            "fixture_sha": "e6f4de6576df705b18f7a2779c4c8780799d8833cec27d560acf548999738c69",
            "first": ("goal123-retire", "yes-explore"),
            "second": ("goal123-retire", "yes-b"),
            "control": ("goal123-retire", "yes-control"),
            "sha": "483221c48209261e13d616dc6466cc4e2bdb567ecdefddee227723520e1118d6",
            "version": "goal110-game-input-audit-v1", "until": 1_350_000_000,
            "samples": 135, "opened": 95},
    "no": {"fixture": "goal123-retire-no.inputs.json",
           "fixture_sha": "0a5ca7d18dd01ac7630fe74b81bcafb724849b2d4040fd7d80e5a51717c61d27",
           "first": ("goal123-retire", "no-a"),
           "second": ("goal123-retire", "no-b"),
           "control": ("goal123-retire", "no-control"),
           "sha": "5de7e959afd1a3ff6b953935610c572414faa4d14b93a1d3bdf99e4e183f0673",
           "version": "goal110-game-input-audit-v1", "until": 1_350_000_000,
           "samples": 135, "opened": 94},
    "hall": {"fixture": "goal123-retire-hall-enter.inputs.json",
             "fixture_sha": "b17af66d66176cf30d0fe878bff8719346d154e811bcfaa16f285a97b120c440",
             "first": ("goal123-retire", "hall-a"),
             "second": ("goal123-retire", "hall-b"),
             "control": ("goal123-retire", "hall-control"),
             "sha": "902d557aaf7f86d4fb913d4891e4c7e584f10963e8b0217e2afc8401bde20efa",
             "version": "goal123-retire-terminal-v1", "until": 1_500_000_000,
             "samples": 142, "opened": 96},
}
SCENES = {
    ("prompt", "1275m"): ("bef37e89eadc25fd4dd98e218f783b17672f6089c3e2dc2a153712c70b900060",
                          "e079bbffd2a759be78cd9248dfb11507330f7012760428aabdad971103e961d8", 94),
    ("yes", "1350m"): ("0ba06b2483b8fd5d7a6502a59b6db2aef28a6e61797782d31fe12565cfabdd49",
                        "c122e9037ef9d319111a37b17253cd40621fded333856cad04b859bc7f0844dc", 95),
    ("no", "1350m"): ("71ecf42fd7261ea39f123fc9ff09cbff245d725cf54bd25e1a6de6ef5c63765d",
                       "70bba2a713389fb94001d13685a99d044b4cc54eb9ccaa313ea4bf965bb9068c", 94),
    ("hall", "1375m"): ("d52c238f56aa62eeed9c1e82b156eff381a22b3e3ccaf8efb51dca4fc03ae63a",
                         "833014b1946225f5d6a1ac2d62b330dbcb9058d5ec48f658b29918312f45a75e", 96),
    ("hall", "terminal"): ("833014b1946225f5d6a1ac2d62b330dbcb9058d5ec48f658b29918312f45a75e",
                          "833014b1946225f5d6a1ac2d62b330dbcb9058d5ec48f658b29918312f45a75e", 96),
}
COMPARE = ("route", "sources", "transfers", "samples", "opened", "key_events", "game_inputs")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prefix(root, pair):
    return root / pair[0] / pair[1]


def read_frame(path, label, sample):
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{path}.{label}.{suffix}").read_bytes()
        need(len(data) == size and sha(data) == sample[field],
             f"{path.name}/{label}: 原版 {suffix} 實檔與收據不同")


def source_text(report, start):
    return bytes(event["value"] for event in report["print_reads"]
                 if event["step"] >= start and event["value"])


def check(game, inputs, fixtures, root, output=None):
    originals = {**FILE_SHA, "MENU.TXT": MENU_SHA, **EXTRA_FILES}
    if not inputs.is_file() or not all((game / name).is_file() for name in originals):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    if output is not None:
        need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
             "收據輸出目錄不存在或擁有者不符")
    for name, expected in originals.items():
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "正常玩家開局輸入版本不符")
    receipts, reports = {}, {}
    for branch, spec in BRANCHES.items():
        fixture = fixtures / spec["fixture"]
        need(sha(fixture.read_bytes()) == spec["fixture_sha"],
             branch + ": 原版玩家事件版本不符")
        raw_a = Path(f"{prefix(root, spec['first'])}.json").read_bytes()
        raw_b = Path(f"{prefix(root, spec['second'])}.json").read_bytes()
        need(raw_a == raw_b and sha(raw_a) == spec["sha"],
             branch + ": 兩次冷啟動或固定收據 SHA 不符")
        observed = json.loads(raw_a)
        control = json.loads(Path(f"{prefix(root, spec['control'])}.json").read_bytes())
        reports[branch] = observed
        for report, is_control in ((observed, False), (control, True)):
            need(report["version"] == spec["version"] and report["control"] is is_control and
                 report["nation"] == "england" and report["next_enter"] is True and
                 report["after_b"] == report["after_follow"] == "enter" and
                 report["follow_until"] == spec["until"] and
                 report["input_sha256"] == INPUT_SHA and
                 report["game_inputs_sha256"] == spec["fixture_sha"] and
                 report["input_hashes"]["MENU.TXT"] == MENU_SHA and
                 len(report["samples"]) == spec["samples"] and
                 len(report["opened"]) == spec["opened"],
                 branch + ": 探針、原版版本或正常玩家路徑不符")
            if branch == "hall":
                terminal = report["game_terminal"]
                need(terminal == {"observed": True, "step": 1_451_193_903,
                     "dos_exited": True, "cpu_halted": True,
                     "events_delivered": 11, "events_total": 11},
                     branch + ": 原版終止不是預期 DOS 正常結束")
            need(report["game_inputs"][-3 if branch in ("no", "yes") else -1]["step"] ==
                 (1_276_000_000 if branch in ("no", "yes") else
                  1_451_000_000 if branch == "hall" else 1_253_000_000),
                 branch + ": 玩家事件順序不符")
        need(not control["print_reads"] and not control["writers"],
             branch + ": 無監看控制仍安裝印字或畫布觀測")
        for field in COMPARE:
            need(observed[field] == control[field],
                 branch + ": 監看擾動原版狀態：" + field)
        if branch == "hall":
            need(observed["game_terminal"] == control["game_terminal"],
                 "名人堂終止與無監看控制不同")
        for label, sample in observed["samples"].items():
            need(sample["opened_count"] <= spec["opened"] and sample["step"] <=
                 (1_451_193_903 if branch == "hall" else spec["until"]),
                 branch + "/" + label + ": 取樣步數或開檔數越界")
            for pair in (spec["first"], spec["second"], spec["control"]):
                read_frame(prefix(root, pair), label, sample)
        receipts[branch] = sha(raw_a)

    prompt = reports["prompt"]["samples"]["1275m"]
    for branch in ("yes", "no", "hall"):
        need(reports[branch]["samples"]["1275m"] == prompt,
             branch + ": 點確認框前不是同一原版狀態")
    need(reports["yes"]["samples"]["1350m"] ==
         reports["hall"]["samples"]["1350m"],
         "名人堂 Enter 前與 Yes 評分不是同一原版狀態")
    for (branch, label), (indexed, canvas, opened) in SCENES.items():
        sample = reports[branch]["samples"][label]
        need(sample["indexed_sha256"] == indexed and sample["canvas_sha256"] == canvas and
             sample["opened_count"] == opened and
             sample["step"] == (1_451_193_903 if label == "terminal" else
                                int(label[:-1]) * 1_000_000),
             branch + "/" + label + ": 固定原版畫面不符")
    need(source_text(reports["prompt"], 1_252_000_000).find(
         b"Do you really  want to quit?YesNo") >= 0,
         "原版確認框沒有實際印字")
    need(b"COLONIZATION SCOREE" in source_text(reports["yes"], 1_278_000_000) and
         b"Spring 1492" in source_text(reports["no"], 1_278_000_000) and
         b"COLONIZATION HALL OF FAME" in source_text(reports["hall"], 1_351_000_000),
         "Yes／No／名人堂實際印字不同於固定玩家畫面")
    for branch in reports:
        need(b"carrying a pioneer" not in source_text(reports[branch], 1_275_000_000),
             branch + ": 觀測到首則 help，必須另建顯示收據")
    result = {"result": "PASS", "scope": "固定英格蘭正常玩家路徑；Retire 不提供同次新局入口",
              "receipt_sha256": receipts, "prompt_ink": {"yes": [126, 102, 140, 109],
                                                   "no": [126, 114, 135, 121]},
              "terminal": reports["hall"]["game_terminal"],
              "final_scenes": {branch: reports[branch]["samples"]["1350m"]["indexed_sha256"]
                               for branch in ("prompt", "yes", "no")}}
    if output is not None:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures, args.reports_root, args.output)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        parser.exit(1, f"FAIL：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
