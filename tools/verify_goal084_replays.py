#!/usr/bin/env python3
"""獨立驗證規格020國家標題真視窗、逐欄回退與舊欄位回歸。"""

import argparse
import base64
import csv
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


CATALOG_SHA = "14b2cc51df1d42ccd938d8fab334c0b90b1cf63314746df19d80449c3865f3f1"
TESTED_CATALOG_SHA = "8484b941a434f51a0514a56fc6d96cee506cb2d968d35f0251966bc5939c6d63"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
TRUE_INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
FIRST_INPUT_SHA = "49c94703244f5890fdfa8ed8e2d5935b7a1c245d898d78b53a66991307b2da4a"
FIELDS = {
    "select": {"key": "LABELS.TXT:0x000008D3", "rect": (156, 140, 292, 184),
               "size": 38, "ink": (82, 35), "pixels": 2611, "zh": "選擇"},
    "power": {"key": "LABELS.TXT:0x000008DB", "rect": (68, 192, 380, 236),
              "size": 38, "ink": (164, 35), "pixels": 5502, "zh": "歐洲國家"},
}
MAIN_KEYS = ("GAME.TXT:0x000001B0", "GAME.TXT:0x000001CB", "GAME.TXT:0x000001E4",
             "GAME.TXT:0x000001F9", "GAME.TXT:0x00000204")
DIFFICULTY_KEYS = ("LABELS.TXT:0x00000888", "LABELS.TXT:0x00000890",
                   "LABELS.TXT:0x0000086E")
CARD_SIZES = {"NAMES.TXT:0x00000C0C": 21, "LABELS.TXT:0x000008A9": 25,
              "NAMES.TXT:0x00000C18": 21, "LABELS.TXT:0x000008B2": 25}
