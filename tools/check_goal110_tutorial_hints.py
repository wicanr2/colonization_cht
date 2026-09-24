#!/usr/bin/env python3
"""獨立核對原版教學選項點擊與海上方向鍵的有界收據。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA


VERSION = "goal110-game-input-audit-v1"
MENU_SHA = "5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702"
FIXTURE_SHA = {
    "goal110-game-menu.inputs.json": "52e99e507b32b230159136d57b0cf76845243de23ad111a90d41da7a7b0bb0c2",
    "goal110-game-options.inputs.json": "c4e462678323df8e1915ffcd363f7e7eb83cee4e85e09f618c9206418977e539",
    "goal110-toggle-tutorial.inputs.json": "5ffad69f2e31e8c46cec86b543455331a4da432ce289d150846e4b1b682ff1a8",
    "goal110-first-west.inputs.json": "2a18788ac74b8928d9fde66e463ba89f9a410dbb338c84e2df28e3130ef513ad",
}
BASE_SCREEN = "72c604a37b42fb61b41f1969fdad1f2a5031228458d09548e70e5d968b81f247"
SCREENS = {
    "toggle": {
        "1250m": "9e4573afe00f88158ed538e0cf5cc23d5d6183cb163ae7490ab9dd27168c2fbc",
        "1275m": "7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546",
        "1300m": "7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546",
        "1325m": "d276bc8469d4e4fef9b9d44f2f454dd42424bc4bcc6f5bb74d6cfde820881b24",
        "1350m": "d276bc8469d4e4fef9b9d44f2f454dd42424bc4bcc6f5bb74d6cfde820881b24",
    },
    "first-west": {
        "1250m": "ae0628b2f68d936f7d94188ae9ac6fb45157d3aafbb7518049e6f6616f3582d4",
        "1275m": "ae0628b2f68d936f7d94188ae9ac6fb45157d3aafbb7518049e6f6616f3582d4",
        "1300m": "a850da7cc62518f3f756ff2d35820864be78639c590cf744433f2c62a013c0c2",
    },
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw(prefix, label, sample):
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == size and digest(data) == sample[field],
             f"{prefix.name}/{label}: 原始 {suffix} 不符")


def branch(reports, name, fixture, end, opened_count):
    prefixes = [reports / f"{name}-{suffix}"
                for suffix in ("explore", "replay2", "control")]
    first = Path(f"{prefixes[0]}.json").read_bytes()
    need(first == Path(f"{prefixes[1]}.json").read_bytes(),
         f"{name}: 兩次冷啟動不一致")
    observed = json.loads(first)
    control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
    for report, is_control in ((observed, False), (control, True)):
        need(report["version"] == VERSION and report["control"] is is_control and
             report["nation"] == "england" and report["after_b"] == "enter" and
             report["after_follow"] == "enter" and report["follow_until"] == end and
             report["input_sha256"] == INPUT_SHA and
             report["game_inputs_sha256"] == FIXTURE_SHA[fixture] and
             report["input_hashes"]["MENU.TXT"] == MENU_SHA and
             len(report["opened"]) == opened_count,
             f"{name}: 路徑、版本或固定來源不符")
    need(not control["print_reads"] and not control["writers"],
         f"{name}: 無監看控制仍有記憶體監看")
    for field in ("route", "sources", "transfers", "samples", "opened",
                  "key_events", "game_inputs"):
        need(observed[field] == control[field],
             f"{name}: 監看器改變原版狀態：{field}")
    need(observed["samples"]["1225m"]["indexed_sha256"] == BASE_SCREEN,
         f"{name}: 海上輸入前畫面不符")
    for label, expected in SCREENS[name].items():
        sample = observed["samples"][label]
        expected_opened = 93 if name == "toggle" and label == "1250m" else opened_count
        need(sample["step"] == int(label[:-1]) * 1_000_000 and
             sample["indexed_sha256"] == expected and
             sample["opened_count"] == expected_opened,
             f"{name}/{label}: 畫面或開檔相位不符")
        raw(prefixes[0], label, sample)
    return observed


def check(game, inputs, fixtures, reports):
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(digest((game / name).read_bytes()) == expected,
             f"原版版本不符：{name}")
    need(digest(inputs.read_bytes()) == INPUT_SHA, "正常玩家輸入版本不符")
    for name, expected in FIXTURE_SHA.items():
        need(digest((fixtures / name).read_bytes()) == expected,
             f"本輪事件檔版本不符：{name}")
    menu = (game / "MENU.TXT").read_bytes()
    game_text = (game / "GAME.TXT").read_bytes()
    need(menu[0xC6:0xC6 + 12] == b"Game Options" and
         game_text[0x4A8:0x4A8 + 12] == b"@GAMEOPTIONS" and
         game_text[0x566:0x566 + 15] == b"~Tutorial Hints" and
         game_text[0x1316A:0x1316A + 10] == b"@TUTORIAL1",
         "原版文字標記位移不符")
    toggle = branch(reports, "toggle", "goal110-toggle-tutorial.inputs.json",
                    1_350_000_000, 94)
    west = branch(reports, "first-west", "goal110-first-west.inputs.json",
                  1_300_000_000, 93)
    need(toggle["samples"]["1300m"]["indexed_sha256"] !=
         toggle["samples"]["1325m"]["indexed_sha256"],
         "教學選項點擊後原版畫面未變")
    before = Path(f"{reports / 'toggle-explore'}.1300m.idx").read_bytes()
    after = Path(f"{reports / 'toggle-explore'}.1325m.idx").read_bytes()
    need(any(before[y * 320 + x] != after[y * 320 + x]
             for y in range(145, 153) for x in range(68, 78)),
         "教學提示行核取圖示沒有像素變化")
    events = [event for event in west["key_events"]
              if event["step"] >= 1_226_000_000]
    need(any(event["pending"] == 1 for event in events) and
         any(event["pending"] == 0 for event in events) and
         west["samples"]["1250m"]["key_pending"] == 0 and
         west["samples"]["1250m"]["indexed_sha256"] != BASE_SCREEN,
         "海上方向鍵未證明送達、消費及畫面反應")
    return {"result": "PASS", "scope": "Game Options、Tutorial Hints 點擊反應及海上左方向鍵；未證實教學正文顯示",
            "toggle_receipt_sha256": digest((reports / "toggle-explore.json").read_bytes()),
            "first_west_receipt_sha256": digest((reports / "first-west-explore.json").read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures, args.reports)
    except (OSError, KeyError, IndexError, TypeError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
