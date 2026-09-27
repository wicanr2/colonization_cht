#!/usr/bin/env python3
"""目標166（Issue #42，規格036 與規格034 補充）：獨立核對載入訊息、主選單版本字串、國王接見與 GAME 下拉選單的
真 GUI、中英同輸入重播與兩個反向對照；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

LOADING = "OPENING.TXT:@MESSAGES:loading"
VERSION = "GAME.TXT:0x00000179"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def active_spans(report):
    """通用引擎每一項的 [啟用, 撤銷) 與安全區；鍵以原版字串來源為準。"""
    safe, start, out = {}, {}, []
    for e in report["events"]:
        cid = e.get("candidate_id", "")
        if e.get("stage") == "source" and "safe" in e:
            safe[cid] = e["safe"]
        elif e.get("stage") == "active" and cid in safe:
            start[cid] = e["step"]
        elif e.get("stage") == "expired" and cid in start:
            out.append((cid, start.pop(cid), e["step"], safe[cid]))
    out += [(cid, s, 1 << 62, safe[cid]) for cid, s in start.items()]
    return out


def live(spans, step, pred):
    return [x for x in spans if x[1] <= step < x[2] and pred(x[0])]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱四處動態文字通過")
        return 77
    r = a.reports
    global SHOTS
    SHOTS = {n: int(s) for n, s in (l.split() for l in (r / "gui-spots.shots").read_text().splitlines())}
    need(list(SHOTS) == ["loading", "mainmenu", "king", "gamemenu", "after"], f"截圖清單不符：{list(SHOTS)}")
    raw = (r / "gui-spots.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    nodialog, nostatic = load(r / "neg-nodialog"), load(r / "neg-nostatic")
    same_state(zh, control, "中英原版狀態不同")
    for neg, name in ((nodialog, "缺對話框圖集"), (nostatic, "空靜態字模")):
        need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], f"{name}反向對照的原版狀態不同")
    for s in SHOTS.values():
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")

    spans = active_spans(zh[0])
    expect = {
        "mainmenu": lambda cid: cid == VERSION,
        "king": lambda cid: cid.startswith("GAME.TXT:@VICEROY:"),
        "gamemenu": lambda cid: cid.startswith("MENU.TXT:") and cid.endswith("+list"),
    }
    for name, pred in expect.items():
        need(live(spans, SHOTS[name], pred), f"{name}：檢查點時對應項目未啟用")
    lines = {l["candidate_id"]: l for l in cp(zh[0], SHOTS["loading"])["lines"]}
    need(lines.get(LOADING, {}).get("applied"), "載入訊息未套用")
    need(not live(spans, SHOTS["after"], lambda cid: cid.startswith("MENU.TXT:")), "按 Esc 後下拉選單仍啟用")

    # 反向對照：缺圖集時通用引擎整個回原文；空靜態字模時載入訊息回原文，其餘不受影響。
    need(nodialog[0].get("dialog_reason") == "font-mask-unavailable" and not active_spans(nodialog[0]), "缺對話框圖集時不得啟用")
    nl = {l["candidate_id"]: l for l in cp(nostatic[0], SHOTS["loading"])["lines"]}
    need(not nl.get(LOADING, {}).get("applied") and nl.get(LOADING, {}).get("reason") == "font-mask-unavailable",
         "空靜態字模時載入訊息應回原文")
    need(len(active_spans(nostatic[0])) == len(spans), "空靜態字模不應影響通用引擎")

    shots = {}
    for name, s in SHOTS.items():
        z = Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB")
        c = Image.open(r / f"replay-control.cp-{s}.png").convert("RGB")
        n = Image.open(r / f"neg-nodialog.cp-{s}.png").convert("RGB")
        g = Image.open(r / f"gui-spots.{name}.png").convert("RGB")
        if name in expect:
            box = tuple(v * 4 for v in live(spans, s, expect[name])[0][3])
            need(ImageChops.difference(z.crop(box), c.crop(box)).getbbox() is not None, f"{name}：中文未改變安全區")
            need(ImageChops.difference(n.crop(box), c.crop(box)).getbbox() is None, f"{name}：缺圖集時安全區應與英文相同")
            need(ImageChops.difference(g.crop(box), z.crop(box)).getbbox() is None, f"{name}：真 GUI 與重播的安全區不同")
        d = ImageChops.difference(g, z).getbbox()
        shots[name] = {"png_sha256": hashlib.sha256((r / f"gui-spots.{name}.png").read_bytes()).hexdigest(),
                       "diff_vs_replay_bbox": list(d) if d else None}
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(),
                      "active": [[x[0], x[1], x[2], x[3]] for x in spans],
                      "final_state_sha256": zh[0]["state"]["memory_sha256"], "shots": shots}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
