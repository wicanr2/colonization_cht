#!/usr/bin/env python3
"""目標178（Issue #55，規格036／038 附記）：獨立核對 ORDERS 停用項目與地圖殖民地名稱標籤；原版缺失回 SKIP 77。

- 中英原版狀態一致；反向對照（draft 移除 ORDERS 停用項目）原版狀態也一致。
- ORDERS 選單整份（含可用與停用項目）以對話框層啟用；截圖時段內安全區真 GUI 與中文重播逐像素相同、且與英文控制不同。
  反向對照中該選單不啟用（停用項目查不到譯稿，整段回原文）。
- 地圖上的殖民地名稱標籤（字串層 STRING:colony，安全區在地圖視窗內）啟用；至少一張截圖中標籤安全區
  真 GUI 與中文重播逐像素相同、且與英文控制不同。
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal172_window import dialog_spans

MAP_VIEW = (0, 8, 240, 190)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def crop(path, box):
    return Image.open(path).convert("RGB").crop(tuple(v * 4 for v in box))


def label_spans(report):
    """地圖視窗內的預設殖民地名標籤啟用區間：(顯示字串, 開始, 結束, 安全區)。"""
    src, start, out = None, None, []
    def close(step):
        nonlocal start
        if start is not None:
            out.append((src[0], start, step, src[1]))
            start = None
    for e in report["events"]:
        if e.get("candidate_id") != "STRING:colony":
            continue
        stage = e.get("stage")
        if stage == "source":
            # 同一鍵亦用於狀態欄名稱；缺項目識別碼的舊收據只能保守歸屬。
            close(e["step"])
            src = (e["shown"], e["safe"]) if e.get("buffer") == "map" else None
        elif stage == "active" and src is not None and start is None:
            start = e["step"]
        elif stage in ("suspended", "expired"):
            close(e["step"])
            if stage == "expired":
                src = None
    if start is not None:
        out.append((src[0], start, 1 << 62, src[1]))
    return out


def check_river(reports, tutorial):
    """補充檢查正常 GUI 輸入的重播；不冒稱新增檢查點已經真 GUI 截圖核對。"""
    zh, control = load(reports / "replay-zh"), load(tutorial / "replay-control")
    same_state(zh, control, "大河重播與原版控制的終點狀態、輸入或完整記憶體不同")
    original = {c["label"]: c for c in control[0]["checkpoints"]}
    current = {c["label"]: c for c in zh[0]["checkpoints"]}
    need(set(original) <= set(current), "大河重播缺既有檢查點")
    for name, c in original.items():
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            need(c.get(key) == current[name].get(key), f"{name}：大河重播原版 {key} 不同")
    cp = current["cp-1060000000"]
    events = [e for e in zh[0]["events"] if e.get("shown") == "(Major River)" and e["step"] <= cp["step"]]
    source = next(e for e in reversed(events) if e["stage"] == "source")
    need(source["entry_ip"] == "0D21:00C6" and source["zh"] == "（大河）" and source["font_px"] == 22,
         "大河來源、譯文或欄位字級不符")
    need(events[-1]["stage"] == "active", "大河在檢查點時未作用中")
    need(not zh[0]["dialog_reason"] and not zh[0]["string_reason"], "圖集綁定失敗")
    need(any(x["candidate_id"] == "STRING" and x["applied"] for x in cp["lines"]), "檢查點未繪製字串層")
    prefix = reports / ("replay-zh." + cp["label"])
    idx, pal = (Path(str(prefix) + "." + ext).read_bytes() for ext in ("idx", "pal"))
    need(len(idx) == 64000 and len(pal) == 768 and max(pal) <= 63, "原版索引或色盤尺寸不符")
    need(hashlib.sha256(idx).hexdigest() == cp["raw_sha256"] and
         hashlib.sha256(pal).hexdigest() == cp["palette_sha256"], "檢查點像素或色盤雜湊不符")
    raw = Image.frombytes("P", (320, 200), idx)
    raw.putpalette([v << 2 | v >> 4 for v in pal])
    raw = raw.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
    safe = tuple(v * 4 for v in source["safe"])
    composed = Image.open(str(prefix) + ".png").convert("RGB")
    need(composed.size == raw.size and ImageChops.difference(composed.crop(safe), raw.crop(safe)).getbbox() is not None,
         "大河安全區未產生中文像素")
    return {"result": "PASS_REPLAY", "evidence_level": "正常 GUI 輸入重播；新增檢查點未做真 GUI 截圖核對",
            "checkpoint_step": cp["step"], "safe": source["safe"], "font_px": source["font_px"],
            "source_step": source["step"], "final_state_sha256": zh[0]["state"]["memory_sha256"]}


def check_occlusion(reports, baseline):
    """檢查已取證的森林項目沒有被教學框單字元撤銷；不驗收其他遮擋情境。"""
    current, old = (json.loads((r / "replay-zh.json").read_text()) for r in (reports, baseline))
    need(current["state"] == old["state"] and current["input_hashes"] == old["input_hashes"],
         "覆蓋修正改變原版終點狀態或輸入")
    now = {c["label"]: c for c in current["checkpoints"] if c["label"] != "final"}
    before = {c["label"]: c for c in old["checkpoints"] if c["label"] != "final"}
    need(set(now) == set(before), "覆蓋修正缺既有檢查點")
    changed = {}
    for name, c in now.items():
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            need(c[key] == before[name][key], f"{name}：覆蓋修正改變原版 {key}")
        a, b = (Image.open(r / ("replay-zh." + name + ".png")).convert("RGB") for r in (reports, baseline))
        diff = ImageChops.difference(a, b).getbbox()
        if diff is None:
            continue
        changed[name] = list(diff)
        outside = a.copy()
        for safe in ((0, 0, 1280, 32), (960, 192, 1280, 800)):
            outside.paste(b.crop(safe), safe)
        need(ImageChops.difference(outside, b).getbbox() is None, f"{name}：覆蓋修正越出頂列／狀態欄")
    label = "cp-993200000"
    cp, prev = (next(c for c in report["checkpoints"] if c["label"] == label) for report in (current, old))
    for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
        need(cp[key] == prev[key], f"森林遮擋修正改變原版 {key}")
    events = [e for e in current["events"] if e.get("shown") == "(Wetland Forest)" and e["step"] <= cp["step"]]
    i = max(i for i, e in enumerate(events) if e["stage"] == "source")
    source, lifecycle = events[i], events[i + 1:]
    need(source["zh"] == "（濕地林）" and source["font_px"] == 22, "森林譯文或字級不符")
    need(any(e["stage"] == "active" for e in lifecycle) and any(e["stage"] == "suspended" for e in lifecycle) and
         not any(e["stage"] == "expired" for e in lifecycle), "森林項目未保留至遮擋檢查點")
    a, b = (Image.open(r / ("replay-zh." + label + ".png")).convert("RGB") for r in (reports, baseline))
    panel = (960, 192, 1280, 800)
    need(ImageChops.difference(a.crop(panel), b.crop(panel)).getbbox() is not None, "修正沒有改變狀態欄")
    outside = a.copy()
    outside.paste(b.crop(panel), panel)
    need(ImageChops.difference(outside, b).getbbox() is None, "森林修正越出狀態欄")
    return {"result": "PASS_REPLAY", "scope": "單字元誤撤銷森林項目；不含低於三成墨跡的其他遮擋",
            "checkpoint_step": cp["step"], "memory_sha256": cp["memory_sha256"],
            "original_checkpoints": len(now), "changed": changed}


def check_status_gui(reports):
    """獨立核對新 GUI 的狀態欄；地圖標籤仍由主檢查嚴格驗收。"""
    gui, zh, control = (load(reports / p) for p in ("gui-sea", "replay-zh", "replay-control"))
    same_state(zh, control, "新 GUI 中英重播的原版狀態或輸入不同")
    need(gui[0]["state"] == zh[0]["state"] and gui[0]["opened"] == zh[0]["opened"] and
         gui[0]["input_hashes"] == zh[0]["input_hashes"] and gui[1] == zh[1],
         "新 GUI 與重播的原版終點、輸入或記憶體不同")
    cps = {c["label"]: c for c in zh[0]["checkpoints"]}
    original = {c["label"]: c for c in control[0]["checkpoints"]}
    checked, sea_checked = [], []
    safe = (960, 192, 1280, 800)
    for line in (reports / "gui-sea.shots").read_text().splitlines():
        name, step = line.split()
        if name == "final" or int(step) < 650000000:
            continue
        label = "cp-" + step
        need(label in cps and label in original, f"{name}：缺狀態欄檢查點")
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            need(cps[label][key] == original[label][key], f"{name}：原版 {key} 不同")
        g, z, c = (Image.open(reports / p).convert("RGB").crop(safe) for p in
                   (f"gui-sea.{name}.png", f"replay-zh.{label}.png", f"replay-control.{label}.png"))
        if ImageChops.difference(z, c).getbbox() is None:
            continue
        need(ImageChops.difference(g, z).getbbox() is None, f"{name}：新 GUI 狀態欄與重播不同")
        checked.append(name)
        if any(x["candidate_id"] == "sea:panel" and x["applied"] for x in cps[label]["lines"]):
            sea_checked.append(name)
    need("after-29" in sea_checked, "未驗到遮擋後恢復的海上狀態欄")
    return {"result": "PASS_STATUS_GUI", "scope": "新 GUI 狀態欄；不含地圖標籤及遮擋殘字策略",
            "shots": checked, "sea_shots": sea_checked,
            "inputs_sha256": hashlib.sha256((reports / "gui-sea.inputs.json").read_bytes()).hexdigest(),
            "final_state_sha256": zh[0]["state"]["memory_sha256"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--river-reports", type=Path, help="額外的大河重播收據；不取代本目標真 GUI 驗證")
    p.add_argument("--tutorial-reports", type=Path, help="目標167 的原版控制收據")
    p.add_argument("--occlusion-baseline", type=Path, help="修正前目標178 收據，補查單字元誤撤銷森林項目")
    p.add_argument("--status-reports", type=Path, help="另驗新 GUI 狀態欄；不取代地圖標籤主檢查")
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱 ORDERS 停用項目與地圖標籤通過")
        return 77
    r = a.reports
    if a.status_reports:
        print(json.dumps(check_status_gui(a.status_reports), ensure_ascii=False, sort_keys=True))
    if a.river_reports:
        need(a.tutorial_reports is not None, "大河檢查需要 --tutorial-reports")
        print(json.dumps(check_river(a.river_reports, a.tutorial_reports), ensure_ascii=False, sort_keys=True))
    if a.occlusion_baseline:
        print(json.dumps(check_occlusion(r, a.occlusion_baseline), ensure_ascii=False, sort_keys=True))
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-sea.shots").read_text().splitlines())]
    raw = (r / "gui-sea.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control, neg = load(r / "replay-zh"), load(r / "replay-control"), load(r / "neg-noorders")
    same_state(zh, control, "中英原版狀態不同")
    need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], "反向對照的原版狀態不同")

    # ORDERS：可用項目與停用項目在同一段啟用。
    spans, nspans = dialog_spans(zh[0]), dialog_spans(neg[0])
    orders = [x for x in spans if "Activate unit" in x[0] and "Clear Forest" in x[0] and "Disband Unit" in x[0]]
    need(orders, "ORDERS 選單整份未以對話框層啟用")
    need(not any("Activate unit" in x[0] or "Clear Forest" in x[0] for x in nspans), "反向對照中 ORDERS 選單不應啟用")
    checked_orders = []
    for name, s in shots:
        for shown, key, t0, t1, safe in orders:
            if t0 <= s < t1:
                g, z, c = (crop(x, safe) for x in (r / f"gui-sea.{name}.png", r / f"replay-zh.cp-{s}.png",
                                                   r / f"replay-control.cp-{s}.png"))
                need(ImageChops.difference(g, z).getbbox() is None, f"{name}：ORDERS 選單真 GUI 與重播不同")
                need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：ORDERS 選單中文未改變安全區")
                checked_orders.append(name)
    need(checked_orders, "沒有截到 ORDERS 選單")

    # 地圖殖民地名稱標籤。
    labels = [x for x in label_spans(zh[0]) if x[0] == "Jamestown" and x[3][0] >= MAP_VIEW[0] and x[3][2] <= MAP_VIEW[2]]
    need(labels, "地圖標籤未啟用")
    checked_labels = []
    for name, s in shots:
        if name == "final":
            continue  # 結束時的畫面不與步數對齊，海面的閃爍動畫可能差一格；其餘截圖都由步數對齊擷取
        for shown, t0, t1, safe in labels:
            if t0 <= s < t1:
                g, z, c = (crop(x, safe) for x in (r / f"gui-sea.{name}.png", r / f"replay-zh.cp-{s}.png",
                                                   r / f"replay-control.cp-{s}.png"))
                if ImageChops.difference(z, c).getbbox() is None:
                    continue  # 標籤區被其他畫面蓋住（例如選單）時中英相同，不算標籤截圖
                need(ImageChops.difference(g, z).getbbox() is None, f"{name}：地圖標籤真 GUI 與重播不同")
                checked_labels.append(name)
    need(checked_labels, "沒有截到地圖標籤")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "orders_shots": checked_orders,
                      "label_shots": checked_labels, "final_state_sha256": zh[0]["state"]["memory_sha256"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
