#!/usr/bin/env python3
"""獨立核對目標137：其他國家開遊戲選項與鍵盤快捷鍵的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import GROUP, ROWS, TITLE, diff_only_in_safes, last_lines, load, same_state


# 現場收據 → (現場額外截圖, 預期整組八列印字事件數)
CASES = {
    "options-france": ("options", 1),
    "options-spain": ("options", 1),
    "options-netherlands": ("options", 1),
    "gui-hotkey": ("key-t", 3),
    "load-explore": ("options", 1),  # 由主選單讀入存檔後開窗
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_case(reports, name, shot_name, groups):
    replay, control = load(reports / f"{name}-replay-zh"), load(reports / f"{name}-replay-control")
    same_state(replay, control, f"{name}：現場輸入重播的中英原版狀態不同")
    need(diff_only_in_safes(replay[2], control[2]) and
         ImageChops.difference(replay[2], control[2]).getbbox() is not None,
         f"{name}：中文越出九欄安全區或未繪製")
    lines = last_lines(replay[0])
    need(all(lines[key]["applied"] for key in ROWS + [TITLE]), f"{name}：終點九欄不是全部中文")
    sources = [e for e in replay[0]["events"] if e.get("candidate_id") == GROUP and e.get("stage") == "source"]
    need(len(sources) == groups, f"{name}：整組八列印字事件數為 {len(sources)}，預期 {groups}")
    gui = json.loads((reports / f"{name}.json").read_text())
    inputs = (reports / f"{name}.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), f"{name}：現場輸入有被拒絕")
    need(all(last_lines(gui)[key]["applied"] for key in ROWS + [TITLE]), f"{name}：現場終點九欄不是全部中文")
    gui_final = Image.open(reports / f"{name}.final.png").convert("RGB")
    need(ImageChops.difference(gui_final, replay[2]).getbbox() is None, f"{name}：現場終點畫面與同輸入重播不符")
    shot = Image.open(reports / f"{name}.{shot_name}.png").convert("RGB")
    need(ImageChops.difference(shot, gui_final).getbbox() is None, f"{name}：現場截圖與現場終點畫面不符")
    return {"state_sha256": replay[0]["state"]["memory_sha256"], "row_groups": len(sources),
            "inputs_sha256": sha(inputs), "shot_png_sha256": sha((reports / f"{name}.{shot_name}.png").read_bytes())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱遊戲選項後續驗證通過")
        return 77
    result = {"result": "PASS"}
    for name, (shot, groups) in CASES.items():
        result[name] = check_case(args.reports, name, shot, groups)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
