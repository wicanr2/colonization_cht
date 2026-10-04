#!/usr/bin/env python3
"""目標179（Issue #57）：正常 GUI 逐篇貨物百科的中英同狀態與缺圖集反向對照。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal134_window import load, same_state
from check_goal171_window import dialog_spans

EXPECTED = {f"PEDIA.TXT:@CARGO{i}" for i in range(16)}
SAVE_SHA = "cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e"
INPUT_SHA = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "PEDIA.TXT": "cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1",
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def observed_strings(report):
    """保守重建字串啟用區間；新來源先關閉舊區間，不沿用不同頁的安全區。"""
    sources, starts, out = {}, {}, []
    for e in report["events"]:
        cid, text = e.get("candidate_id", ""), e.get("shown")
        if not cid.startswith("STRING") or text is None:
            continue
        key = (cid, text)
        stage = e.get("stage")
        if stage in ("source", "suspended", "expired") and key in starts:
            out.append((text, cid, starts.pop(key), e["step"], sources[key]))
        if stage == "source":
            sources[key] = e["safe"]
        elif stage == "active" and key in sources and key not in starts:
            starts[key] = e["step"]
        elif stage == "expired":
            sources.pop(key, None)
    out.extend((text, cid, step, 1 << 62, sources[(cid, text)]) for (cid, text), step in starts.items())
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    r = a.reports
    if not all((a.game / f).is_file() for f in INPUT_SHA) or not (r / "scratch/COLONY00.SAV").is_file():
        print("SKIP：缺合法原版或正常 GUI 存檔入口，未宣稱百科通過")
        return 77
    for name, expected in INPUT_SHA.items():
        need(hashlib.sha256((a.game / name).read_bytes()).hexdigest() == expected, f"{name} 原版指紋不同")
    need(hashlib.sha256((r / "scratch/COLONY00.SAV").read_bytes()).hexdigest() == SAVE_SHA,
         "正常存檔入口指紋不同")
    gui, zh, control, neg = (load(r / n) for n in ("gui-pedia", "replay-zh", "replay-control", "neg-noatlas"))
    same_state(zh, control, "百科中英原版狀態或輸入不同")
    for name in ("OPENING.EXE", "VICEROY.EXE"):
        need(zh[0]["input_hashes"].get(name) == INPUT_SHA[name], f"{name} 收據指紋不同")
    for other, name in ((gui, "真 GUI"), (neg, "缺圖集負例")):
        need(other[0]["state"] == zh[0]["state"] and other[0]["input_hashes"] == zh[0]["input_hashes"] and
             other[0]["opened"] == zh[0]["opened"] and other[1] == zh[1], f"{name} 原版狀態不同")
    raw = (r / "gui-pedia.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "真 GUI 有拒絕輸入")
    spans = [s for s in dialog_spans(zh[0]) if s[0] in EXPECTED]
    need({s[0] for s in spans} == EXPECTED, "沒有正常進入全部 16 篇貨物條目")
    need(neg[0]["dialog_reason"] == "font-mask-unavailable" and
         not any(s[0] in EXPECTED for s in dialog_spans(neg[0])), "缺圖集負例仍顯示百科中文")
    cps, controls = ({c["label"]: c for c in v[0]["checkpoints"]} for v in (zh, control))
    checked, strings_checked = {}, set()
    strings = observed_strings(zh[0])
    expected_efficiency = {e["shown"] for e in zh[0]["events"] if e.get("stage") == "source" and
                           e.get("candidate_id") == "STRING:template:with-expert"}
    for line in (r / "gui-pedia.shots").read_text().splitlines():
        name, step = line.split()
        label = "cp-" + step
        need(label in cps and label in controls, f"{name} 缺檢查點")
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            need(cps[label][key] == controls[label][key], f"{name} 原版 {key} 不同")
        for cid, lo, hi, safe in spans:
            if lo <= int(step) < hi:
                box = tuple(x * 4 for x in safe)
                g, z, c = (Image.open(r / f).convert("RGB").crop(box) for f in
                           (f"gui-pedia.{name}.png", f"replay-zh.{label}.png", f"replay-control.{label}.png"))
                need(ImageChops.difference(g, z).getbbox() is None, f"{name} {cid} 真 GUI 與重播不同")
                need(ImageChops.difference(z, c).getbbox() is not None, f"{name} {cid} 未顯示中文")
                checked[cid] = name
        if name.startswith("cargo-"):
            for text, cid, lo, hi, safe in strings:
                if lo <= int(step) < hi:
                    box = tuple(x * 4 for x in safe)
                    g, z, c = (Image.open(r / f).convert("RGB").crop(box) for f in
                               (f"gui-pedia.{name}.png", f"replay-zh.{label}.png", f"replay-control.{label}.png"))
                    need(ImageChops.difference(g, z).getbbox() is None, f"{name} {cid} 字串安全區不同")
                    need(ImageChops.difference(z, c).getbbox() is not None, f"{name} {cid} 字串未顯示中文")
                    strings_checked.add(text)
    need(set(checked) == EXPECTED, "沒有逐篇截到全部貨物條目")
    need(expected_efficiency and expected_efficiency <= strings_checked, "沒有逐項截到貨物效率表格標籤")
    print(json.dumps({"result": "PASS", "scope": "16 篇貨物百科；其餘百科仍待驗收",
                      "articles": checked, "inputs_sha256": hashlib.sha256(raw).hexdigest(),
                      "string_fields": len(strings_checked), "efficiency_fields": len(expected_efficiency),
                      "input_fingerprints": INPUT_SHA,
                      "save_sha256": SAVE_SHA, "final_state_sha256": zh[0]["state"]["memory_sha256"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
