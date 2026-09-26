#!/usr/bin/env python3
"""獨立核對規格032海上頂列與狀態欄的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import last_lines, load, same_state

BAR, PANEL = (0, 0, 1280, 32), (960, 192, 1280, 800)  # 四倍安全區
LAYERS = ("sea:bar", "sea:panel")
POINTS = {565000000: "title", 590000000: "menu", 612000000: "move1", 652000000: "move3",
          662000000: "cursor", 672000000: "away"}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def outside(a, b, boxes):
    a = a.copy()
    for box in boxes:
        a.paste(b.crop(box), box[:2])
    return ImageChops.difference(a, b).getbbox()


def checkpoint(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def check(r):
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    same_state(zh, control, "終點中英原版狀態不同")
    shots = {}
    for step, name in POINTS.items():
        a, b = checkpoint(zh[0], step), checkpoint(control[0], step)
        need(a["memory_sha256"] == b["memory_sha256"] and a["raw_sha256"] == b["raw_sha256"], f"{name}：中英原版狀態不同")
        lines = {l["candidate_id"]: l for l in a["lines"]}
        need(all(lines[k]["applied"] for k in LAYERS), f"{name}：頂列或狀態欄未套用")
        live = Image.open(r / f"replay-zh.cp-{step}.png").convert("RGB")
        english = Image.open(r / f"replay-control.cp-{step}.png").convert("RGB")
        need(outside(live, english, (BAR, PANEL)) is None and ImageChops.difference(live, english).getbbox(),
             f"{name}：中文越出安全區或未繪製")
        gui = Image.open(r / f"gui-sea.{name}.png").convert("RGB")
        for box in (BAR, PANEL):
            need(ImageChops.difference(gui.crop(box), live.crop(box)).getbbox() is None, f"{name}：現場截圖與重播的安全區不符")
        rest = ImageChops.difference(gui, live).getbbox()
        shots[name] = {"png_sha256": sha((r / f"gui-sea.{name}.png").read_bytes()),
                       "full_frame_diff_bbox": list(rest) if rest else None}
    inputs = (r / "gui-sea.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "現場輸入有被拒絕")
    return {"final_state_sha256": zh[0]["state"]["memory_sha256"], "inputs_sha256": sha(inputs), "shots": shots,
            "misses": zh[0].get("sea_misses")}


def negatives(r):
    out = []
    for name, reasons in (("neg-missing", {"missing-ink"}), ("neg-no-atlas", {"font-mask-unavailable"}),
                          ("neg-duplicate", {"catalog-source-mismatch", "catalog-duplicate", "font-binding-mismatch"})):
        last = last_lines(json.loads((r / f"{name}.json").read_text()))
        need(all(not last[k]["applied"] and last[k]["reason"] in reasons for k in LAYERS), f"{name}：未回退原文")
        out.append(name)
    report = json.loads((r / "neg-missing-word.json").read_text())
    last = last_lines(report)
    need(last["sea:panel"]["applied"] and last["sea:panel"]["rows"] == 10 and "(Ocean)" in report["sea_misses"],
         "缺詞負例：地形行未單獨回英文")
    out.append("neg-missing-word")
    return out


def combo(r):
    both = load(r / "combo-options")
    rows = load(r / "regress" / "rows-1280m")
    need(both[0]["state"] == rows[0]["state"] and both[1] == rows[1], "組合重播改變了原版狀態")
    a, b = last_lines(both[0]), last_lines(rows[0])
    # 組合重播另帶 --all-menu 等旗標，多出的欄位不在比對範圍；只比單開選項時也有的欄位。
    need(set(b) <= set(a) and all(a[k]["applied"] == b[k]["applied"] for k in b), "組合重播中遊戲選項欄位狀態不同")
    need(outside(both[2], rows[2], (BAR, PANEL)) is None, "組合重播在海上安全區外與只開選項時不同")
    return {k: a[k]["applied"] for k in LAYERS}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file() or not (a.game / "NAMES.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱海上選單列與狀態欄正式中文通過")
        return 77
    result = {"result": "PASS", **check(a.reports), "negatives": negatives(a.reports), "combo_sea_applied": combo(a.reports)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
