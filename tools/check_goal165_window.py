#!/usr/bin/env python3
"""目標165（Issue #41，規格035）：獨立核對通用對話框的真 GUI、中英同輸入重播與兩個反向對照；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

POINTS = [690000000, 830000000, 870000000, 885000000, 900000000, 920000000]
SHOTS = {"landho": 690000000, "landfall": 830000000, "welcome": 870000000, "peace": 885000000, "come": 900000000,
         "after": 920000000}
EXPECTED = ["@LANDHO", "@LANDFALL", "@INDIANWELCOME", "@INDIANPEACE", "@INDIANCOME"]
# 登陸詢問依船停靠位置而定：海岸為 @LANDFALL，河道為 @LANDFALL2（同一對話框類型）。
LANDFALLS = {"@LANDFALL", "@LANDFALL2"}


def norm(seq):
    return ["@LANDFALL" if x in LANDFALLS else x for x in seq]
NATIVE = {"@INDIANWELCOME", "@INDIANPEACE", "@INDIANCOME"}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def section(candidate):
    return candidate.split(":")[1]


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def spans(report):
    """每則對話框的 [啟用步數, 撤銷步數) 與安全區（320×200）。"""
    out, safe, start = [], {}, {}
    for e in report["events"]:
        cid = e.get("candidate_id", "")
        if e.get("stage") == "source" and "safe" in e:
            safe[cid] = e["safe"]
        elif e.get("stage") == "active" and cid in safe:
            start[cid] = e["step"]
        elif e.get("stage") == "expired" and cid in start:
            out.append((section(cid), start.pop(cid), e["step"], safe[cid], e["reason"]))
    for cid, s in start.items():
        out.append((section(cid), s, 1 << 62, safe[cid], "still-active"))
    return out


def inside(bbox, rect):
    return bbox is None or (bbox[0] >= rect[0] * 4 and bbox[1] >= rect[1] * 4 and bbox[2] <= rect[2] * 4 and bbox[3] <= rect[3] * 4)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱通用對話框通過")
        return 77
    r = a.reports
    raw = (r / "gui-dialog.inputs.json").read_bytes()
    gui = json.loads(raw)
    need(not gui.get("rejected"), "現場輸入有被拒絕")
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    noatlas, noterm = load(r / "neg-noatlas"), load(r / "neg-noterm")
    same_state(zh, control, "中英原版狀態不同")
    for neg, name in ((noatlas, "缺圖集"), (noterm, "缺譯名")):
        need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], f"{name}反向對照的原版狀態不同")
    for s in POINTS:
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")

    # 中文：五則依序啟用，全部以畫布改變撤銷（玩家按鍵關閉）；每個檢查點的差異只在當時啟用的安全區內。
    active = spans(zh[0])
    need(norm([x[0] for x in active]) == EXPECTED, f"啟用序列不符：{[x[0] for x in active]}")
    need(all(x[4] == "canvas-page-changed" for x in active), f"撤銷原因不符：{[x[4] for x in active]}")
    frames = {}
    for s in POINTS:
        z = Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB")
        c = Image.open(r / f"replay-control.cp-{s}.png").convert("RGB")
        frames[s] = z
        bbox = ImageChops.difference(z, c).getbbox()
        live = [x for x in active if x[1] <= s < x[2]]
        if live:
            need(bbox is not None and inside(bbox, live[0][3]), f"{s}：中文差異 {bbox} 不在 {live[0][0]} 安全區 {live[0][3]}")
        else:
            need(bbox is None, f"{s}：無對話框時中英畫面不同 {bbox}")
        n = Image.open(r / f"neg-noatlas.cp-{s}.png").convert("RGB")
        need(ImageChops.difference(n, c).getbbox() is None, f"{s}：缺圖集時畫面應與英文控制相同")
    need(noatlas[0].get("dialog_reason") == "font-mask-unavailable", "缺圖集原因不符")
    need(not [e for e in noatlas[0]["events"] if e.get("stage") == "active"], "缺圖集時不得啟用")
    # 缺譯名：原住民三則回原文並記原因，其餘兩則照常中文。
    neg_active = [x[0] for x in spans(noterm[0])]
    need(norm(neg_active) == ["@LANDHO", "@LANDFALL"], f"缺譯名時啟用序列不符：{neg_active}")
    fallbacks = [e for e in noterm[0]["events"] if e.get("stage") == "fallback" and e["reason"] == "variable-without-term"]
    native = [e["shown"] for e in zh[0]["events"] if e.get("stage") == "source" and section(e["candidate_id"]) in NATIVE]
    need(len(native) == 3 and [e["shown"] for e in fallbacks] == native, f"缺譯名回退不符：{len(fallbacks)}")

    # 真 GUI 截圖：對話框安全區內與同輸入中文重播逐像素相同。
    shots = {}
    for name, s in SHOTS.items():
        g = Image.open(r / f"gui-dialog.{name}.png").convert("RGB")
        d = ImageChops.difference(g, frames[s]).getbbox()
        live = [x for x in active if x[1] <= s < x[2]]
        if live:
            box = tuple(v * 4 for v in live[0][3])
            need(ImageChops.difference(g.crop(box), frames[s].crop(box)).getbbox() is None,
                 f"{name}：真 GUI 與重播的對話框安全區不同")
        shots[name] = {"png_sha256": hashlib.sha256((r / f"gui-dialog.{name}.png").read_bytes()).hexdigest(),
                       "dialog": live[0][0] if live else None, "diff_vs_replay_bbox": list(d) if d else None}
    need(norm([shots[k]["dialog"] for k in ("landho", "landfall", "welcome", "peace", "come")]) == EXPECTED,
         f"截圖時點的對話框不符：{[shots[k]['dialog'] for k in shots]}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(),
                      "active": [[x[0], x[1], x[2], x[3]] for x in active],
                      "final_state_sha256": zh[0]["state"]["memory_sha256"], "shots": shots}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
