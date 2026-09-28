#!/usr/bin/env python3
"""目標171（Issue #44，規格036／038）：獨立核對殖民百科路徑的真 GUI、中英同輸入重播與兩個反向對照；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal169_window import string_spans

# 六個類別的首篇條目正文（通用引擎以百科雙語稿鍵啟用）與清單頁標題。
EXPECTED_ARTICLES = {"PEDIA.TXT:@CARGO10"}
EXPECTED_STRINGS = {"ENCYCLOPEDIA OF COLONIZATION"}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def dialog_spans(report):
    safe, start, out = {}, {}, []
    for e in report["events"]:
        cid = e.get("candidate_id", "")
        if cid.startswith("STRING") or not cid.startswith(("PEDIA.TXT", "GAME.TXT")):
            continue
        if e.get("stage") == "source" and "safe" in e:
            safe[cid] = e["safe"]
        elif e.get("stage") == "active" and cid in safe:
            start[cid] = e["step"]
        elif e.get("stage") == "expired" and cid in start:
            out.append((cid, start.pop(cid), e["step"], safe[cid]))
    out += [(cid, s, 1 << 62, safe[cid]) for cid, s in start.items()]
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱殖民百科通過")
        return 77
    r = a.reports
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-pedia.shots").read_text().splitlines())]
    raw = (r / "gui-pedia.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    noatlas, nocigars = load(r / "neg-noatlas"), load(r / "neg-nocigars")
    same_state(zh, control, "中英原版狀態不同")
    for neg, name in ((noatlas, "缺對話框圖集"), (nocigars, "百科稿缺 Cigars")):
        need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], f"{name}反向對照的原版狀態不同")
    for _, s in shots:
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")

    articles = dialog_spans(zh[0])
    pedia = {x[0] for x in articles if x[0].startswith("PEDIA.TXT")}
    need(len(pedia) >= 6 and EXPECTED_ARTICLES <= pedia, f"百科條目啟用不足：{sorted(pedia)}")
    strings = string_spans(zh[0])
    need(EXPECTED_STRINGS <= {k for k, *_ in strings}, "清單頁標題未啟用")
    need(noatlas[0].get("dialog_reason") == "font-mask-unavailable" and not dialog_spans(noatlas[0]), "缺圖集時正文不得啟用")
    # 字串層依賴通用對話框引擎載入成功（規格038：--string-a 需同時啟用 --dialog-a），缺對話框圖集時一併回原文。
    need(noatlas[0].get("string_reason") == "dialog-catalog-unavailable" and not string_spans(noatlas[0]), "缺對話框圖集時字串層應一併回原文")
    neg = {x[0] for x in dialog_spans(nocigars[0])}
    need("PEDIA.TXT:@CARGO10" not in neg and (pedia - {"PEDIA.TXT:@CARGO10"}) <= neg, f"百科稿缺 Cigars 反向對照不符：{sorted(neg)}")

    checked = {}
    for name, s in shots:
        live = [(x[0], x[3]) for x in articles if x[1] <= s < x[2]] + [(x[0], x[4]) for x in strings if x[2] <= s < x[3]]
        for key, safe in live:
            box = tuple(v * 4 for v in safe)
            g = Image.open(r / f"gui-pedia.{name}.png").convert("RGB").crop(box)
            z = Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB").crop(box)
            c = Image.open(r / f"replay-control.cp-{s}.png").convert("RGB").crop(box)
            need(ImageChops.difference(g, z).getbbox() is None, f"{name}：{key!r} 真 GUI 與重播不同")
            need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：{key!r} 中文未改變安全區")
            checked.setdefault(name, []).append(key)
    got = {k for v in checked.values() for k in v}
    need(len({k for k in got if k.startswith("PEDIA.TXT")}) >= 6, f"截到的百科條目太少：{sorted(got)}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "articles": sorted(pedia),
                      "shots": checked, "final_state_sha256": zh[0]["state"]["memory_sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
