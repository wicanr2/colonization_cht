#!/usr/bin/env python3
"""獨立核對規格025英格蘭首次介紹兩頁的同輸入前端收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


PAGE_A, PAGE_B = "GAME.TXT:@NATION0A", "GAME.TXT:@NATION0B"
SOURCE = "GAME.TXT:@NATION0"
PANEL = (32, 32, 1248, 768)  # 四倍輸出的木紋頁內；中文只能改動這個範圍


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(prefix):
    data = json.loads(Path(str(prefix) + ".json").read_text())
    files = {ext: Path(str(prefix) + "." + ext).read_bytes() for ext in ("memory", "final.idx", "final.pal")}
    return data, files, Image.open(str(prefix) + ".final.png").convert("RGB")


def lines(frame):
    return {line["candidate_id"]: line for line in frame["lines"]}


def same_state(live, control, why):
    (a, fa, pa), (b, fb, pb) = live, control
    need(a["control"] is False and b["control"] is True and a["state"] == b["state"] and
         a["opened"] == b["opened"] and a["input_hashes"] == b["input_hashes"] and fa == fb and
         len(a["frames"]) == len(b["frames"]) and pa.size == pb.size == (1280, 800), why)


def page_events(report):
    return [e for e in report["events"] if e.get("candidate_id", "").startswith("GAME.TXT:@NATION0")]


def check_page(live_prefix, control_prefix, page, steps):
    live, control = load(live_prefix), load(control_prefix)
    same_state(live, control, f"{page}：中文與英文控制的原版狀態、輸入或完整記憶體不同")
    report = live[0]
    need(report["state"]["steps"] == steps, "終點步數不符")
    last = lines(report["frames"][-1])
    other = PAGE_B if page == PAGE_A else PAGE_A
    need(last[page]["applied"] and not last[other]["applied"], f"{page}：終點畫格沒有中文或另一頁誤套用")
    events = page_events(report)
    actives = [e for e in events if e["stage"] == "active" and e["candidate_id"] == page]
    need(actives and all(e["visible_chars"] == (833 if page == PAGE_A else 170) and
                         e["changed_pixels"] == (14193 if page == PAGE_A else 2932) for e in actives),
         f"{page}：啟用事件的可見字數或改色點數不符")
    first = min(e["step"] for e in actives)
    sources = [e for e in events if e["candidate_id"] == SOURCE and e["stage"] == "source" and e["step"] < first]
    need(sources and sources[-1]["source_linear"] == 0x2A862 and sources[-1]["entry_ip"] == "0D21:00C6",
         f"{page}：缺當次整頁印字來源事件")
    for frame in report["frames"]:
        line = lines(frame).get(page)
        if line and line["applied"]:
            need(frame["step"] >= first, f"{page}：真 VGA 同步前就套用中文")
    outside = live[2].copy()
    outside.paste(control[2].crop(PANEL), PANEL)
    need(ImageChops.difference(outside, control[2]).getbbox() is None and
         ImageChops.difference(live[2], control[2]).getbbox() is not None,
         f"{page}：中文像素越出木紋頁內或完全未繪製")
    return {"state_sha256": report["state"]["memory_sha256"], "active_step": first,
            "applied_frames": sum(1 for f in report["frames"] if lines(f).get(page, {}).get("applied"))}


def check_exit(live_prefix, control_prefix):
    live, control = load(live_prefix), load(control_prefix)
    same_state(live, control, "離頁後中英原版狀態或完整記憶體不同")
    last = lines(live[0]["frames"][-1])
    expired = [e for e in page_events(live[0]) if e["stage"] == "expired" and e["candidate_id"] == PAGE_B]
    need(not last[PAGE_A]["applied"] and not last[PAGE_B]["applied"] and expired and
         ImageChops.difference(live[2], control[2]).getbbox() is None,
         "B 頁離開後仍殘留中文或未撤銷")
    return {"exit_state_sha256": live[0]["state"]["memory_sha256"], "exit_step": expired[-1]["step"]}


def check_negative(prefix, reason):
    report = json.loads(Path(str(prefix) + ".json").read_text())
    last = lines(report["frames"][-1])
    need(all(not last[p]["applied"] and last[p]["reason"] == reason for p in (PAGE_A, PAGE_B)),
         f"負例未以 {reason} 回退原文")
    return Path(prefix).name


def check_gui(gui_prefix, reports):
    gui = json.loads(Path(str(gui_prefix) + ".json").read_text())
    inputs = Path(str(gui_prefix) + ".inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), "現場輸入有被拒絕")
    need(lines(gui["frames"][-1])[PAGE_B]["applied"], "現場視窗終點 B 頁沒有中文")
    result = {"real_gui_inputs_sha256": sha(inputs)}
    for name, replay in (("page-a", "zh-53m"), ("page-b", "zh-62m")):
        shot = Image.open(str(gui_prefix) + f".{name}.png").convert("RGB")
        _, _, png = load(reports / replay)
        need(ImageChops.difference(shot, png).getbbox() is None, f"現場 {name} 截圖與已驗重播不符")
        result[f"real_gui_{name}_png_sha256"] = sha(Path(str(gui_prefix) + f".{name}.png").read_bytes())
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱介紹頁正式中文通過")
        return 77
    r = args.reports
    result = {"result": "PASS"}
    result["page_a"] = check_page(r / "zh-53m", r / "control-53m", PAGE_A, 53000000)
    result["page_b"] = check_page(r / "zh-62m", r / "control-62m", PAGE_B, 62000000)
    result.update(check_exit(r / "zh-72m", r / "control-72m"))
    result["negatives"] = [check_negative(r / "neg-missing", "missing-ink"),
                           check_negative(r / "neg-no-masks", "font-mask-unavailable")]
    if (r / "gui-real.json").is_file():
        result.update(check_gui(r / "gui-real", r))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
