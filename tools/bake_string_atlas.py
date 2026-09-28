#!/usr/bin/env python3
"""目標169（規格038）：烘製通用字串層的執行期字元圖集（30～12px）；只輸出本機研究產物。

字集涵蓋字串模板、海上詞典、語料清冊、譯稿、定稿譯名、殖民地名稱的中文與可列印 ASCII；
綁定字型與上述來源雜湊，任一不符前端整層回原文。
"""

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

SIZE = 30  # 原版大寫字高 7 時的起始字級（⌊7×4.4⌋）
FLOOR = 12  # 字高 4 時起始 17px 的 2/3 取整；更小的字高本輪不處理
csv.field_size_limit(1 << 24)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--templates", type=Path, default=Path("/repo/text/string-templates.zh-Hant.tsv"))
    p.add_argument("--sea", type=Path, default=Path("/repo/text/sea-status.zh-Hant.tsv"))
    p.add_argument("--corpus", type=Path, default=Path("/repo/text/corpus.zh-Hant.tsv"))
    p.add_argument("--draft", type=Path, default=Path("/repo/text/draft.zh-Hant.tsv"))
    p.add_argument("--terms", type=Path, default=Path("/repo/text/terms.zh-Hant.tsv"))
    p.add_argument("--colony", type=Path, default=Path("/repo/text/colony-bilingual.tsv"))
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "LABELS.TXT").is_file():
        print("SKIP：缺少合法原版，未產生圖集")
        return 77
    require(a.output.is_dir() and a.output.stat().st_uid == os.getuid(), "本機輸出目錄不存在或擁有者不符")
    require(sha(a.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    src = {k: getattr(a, k).read_bytes() for k in ("templates", "sea", "corpus", "draft", "terms", "colony")}
    text = "".join(r["zh_hant"] for k in ("templates", "sea", "corpus", "draft", "colony") for r in rows(src[k]))
    text += "".join(r["zh"] for r in rows(src["terms"]))
    chars = sorted({c for c in text if c not in "{}\\\t\n" and ord(c) >= 0x20} |
                   {chr(c) for c in range(0x20, 0x7f)} - set("{}\\"))
    sizes = {}
    for size in range(SIZE, FLOOR - 1, -1):
        font = ImageFont.truetype(str(a.font), size)
        ascent, descent = font.getmetrics()
        height = ascent + descent
        probe = font.getbbox("國", anchor="ls")
        glyphs = {}
        for ch in chars:
            width = round(font.getlength(ch))
            if width <= 0:
                continue  # 字型沒有字形者不入圖集；前端遇到即該串回原文
            cell = Image.new("L", (width, height))
            ImageDraw.Draw(cell).text((0, ascent), ch, font=font, fill=255, anchor="ls")
            glyphs[ch] = {"w": width, "alpha": base64.b64encode(cell.tobytes()).decode()}
        sizes[str(size)] = {"height": height, "ascent": ascent, "cjk_ink_top": ascent + probe[1],
                            "cjk_ink_bottom": ascent + probe[3], "glyphs": glyphs}
    payload = {"font_sha256": FONT_SHA, "font_px": SIZE, "floor_px": FLOOR,
               "bindings": {k: sha(v) for k, v in src.items()},
               "charset_sha256": sha("".join(chars).encode()), "sizes": sizes,
               "scope": "由 Cubic 11 烘製的字模；授權見 font/Cubic-11-OFL.txt"}
    (a.output / "string-atlas.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    for s in ("30", "22", "15"):
        z = sizes[s]
        print(f"{s}px：高 {z['height']}、中文墨跡 {z['cjk_ink_top']}–{z['cjk_ink_bottom']}")
    print(f"字元 {len(chars)}、字級 {SIZE}～{FLOOR}px")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
