#!/usr/bin/env python3
"""目標163（Issue #39）：獨立核對功能鍵與數字鍵盤的真 GUI 同輸入收據；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state

POINTS = [590000000, 612000000, 640000000, 670000000, 705000000]


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def cp(report, step):
    found = [c for c in report["checkpoints"] if c.get("label") == f"cp-{step}"]
    need(len(found) == 1, f"缺少檢查點 {step}")
    return found[0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱功能鍵轉送通過")
        return 77
    r = a.reports
    raw = (r / "gui-keys.inputs.json").read_bytes()
    gui = json.loads(raw)
    need(not gui.get("rejected"), "現場輸入有被拒絕")
    keys = [e["text"] for e in gui["inputs"] if e["kind"] == "key"]
    need(keys == ["kp8", "kp7", "f1"], f"現場按鍵序列不符：{keys}")
    need(any(e["kind"] == "escape" for e in gui["inputs"]), "缺少 Esc 返回")
    zh, control, neg = load(r / "replay-zh"), load(r / "replay-control"), load(r / "neg-nokeys")
    same_state(zh, control, "中英原版狀態不同")
    for s in POINTS:
        need(cp(zh[0], s)["memory_sha256"] == cp(control[0], s)["memory_sha256"], f"{s}：中英原版狀態不同")
    # 反向對照：移除 key 事件後，按鍵之後的原版狀態必須不同（按鍵確實被原版消費）
    need(cp(zh[0], 590000000)["memory_sha256"] == cp(neg[0], 590000000)["memory_sha256"], "按鍵前的狀態不應受影響")
    changed = {s: cp(zh[0], s)["memory_sha256"] != cp(neg[0], s)["memory_sha256"] for s in POINTS[1:]}
    need(all(changed.values()), f"移除按鍵後狀態仍相同：{changed}")
    frames = {s: Image.open(r / f"replay-zh.cp-{s}.png").convert("RGB") for s in POINTS}
    need(ImageChops.difference(frames[640000000], frames[670000000]).getbbox() is not None, "F1 後畫面未改變")
    shots = {}
    for name, s in (("kp8", 612000000), ("kp7", 640000000), ("f1", 670000000), ("back", 705000000)):
        g = Image.open(r / f"gui-keys.{name}.png").convert("RGB")
        d = ImageChops.difference(g, frames[s]).getbbox()
        shots[name] = {"png_sha256": hashlib.sha256((r / f"gui-keys.{name}.png").read_bytes()).hexdigest(),
                       "diff_vs_replay_bbox": list(d) if d else None}
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(), "keys": keys,
                      "final_state_sha256": zh[0]["state"]["memory_sha256"], "shots": shots}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
