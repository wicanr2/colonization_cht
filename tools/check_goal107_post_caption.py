#!/usr/bin/env python3
"""獨立核對英格蘭開場字幕的鍵盤相位與四張實際畫面。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA


VERSION = "goal107-post-caption-audit-v1"
RAW = (("idx", "indexed_sha256", 64000),
       ("canvas", "canvas_sha256", 64000),
       ("pal", "palette_sha256", 768))
PHASES = (
    ("90m", "195m", "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"),
    ("200m", "300m", "69859c61c490112c333982957339c23f09df22f2e2918ca881c44d8911dc54c3"),
    ("310m", "420m", "7570358e60c4302624ae02dd5aa9683481fc94ce03e45a00b2f0cd566ff87d94"),
    ("430m", "500m", "b83918fce65d04268703fcfa49c8d5ee4474d9b21e5295dffcc716b01597ed14"),
)
PRINT_SHA = (
    (88_689_021, 88_754_524, 0x2A560, 61,
     "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6"),
    (199_163_156, 199_222_763, 0x2A534, 55,
     "0cfc5ab07ea787de0d84826366302ef1810044e8e34094a67b557daeda9fc937"),
    (307_692_550, 307_731_762, 0x2A534, 37,
     "bbbbdd6e1a3539314ea015d7764af6ed6451f5a4534c169bba1f882ce560d767"),
    (427_644_076, 427_695_982, 0x2A534, 48,
     "c6e372958c2d98a8b53e59d58dac57d7de1eeaab01e145b71c40b9fcf6e373d5"),
)
MARKERS = ((0x153B0, b"@BUILD1", 88_646_378),
           (0x1540F, b"@BUILD2", 199_136_263),
           (0x15466, b"@BUILD3", 307_664_957),
           (0x154AF, b"@BUILD4", 427_611_302))
LATE_PRINT_SHA = (
    (536_921_911, 536_948_638, 0x2A534, 25,
     "ee8b6569c2bba4b57ce2133fd1f0ac9fe52f62db4f5621ce73fa40898f1a78d5"),
    (645_341_112, 645_366_503, 0x2A560, 24,
     "b8cb47fdb1c13aa34a0fce30e333a1232d7991ded6a9daedd8b210cf24cc27c2"),
    (753_776_679, 753_839_172, 0x2A560, 59,
     "53f1e7991791074f9e5a1f54f9a40abc9b4b1957ff168e01d502f2f52b21eda6"),
    (862_217_356, 862_259_926, 0x2A560, 40,
     "0d3ec9226fae1b8b33356f299e2726dc109db51904c5409d1c71b7a3360abf13"),
    (970_656_140, 970_708_177, 0x2A560, 51,
     "65e7fb3ace0f3a3b37f53d6410ee6de05bacab86a2ead7e37e81608fd4bbca5a"),
    (1_079_093_013, 1_079_105_807, 0x2A560, 12,
     "cff475dbcfaf09ea9edf40efa8a40350da7eba8e0f0f0983175eef16e479480e"),
)
LATE_MARKERS = ((0x15506, b"@BUILD5", 536_888_023),
                (0x15541, b"@BUILD6", 645_303_859),
                (0x1557B, b"@BUILD7", 753_733_249),
                (0x155D9, b"@BUILD8", 862_170_153),
                (0x15623, b"@BUILD9", 970_635_177),
                (0x15678, b"@BUILD10", 1_079_071_281))
LATE_SCREENS = (
    ("550m", "d681e6bf78f2ca7c9cbd91769eaac3bc2cea7951744ecd6bbf7051275c486c43"),
    ("650m", "9479b3399a2324a2615ed3a362ced7fe156eefaea90facefcfd309028c6a62a5"),
    ("775m", "977f89f504dc72c577e3bdba7fabc62fc4317cc8c1593e690abf50dfaf9ba35a"),
    ("875m", "607e5ed7cee5b0e1d7b3f635e52af4b32ccc6d438f559db8b76848293482ef62"),
    ("975m", "3ed89dc0c35960d1d94181716448bd39bf94cae6b6fe371c53123c7ff52097b3"),
    ("1100m", "755b912dd898a7c73cc75938e648ac8d7e0e7a9ab6774f06c4d088915d65deec"),
    ("1200m", "6b573d93de2513333a5889bc8e04ff2a81d634b8098482fe4327d6360d1cbb16"),
    ("1225m", "72c604a37b42fb61b41f1969fdad1f2a5031228458d09548e70e5d968b81f247"),
    ("1275m", "8b323b239995fbe1dc381bf263dcb6d0113be17b3753925b8c0a4375d8dc9e73"),
    ("1325m", "72c604a37b42fb61b41f1969fdad1f2a5031228458d09548e70e5d968b81f247"),
    ("1350m", "72c604a37b42fb61b41f1969fdad1f2a5031228458d09548e70e5d968b81f247"),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw_sample(prefix, label, sample):
    need(sample["step"] == int(label[:-1]) * 1_000_000,
         f"{prefix.name}/{label}: 指令數不符")
    for suffix, field, length in RAW:
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == length and sha(data) == sample[field],
             f"{prefix.name}/{label}: 原始 {suffix} 不符")


def print_bursts(report, expected=PRINT_SHA, end=None):
    events = [event for event in report["print_reads"]
              if event["step"] >= 85_000_000 and
              (end is None or event["step"] < end) and
              event["cs_ip"] == "0D21:00C6"]
    groups = []
    for event in events:
        if not groups or event["step"] - groups[-1][-1]["step"] > 1_000_000:
            groups.append([])
        groups[-1].append(event)
    need(len(groups) == len(expected), "實際字幕印字段數不符")
    for group, (first, last, linear, length, digest) in zip(groups, expected):
        need(group[0]["step"] == first and group[-1]["step"] == last and
             len(group) == length * 2, "實際印字步數或長度不符")
        need(all(event["linear"] == linear + i % 2 and
                 (i % 2 == 0 or event["value"] == 0)
                 for i, event in enumerate(group)), "印字 RAM 位址或交錯零位不符")
        need(sha(bytes(event["value"] for event in group[::2])) == digest,
             "實際印字內容雜湊不符")


def check(game, inputs, reports):
    if not inputs.is_file() or not all((game / name).is_file() for name in FILE_SHA):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, digest in FILE_SHA.items():
        need(sha((game / name).read_bytes()) == digest, f"原版版本不符：{name}")
    need(sha(inputs.read_bytes()) == INPUT_SHA, "玩家輸入版本不符")
    original = (game / "GAME.TXT").read_bytes()
    for offset, marker, _ in MARKERS:
        need(original[offset:offset + len(marker)] == marker,
             f"原版標記位移不符：{offset:#x}")
    prefixes = (reports / "england-no-extra-500m-a",
                reports / "england-no-extra-500m-b",
                reports / "england-no-extra-500m-control")
    a_bytes, b_bytes = (Path(f"{prefix}.json").read_bytes() for prefix in prefixes[:2])
    need(a_bytes == b_bytes, "500M 兩次冷啟動收據不同")
    observed = json.loads(a_bytes)
    control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
    need(observed["version"] == control["version"] == VERSION and
         observed["control"] is False and control["control"] is True and
         observed["nation"] == control["nation"] == "england" and
         observed["after_b"] == control["after_b"] == "enter" and
         observed["after_follow"] == control["after_follow"] == "enter" and
         observed["follow_until"] == control["follow_until"] == 500_000_000 and
         observed.get("follow_enter_at") == control.get("follow_enter_at") == "" and
         observed["input_sha256"] == control["input_sha256"] == INPUT_SHA and
         observed["input_hashes"] == control["input_hashes"] == FILE_SHA and
         not control["print_reads"] and not control["writers"],
         "500M 版本、路徑或無監看控制不符")
    for field in ("route", "sources", "transfers", "samples", "opened", "key_events"):
        need(observed[field] == control[field], f"500M 觀測器改變原版狀態：{field}")
    labels = sorted(observed["samples"], key=lambda k: observed["samples"][k]["step"])
    need([observed["samples"][label]["step"] for label in labels if
          observed["samples"][label]["step"] >= 90_000_000] ==
         list(range(90_000_000, 500_000_001, 5_000_000)),
         "500M 檢查點不連續")
    for label in labels:
        for prefix in prefixes:
            raw_sample(prefix, label, observed["samples"][label])
    need(observed["key_events"] == [
        {"event": "enqueue-enter", "pending": 1, "step": 85_000_000},
        {"event": "observed", "pending": 0, "step": 85_001_216,
         "segments": [40960, 2920, 7274, 11438], "ip": 1318}],
         "85M Enter 鍵盤消費相位不符")
    need(all(sample["key_pending"] == 0 for label, sample in
             observed["samples"].items() if sample["step"] >= 85_000_000),
         "字幕序列有未消費的鍵")
    for first, last, digest in PHASES:
        for label in (first, last):
            need(observed["samples"][label]["indexed_sha256"] == digest,
                 f"字幕畫面相位不符：{label}")
    screen_order = []
    for label in labels:
        if observed["samples"][label]["step"] < 90_000_000:
            continue
        digest = observed["samples"][label]["indexed_sha256"]
        if not screen_order or digest != screen_order[-1]:
            screen_order.append(digest)
    need(screen_order == [phase[2] for phase in PHASES],
         "90M–500M 畫面不是四張依序字幕")
    print_bursts(observed)
    for offset, marker, step in MARKERS:
        need(any(t["file_offset"] == offset and t["step"] == step and
                 t["match"] is True and t["prefix_sha256"] == sha(marker)
                 for t in observed["transfers"]),
             f"原版標記缺少當次 DOS 讀取：{offset:#x}")
    need(observed["opened"][68:75] == ["LEVN0002.PIK", "GAME.TXT",
          "LEVN0003.PIK", "GAME.TXT", "LEVN0004.PIK", "GAME.TXT", "GAME.TXT"],
         "字幕二至四開檔序列不符")

    extras = (reports / "england-enter-250m-a",
              reports / "england-enter-250m-b",
              reports / "england-enter-250m-control")
    need(Path(f"{extras[0]}.json").read_bytes() == Path(f"{extras[1]}.json").read_bytes(),
         "100M 加送鍵的兩次冷啟動收據不同")
    extra_report = json.loads(Path(f"{extras[0]}.json").read_bytes())
    extra_control = json.loads(Path(f"{extras[2]}.json").read_bytes())
    need(extra_report["version"] == VERSION and
         extra_control["version"] == VERSION and
         extra_report["control"] is False and extra_control["control"] is True and
         extra_report["follow_enter_at"] == extra_control["follow_enter_at"] == "100" and
         extra_report["follow_until"] == extra_control["follow_until"] == 250_000_000 and
         extra_report["key_events"][2]["step"] == 100_000_000 and
         extra_report["key_events"][2]["pending"] == 1 and
         extra_report["key_events"][3]["step"] == 100_898_816 and
         extra_report["key_events"][3]["pending"] == 0 and
         not extra_control["print_reads"] and not extra_control["writers"],
         "100M 加送 Enter 未證實消費")
    for field in ("route", "sources", "transfers", "samples", "opened", "key_events"):
        need(extra_report[field] == extra_control[field],
             f"加送鍵觀測器改變原版狀態：{field}")
    for label, sample in extra_report["samples"].items():
        for prefix in extras:
            raw_sample(prefix, label, sample)
        if sample["step"] < 85_000_000:
            continue
        original_sample = observed["samples"][label]
        need(all(sample[field] == original_sample[field] for _, field, _ in RAW) and
             sample["opened_count"] == original_sample["opened_count"],
             f"加送 Enter 改變已驗可見相位：{label}")

    long_prefixes = (reports / "england-no-extra-1350m-explore",
                     reports / "england-no-extra-1350m-b",
                     reports / "england-no-extra-1350m-control")
    need(Path(f"{long_prefixes[0]}.json").read_bytes() ==
         Path(f"{long_prefixes[1]}.json").read_bytes(),
         "1350M 兩次冷啟動收據不同")
    long_report = json.loads(Path(f"{long_prefixes[0]}.json").read_bytes())
    long_control = json.loads(Path(f"{long_prefixes[2]}.json").read_bytes())
    need(long_report["version"] == long_control["version"] == VERSION and
         long_report["control"] is False and long_control["control"] is True and
         long_report["follow_until"] == long_control["follow_until"] == 1_350_000_000 and
         long_report["key_events"] == observed["key_events"] and
         not long_control["print_reads"] and not long_control["writers"],
         "1350M 版本、鍵盤或無監看控制不符")
    for field in ("route", "sources", "transfers", "samples", "opened", "key_events"):
        need(long_report[field] == long_control[field],
             f"1350M 觀測器改變原版狀態：{field}")
    long_labels = sorted(long_report["samples"],
                         key=lambda k: long_report["samples"][k]["step"])
    need([long_report["samples"][label]["step"] for label in long_labels if
          long_report["samples"][label]["step"] > 500_000_000] ==
         list(range(525_000_000, 1_350_000_001, 25_000_000)),
         "500M 後稀疏檢查點不連續")
    for label in long_labels:
        sample = long_report["samples"][label]
        if sample["step"] <= 500_000_000:
            need(sample == observed["samples"][label],
                 f"1350M 與500M的共同原版狀態不同：{label}")
        for prefix in long_prefixes:
            raw_sample(prefix, label, sample)
    print_bursts(long_report, PRINT_SHA + LATE_PRINT_SHA, 1_180_000_000)
    for offset, marker, step in LATE_MARKERS:
        need(original[offset:offset + len(marker)] == marker and
             any(t["file_offset"] == offset and t["step"] == step and
                 t["match"] is True and t["prefix_sha256"] == sha(marker)
                 for t in long_report["transfers"]),
             f"後段字幕標記缺少當次 DOS 讀取：{offset:#x}")
    for label, digest in LATE_SCREENS:
        need(long_report["samples"][label]["indexed_sha256"] == digest,
             f"字幕或遊戲畫面相位不符：{label}")
    need(long_report["opened"][-5:] == ["PHYS0.SS", "ICONS.SS", "BUILDING.SS",
          "CYCLE.DAT", "MENU.TXT"] and len(long_report["opened"]) == 93 and
         all(long_report["samples"][label]["key_pending"] == 0
             for label, _ in LATE_SCREENS),
         "正常遊戲畫面開檔或鍵盤相位不符")
    return {"result": "PASS", "scope": "英格蘭開場十張字幕至首個海上遊戲畫面；抽樣未見 help",
            "input_sha256": INPUT_SHA, "game_sha256": FILE_SHA["GAME.TXT"],
            "dosgolem_commit": "9dd36726eeaf9c1f3a745aabdcbb84413791d90f",
            "screen_sha256": [phase[2] for phase in PHASES],
            "printed_sha256": [item[4] for item in PRINT_SHA],
            "later_caption_sha256": [item[4] for item in LATE_PRINT_SHA],
            "gameplay_1200m_indexed_sha256": dict(LATE_SCREENS)["1200m"],
            "tutorial1_sampled_visible": False,
            "reports_sha256": {prefix.name: sha(Path(f"{prefix}.json").read_bytes())
                               for prefix in prefixes + extras + long_prefixes},
            "limitation": "只證實固定版本、英格蘭正常路徑至1350M；抽樣畫面未見首則 help，不證明其他操作下不會出現"}


def main(args):
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    receipt = check(args.game, args.inputs, args.reports)
    if receipt["result"] == "SKIP":
        print("SKIP：" + receipt["reason"])
        return 77
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("PASS：" + receipt["scope"])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
