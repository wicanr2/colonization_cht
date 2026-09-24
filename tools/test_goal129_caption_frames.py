#!/usr/bin/env python3
"""目標129：原版逐幀收據及 DRAFT 回退候選的獨立篡改負例。"""

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import check_goal129_caption_frames as check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--preprint", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    original = [json.loads((args.reports / f"{name}.json").read_bytes())
                for name in ("observed-a", "observed-b", "control")]
    payload = (args.game.read_bytes(), args.inputs.read_bytes(),
               args.catalog.read_text(encoding="utf-8"), args.preprint.read_bytes(),
               args.reports)
    assert check.validate(*original, *payload)["result"] == "PASS"
    failures = 0
    for label, mutate in (
        ("原版完整 RAM 不同", lambda x: x[2]["samples"]["90m"].__setitem__("memory_sha256", "0" * 64)),
        ("印字來源錯誤", lambda x: x[0]["print_reads"][next(
            i for i, r in enumerate(x[0]["print_reads"]) if r["step"] == 88689021)].__setitem__("value", 0)),
        ("原版畫布寫入缺一點", lambda x: x[0]["caption_frame_audit"].__setitem__("write_count", 1039)),
        ("少一可顯示畫格", lambda x: x[0]["caption_frame_audit"].__setitem__("eligible_frames", 646)),
        ("離頁仍顯示", lambda x: x[0]["caption_frame_audit"]["transitions"][1].__setitem__("event", "ready")),
        ("錯色盤", lambda x: x[0]["samples"]["90m"].__setitem__("palette_sha256", "0" * 64)),
    ):
        changed = copy.deepcopy(original)
        mutate(changed)
        try:
            check.validate(*changed, *payload)
        except ValueError:
            failures += 1
        else:
            raise AssertionError(f"未拒絕：{label}")
    source = original[0]["caption_frame_audit"]
    for label, kw in (
        ("未印字", {"event": False}),
        ("缺譯", {"translation": ""}),
        ("畫布錯版", {"canvas_sha": "0" * 64}),
        ("色盤錯版", {"palette_sha": "0" * 64}),
        ("已離頁", {"mode": 3}),
        ("寫入不足", {"writes": 1039}),
        ("字框錯位", {"bbox": [15, 30, 303, 39]}),
    ):
        fields = dict(event=source["read_end_step"] != 0, writes=1040,
                      bbox=[16, 30, 303, 39], mode=0x13,
                      canvas_sha=check.CAPTION_SHA, palette_sha=check.PALETTE_SHA,
                      translation="主後一千四百九十二年，")
        fields.update(kw)
        assert not check.eligible(**fields), f"未回退：{label}"
        failures += 1
    assert check.eligible(True, 1040, [16, 30, 303, 39], 0x13,
                          check.CAPTION_SHA, check.PALETTE_SHA, "主後一千四百九十二年，")
    command = [sys.executable, str(Path(check.__file__)), "--game", str(args.game.parent / "MISSING-GAME.TXT"),
               "--inputs", str(args.inputs), "--catalog", str(args.catalog),
               "--preprint", str(args.preprint), "--reports", str(args.reports)]
    skipped = subprocess.run(command, check=False, capture_output=True, text=True)
    assert skipped.returncode == 77 and '"result": "SKIP"' in skipped.stdout
    print(f"PASS：{failures}項篡改／回退負例、1項缺合法原版 SKIP 77；不代表正式真視窗已通過")


if __name__ == "__main__":
    main()
