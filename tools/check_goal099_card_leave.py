#!/usr/bin/env python3
"""獨立核對第一張旗卡正常完成區離頁的雙重播與無觀測控制。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
BASE_INDEXED_SHA = "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835"
BASE_CANVAS_SHA = "2e005b93f811c7e0eb557eb68d1f5c1721caf027e5f32220c3c62195e7c9100b"
LEFT_NAME_INDEXED_SHA = "e4f2c72c82042aad1333fc7388bbd55b9b8f13bf1c82684c9462df80a4805e8c"
LEFT_NAME_CANVAS_SHA = "4b3549e17aba643a3a8f4759588fe4d6ab63b10b518bf1dda6785a7f71b678d8"
LABELS = ("43m", "44m", "45m", "46m", "49m")
RECTS = ((125, 12, 190, 24), (125, 83, 190, 96))


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def changed_in_rect(left, right, rect):
    x0, y0, x1, y1 = rect
    return sum(left[y * 320 + x] != right[y * 320 + x]
               for y in range(y0, y1) for x in range(x0, x1))


def verify(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    a_bytes = (p / "leave-a.json").read_bytes()
    need(a_bytes == (p / "leave-b.json").read_bytes(), "雙次冷啟動報告不同")
    a = json.loads(a_bytes)
    control = json.loads((p / "leave-control.json").read_bytes())
    need(a["version"] == control["version"] == "goal099-first-card-leave-v1" and
         a["input_sha256"] == control["input_sha256"] == INPUT_SHA and
         a["source_hashes"] == control["source_hashes"] and
         a["samples"] == control["samples"] and
         a["opened"] == control["opened"] and
         not a["control"] and control["control"] and
         not control["writers_after_43m"],
         "觀測器改變 CPU／RAM／索引／色盤／時間或控制不乾淨")
    need([a["samples"][name]["step"] for name in LABELS] ==
         [43_000_000, 44_000_000, 45_000_000, 46_000_000, 49_000_000] and
         [a["samples"][name]["opened_count"] for name in LABELS] ==
         [51, 51, 51, 53, 53] and
         [a["samples"][name]["last_opened"] for name in LABELS] ==
         ["NATIONS.PIK"] * 3 + ["GAME.TXT"] * 2 and
         a["opened"][-2:] == ["WOODPANL.PIK", "GAME.TXT"] and
         a["samples"]["43m"]["indexed_sha256"] == BASE_INDEXED_SHA and
         a["samples"]["43m"]["canvas_sha256"] == BASE_CANVAS_SHA and
         a["samples"]["46m"]["indexed_sha256"] ==
         a["samples"]["49m"]["indexed_sha256"] == LEFT_NAME_INDEXED_SHA and
         a["samples"]["46m"]["canvas_sha256"] ==
         a["samples"]["49m"]["canvas_sha256"] == LEFT_NAME_CANVAS_SHA,
         "第一張旗卡直接完成的畫面或開檔相位不符")
    for label in LABELS:
        for suffix in ("idx", "canvas", "pal"):
            left = (p / f"leave-a.{label}.{suffix}").read_bytes()
            for variant in ("leave-b", "leave-control"):
                need(left == (p / f"{variant}.{label}.{suffix}").read_bytes(),
                     f"雙次或控制原版畫素不同：{label}/{suffix}")
            need(len(left) == (768 if suffix == "pal" else 64000),
                 "原版畫布或色盤長度不符")
    before = (p / "leave-a.43m.canvas").read_bytes()
    after = (p / "leave-a.46m.canvas").read_bytes()
    differences = [changed_in_rect(before, after, rect) for rect in RECTS]
    need(differences == [761, 829] and
         sum(x != y for x, y in zip(before, after)) == 63265,
         "離頁後舊旗卡安全區仍可沿用的假設未被推翻")
    receipt = {"result": "PASS", "scope": "第一張國家旗卡直接點完成區至下一畫面；非中文正式覆蓋",
               "input_sha256": INPUT_SHA, "source_report_sha256": sha(a_bytes),
               "first_card_canvas_sha256": BASE_CANVAS_SHA,
               "left_name_canvas_sha256": LEFT_NAME_CANVAS_SHA,
               "card_rect_changed_pixels_after_leave": differences,
               "observed_matches_control": True,
               "limitations": "第三次 Enter、其他旗卡及正式逐欄中文回退另驗"}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("PASS：第一張旗卡直接完成後重繪兩欄；雙次與無觀測控制同狀態")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
