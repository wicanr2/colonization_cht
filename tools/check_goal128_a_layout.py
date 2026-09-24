#!/usr/bin/env python3
"""鎖定兩處已選 A 字級；核對 @BUILD1 固定原版取樣的保守離頁條件。"""

import argparse
import base64
import csv
import hashlib
import json
import os
from pathlib import Path


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
CAPTION_KEY = "GAME.TXT:0x000153CC"
CAPTION_BYTES = b"In the Year of Our Lord One Thousand Four Hundred Ninety-Two,"
CAPTION_SCREEN = "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"
CAPTION_PALETTE = "92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b"
NEXT_SCREEN = "69859c61c490112c333982957339c23f09df22f2e2918ca881c44d8911dc54c3"
OPTION_SCREEN = "7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546"
OPTION_PALETTE = "b81c99f3ef54dd7015107ece98b6770620b4c3472281172a92f0302f8ec6b4c9"
OPTION_SIZES_A = (34, 25, 28, 28, 25, 28, 28, 27, 28)
OPTION_OFFSETS = (0x4CD, 0x4E9, 0x4FD, 0x512, 0x525, 0x533, 0x53E, 0x550, 0x566)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def record(path):
    return json.loads(path.read_bytes())


def within(box, safe):
    return safe[0] <= box[0] < box[2] <= safe[2] and safe[1] <= box[1] < box[3] <= safe[3]


def eligible_caption(source_seen, version_ok, mode, indexed_sha, palette_sha):
    """僅供固定取樣的 DRAFT 守門候選；不聲稱已接真視窗每幀。"""
    return (source_seen and version_ok and mode == 0x13 and
            indexed_sha == CAPTION_SCREEN and palette_sha == CAPTION_PALETTE)


def check_caption_layout(preview, row):
    require(preview["source_key"] == CAPTION_KEY and preview["game_sha256"] == GAME_SHA
            and preview["font_sha256"] == FONT_SHA and preview["font_size"] == 38
            and preview["candidate_ink_size"] == [430, 35]
            and preview["original_ink_height_scaled"] == 36
            and preview["foreground_bbox"] == [423, 120, 853, 155]
            and preview["shadow_bbox"] == [427, 124, 857, 159]
            and preview["safe_scaled"] == [48, 108, 1228, 168]
            and preview["foreground_index"] == 14 and preview["shadow_index"] == 47,
            "@BUILD1 不是使用者選定的38px A 版")
    require(all(within(preview[name], preview["safe_scaled"])
                for name in ("foreground_bbox", "shadow_bbox")),
            "@BUILD1 中文或陰影超出安全區")
    require(row["source_sha256"] == GAME_SHA and row["status"] == "draft"
            and row["zh_hant"].startswith("^^") and
            digest(row["zh_hant"].encode()) == preview["translation_sha256"],
            "@BUILD1 A 原型與目前譯文不符")


def check_options_layout(preview, verified, rows):
    require(preview["prototype"] is True and preview["variant"] == "faithful"
            and preview["font_sha256"] == FONT_SHA and
            verified["prototype"] is True and verified["result"] == "PASS" and
            verified["source_receipt_sha256"] == preview["source_receipt_sha256"],
            "遊戲選項 A 原型或逐像素驗證收據不符")
    require(digest(base64.b64decode(preview["indexed"])) == OPTION_SCREEN and
            digest(base64.b64decode(preview["palette"])) == OPTION_PALETTE,
            "遊戲選項原版畫面／色盤不是固定基準")
    layers = preview["layers"]
    require(len(layers) == 9 and len(verified["changed_pixels_by_field"]) == 9,
            "遊戲選項不是九個獨立欄位")
    for index, layer in enumerate(layers):
        name = f"option-{index:02d}"
        key = f"GAME.TXT:0x{OPTION_OFFSETS[index]:08X}"
        x, y = layer["position"]
        safe = [value * 4 for value in layer["safe"]]
        ink = [x, y, x + layer["ink_width"], y + layer["ink_height"]]
        shadow = [x + 4, y + 4, ink[2] + 4, ink[3] + 4]
        require(layer["name"] == name and layer["candidate_id"] == key and
                layer["font_size"] == OPTION_SIZES_A[index] and
                layer["color_index"] == 68 and layer["shadow_index"] == 47 and
                layer["shadow_dx"] == 4 and within(ink, safe) and within(shadow, safe) and
                verified["changed_pixels_by_field"].get(name, 0) > 0,
                f"{name} 字級、墨跡、陰影或安全區不符 A 版")
        require(key in rows and rows[key]["source_sha256"] == GAME_SHA and
                rows[key]["status"] == "draft" and
                (index == 0 or "~" in rows[key]["zh_hant"]) and
                digest(rows[key]["zh_hant"].replace("~", "").encode()) ==
                layer["translation_sha256"],
                f"{name} 譯文或快捷鍵標記與 A 原型不符")


