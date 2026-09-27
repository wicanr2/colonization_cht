#!/usr/bin/env python3
"""獨立核對規格034開場製作名單職稱橫幅的真 GUI 與同輸入重播收據；原版缺失回 SKIP 77。"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

# 檢查點 → (GUI 截圖名, 應套用的鍵；None 表示任何職稱橫幅都不得套用)
POINTS = {320000000: ("adventure", "adventure"), 460000000: ("design", "design"), 480000000: ("names", None),
          555000000: ("programming", "programming"), 655000000: ("graphics", "graphics"), 810000000: ("music", "music"),
          960000000: ("sound", "sound"), 1060000000: ("nobanner", None), 1115000000: ("qa", "qa")}
PREFIX = "OPENCRD1.SS:role:"
NEGATIVES = {"missing": {"missing-ink"}, "nomasks": {"font-mask-unavailable"},
             "edited": {"font-binding-mismatch"}, "duplicate": {"duplicate-key", "font-binding-mismatch"}}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bands(catalog):
    rows = csv.DictReader(io.StringIO(catalog.read_text(encoding="utf-8")), delimiter="\t")
    return {r["candidate_id"]: tuple(4 * int(v) for v in r["text_band"].split(",")) for r in rows
            if r["candidate_id"].startswith(PREFIX)}  # 目標166 起清冊另有非製作名單列


def checkpoint(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def statics(cp):
    return {l["candidate_id"]: l for l in cp["lines"] if l["candidate_id"].startswith(PREFIX)}


def check(r, band):
    zh, control = load(r / "replay/zh"), load(r / "replay/control")
    same_state(zh, control, "終點中英原版狀態不同")
    shots = {}
    for step, (name, role) in POINTS.items():
        a, b = checkpoint(zh[0], step), checkpoint(control[0], step)
        need(a["memory_sha256"] == b["memory_sha256"] and a["raw_sha256"] == b["raw_sha256"], f"{name}：中英原版狀態不同")
        lines = statics(a)
        need(len(lines) == len(band), f"{name}：靜態欄位數不符")
        on = {k for k, l in lines.items() if l["applied"]}
        need(on == ({PREFIX + role} if role else set()), f"{name}：套用集合不符 {sorted(on)}")
        need(all(l["reason"] == "fingerprint-mismatch" for k, l in lines.items() if k not in on), f"{name}：未套用原因不符")
        live = Image.open(r / f"replay/zh.cp-{step}.png").convert("RGB")
        english = Image.open(r / f"replay/control.cp-{step}.png").convert("RGB")
        diff = ImageChops.difference(live, english).getbbox()
        if role:
            box = band[PREFIX + role]
            need(diff is not None and box[0] <= diff[0] and box[1] <= diff[1] and diff[2] <= box[2] and diff[3] <= box[3],
                 f"{name}：中文越出文字帶或未繪製 {diff}")
        else:
            need(diff is None, f"{name}：非職稱畫面被改動 {diff}")
        gui = Image.open(r / f"gui-opening.{name}.png").convert("RGB")
        need(gui.size == (1280, 800), f"{name}：GUI 截圖尺寸不符")
        if role:
            box = band[PREFIX + role]
            need(ImageChops.difference(gui.crop(box), live.crop(box)).getbbox() is None, f"{name}：現場截圖與重播文字帶不符")
        rest = ImageChops.difference(gui, live).getbbox()
        shots[name] = {"png_sha256": sha((r / f"gui-opening.{name}.png").read_bytes()), "applied": sorted(on),
                       "zh_control_diff_bbox": list(diff) if diff else None, "full_frame_diff_bbox": list(rest) if rest else None}
    last = statics(zh[0]["frames"][-1])
    need(all(l["accepted_events"] == 1 for l in last.values()), "每個職稱應恰好啟用一次")
    need(not any(l["applied"] for l in statics(control[0]["frames"][-1]).values()) and
         all(l["accepted_events"] == 0 for l in statics(control[0]["frames"][-1]).values()), "英文控制出現中文")
    inputs = (r / "gui-opening.inputs.json").read_bytes()
    # 視窗啟動時只記下初始指標位置；不得有任何按鍵或滑鼠按鈕事件。
    need(not json.loads(inputs).get("rejected") and all(e["kind"] == "move" and not e["button"] for e in json.loads(inputs)["inputs"]),
         "開場應為玩家不按鍵")
    return {"final_state_sha256": zh[0]["state"]["memory_sha256"], "inputs_sha256": sha(inputs), "shots": shots}


def negatives(r):
    out = {}
    english = Image.open(r / "replay/control.cp-460000000.png").convert("RGB")
    for name, reasons in NEGATIVES.items():
        report = json.loads((r / f"neg/{name}.json").read_text())
        lines = statics(checkpoint(report, 460000000))
        need(lines and not any(l["applied"] for l in lines.values()), f"{name}：負例仍套用")
        need(all(l["reason"] in reasons for l in lines.values()), f"{name}：原因不符")
        png = Image.open(r / f"neg/{name}.cp-460000000.png").convert("RGB")
        need(ImageChops.difference(png, english).getbbox() is None, f"{name}：負例畫面不是原版")
        out[name] = sorted({l["reason"] for l in lines.values()})
    need(statics(checkpoint(json.loads((r / "neg/duplicate.json").read_text()), 460000000))[PREFIX + "design"]["reason"]
         == "duplicate-key", "重複鍵未整組停用")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/static-overlay.zh-Hant.tsv"))
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱開場職稱橫幅中文通過")
        return 77
    result = {"result": "PASS", **check(a.reports, bands(a.catalog)), "negatives": negatives(a.reports)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
