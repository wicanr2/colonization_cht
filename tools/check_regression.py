#!/usr/bin/env python3
"""全面回歸：比對候選前端與基準收據的六個固定重播點（原版 RAM、索引、色盤、輸出圖、狀態、套用幀數）；原版缺失回 SKIP 77。"""

import argparse
import json
from pathlib import Path

POINTS = {"regress": ["regression-build1-82m", "regression-title-1280m", "rows-1280m"],
          "regress135": ["zh-53m", "zh-62m", "zh-72m"]}


def applied_frames(report):
    return sum(1 for f in report["frames"] if any(l["applied"] for l in f["lines"]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱回歸通過")
        return 77
    result, ok = {}, True
    for sub, names in POINTS.items():
        for n in names:
            x, y = a.baseline / sub / n, a.candidate / sub / n
            same = all(Path(f"{x}{e}").read_bytes() == Path(f"{y}{e}").read_bytes()
                       for e in (".memory", ".final.idx", ".final.pal", ".final.png"))
            jx, jy = json.loads(Path(f"{x}.json").read_text()), json.loads(Path(f"{y}.json").read_text())
            same = same and jx["state"] == jy["state"] and len(jx["frames"]) == len(jy["frames"]) and \
                applied_frames(jx) == applied_frames(jy)
            result[f"{sub}/{n}"] = {"same": same, "applied_frames": applied_frames(jy)}
            ok = ok and same
    print(json.dumps({"result": "PASS" if ok else "FAIL", "points": result}, ensure_ascii=False, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
