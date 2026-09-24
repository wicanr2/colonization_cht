#!/usr/bin/env python3
"""獨立核對教學提示的同焦點圖示狀態與有界玩家操作。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal110_tutorial_hints import MENU_SHA


FIXTURE_SHA = {
    "hover-away": "a63a789b575dca90bfd1de86395d4cbc40e89be7a4ca73e8f257ea40a8364bff",
    "click-away": "c326c3da93f4bcefe958be00c7aa5f19e7a0f978a97223f8af430ac91f8e8a5c",
    "icon-click-away": "7bc9bbe074bcb76faec0f678357a8e5c1d97ed3bf5b25760ee1ab53762b6c0da",
    "first-row-only": "86896d9d5444cd00fe9fd82ac35a9b33e944620d0dcb4e8f638c885c04d89a1c",
    "tutorial-then-first-row": "49c1e006724bb8b51a1b0dff6786e696f01dc5b9b1491c282efb9965b13a9d93",
    "untouched-esc-left": "4f12699fdfd2ab7faf66bef580892416c5e1ea6b49fda1f71bdfa9dfc7ae0278",
    "toggled-esc-left": "4855950305faf98ce730021bda2a35c384734bd2708b1afe78a3985f05739156",
    "orders-menu": "adbf3d098903c0e1338c1954f2fbaf3671d009c1b76988199e9316879ab9529b",
    "untouched-esc-space": "b32dd7d93efef2c4878eb03618353e8ad6922f0ba638709e98b8bf1102de2853",
    "toggled-esc-space": "e7cd7cef03a3f2e71fef86870504b0152424f86c51afea29f01694cf28d10396",
    "retire-menu": "a2638a3de1d9b4ecb6499efee6e8a07722c9c0e6b4dce6d0630094310ad464f8",
}
BEFORE_OPTION = "7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546"
FINAL_SCENE = {
    "first-row-only": "7b6bf011f389933ce5a09553f10a1f069a6d3bf5f26fe7978bf130897e80f450",
    "tutorial-then-first-row": "4836e52fc8154ee45a41b9afc49f496f9d9563b86100c87abb009c49b5d15f4e",
}
SPACE_SCENE = {
    "1375m": "e556a23e39370303c2d8b4a86cbb8d5e901b1a4f2cc36b9f9aebe53fe58ed9b0",
    "1425m": "2ddf468d3c8bffc3f119ae8b8fb357c21938ed8720c26c2d600069e08751cad3",
    "1500m": "8b92a07b51fd195cca7ee212a5ca11bfd55673582a17bd9a5eba842002501f14",
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(prefix, label, sample):
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == size and sha(data) == sample[field],
             f"{prefix.name}/{label}: 原始 {suffix} 不符")


def matched_focus_branch(reports, name):
    prefixes = [reports / f"{name}-{suffix}"
                for suffix in ("explore", "replay2", "control")]
    observed_bytes = Path(f"{prefixes[0]}.json").read_bytes()
    need(observed_bytes == Path(f"{prefixes[1]}.json").read_bytes(),
         f"{name}: 雙重播不一致")
    observed = json.loads(observed_bytes)
    control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
    for report, is_control in ((observed, False), (control, True)):
        need(report["version"] == "goal110-game-input-audit-v1" and
             report["control"] is is_control and report["nation"] == "england" and
             report["after_b"] == report["after_follow"] == "enter" and
             report["follow_until"] == 1_400_000_000 and
             report["input_sha256"] == INPUT_SHA and
             report["game_inputs_sha256"] == FIXTURE_SHA[name] and
             report["input_hashes"]["MENU.TXT"] == MENU_SHA and
             len(report["opened"]) == 94,
             f"{name}: 路徑、來源或探針版本不符")
    need(not control["print_reads"] and not control["writers"],
         f"{name}: 無監看控制仍有記憶體監看")
    for field in ("route", "sources", "transfers", "samples", "opened",
                  "key_events", "game_inputs"):
        need(observed[field] == control[field],
             f"{name}: 監看擾動原版狀態：{field}")
    need(observed["samples"]["1300m"]["indexed_sha256"] == BEFORE_OPTION,
         f"{name}: 同狀態起點不符")
    for label in ("1300m", "1375m", "1400m"):
        sample = observed["samples"][label]
        need(sample["step"] == int(label[:-1]) * 1_000_000 and
             sample["indexed_sha256"] ==
             (BEFORE_OPTION if label == "1300m" else FINAL_SCENE[name]),
             f"{name}/{label}: 原版畫面不符")
        raw(prefixes[0], label, sample)
    return observed, sha(observed_bytes)


def exploratory_space(reports, name):
    prefix = reports / f"{name}-explore"
    report = json.loads(Path(f"{prefix}.json").read_bytes())
    need(report["version"] == "goal111-game-input-audit-v2" and
         report["control"] is False and report["follow_until"] == 1_500_000_000 and
         report["game_inputs_sha256"] == FIXTURE_SHA[name] and
         report["input_sha256"] == INPUT_SHA,
         f"{name}: Space 探索路徑不符")
    for label, expected in SPACE_SCENE.items():
        sample = report["samples"][label]
        need(sample["indexed_sha256"] == expected and sample["key_pending"] == 0,
             f"{name}/{label}: 原版取樣畫面或鍵盤不符")
        raw(prefix, label, sample)
    after = [event for event in report["key_events"]
             if event["step"] >= 1_401_000_000]
    need(any(event["pending"] == 1 for event in after) and
         any(event["pending"] == 0 for event in after),
         f"{name}: Space 沒有入列並被原版取走")
    printed = bytes(event["value"] for event in report["print_reads"]
                    if event["cs_ip"] == "0D21:00C6" and
                    event["step"] >= 1_225_000_000 and event["value"])
    need(b"carrying a pioneer" not in printed,
         f"{name}: 觀測到首則正文，須改做輸出來源閉合")


def check(game, inputs, fixtures, reports):
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, digest in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == digest,
             f"原版版本不符：{name}")
    need(sha(inputs.read_bytes()) == INPUT_SHA, "正常玩家輸入版本不符")
    for name, digest in FIXTURE_SHA.items():
        need(sha((fixtures / f"goal111-{name}.inputs.json").read_bytes()) == digest,
             f"玩家事件檔版本不符：{name}")
    menu = (game / "MENU.TXT").read_bytes()
    text = (game / "GAME.TXT").read_bytes()
    need(menu[902:911] == b"No Orders" and
         text[0x1316A:0x1316A + 10] == b"@TUTORIAL1",
         "原版檔案位移不符")
    no_click, no_click_sha = matched_focus_branch(reports, "first-row-only")
    clicked, clicked_sha = matched_focus_branch(reports, "tutorial-then-first-row")
    need(no_click["samples"]["1300m"] == clicked["samples"]["1300m"],
         "教學點擊前狀態不同")
    before = (reports / "first-row-only-explore.1375m.idx").read_bytes()
    after = (reports / "tutorial-then-first-row-explore.1375m.idx").read_bytes()
    changes = [(i % 320, i // 320, old, new)
               for i, (old, new) in enumerate(zip(before, after)) if old != new]
    need(changes == [(73, 148, 47, 149), (74, 148, 47, 149),
                     (73, 149, 47, 149), (74, 149, 47, 149)],
         "教學選項差異不是同焦點下的四個圖示像素")
    for name in ("untouched-esc-space", "toggled-esc-space"):
        exploratory_space(reports, name)
    for name, label, expected in (
            ("orders-menu", "1250m", "a6a3f5bf8fd6e4457fdfce72f0064b34d7800411717eb39b7a94a0161da547f4"),
            ("retire-menu", "1275m", "bef37e89eadc25fd4dd98e218f783b17672f6089c3e2dc2a153712c70b900060")):
        prefix = reports / f"{name}-explore"
        report = json.loads(Path(f"{prefix}.json").read_bytes())
        need(report["game_inputs_sha256"] == FIXTURE_SHA[name] and
             report["samples"][label]["indexed_sha256"] == expected,
             f"{name}: 選單或確認視窗不符")
        raw(prefix, label, report["samples"][label])
    return {"result": "PASS",
            "scope": "教學選項確實切換；Space／Retire 僅有界探索，首則 help 未證實顯示",
            "first_row_receipt_sha256": no_click_sha,
            "tutorial_clicked_receipt_sha256": clicked_sha}


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
