#!/usr/bin/env python3
"""獨立核對姓名欄 dosgolem 雙路收據與 Ebitengine A／B 原型。"""

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops


SCENARIOS = ("idle", "letter", "backspace", "enter")
SAMPLES = ("before", "before_ink", "after", "49m", "55m", "57m", "65m")
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
NAME_SHA = "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"
SAFE = (80, 100, 245, 111)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def diff_points(a, b):
    need(len(a) == len(b) == 64000, "索引或畫布長度不符")
    return [(i % 320, i // 320, a[i], b[i]) for i in range(64000) if a[i] != b[i]]


def bbox(points):
    return (min(z[0] for z in points), min(z[1] for z in points),
            max(z[0] for z in points) + 1, max(z[1] for z in points) + 1)


def section(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def verify(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據目錄不存在或擁有者不符")
    name_file = (args.game / "NAMES.TXT").read_bytes()
    need(sha(name_file) == NAME_SHA and
         name_file[0xB4B:0xB4B + 15] == b"Jacques Cartier", "原始姓名來源不符")
    need((p / "idle-a.json").read_bytes() == (p / "idle-b.json").read_bytes(),
         "雙次獨立冷啟動報告不同")
    records = {}
    for scene in SCENARIOS:
        record = load(p / f"{scene}-a.json")
        control = load(p / f"{scene}-control.json")
        need(record["version"] == control["version"] == "goal097-name-field-v1" and
             record["scenario"] == control["scenario"] == scene and
             record["input_sha256"] == control["input_sha256"] == INPUT_SHA and
             record["samples"] == control["samples"] and
             record["opened"] == control["opened"] and
             not control["reads"] and not control["writes"],
             "原版觀測／控制狀態不符：" + scene)
        for sample in SAMPLES:
            for suffix in ("idx", "canvas", "pal"):
                need((p / f"{scene}-a.{sample}.{suffix}").read_bytes() ==
                     (p / f"{scene}-control.{sample}.{suffix}").read_bytes(),
                     "原版索引／畫布／色盤與控制不同：" + scene + "/" + sample)
        records[scene] = record
    record = records["idle"]
    need(record["samples"]["before_ink"]["step"] == 48746663 and
         record["samples"]["after"]["step"] == 48764342 and
         record["samples"]["55m"]["indexed_sha256"] ==
         "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e",
         "姓名印字相位或穩定畫面基準不符")
    for scene in SCENARIOS[1:]:
        for sample in ("before", "before_ink", "after", "49m", "55m"):
            need(records[scene]["samples"][sample] == record["samples"][sample],
                 "姓名編輯前置狀態不相同：" + scene + "/" + sample)
    name_reads = bytes(z["value"] for z in record["reads"] if z["linear"] == 0x2A972)
    need(name_reads.endswith(b"Jacques Cartier_") and
         name_reads[:-len(b"Jacques Cartier_")].strip() == b"" and
         all(z["cs_ip"] == "0D21:00C6" for z in record["reads"]),
         "預設姓名原版逐字讀取與來源不同")
    writes = record["writes"]
    name_writes = [z for z in writes if z["cs_ip"] == "0D21:012C"]
    need(len(name_writes) == 286 and
         bbox([(z["x"], z["y"]) for z in name_writes]) == (82, 101, 164, 110) and
         Counter(z["new"] for z in name_writes) == {68: 132, 47: 89, 128: 65},
         "姓名 286 筆原版畫布寫入、墨跡或色號不符")
    before_frame = (p / "idle-a.before.canvas").read_bytes()
    before_ink = (p / "idle-a.before_ink.canvas").read_bytes()
    after = (p / "idle-a.after.canvas").read_bytes()
    frame_points = diff_points(before_frame, before_ink)
    ink_points = diff_points(before_ink, after)
    need(len(frame_points) == 1077 and bbox(frame_points) == (79, 98, 246, 112) and
         Counter(z[1] for z in frame_points)[98] == 167 and
         Counter(z[1] for z in frame_points)[111] == 167,
         "輸入框上下邊線證據不符")
    need(len(ink_points) == 285 and bbox(ink_points) == (82, 101, 164, 110) and
         Counter(z[3] for z in ink_points) == {68: 131, 47: 89, 128: 65} and
         all(SAFE[0] <= z[0] < SAFE[2] and SAFE[1] <= z[1] < SAFE[3]
             for z in ink_points) and
         section(after, SAFE) == section((p / "idle-a.55m.idx").read_bytes(), SAFE),
         "字形淨差分、安全區或 55M 穩定畫面不符")
    idle57 = (p / "idle-a.57m.idx").read_bytes()
    letter57 = (p / "letter-a.57m.idx").read_bytes()
    letter_points = diff_points(idle57, letter57)
    need(len(letter_points) == 733 and
         all(79 <= x < 246 and 98 <= y < 112 for x, y, _, _ in letter_points),
         "輸入 x 的畫面差分越出姓名欄")
    letter65 = (p / "letter-a.65m.idx").read_bytes()
    back65 = (p / "backspace-a.65m.idx").read_bytes()
    back_points = diff_points(letter65, back65)
    need(len(back_points) == 35 and
         all(79 <= x < 246 and 98 <= y < 112 for x, y, _, _ in back_points),
         "退格差分越出姓名欄")
    enter_points = diff_points((p / "idle-a.65m.idx").read_bytes(),
                               (p / "enter-a.65m.idx").read_bytes())
    need(len(enter_points) == 14167 and
         records["enter"]["samples"]["65m"]["opened_count"] >
         record["samples"]["65m"]["opened_count"],
         "Enter 未進入下一玩家狀態")
    meta = load(p / "metadata.json")
    need(meta["placeholder_is_translation"] is False and
         meta["font_size"] == 38 and meta["safe"] == list(SAFE) and
         meta["ink_size"] == [268, 35] and meta["position"] == [328, 404],
         "示意譯名被誤當正式譯文或幾何不符")
    a = Image.open(p / "choice-a-formal.png").convert("RGB")
    b = Image.open(p / "choice-b-formal.png").convert("RGB")
    formal = Image.open(args.formal).convert("RGB")
    need(a.size == b.size == formal.size == (1280, 800) and
         a.tobytes() == formal.tobytes() and
         sha(args.formal.read_bytes()) == meta["formal_base_sha256"],
         "A 圖不是原已驗真視窗畫面")
    diff = ImageChops.difference(a, b)
    bounds = diff.getbbox()
    need(bounds == (328, 404, 656, 440), "A/B 差分框不符")
    for y in range(800):
        for x in range(1280):
            if a.getpixel((x, y)) != b.getpixel((x, y)):
                need(SAFE[0] * 4 <= x < SAFE[2] * 4 and
                     SAFE[1] * 4 <= y < SAFE[3] * 4,
                     "原型改動越出姓名欄安全區")
    receipt = {"result": "PASS", "scope": "disposable layout comparison only",
               "goal": "097", "input_sha256": INPUT_SHA,
               "probe_report_sha256": sha((p / "idle-a.json").read_bytes()),
               "original_name_ink_writes": len(name_writes),
               "original_name_net_pixels": len(ink_points),
               "name_safe_original": SAFE, "choice_diff_bbox_4x": bounds,
               "choice_a_png_sha256": sha((p / "choice-a-formal.png").read_bytes()),
               "choice_b_png_sha256": sha((p / "choice-b-formal.png").read_bytes()),
               "editable_name_translation_decided": False,
               "name_placeholder_is_translation": False}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("PASS：雙次原版、各分支控制及真視窗 A/B 差分均符合限定原型契約")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())


if __name__ == "__main__":
    main()
