#!/usr/bin/env python3
"""核對第一張旗卡的游標、按鍵、換卡與離頁逐欄守門。"""

import argparse
import hashlib
import json
from pathlib import Path


IDS = ("NAMES.TXT:0x000008EA", "LABELS.TXT:0x000008F2")
CASES = {
    "hover-upper": (43_500_000, (False, True), ("cursor-over-card-field", "applied"), 51),
    "hover-lower": (43_500_000, (True, False), ("applied", "cursor-over-card-field"), 51),
    "hover-clear": (44_000_000, (True, True), ("applied", "applied"), 51),
    "press-lower": (44_000_000, (True, False), ("applied", "cursor-over-card-field"), 51),
    "switch-right": (46_000_000, (False, False), ("frame-mismatch", "frame-mismatch"), 51),
    "leave-page": (49_000_000, (False, False), ("missing-patch", "missing-patch"), 53),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = {"result": "PASS", "scope": "recorded-input Ebitengine replay",
               "cases": {}}
    for name, (steps, applied, reasons, opened_count) in CASES.items():
        prefix = args.out / name
        report = json.loads(prefix.with_suffix(".json").read_text())
        require(report["state"]["steps"] == steps, name + " 步數不符")
        require(len(report["opened"]) == opened_count, name + " 開檔世代不符")
        require(digest(args.out / f"{name}.final.idx") == report["state"]["frame_sha256"],
                name + " 原版索引畫面收據不符")
        require(digest(args.out / f"{name}.final.pal") == report["state"]["palette_sha256"],
                name + " 色盤收據不符")
        lines = {line["candidate_id"]: line for line in report["checkpoints"][-1]["lines"]}
        actual_applied = tuple(lines[key]["applied"] for key in IDS)
        actual_reasons = tuple(lines[key]["reason"] for key in IDS)
        require(actual_applied == applied and actual_reasons == reasons,
                name + " 逐欄守門與原版事件不符")
        accepted = [event for event in report["events"] if event.get("accepted")
                    and event.get("candidate_id") in IDS]
        require(len(accepted) == 2, name + " 最初旗卡來源事件不完整")
        if name == "switch-right":
            require(report["opened"][-1].upper() == "NATIONS.PIK", "換卡不在國家頁")
        if name == "leave-page":
            require([item.upper() for item in report["opened"][-2:]] ==
                    ["WOODPANL.PIK", "GAME.TXT"], "沒有由正常玩家路徑離頁")
        if name in ("switch-right", "leave-page"):
            baseline = json.loads((args.out / f"baseline-{name}.json").read_text())
            require(report["state"] == baseline["state"] and
                    report["opened"] == baseline["opened"], name + " 與舊版不同狀態")
            for suffix in ("idx", "pal", "png"):
                require(digest(args.out / f"{name}.final.{suffix}") ==
                        digest(args.out / f"baseline-{name}.final.{suffix}"),
                        name + " 換頁後仍有旗卡覆蓋殘留：" + suffix)
        receipt["cases"][name] = {"steps": steps, "applied": applied,
                                  "reasons": reasons,
                                  "frame_sha256": report["state"]["frame_sha256"],
                                  "png_sha256": digest(args.out / f"{name}.final.png")}
    path = args.out / "verify-runtime.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
