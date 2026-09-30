#!/usr/bin/env python3
"""目標177（Issue #55，規格032／035／036／038 附記）：獨立核對下拉選單、引號變數與部分遮擋；原版缺失回 SKIP 77。

- 中英原版狀態一致；反向對照（draft 移除 MENU.TXT 含 ~ 或 # 的列）原版狀態也一致。
- 六個下拉選單都以對話框層啟用；截圖時段內安全區真 GUI 與中文重播逐像素相同、且與英文控制不同。
  反向對照中項目含 ~、# 的 VIEW、ORDERS、REPORTS 不啟用。
- Find Colony 找不到時的 "…" not found.（引號變數，可為空字串）啟用。
- 士兵教學提示壓住右側狀態欄時，狀態欄區真 GUI 與重播相同、且與英文不同（部分遮擋仍顯示中文）。
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal172_window import dialog_spans

MENUS = {"GAME": "Save Game", "VIEW": "Move Pieces", "ORDERS": "Disband Unit", "REPORTS": "Religious",
         "TRADE": "Trade Route", "PEDIA": "Cargo Types"}
# 項目含 ~ 或 # 的選單（本目標才採用）；GAME、TRADE、PEDIA 的項目不含標記，反向對照中照樣中文。
MARKED = {"VIEW", "ORDERS", "REPORTS"}
PANEL = (240, 48, 320, 200)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def crop(path, box):
    return Image.open(path).convert("RGB").crop(tuple(v * 4 for v in box))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱選單與遮擋通過")
        return 77
    r = a.reports
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-sea.shots").read_text().splitlines())]
    raw = (r / "gui-sea.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control, neg = load(r / "replay-zh"), load(r / "replay-control"), load(r / "neg-nomenu")
    same_state(zh, control, "中英原版狀態不同")
    need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], "反向對照的原版狀態不同")

    spans, nspans = dialog_spans(zh[0]), dialog_spans(neg[0])
    checked = {}
    for menu, frag in MENUS.items():
        live = [x for x in spans if frag in x[0]]
        need(live, f"{menu} 選單未啟用")
        if menu in MARKED:
            need(not any(frag in x[0] for x in nspans), f"反向對照中 {menu} 選單不應啟用")
        for name, s in shots:
            for shown, key, t0, t1, safe in live:
                if t0 <= s < t1:
                    g, z, c = (crop(x, safe) for x in (r / f"gui-sea.{name}.png", r / f"replay-zh.cp-{s}.png",
                                                       r / f"replay-control.cp-{s}.png"))
                    need(ImageChops.difference(g, z).getbbox() is None, f"{name}：{menu} 選單真 GUI 與重播不同")
                    need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：{menu} 選單中文未改變安全區")
                    checked.setdefault(menu, []).append(name)
    need(set(checked) == set(MENUS), f"截到的選單不齊：{sorted(checked)}")
    need(any(x[0].startswith('"') and x[0].rstrip().endswith("not found.") for x in spans), "引號變數訊息未啟用")

    log = (r / "gui-sea.auto.log").read_text(encoding="utf-8")
    m = re.search(r"應答 (\d+)：.Our soldiers have two uses", log)
    need(m is not None, "路徑未經過士兵教學提示")
    shot = [(n, s) for n, s in shots if s == int(m.group(1))]
    need(shot, "士兵教學提示沒有截圖")
    name, s = shot[0]
    g, z, c = (crop(x, PANEL) for x in (r / f"gui-sea.{name}.png", r / f"replay-zh.cp-{s}.png", r / f"replay-control.cp-{s}.png"))
    need(ImageChops.difference(g, z).getbbox() is None, "遮擋時狀態欄真 GUI 與重播不同")
    need(ImageChops.difference(z, c).getbbox() is not None, "遮擋時狀態欄應仍有中文")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "menus": checked,
                      "occluded_shot": name, "final_state_sha256": zh[0]["state"]["memory_sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
