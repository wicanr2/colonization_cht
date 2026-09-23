#!/usr/bin/env python3
"""獨立驗證姓名畫面來源、鍵盤分支及 Ebitengine 原文控制圖。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


SCENARIOS = ("idle", "letter", "backspace", "enter", "letter-enter")
SAMPLES = ("49m", "55m", "57m", "65m")
NAME_RECT = (79, 98, 246, 112)
ORIGINAL_INDEX_SHA = "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def report(path):
    return json.loads(path.read_text())


def diff_points(a, b):
    need(len(a) == len(b) == 64000, "原版索引畫面大小不符")
    return [(i % 320, i // 320) for i, (left, right) in enumerate(zip(a, b)) if left != right]


def in_rect(points, rect):
    x0, y0, x1, y1 = rect
    return all(x0 <= x < x1 and y0 <= y < y1 for x, y in points)


def confirm_ebitengine(p, scene, sample, png_scene=None):
    data = report(p / f"{scene}-a.json")
    indexed = (p / f"{scene}-a.{sample}.idx").read_bytes()
    palette = (p / f"{scene}-a.{sample}.pal").read_bytes()
    need(sha(indexed) == data["samples"][sample]["indexed_sha256"] and
         sha(palette) == data["samples"][sample]["palette_sha256"] and
         len(palette) == 768 and max(palette) <= 63, "Ebitengine 來源收據不符")
    lut = [tuple((v << 2) | (v >> 4) for v in palette[i:i + 3])
           for i in range(0, len(palette), 3)]
    rgb = bytes(c for index in indexed for c in lut[index])
    expected = Image.frombytes("RGB", (320, 200), rgb).resize((1280, 800), Image.Resampling.NEAREST)
    png_path = p / f"{png_scene or scene}-control.png"
    png = Image.open(png_path).convert("RGB")
    need(png.size == expected.size and png.tobytes() == expected.tobytes(),
         "Ebitengine 控制圖不等於原版索引／色盤四倍畫布：" + scene)
    return sha(png_path.read_bytes())


def verify(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    source_a = p / "source3-a.json"
    source_b = p / "source3-b.json"
    need(source_a.read_bytes() == source_b.read_bytes(), "兩次來源冷啟動不一致")
    source = report(source_a)
    control = report(p / "source3-control.json")
    need(source["version"] == "goal093-name-v1" and source["scenario"] == "idle" and
         source["samples"] == control["samples"] and source["opened"] == control["opened"] and
         source["transfers"] == control["transfers"] and
         not control["reads"] and not control["writes"] and not control["frames"],
         "來源觀測改變原版狀態或控制組不乾淨")
    need(source["samples"]["49m"]["indexed_sha256"] == ORIGINAL_INDEX_SHA and
         source["samples"]["55m"]["indexed_sha256"] == ORIGINAL_INDEX_SHA,
         "姓名畫面基準不符")
    transfers = source["transfers"]
    need(len(transfers) == 3 and all(x["match"] and x["got"] == 512 and x["read_pos"] == 2560
                                     for x in transfers), "DOS 讀入時原始位元組不符")
    need([(x["name"], x["file_offset"], x["step"]) for x in transfers] ==
         [("NAMES.TXT", 0xB4B, 15584990), ("NAMES.TXT", 0xB4B, 17057573),
          ("GAME.TXT", 0xA7C, 48655905)], "來源檔案或讀入相位不符")
    load_writes = [x for x in source["load_writes"] if 0x21AE2 <= x["linear"] < 0x21AF1]
    need(len(load_writes) == len(b"Jacques Cartier") and
         sorted(load_writes, key=lambda x: x["linear"]) == load_writes and
         bytes(x["New"] for x in load_writes) == b"Jacques Cartier" and
         all(x["step"] == 15612172 and x["cs_ip"] == "0E2D:11A5" for x in load_writes) and
         any(x["step"] == 15587654 and x["linear"] == 0x2B14D and x["value"] == 74
             for x in source["load_reads"]), "NAMES.TXT 至常駐 RAM 的來源鏈未閉合")
    prompt = bytes(x["value"] for x in source["reads"] if x["linear"] == 0x2A864)
    name = bytes(x["value"] for x in source["reads"] if x["linear"] == 0x2A972)
    need(prompt == b"Please Enter Your Name." and name.endswith(b"Jacques Cartier_") and
         name[:-len(b"Jacques Cartier_")].strip() == b"", "原版印字讀取序列不符")
    source_reads = source["source_reads"]
    for linear, value in ((0x21AE2, 74), (0x2B072, 80), (0x6F200, 80),
                          (0x6F25C, 74), (0x2AA06, 74)):
        need(any(x["linear"] == linear and x["value"] == value for x in source_reads),
             f"缺少原版 RAM 來源讀取 {linear:05X}")
    writes = source["writes"]
    need(len(writes) == 701 and all(x["cs_ip"] == "0D21:012C" for x in writes),
         "姓名畫面文字畫布寫入點不符")
    prompt_ink = [x for x in writes if 88 <= x["Y"] <= 96]
    name_ink = [x for x in writes if 101 <= x["Y"] <= 109]
    need(prompt_ink and name_ink and len(prompt_ink) + len(name_ink) == len(writes) and
         min(x["X"] for x in prompt_ink) == 104 and max(x["X"] for x in prompt_ink) == 214 and
         min(x["X"] for x in name_ink) == 82 and max(x["X"] for x in name_ink) == 163,
         "兩行原版墨跡座標不符")

    records = {}
    for scene in SCENARIOS:
        a = p / f"{scene}-a.json"
        b = p / f"{scene}-b.json"
        need(a.read_bytes() == b.read_bytes(), "兩次鍵盤冷啟動不一致：" + scene)
        record = report(a)
        control = report(p / f"{scene}-control.json")
        need(record["scenario"] == scene and record["samples"] == control["samples"] and
             record["opened"] == control["opened"] and record["transfers"] == control["transfers"] and
             not control["reads"] and not control["writes"] and not control["frames"],
             "鍵盤觀測改變原版狀態：" + scene)
        for sample in SAMPLES:
            need((p / f"{scene}-a.{sample}.idx").read_bytes() ==
                 (p / f"{scene}-control.{sample}.idx").read_bytes() and
                 (p / f"{scene}-a.{sample}.pal").read_bytes() ==
                 (p / f"{scene}-control.{sample}.pal").read_bytes(),
                 "觀測與控制圖不同：" + scene + "/" + sample)
        records[scene] = record

    idle57 = (p / "idle-a.57m.idx").read_bytes()
    idle65 = (p / "idle-a.65m.idx").read_bytes()
    letter57 = (p / "letter-a.57m.idx").read_bytes()
    back57 = (p / "backspace-a.57m.idx").read_bytes()
    back65 = (p / "backspace-a.65m.idx").read_bytes()
    enter65 = (p / "enter-a.65m.idx").read_bytes()
    letter_enter65 = (p / "letter-enter-a.65m.idx").read_bytes()
    need(idle57 == idle65 and records["idle"]["samples"]["55m"]["indexed_sha256"] == sha(idle57),
         "無輸入時姓名畫面不穩定")
    letter_diff = diff_points(idle57, letter57)
    back_diff = diff_points(letter57, back65)
    need(letter_diff and back_diff and in_rect(letter_diff, NAME_RECT) and
         in_rect(back_diff, NAME_RECT) and letter57 == back57 and
         letter57 == (p / "letter-a.65m.idx").read_bytes(),
         "字元或退格的差異超出姓名欄")
    need(len(diff_points(idle65, enter65)) > 10000 and enter65 == letter_enter65 and
         (p / "enter-a.65m.pal").read_bytes() == (p / "letter-enter-a.65m.pal").read_bytes() and
         records["enter"]["samples"]["65m"]["memory_sha256"] !=
         records["letter-enter"]["samples"]["65m"]["memory_sha256"] and
         len(records["enter"]["opened"]) == len(records["idle"]["opened"]) + 1 and
         records["enter"]["opened"][-1].upper() == "GAME.TXT", "Enter 下一畫面或姓名 RAM 差異不符")
    pngs = {"idle": confirm_ebitengine(p, "source3", "55m", "idle")}
    # 來源追蹤與按鍵重播均從相同的無按鍵原版畫面起跑，控制圖只需一張。
    need((p / "source3-a.55m.idx").read_bytes() == (p / "idle-a.55m.idx").read_bytes(),
         "來源追蹤與按鍵重播起點不同")
    for scene, sample in (("letter", "57m"), ("backspace", "65m"),
                          ("enter", "65m"), ("letter-enter", "65m")):
        pngs[scene] = confirm_ebitengine(p, scene, sample)
    result = {"result": "PASS", "scope": "姓名畫面來源與正常鍵盤分支；正式中文覆蓋未授權",
              "source_receipt_sha256": sha(source_a.read_bytes()),
              "input_receipts_sha256": {scene: sha((p / f"{scene}-a.json").read_bytes()) for scene in SCENARIOS},
              "source_transfer_matches": len(transfers), "print_canvas_writes": len(writes),
              "letter_changed_pixels": len(letter_diff), "backspace_changed_pixels": len(back_diff),
              "enter_changed_pixels": len(diff_points(idle65, enter65)),
              "same_state_observed_vs_controls": True, "ebitengine_controls_sha256": pngs,
              "limitations": "顯示譯文與可編輯姓名隔離、欄位安全矩形／字級及下一畫面文字未正式驗收"}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
