#!/usr/bin/env python3
"""目標170（Issue #44，規格038）：獨立核對歐洲港口與顧問報告路徑的真 GUI、中英同輸入重播與兩個反向對照；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

# 本路徑必須中文化並啟用的字串（以原文比對；港口標題以模板鍵比對，年份與金額隨路徑而定）。
EXPECTED = {"RECRUIT", "PURCHASE", "TRAIN", "Bound For", "Expected Soon", "LABOR ADVISER REPORT", "ECONOMIC ADVISER REPORT",
            "COLONY ADVISER REPORT", "NAVAL ADVISER REPORT", "FOREIGN AFFAIRS REPORT", "INDIAN ADVISER REPORT",
            "COLONIZATION SCORE", "CONTINENTAL CONGRESS ACTIVITIES", "RELIGIOUS ADVISER REPORT", "OK"}
TITLE = "STRING:template:port-title"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def string_spans(report):
    """依事件重建每串的啟用區間：(原文, 鍵, 開始, 結束, 安全區)；同一原文可有多段（暫停後恢復）。"""
    safe, start, out = {}, {}, []
    for e in report["events"]:
        cid = e.get("candidate_id", "")
        if not cid.startswith("STRING"):
            continue
        k = e.get("shown")
        if e["stage"] == "source":
            safe[k] = (cid, e["safe"])
        elif e["stage"] == "active" and k in safe:
            start[k] = e["step"]
        elif e["stage"] in ("suspended", "expired") and k in start:
            out.append((k, safe[k][0], start.pop(k), e["step"], safe[k][1]))
    out += [(k, safe[k][0], s, 1 << 62, safe[k][1]) for k, s in start.items()]
    return out


def dialog_sections(report):
    return {e["candidate_id"].split(":")[1] for e in report["events"]
            if e.get("stage") == "active" and e.get("candidate_id", "").count(":") >= 1
            and not e["candidate_id"].startswith("STRING")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱歐洲港口與報告通過")
        return 77
    r = a.reports
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-eu.shots").read_text().splitlines())]
    raw = (r / "gui-eu.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control = load(r / "replay-zh"), load(r / "replay-control")
    noatlas, notitle = load(r / "neg-noatlas"), load(r / "neg-noport")
    same_state(zh, control, "中英原版狀態不同")
    for neg, name in ((noatlas, "缺字串圖集"), (notitle, "模板缺港口標題")):
        need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], f"{name}反向對照的原版狀態不同")
    for _, s in shots:
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")

    spans = string_spans(zh[0])
    texts = {k for k, *_ in spans}
    need(EXPECTED <= texts, f"字串未全部啟用：缺 {sorted(EXPECTED - texts)}")
    titles = [x for x in spans if x[1] == TITLE]
    need(titles, "港口標題未啟用")
    title = titles[0][0]
    resumed = [e for e in zh[0]["events"] if e.get("reason") == "canvas-restored" and e.get("shown") in EXPECTED | {title}]
    need(resumed, "港口對話框關閉、原版整塊還原後沒有字串恢復中文")

    need(zh[0].get("string_reason") == "", "字串層未載入")
    need(noatlas[0].get("string_reason") == "font-mask-unavailable" and not string_spans(noatlas[0]), "缺圖集時字串層不得啟用")
    need(dialog_sections(noatlas[0]) == dialog_sections(zh[0]), "缺字串圖集不應影響對話框")
    neg_spans = string_spans(notitle[0])
    need(not [x for x in neg_spans if x[0] == title], "模板缺港口標題時標題仍啟用")
    need(notitle[0]["string_misses"].get("no-template\t" + title), "模板缺港口標題應記錄缺譯")
    need(EXPECTED <= {k for k, *_ in neg_spans}, "模板缺標題不應影響其他字串")

    checked = {}
    for name, s in shots:
        live = [x for x in spans if x[2] <= s < x[3]]
        for text, cid, _, _, safe in live:
            box = tuple(v * 4 for v in safe)
            g = Image.open(r / f"gui-eu.{name}.png").convert("RGB").crop(box)
            z = Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB").crop(box)
            c = Image.open(r / f"replay-control.cp-{s}.png").convert("RGB").crop(box)
            need(ImageChops.difference(g, z).getbbox() is None, f"{name}：{text!r} 真 GUI 與重播不同")
            need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：{text!r} 中文未改變安全區")
            checked.setdefault(name, []).append(text)
    got = {t for v in checked.values() for t in v}
    need(EXPECTED <= got and title in got, f"截到的字串太少：{sorted(got)}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "strings": sorted(texts),
                      "title": title, "shots": checked, "final_state_sha256": zh[0]["state"]["memory_sha256"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
