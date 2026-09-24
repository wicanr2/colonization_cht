#!/usr/bin/env python3
"""獨立核對真 Ebitengine 玩家左鍵／Esc 路徑及兩個反向對照。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal112_options_source import MENU_SHA


CYCLE_SHA = "97d2506bcbab011ebaedc397fb06ed8bde8030160a1a129ddae897db05f72a2e"
INPUT_SHA = "dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98"
WINDOW_SOURCE_SHA = "2e6d4238d4ed0a49797e6750c2ca5135345c2120a17bbd93aafce01f992ee1eb"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def original_bytes(reports, stem, suffix):
    data = (reports / f"{stem}.{suffix}").read_bytes()
    need(bool(data), f"缺少原版收據：{stem}.{suffix}")
    return data


def check(game, reports, source, output=None):
    originals = {**FILE_SHA, "MENU.TXT": MENU_SHA, "CYCLE.DAT": CYCLE_SHA}
    if not all((game / name).is_file() for name in originals):
        return {"result": "SKIP", "reason": "合法 DOS 原版不齊"}
    for name, expected in originals.items():
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    if output is not None:
        need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
             "收據輸出目錄不存在或擁有者不符")
    need(sha(source.read_bytes()) == WINDOW_SOURCE_SHA, "真視窗前端程式版本不符")

    prefix = "live-route-b"
    input_bytes = original_bytes(reports, prefix, "inputs.json")
    need(sha(input_bytes) == INPUT_SHA, "真視窗玩家收據版本不符")
    inputs = json.loads(input_bytes)
    need(inputs.get("end") == 1_350_000_000 and not inputs.get("rejected"),
         "真視窗終點或被拒絕輸入不符")
    events = inputs["inputs"]
    need(all(isinstance(e.get("step"), int) and 0 <= e["step"] <= inputs["end"]
             for e in events) and
         all(a["step"] <= b["step"] for a, b in zip(events, events[1:])),
         "真視窗輸入時間不單調")
    keys = [(e["kind"], e["step"], e.get("text")) for e in events
            if e["kind"] in ("enter", "escape", "left", "right", "up", "down", "text", "backspace")]
    need([k[0] for k in keys] == ["enter"] * 5 + ["left", "escape"] and
         1_225_000_000 <= keys[5][1] < 1_250_000_000 and
         1_290_000_000 <= keys[6][1] < 1_320_000_000,
         "真視窗鍵序不是五次 Enter、海上左鍵、選項 Esc")
    need(all(e.get("text") is None and e.get("button") == e.get("x") == e.get("y") == 0
             for e in events if e["kind"] in ("enter", "escape", "left")),
         "控制鍵混入文字或滑鼠欄位")

    live = read_json(reports / f"{prefix}.json")
    control = read_json(reports / f"{prefix}-control.json")
    need(live["control"] is False and control["control"] is True and
         live["all_menu"] is True and control["all_menu"] is True,
         "中文與英文控制模式不符")
    need(live["state"] == control["state"] and live["opened"] == control["opened"] and
         live["input_hashes"] == control["input_hashes"],
         "真視窗／英文控制的原版 CPU、RAM、時間或開檔不同")
    for suffix in ("memory", "final.idx", "final.pal"):
        need(original_bytes(reports, prefix, suffix) ==
             original_bytes(reports, prefix + "-control", suffix),
             "真視窗／英文控制的原版實檔不同：" + suffix)
    need("MENU.TXT" in live["opened"] and live["opened"].count("GAME.TXT") >= 2,
         "原版遊戲選項頁未由正常玩家路徑開啟")

    control_inputs = {"inputs": inputs["inputs"], "end": inputs["end"]}
    counterfactuals = {}
    for kind in ("left", "escape"):
        name = f"without-{kind}"
        variant = read_json(reports / f"{name}.inputs.json")
        expected = {"inputs": [e for e in control_inputs["inputs"] if e["kind"] != kind],
                    "end": control_inputs["end"]}
        need(variant == expected, f"反向對照 {kind} 不是只移除單一鍵")
        report = read_json(reports / f"{name}.json")
        need(report["control"] is True and report["input_hashes"] == control["input_hashes"],
             f"反向對照 {kind} 的原版或控制模式不符")
        need(report["state"] != control["state"] and
             original_bytes(reports, name, "final.idx") !=
             original_bytes(reports, prefix + "-control", "final.idx"),
             f"移除 {kind} 後原版玩家可見畫面未改變")
        counterfactuals[kind] = {
            "input_sha256": sha((reports / f"{name}.inputs.json").read_bytes()),
            "final_index_sha256": sha(original_bytes(reports, name, "final.idx")),
        }

    shots = {}
    for name in ("sea-before", "sea-after-left", "game-menu", "game-options", "after-escape"):
        data = original_bytes(reports, prefix, name + ".png")
        need(data[:8] == b"\x89PNG\r\n\x1a\n" and data[16:24] ==
             (1280).to_bytes(4, "big") + (800).to_bytes(4, "big"),
             "真視窗截圖格式或尺寸不符：" + name)
        shots[name] = sha(data)
    need(shots["sea-before"] != shots["sea-after-left"] and
         shots["game-options"] != shots["after-escape"],
         "真視窗左鍵或 Esc 前後畫面沒有變化")
    focus_inputs = read_json(reports / "focus-left.inputs.json")
    need(focus_inputs.get("end") == 30_000_000 and not focus_inputs.get("rejected") and
         [e["kind"] for e in focus_inputs["inputs"] if e["kind"] in
          ("enter", "escape", "left", "right", "up", "down", "text", "backspace")] == ["enter"],
         "失焦左鍵延遲送入原版，或正常 Enter 消失")
    focus = read_json(reports / "focus-left.json")
    focus_control = read_json(reports / "focus-left-control.json")
    need(focus["control"] is False and focus_control["control"] is True and
         focus["state"] == focus_control["state"] and
         focus["opened"] == focus_control["opened"],
         "失焦負例與英文控制的原版狀態不同")
    for suffix in ("memory", "final.idx", "final.pal"):
        need(original_bytes(reports, "focus-left", suffix) ==
             original_bytes(reports, "focus-left-control", suffix),
             "失焦負例原版實檔不同：" + suffix)
    result = {
        "result": "PASS",
        "scope": "固定英格蘭真視窗冷啟動；五次 Enter 後於海上送左鍵，再開 Game Options 並送 Esc",
        "input_sha256": sha(input_bytes),
        "keyboard": keys,
        "state_sha256": sha(json.dumps(live["state"], sort_keys=True).encode()),
        "final_index_sha256": sha(original_bytes(reports, prefix, "final.idx")),
        "screenshots_sha256": shots,
        "counterfactuals": counterfactuals,
        "unfocused_input_sha256": sha((reports / "focus-left.inputs.json").read_bytes()),
        "limitations": "右／上／下只驗 BIOS 轉送，未驗遊戲效果；首則 help 未因本項宣稱顯示",
    }
    if output is not None:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path(__file__).parent / "window_prototype.go")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.game, args.reports, args.source, args.output)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f"FAIL：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(77 if result["result"] == "SKIP" else 0)
