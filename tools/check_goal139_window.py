#!/usr/bin/env python3
"""獨立核對規格016第三張難度卡 A 版的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import last_lines, load, same_state


UPPER, LOWER = "NAMES.TXT:0x00000C22", "LABELS.TXT:0x000008B8"
FIELDS = {UPPER: (29, 139, 84, 148), LOWER: (38, 148, 76, 157)}  # 320×200 半開安全矩形


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def diff_boxes(live, control):
    """回傳中英差異落在哪些欄位；差異越出兩欄安全區時丟例外。"""
    outside = live.copy()
    hit = set()
    for key, (x0, y0, x1, y1) in FIELDS.items():
        box = (x0 * 4, y0 * 4, x1 * 4, y1 * 4)
        if ImageChops.difference(live.crop(box), control.crop(box)).getbbox() is not None:
            hit.add(key)
        outside.paste(control.crop(box), box)
    need(ImageChops.difference(outside, control).getbbox() is None, "中文越出第三卡兩欄安全區")
    return hit


def point(reports, tag, applied):
    zh, base, control = (load(reports / f"{tag}-{m}") for m in ("zh", "base", "control"))
    same_state(zh, control, f"{tag}：中英原版狀態不同")
    need(zh[0]["state"] == base[0]["state"] and zh[1] == base[1], f"{tag}：啟用第三卡改變了原版狀態")
    last, base_last = last_lines(zh[0]), last_lines(base[0])
    need({k for k in FIELDS if last[k]["applied"]} == applied, f"{tag}：啟用欄位不符預期 {sorted(applied)}")
    need(not any(k in base_last for k in FIELDS), f"{tag}：未啟用旗標時仍載入第三卡欄位")
    need({k: v["applied"] for k, v in last.items() if k not in FIELDS} ==
         {k: v["applied"] for k, v in base_last.items() if k not in FIELDS}, f"{tag}：其他欄位狀態被改變")
    # 其他已正式欄位在兩者都相同；差異只能落在第三卡兩欄。
    need(diff_boxes(zh[2], base[2]) == applied, f"{tag}：畫面差異欄位與啟用欄位不符")
    return zh, {k: last[k]["reason"] for k in FIELDS}


def check(reports):
    card, card_reasons = point(reports, "card", set(FIELDS))
    # 游標守門是整張卡的外擴範圍（同前兩張卡），壓上欄時兩欄一起回原文。
    hover, hover_reasons = point(reports, "hover", set())
    need(set(hover_reasons.values()) == {"cursor-conservative-guard"}, "游標壓卡時未以游標守門回原文")
    away, _ = point(reports, "away", set(FIELDS))
    nation, _ = point(reports, "nation", set())
    gui = json.loads((reports / "gui-third.json").read_text())
    inputs = (reports / "gui-third.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "現場輸入有被拒絕")
    for shot, replay in (("card", card), ("hover", hover), ("away", away), ("nation", nation)):
        live = Image.open(reports / f"gui-third.{shot}.png").convert("RGB")
        need(ImageChops.difference(live, replay[2]).getbbox() is None, f"{shot}：現場截圖與同輸入重播不符")
    final = Image.open(reports / "gui-third.final.png").convert("RGB")
    need(ImageChops.difference(final, nation[2]).getbbox() is None, "現場終點與重播不符")
    need(not any(last_lines(gui)[k]["applied"] for k in FIELDS), "現場終點仍殘留第三卡中文")
    return {"card_state_sha256": card[0]["state"]["memory_sha256"],
            "nation_state_sha256": nation[0]["state"]["memory_sha256"],
            "inputs_sha256": sha(inputs),
            "card_png_sha256": sha((reports / "gui-third.card.png").read_bytes())}


def check_negative(prefix, reasons):
    report = json.loads(Path(str(prefix) + ".json").read_text())
    last = last_lines(report)
    for key, reason in reasons.items():
        need(not last[key]["applied"] and last[key]["reason"] == reason, f"{prefix.name}：{key} 未以 {reason} 回退原文")
    return prefix.name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "NAMES.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱第三張難度卡正式中文通過")
        return 77
    result = {"result": "PASS", **check(args.reports)}
    r = args.reports
    result["negatives"] = [
        check_negative(r / "neg-missing", {k: "missing-ink" for k in FIELDS}),
        check_negative(r / "neg-no-fonts", {k: "font-mask-unavailable" for k in FIELDS}),
        check_negative(r / "neg-duplicate", {UPPER: "missing-or-invalid-translation"}),
    ]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
