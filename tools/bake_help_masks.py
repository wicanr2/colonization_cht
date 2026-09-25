#!/usr/bin/env python3
"""目標142：依使用者選定的 A 版（30px）烘製首則 help 的陰影／一般／強調三層字模；只輸出本機研究產物。"""

import argparse
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

from preview_goal102_nation_intro import FONT_SHA
from preview_goal142_help import CARAVEL, TEXT, layout

KEY = "GAME.TXT:@TUTORIAL1"
FIELDS = ["message_id", "source_file", "source_file_sha256", "section_offset", "text_offset", "text_byte_length",
          "source_bytes_sha256", "source_en", "zh_hant", "status", "notes"]
GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bake(args):
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(), "本機輸出目錄不存在或擁有者不符")
    require(sha(args.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    catalog = args.catalog.read_bytes()
    rows = list(csv.DictReader(io.StringIO(catalog.decode("utf-8")), delimiter="\t", strict=True))
    require(rows and list(rows[0]) == FIELDS, "help TSV 欄位不符")
    match = [r for r in rows if r["message_id"] == KEY]
    require(len(match) == 1, "help TSV 缺鍵或重複")
    row = match[0]
    game = (args.game / "GAME.TXT").read_bytes()
    offset, length = int(row["text_offset"], 0), int(row["text_byte_length"])
    require(sha(game) == GAME_SHA == row["source_file_sha256"] and
            sha(game[offset:offset + length]) == row["source_bytes_sha256"] and row["status"] == "draft",
            "help 來源片段不符")
    translation = row["zh_hant"].replace("%STRING0", CARAVEL)
    require("%" not in translation, "help 譯文有未展開變數")
    lay = layout(translation, args.font, 0)
    require(lay["size"] == 30 and lay["fits"], "A 版字級或版面不符使用者決定")
    width, height = TEXT[2] - TEXT[0], TEXT[3] - TEXT[1]
    layers = {name: Image.new("L", (width, height)) for name in ("shadow", "normal", "highlight")}
    draws = {name: ImageDraw.Draw(image) for name, image in layers.items()}
    ref = draws["normal"].textbbox((0, 0), "國", font=lay["font"], anchor="ls")
    top = (height - lay["total"]) // 2
    font = lay["font"]
    for i, line in enumerate(lay["lines"]):
        x, baseline = 4, top + i * lay["advance"] - ref[1]
        value = "".join(c for c, _ in line)
        draws["shadow"].text((x + 4, baseline + 4), value, font=font, anchor="ls", fill=255)
        draws["normal"].text((x, baseline), value, font=font, anchor="ls", fill=255)
        start = 0
        while start < len(line):
            if not line[start][1]:
                start += 1
                continue
            end = start + 1
            while end < len(line) and line[end][1]:
                end += 1
            prefix = "".join(c for c, _ in line[:start])
            draws["highlight"].text((x + round(font.getlength(prefix)), baseline),
                                    "".join(c for c, _ in line[start:end]), font=font, anchor="ls", fill=255)
            start = end
    for name, image in layers.items():
        require(image.getbbox() is not None, "字模層沒有墨跡：" + name)
    payload = {"message_id": KEY, "catalog_sha256": sha(catalog), "translation_sha256": sha(translation.encode()),
               "font_sha256": FONT_SHA, "body_font_px": lay["size"], "width": width, "height": height,
               "lines": ["".join(c for c, _ in line) for line in lay["lines"]],
               **{name: base64.b64encode(image.tobytes()).decode() for name, image in layers.items()},
               "scope": "local-only；衍生字模不加入 Git 或散布包"}
    path = args.output / "GAME.TXT-@TUTORIAL1.json"
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{KEY}：{width}×{height}，{lay['size']}px，{len(lay['lines'])} 行")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/help-bilingual.tsv"))
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺少合法原版，未產生字模")
        return 77
    bake(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
