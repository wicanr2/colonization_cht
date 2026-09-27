#!/usr/bin/env python3
"""目標167（Issue #43，規格035）：獨立核對教學提示路徑的真 GUI、中英同輸入重播與兩個反向對照；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

# 本路徑觸發的教學提示（首則由規格026 專屬欄位處理，不在此列）。
EXPECTED = {"@TUTORIAL2", "@TUTORIAL5", "@TUTORIAL11", "@TUTORIAL13", "@TUTORIAL14"}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def spans(report):
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


def section(cid):
    return cid.split(":")[1] if cid.count(":") >= 1 else cid


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱教學提示通過")
        return 77
    r = a.reports
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-tutorial.shots").read_text().splitlines())]
    raw = (r / "gui-tutorial.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    noatlas, nohelp = load(r / "neg-noatlas"), load(r / "neg-nohelp")
    same_state(zh, control, "中英原版狀態不同")
    for neg, name in ((noatlas, "缺對話框圖集"), (nohelp, "缺教學提示譯稿")):
        need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], f"{name}反向對照的原版狀態不同")
    for _, s in shots:
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")

    active = spans(zh[0])
    tutorials = {section(x[0]) for x in active if section(x[0]).startswith("@TUTORIAL")}
    need(EXPECTED <= tutorials, f"教學提示未全部啟用：缺 {sorted(EXPECTED - tutorials)}")
    others = sorted({section(x[0]) for x in active} - tutorials)
    need(not spans(noatlas[0]) and noatlas[0].get("dialog_reason") == "font-mask-unavailable", "缺圖集時不得啟用")
    neg_active = {section(x[0]) for x in spans(nohelp[0])}
    need(not {s for s in neg_active if s.startswith("@TUTORIAL")}, f"缺教學提示譯稿時仍啟用 {sorted(neg_active)}")
    need(set(others) <= neg_active, "缺教學提示譯稿不應影響其他訊息")

    checked = {}
    for name, s in shots:
        live = [x for x in active if x[1] <= s < x[2]]
        if not live:
            continue
        box = tuple(v * 4 for v in live[0][3])
        g = Image.open(r / f"gui-tutorial.{name}.png").convert("RGB").crop(box)
        z = Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB").crop(box)
        c = Image.open(r / f"replay-control.cp-{s}.png").convert("RGB").crop(box)
        need(ImageChops.difference(g, z).getbbox() is None, f"{name}：真 GUI 與重播的安全區不同")
        need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：中文未改變安全區")
        checked[name] = {"dialog": section(live[0][0]), "step": s,
                         "png_sha256": hashlib.sha256((r / f"gui-tutorial.{name}.png").read_bytes()).hexdigest()}
    need({v["dialog"] for v in checked.values()} >= EXPECTED,
         f"截到的對話框太少：{sorted(v['dialog'] for v in checked.values())}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "tutorials": sorted(tutorials),
                      "other_dialogs": others, "shots": checked, "final_state_sha256": zh[0]["state"]["memory_sha256"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
