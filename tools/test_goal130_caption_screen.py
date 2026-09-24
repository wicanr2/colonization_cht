#!/usr/bin/env python3
"""首張字幕 READY 審查資料的篡改與失敗即保留原文負例。"""

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import check_goal130_caption_screen as check


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--preprint", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    source = [json.loads((a.reports / f"operands-{name}.json").read_bytes())
              for name in ("a", "b", "control")]
    inputs = (a.game.read_bytes(), a.inputs.read_bytes(),
              a.catalog.read_text(encoding="utf-8"), a.preprint.read_bytes(), a.reports)
    assert check.verify_reports(*source, *inputs)["result"] == "PASS"
    rejected = 0
    for name, alter in (
        ("來源運算元錯位", lambda x: x[0]["caption_screen_audit"]["read_operands"][3].__setitem__("ss_bx_linear", 0)),
        ("原版印前底圖錯誤", lambda x: x[0]["caption_screen_audit"].__setitem__("first_read_canvas_sha256", "0" * 64)),
        ("VGA 前六幀缺失", lambda x: x[0]["caption_screen_audit"].__setitem__("safe_mismatch_frames", 5)),
        ("過早蓋字", lambda x: x[0]["caption_frame_audit"]["transitions"][0].__setitem__("step", 88770000)),
        ("離頁仍顯示", lambda x: x[0]["caption_frame_audit"]["transitions"][1].__setitem__("event", "ready")),
        ("控制組 RAM 岔開", lambda x: x[2]["samples"]["90m"].__setitem__("memory_sha256", "0" * 64)),
        ("字幕 VGA 變造", lambda x: x[0]["samples"]["90m"].__setitem__("indexed_sha256", "0" * 64)),
        ("漏一字", lambda x: x[0]["caption_screen_audit"]["read_operands"].pop()),
    ):
        reports = copy.deepcopy(source)
        alter(reports)
        try:
            check.verify_reports(*reports, *inputs)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(f"未拒絕：{name}")
    base = dict(event=True, writes=1040, bbox=[16, 30, 303, 39],
                before_sha=check.PREPRINT_SHA, canvas_sha=check.SCREEN_SHA,
                indexed_sha=check.SCREEN_SHA, palette_sha=check.PALETTE_SHA,
                mode=0x13, translation="測試譯文", mask_ok=True)
    assert check.candidate(**base)
    for name, altered in (
        ("無當次事件", {"event": False}),
        ("少一畫素", {"writes": 1039}),
        ("原版墨跡框錯", {"bbox": [15, 30, 303, 39]}),
        ("錯印前底圖", {"before_sha": "0" * 64}),
        ("底層畫布已換頁", {"canvas_sha": check.NEXT_SHA}),
        ("實際 VGA 尚未更新", {"indexed_sha": "0" * 64}),
        ("色盤錯", {"palette_sha": "0" * 64}),
        ("模式錯", {"mode": 3}),
        ("缺譯", {"translation": ""}),
        ("缺字模", {"mask_ok": False}),
    ):
        case = dict(base)
        case.update(altered)
        assert not check.candidate(**case), f"未回退：{name}"
        rejected += 1
    command = [sys.executable, str(Path(check.__file__)),
               "--game", str(a.game.parent / "MISSING-GAME.TXT"),
               "--inputs", str(a.inputs), "--catalog", str(a.catalog),
               "--preprint", str(a.preprint), "--reports", str(a.reports)]
    skipped = subprocess.run(command, check=False, capture_output=True, text=True)
    assert skipped.returncode == 77 and '"result": "SKIP"' in skipped.stdout
    print(f"PASS：{rejected} 項篡改／回退負例、缺合法原版 SKIP 77")


if __name__ == "__main__":
    main()
