#!/usr/bin/env python3
"""目標144：以三種真實輸出情境的探針收據套用規格033資料模型，確認每則訊息只歸到一組來源鍵。原版缺失回 SKIP 77。"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from text_model import classify, load_dictionary

# 情境 → (收據, 起始步數, 必須命中的鍵)
SCENARIOS = {
    "captions": ("goal141-captions/full/a.json", 76000000,
                 {"GAME.TXT:0x000153CC", "GAME.TXT:0x0001542B", "GAME.TXT:0x00015482", "GAME.TXT:0x000154CB",
                  "GAME.TXT:0x00015522", "GAME.TXT:0x0001555D", "GAME.TXT:0x00015597", "GAME.TXT:0x000155F5",
                  "GAME.TXT:0x0001563F", "GAME.TXT:0x00015695", "MENU.TXT:~GAME..~COLONIZOPEDIA"}),
    "help": ("goal142-help/discoverer/a.json", 76000000, {"GAME.TXT:@TUTORIAL1"}),
    "sea": ("goal143-sea/probe/a.json", 548000000, {"MENU.TXT:~GAME..~COLONIZOPEDIA", "NAMES.TXT:0x000000C0",
            "LABELS.TXT:0x00000BB2", "LABELS.TXT:0x000000C0", "LABELS.TXT:0x000000C8", "NAMES.TXT:0x0000099B",
            "NAMES.TXT:0x000025FD", "NAMES.TXT:0x00002855", "NAMES.TXT:0x000005C4", "NAMES.TXT:0x000005FD",
            "NAMES.TXT:0x000006E1", "LABELS.TXT:0x00000411", "NAMES.TXT:0x0000286A", "NAMES.TXT:0x000021C5",
            "LABELS.TXT:0x00000116", "NAMES.TXT:0x00000969", "NAMES.TXT:0x000009C1"}),
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--dictionary", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱資料模型驗證通過")
        return 77
    dictionary = load_dictionary(a.dictionary)
    result = {"result": "PASS", "scenarios": {}}
    for name, (path, start, required) in SCENARIOS.items():
        report = json.loads((a.reports / path).read_text())
        report["prints"] = [x for x in report["prints"] if x["Start"] >= start]
        known, unknown = classify(report, dictionary)
        keys = set(k for e in known for k in e["keys"])
        need(required <= keys, f"{name}：缺少必要來源鍵 {sorted(required - keys)}")
        # 同一英文字串在不同情境（位置）只能對到同一組鍵：同文異境不得分歧。
        by_text = defaultdict(set)
        for e in known:
            by_text[(e["class"], e["text"])].add(tuple(e["keys"]))
        conflicts = {t: v for t, v in by_text.items() if len(v) > 1}
        need(not conflicts, f"{name}：同文對到多組鍵 {conflicts}")
        contexts = defaultdict(set)
        for e in known:
            contexts[e["text"]].add(tuple(e["box"]))
        result["scenarios"][name] = {
            "classified": len(known), "unknown": len(unknown), "distinct_keys": len(keys),
            "classes": sorted({e["class"] for e in known}),
            "same_text_multiple_positions": sorted(t for t, v in contexts.items() if len(v) > 1),
            "unknown_texts": sorted({u["text"] for u in unknown})[:20]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
