#!/usr/bin/env python3
"""目標096：逐欄缺譯、字模、游標及同狀態回退的獨立核對。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


KEY = "GAME.TXT:0x00000A7A"
PROMPT = (400, 340, 876, 392)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image(path):
    value = Image.open(path).convert("RGB")
    need(value.size == (1280, 800), f"尺寸不符：{path}")
    return value


def line(frame):
    matches = [item for item in frame["lines"] if item["candidate_id"] == KEY]
    need(len(matches) == 1, "提示欄記錄數不符")
    return matches[0]


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--reports", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
need(args.out.parent.is_dir() and args.out.parent.stat().st_uid == os.getuid(),
     "收據目錄不存在或擁有者不符")
p = args.reports
names = ("baseline", "control", "missing", "duplicate", "missing-mask",
         "wrong-size", "cursor", "cursor-control")
reports = {name: load(p / f"{name}.json") for name in names}
shots = {name: image(p / f"{name}.final.png") for name in names}
baseline = reports["baseline"]
control = reports["control"]
need(not baseline["control"] and control["control"] and
     baseline["state"] == control["state"] and baseline["opened"] == control["opened"] and
     (p / "baseline.memory").read_bytes() == (p / "control.memory").read_bytes(),
     "正常提示覆蓋擾動原版狀態")
for suffix in ("idx", "pal"):
    need((p / f"baseline.final.{suffix}").read_bytes() ==
         (p / f"control.final.{suffix}").read_bytes(),
         f"正常提示覆蓋擾動原版畫面：{suffix}")
need(line(baseline["frames"][-1])["applied"] and
     ImageChops.difference(shots["baseline"].crop(PROMPT),
                           shots["control"].crop(PROMPT)).getbbox() is not None,
     "基準畫面沒有中文提示")

reasons = {"missing": "missing-or-invalid-translation",
           "duplicate": "missing-or-invalid-translation",
           "missing-mask": "font-mask-unavailable",
           "wrong-size": "font-binding-mismatch"}
for name, reason in reasons.items():
    report = reports[name]
    need(report["state"] == control["state"] and report["opened"] == control["opened"] and
         (p / f"{name}.memory").read_bytes() == (p / "control.memory").read_bytes(),
         f"{name} 擾動原版 CPU／RAM／時間或開檔")
    for suffix in ("idx", "pal"):
        need((p / f"{name}.final.{suffix}").read_bytes() ==
             (p / f"control.final.{suffix}").read_bytes(),
             f"{name} 擾動原版索引或色盤")
    final = line(report["frames"][-1])
    need(not final["applied"] and final["reason"] == reason and
         final["accepted_events"] == 1,
         f"{name} 未逐欄回退，或回退理由不符")
    need(ImageChops.difference(shots[name].crop(PROMPT),
                               shots["control"].crop(PROMPT)).getbbox() is None,
         f"{name} 未顯示原文提示")
    outside = shots[name].copy()
    outside.paste(shots["baseline"].crop(PROMPT), PROMPT)
    need(ImageChops.difference(outside, shots["baseline"]).getbbox() is None,
         f"{name} 誤傷提示區以外的既有十四欄")

cursor = reports["cursor"]
cursor_control = reports["cursor-control"]
need(cursor["state"] == cursor_control["state"] and
     cursor["opened"] == cursor_control["opened"] and
     (p / "cursor.memory").read_bytes() ==
     (p / "cursor-control.memory").read_bytes(), "游標負例擾動原版狀態")
for suffix in ("idx", "pal"):
    need((p / f"cursor.final.{suffix}").read_bytes() ==
         (p / f"cursor-control.final.{suffix}").read_bytes(),
         "游標負例擾動原版索引或色盤")
near = [(f["step"], line(f)) for f in cursor["frames"] if
        55_500_000 <= f["step"] < 57_500_000]
need(any(step < 56_000_000 and item["applied"] for step, item in near) and
     any(56_000_000 <= step < 57_000_000 and not item["applied"] and
         item["reason"] == "frame-mismatch" for step, item in near) and
     any(step >= 57_000_000 and item["applied"] for step, item in near),
     "游標遮擋未回退英文或移開後未恢復中文")
need(not (p / "wrong-version.json").exists() and
     sha(p / "wrong-game/GAME.TXT") != baseline["input_hashes"]["GAME.TXT"],
     "錯版測試未在輸出前拒絕")

result = {"result": "PASS", "scope": "四類逐欄回退、游標遮擋與移開、同輸入控制；錯版另由腳本核對 exit 2",
          "baseline_state_sha256": sha(p / "baseline.memory"),
          "cases": {name: {"reason": reason, "report_sha256": sha(p / f"{name}.json")}
                    for name, reason in reasons.items()},
          "cursor_report_sha256": sha(p / "cursor.json"),
          "wrong_original_sha256": sha(p / "wrong-game/GAME.TXT")}
args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print("目標096 逐欄回退、游標與錯版負例：PASS")
