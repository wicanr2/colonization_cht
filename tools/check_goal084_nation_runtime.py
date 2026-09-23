#!/usr/bin/env python3
"""獨立核對國家標題可丟棄執行期守門、游標反例與原版同狀態。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


VERSIONS = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
}
INPUTS = {
    "click": "bb86566b14d73136e27a096b35ba6b1e2e84ef011122ac817dd989dd7727e550",
    "hover-select": "44dc7ed1f4b6c321b67e39d62d7c973d2f9ade79e8159e4893d3f0814bca4d37",
    "hover-power": "4ac6c8ebeadec85b5ec650422e7b20fc9095020531f100ca2ad1bedabbf8b2d6",
    "button": "27fe020f415a137f1c6cea3cb1da57d515e23bbd8a2bd129c952fe220794ceda",
}
FIELDS = {
    "select": {"safe": (39, 35, 73, 46), "bbox": [42, 36, 69, 44],
               "pixels": 120, "before": "7092302ca905ced59a9839c528df5f28a0dc2823618f4f0d99cdd729c6bd5251",
               "output_pixels": 2611},
    "power": {"safe": (17, 48, 95, 59), "bbox": [20, 49, 91, 57],
              "pixels": 270, "before": "ec7ea1fd43546a53a09172591abbd89269e9b146db2bd591fd98b12f860543a0",
              "output_pixels": 5502},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def safe_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def check(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "輸出目錄不存在或擁有者不符")
    for name, expected in VERSIONS.items():
        source = args.game / name
        if not source.is_file():
            raise SystemExit(77)
        need(sha(source.read_bytes()) == expected, "原版檔案版本不符：" + name)
    for name, expected in INPUTS.items():
        need(sha((p / f"{name}.inputs.json").read_bytes()) == expected,
             "玩家輸入版本不符：" + name)
    expected_preview = "6d530c7164df76ac4ab923bad296df3823299b77feb76a64441a6f017748efe7"
    need(sha((p / "nation-preview.json").read_bytes()) == expected_preview,
         "固定本機字模預覽版本不符")
    first_bytes = (p / "goal084-v2-click-a.json").read_bytes()
    need(first_bytes == (p / "goal084-v2-click-b.json").read_bytes(),
         "雙次正常玩家探針收據不一致")
    reports = {}
    for name in INPUTS:
        path = p / ("goal084-v2-click-a.json" if name == "click" else f"goal084-v2-{name}.json")
        report = json.loads(path.read_bytes())
        control = json.loads((p / f"goal084-v2-{name}-control.json").read_bytes())
        need(report["version"] == control["version"] == "goal084-nation-runtime-v2" and
             report["input_hashes"] == control["input_hashes"] == VERSIONS and
             report["input_sha256"] == control["input_sha256"] == INPUTS[name] and
             report["preview_sha256"] == control["preview_sha256"] == expected_preview,
             "探針、原版或預覽指紋不符：" + name)
        need(not report["control"] and control["control"] and
             report["state"] == control["state"] and
             report["opened"] == control["opened"],
             "同輸入原版狀態不一致：" + name)
        if name == "button":
            need("WOODPANL.PIK" in [opened.upper() for opened in report["opened"]] and
                 report["opened"][-1].upper() == "GAME.TXT",
                 "滑鼠放開後的原版場景轉移與控制組不符")
        else:
            need(report["opened"][-1].upper() == "NATIONS.PIK",
                 "原版意外離開國家選擇頁：" + name)
        need(report["first_both_applied"] and not control["first_both_applied"] and
             not control["frames"] and len(report["frames"]) > 80,
             "缺少兩行同時套用或控制組不乾淨：" + name)
        for field_name, spec in FIELDS.items():
            event = report["source_events"].get(field_name)
            need(event is not None and event["formatted_seen"] and
                 event["changed_pixels"] == spec["pixels"] and
                 event["bbox"] == spec["bbox"] and
                 event["before_safe_sha256"] == spec["before"] and
                 event["read_step"] < event["patch_step"] < 44_000_000,
                 "當次來源、底圖或畫素證據不符：" + name + "/" + field_name)
            before = (p / f"nation-evidence-a.before-{field_name}-source.canvas").read_bytes()
            need(sha(safe_bytes(before, spec["safe"])) == spec["before"],
                 "執行期底圖與獨立原版快照不符：" + field_name)
        negatives = report["negative"]
        need(negatives["stale-first"] == ["frame-mismatch", "applied"] and
             negatives["stale-second"] == ["applied", "frame-mismatch"] and
             negatives["missing-ink"] == {
                 "original_pixels": True, "reasons": ["missing-ink", "missing-ink"]},
             "兩行補片互借、舊底圖或缺字模反例失敗：" + name)
        frames = report["frames"]
        need(any(f["applied"] == 2 and not f["cursor_in_title"] and not f["button_guard"]
                 for f in frames), "未曾安全套用兩行中文：" + name)
        if name == "button":
            guarded = [f for f in frames if f["button_guard"]]
            after_release = [f for f in frames if f["step"] > guarded[-1]["step"]]
            need(len(guarded) == 24 and
                 all(f["applied"] == 0 and not f["cursor_in_title"] and
                     f["reasons"] == ["mouse-button-held", "mouse-button-held"]
                     for f in guarded) and
                 after_release[0]["applied"] == 2 and
                 all(f["applied"] == 0 and f["valid"] == [False, False]
                     for f in after_release[1:]) and
                 frames[-1]["valid"] == [False, False],
                 "滑鼠按住回退或原版場景切換後補片清除失敗")
        elif name.startswith("hover-"):
            guarded = [f for f in frames if f["cursor_in_title"]]
            expected_reasons = (["frame-mismatch", "frame-mismatch"] if name == "hover-select"
                                else ["applied", "frame-mismatch"])
            need(report["hover_fallback"] and report["away_recovered"] and
                 len(guarded) == 24 and
                 all(f["applied"] == (0 if name == "hover-select" else 1) and
                     f["reasons"] == expected_reasons and not f["button_guard"]
                     for f in guarded) and
                 any(f["applied"] == 2 for f in frames if f["step"] > guarded[-1]["step"]),
                 "游標回退或移開恢復失敗：" + name)
        else:
            need(not report["hover_fallback"] and not report["away_recovered"],
                 "無游標變體誤判為游標回退")
        if name != "button":
            need(frames[-1]["applied"] == 2 and not frames[-1]["cursor_in_title"] and
                 not frames[-1]["button_guard"],
                 "國家選擇頁穩定狀態未維持兩行中文：" + name)
        reports[name] = {"receipt_sha256": sha(path.read_bytes()),
                         "frames": len(frames),
                         "cursor_intersection_frames": sum(f["cursor_in_title"] for f in frames),
                         "button_guard_frames": sum(f["button_guard"] for f in frames),
                         "original_state_equal_control": True}
    with Image.open(p / "goal084-v2-click-a.control.png") as raw, \
            Image.open(p / "goal084-v2-click-a.zh.png") as localized:
        raw = raw.convert("RGB")
        localized = localized.convert("RGB")
        need(raw.size == localized.size == (1280, 800), "執行期畫面尺寸不符")
        diff = ImageChops.difference(raw, localized)
        changed = {name: 0 for name in FIELDS}
        for y in range(800):
            for x in range(1280):
                if diff.getpixel((x, y)) == (0, 0, 0):
                    continue
                hit = [name for name, spec in FIELDS.items()
                       if spec["safe"][0] * 4 <= x < spec["safe"][2] * 4 and
                       spec["safe"][1] * 4 <= y < spec["safe"][3] * 4]
                need(len(hit) == 1, "中文改動超出核准安全區或跨欄重疊")
                changed[hit[0]] += 1
        need(all(changed[name] == spec["output_pixels"] for name, spec in FIELDS.items()),
             "執行期文字差異像素數不符")
    receipt = {"result": "PASS", "scope": "國家選擇標題兩行可丟棄執行期守門；非正式顯示",
               "double_receipt_sha256": sha(first_bytes), "variants": reports,
               "output_changed_pixels": changed,
               "limitations": "尚未接正式 Ebitengine、真 TSV 缺鍵／重複鍵、錯版本與既有十二段回歸"}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    check(parser.parse_args())
