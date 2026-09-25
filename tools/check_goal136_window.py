#!/usr/bin/env python3
"""獨立核對規格025法國、西班牙、荷蘭首次介紹兩頁的現場輸入同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal135_window import PANEL, lines, load, page_events, same_state


# 國家 → (訊息鍵前綴, A 頁可見字／改色點數, B 頁可見字／改色點數)；取自目標101／102 已證實收據。
NATIONS = {
    "france": ("GAME.TXT:@NATION1", (794, 13412), (207, 3438)),
    "spain": ("GAME.TXT:@NATION2", (953, 16103), (180, 3168)),
    "netherlands": ("GAME.TXT:@NATION3", (957, 16401), (299, 5262)),
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_page(reports, nation, phase, steps):
    key, a, b = NATIONS[nation]
    page = key + phase
    chars, writes = a if phase == "A" else b
    tag = f"{steps // 1000000}m"
    live, control = load(reports / f"{nation}-zh-{tag}"), load(reports / f"{nation}-control-{tag}")
    same_state(live, control, f"{page}：中文與英文控制的原版狀態不同")
    report = live[0]
    last = lines(report["frames"][-1])
    need(last[page]["applied"] and sum(1 for k, v in last.items() if k.startswith("GAME.TXT:@NATION") and v["applied"]) == 1,
         f"{page}：終點畫格沒有中文或其他頁誤套用")
    actives = [e for e in page_events(report) if e["stage"] == "active" and e["candidate_id"] == page]
    need(actives and all(e["visible_chars"] == chars and e["changed_pixels"] == writes for e in actives),
         f"{page}：啟用事件的可見字數或改色點數不符")
    first = min(e["step"] for e in actives)
    sources = [e for e in page_events(report) if e["stage"] == "source" and e["step"] < first]
    need(sources and sources[-1]["source_linear"] == 0x2A862, f"{page}：缺當次整頁印字來源事件")
    for frame in report["frames"]:
        line = lines(frame).get(page)
        if line and line["applied"]:
            need(frame["step"] >= first, f"{page}：真 VGA 同步前就套用中文")
    outside = live[2].copy()
    outside.paste(control[2].crop(PANEL), PANEL)
    need(ImageChops.difference(outside, control[2]).getbbox() is None and
         ImageChops.difference(live[2], control[2]).getbbox() is not None,
         f"{page}：中文越出頁內或未繪製")
    return {"active_step": first, "state_sha256": report["state"]["memory_sha256"]}


def check_exit(reports, nation):
    key = NATIONS[nation][0]
    live, control = load(reports / f"{nation}-zh-75m"), load(reports / f"{nation}-control-75m")
    same_state(live, control, f"{nation}：離頁後中英原版狀態不同")
    last = lines(live[0]["frames"][-1])
    expired = [e for e in page_events(live[0]) if e["stage"] == "expired" and e["candidate_id"] == key + "B"]
    need(expired and not any(v["applied"] for k, v in last.items() if k.startswith("GAME.TXT:@NATION")) and
         ImageChops.difference(live[2], control[2]).getbbox() is None, f"{nation}：離頁後仍殘留中文")
    return {"exit_step": expired[-1]["step"], "exit_state_sha256": live[0]["state"]["memory_sha256"]}


def check_gui(reports, nation):
    gui = reports / f"gui-{nation}"
    report = json.loads(Path(str(gui) + ".json").read_text())
    inputs = Path(str(gui) + ".inputs.json").read_bytes()
    need(not json.loads(inputs).get("rejected"), f"{nation}：現場輸入有被拒絕")
    need(lines(report["frames"][-1])[NATIONS[nation][0] + "B"]["applied"], f"{nation}：現場終點 B 頁沒有中文")
    result = {"inputs_sha256": sha(inputs)}
    for name, tag in (("page-a", "56m"), ("page-b", "64m")):
        shot = Image.open(str(gui) + f".{name}.png").convert("RGB")
        _, _, png = load(reports / f"{nation}-zh-{tag}")
        need(ImageChops.difference(shot, png).getbbox() is None, f"{nation}：現場 {name} 截圖與重播不符")
        result[f"{name}_png_sha256"] = sha(Path(str(gui) + f".{name}.png").read_bytes())
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱介紹頁正式中文通過")
        return 77
    result = {"result": "PASS"}
    for nation in NATIONS:
        result[nation] = {"page_a": check_page(args.reports, nation, "A", 56000000),
                          "page_b": check_page(args.reports, nation, "B", 64000000),
                          **check_exit(args.reports, nation), "gui": check_gui(args.reports, nation)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
