#!/usr/bin/env python3
"""獨立核對 @BUILD1 真正印前底圖、同狀態控制及本機中文樣本。"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA


CAPTION = b"In the Year of Our Lord One Thousand Four Hundred Ninety-Two,"
BEFORE_SHA = "d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab"
FINAL_SHA = "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
SAFE = (12, 27, 307, 42)
SOURCE_KEY = "GAME.TXT:0x000153CC"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def file_bytes(path, size, expected=None):
    raw = path.read_bytes()
    need(len(raw) == size and (expected is None or sha(raw) == expected),
         f"原始檔大小或 SHA 不符：{path.name}")
    return raw


def check(game, inputs, reports, preview, catalog, font):
    if (not inputs.is_file() or not font.is_file() or
            not all((game / name).is_file() for name in FILE_SHA)):
        return {"result": "SKIP", "reason": "合法原版、固定字型或玩家輸入缺失"}
    for name, expected in FILE_SHA.items():
        need(sha((game / name).read_bytes()) == expected,
             "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "玩家輸入版本不符")
    need(sha(font.read_bytes()) == FONT_SHA, "固定 Cubic 11 字型不符")
    source = (game / "GAME.TXT").read_bytes()
    need(source[0x153CC:0x153CC + 2 + len(CAPTION)] == b"^^" + CAPTION,
         "GAME.TXT:@BUILD1 原始行不符")
    a = read_json(reports / "england-enter-a.json")
    b = read_json(reports / "england-enter-b.json")
    control = read_json(reports / "england-enter-control.json")
    need(a == b and a["version"] == "goal106-build-preprint-v1" and
         control["version"] == "goal105-tutorial-route-v4" and
         a["control"] is b["control"] is False and
         control["control"] is True and
         all(item["nation"] == "england" and item["after_b"] == "enter" and
             item["after_follow"] == "enter" and item["next_enter"] is True and
             item["input_sha256"] == INPUT_SHA and item["input_hashes"] == FILE_SHA
             for item in (a, b, control)),
         "兩次原版重播／無監看控制或版本不符")
    need(all(a[key] == control[key]
             for key in ("route", "sources", "transfers", "samples", "opened")) and
         not control["print_reads"] and not control["writers"],
         "探針改變原版 CPU、RAM、時間、開檔或畫布")
    for label in ("85m", "90m", "95m", "100m"):
        for kind, field, size in (("idx", "indexed_sha256", 64000),
                                  ("canvas", "canvas_sha256", 64000),
                                  ("pal", "palette_sha256", 768)):
            raw = file_bytes(reports / f"england-enter-a.{label}.{kind}", size,
                             a["samples"][label][field])
            need(raw == file_bytes(reports / f"england-enter-b.{label}.{kind}", size) ==
                 file_bytes(reports / f"england-enter-control.{label}.{kind}", size),
                 f"{label}: 雙重播／控制原始 {kind} 不同")
    writer = a["writers"].get("after-follow/0D21:012C", {})
    pre = a["preprint"].get("after-follow", {})
    need(writer.get("count") == 1040 and writer.get("bbox") == [16, 30, 303, 39] and
         writer.get("first_step") == pre.get("step") == 88_689_058 and
         pre.get("writer_ip") == "0D21:012C" and
         pre.get("canvas_sha256") == BEFORE_SHA,
         "當次字幕首字印前事件或畫布範圍不符")
    for suffix in ("a", "b"):
        need(file_bytes(reports / f"england-enter-{suffix}.after-follow.pre.canvas",
                        64000, BEFORE_SHA) ==
             file_bytes(reports / f"england-enter-a.after-follow.pre.canvas", 64000),
             "兩次原版字幕印前底圖不同")
    before = file_bytes(reports / "england-enter-a.after-follow.pre.canvas",
                        64000, BEFORE_SHA)
    after = file_bytes(reports / "england-enter-a.90m.canvas", 64000)
    need(a["samples"]["90m"]["indexed_sha256"] == FINAL_SHA,
         "字幕畫面索引基準不符")
    changed = [i for i, (old, new) in enumerate(zip(before, after)) if old != new]
    need(len(changed) == 1040 and
         (min(i % 320 for i in changed), min(i // 320 for i in changed),
          max(i % 320 for i in changed) + 1,
          max(i // 320 for i in changed) + 1) == (16, 30, 303, 39) and
         {after[i] for i in changed} == {14, 47, 54} and
         all(SAFE[0] <= i % 320 < SAFE[2] and
             SAFE[1] <= i // 320 < SAFE[3] for i in changed),
         "原版字幕實際畫布差分、色號或安全界不符")
    printed = bytes(event["value"] for event in a["print_reads"]
                    if event["step"] >= 85_000_000 and
                    event["cs_ip"] == "0D21:00C6")
    need(printed == b"".join(bytes((char, 0)) for char in CAPTION),
         "當次 0D21:00C6 逐字印字不符")
    receipt = read_json(preview / "preview.json")
    with catalog.open(encoding="utf-8", newline="") as stream:
        rows = [row for row in csv.DictReader(stream, delimiter="\t")
                if row["candidate_id"] == SOURCE_KEY]
    need(len(rows) == 1 and rows[0]["status"] == "draft" and
         rows[0]["source_sha256"] == FILE_SHA["GAME.TXT"] and
         rows[0]["source_bytes_sha256"] == sha(b"^^" + CAPTION) and
         rows[0]["zh_hant"].startswith("^^") and
         receipt["catalog_sha256"] == sha(catalog.read_bytes()) and
         receipt["translation_sha256"] == sha(rows[0]["zh_hant"].encode()),
         "目前 TSV 字幕譯文與樣本不符")
    need(receipt["source_key"] == SOURCE_KEY and
         receipt["game_sha256"] == FILE_SHA["GAME.TXT"] and
         receipt["font_sha256"] == FONT_SHA and
         receipt["preprint_sha256"] == BEFORE_SHA and
         receipt["final_canvas_sha256"] == sha(after) and
         receipt["palette_sha256"] == a["samples"]["90m"]["palette_sha256"] and
         receipt["font_size"] == 38 and
         receipt["candidate_ink_size"][1] == 35 and
         receipt["safe_logical"] == list(SAFE) and
         receipt["original_ink_bbox"] == [16, 30, 303, 39],
         "中文字級樣本或來源收據不符")
    safe = tuple(n * 4 for n in SAFE)
    for box in (receipt["foreground_bbox"], receipt["shadow_bbox"]):
        need(safe[0] <= box[0] < box[2] <= safe[2] and
             safe[1] <= box[1] < box[3] <= safe[3],
             "中文墨跡或陰影超出安全矩形")
    images = {}
    for name in ("original", "candidate"):
        path = preview / f"{name}.png"
        need(sha(path.read_bytes()) == receipt[f"{name}_png_sha256"],
             "本機樣本 PNG SHA 不符：" + name)
        with Image.open(path) as image:
            need(image.size == (1280, 800) and image.mode == "RGB",
                 "本機樣本畫布尺寸或色彩模式不符")
            images[name] = image.copy()
    diff = ImageChops.difference(images["original"], images["candidate"])
    box = diff.getbbox()
    need(box is not None and safe[0] <= box[0] < box[2] <= safe[2] and
         safe[1] <= box[1] < box[3] <= safe[3],
         "樣本不變或安全矩形外有畫素差異")
    return {"result": "PASS", "scope": "英格蘭 @BUILD1 印前底圖與38px本機可丟棄樣本",
            "input_sha256": INPUT_SHA, "preprint_sha256": BEFORE_SHA,
            "preview_sha256": sha((preview / "preview.json").read_bytes()),
            "status": "DRAFT; not a formal Ebitengine overlay",
            "limitations": "只驗一條原版字幕的可逆樣本；其餘字幕、help、玩家後續及正式輸出尚未驗"}


def main(args):
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    result = check(args.game, args.inputs, args.reports, args.preview,
                   args.catalog, args.font)
    if result["result"] == "SKIP":
        print("SKIP：" + result["reason"])
        return 77
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                      indent=2) + "\n", encoding="utf-8")
    print("PASS：" + result["scope"])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
