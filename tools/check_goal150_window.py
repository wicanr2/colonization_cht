#!/usr/bin/env python3
"""目標150（Issue #12）：動態覆蓋綜合驗證；原版缺失回 SKIP 77。"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

FULL_EXPECTED = {  # Explorer 無跳過路徑：主選單、難度、旗卡、姓名、英格蘭介紹、十張字幕、海上、遊戲選項九欄
    "GAME.TXT:0x000001CB", "GAME.TXT:0x000001E4", "GAME.TXT:0x000001F9", "GAME.TXT:0x00000204",
    "LABELS.TXT:0x00000888", "LABELS.TXT:0x00000890", "LABELS.TXT:0x0000086E", "NAMES.TXT:0x00000C0C",
    "LABELS.TXT:0x000008A9", "NAMES.TXT:0x00000C18", "LABELS.TXT:0x000008B2", "LABELS.TXT:0x000008D3",
    "LABELS.TXT:0x000008DB", "NAMES.TXT:0x000008EA", "LABELS.TXT:0x000008F2", "GAME.TXT:0x00000A7A",
    "GAME.TXT:@NATION0A", "GAME.TXT:@NATION0B", "GAME.TXT:0x000153CC", "GAME.TXT:0x0001542B",
    "GAME.TXT:0x00015482", "GAME.TXT:0x000154CB", "GAME.TXT:0x00015522", "GAME.TXT:0x0001555D",
    "GAME.TXT:0x00015597", "GAME.TXT:0x000155F5", "GAME.TXT:0x0001563F", "GAME.TXT:0x00015695",
    "sea:bar", "sea:panel", "GAME.TXT:0x000004CD", "GAME.TXT:0x000004E9", "GAME.TXT:0x000004FD",
    "GAME.TXT:0x00000512", "GAME.TXT:0x00000525", "GAME.TXT:0x00000533", "GAME.TXT:0x0000053E",
    "GAME.TXT:0x00000550", "GAME.TXT:0x00000566"}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def applied(report):
    return {l["candidate_id"] for f in report["frames"] for l in f["lines"] if l["applied"]}


def checkpoints_equal(zh, control):
    a = {c["label"]: c for c in zh["checkpoints"] if c["label"].startswith("cp-")}
    b = {c["label"]: c for c in control["checkpoints"] if c["label"].startswith("cp-")}
    need(a.keys() == b.keys() and all(a[k]["memory_sha256"] == b[k]["memory_sha256"] and
                                      a[k]["raw_sha256"] == b[k]["raw_sha256"] for k in a), "檢查點中英原版狀態不同")
    return len(a)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱動態覆蓋綜合驗證通過")
        return 77
    r = a.reports / "goal150-dynamic"
    old = a.reports / "goal143-sea"
    result = {"result": "PASS"}
    sea = json.loads((r / "sea-regress.json").read_text())
    ref = json.loads((old / "replay-zh.json").read_text())
    need(sea["state"] == ref["state"], "多字級圖集改變了海上路徑原版狀態")
    for c in (c for c in ref["checkpoints"] if c["label"].startswith("cp-")):
        x = Image.open(r / f"sea-regress.{c['label']}.png").convert("RGB")
        y = Image.open(old / f"replay-zh.{c['label']}.png").convert("RGB")
        need(ImageChops.difference(x, y).getbbox() is None, f"多字級圖集畫面與目標143不同：{c['label']}")
    long_ = json.loads((r / "shrink-long.json").read_text())
    too = json.loads((r / "shrink-toolong.json").read_text())
    last = lambda d: {l["candidate_id"]: l for l in d["frames"][-1]["lines"]}["sea:panel"]
    need(last(long_)["applied"] and last(long_)["rows"] == 11 and "Eng. Caravel" not in long_["sea_misses"], "16 字單位名未縮字套用")
    need(last(too)["applied"] and last(too)["rows"] == 10 and too["sea_misses"].get("Eng. Caravel", 0) > 0, "23 字單位名未回原文並記錄")
    full, full_c = load(r / "full-zh"), load(r / "full-control")
    same_state(full, full_c, "全流程終點中英原版狀態不同")
    got = applied(full[0])
    need(FULL_EXPECTED <= got, f"全流程有欄位從未套用：{sorted(FULL_EXPECTED - got)}")
    need(not applied(full_c[0]), "英文控制出現中文")
    helpz, help_c = load(r / "help-zh"), load(r / "help-control")
    same_state(helpz, help_c, "help 路徑終點中英原版狀態不同")
    need("GAME.TXT:@TUTORIAL1" in applied(helpz[0]) and "GAME.TXT:0x0001542B" not in applied(helpz[0]),
         "help 路徑：@TUTORIAL1 未套用或 Discoverer 版 @BUILD2 誤套用")
    result.update({"sea_regress_checkpoints": 6, "full_applied_keys": len(got),
                   "full_checkpoints": checkpoints_equal(full[0], full_c[0]),
                   "help_checkpoints": checkpoints_equal(helpz[0], help_c[0]),
                   "full_final_state": full[0]["state"]["memory_sha256"],
                   "help_final_state": helpz[0]["state"]["memory_sha256"]})
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
