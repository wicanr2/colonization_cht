#!/usr/bin/env python3
"""正常鍵盤百科選單：六項環繞、真GUI安全區與三側原版狀態。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal134_window import load, same_state
from check_goal179_window import INPUT_SHA, SAVE_SHA, need


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    r = a.reports
    if not all((a.game / n).is_file() for n in INPUT_SHA) or not (r / "scratch/COLONY00.SAV").is_file():
        print("SKIP：缺合法原版或正常存檔，不宣稱選單驗收")
        return 77
    for name, expected in INPUT_SHA.items():
        need(hashlib.sha256((a.game / name).read_bytes()).hexdigest() == expected, "原版指紋不同：" + name)
    need(hashlib.sha256((r / "scratch/COLONY00.SAV").read_bytes()).hexdigest() == SAVE_SHA, "正常存檔指紋不同")
    gui, zh, control, neg = (load(r / n) for n in ("gui-pedia", "replay-zh", "replay-control", "neg-noatlas"))
    same_state(zh, control, "選單中英完整原版狀態不同")
    for side in (gui, neg):
        need(side[0]["state"] == zh[0]["state"] and side[0]["input_hashes"] == zh[0]["input_hashes"]
             and side[0]["opened"] == zh[0]["opened"] and side[1] == zh[1], "GUI或負例完整原版狀態不同")
    inputs = (r / "gui-pedia.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "正常鍵盤輸入有拒絕")
    cps, controls, negatives = ({c["label"]: c for c in side[0]["checkpoints"]} for side in (zh, control, neg))
    # 原版可見六列與分隔列的完整下拉框；不含底下世界畫面的色盤動畫。
    menu = (250 * 4, 12 * 4, 318 * 4, 69 * 4)
    choices = []
    shots = dict(line.split() for line in (r / "gui-pedia.shots").read_text().splitlines())
    for name, value in shots.items():
        label = "cp-" + value
        need(label in cps and label in controls and label in negatives, "缺原版取樣點：" + name)
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            need(cps[label][key] == controls[label][key] == negatives[label][key], "原版取樣點不同：" + name)
        if not name.startswith("pedia-down-"):
            continue
        images = [Image.open(r / f).convert("RGB").crop(menu) for f in
                  (f"gui-pedia.{name}.png", f"replay-zh.{label}.png", f"replay-control.{label}.png")]
        need(ImageChops.difference(images[0], images[1]).getbbox() is None, "真GUI選單安全區不同：" + name)
        need(ImageChops.difference(images[1], images[2]).getbbox() is not None, "選單沒有中文：" + name)
        choices.append(hashlib.sha256(images[2].tobytes()).hexdigest())
    need(len(choices) == 8 and len(set(choices[:6])) == 6 and choices[6:] == choices[:2], "原版選單未呈現六項環繞")
    lo, hi = int(shots["pedia-down-7"]), int(shots["pedia-keyboard-enter"])
    names = {e.get("shown") for e in zh[0]["events"] if e.get("stage") == "active" and lo < e.get("step", 0) <= hi}
    need({"Armed Braves", "Artillery", "Colonists"} <= names, "環繞後Enter未進入已知單位清單")
    print(json.dumps({"result": "PASS", "menu_choices": 6, "keyboard_down": 8, "menu_control_sha256": choices,
                      "checkpoints": len(shots), "inputs_sha256": hashlib.sha256(inputs).hexdigest(),
                      "memory_sha256": zh[0]["state"]["memory_sha256"], "input_fingerprints": INPUT_SHA,
                      "limit": "只驗本版正常百科下拉選單；不宣稱其他路徑沒有資料讀取端"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
