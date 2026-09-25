#!/usr/bin/env python3
"""獨立核對規格031遊戲選項八列（與規格030標題）的同輸入前端收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


ROWS = [f"GAME.TXT:0x{offset:08X}" for offset in (0x4E9, 0x4FD, 0x512, 0x525, 0x533, 0x53E, 0x550, 0x566)]
TITLE = "GAME.TXT:0x000004CD"
GROUP = "GAME.TXT:options-rows"
BACKGROUNDS = {
    "3c24c328cb52d0ddfe5da07f462e685f9d41c89fabad06722a38095ff0078947",
    "903ff7549ac31fbb35f8a978ed3072aa4d6c7ab035dcea9ede983aea48490159",
    "a37541c55677774da71ee04095a82752663fd9e0a24bbaf671d79134a8627bff",
    "96f7592f13131bb6eaf8128df7a612867459f9abe14ebedf18d3810405180807",
}
# 四倍輸出的標題與八列安全矩形（半開）。
SAFES = [(260, 176, 1012, 236)] + [(320, 236 + 48 * i, 1008, 284 + 48 * i) for i in range(8)]


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(prefix):
    data = json.loads(Path(str(prefix) + ".json").read_text())
    files = {ext: Path(str(prefix) + "." + ext).read_bytes() for ext in ("memory", "final.idx", "final.pal")}
    return data, files, Image.open(str(prefix) + ".final.png").convert("RGB")


def last_lines(report):
    return {line["candidate_id"]: line for line in report["frames"][-1]["lines"]}


def same_state(live, control, why):
    (a, fa, pa), (b, fb, pb) = live, control
    need(a["control"] is False and b["control"] is True and a["state"] == b["state"] and
         a["opened"] == b["opened"] and a["input_hashes"] == b["input_hashes"] and fa == fb and
         len(a["frames"]) == len(b["frames"]) and pa.size == pb.size == (1280, 800), why)


def diff_only_in_safes(live_png, control_png):
    outside = live_png.copy()
    for box in SAFES:
        outside.paste(control_png.crop(box), box)
    return ImageChops.difference(outside, control_png).getbbox() is None


def row_events(report):
    return [e for e in report["events"] if e.get("candidate_id") in ROWS or e.get("candidate_id") == GROUP]


def check_active(live_prefix, control_prefix, steps):
    live, control = load(live_prefix), load(control_prefix)
    same_state(live, control, "中文與英文控制的原版狀態、輸入或完整記憶體不同")
    report = live[0]
    need(report["state"]["steps"] == steps, "終點步數不符")
    lines = last_lines(report)
    need(all(lines[key]["applied"] for key in ROWS) and lines[TITLE]["applied"],
         "終點畫格八列或標題沒有中文")
    events = row_events(report)
    sources = [e for e in events if e["candidate_id"] == GROUP and e["stage"] == "source"]
    actives = [e for e in events if e["stage"] == "active"]
    need(sources and all(e["entry_ip"] == "0D21:00C6" and e["source_linear"] in (0x2ADDE, 0x2AE46)
                         for e in sources), "缺整組八列當次來源事件或位址不符")
    need({e["candidate_id"] for e in actives} == set(ROWS) and
         all(e["background_sha256"] in BACKGROUNDS and e["step"] > sources[0]["step"] for e in actives),
         "八列啟用事件、當次底圖或時序不符")
    first_active = {key: min(e["step"] for e in actives if e["candidate_id"] == key) for key in ROWS}
    for frame in report["frames"]:
        for line in frame["lines"]:
            if line["candidate_id"] in ROWS and line["applied"]:
                need(frame["step"] >= first_active[line["candidate_id"]], "真 VGA 同步前就套用中文")
    need(diff_only_in_safes(live[2], control[2]) and
         ImageChops.difference(live[2], control[2]).getbbox() is not None,
         "中文像素越出九欄安全區或完全未繪製")
    return {"state_sha256": report["state"]["memory_sha256"], "row_sources": len(sources),
            "row_active_events": len(actives),
            "row_applied_frames": {key: sum(any(l["candidate_id"] == key and l["applied"] for l in f["lines"])
                                            for f in report["frames"]) for key in ROWS}}


def check_exit(live_prefix, control_prefix):
    live, control = load(live_prefix), load(control_prefix)
    same_state(live, control, "ESC 離窗後中英原版狀態或完整記憶體不同")
    lines = last_lines(live[0])
    expired = [e for e in row_events(live[0]) if e["stage"] == "expired" and e["candidate_id"] in ROWS]
    need(all(not lines[key]["applied"] and lines[key]["reason"] == "expired" for key in ROWS) and
         {e["candidate_id"] for e in expired} >= set(ROWS) and
         ImageChops.difference(live[2], control[2]).getbbox() is None,
         "ESC 離窗後八列仍殘留中文或未撤銷")
    return {"exit_state_sha256": live[0]["state"]["memory_sha256"]}


def check_negative(prefix, reason, broken=None):
    """broken 為被竄改的列；該列須為 reason，其餘列因整份 TSV 雜湊改變須為字模綁定不符。"""
    report = json.loads(Path(str(prefix) + ".json").read_text())
    lines = last_lines(report)
    for key in ROWS:
        want = reason if broken in (None, key) else "font-binding-mismatch"
        need(not lines[key]["applied"] and lines[key]["reason"] == want,
             f"負例 {Path(prefix).name} 的 {key} 未以 {want} 回退原文")
    return Path(prefix).name


def check_gui(gui_prefix, replay_prefix, replay_control_prefix, active_prefix):
    gui = json.loads(Path(str(gui_prefix) + ".json").read_text())
    inputs_data = Path(str(gui_prefix) + ".inputs.json").read_bytes()
    need(not json.loads(inputs_data).get("rejected"), "現場輸入有被拒絕")
    need(all(last_lines(gui)[key]["applied"] for key in ROWS), "現場視窗終點八列沒有中文")
    replay, replay_control = load(replay_prefix), load(replay_control_prefix)
    same_state(replay, replay_control, "現場輸入重播的中英原版狀態不同")
    need(diff_only_in_safes(replay[2], replay_control[2]), "現場輸入重播的中文越出安全區")
    groups = [e for e in row_events(replay[0]) if e["candidate_id"] == GROUP and e["stage"] == "source"]
    need(len(groups) >= 2 and any(e["source_linear"] == 0x2AE46 for e in groups), "現場點擊後沒有重印事件")
    shots = {}
    for name in ("options", "clicked"):
        shot = Image.open(str(gui_prefix) + f".{name}.png").convert("RGB")
        shots[name] = shot
    _, _, active_png = load(active_prefix)
    need(ImageChops.difference(shots["options"], active_png).getbbox() is None,
         "開窗現場截圖與已驗1280M中文重播不符")
    gui_final = Image.open(str(gui_prefix) + ".final.png").convert("RGB")
    need(ImageChops.difference(gui_final, replay[2]).getbbox() is None,
         "現場視窗終點畫面與同輸入重播不符")
    need(ImageChops.difference(shots["clicked"], gui_final).getbbox() is None,
         "點擊後現場截圖與終點畫面不符")
    return {"real_gui_inputs_sha256": sha(inputs_data),
            "real_gui_options_png_sha256": sha(Path(str(gui_prefix) + ".options.png").read_bytes()),
            "real_gui_clicked_png_sha256": sha(Path(str(gui_prefix) + ".clicked.png").read_bytes()),
            "real_gui_row_groups": len(groups)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱八列正式中文通過")
        return 77
    r = args.reports
    result = {"result": "PASS"}
    result.update(check_active(r / "zh-1280m", r / "control-1280m", 1280000000))
    result.update(check_exit(r / "zh-full", r / "control-full"))
    result["negatives"] = [check_negative(r / "neg-missing-ink", "missing-ink"),
                           check_negative(r / "neg-no-fonts", "font-mask-unavailable")] + [
        check_negative(r / f"neg-{variant}", "missing-or-invalid-translation", key)
        for variant, key in (("blank", ROWS[0]), ("duplicate", ROWS[1]),
                             ("wrong-hotkey", ROWS[2]), ("no-hotkey", ROWS[3]))]
    if (r / "gui-real.json").is_file():
        result.update(check_gui(r / "gui-real", r / "gui-replay-zh", r / "gui-replay-control", r / "zh-1280m"))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
