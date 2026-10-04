#!/usr/bin/env python3
"""目標180：其餘百科逐篇正常 GUI、中英同狀態與缺圖集負例。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal134_window import load, same_state
from check_goal171_window import dialog_spans
from check_goal179_window import INPUT_SHA, SAVE_SHA, need, observed_strings

CATEGORIES = {
    "unit": ("UNIT", set(range(23)), 23),
    # 正常 GUI 收據的模板鍵；同文同譯時引擎選最後一個模板。
    # 這不是原版段落位移歸屬證據，等價鍵說明見目標180。
    "terrain": ("TERRAIN", set(range(8)) | {12, 13, 14, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28}, 21),
    "job": ("JOB", set(range(28)) - {18}, 27),
    "building": ("BUILDING", set(range(42)) - {10, 11, 30, 31}, 38),
    "father": ("FATHER", set(range(25)), 25),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--category", choices=CATEGORIES, required=True)
    p.add_argument("--require-no-string-misses", action="store_true",
                   help="最終欄位驗收須沒有未翻譯字串；舊部分驗收保留原範圍")
    p.add_argument("--require-pedia-fields", action="store_true",
                   help="建築先決條件22欄須實際啟用，不能只看來源匹配")
    a = p.parse_args()
    r = a.reports
    if not all((a.game / f).is_file() for f in INPUT_SHA) or not (r / "scratch/COLONY00.SAV").is_file():
        print("SKIP：缺合法原版或正常存檔入口，未宣稱完成")
        return 77
    for name, expected in INPUT_SHA.items():
        need(hashlib.sha256((a.game / name).read_bytes()).hexdigest() == expected, f"{name} 原版指紋不同")
    need(hashlib.sha256((r / "scratch/COLONY00.SAV").read_bytes()).hexdigest() == SAVE_SHA, "正常存檔指紋不同")
    gui, zh, control, neg = (load(r / n) for n in ("gui-pedia", "replay-zh", "replay-control", "neg-noatlas"))
    same_state(zh, control, "中英完整原版狀態不同")
    for name in ("OPENING.EXE", "VICEROY.EXE"):
        need(zh[0]["input_hashes"].get(name) == INPUT_SHA[name], f"{name} 收據指紋不同")
    for other, name in ((gui, "真 GUI"), (neg, "缺圖集負例")):
        need(other[0]["state"] == zh[0]["state"] and other[0]["input_hashes"] == zh[0]["input_hashes"] and
             other[0]["opened"] == zh[0]["opened"] and other[1] == zh[1], f"{name} 完整原版狀態不同")
    raw = (r / "gui-pedia.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "真 GUI 有拒絕輸入")
    prefix, ids, count = CATEGORIES[a.category]
    allowed = {f"PEDIA.TXT:@{prefix}{i}" for i in ids}
    spans = [s for s in dialog_spans(zh[0]) if s[0].startswith("PEDIA.TXT:")]
    got = {s[0] for s in spans}
    need(got <= allowed and len(got) == count, f"正文來源鍵不足或異常：{sorted(got)}")
    need(neg[0]["dialog_reason"] == "font-mask-unavailable" and not dialog_spans(neg[0]), "缺圖集負例仍啟用正文")
    cps, controls, negatives = ({c["label"]: c for c in v[0]["checkpoints"]} for v in (zh, control, neg))
    strings = observed_strings(zh[0])
    misses = zh[0].get("string_misses") or {}
    if a.require_no_string_misses:
        need(not misses, f"仍有未翻譯字串：{misses}")
    if a.require_pedia_fields:
        need(a.category == "building", "先決條件驗收只適用建築類")
        expected = {e["shown"] for e in zh[0]["events"]
                    if e.get("candidate_id") == "STRING:template:pedia-prerequisite"
                    and e.get("stage") == "source"}
        activated = {text for text, cid, lo, hi, safe in strings
                     if cid == "STRING:template:pedia-prerequisite"}
        need(len(expected) == 22 and activated == expected,
             f"先決條件來源{len(expected)}欄，實際啟用{len(activated)}欄，缺{sorted(expected - activated)}")
    articles, checked_strings, checked_prerequisites = {}, set(), set()
    for line in (r / "gui-pedia.shots").read_text().splitlines():
        name, step = line.split()
        label, step = "cp-" + step, int(step)
        need(label in cps and label in controls and label in negatives, f"{name} 缺檢查點")
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            need(cps[label][key] == controls[label][key] == negatives[label][key], f"{name} 原版 {key} 不同")
        if not name.startswith(a.category + "-"):
            continue
        images = [Image.open(r / f).convert("RGB") for f in
                  (f"gui-pedia.{name}.png", f"replay-zh.{label}.png", f"replay-control.{label}.png")]
        active = [(cid, safe) for cid, lo, hi, safe in spans if lo <= step < hi]
        if name.startswith(a.category + "-article-"):
            need(len(active) == 1, f"{name} 沒有唯一啟用正文")
            cid = active[0][0]
            need(cid not in articles, f"{name} 重複開啟正文 {cid}")
            articles[cid] = name
            checked_prerequisites.update(text for text, cid, lo, hi, safe in strings
                                         if cid == "STRING:template:pedia-prerequisite" and lo <= step < hi)
        fields = active + [(cid, safe) for text, cid, lo, hi, safe in strings if lo <= step < hi]
        for cid, safe in fields:
            box = tuple(x * 4 for x in safe)
            g, z, c = (im.crop(box) for im in images)
            need(ImageChops.difference(g, z).getbbox() is None, f"{name} {cid} 真 GUI 安全區不同")
            need(ImageChops.difference(z, c).getbbox() is not None, f"{name} {cid} 沒有中文")
        checked_strings.update(text for text, cid, lo, hi, safe in strings if lo <= step < hi)
    need(set(articles) == got, "沒有逐篇截到全部啟用正文")
    if a.require_pedia_fields:
        need(checked_prerequisites == expected, "先決條件沒有在全部正常GUI逐篇取樣點啟用")
    print(json.dumps({"result": "PASS", "category": a.category, "articles": articles,
                      "string_fields": len(checked_strings), "inputs_sha256": hashlib.sha256(raw).hexdigest(),
                      "string_misses": misses,
                      "input_fingerprints": INPUT_SHA, "save_sha256": SAVE_SHA,
                      "final_state_sha256": zh[0]["state"]["memory_sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
