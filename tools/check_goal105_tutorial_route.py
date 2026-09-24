#!/usr/bin/env python3
"""獨立核對首則教學預讀與 @BUILD1 開場字幕的正常玩家收據。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA


CAPTION = b"In the Year of Our Lord One Thousand Four Hundred Ninety-Two,"
CAPTION_SHA = "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6"
FOLLOW_SHA = "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"
LABELS = ("85m", "90m", "95m", "100m")
RAW = (("idx", "indexed_sha256", 64000),
       ("canvas", "canvas_sha256", 64000),
       ("pal", "palette_sha256", 768))
SOURCES = ((0x1316A, b"@TUTORIAL1", 0x13000, 0x2B16C),
           (0x13190, b"Our {%STRING0}", 0x13000, 0x2B192),
           (0x153B0, b"@BUILD1", 0x15200, 0x2B1B2),
           (0x153CE, CAPTION[:0x15400 - 0x153CE], 0x15200, 0x2B1D0),
           (0x15400, CAPTION[0x15400 - 0x153CE:], 0x15400, 0x2B002))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def check_raw(prefix, report):
    for label in LABELS:
        sample = report["samples"][label]
        need(sample["step"] == int(label[:-1]) * 1_000_000,
             f"{prefix.name}/{label}: 觀測步數不符")
        for suffix, field, length in RAW:
            value = Path(f"{prefix}.{label}.{suffix}").read_bytes()
            need(len(value) == length and sha(value) == sample[field],
                 f"{prefix.name}/{label}: 原始 {suffix} 與 JSON 不符")


def printed_after_85m(report):
    events = [event for event in report["print_reads"]
              if event["step"] >= 85_000_000 and event["cs_ip"] == "0D21:00C6"]
    raw = bytes(event["value"] for event in events)
    need(len(raw) == 2 * len(CAPTION) and
         all(raw[i + 1] == 0 for i in range(0, len(raw), 2)) and
         all(event["linear"] == (0x2A560 if i % 2 == 0 else 0x2A561)
             for i, event in enumerate(events)),
         "開場字幕實模式逐字讀取或 RAM 位址不符")
    return raw[::2]


def check(game, inputs, reports, baseline):
    if not inputs.is_file() or not all((game / name).is_file() for name in FILE_SHA):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in FILE_SHA.items():
        need(sha((game / name).read_bytes()) == expected,
             f"原版檔案版本不符：{name}")
    need(sha(inputs.read_bytes()) == INPUT_SHA, "固定玩家輸入版本不符")
    game_bytes = (game / "GAME.TXT").read_bytes()
    need(game_bytes[0x153CC:0x153CC + 2 + len(CAPTION)] == b"^^" + CAPTION and
         sha(game_bytes[0x153CE:0x153CE + len(CAPTION)]) == CAPTION_SHA,
         "@BUILD1 原始字幕不符")
    for offset, raw, _, _ in SOURCES:
        need(game_bytes[offset:offset + len(raw)] == raw,
             f"GAME.TXT:{offset:#x} 原始來源不符")
    old = load(baseline / "england-enter-a.json")
    branches = {}
    for action in ("wait", "enter", "esc"):
        prefix = reports / f"england-{action}-v4"
        a_bytes = Path(f"{prefix}-a.json").read_bytes()
        need(a_bytes == Path(f"{prefix}-b.json").read_bytes(),
             f"{action}: 兩次獨立重播 JSON 不同")
        observed = json.loads(a_bytes)
        control = load(Path(f"{prefix}-control.json"))
        need(observed["version"] == control["version"] == "goal105-tutorial-route-v4" and
             observed["nation"] == control["nation"] == "england" and
             observed["after_b"] == control["after_b"] == "enter" and
             observed["after_follow"] == control["after_follow"] == action and
             observed["next_enter"] is control["next_enter"] is True and
             observed["control"] is False and control["control"] is True and
             observed["input_sha256"] == control["input_sha256"] == INPUT_SHA and
             observed["input_hashes"] == control["input_hashes"] == FILE_SHA and
             all(observed[key] == control[key]
                 for key in ("route", "sources", "transfers", "samples", "opened")) and
             not control["print_reads"] and not control["writers"],
             f"{action}: 觀測／無觀測控制的 CPU、RAM、時間或流程不同")
        need(observed["samples"]["85m"] == old["samples"]["85m"] and
             observed["opened"][:len(old["opened"])] == old["opened"],
             f"{action}: 85M 已驗共同起點不符")
        for suffix in ("a", "b", "control"):
            check_raw(Path(f"{prefix}-{suffix}"),
                      control if suffix == "control" else observed)
        for label in LABELS:
            for suffix, _, _ in RAW:
                a_raw = Path(f"{prefix}-a.{label}.{suffix}").read_bytes()
                need(a_raw == Path(f"{prefix}-b.{label}.{suffix}").read_bytes() ==
                     Path(f"{prefix}-control.{label}.{suffix}").read_bytes(),
                     f"{action}/{label}: 雙重播或控制的原始 {suffix} 不同")
                if label == "85m":
                    need(a_raw == (baseline / f"england-enter-a.85m.{suffix}").read_bytes(),
                         f"{action}: 85M 原始共同起點不同")
        branches[action] = observed
    waiting = branches["wait"]
    need(not any(key.startswith("after-follow/") for key in waiting["writers"]) and
         not any(item["step"] >= 85_000_000 for item in waiting["print_reads"]) and
         all(waiting["samples"][label][field] == waiting["samples"]["85m"][field]
             for label in ("90m", "95m", "100m") for _, field, _ in RAW) and
         all(waiting["samples"][label]["opened_count"] == 60 for label in LABELS),
         "無鍵對照不應自行離開後續頁")
    for action in ("enter", "esc"):
        record = branches[action]
        need(record["opened"][60:65] ==
             ["LEVN0001.PIK", "GAME.TXT", "PHYS0.SS", "ICONS.SS", "BUILDING.SS"] and
             all(record["samples"][label]["indexed_sha256"] == FOLLOW_SHA
                 for label in ("90m", "95m", "100m")) and
             all(record["samples"][label][field] == record["samples"]["90m"][field]
                 for label in ("95m", "100m") for _, field, _ in RAW),
             f"{action}: 字幕頁可見畫面或開檔不符")
        transfers = [item for item in record["transfers"]
                     if item["file_offset"] >= 0x1316A]
        need(len(transfers) == len(SOURCES), f"{action}: 新來源的 DOS 讀取數不符")
        for transfer, (offset, raw, read_pos, linear) in zip(transfers, SOURCES):
            need(transfer["file_offset"] == offset and transfer["read_pos"] == read_pos and
                 transfer["candidate_linear"] == linear and transfer["match"] is True and
                 transfer["prefix_sha256"] == sha(raw) and transfer["name"].upper() == "GAME.TXT" and
                 85_000_000 < transfer["step"] < 90_000_000,
                 f"{action}: GAME.TXT:{offset:#x} 至 RAM 的來源邊不符")
        need(transfers[1]["step"] < transfers[2]["step"] <= transfers[3]["step"] <
             transfers[4]["step"],
             f"{action}: 教學預讀與字幕讀入順序不符")
        need(printed_after_85m(record) == CAPTION,
             f"{action}: 當次實際印字不是 @BUILD1 字幕")
        writer = record["writers"].get("after-follow/0D21:012C", {})
        need(writer.get("count") == 1040 and writer.get("bbox") == [16, 30, 303, 39] and
             85_000_000 < writer["first_step"] < writer["last_step"] < 90_000_000,
             f"{action}: 原版字幕畫布改色不符")
    need(all(branches["enter"]["samples"]["100m"][field] ==
             branches["esc"]["samples"]["100m"][field] for _, field, _ in RAW) and
         branches["enter"]["samples"]["100m"]["memory_sha256"] !=
         branches["esc"]["samples"]["100m"]["memory_sha256"],
         "Enter／ESC 可見畫面或內部差異不符")
    return {"result": "PASS", "scope": "英格蘭後續頁至 @BUILD1 字幕；@TUTORIAL1 僅預讀",
            "game_sha256": FILE_SHA["GAME.TXT"], "input_sha256": INPUT_SHA,
            "caption_file_offset": "GAME.TXT:0x153CE", "caption_sha256": CAPTION_SHA,
            "caption_indexed_sha256": FOLLOW_SHA,
            "tutorial_marker_file_offset": "GAME.TXT:0x1316A",
            "tutorial_visible": False,
            "report_sha256": {action: sha((reports / f"england-{action}-v4-a.json").read_bytes())
                              for action in ("wait", "enter", "esc")},
            "limitations": "教學文字只證實 DOS 預讀，未有畫布印字或中文覆蓋；Enter／ESC 內部 RAM 不同"}


def main(args):
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    receipt = check(args.game, args.inputs, args.reports, args.baseline)
    if receipt["result"] == "SKIP":
        print("SKIP：" + receipt["reason"])
        return 77
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(receipt["result"] + "：" + receipt["scope"])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
