#!/usr/bin/env python3
"""核對四國八節介紹譯稿與固定 DOS GAME.TXT；不執行或修改遊戲。"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
COLUMNS = (
    "message_id", "source_file", "source_file_sha256", "section_offset",
    "section_byte_length", "section_sha256", "source_en_display",
    "zh_hant_draft", "status", "notes",
)
# 檔案位移，不是 RAM、CS:IP 或畫布座標。
SECTIONS = (
    ("NATION0A", 0xAE7C, 0xB204, "ENGLAND", "英格蘭", "7315f80026bfce88671deb0ed082dc09d4894fa6c7dd90d1a05cac83cd42be6c"),
    ("NATION0B", 0xB204, 0xB2DB, "ENGLAND", "英格蘭", "18c13609d357fb8b151c186abf54924d60a9d2312422557c8e9318b3ae74a9c1"),
    ("NATION1A", 0xB2DB, 0xB641, "FRANCE", "法國", "8b9eec55083e64f4c45989631dbcd512b3019a978af5a84c7ad4e59ba0a2534b"),
    ("NATION1B", 0xB641, 0xB73E, "FRANCE", "法國", "78da983dc6a4bfc965e8ab616ec1bdd6dd2c18c8901fc2015c2e371c518d78ae"),
    ("NATION2A", 0xB73E, 0xBB46, "SPAIN", "西班牙", "86990d9fdcfa4e77199d011d4d3fd6b7c140c1e92c6b1619c6a6b32feba0b2e6"),
    ("NATION2B", 0xBB46, 0xBC28, "SPAIN", "西班牙", "fda7944fa37e2959d5a8d0ebba7b6b37ac58948dc961eda2abfa664e1b4d96e5"),
    ("NATION3A", 0xBC28, 0xC032, "NETHERLANDS", "荷蘭", "de92a74437b235520e7b7eec2552ff3193daece1774c761138b7dee0f98898b4"),
    ("NATION3B", 0xC032, 0xC191, "NETHERLANDS", "荷蘭", "6f69bbd647044d79afa0d76248e69a961e555f4ce8bc4a4e41a226a9fad87bf6"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return re.sub(r"\s|[{}]", "", value)


def marked_spans(value, key):
    require(value.count("{") == value.count("}"), f"{key}: 大括號不成對")
    spans = re.findall(r"\{([^{}]+)\}", value)
    require(len(spans) == value.count("{"), f"{key}: 強調標記巢狀或為空")
    return spans


def read_section(block, key, expected_title):
    lines = block.decode("cp437").splitlines()
    require(lines[:2] == [f"@{key}", "@width=300"], f"{key}: 段落頭或寬度錯誤")
    require(lines[2:4] == [f"^^{expected_title}", "^^_"], f"{key}: 原版標題錯誤")
    body = lines[4:]
    require(body and any(body), f"{key}: 原版正文為空")
    if body[0].startswith("__"):
        body[0] = body[0][2:]
    require(all(not line.startswith(("@", "^^", "__")) for line in body),
            f"{key}: 正文出現未處理控制標記")
    return "".join(body)


def check(game_path, catalog_path):
    game = game_path.read_bytes()
    require(digest(game) == GAME_SHA, "GAME.TXT 版本雜湊不符，停止套用")
    markers = list(re.finditer(rb"(?m)^@[A-Z][A-Z0-9_]*", game))
    offsets = {match.start(): (match.group().decode("ascii"),
                               markers[index + 1].start() if index + 1 < len(markers) else len(game))
               for index, match in enumerate(markers)}
    require(offsets.get(SECTIONS[-1][2], (None,))[0] == "@PICKACARGO",
            "最後一節後不是預期的下一頂層標記")
    with catalog_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        require(tuple(reader.fieldnames or ()) == COLUMNS, "TSV 欄位契約不符")
        rows = list(reader)
    require(len(rows) == len(SECTIONS), "TSV 段落數不是精確八節")
    require(len({row.get("message_id") for row in rows}) == len(SECTIONS), "TSV 來源鍵重複")
    receipt = []
    for index, (row, (key, start, end, title, zh_title, expected_sha)) in enumerate(zip(rows, SECTIONS)):
        require(None not in row and all(isinstance(value, str) for value in row.values()),
                f"{key}: TSV 欄位多出或缺少")
        require(offsets.get(start) == (f"@{key}", end), f"{key}: 非完整頂層節邊界")
        require(start < end and (index == 0 or start == SECTIONS[index - 1][2]),
                f"{key}: 位移不連續")
        block = game[start:end]
        require(digest(block) == expected_sha, f"{key}: 段落原始 bytes 雜湊不符")
        expected = {
            "message_id": f"GAME.TXT:@{key}", "source_file": "GAME.TXT",
            "source_file_sha256": GAME_SHA, "section_offset": f"0x{start:08X}",
            "section_byte_length": str(end - start), "section_sha256": expected_sha,
            "status": "draft",
        }
        require(all(row[field] == value for field, value in expected.items()),
                f"{key}: TSV 來源鍵、版本或草稿狀態不符")
        english = row["source_en_display"]
        chinese = row["zh_hant_draft"]
        require(english.startswith(f"{title}\\n") and chinese.startswith(f"{zh_title}\\n"),
                f"{key}: 雙語標題或換行缺失")
        require(row["notes"].strip() and chinese.split("\\n", 1)[1].strip(),
                f"{key}: 譯文或審查註記為空")
        require(all("\t" not in value and "\r" not in value and "\n" not in value
                    and not any(ord(c) < 32 for c in value)
                    for value in (english, chinese, row["notes"])),
                f"{key}: TSV 含實際控制字元")
        require(english.count("\\n") == 1 and chinese.count("\\n") == 1,
                f"{key}: 虛擬換行數量不符")
        require(not any(token in chinese for token in ("^^", "__", "@width=")),
                f"{key}: 譯文混入原版控制標記")
        original_body = read_section(block, key, title)
        require(compact(english.split("\\n", 1)[1]) == compact(original_body),
                f"{key}: 英文原文與來源 bytes 不符")
        original_spans = marked_spans(original_body, key)
        en_spans = marked_spans(english, key)
        zh_spans = marked_spans(chinese, key)
        require([compact(span) for span in original_spans] ==
                [compact(span) for span in en_spans], f"{key}: 原文強調範圍與 bytes 不符")
        require(len(en_spans) == len(zh_spans), f"{key}: 中文強調標記數量不符")
        receipt.append({"key": key, "offset": f"0x{start:08X}", "length": end - start,
                        "section_sha256": expected_sha, "emphasis_count": len(en_spans),
                        "runtime_display": "confirmed" if key.startswith("NATION1") else "unknown"})
    return {"game_sha256": GAME_SHA, "catalog_sha256": digest(catalog_path.read_bytes()),
            "section_count": len(receipt), "sections": receipt}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.game, args.catalog), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