INPUTS = {"hover-select": "44dc7ed1f4b6c321b67e39d62d7c973d2f9ade79e8159e4893d3f0814bca4d37",
          "hover-power": "4ac6c8ebeadec85b5ec650422e7b20fc9095020531f100ca2ad1bedabbf8b2d6",
          "button": "27fe020f415a137f1c6cea3cb1da57d515e23bbd8a2bd129c952fe220794ceda"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def report(path):
    return json.loads(path.read_bytes())


def catalog_rows(data):
    return list(csv.DictReader(data.decode("utf-8").splitlines(), delimiter="\t"))


def without_notes(rows):
    return [{key: value for key, value in row.items() if key != "notes"}
            for row in rows]


def last_line(receipt, key):
    return next(line for line in receipt["checkpoints"][-1]["lines"]
                if line["candidate_id"] == key)


def range_lines(receipt, key, start, end):
    return [line for frame in receipt["frames"] if start <= frame["step"] < end
            for line in frame["lines"] if line["candidate_id"] == key]


def equal_rect(left, right, rect):
    return ImageChops.difference(left.crop(rect), right.crop(rect)).getbbox() is None


def verify(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    need(sha(args.catalog.read_bytes()) == CATALOG_SHA, "正式 TSV 版本不符")
    rows = catalog_rows(args.catalog.read_bytes())
    need(len(rows) == 368, "主譯稿筆數已變")
    # 正式重播後只修訂了兩筆 TSV 的證據備註；從當時的重複鍵反例
    # 還原被驗證的完整 TSV，逐列排除 notes 比較，不讓譯文變更混過。
    tested_variant = (p / "goal084-catalog-duplicate-select.tsv").read_bytes()
    lines = tested_variant.splitlines(keepends=True)
    target = b"LABELS.TXT:0x000008D3\t"
    positions = [i for i, line in enumerate(lines) if line.startswith(target)]
    need(len(positions) == 2 and lines[positions[0]] == lines[positions[1]],
         "無法從重複鍵反例還原已驗正式 TSV")
    tested = b"".join(lines[:positions[1]] + lines[positions[1] + 1:])
    need(sha(tested) == TESTED_CATALOG_SHA and
         without_notes(catalog_rows(tested)) == without_notes(rows),
         "備註修訂以外的正式 TSV 內容與已驗收版本不同")
    sizes = {key: 24 for key in MAIN_KEYS + DIFFICULTY_KEYS}
    sizes.update(CARD_SIZES)
    sizes.update({spec["key"]: spec["size"] for spec in FIELDS.values()})
    need(len(sizes) == 14 and
         len(list(args.font_dir.glob("*.json"))) == 14, "正式字模包不是14欄")
    for key, size in sizes.items():
        matches = [row for row in rows if row["candidate_id"] == key]
        need(len(matches) == 1 and matches[0]["status"] == "draft" and
             matches[0]["zh_hant"], "正式 TSV 欄位缺失或重複：" + key)
        mask = report(args.font_dir / (key.replace(":", "-") + ".json"))
        alpha = base64.b64decode(mask["alpha"], validate=True)
        need(mask["candidate_id"] == key and mask["font_sha256"] == FONT_SHA and
             mask["font_size"] == size and
             mask["translation_sha256"] == sha(matches[0]["zh_hant"].encode()) and
             len(alpha) == mask["width"] * mask["height"] and any(alpha),
             "字模未綁定真實譯文與逐欄字級：" + key)
        if key in [field["key"] for field in FIELDS.values()]:
            field = next(field for field in FIELDS.values() if field["key"] == key)
            need(matches[0]["zh_hant"] == field["zh"] and
                 (mask["width"], mask["height"]) == field["ink"],
                 "國家標題譯文或字模尺寸已變：" + key)
    true_inputs = (p / "goal084-window-full.inputs.json").read_bytes()
    need(sha(true_inputs) == TRUE_INPUT_SHA and
         len(json.loads(true_inputs)["inputs"]) == 16, "真視窗輸入版本不符")
    live = report(p / "goal084-window-full.json")
    live_control = report(p / "goal084-window-full-control.json")
    need(live["state"] == live_control["state"] and
         live["opened"] == live_control["opened"] and
         live["opened"][-1].upper() == "NATIONS.PIK" and
         (p / "goal084-window-full.final.idx").read_bytes() ==
         (p / "goal084-window-full-control.final.idx").read_bytes() and
         (p / "goal084-window-full.final.pal").read_bytes() ==
         (p / "goal084-window-full-control.final.pal").read_bytes(),
         "真視窗中文／英文控制原版狀態不同")
    for field in FIELDS.values():
        key = field["key"]
        need(len([event for event in live["events"]
                  if event.get("candidate_id") == key and event.get("accepted")]) == 1 and
             last_line(live, key)["applied"],
             "真視窗未各接受一次國家標題原文事件：" + key)
    replay_names = ("zh", "control", "missing-select", "missing-power",
                    "duplicate-select", "duplicate-power", "hover-select",
                    "hover-select-control", "hover-power", "hover-power-control",
                    "button", "button-control")
    receipts = {name: report(p / f"goal084-full-replay-{name}.json") for name in replay_names}
    need(all(receipts[name]["state"] == receipts["control"]["state"]
             for name in replay_names[:6]) and
         receipts["zh"]["state"] == live["state"] and
         receipts["control"]["state"] == live_control["state"],
         "真視窗重播／TSV 反例與英文控制原版不同狀態")
    images = {name: Image.open(p / f"goal084-full-replay-{name}.final.png").convert("RGB")
              for name in replay_names}
    live_image = Image.open(p / "goal084-window-full.final.png").convert("RGB")
    control_image = Image.open(p / "goal084-window-full-control.final.png").convert("RGB")
    capture = Image.open(p / "goal084-window-full.after-finish.png").convert("RGB")
    need(live_image.size == control_image.size == capture.size == (1280, 800) and
         ImageChops.difference(live_image, capture).getbbox() is None and
         ImageChops.difference(live_image, images["zh"]).getbbox() is None and
         ImageChops.difference(control_image, images["control"]).getbbox() is None,
         "真視窗擷取、正式輸出與同輸入重播不一致")
    current = report(p / "goal084-current-catalog.json")
    need(current["state"] == live["state"] and
         all((p / f"goal084-current-catalog.final.{suffix}").read_bytes() ==
             (p / f"goal084-window-full.final.{suffix}").read_bytes()
             for suffix in ("png", "idx", "pal")),
         "修訂備註與重新烘製字模後的目前 TSV 重播不等於已驗真視窗")
    diff = ImageChops.difference(live_image, control_image)
    changed = {name: 0 for name in FIELDS}
    pixels = diff.load()
    for y in range(800):
        for x in range(1280):
            if not any(pixels[x, y]):
                continue
            hit = [name for name, field in FIELDS.items()
                   if field["rect"][0] <= x < field["rect"][2] and
                   field["rect"][1] <= y < field["rect"][3]]
            need(len(hit) == 1, f"正式中文像素超出兩個安全矩形：{x},{y}")
            changed[hit[0]] += 1
    need(all(changed[name] == field["pixels"] for name, field in FIELDS.items()),
         "正式國家標題逐欄中文字模或底圖變更")
    for name in ("missing-select", "missing-power", "duplicate-select", "duplicate-power"):
        target = name.split("-", 1)[1]
        other = "power" if target == "select" else "select"
        key = FIELDS[target]["key"]
        other_key = FIELDS[other]["key"]
        need(last_line(receipts[name], key)["reason"] == "missing-or-invalid-translation" and
             not last_line(receipts[name], key)["applied"] and
             last_line(receipts[name], other_key)["applied"] and
             equal_rect(images[name], images["control"], FIELDS[target]["rect"]) and
             equal_rect(images[name], images["zh"], FIELDS[other]["rect"]),
             "缺鍵／重複鍵未逐欄回退：" + name)
    for name, expected in INPUTS.items():
        need(sha((p / f"{name}.inputs.json").read_bytes()) == expected,
             "互動輸入指紋不符：" + name)
        a, b = receipts[name], receipts[name + "-control"]
        need(a["state"] == b["state"] and a["opened"] == b["opened"] and
             a["state"]["steps"] == 68_000_000,
             "互動反例原版不同狀態：" + name)
        for field_name, field in FIELDS.items():
            over = range_lines(a, field["key"], 60_000_000, 64_000_000)
            away = range_lines(a, field["key"], 64_000_000, 68_000_000)
            need(len(over) == 24 and len(away) == 25,
                 "互動反例的原版幀相位或數量不符：" + name + "/" + field_name)
            if name == "hover-select" or (name == "hover-power" and field_name == "power"):
                need(all(not line["applied"] and line["reason"] == "frame-mismatch"
                         for line in over) and
                     all(line["applied"] for line in away),
                     "游標遮擋未逐欄回退／恢復：" + name + "/" + field_name)
            elif name == "hover-power":
                need(all(line["applied"] for line in over + away),
                     "第二行游標誤讓第一行退回英文")
            else:
                need(all(not line["applied"] and line["reason"] == "mouse-button-held"
                         for line in over) and away[0]["applied"] and
                     all(not line["applied"] for line in away[1:]),
                     "滑鼠按住／放開後切場殘留舊中文：" + field_name)
        if name == "button":
            need("WOODPANL.PIK" in [opened.upper() for opened in a["opened"]] and
                 all(not last_line(a, field["key"])["applied"] for field in FIELDS.values()),
                 "原版已切場但國家標題仍存在")
        else:
            need(all(last_line(a, field["key"])["applied"] for field in FIELDS.values()),
                 "游標移開後國家標題未恢復")
    need(sha((p / "goal084-first-card-40m.inputs.json").read_bytes()) == FIRST_INPUT_SHA,
         "舊第一張卡片同輸入版本不符")
    old_root = args.old_reports
    for new_name, old_prefix in (
        ("goal084-fixed-replay-first-card-regression", p / "goal084-old-first-same-input"),
        ("goal084-fixed-replay-second-card-regression", old_root / "goal082-window"),
    ):
        new_prefix = p / new_name
        need(report(new_prefix.with_suffix(".json"))["state"] ==
             report(old_prefix.with_suffix(".json"))["state"] and
             all(new_prefix.with_suffix("." + suffix).read_bytes() ==
                 old_prefix.with_suffix("." + suffix).read_bytes()
                 for suffix in ("final.png", "final.idx", "final.pal")),
             "既有難度卡片不是同輸入逐位元組回歸：" + new_name)
    old_checkpoints = report(p / "goal084-old-checkpoints.json")
    new_checkpoints = report(p / "goal084-new-checkpoints.json")
    labels = [checkpoint["label"] for checkpoint in old_checkpoints["checkpoints"]]
    need(old_checkpoints["state"] == new_checkpoints["state"] and
         labels == [checkpoint["label"] for checkpoint in new_checkpoints["checkpoints"]] and
         len(labels) == 15 and "menu-initial" in labels and "difficulty-clear" in labels,
         "主選單／難度頁檢查點或原版終點不同")
    for label in labels:
        need(all((p / f"goal084-old-checkpoints.{label}.{suffix}").read_bytes() ==
                 (p / f"goal084-new-checkpoints.{label}.{suffix}").read_bytes()
                 for suffix in ("png", "idx", "pal")),
             "舊版主選單／難度頁檢查點出現畫面回歸：" + label)
    wrong = report(p / "goal084-wrong-version.json")
    need(wrong["result"] == "PASS" and wrong["exit_code"] == 2 and
         wrong["version_rejected"] and not wrong["output_files"] and
         "LABELS.TXT" in wrong["scope"], "錯版本沒有在啟動前拒絕")
    receipt = {"result": "PASS", "scope": "規格020國家頁左側兩行正式中文顯示",
               "tested_catalog_sha256": TESTED_CATALOG_SHA,
               "current_catalog_sha256": CATALOG_SHA,
               "catalog_note_only_equivalent": True,
               "true_window_input_sha256": TRUE_INPUT_SHA,
               "true_window_screenshot_sha256": sha((p / "goal084-window-full.final.png").read_bytes()),
               "original_state_equal_control": True,
               "new_changed_pixels": changed,
               "per_field_missing_and_duplicate_fallback": True,
               "hover_and_button_frames_checked": True,
               "first_and_second_card_same_input_regression": True,
               "prior_menu_and_difficulty_checkpoints_equal": len(labels),
               "wrong_version_rejected": True,
               "limitations": "僅國家頁兩行；其他國家卡片、help、後續玩家路徑與完整遊玩未驗"}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--old-reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