def check(args):
    necessary = [args.game / "GAME.TXT", args.font, args.inputs, args.catalog,
                 args.caption_preview / "preview.json",
                 args.caption / "england-enter-a.json",
                 args.options_preview / "options-faithful.json",
                 args.options_preview / "options-faithful.verify.json",
                 args.options / "preprint-a.json",
                 args.options / "options-faithful.png",
                 args.reports / "england-no-extra-1350m-explore.json",
                 args.reports / "england-no-extra-1350m-b.json",
                 args.reports / "england-no-extra-1350m-control.json"]
    if not all(path.is_file() for path in necessary):
        return {"result": "SKIP", "reason": "合法原版、固定字型、玩家輸入或本機收據缺失"}
    require(digest((args.game / "GAME.TXT").read_bytes()) == GAME_SHA and
            digest(args.font.read_bytes()) == FONT_SHA and
            digest(args.inputs.read_bytes()) == INPUT_SHA,
            "原版、字型或玩家輸入版本不符")
    require((args.game / "GAME.TXT").read_bytes()[0x153CC:0x153CE + len(CAPTION_BYTES)] ==
            b"^^" + CAPTION_BYTES, "@BUILD1 原始位移與 bytes 不符")
    with args.catalog.open(encoding="utf-8", newline="") as stream:
        catalog_rows = list(csv.DictReader(stream, delimiter="\t"))
    required_keys = (CAPTION_KEY,) + tuple(
        f"GAME.TXT:0x{offset:08X}" for offset in OPTION_OFFSETS)
    require(all(sum(row["candidate_id"] == key for row in catalog_rows) == 1
                for key in required_keys), "字幕或遊戲選項譯文鍵缺失／重複")
    rows = {row["candidate_id"]: row for row in catalog_rows}
    caption = record(args.caption_preview / "preview.json")
    require(caption["catalog_sha256"] == digest(args.catalog.read_bytes()),
            "@BUILD1 A 預覽仍綁舊版整份 TSV；須重烘現行譯稿")
    check_caption_layout(caption, rows[CAPTION_KEY])
    require(digest((args.caption_preview / "candidate.png").read_bytes()) ==
            caption["candidate_png_sha256"], "@BUILD1 A 對照圖不符")
    option = record(args.options_preview / "options-faithful.json")
    option_verify = record(args.options_preview / "options-faithful.verify.json")
    require(option["catalog_sha256"] == digest(args.catalog.read_bytes()),
            "遊戲選項 A 預覽仍綁舊版整份 TSV；須重烘現行譯稿")
    require(digest((args.options / "preprint-a.json").read_bytes()) ==
            option["source_receipt_sha256"] and
            digest((args.options / "options-faithful.png").read_bytes()) ==
            option_verify["chinese_png_sha256"], "遊戲選項 A 原始收據或對照圖不符")
    check_options_layout(option, option_verify, rows)
    first = record(args.caption / "england-enter-a.json")
    printed = bytes(event["value"] for event in first["print_reads"]
                    if event["step"] >= 85_000_000 and event["cs_ip"] == "0D21:00C6")
    source_seen = printed == b"".join(bytes((value, 0)) for value in CAPTION_BYTES)
    require(source_seen and first["preprint"]["after-follow"]["canvas_sha256"] ==
            caption["preprint_sha256"] and
            first["writers"]["after-follow/0D21:012C"]["count"] == 1040,
            "@BUILD1 當次印字、印前底圖或原版畫布事件不符")
    names = ("england-no-extra-1350m-explore", "england-no-extra-1350m-b",
             "england-no-extra-1350m-control")
    reruns = [record(args.reports / f"{name}.json") for name in names]
    require([item["control"] for item in reruns] == [False, False, True] and
            all(item["version"] == "goal107-post-caption-audit-v1" and
                item["input_sha256"] == INPUT_SHA for item in reruns) and
            reruns[0] == reruns[1], "字幕後雙重播／無監看控制資格不符")
    for label in ("85m", "90m", "175m", "195m", "200m"):
        samples = [item["samples"][label] for item in reruns]
        require(samples[0] == samples[1] == samples[2],
                f"{label} 原版 CPU／RAM／畫面／色盤／時間不同")
        frame = samples[0]
        eligible = eligible_caption(source_seen, True, 0x13,
                                    frame["indexed_sha256"], frame["palette_sha256"])
        require(eligible == (label not in ("85m", "200m")),
                f"{label} 字幕頁相位守門分類錯誤")
        if label != "85m":
            require(frame["indexed_sha256"] ==
                    (NEXT_SCREEN if label == "200m" else CAPTION_SCREEN),
                    f"{label} 原版畫面與已知相位不符")
    return {"result": "PASS", "scope": "兩處 A 版面鎖定與 @BUILD1 固定取樣離頁守門候選",
            "caption_font_size": 38, "option_font_sizes": OPTION_SIZES_A,
            "caption_first_known_visible_step": 90_000_000,
            "caption_last_known_stable_step": 195_000_000,
            "caption_first_known_changed_step": 200_000_000,
            "status": "DRAFT；尚無真視窗逐幀守門或正式中文覆蓋"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "font", "inputs", "catalog", "caption", "caption-preview",
                 "options", "options-preview", "reports", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    result = check(args)
    if result["result"] == "SKIP":
        print("SKIP：" + result["reason"])
        return 77
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid ==
            os.getuid(), "輸出目錄不存在或 UID 不符")
    require(not args.output.exists(), "拒絕覆寫既有收據")
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("PASS：" + result["scope"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
