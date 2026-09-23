#!/usr/bin/env python3
"""獨立驗證難度標題 A 版的兩欄差異、同狀態與逐欄回退。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


FIELDS = {
    "choose": ("LABELS.TXT:0x00000888", (156, 56, 304, 104), 34, (74, 32)),
    "level": ("LABELS.TXT:0x00000890", (80, 108, 384, 160), 38, (82, 35)),
}
CATALOG_SHA = "14b2cc51df1d42ccd938d8fab334c0b90b1cf63314746df19d80449c3865f3f1"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def png(path):
    return Image.open(path).convert("RGB")


def equal_rect(a, b, rect):
    return ImageChops.difference(a.crop(rect), b.crop(rect)).getbbox() is None


def last_line(data, key):
    return next(row for row in data["checkpoints"][-1]["lines"]
                if row["candidate_id"] == key)


def changed_only(a, b):
    need(a.size == b.size == (1280, 800), "畫布尺寸不符")
    diff = ImageChops.difference(a, b)
    counts = {name: 0 for name in FIELDS}
    pixels = diff.load()
    for y in range(800):
        for x in range(1280):
            if not any(pixels[x, y]):
                continue
            hit = [name for name, (_, rect, _, _) in FIELDS.items()
                   if rect[0] <= x < rect[2] and rect[1] <= y < rect[3]]
            need(len(hit) == 1, f"變動超出兩個標題安全區：{x},{y}")
            counts[hit[0]] += 1
    return counts


def equal_original(p, a, b):
    left, right = load(p / f"{a}.json"), load(p / f"{b}.json")
    need(left["state"] == right["state"] and left["opened"] == right["opened"],
         f"原版 CPU／RAM／時間／檔案開啟不同：{a}/{b}")
    for suffix in ("final.idx", "final.pal", "memory"):
        need(sha(p / f"{a}.{suffix}") == sha(p / f"{b}.{suffix}"),
             f"原版索引／色盤／RAM 不同：{a}/{b}/{suffix}")
    return left, right


def verify(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據目錄不存在或擁有者不符")
    need(sha(args.catalog) == CATALOG_SHA, "正式譯稿版本不符")
    masks = sorted(args.font_dir.glob("*.json"))
    old_masks = sorted(args.old_font_dir.glob("*.json"))
    need(len(masks) == len(old_masks) == 14, "十四欄字模數量不符")
    modified = [path.name for path in masks
                if sha(path) != sha(args.old_font_dir / path.name)]
    need(set(modified) == {item[0].replace(":", "-") + ".json"
                           for item in FIELDS.values()}, "除了兩個標題還有字模變動")
    for key, _, size, ink in FIELDS.values():
        mask = load(args.font_dir / (key.replace(":", "-") + ".json"))
        need(mask["candidate_id"] == key and mask["font_size"] == size and
             (mask["width"], mask["height"]) == ink, "標題字模尺寸／字級不符：" + key)
    live, control = equal_original(p, "live-first", "live-first-control")
    old = load(p / "old-live-first-same-input.json")
    need(live["state"] == old["state"] and live["opened"] == old["opened"] and
         all(sha(p / f"live-first.{suffix}") ==
             sha(p / f"old-live-first-same-input.{suffix}")
             for suffix in ("final.idx", "final.pal", "memory")),
         "新版／舊版同輸入的原版狀態不同")
    for key, _, _, _ in FIELDS.values():
        need(last_line(live, key)["applied"], "真視窗未套用標題：" + key)
    live_image = png(p / "live-first.final.png")
    capture = png(p / "live-first.difficulty.png")
    need(ImageChops.difference(live_image, capture).getbbox() is None,
         "真視窗擷取與最終畫面不同")
    changed = changed_only(live_image, png(p / "old-live-first-same-input.final.png"))
    need(all(changed.values()), "兩個標題有未實際改變的欄位")
    hover, _ = equal_original(p, "live", "live-control")
    need("NATIONS.PIK" in [name.upper() for name in hover["opened"]],
         "舊第二張卡片／完成區的正常路徑未到國家頁")
    nation_old = load(p / "old-live-nation-same-input.json")
    need(nation_old["state"] == hover["state"] and
         nation_old["opened"] == hover["opened"] and
         all(sha(p / f"old-live-nation-same-input.{suffix}") ==
             sha(p / f"live.{suffix}")
             for suffix in ("final.png", "final.idx", "final.pal", "memory")),
         "國家頁舊十二欄同輸入畫面或原版狀態回歸")
    for key in ("LABELS.TXT:0x000008D3", "LABELS.TXT:0x000008DB"):
        need(last_line(hover, key)["applied"], "國家頁既有中文欄位未套用：" + key)
    second_new, second_old = equal_original(p, "new-live-second-same-input",
                                             "old-live-second-same-input")
    second_diff = changed_only(png(p / "new-live-second-same-input.final.png"),
                               png(p / "old-live-second-same-input.final.png"))
    for key in ("NAMES.TXT:0x00000C18", "LABELS.TXT:0x000008B2"):
        need(last_line(second_new, key)["applied"] and last_line(second_old, key)["applied"],
             "第二張卡片既有中文欄位未套用：" + key)
    over = [frame for frame in hover["frames"] if 38_000_000 <= frame["step"] < 40_000_000]
    away = [frame for frame in hover["frames"] if 41_000_000 <= frame["step"] < 42_000_000]
    need(over and away, "缺游標遮擋／移開幀")
    def frame_line(frame, key):
        return next(row for row in frame["lines"] if row["candidate_id"] == key)
    choose_key, level_key = FIELDS["choose"][0], FIELDS["level"][0]
    need(all(frame_line(frame, choose_key)["applied"] and
             frame_line(frame, level_key)["reason"] == "frame-mismatch"
             for frame in over) and
         all(frame_line(frame, choose_key)["applied"] and
             frame_line(frame, level_key)["applied"] for frame in away),
         "游標遮擋未逐欄回退／移開恢復")
    checkpoint_receipt = load(p / "checkpoints.json")
    checkpoints = checkpoint_receipt["checkpoints"]
    # 舊檢查點前綴由呼叫端明示，避免把歷史路徑硬編進正式證據。
    old_receipt = load(args.old_checkpoints.with_suffix(".json"))
    need(checkpoint_receipt["state"] == old_receipt["state"] and
         [x["label"] for x in checkpoints] ==
         [x["label"] for x in old_receipt["checkpoints"]] and len(checkpoints) == 15,
         "十五個既有檢查點不相同")
    for item in checkpoints:
        label = item["label"]
        prefix = p / f"checkpoints.{label}"
        old_prefix = Path(str(args.old_checkpoints) + f".{label}")
        for suffix in ("idx", "pal"):
            need(sha(Path(str(prefix) + "." + suffix)) ==
                 sha(Path(str(old_prefix) + "." + suffix)),
                 "檢查點原版索引／色盤變動：" + label)
        counts = changed_only(png(Path(str(prefix) + ".png")),
                              png(Path(str(old_prefix) + ".png")))
        if label.startswith("menu") or label.startswith("switch"):
            need(not any(counts.values()), "主選單畫面回歸：" + label)
    baseline, baseline_control = equal_original(p, "fallback-baseline", "fallback-baseline-control")
    baseline_image = png(p / "fallback-baseline.final.png")
    need(baseline["state"]["steps"] == 45_000_000, "反例重播終點不符")
    for name, (key, rect, _, _) in FIELDS.items():
        other = "level" if name == "choose" else "choose"
        other_key, other_rect, _, _ = FIELDS[other]
        for action, reason in (("missing", "missing-or-invalid-translation"),
                               ("duplicate", "missing-or-invalid-translation"),
                               ("missing-mask", "font-mask-unavailable"),
                               ("wrong-size", "font-binding-mismatch")):
            label = f"fallback-{action}-{name}"
            data = load(p / f"{label}.json")
            image = png(p / f"{label}.final.png")
            need(data["state"] == baseline["state"] and data["opened"] == baseline["opened"] and
                 all(sha(p / f"{label}.{suffix}") ==
                     sha(p / f"fallback-baseline.{suffix}")
                     for suffix in ("final.idx", "final.pal", "memory")),
                 "反例改變原版狀態：" + label)
            need(last_line(data, key)["reason"] == reason and
                 not last_line(data, key)["applied"] and
                 last_line(data, other_key)["applied"] and
                 equal_rect(image, png(p / "fallback-baseline-control.final.png"), rect) and
                 equal_rect(image, baseline_image, other_rect),
                 "未逐欄回退英文或誤傷另一欄：" + label)
            changed_only(image, baseline_image)
    wrong = load(p / "wrong-version.json")
    need(wrong["result"] == "PASS" and wrong["exit_code"] == 2 and
         wrong["version_rejected"] and not wrong["output_files"], "錯版本未拒絕")
    result = {"result": "PASS", "scope": "難度標題 A 版兩欄；其他欄位與原版未改",
              "changed_pixels_vs_old": changed,
              "same_state_with_english_control_and_prior_binary": True,
              "true_window_input_sha256": sha(p / "live-first.inputs.json"),
              "private_screenshot_source_sha256": sha(p / "live-first.difficulty.png"),
              "old_field_masks_byte_identical": 12,
              "prior_checkpoints": 15,
              "second_card_changed_only_headings": second_diff,
              "nation_page_pixel_identical_to_prior_binary": True,
              "cursor_overlap_per_field_fallback": True,
              "per_field_missing_duplicate_missing_mask_wrong_size": True,
              "wrong_original_version_rejected": True,
              "limitations": "只驗難度標題兩欄；不延伸到國家旗卡或 help"}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--old-font-dir", type=Path, required=True)
    parser.add_argument("--old-checkpoints", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
