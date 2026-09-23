#!/usr/bin/env python3
"""獨立核對首次國家介紹兩頁的 DOS 來源、原版印字與同狀態畫布。"""

import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path

from PIL import Image


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
A_BLOCK_SHA = "8b9eec55083e64f4c45989631dbcd512b3019a978af5a84c7ad4e59ba0a2534b"
B_BLOCK_SHA = "78da983dc6a4bfc965e8ab616ec1bdd6dd2c18c8901fc2015c2e371c518d78ae"
A_PRINT_SHA = "7285983b0263b270b7e952a78aecc40e0fa682e45302ae088371b493da0a258b"
B_PRINT_SHA = "9018be96a5ab5eb08fcb830beaa493a6090b6aec2eecdd682594065d6a6971d9"
SAMPLES = ("55m", "56m", "57m", "60m", "65m")
NEXT_SAMPLES = SAMPLES + ("70m", "75m")
OFFSETS = (0xB2DB, 0xB2F2, 0xB303, 0xB641, 0xB658)
CATALOG_COLUMNS = ("message_id", "source_file", "source_file_sha256",
                   "section_offset", "section_byte_length", "section_sha256",
                   "source_en_display", "zh_hant_draft", "status", "notes")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def source_visible(block):
    parts = []
    for line in block.decode("cp437").splitlines():
        if line.startswith("@") or not line or line.startswith("^^_"):
            continue
        if line.startswith("^^") or line.startswith("__"):
            line = line[2:]
        parts.append(line.replace("{", "").replace("}", ""))
    return "".join(parts).encode("cp437")


