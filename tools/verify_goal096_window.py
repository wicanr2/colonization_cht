#!/usr/bin/env python3
"""目標096：真 Ebitengine 視窗姓名提示、編輯與離頁的獨立核對。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


KEY = "GAME.TXT:0x00000A7A"
PROMPT = (400, 340, 876, 392)
NAME = (316, 392, 984, 448)
CURSORS = ((64, 64, 128, 128), (260, 736, 304, 800))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def image(path):
    shot = Image.open(path).convert("RGB")
    need(shot.size == (1280, 800), f"截圖尺寸錯誤：{path}")
    return shot


def equal_except(left, right, masks):
    compare = left.copy()
    for rect in masks:
        compare.paste(right.crop(rect), rect)
    return ImageChops.difference(compare, right).getbbox() is None


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--reports", type=Path, required=True)
parser.add_argument("--prior", type=Path, required=True)
parser.add_argument("--fonts", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
need(args.out.parent.is_dir() and args.out.parent.stat().st_uid == os.getuid(),
     "收據輸出目錄不存在或擁有者不符")
p = args.reports
live, control = load(p / "live-name.json"), load(p / "live-name-control.json")
inputs = load(p / "live-name.inputs.json")
need(not live["control"] and control["control"] and live["all_menu"] and
     control["all_menu"] and inputs["end"] == 90_000_000 and not inputs.get("rejected"),
     "真視窗、中英文控制或輸入收據不符")
keys = [(e["kind"], e.get("text")) for e in inputs["inputs"]
        if e["kind"] in ("text", "backspace", "enter")]
need(keys == [("enter", None), ("text", "x"), ("backspace", None), ("enter", None)],
     "真視窗鍵盤玩家路徑不符")
need(live["state"] == control["state"] and live["opened"] == control["opened"] and
     live["input_hashes"] == control["input_hashes"] and
     (p / "live-name.memory").read_bytes() == (p / "live-name-control.memory").read_bytes(),
     "原版 CPU／完整 RAM／時間或開檔序列被中文輸出擾動")
for suffix in ("idx", "pal"):
    need((p / f"live-name.final.{suffix}").read_bytes() ==
         (p / f"live-name-control.final.{suffix}").read_bytes(),
         f"原版最終索引／色盤被擾動：{suffix}")

events = [e for e in live["events"] if e["candidate_id"] == KEY]
accepted = [e for e in events if e.get("accepted")]
need(len(accepted) == 1 and accepted[0]["entry_ip"] == "0E2D:09F4" and
     accepted[0]["writer_ip"] == "0D21:012C" and
     accepted[0]["source_linear"] == 0x2B072 and
     accepted[0]["changed_pixels"] == 415 and
     accepted[0]["bbox_inclusive"] == [104, 88, 214, 96],
     "正式覆蓋未綁到完整提示的原版印字事件")
need(any(e.get("stage") == "canvas-candidate" and e["glyph_count"] == 23 and
         e["formatted_seen"] and e["valid_colors"] and
         e["colors"] == {"128": 81, "47": 135, "68": 199} for e in events),
     "逐字來源、415點色號或畫布候選不符")
frames = live["frames"]
applied = [f["step"] for f in frames if
           next((line["applied"] for line in f["lines"] if line["candidate_id"] == KEY), False)]
need(applied and min(applied) > accepted[0]["entry_step"] and
     49_000_000 <= min(applied) < 55_000_000 and max(applied) < 64_000_000,
     "姓名畫面未套用或 Enter 後仍有提示覆蓋")
for f in frames:
    if 55_000_000 <= f["step"] < 63_200_000:
        need(next(line["applied"] for line in f["lines"] if line["candidate_id"] == KEY),
             "姓名編輯時提示覆蓋消失")
    if f["step"] >= 66_000_000:
        need(not next(line["applied"] for line in f["lines"] if line["candidate_id"] == KEY),
             "離頁後提示覆蓋未撤除")

mask = load(args.fonts / "GAME.TXT-0x00000A7A.json")
need(mask["candidate_id"] == KEY and mask["font_size"] == 38 and
     (mask["width"], mask["height"]) == (328, 35) and
     mask["font_sha256"] ==
     "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c" and
     mask["translation_sha256"] == hashlib.sha256("請輸入您的姓名。".encode()).hexdigest(),
     "姓名提示字模未綁定真譯文與欄位專屬字級")
shots = {name: image(p / f"live-name.{name}.png") for name in
         ("idle", "letter", "backspace", "after-enter")}
english_idle = image(args.prior / "idle-control.png")
english_exit = image(args.prior / "enter-control.png")
need(ImageChops.difference(shots["idle"].crop(PROMPT), english_idle.crop(PROMPT)).getbbox()
     is not None and equal_except(shots["idle"], english_idle, (PROMPT, *CURSORS)),
     "中文畫素逃出提示安全區或姓名畫面沒有中文")
need(equal_except(shots["after-enter"], english_exit, CURSORS),
     "Enter 後仍殘留中文或下一頁回歸")
for name in ("letter", "backspace"):
    need(ImageChops.difference(shots["idle"].crop(PROMPT),
                               shots[name].crop(PROMPT)).getbbox() is None,
         f"姓名編輯改變中文提示：{name}")
for left, right in (("idle", "letter"), ("letter", "backspace")):
    bbox = ImageChops.difference(shots[left], shots[right]).getbbox()
    need(bbox is not None and NAME[0] <= bbox[0] < bbox[2] <= NAME[2] and
         NAME[1] <= bbox[1] < bbox[3] <= NAME[3],
         f"姓名欄編輯逃出安全範圍：{left}→{right}")

result = {"result": "PASS", "scope": "真 Ebitengine 視窗固定姓名提示、x／退格／Enter及英文同狀態；負例仍另驗",
          "input_sha256": sha(p / "live-name.inputs.json"),
          "live_sha256": sha(p / "live-name.json"), "control_sha256": sha(p / "live-name-control.json"),
          "mask_sha256": sha(args.fonts / "GAME.TXT-0x00000A7A.json"),
          "screenshots_sha256": {name: sha(p / f"live-name.{name}.png") for name in shots},
          "accepted_event": accepted[0], "applied_frames": len(applied)}
args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print("目標096 真視窗中文提示及同狀態：PASS")
