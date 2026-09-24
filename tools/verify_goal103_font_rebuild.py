#!/usr/bin/env python3
"""獨立核對固定 Cubic 11 重烘十七欄與既有正式驗收字模。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from validate_nation_card_fragments import validate as validate_card
from validate_translation_draft import read_catalog, validate_sources


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
GAME_SHA = {"GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
            "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
            "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"}
CATALOG_SHA = "9c9efe393ca59356f2453ebe0f2b4ad8c5b34bd948af2c59117131163b5de008"
CARD_CATALOG_SHA = "d4cf454a4851778546b90a778f2966f9cfa6cc9e2a2b01fae9e261844d0f64b6"
OLD_PREVIEW_SHA = "c3fbdabfab91e03ed5b3c4231dc35f8172ee947e85633cfd8e04f43aa76d55eb"
STANDARD = (
    "GAME.TXT:0x000001B0", "GAME.TXT:0x000001CB", "GAME.TXT:0x000001E4",
    "GAME.TXT:0x000001F9", "GAME.TXT:0x00000204", "LABELS.TXT:0x00000888",
    "LABELS.TXT:0x00000890", "LABELS.TXT:0x0000086E", "GAME.TXT:0x00000A7A",
    "NAMES.TXT:0x00000C0C", "LABELS.TXT:0x000008A9", "NAMES.TXT:0x00000C18",
    "LABELS.TXT:0x000008B2", "LABELS.TXT:0x000008D3", "LABELS.TXT:0x000008DB",
)
CARD = {"NAMES.TXT:0x000008EA": (21, 92, 19,
                                    "29ef858ea29168dba4d493f82429e8df3e7c4ba9be65eec511f7894987249d42"),
        "LABELS.TXT:0x000008F2": (25, 54, 23,
                                     "9bd96a25dcd72d9d10709279c3509e9ee93ead8fe0c900564a2c8c02aa5bf471")}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def filename(key):
    return key.replace(":", "-") + ".json"


def json_files(directory):
    require(directory.is_dir(), "字模目錄不存在：" + str(directory))
    return {item.name for item in directory.glob("*.json")}


def read_mask(path, key):
    raw = path.read_bytes()
    payload = json.loads(raw)
    require(payload.get("candidate_id") == key and payload.get("font_sha256") == FONT_SHA,
            "字模鍵或字型指紋不符：" + key)
    width, height = payload.get("width"), payload.get("height")
    require(isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0,
            "字模尺寸不合法：" + key)
    alpha = base64.b64decode(payload["alpha"], validate=True)
    require(len(alpha) == width * height, "Alpha 長度與尺寸不符：" + key)
    return raw, payload, alpha


def verify(args):
    missing = [name for name in GAME_SHA if not (args.game / name).is_file()]
    if missing:
        raise FileNotFoundError("缺少合法原版：" + "、".join(missing))
    require({name: sha((args.game / name).read_bytes()) for name in GAME_SHA} == GAME_SHA,
            "原版 TXT 指紋不符")
    require(sha(args.font.read_bytes()) == FONT_SHA, "原始 Cubic 11 指紋不符")
    require(sha(args.catalog.read_bytes()) == CATALOG_SHA and
            sha(args.card_catalog.read_bytes()) == CARD_CATALOG_SHA,
            "主譯稿或旗卡片段 TSV 指紋不符")
    rows = read_catalog(args.catalog)
    validate_sources(rows, args.game)
    card_rows = {row["candidate_id"]: row for row in
                 validate_card(args.card_catalog, args.game, args.font)}
    all_keys = STANDARD + tuple(CARD)
    require(len(set(all_keys)) == 17, "十七欄鍵重複")
    require(json_files(args.new) == {filename(key) for key in all_keys},
            "新烘字模不是完整且唯一的十七欄")
    require(json_files(args.old_standard) == {filename(key) for key in STANDARD},
            "歷史十五欄基準不完整")
    require({filename(key) for key in CARD} <= json_files(args.old_card),
            "歷史旗卡兩欄基準不完整")
    main_rows = {row["candidate_id"]: row for row in rows}
    results = []
    for key in STANDARD:
        current, payload, alpha = read_mask(args.new / filename(key), key)
        old, _, _ = read_mask(args.old_standard / filename(key), key)
        require(current == old and
                payload["translation_sha256"] == sha(
                    (main_rows[key]["zh_hant"][2:] if key == "GAME.TXT:0x00000A7A"
                     else main_rows[key]["zh_hant"]).encode("utf-8")),
                "十五欄重烘與已驗基準不同：" + key)
        results.append({"candidate_id": key, "font_px": payload["font_size"],
                        "ink": [payload["width"], payload["height"]],
                        "alpha_sha256": sha(alpha), "receipt_sha256": sha(current),
                        "parity": "whole-json-equal"})
    for key, (size, width, height, expected_alpha) in CARD.items():
        current, payload, alpha = read_mask(args.new / filename(key), key)
        old, previous, old_alpha = read_mask(args.old_card / filename(key), key)
        translated = card_rows[key]["zh_hant"] + ("：" if key.startswith("NAMES.") else "")
        require(payload.get("local_only") is True and previous.get("local_only") is True and
                previous.get("source_preview_sha256") == OLD_PREVIEW_SHA and
                (payload["font_size"], payload["width"], payload["height"]) ==
                (size, width, height) and
                payload["translation_sha256"] == previous["translation_sha256"] ==
                sha(translated.encode("utf-8")) and
                alpha == old_alpha and sha(alpha) == expected_alpha,
                "旗卡原始 TTF 重烘與已驗 A 版字模不同：" + key)
        results.append({"candidate_id": key, "font_px": size, "ink": [width, height],
                        "alpha_sha256": sha(alpha), "receipt_sha256": sha(current),
                        "historical_receipt_sha256": sha(old),
                        "parity": "alpha-exact-equal"})
    return {"result": "PASS", "scope": "固定原始字型重烘十七欄；僅本機資產，不是新畫面驗收",
            "input_sha256": {"font": FONT_SHA, "main_catalog": CATALOG_SHA,
                             "card_catalog": CARD_CATALOG_SHA, **GAME_SHA},
            "field_count": len(results), "fields": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--card-catalog", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--old-standard", type=Path, required=True)
    parser.add_argument("--old-card", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require(args.receipt.parent.is_dir() and args.receipt.parent.stat().st_uid == os.getuid(),
            "驗證收據輸出目錄不存在或擁有者不符")
    try:
        result = verify(args)
    except FileNotFoundError as exc:
        print("SKIP：" + str(exc))
        return 77
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print("PASS：固定字型重烘十七欄；十五欄整檔、旗卡兩欄 Alpha 精確相同")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
