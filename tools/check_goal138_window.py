#!/usr/bin/env python3
"""獨立核對規格028退休確認框三欄的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import last_lines, load, same_state


FIELDS = {"GAME.TXT:0x00000122": (118, 75, 184, 99), "GAME.TXT:0x00000141": (122, 99, 144, 112),
          "GAME.TXT:0x00000146": (122, 112, 142, 125)}  # 320×200 半開安全矩形


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def only_in_fields(live, control):
    outside = live.copy()
    for x0, y0, x1, y1 in FIELDS.values():
        box = (x0 * 4, y0 * 4, x1 * 4, y1 * 4)
        outside.paste(control.crop(box), box)
    return ImageChops.difference(outside, control).getbbox() is None


def check(reports):
    dialog, dialog_control = load(reports / "dialog-zh"), load(reports / "dialog-control")
    same_state(dialog, dialog_control, "開框時中英原版狀態不同")
    lines = last_lines(dialog[0])
    need(all(lines[key]["applied"] for key in FIELDS), "開框時三欄不是全部中文")
    need(only_in_fields(dialog[2], dialog_control[2]) and
         ImageChops.difference(dialog[2], dialog_control[2]).getbbox() is not None, "中文越出三欄安全區或未繪製")
    events = [e for e in dialog[0]["events"] if e.get("candidate_id") in FIELDS]
    actives = {e["candidate_id"]: e for e in events if e["stage"] == "active"}
    need(set(actives) == set(FIELDS) and
         [actives[k]["changed_pixels"] for k in FIELDS] == [441, 64, 54], "三欄啟用事件或改色點數不符")
    closed, closed_control = load(reports / "closed-zh"), load(reports / "closed-control")
    same_state(closed, closed_control, "關框後中英原版狀態不同")
    last = last_lines(closed[0])
    need(not any(last[key]["applied"] for key in FIELDS) and
         ImageChops.difference(closed[2], closed_control[2]).getbbox() is None, "關框後仍殘留中文")
    gui = json.loads((reports / "gui-retire.json").read_text())
    inputs = (reports / "gui-retire.inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "現場輸入有被拒絕")
    shot = Image.open(reports / "gui-retire.dialog.png").convert("RGB")
    need(ImageChops.difference(shot, dialog[2]).getbbox() is None, "開框現場截圖與重播不符")
    final = Image.open(reports / "gui-retire.final.png").convert("RGB")
    need(ImageChops.difference(final, closed[2]).getbbox() is None, "關框現場終點與重播不符")
    return {"dialog_state_sha256": dialog[0]["state"]["memory_sha256"],
            "closed_state_sha256": closed[0]["state"]["memory_sha256"],
            "active_steps": {k: actives[k]["step"] for k in FIELDS},
            "inputs_sha256": sha(inputs), "dialog_png_sha256": sha((reports / "gui-retire.dialog.png").read_bytes())}


def check_negative(prefix, reason):
    report = json.loads(Path(str(prefix) + ".json").read_text())
    last = last_lines(report)
    need(all(not last[key]["applied"] and last[key]["reason"] == reason for key in FIELDS),
         f"負例未以 {reason} 回退原文")
    return Path(prefix).name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱退休確認框正式中文通過")
        return 77
    result = {"result": "PASS", **check(args.reports)}
    result["negatives"] = [check_negative(args.reports / "neg-missing", "missing-ink"),
                           check_negative(args.reports / "neg-no-fonts", "font-mask-unavailable")]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
