#!/usr/bin/env python3
"""由真 Retire 印前底圖、唯一譯稿與固定字型產生本機 Ebitengine 三欄原型。"""

import argparse
import base64
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from prototype_overlay import cmap_coverage


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
FIXTURE_SHA = "a2638a3de1d9b4ecb6499efee6e8a07722c9c0e6b4dce6d0630094310ad464f8"
FIELDS = (
    ("question", 0x122, "確定要離開遊戲嗎？", (118, 75, 184, 99),
     (122, 78, 181, 97), 441, (205, 159, 77), (512, 312), (185, 72), 1253314215),
    ("yes", 0x141, "是", (122, 99, 144, 112),
     (126, 102, 141, 110), 64, (29, 22, 13), (514, 408), (37, 32), 1253343962),
    ("no", 0x146, "否", (122, 112, 142, 125),
     (126, 114, 136, 122), 54, (27, 20, 7), (506, 456), (37, 32), 1253348262),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def mask_for(name, text, font, variant):
    if name == "question":
        first, second = text[:5], text[5:]
        require((first, second) == ("確定要離開", "遊戲嗎？"), "問句版面分行不符")
        expected = (((0, 3, 185, 35), (0, 3, 148, 35)) if variant == "center-34" else
                    ((0, 3, 205, 38), (0, 3, 164, 38)))
        require((font.getbbox(first), font.getbbox(second)) == expected,
                "問句墨跡尺寸不符")
        mask = Image.new("L", (185, 72) if variant == "center-34" else (205, 75))
        draw = ImageDraw.Draw(mask)
        draw.text((0, -3), first, fill=255, font=font)
        draw.text((18, 37) if variant == "center-34" else (0, 37),
                  second, fill=255, font=font)
        return mask
    require(font.getbbox(text) == (0, 3, 37, 35), "按鈕墨跡尺寸不符")
    mask = Image.new("L", (37, 32))
    ImageDraw.Draw(mask).text((0, -3), text, fill=255, font=font)
    return mask


def validate(args):
    if not (args.game / "GAME.TXT").is_file() or not args.fixture.is_file():
        return None
    require(sha((args.game / "GAME.TXT").read_bytes()) == GAME_SHA, "原版 GAME.TXT 版本不符")
    require(sha(args.fixture.read_bytes()) == FIXTURE_SHA, "玩家事件版本不符")
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(),
            "本機輸出目錄不存在或擁有者不符")
    require(args.font.is_file() and sha(args.font.read_bytes()) == FONT_SHA,
            "固定 Cubic 11 字型不存在或版本不符")
    require(not (args.output / "preview.json").exists(), "不覆寫既有原型")
    with args.catalog.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    game = (args.game / "GAME.TXT").read_bytes()
    for name, offset, text, *_ in FIELDS:
        key = f"GAME.TXT:0x{offset:08X}"
        matches = [r for r in rows if r["candidate_id"] == key]
        require(len(matches) == 1, "主譯稿鍵缺失或重複：" + key)
        row = matches[0]
        length = int(row["source_byte_length"])
        require(row["source_file"] == "GAME.TXT" and
                row["source_sha256"] == GAME_SHA and
                int(row["byte_offset"], 0) == offset and
                row["source_bytes_sha256"] == sha(game[offset:offset + length]) and
                row["zh_hant"] == text and row["status"] == "draft",
                "主譯稿來源或譯文不符：" + key)
    font_bytes = args.font.read_bytes()
    coverage = cmap_coverage(font_bytes)
    require(all(ord(ch) in coverage for _, _, text, *_ in FIELDS for ch in text),
            "Cubic 11 缺少問句或按鈕中文字形")

    base = args.reports
    first = (base / "prompt-b.json").read_bytes()
    require(first == (base / "prompt-c.json").read_bytes(), "雙次冷啟動報告不同")
    observed = json.loads(first)
    control = json.loads((base / "prompt-control.json").read_bytes())
    require(observed["version"] == control["version"] == "goal126-retire-preprint-v1"
            and observed["control"] is False and control["control"] is True,
            "探針報告版本或監看控制不符")
    require(observed["game_inputs_sha256"] == control["game_inputs_sha256"] == FIXTURE_SHA,
            "探針玩家輸入不符")
    for key in ("route", "transfers", "samples", "opened", "key_events", "game_inputs"):
        require(observed[key] == control[key], "無監看控制原版狀態不符：" + key)
    require(not control["print_reads"] and not control["writers"], "無監看控制仍有觀測事件")
    require(observed["samples"]["1275m"]["step"] == 1275000000,
            "退休確認框取樣相位不符")
    for offset in (0x122, 0x141, 0x146):
        hits = [t for t in observed["transfers"]
                if t["file_offset"] == offset and t["step"] == 1253245641]
        require(len(hits) == 1 and hits[0]["match"] is True and hits[0]["read_pos"] == 0,
                "當次原版 DOS 讀入來源不符：" + hex(offset))
    indexed = (base / "prompt-b.1275m.idx").read_bytes()
    canvas = (base / "prompt-b.1275m.canvas").read_bytes()
    palette = (base / "prompt-b.1275m.pal").read_bytes()
    sample = observed["samples"]["1275m"]
    for data, size, digest in ((indexed, 64000, sample["indexed_sha256"]),
                               (canvas, 64000, sample["canvas_sha256"]),
                               (palette, 768, sample["palette_sha256"])):
        require(len(data) == size and sha(data) == digest, "原版畫面實檔不符")

    button_font = ImageFont.truetype(str(args.font), 34)
    question_font = ImageFont.truetype(str(args.font),
                                       34 if args.variant == "center-34" else 38)
    layers = []
    for name, offset, text, safe, bbox, pixels, colors, position, size, step in FIELDS:
        if args.variant == "left-38":
            if name == "question":
                position, size = (485, 312), (205, 75)
            elif name == "yes":
                position = (501, 408)
            else:
                position = (501, 456)
        meta = observed["retire_preprint"][name]
        before = (base / f"prompt-b.before-{name}.canvas").read_bytes()
        other = (base / f"prompt-c.before-{name}.canvas").read_bytes()
        require(len(before) == 64000 and before == other and sha(before) == meta["canvas_sha256"]
                and meta["step"] == step, "首字前底圖或步數不符：" + name)
        x0, y0, x1, y1 = safe
        changed = [i for y in range(y0, y1) for x in range(x0, x1)
                   if (i := y * 320 + x) >= 0 and before[i] != canvas[i]]
        measured = (min(i % 320 for i in changed), min(i // 320 for i in changed),
                    max(i % 320 for i in changed) + 1, max(i // 320 for i in changed) + 1)
        counts = Counter(canvas[i] for i in changed)
        require(len(changed) == pixels and measured == bbox and
                tuple(counts[color] for color in (68, 47, 128)) == colors and
                set(counts) == {68, 47, 128}, "原版逐欄墨跡不符：" + name)
        mask = mask_for(name, text,
                        question_font if name == "question" else button_font,
                        args.variant)
        expected_alpha = {"question": ((3, 0, 182, 72) if args.variant == "center-34"
                                       else (2, 0, 202, 75)),
                          "yes": (3, 0, 35, 32), "no": (3, 0, 34, 32)}[name]
        require(mask.size == size and mask.getbbox() == expected_alpha,
                "中文字模尺寸不符：" + name)
        px, py = position
        require(px >= x0 * 4 + 4 and py >= y0 * 4 + 4 and
                px + size[0] + 4 <= x1 * 4 - 4 and py + size[1] <= y1 * 4 - 4,
                "中文及陰影超出安全區：" + name)
        background = bytes(before[y * 320 + x] for y in range(y0, y1)
                           for x in range(x0, x1))
        layers.append({"name": name, "safe": safe, "ink_width": size[0],
                       "ink_height": size[1], "position": position,
                       "background": base64.b64encode(background).decode("ascii"),
                       "mask": base64.b64encode(mask.tobytes()).decode("ascii"),
                       "color_index": 68, "shadow_index": 47, "shadow_dx": 4,
                       "candidate_id": f"GAME.TXT:0x{offset:08X}",
                       "translation_sha256": sha(text.encode("utf-8"))})
    return {"prototype": True, "indexed": base64.b64encode(indexed).decode("ascii"),
            "palette": base64.b64encode(palette).decode("ascii"), "layers": layers,
            "font_sha256": FONT_SHA, "variant": args.variant,
            "question_font_size": 34 if args.variant == "center-34" else 38,
            "button_font_size": 34,
            "source_receipt_sha256": sha(first),
            "rights": "local-only; original pixels and font masks must not be committed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("center-34", "left-38"),
                        default="center-34")
    args = parser.parse_args()
    result = validate(args)
    if result is None:
        print("SKIP：合法 DOS 原版或固定玩家事件缺失")
        return 77
    args.output.joinpath("preview.json").write_text(
        json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PASS：三欄原版來源、印前底圖、中文字模與 Ebitengine 原型資料")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
