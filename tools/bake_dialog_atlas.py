#!/usr/bin/env python3
"""目標165（規格035）：烘製通用對話框的執行期字元圖集（A 版 30px，縮字下限 20px）；只輸出本機研究產物。

字集涵蓋語料清冊全部 GAME.TXT 譯文、定稿譯名、NAMES.TXT 譯文、譯稿 TSV（目標166 逐行字典）、變數值表與可列印 ASCII；
前端拼字時再依安全區寬度重排。
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

SIZE = 30
FLOOR = 20  # 使用者 2026-09-26 決定：超界縮字下限為欄位字級 2/3
csv.field_size_limit(1 << 24)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, default=Path("/repo/text/corpus.zh-Hant.tsv"))
    p.add_argument("--terms", type=Path, default=Path("/repo/text/terms.zh-Hant.tsv"))
    p.add_argument("--draft", type=Path, default=Path("/repo/text/draft.zh-Hant.tsv"))
    p.add_argument("--values", type=Path, default=Path("/repo/text/variable-values.zh-Hant.tsv"))
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺少合法原版，未產生圖集")
        return 77
    require(a.output.is_dir() and a.output.stat().st_uid == os.getuid(), "本機輸出目錄不存在或擁有者不符")
    require(sha(a.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    corpus, terms, draft, values = (a.corpus.read_bytes(), a.terms.read_bytes(),
                                    a.draft.read_bytes(), a.values.read_bytes())
    rows = list(csv.DictReader(io.StringIO(corpus.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))
    text = "".join(r["zh_hant"] for r in rows if r["source_file"] in ("GAME.TXT", "NAMES.TXT"))
    text += "".join(r[1] for r in csv.reader(io.StringIO(terms.decode("utf-8")), delimiter="\t") if len(r) > 1)
    for extra in (draft, values):
        rows = list(csv.DictReader(io.StringIO(extra.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))
        text += "".join(r.get("zh_hant") or r.get("zh") or "" for r in rows)
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
                continue  # 字型沒有字形者不入圖集；前端遇到即整段回原文
            cell = Image.new("L", (width, height))
            ImageDraw.Draw(cell).text((0, ascent), ch, font=font, fill=255, anchor="ls")
            glyphs[ch] = {"w": width, "alpha": base64.b64encode(cell.tobytes()).decode()}
        sizes[str(size)] = {"height": height, "ascent": ascent, "cjk_ink_top": ascent + probe[1],
                            "cjk_ink_bottom": ascent + probe[3], "glyphs": glyphs}
    payload = {"font_sha256": FONT_SHA, "font_px": SIZE, "floor_px": FLOOR,
               "bindings": {"corpus": sha(corpus), "terms": sha(terms), "draft": sha(draft), "values": sha(values)},
               "charset_sha256": sha("".join(chars).encode()), "sizes": sizes,
               "scope": "由 Cubic 11 烘製的字模；授權見 font/Cubic-11-OFL.txt"}
    (a.output / "dialog-atlas.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    top = sizes[str(SIZE)]
    print(f"字元 {len(chars)}（30px 有字形 {len(top['glyphs'])}）、字級 {SIZE}～{FLOOR}px、30px 高 {top['height']}、"
          f"中文墨跡 {top['cjk_ink_top']}–{top['cjk_ink_bottom']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
