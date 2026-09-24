#!/usr/bin/env python3
"""核對四國開場字幕占位值的原版檔案候選與實際印字；不授權正式覆蓋。"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

from check_goal108_caption_corpus import BLOCKS, GAME_SHA, INPUT_SHA, VERSION


NAMES_SHA = "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"
NATIONS = ("england", "france", "spain", "netherlands")
SLOTS = (("@BUILD2", "%STRING0"), ("@BUILD2", "%STRING1"),
         ("@BUILD3", "%STRING0"), ("@BUILD4", "%STRING0"),
         ("@BUILD4", "%STRING1"), ("@BUILD7", "%STRING0"))
OFFSETS = {
    "england": (0xC18, 0xB27, 0x9C1, 0x8EA, 0xCB9C, 0x8EA),
    "france": (0xC18, 0xB4B, 0x9C9, 0x906, 0xCBA2, 0x906),
    "spain": (0xC18, 0xB6F, 0x9D6, 0x921, 0xCBA8, 0x921),
    "netherlands": (0xC18, 0xB93, 0x9DF, 0x93D, 0xCBAE, 0x93D),
}
COORDS = {"england": (155, 50), "france": (255, 50),
          "spain": (155, 150), "netherlands": (255, 150)}
HEADER = ("nation", "caption", "placeholder", "source_file", "source_file_sha256",
          "byte_offset", "source_byte_length", "source_bytes_sha256", "source_text",
          "observed_text", "zh_hant", "status", "evidence")


class Invalid(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise Invalid(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_rows(catalog):
    with catalog.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        need(tuple(reader.fieldnames or ()) == HEADER, "字幕變數 TSV 欄位不符")
        rows = list(reader)
    need(len(rows) == len(NATIONS) * len(SLOTS), "字幕變數須恰有四國各六筆")
    result = {}
    for row in rows:
        need(None not in row and all(value is not None and "\t" not in value
                                     for value in row.values()),
             "字幕變數 TSV 有缺漏或額外欄位")
        key = (row["nation"], row["caption"], row["placeholder"])
        need(row["nation"] in NATIONS and key[1:] in SLOTS and key not in result,
             "字幕變數國別、占位符或重複鍵不符：" + repr(key))
        need(row["status"] == "draft" and row["zh_hant"] and row["evidence"],
             "字幕變數不得空譯或冒稱 READY")
        result[key] = row
    need(set(result) == {(nation, *slot) for nation in NATIONS for slot in SLOTS},
         "字幕變數有缺鍵")
    return result


def lookup(rows, nation, caption, placeholder, observed_text):
    """只供草稿查詢；國別、欄位或當次原值不符就不給中文候選。"""
    row = rows.get((nation, caption, placeholder))
    if row is None or row["observed_text"] != observed_text or row["status"] != "draft":
        return None
    return row["zh_hant"]


def check(game, catalog, reports, england_reports):
    if not (game / "GAME.TXT").is_file() or not (game / "NAMES.TXT").is_file():
        return {"result": "SKIP", "reason": "合法原版 GAME.TXT／NAMES.TXT 缺失"}
    originals = {name: (game / name).read_bytes() for name in ("GAME.TXT", "NAMES.TXT")}
    need(sha(originals["GAME.TXT"]) == GAME_SHA and
         sha(originals["NAMES.TXT"]) == NAMES_SHA, "合法原版版本不符")
    rows = load_rows(catalog)
    for nation in NATIONS:
        for index, (caption, placeholder) in enumerate(SLOTS):
            row = rows[(nation, caption, placeholder)]
            filename = "GAME.TXT" if index == 4 else "NAMES.TXT"
            source = originals[filename]
            offset = OFFSETS[nation][index]
            fragment = row["source_text"].encode("ascii")
            need(row["source_file"] == filename and
                 row["source_file_sha256"] == sha(source) and
                 int(row["byte_offset"], 16) == offset and
                 int(row["source_byte_length"]) == len(fragment) and
                 source[offset:offset + len(fragment)] == fragment and
                 row["source_bytes_sha256"] == sha(fragment) and
                 row["observed_text"] and row["observed_text"].isascii(),
                 f"{nation} {caption} {placeholder} 原版來源候選不符")

    receipt = {"result": "PASS", "nations": {}, "draft_rows": len(rows),
               "scope": "四國固定難度正常路徑的可見值與檔案候選；未驗正式中文畫面"}
    for nation in NATIONS:
        base = england_reports if nation == "england" else reports
        stem = "england-no-extra-1350m" if nation == "england" else nation + "-800m"
        raw = [(base / f"{stem}-{suffix}.json").read_bytes()
               for suffix in ("explore", "b", "control")]
        need(raw[0] == raw[1], nation + " dosgolem 雙重播報告不同")
        observed, control = json.loads(raw[0]), json.loads(raw[2])
        need(observed["version"] == control["version"] == VERSION and
             observed["nation"] == control["nation"] == nation and
             observed["input_sha256"] == control["input_sha256"] == INPUT_SHA and
             observed["input_hashes"]["GAME.TXT"] == GAME_SHA and
             observed["input_hashes"]["NAMES.TXT"] == NAMES_SHA and
             observed["control"] is False and control["control"] is True and
             not control["print_reads"] and not control["writers"] and
             observed["route"]["selected_x"] == COORDS[nation][0] and
             observed["route"]["selected_y"] == COORDS[nation][1] and
             observed["next_enter"] and observed["after_b"] == "enter" and
             observed["after_follow"] == "enter", nation + " 重播條件不符")
        for field in ("route", "sources", "transfers", "samples", "opened", "key_events"):
            need(observed[field] == control[field], nation + " 監看改變原版狀態：" + field)
        events = [event for event in observed["print_reads"]
                  if event["step"] >= 85_000_000 and event["cs_ip"] == "0D21:00C6"]
        groups = []
        for event in events:
            if not groups or event["step"] - groups[-1][-1]["step"] > 1_000_000:
                groups.append([])
            groups[-1].append(event)
        need(len(groups) >= 7, nation + " 未印出前七張字幕")
        if nation != "england":
            need(len(groups) == 7 and observed["follow_until"] == 800_000_000,
                 nation + " 有界收據段數／停止步數不符")
        for number, (_, lines) in enumerate(BLOCKS[:7], 1):
            expanded = bytearray()
            for offset, length, digest in lines:
                original = originals["GAME.TXT"][offset:offset + length]
                need(sha(original) == digest and original.startswith(b"^^"),
                     f"@BUILD{number} 原版模板不符")
                part = original[2:]
                for slot in ("%STRING0", "%STRING1"):
                    row = rows.get((nation, f"@BUILD{number}", slot))
                    if row is not None:
                        part = part.replace(slot.encode("ascii"), row["observed_text"].encode("ascii"))
                need(b"%STRING" not in part, f"@BUILD{number} 有未知占位符")
                expanded.extend(part)
            group = groups[number - 1]
            need(len(group) == 2 * len(expanded) and
                 all(event["value"] == 0 for event in group[1::2]) and
                 bytes(event["value"] for event in group[::2]) == expanded,
                 f"{nation} @BUILD{number} 實際印字與來源候選不同")
        receipt["nations"][nation] = {
            "observed_report_sha256": sha(raw[0]),
            "control_report_sha256": sha(raw[2]),
            "caption_count_checked": 7,
            "placeholder_occurrences_checked": len(SLOTS),
        }
    receipt["catalog_sha256"] = sha(catalog.read_bytes())
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--catalog", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                        "text/build-caption-values.zh-Hant.tsv")
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--england-reports", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check(args.game, args.catalog, args.reports, args.england_reports)
        if args.out:
            need(args.out.parent.is_dir(), "收據輸出目錄不存在")
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    except (Invalid, OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        print("驗證失敗：" + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    sys.exit(main())
