#!/usr/bin/env python3
"""目標164（Issue #40）：核對步數對齊的真 GUI 選國收據；國別與輸入間距。原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

NATIONS = {"france": "1", "spain": "2", "netherlands": "3"}
UPDATE_STEPS = 200000


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def check_inputs(inputs, name):
    moves = {e["step"] for e in inputs if e["kind"] == "move"}
    press = {}
    counts = {"press": 0, "release": 0}
    for e in inputs:
        if e["kind"] == "press":
            need(e["step"] not in moves, f"{name}：按下與移動同在步數 {e['step']}")
            press[e["button"]] = e["step"]
            counts["press"] += 1
        elif e["kind"] == "release" and e.get("button") in press:
            gap = e["step"] - press.pop(e["button"])
            need(gap >= 2 * UPDATE_STEPS, f"{name}：按住只有 {gap} 步")
            counts["release"] += 1
    need(counts["press"] > 0 and counts["press"] == counts["release"], f"{name}：按下／放開數不符 {counts}")
    return counts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--runs", type=int, default=2)
    a = p.parse_args()
    if not (a.game / "VICEROY.EXE").is_file():
        print("SKIP：缺原版")
        return 77
    out = {}
    for n, code in NATIONS.items():
        for r in range(1, a.runs + 1):
            name = f"options-{n}-run{r}"
            prefix = a.reports / name
            report = json.loads(Path(f"{prefix}.json").read_text())
            raw = Path(f"{prefix}.inputs.json").read_bytes()
            inputs = json.loads(raw)["inputs"]
            pages = {e["candidate_id"] for e in report["events"]
                     if str(e.get("candidate_id", "")).startswith("GAME.TXT:@NATION") and e["candidate_id"] != "GAME.TXT:@NATION"}
            need(pages == {f"GAME.TXT:@NATION{code}A", f"GAME.TXT:@NATION{code}B"}, f"{name}：國別不符，介紹頁事件為 {sorted(pages)}")
            need(Path(f"{prefix}.options.png").is_file(), f"{name}：缺遊戲選項截圖")
            out[name] = {"pages": sorted(pages), "clicks": check_inputs(inputs, name),
                         "inputs_sha256": hashlib.sha256(raw).hexdigest()}
    body = {"result": "PASS", "runs": out}
    print(json.dumps(body, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as e:
        print(f"FAIL：{e}")
        sys.exit(1)
