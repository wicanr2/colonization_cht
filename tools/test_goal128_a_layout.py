#!/usr/bin/env python3
"""目標128 A 版面與固定取樣字幕守門的獨立負例。"""

import argparse
import copy
import csv
import json
from pathlib import Path

from check_goal128_a_layout import (
    CAPTION_PALETTE, CAPTION_SCREEN, GAME_SHA, OPTION_SIZES_A,
    check_caption_layout, check_options_layout, eligible_caption,
)


def rejects(action, name):
    try:
        action()
    except (ValueError, KeyError, IndexError):
        return
    raise AssertionError(name + " 本應拒絕")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caption-preview", type=Path, required=True)
    parser.add_argument("--options-preview", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    paths = (args.caption_preview / "preview.json",
             args.options_preview / "options-faithful.json",
             args.options_preview / "options-faithful.verify.json", args.catalog)
    if not all(path.is_file() for path in paths):
        print("SKIP：合法本機 A 版對照或譯稿缺失")
        return 77
    caption, options, verify = (json.loads(path.read_bytes()) for path in paths[:3])
    with args.catalog.open(encoding="utf-8", newline="") as stream:
        rows = {row["candidate_id"]: row for row in csv.DictReader(stream, delimiter="\t")}
    caption_row = rows["GAME.TXT:0x000153CC"]
    check_caption_layout(caption, caption_row)
    check_options_layout(options, verify, rows)
    assert OPTION_SIZES_A == (34, 25, 28, 28, 25, 28, 28, 27, 28)
    assert eligible_caption(True, True, 0x13, CAPTION_SCREEN, CAPTION_PALETTE)
    for valid in (
        eligible_caption(False, True, 0x13, CAPTION_SCREEN, CAPTION_PALETTE),
        eligible_caption(True, False, 0x13, CAPTION_SCREEN, CAPTION_PALETTE),
        eligible_caption(True, True, 0x03, CAPTION_SCREEN, CAPTION_PALETTE),
        eligible_caption(True, True, 0x13, "wrong-page", CAPTION_PALETTE),
        eligible_caption(True, True, 0x13, CAPTION_SCREEN, "wrong-palette"),
    ):
        assert not valid, "錯來源／版本／模式／畫面／色盤誤判可覆蓋"
    bad = copy.deepcopy(caption)
    bad["font_size"] = 42
    rejects(lambda: check_caption_layout(bad, caption_row), "字幕 B 字級")
    bad = copy.deepcopy(caption)
    bad["shadow_bbox"][2] = bad["safe_scaled"][2] + 1
    rejects(lambda: check_caption_layout(bad, caption_row), "字幕陰影越界")
    bad = copy.deepcopy(options)
    bad["layers"][0]["font_size"] = 38
    rejects(lambda: check_options_layout(bad, verify, rows), "九欄 B 字級")
    bad = copy.deepcopy(options)
    bad["layers"][8]["position"][1] = 800
    rejects(lambda: check_options_layout(bad, verify, rows), "第八列溢出")
    bad = copy.deepcopy(rows)
    bad["GAME.TXT:0x00000566"]["zh_hant"] = "教學提示"
    rejects(lambda: check_options_layout(options, verify, bad), "熱鍵標記消失")
    bad = copy.deepcopy(rows)
    bad["GAME.TXT:0x00000566"]["source_sha256"] = "wrong-version"
    rejects(lambda: check_options_layout(options, verify, bad), "原版鍵版本不符")
    assert GAME_SHA == caption_row["source_sha256"]
    print("PASS：A 字級、來源、版面、快捷鍵與錯頁／錯色盤／離頁負例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
