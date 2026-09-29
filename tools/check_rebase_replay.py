#!/usr/bin/env python3
"""以新前端重播舊基準的同一份輸入，逐檢查點比對新舊重播截圖（目標172）。

舊基準通過時真 GUI 與舊中文重播逐像素相同；新舊中文重播相同的檢查點因此仍與真 GUI 相同。
英文對照重播必須全部相同；中文重播的差異逐一列出，並要求落在 --allow 指定的檢查點步數內。
原版缺失回 SKIP 77。
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--old", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--allow", type=int, nargs="*", default=[], help="允許中文重播改變的檢查點步數")
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱重播回歸通過")
        return 77
    files = sorted(x.name for x in a.old.glob("replay-*.cp-*.png"))
    if not files:
        raise ValueError("舊基準沒有重播截圖")
    changed = {}
    for f in files:
        if not (a.new / f).is_file():
            raise ValueError(f"新重播缺 {f}")
        box = ImageChops.difference(Image.open(a.old / f).convert("RGB"), Image.open(a.new / f).convert("RGB")).getbbox()
        if box:
            changed[f] = list(box)
    for run in sorted({f.split(".cp-")[0] for f in files}):
        old, new = (json.loads((d / f"{run}.json").read_text()) for d in (a.old, a.new))
        om = {c["label"]: c.get("memory_sha256") for c in old["checkpoints"]}
        nm = {c["label"]: c.get("memory_sha256") for c in new["checkpoints"]}
        if om != nm or old["state"]["memory_sha256"] != new["state"]["memory_sha256"]:
            raise ValueError(f"{run}：新舊重播的原版狀態不同")
    bad = [f for f in changed if not f.startswith("replay-zh.")]
    if bad:
        raise ValueError(f"英文或反向對照重播改變：{bad}")
    extra = [f for f in changed if int(f.split(".cp-")[1].split(".")[0]) not in a.allow]
    if extra:
        raise ValueError(f"未預期的中文重播改變：{extra}")
    print(json.dumps({"result": "PASS", "checkpoints": len(files), "changed": changed}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
