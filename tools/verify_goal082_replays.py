#!/usr/bin/env python3
"""獨立驗證規格019第二張卡片的真視窗、缺譯、游標與安全矩形。"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


TITLE = "NAMES.TXT:0x00000C18"
SUBTITLE = "LABELS.TXT:0x000008B2"
FIELDS = ((TITLE, (247 * 4, 44 * 4, 287 * 4, 51 * 4), 21, (69, 19), 2280),
          (SUBTITLE, (256 * 4, 52 * 4, 279 * 4, 60 * 4), 25, (54, 23), 1233))
OLD_RECTS = ((39 * 4, 14 * 4, 76 * 4, 26 * 4),
             (20 * 4, 27 * 4, 96 * 4, 40 * 4),
             (10 * 4, 79 * 4, 105 * 4, 88 * 4))
INPUT_SHA = "34d8ec6046830793b2e336ed41a638b533bb0782f5634263d0a1c338adda0f4b"
NAMES = ("zh", "control", "missing-title", "duplicate-title", "missing-subtitle",
         "duplicate-subtitle", "hover", "hover-control")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def line_frames(report, key):
    return [(frame["step"], line["applied"], line["reason"])
            for frame in report["frames"] for line in frame["lines"]
            if line["candidate_id"] == key]


def line_at_final(report, key):
    return next(line for line in report["checkpoints"][-1]["lines"]
                if line["candidate_id"] == key)


def equal_rect(left, right, rect):
    return ImageChops.difference(left.crop(rect), right.crop(rect)).getbbox() is None


def verify(args):
    p = args.out
    inputs = (p / "goal082-window.inputs.json").read_bytes()
    require(sha(inputs) == INPUT_SHA and
            len(json.loads(inputs)["inputs"]) == 12, "真視窗輸入指紋不符")
    with args.catalog.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    for key, _, size, ink, _ in FIELDS:
        matches = [row for row in rows if row["candidate_id"] == key]
        require(len(matches) == 1 and matches[0]["status"] == "draft" and
                matches[0]["zh_hant"], "原始 TSV 鍵不唯一：" + key)
        mask = json.loads((args.font_dir / (key.replace(":", "-") + ".json")).read_text())
        require(mask["candidate_id"] == key and mask["font_size"] == size and
                (mask["width"], mask["height"]) == ink and
                mask["font_sha256"] ==
                "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c" and
                mask["translation_sha256"] == sha(matches[0]["zh_hant"].encode()),
                "逐欄字模未綁定實際譯文與原版字級：" + key)
    live = json.loads((p / "goal082-window.json").read_text())
    live_control = json.loads((p / "goal082-window-control.json").read_text())
    require(live["state"] == live_control["state"] and
            (p / "goal082-window.final.idx").read_bytes() ==
            (p / "goal082-window-control.final.idx").read_bytes() and
            (p / "goal082-window.final.pal").read_bytes() ==
            (p / "goal082-window-control.final.pal").read_bytes(),
            "真 Ebitengine 視窗與英文控制原版狀態不同")
    require(live["state"]["steps"] == 100000000 and
            all(len([event for event in live["events"]
                     if event.get("candidate_id") == key and event.get("accepted")]) == 1
                for key, *_ in FIELDS) and
            all(line_at_final(live, key)["applied"] for key, *_ in FIELDS),
            "真視窗未各接受一個原版印字事件並套用中文")
    images = {name: Image.open(p / f"goal082-replay-{name}.final.png").convert("RGB")
              for name in NAMES}
    live_image = Image.open(p / "goal082-window.final.png").convert("RGB")
    live_control_image = Image.open(p / "goal082-window-control.final.png").convert("RGB")
    capture = Image.open(p / "goal082-window.second-card.png").convert("RGB")
    require(live_image.size == live_control_image.size == capture.size == (1280, 800) and
            ImageChops.difference(live_image, capture).getbbox() is None,
            "真視窗抓圖與正式 Ebitengine 輸出不同")
    diff = ImageChops.difference(live_image, live_control_image)
    changed = {key: 0 for key, *_ in FIELDS}
    prior_changed = 0
    px = diff.load()
    for y in range(800):
        for x in range(1280):
            if not any(px[x, y]):
                continue
            key = next((key for key, rect, *_ in FIELDS
                        if rect[0] <= x < rect[2] and rect[1] <= y < rect[3]), None)
            if key:
                changed[key] += 1
            elif any(rect[0] <= x < rect[2] and rect[1] <= y < rect[3]
                     for rect in OLD_RECTS):
                prior_changed += 1
            else:
                raise ValueError(f"真視窗中文像素超出已核准安全矩形：{x},{y}")
    require(changed == {key: expected for key, _, _, _, expected in FIELDS} and
            prior_changed > 0, "第二張卡片逐欄變更像素不符")
    reports = {name: json.loads((p / f"goal082-replay-{name}.json").read_text())
               for name in NAMES}
    require(all(reports[name]["state"] == reports["control"]["state"]
                for name in NAMES if not name.startswith("hover")) and
            reports["hover"]["state"] == reports["hover-control"]["state"],
            "缺譯／游標重播與同輸入英文控制原版狀態不同")
    require(all(reports[name]["state"]["steps"] ==
                (48000000 if name.startswith("hover") else 40000000) for name in NAMES),
            "重播未走到固定終點")
    require((p / "goal082-replay-zh.final.idx").read_bytes() ==
            (p / "goal082-replay-control.final.idx").read_bytes() ==
            (p / "goal082-window.final.idx").read_bytes(),
            "同輸入重播與真視窗的原版索引畫面不同")
    for key, rect, *_ in FIELDS:
        require(len([event for event in reports["zh"]["events"]
                     if event.get("candidate_id") == key and event.get("accepted")]) == 1 and
                line_at_final(reports["zh"], key)["applied"] and
                not equal_rect(images["zh"], images["control"], rect),
                "正式重播缺少第二張卡片中文：" + key)
        for action, target in (("missing", "missing-or-invalid-translation"),
                               ("duplicate", "missing-or-invalid-translation")):
            label = "title" if key == TITLE else "subtitle"
            name = f"{action}-{label}"
            require(line_at_final(reports[name], key)["reason"] == target and
                    not line_at_final(reports[name], key)["applied"] and
                    equal_rect(images[name], images["control"], rect),
                    "真實 TSV 缺鍵／重複鍵未逐欄回退原文：" + name)
            other_key, other_rect = next((other_key, other_rect)
                                         for other_key, other_rect, *_ in FIELDS
                                         if other_key != key)
            require(line_at_final(reports[name], other_key)["applied"] and
                    equal_rect(images[name], images["zh"], other_rect),
                    "單欄缺譯錯誤地影響另一欄：" + name)
        over = [(step, applied, reason) for step, applied, reason in
                line_frames(reports["hover"], key) if 40000000 <= step < 44000000]
        away = [(step, applied, reason) for step, applied, reason in
                line_frames(reports["hover"], key) if step >= 44000000]
        require(len(over) == len(away) == 24 and
                all(not applied and reason == "cursor-conservative-guard"
                    for _, applied, reason in over) and
                all(applied and reason == "applied" for _, applied, reason in away) and
                equal_rect(images["hover"], images["zh"], rect),
                "游標進出未逐欄回退並恢復：" + key)
    result = {"result": "PASS", "scope": "規格019第二張卡片兩行；真視窗與同輸入受控重播",
              "true_window_input_sha256": sha(inputs),
              "true_window_original_state_equal_control": True,
              "true_window_capture_equals_output": True,
              "new_changed_pixels": changed,
              "other_changed_pixels_only_prior_rectangles": prior_changed,
              "missing_and_duplicate_per_field_fallback": True,
              "hover_fallback_frames_per_field": 24,
              "after_hover_applied_frames_per_field": 24,
              "original_state_equal_control_for_all_variants": True,
              "screenshot_sha256": sha((p / "goal082-window.second-card.png").read_bytes())}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
