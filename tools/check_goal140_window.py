#!/usr/bin/env python3
"""獨立核對規格022其餘三張國家旗卡 A 版的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import last_lines, load, same_state


# 320×200 半開安全矩形
FIELDS = {
    "NAMES.TXT:0x00000906": (225, 12, 290, 24), "LABELS.TXT:0x000008FF": (225, 83, 290, 96),
    "NAMES.TXT:0x00000921": (125, 103, 190, 115), "LABELS.TXT:0x0000090C": (125, 174, 190, 187),
    "NAMES.TXT:0x0000093D": (225, 103, 290, 115), "LABELS.TXT:0x00000916": (225, 174, 290, 187),
}
FRANCE, SPAIN, NETHERLANDS = list(FIELDS)[0:2], list(FIELDS)[2:4], list(FIELDS)[4:6]
# 檢查點 → 預期啟用欄位
POINTS = {"france": set(FRANCE), "spain": set(SPAIN), "netherlands": set(NETHERLANDS),
          "cursor": {NETHERLANDS[1]}, "away": set(NETHERLANDS), "name": set()}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def diff_fields(live, base):
    """回傳畫面差異落在哪些欄位；差異越出安全區時丟例外。"""
    outside = live.copy()
    hit = set()
    for key, (x0, y0, x1, y1) in FIELDS.items():
        box = (x0 * 4, y0 * 4, x1 * 4, y1 * 4)
        if ImageChops.difference(live.crop(box), base.crop(box)).getbbox() is not None:
            hit.add(key)
        outside.paste(base.crop(box), box)
    need(ImageChops.difference(outside, base).getbbox() is None, "中文越出旗卡安全區")
    return hit


def point(reports, tag, applied):
    zh, base, control = (load(reports / f"{tag}-{m}") for m in ("zh", "base", "control"))
    same_state(zh, control, f"{tag}：中英原版狀態不同")
    need(zh[0]["state"] == base[0]["state"] and zh[1] == base[1], f"{tag}：啟用旗標改變了原版狀態")
    last, base_last = last_lines(zh[0]), last_lines(base[0])
    need({k for k in FIELDS if last[k]["applied"]} == applied, f"{tag}：啟用欄位不符預期 {sorted(applied)}")
    need(not any(k in base_last for k in FIELDS), f"{tag}：未啟用旗標時仍載入其餘旗卡欄位")
    need({k: v["applied"] for k, v in last.items() if k not in FIELDS} ==
         {k: v["applied"] for k, v in base_last.items() if k not in FIELDS}, f"{tag}：其他欄位狀態被改變")
    need(diff_fields(zh[2], base[2]) == applied, f"{tag}：畫面差異欄位與啟用欄位不符")
    return zh, {k: last[k]["reason"] for k in FIELDS}


def check(reports):
    replays = {}
    for tag, applied in POINTS.items():
        replays[tag], reasons = point(reports, tag, applied)
        if tag == "cursor":
            need(reasons[NETHERLANDS[0]] == "cursor-over-card-field", "游標壓荷蘭上欄時未以游標守門回原文")
    inputs = (reports / "gui-cards.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "現場輸入有被拒絕")
    for tag in POINTS:
        live = Image.open(reports / f"gui-cards.{tag}.png").convert("RGB")
        need(ImageChops.difference(live, replays[tag][2]).getbbox() is None, f"{tag}：現場截圖與同輸入重播不符")
    gui = json.loads((reports / "gui-cards.json").read_text())
    need(not any(last_lines(gui)[k]["applied"] for k in FIELDS), "現場終點仍殘留旗卡中文")
    return {"inputs_sha256": sha(inputs),
            "states": {tag: replays[tag][0]["state"]["memory_sha256"] for tag in POINTS},
            "shots": {tag: sha((reports / f"gui-cards.{tag}.png").read_bytes()) for tag in POINTS}}


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
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "NAMES.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱其餘三張旗卡正式中文通過")
        return 77
    result = {"result": "PASS", **check(args.reports)}
    r = args.reports
    result["negatives"] = [
        check_negative(r / "neg-missing", {k: "missing-ink" for k in SPAIN}),
        check_negative(r / "neg-no-fonts", {k: "font-mask-unavailable" for k in SPAIN}),
        check_negative(r / "neg-duplicate", {SPAIN[0]: "missing-or-invalid-translation"}),
    ]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
