#!/usr/bin/env python3
"""獨立驗證規格017的真 TSV 缺鍵、游標回退與輸出安全矩形。"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops


KEYS = ("NAMES.TXT:0x00000C0C", "LABELS.TXT:0x000008A9")
RECTS = ((138 * 4, 44 * 4, 186 * 4, 51 * 4),
         (146 * 4, 52 * 4, 180 * 4, 60 * 4))
NAMES = ("zh", "control", "missing-title", "duplicate-title", "hover", "hover-control")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_frames(report, key):
    return [(frame["step"], line["applied"], line["reason"])
            for frame in report["frames"] for line in frame["lines"]
            if line["candidate_id"] == key]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()
    reports = {name: json.loads((args.out / f"goal079-replay-{name}.json").read_text())
               for name in NAMES}
    assert all(reports[name]["state"] == reports["control"]["state"]
               for name in NAMES[:4]), "一般／缺譯／重複鍵／英文原版狀態不同"
    assert reports["hover"]["state"] == reports["hover-control"]["state"], "游標同輸入狀態不同"
    assert all(reports[name]["state"]["steps"] == 40000000 for name in NAMES)
    for key in KEYS:
        events = [e for e in reports["zh"]["events"]
                  if e.get("candidate_id") == key and e.get("accepted")]
        assert len(events) == 1, (key, events)
        assert any(applied for _, applied, _ in line_frames(reports["zh"], key))
    missing_title = line_frames(reports["missing-title"], KEYS[0])
    missing_subtitle = line_frames(reports["missing-title"], KEYS[1])
    assert missing_title and all(not applied and reason == "missing-or-invalid-translation"
                                 for _, applied, reason in missing_title)
    assert any(applied for _, applied, _ in missing_subtitle)
    duplicate_title = line_frames(reports["duplicate-title"], KEYS[0])
    duplicate_subtitle = line_frames(reports["duplicate-title"], KEYS[1])
    assert duplicate_title and all(not applied and reason == "missing-or-invalid-translation"
                                   for _, applied, reason in duplicate_title)
    assert any(applied for _, applied, _ in duplicate_subtitle)
    hover_counts = {}
    for key in KEYS:
        frames = line_frames(reports["hover"], key)
        counter = Counter(reason for _, _, reason in frames)
        assert counter["cursor-conservative-guard"] == 25, (key, counter)
        assert any(step < 32000000 and applied for step, applied, _ in frames)
        assert any(32000000 <= step < 36000000 and reason == "cursor-conservative-guard"
                   for step, _, reason in frames)
        assert any(step >= 36000000 and applied for step, applied, _ in frames)
        hover_counts[key] = dict(counter)
    images = {name: Image.open(args.out / f"goal079-replay-{name}.final.png").convert("RGB")
              for name in NAMES}
    assert all(image.size == (1280, 800) for image in images.values())
    def equal_rect(a, b, rect):
        return ImageChops.difference(images[a].crop(rect), images[b].crop(rect)).getbbox() is None
    assert equal_rect("missing-title", "control", RECTS[0]), "缺鍵稱號未回退原文"
    assert equal_rect("missing-title", "zh", RECTS[1]), "缺鍵不應影響副標"
    assert equal_rect("duplicate-title", "control", RECTS[0]), "重複鍵稱號未回退原文"
    assert equal_rect("duplicate-title", "zh", RECTS[1]), "重複鍵不應影響副標"
    assert equal_rect("hover", "zh", RECTS[0]) and equal_rect("hover", "zh", RECTS[1]), \
        "游標移開後兩欄未恢復"
    assert not equal_rect("zh", "control", RECTS[0]) and not equal_rect("zh", "control", RECTS[1])
    receipt = {"scope": "規格017第一張卡片兩行；Ebitengine已記錄輸入的受控重播，非所有玩家路徑",
               "normal_state_equal": True, "hover_state_equal": True,
               "card_events": {key: [e["entry_step"] for e in reports["zh"]["events"]
                                      if e.get("candidate_id") == key and e.get("accepted")]
                               for key in KEYS},
               "missing_title_reason": "missing-or-invalid-translation",
               "missing_title_original_pixels": True, "duplicate_title_original_pixels": True,
               "subtitle_still_chinese": True,
               "hover_counts": hover_counts, "hover_restores_chinese": True,
               "image_sha256": {name: sha(args.out / f"goal079-replay-{name}.final.png")
                                for name in NAMES}}
    path = args.out / "goal079-replay-receipt.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
