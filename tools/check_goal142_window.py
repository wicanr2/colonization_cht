#!/usr/bin/env python3
"""獨立核對目標142首則教學提示 A 版的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import last_lines, load, same_state

KEY = "GAME.TXT:@TUTORIAL1"
TEXT = (68 * 4, 104 * 4, 256 * 4, 169 * 4)  # 四倍文字安全區
# 檢查點 → (現場截圖名, 是否應顯示中文)
POINTS = {575000000: ("help", True), 585000000: ("cursor", True), 592000000: ("away", True), 620000000: ("closed", False)}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checkpoint(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def check(reports):
    zh, control = load(reports / "replay-zh"), load(reports / "replay-control")
    same_state(zh, control, "終點中英原版狀態不同")
    need(ImageChops.difference(zh[2], control[2]).getbbox() is None, "終點畫面與英文控制不同")
    shots = {}
    for step, (name, shown) in POINTS.items():
        a, b = checkpoint(zh[0], step), checkpoint(control[0], step)
        need(a["memory_sha256"] == b["memory_sha256"] and a["raw_sha256"] == b["raw_sha256"], f"{name}：中英原版狀態不同")
        line = {l["candidate_id"]: l for l in a["lines"]}[KEY]
        need(line["applied"] == shown, f"{name}：help 中文啟用狀態不符")
        live = Image.open(reports / f"replay-zh.cp-{step}.png").convert("RGB")
        english = Image.open(reports / f"replay-control.cp-{step}.png").convert("RGB")
        diff = ImageChops.difference(live, english).getbbox()
        if shown:
            outside = live.copy()
            outside.paste(english.crop(TEXT), TEXT[:2])
            need(diff is not None and ImageChops.difference(outside, english).getbbox() is None, f"{name}：中文越出安全區或未繪製")
        else:
            need(diff is None, f"{name}：關閉後仍殘留中文")
        gui = Image.open(reports / f"gui-help.{name}.png").convert("RGB")
        # 現場 import 可能比檢查點晚一兩幀，原版框外小動畫（船隻閃爍）會不同；help 文字區必須逐像素相同。
        need(ImageChops.difference(gui.crop(TEXT), live.crop(TEXT)).getbbox() is None, f"{name}：現場截圖與同輸入重播的文字區不符")
        outside = ImageChops.difference(gui, live).getbbox()
        shots[name] = {"png_sha256": sha((reports / f"gui-help.{name}.png").read_bytes()),
                       "full_frame_diff_bbox": list(outside) if outside else None}
    stages = [e for e in zh[0]["events"] if e.get("candidate_id") == KEY]
    need([e["stage"] for e in stages] == ["source", "active", "expired"] and stages[2]["reason"] == "canvas-page-changed",
         "help 事件不是來源／啟用／關閉撤銷各一次")
    inputs = (reports / "gui-help.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "現場輸入有被拒絕")
    return {"final_state_sha256": zh[0]["state"]["memory_sha256"], "inputs_sha256": sha(inputs),
            "active_step": stages[1]["step"], "expired_step": stages[2]["step"], "shots": shots}


def check_negative(prefix, reason):
    line = last_lines(json.loads(Path(str(prefix) + ".json").read_text()))[KEY]
    need(not line["applied"] and line["reason"] == reason, f"{prefix.name}：未以 {reason} 回退原文")
    return prefix.name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱首則教學提示正式中文通過")
        return 77
    result = {"result": "PASS", **check(args.reports)}
    r = args.reports
    result["negatives"] = [check_negative(r / "neg-missing", "missing-ink"),
                           check_negative(r / "neg-no-fonts", "font-mask-unavailable"),
                           check_negative(r / "neg-duplicate", "missing-or-invalid-translation")]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
