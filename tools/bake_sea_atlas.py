#!/usr/bin/env python3
"""目標143：依使用者選定的 22px（Cubic 11 兩倍）烘製海上選單列與狀態欄的字元圖集；只輸出本機研究產物。"""

import argparse
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from preview_goal102_nation_intro import FONT_SHA

SIZE = 22
FLOOR = 15  # 使用者 2026-09-26 決定：超界縮字下限為欄位字級 2/3（22px → 15px）
FIELDS = ["candidate_id", "source_file", "source_sha256", "byte_offset", "source_byte_length",
          "source_bytes_sha256", "source_text", "zh_hant", "role", "status", "notes"]
# 模板固定字（見規格032）：季節列「年」、全形括號、全形空白。
TEMPLATE_CHARS = "年（）　"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/sea-status.zh-Hant.tsv"))
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "NAMES.TXT").is_file():
        print("SKIP：缺少合法原版，未產生圖集")
        return 77
    require(a.output.is_dir() and a.output.stat().st_uid == os.getuid(), "本機輸出目錄不存在或擁有者不符")
    require(sha(a.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    catalog = a.catalog.read_bytes()
    rows = list(csv.DictReader(io.StringIO(catalog.decode("utf-8")), delimiter="\t", strict=True))
    require(rows and list(rows[0]) == FIELDS, "海上詞典 TSV 欄位不符")
    require(len({r["candidate_id"] for r in rows}) == len(rows), "海上詞典來源鍵重複")
    for r in rows:
        data = (a.game / r["source_file"]).read_bytes()
        offset, length = int(r["byte_offset"], 0), int(r["source_byte_length"])
        require(sha(data) == r["source_sha256"] and data[offset:offset + length] == r["source_text"].encode() and
                sha(r["source_text"].encode()) == r["source_bytes_sha256"] and r["zh_hant"] and r["status"] == "draft",
                "海上詞典來源不符：" + r["candidate_id"])
    chars = sorted(set("".join(r["zh_hant"] for r in rows) + TEMPLATE_CHARS +
                       "".join(chr(c) for c in range(0x20, 0x7f))))
    sizes = {}
    for size in range(SIZE, FLOOR - 1, -1):
        font = ImageFont.truetype(str(a.font), size)
        ascent, descent = font.getmetrics()
        height = ascent + descent
        probe = font.getbbox("國", anchor="ls")
        glyphs = {}
        for ch in chars:
            width = round(font.getlength(ch))
            require(width > 0, "字元寬度為零：" + repr(ch))
            cell = Image.new("L", (width, height))
            ImageDraw.Draw(cell).text((0, ascent), ch, font=font, fill=255, anchor="ls")
            glyphs[ch] = {"w": width, "alpha": base64.b64encode(cell.tobytes()).decode()}
        sizes[str(size)] = {"height": height, "ascent": ascent, "cjk_ink_top": ascent + probe[1],
                            "cjk_ink_bottom": ascent + probe[3], "glyphs": glyphs}
    top = sizes[str(SIZE)]
    payload = {"font_sha256": FONT_SHA, "font_px": SIZE, "floor_px": FLOOR, "height": top["height"],
               "ascent": top["ascent"], "cjk_ink_top": top["cjk_ink_top"], "cjk_ink_bottom": top["cjk_ink_bottom"],
               "catalog_sha256": sha(catalog), "charset_sha256": sha("".join(chars).encode()),
               "glyphs": top["glyphs"], "sizes": sizes, "scope": "local-only；衍生字模不加入 Git 或散布包"}
    (a.output / "sea-atlas.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"字元 {len(chars)}、字級 {SIZE}～{FLOOR}px、22px 高 {top['height']}、中文墨跡 {top['cjk_ink_top']}–{top['cjk_ink_bottom']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