def check_catalog(path, game):
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        need(tuple(reader.fieldnames or ()) == CATALOG_COLUMNS,
             "介紹譯稿 TSV 欄位契約不符")
        rows = list(reader)
    sections = (("GAME.TXT:@NATION1A", 0xB2DB, 0xB641, A_BLOCK_SHA),
                ("GAME.TXT:@NATION1B", 0xB641, 0xB73E, B_BLOCK_SHA))
    need(len(rows) == len(sections), "介紹譯稿不是精確兩段")
    for row, (key, start, end, digest) in zip(rows, sections):
        need(None not in row and row["message_id"] == key and
             row["source_file"] == "GAME.TXT" and
             row["source_file_sha256"] == GAME_SHA and
             row["section_offset"] == f"0x{start:08X}" and
             row["section_byte_length"] == str(end - start) and
             row["section_sha256"] == digest and row["status"] == "draft" and
             row["notes"] and row["zh_hant_draft"].startswith("法國\\n"),
             f"介紹譯稿的來源鍵、版本或草稿狀態不符：{key}")
        original = source_visible(game[start:end]).decode("cp437")
        display = row["source_en_display"].replace("\\n", "")
        compact = lambda value: re.sub(r"\s|[{}]", "", value)
        need(compact(display) == compact(original),
             f"介紹譯稿英文明文與原始段落不符：{key}")
        for value in (row["source_en_display"], row["zh_hant_draft"]):
            need(value.count("{") == value.count("}") and
                 "\n" not in value and "\r" not in value and "\t" not in value,
                 f"介紹譯稿控制標記或 TSV 換行錯誤：{key}")
        need(row["source_en_display"].count("{") ==
             row["zh_hant_draft"].count("{"),
             f"介紹譯稿強調標記數量不符：{key}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def printed(record, start, end):
    events = [x for x in record["print_reads"]
              if x["cs_ip"] == "0D21:00C6" and start <= x["step"] < end]
    raw = bytes(x["value"] for x in events)
    need(len(raw) % 2 == 0 and
         all(raw[i] == 0 for i in range(1, len(raw), 2)) and
         all(x["linear"] == (0x2A862 if i % 2 == 0 else 0x2A863)
             for i, x in enumerate(events)), "原版逐字讀取不是已驗二位元組模式")
    return raw[::2]


def ink_groups(writer):
    rows = {int(y): data for y, data in writer["rows"].items()}
    groups = []
    for y in sorted(rows):
        if not groups or y > groups[-1][-1] + 1:
            groups.append([y])
        else:
            groups[-1].append(y)
    return [(group[0], group[-1], sum(rows[y]["count"] for y in group),
             min(rows[y]["min_x"] for y in group),
             max(rows[y]["max_x"] for y in group)) for group in groups]


def verify(args):
    p = args.reports
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據目錄不存在或擁有者不符")
    source = args.game / "GAME.TXT"
    if not source.is_file():
        print("SKIP：合法 DOS 原版 GAME.TXT 不存在")
        return
    game = source.read_bytes()
    need(sha(game) == GAME_SHA and
         sha(game[0xB2DB:0xB641]) == A_BLOCK_SHA and
         sha(game[0xB641:0xB73E]) == B_BLOCK_SHA,
         "原版 GAME.TXT 或兩段來源版本不符")
    catalog_sha = check_catalog(args.catalog, game)
    a_bytes, b_bytes = (p / "intro-a.json").read_bytes(), (p / "intro-b.json").read_bytes()
    need(a_bytes == b_bytes, "雙次冷啟動報告不同")
    first, first_control = load(p / "intro-a.json"), load(p / "intro-control.json")
    next_page, next_control = load(p / "next-a.json"), load(p / "next-control.json")
    for record, control, labels, expect_next in (
            (first, first_control, SAMPLES, False),
            (next_page, next_control, NEXT_SAMPLES, True)):
        need(record["version"] == control["version"] == "goal098-intro-v3" and
             record["input_sha256"] == control["input_sha256"] == INPUT_SHA and
             record["next_enter"] is control["next_enter"] is expect_next and
             record["sources"] == control["sources"] and
             record["transfers"] == control["transfers"] and
             record["samples"] == control["samples"] and
             record["opened"] == control["opened"] and
             not control["print_reads"] and not control["writers"],
             "觀測改變原版狀態或控制不乾淨")
        name = "next" if expect_next else "intro"
        for label in labels:
            for suffix in ("idx", "canvas", "pal"):
                left = (p / f"{name}-a.{label}.{suffix}").read_bytes()
                right = (p / f"{name}-control.{label}.{suffix}").read_bytes()
                need(left == right, f"原版畫布／索引／色盤與控制不同：{name}/{label}/{suffix}")
                if not expect_next:
                    also = (p / f"intro-b.{label}.{suffix}").read_bytes()
                    need(left == also, "兩次冷啟動畫面不同")
    need([x["file_offset"] for x in first["transfers"]] == list(OFFSETS) and
         [x["file_offset"] for x in next_page["transfers"]] == list(OFFSETS) * 2 and
         all(x["match"] and x["name"].upper() == "GAME.TXT"
             for x in next_page["transfers"]) and
         [x["step"] for x in first["transfers"]] ==
         [56918755] * 3 + [56974308] * 2 and
         [x["step"] for x in next_page["transfers"][5:]] ==
         [66919650] * 3 + [66950288] * 2,
         "GAME.TXT A／B 候選 DOS 讀入相位或來源不同")
    need(first["samples"]["55m"]["opened_count"] == 53 and
         first["samples"]["65m"]["opened_count"] == 54 and
         next_page["samples"]["75m"]["opened_count"] == 55 and
         first["samples"]["60m"]["indexed_sha256"] ==
         first["samples"]["65m"]["indexed_sha256"] ==
         "aa987cee149ab9503b919dccd6747f57c87c94cbdb026fcdd1edb070ad7aafe5" and
         next_page["samples"]["70m"]["indexed_sha256"] ==
         next_page["samples"]["75m"]["indexed_sha256"] ==
         "19c0622b683673f929daedda9dc6b61bfc06d2e048165f376c15af28bb2dbb0a" and
         next_page["samples"]["65m"] == first["samples"]["65m"],
         "兩頁開檔、穩定畫面或共同起點不同")
    first_print = printed(first, 55_000_000, 65_000_000)
    second_print = printed(next_page, 65_000_000, 75_000_000)
    need(len(first_print) == 794 and sha(first_print) == A_PRINT_SHA and
         len(second_print) == 207 and sha(second_print) == B_PRINT_SHA and
         printed(next_page, 55_000_000, 65_000_000) == first_print and
         source_visible(game[0xB2DB:0xB641]).replace(b" ", b"") ==
         first_print.replace(b" ", b"") and
         source_visible(game[0xB641:0xB73E]).replace(b" ", b"") ==
         second_print.replace(b" ", b""),
         "A／B 來源與原版逐字輸出不符；不得以預讀充當畫面命中")
    first_ink = first["writers"]["first/0D21:012C"]
    second_ink = next_page["writers"]["second/0D21:012C"]
    need(first_ink["count"] == 13412 and first_ink["bbox"] == [10, 25, 304, 174] and
         len(ink_groups(first_ink)) == 14 and
         ink_groups(first_ink)[0][:2] == (25, 32) and
         ink_groups(first_ink)[1][:2] == (45, 53) and
         ink_groups(first_ink)[-1][:2] == (165, 173) and
         second_ink["count"] == 3438 and second_ink["bbox"] == [10, 70, 308, 129] and
         [(x[0], x[1]) for x in ink_groups(second_ink)] ==
         [(70, 77), (90, 98), (100, 108), (110, 118), (122, 128)],
         "逐頁標題、正文畫素分布或原版印字相位不符")
    original_idx = (p / "intro-a.65m.idx").read_bytes()
    original_pal = (p / "intro-a.65m.pal").read_bytes()
    need(len(original_idx) == 64000 and len(original_pal) == 768 and max(original_pal) <= 63,
         "原版索引或色盤格式不符")
    screen = Image.frombytes("P", (320, 200), original_idx)
    screen.putpalette([(v << 2) | (v >> 4) for v in original_pal])
    expected = screen.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
    prior = Image.open(args.prior_ebiten).convert("RGB")
    need(prior.size == expected.size and prior.tobytes() == expected.tobytes(),
         "首次介紹畫面未與既有 Ebitengine 原文控制圖逐像素對齊")
    receipt = {"result": "PASS", "scope": "首段 A 與 Enter 後 B 的原版來源、印字與畫素；未接正式中文",
               "source_game_sha256": GAME_SHA, "input_sha256": INPUT_SHA,
               "catalog_sha256": catalog_sha, "catalog_rows": 2,
               "first_report_sha256": sha(a_bytes),
               "second_report_sha256": sha((p / "next-a.json").read_bytes()),
               "first_source_sha256": A_BLOCK_SHA, "second_source_sha256": B_BLOCK_SHA,
               "first_print_chars": len(first_print), "second_print_chars": len(second_print),
               "first_ink_writes": first_ink["count"], "second_ink_writes": second_ink["count"],
               "first_ink_bbox": first_ink["bbox"], "second_ink_bbox": second_ink["bbox"],
               "first_ink_rows": ink_groups(first_ink), "second_ink_rows": ink_groups(second_ink),
               "observed_matches_control": True, "prior_ebiten_control_pixel_exact": True,
               "limitations": "未驗第二頁真視窗、第三頁／離頁、中文換行與回退；不得宣稱完成覆蓋"}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("PASS：兩段原版來源、實際印字、逐頁畫素與同狀態控制閉合")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--prior-ebiten", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
