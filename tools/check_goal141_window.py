#!/usr/bin/env python3
"""獨立核對規格026目標141十張開場字幕的同輸入前端收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import last_lines, load, same_state


# 檢查點步數 → (字幕鍵, 320×200 半開安全區)
CHECKPOINTS = {
    110000000: ("GAME.TXT:0x000153CC", (12, 27, 307, 42)),
    238000000: ("GAME.TXT:0x0001542B", (12, 27, 307, 52)),
    348000000: ("GAME.TXT:0x00015482", (12, 27, 307, 42)),
    484000000: ("GAME.TXT:0x000154CB", (12, 27, 307, 42)),
    590000000: ("GAME.TXT:0x00015522", (12, 27, 307, 42)),
    699000000: ("GAME.TXT:0x0001555D", (12, 27, 307, 42)),
    807000000: ("GAME.TXT:0x00015597", (12, 27, 307, 42)),
    915000000: ("GAME.TXT:0x000155F5", (12, 27, 307, 42)),
    1024000000: ("GAME.TXT:0x0001563F", (12, 27, 307, 42)),
    1132000000: ("GAME.TXT:0x00015695", (12, 27, 307, 42)),
}
KEYS = [key for key, _ in CHECKPOINTS.values()]
NEW = KEYS[1:]


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checkpoint(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def only_in(live, control, box):
    x0, y0, x1, y1 = (v * 4 for v in box)
    outside = live.copy()
    outside.paste(control.crop((x0, y0, x1, y1)), (x0, y0))
    return (ImageChops.difference(outside, control).getbbox() is None and
            ImageChops.difference(live, control).getbbox() is not None)


def check(reports):
    zh, control = load(reports / "replay-zh"), load(reports / "replay-control")
    same_state(zh, control, "終點中英原版狀態不同")
    need(not any(last_lines(zh[0])[k]["applied"] for k in KEYS), "終點仍殘留字幕中文")
    need(ImageChops.difference(zh[2], control[2]).getbbox() is None, "終點畫面與英文控制不同")
    shots = {}
    for step, (key, box) in CHECKPOINTS.items():
        a, b = checkpoint(zh[0], step), checkpoint(control[0], step)
        need(a["memory_sha256"] == b["memory_sha256"] and a["raw_sha256"] == b["raw_sha256"] and
             a["palette_sha256"] == b["palette_sha256"], f"{step}：中英原版狀態不同")
        lines = {line["candidate_id"]: line for line in a["lines"]}
        need({k for k in KEYS if lines[k]["applied"]} == {key}, f"{step}：啟用字幕不是 {key}")
        live = Image.open(reports / f"replay-zh.cp-{step}.png").convert("RGB")
        english = Image.open(reports / f"replay-control.cp-{step}.png").convert("RGB")
        need(only_in(live, english, box), f"{step}：中文越出安全區或未繪製")
        gui = Image.open(reports / f"gui-captions.cp-{step}.png").convert("RGB")
        need(ImageChops.difference(gui, live).getbbox() is None, f"{step}：現場截圖與同輸入重播不符")
        shots[key] = sha((reports / f"gui-captions.cp-{step}.png").read_bytes())
    # 每張字幕只在自己的來源事件與撤銷事件之間套用。
    events = zh[0]["events"]
    for key in KEYS:
        stages = [e for e in events if e.get("candidate_id") == key]
        source = [e["step"] for e in stages if e["stage"] == "source"]
        active = [e["step"] for e in stages if e["stage"] == "active"]
        expired = [e["step"] for e in stages if e["stage"] == "expired"]
        need(len(source) == len(active) == len(expired) == 1 and source[0] < active[0] < expired[0],
             f"{key}：來源／啟用／撤銷事件不是各一次")
        applied = [f["step"] for f in zh[0]["frames"]
                   if any(l["candidate_id"] == key and l["applied"] for l in f["lines"])]
        need(applied and active[0] <= applied[0] and applied[-1] < expired[0], f"{key}：套用畫格越出事件範圍")
    gui_inputs = (reports / "gui-captions.inputs.json").read_bytes()
    need(not json.loads(gui_inputs).get("rejected"), "現場輸入有被拒絕")
    return {"final_state_sha256": zh[0]["state"]["memory_sha256"], "gui_inputs_sha256": sha(gui_inputs), "shots": shots}


def check_negative(prefix, reasons):
    last = last_lines(json.loads(Path(str(prefix) + ".json").read_text()))
    for key, reason in reasons.items():
        need(not last[key]["applied"] and last[key]["reason"] == reason, f"{prefix.name}：{key} 未以 {reason} 回退原文")
    return prefix.name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱開場字幕正式中文通過")
        return 77
    result = {"result": "PASS", **check(args.reports)}
    r = args.reports
    result["negatives"] = [
        check_negative(r / "neg-missing", {k: "missing-ink" for k in KEYS}),
        check_negative(r / "neg-no-fonts", {k: "font-mask-unavailable" for k in NEW}),
        check_negative(r / "neg-duplicate", {"GAME.TXT:0x00015482": "missing-or-invalid-translation"}),
        # 變數 TSV 被改：該列來源不符而視為缺值（@BUILD3 展開失敗），其餘字模綁定的變數 TSV 雜湊也失效。
        check_negative(r / "neg-values", {k: ("missing-or-invalid-translation" if k == "GAME.TXT:0x00015482"
                                             else "font-binding-mismatch") for k in NEW}),
    ]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
