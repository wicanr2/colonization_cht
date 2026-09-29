#!/usr/bin/env python3
"""目標172（Issue #44／#46，規格035／038）：獨立核對殖民地畫面內操作路徑的真 GUI、中英同輸入重播與兩個反向對照；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal169_window import string_spans

# 以原版顯示字串的片段辨識各段逐字印字（職業選單標題與清單、建造清單標題與清單）。
DIALOGS = {"profession-title": "Select a Profession", "profession-list": "Farmer", "build-title": "Select An Item To Build",
           "build-list": "ARMORY"}
STRINGS = {"Town Hall", "Food (0 Tons)"}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def dialog_spans(report):
    """通用對話框引擎（非 STRING 串）的啟用區間：(顯示字串, 鍵, 開始, 結束, 安全區)。"""
    src, start, out = {}, {}, []
    for e in report["events"]:
        cid = e.get("candidate_id", "")
        if cid.startswith("STRING:") and not cid.startswith("STRING:line"):
            continue
        if e.get("stage") == "source" and "safe" in e and "shown" in e:
            src[cid] = (e["shown"], e["safe"])
        elif e.get("stage") == "active" and cid in src:
            start[cid] = e["step"]
        elif e.get("stage") == "expired" and cid in start:
            out.append((src[cid][0], cid, start.pop(cid), e["step"], src[cid][1]))
    out += [(src[c][0], c, s, 1 << 62, src[c][1]) for c, s in start.items()]
    return out


def found(spans):
    return {k for k, frag in DIALOGS.items() if any(frag in x[0] for x in spans)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱殖民地操作通過")
        return 77
    r = a.reports
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-colony.shots").read_text().splitlines())]
    raw = (r / "gui-colony.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    noatlas, noyield = load(r / "neg-noatlas"), load(r / "neg-noyield")
    same_state(zh, control, "中英原版狀態不同")
    for neg, name in ((noatlas, "缺字串圖集"), (noyield, "模板缺產量欄")):
        need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], f"{name}反向對照的原版狀態不同")
    for _, s in shots:
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")

    dspans, sspans = dialog_spans(zh[0]), string_spans(zh[0])
    got = found(dspans)
    need(got == set(DIALOGS), f"殖民地操作的逐字段未全部啟用：缺 {sorted(set(DIALOGS) - got)}")
    need(STRINGS <= {k for k, *_ in sspans}, f"懸停標籤未全部啟用：缺 {sorted(STRINGS - {k for k, *_ in sspans})}")
    neg1 = found(dialog_spans(noatlas[0]))
    need(noatlas[0].get("string_reason") == "font-mask-unavailable" and not string_spans(noatlas[0]), "缺字串圖集時字串層不得啟用")
    need("profession-list" not in neg1 and "build-list" not in neg1, "缺字串圖集時清單不應有字串層後備")
    neg2 = found(dialog_spans(noyield[0]))
    need("profession-list" not in neg2 and "build-list" in neg2, f"模板缺產量欄反向對照不符：{sorted(neg2)}")

    checked = {}
    for name, s in shots:
        live = [(x[1], x[4]) for x in dspans if x[2] <= s < x[3]] + [(x[0], x[4]) for x in sspans if x[2] <= s < x[3]]
        for key, safe in live:
            box = tuple(v * 4 for v in safe)
            g = Image.open(r / f"gui-colony.{name}.png").convert("RGB").crop(box)
            z = Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB").crop(box)
            c = Image.open(r / f"replay-control.cp-{s}.png").convert("RGB").crop(box)
            need(ImageChops.difference(g, z).getbbox() is None, f"{name}：{key!r} 真 GUI 與重播不同")
            need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：{key!r} 中文未改變安全區")
            checked.setdefault(name, []).append(key)
    shot_keys = {k for v in checked.values() for k in v}
    need(STRINGS <= shot_keys, f"截到的懸停標籤太少：{sorted(shot_keys)}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "dialogs": sorted(got),
                      "shots": checked, "final_state_sha256": zh[0]["state"]["memory_sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
