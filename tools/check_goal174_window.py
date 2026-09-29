#!/usr/bin/env python3
"""目標174（Issue #46，規格035）：獨立核對輸入列標籤的真 GUI、中英同輸入重播與反向對照；原版缺失回 SKIP 77。

- 中英原版狀態一致；反向對照（draft 移除三種標籤譯名）原版狀態也一致。
- 命名新陸地、命名殖民地、Find Colony 三個輸入列的標籤都啟用；啟用期間的截圖，標籤安全區真 GUI 與中文重播逐像素相同、
  且與英文控制不同；標籤右側的輸入內容（同一行、到安全區右方 160 邏輯像素）中英完全相同。
- 反向對照（draft 移除標籤譯名、模板表移除 label-trailing）：`Colony:` 只有這兩個來源，標籤不啟用，
  截圖的標籤區與英文控制相同。`Name:` 另可由字串層片段字典（語料多行譯文拆出）翻譯，不在反向對照範圍。
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state



def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def spans(report):
    """輸入列標籤的啟用區間：(顯示字串, 開始, 結束, 安全區, 字級)。"""
    src, start, out = {}, {}, []
    for e in report["events"]:
        if e.get("candidate_id") != "STRING:input-label":
            continue
        if e.get("stage") == "source" and "safe" in e:
            src = (e["shown"], json.loads(e["safe"]) if isinstance(e["safe"], str) else e["safe"], int(e["font_px"]))
        elif e.get("stage") == "active" and src:
            start = (src, e["step"])
        elif e.get("stage") in ("expired", "suspended") and start:
            (shown, safe, zh), s = start
            out.append((shown, int(s), int(e["step"]), safe, zh))
            start = {}
    if start:
        (shown, safe, zh), s = start
        out.append((shown, int(s), 1 << 62, safe, zh))
    return out


def crop(path, box):
    return Image.open(path).convert("RGB").crop(tuple(v * 4 for v in box))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱輸入欄標籤通過")
        return 77
    r = a.reports
    shots = [(n, int(s)) for n, s in (l.split() for l in (r / "gui-input.shots").read_text().splitlines())]
    raw = (r / "gui-input.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    zh, control, neg = load(r / "replay-zh"), load(r / "replay-control"), load(r / "neg-nolabel")
    same_state(zh, control, "中英原版狀態不同")
    need(neg[0]["state"] == control[0]["state"] and neg[1] == control[1], "反向對照的原版狀態不同")

    live = spans(zh[0])
    got = {x[0] for x in live}
    need(any(s.startswith("Name: New England") for s in got) and any(s.startswith("Name: Jamestown") for s in got)
         and any(s.startswith("Colony:") for s in got), f"輸入列標籤未全部啟用：{sorted(got)}")
    need(all(12 <= x[4] <= 30 for x in live), f"標籤字級超出圖集範圍：{sorted({x[4] for x in live})}")
    need(not any(x[0].startswith("Colony:") for x in spans(neg[0])), "反向對照不應有 Colony: 標籤")

    checked = []
    for name, s in shots:
        for shown, t0, t1, safe, _ in live:
            if not t0 <= s < t1:
                continue
            g, z, c, n = (crop(x, safe) for x in (r / f"gui-input.{name}.png", r / f"replay-zh.cp-{s}.png",
                                                   r / f"replay-control.cp-{s}.png", r / f"neg-nolabel.cp-{s}.png"))
            need(ImageChops.difference(g, z).getbbox() is None, f"{name}：{shown!r} 真 GUI 與重播不同")
            need(ImageChops.difference(z, c).getbbox() is not None, f"{name}：{shown!r} 中文未改變標籤區")
            if shown.startswith("Colony:"):
                need(ImageChops.difference(n, c).getbbox() is None, f"{name}：反向對照的標籤區應與英文相同")
            buf = (safe[2], safe[1], min(320, safe[2] + 160), safe[3])
            need(ImageChops.difference(crop(r / f"replay-zh.cp-{s}.png", buf), crop(r / f"replay-control.cp-{s}.png", buf)).getbbox() is None,
                 f"{name}：輸入內容區中英不同")
            checked.append((name, shown))
    need({x[1].split(":")[0] for x in checked} >= {"Name", "Colony"}, f"截到的輸入列太少：{checked}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "labels": sorted(got),
                      "shots": checked, "final_state_sha256": zh[0]["state"]["memory_sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
