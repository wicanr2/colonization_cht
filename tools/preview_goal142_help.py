#!/usr/bin/env python3
"""目標142：首則 help（@TUTORIAL1）視窗的可丟棄 A／B 中文版面預覽；原版像素只輸出到已忽略的 workplace。"""

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

from preview_goal102_nation_intro import FONT_SHA, choose_size, draw_line, marked_chars, wrap

# 原版木紋框 (64,100)–(260,172)；文字區以原版墨跡 (69,106)–(250,165) 外擴，四倍座標。
PANEL = (64 * 4, 100 * 4, 260 * 4, 172 * 4)
TEXT = (68 * 4, 104 * 4, 256 * 4, 169 * 4)
ORIGINAL_INK_HEIGHT = 7   # 原版正文大寫字墨跡高（邏輯像素）
ORIGINAL_LINE_ADVANCE = 10
NORMAL, HIGHLIGHT, SHADOW = 68, 149, 47  # 原版一般字、{} 強調字與陰影色號
CARAVEL = "卡拉維爾帆船"  # PEDIA.TXT:@UNIT13 的既有譯名；執行期 %STRING0 = Caravel


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rgb(palette, index):
    return tuple(palette[index * 3 + i] * 255 // 63 for i in range(3))


def indexed_image(canvas, palette):
    image = Image.new("RGB", (320, 200))
    image.putdata([rgb(palette, v) for v in canvas])
    return image.resize((1280, 800), Image.NEAREST)


def layout(body, font_path, delta):
    font, size, exact, exact_height, height = choose_size((font_path, "國"), ORIGINAL_INK_HEIGHT * 4, delta)
    limit = TEXT[2] - TEXT[0] - 8  # 右界預留 4px 陰影與 4px 內距
    lines, widths, bad = wrap(marked_chars(body), font, limit)
    advance = max(height + 6, ORIGINAL_LINE_ADVANCE * 4)
    total = (len(lines) - 1) * advance + height + 4
    return {"font": font, "size": size, "exact": exact, "height": height, "lines": lines,
            "widths": widths, "bad": bad, "advance": advance, "total": total,
            "fits": total <= TEXT[3] - TEXT[1] and not bad and max(widths) <= limit}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/help-bilingual.tsv"))
    p.add_argument("--reports", type=Path, required=True, help="目標142 Discoverer 探針輸出目錄")
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(), "輸出目錄不存在或擁有者不符")
    require(sha(args.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    rows = [r for r in csv.DictReader(io.StringIO(args.catalog.read_text(encoding="utf-8")), delimiter="\t")
            if r["message_id"] == "GAME.TXT:@TUTORIAL1"]
    require(len(rows) == 1, "help 草稿缺鍵或重複")
    body = rows[0]["zh_hant"].replace("%STRING0", CARAVEL)
    before = (args.reports / "a.print-565076913.before.canvas").read_bytes()
    after = (args.reports / "a.print-565321195.after.canvas").read_bytes()
    palette = (args.reports / "a.final.pal").read_bytes()
    require(sha(before) == "a18ee5bc02b824945f57b1c454a0756ae09434a3b20683b22afd7168cf3c8b52" and
            sha(after) == "111a048748df4ed963443821839c41703939017197ddf7b3d6ce583f4086c5b3", "原版收據不符")
    control = indexed_image(after, palette)
    # 文字區只還原印字前的木紋框（肖像在框外，保留印後畫面）。
    clean = control.copy()
    box = tuple(v for v in TEXT)
    clean.paste(indexed_image(before, palette).crop(box), box[:2])
    control.save(args.output / "help-control.png")
    receipt = {"body": body, "variants": {}}
    for name, delta in (("A-matched", 0), ("B-larger", 4)):
        lay = layout(body, args.font, delta)
        image = clean.copy()
        draw = ImageDraw.Draw(image)
        ref = draw.textbbox((0, 0), "國", font=lay["font"], anchor="ls")
        top = TEXT[1] + (TEXT[3] - TEXT[1] - lay["total"]) // 2
        for i, line in enumerate(lay["lines"]):
            draw_line(draw, line, lay["font"], TEXT[0] + 4, top + i * lay["advance"] - ref[1],
                      rgb(palette, NORMAL), rgb(palette, HIGHLIGHT), rgb(palette, SHADOW))
        image.save(args.output / f"help-{name}.png")
        receipt["variants"][name] = {"size": lay["size"], "ink_height": lay["height"], "lines": len(lay["lines"]),
                                     "line_advance": lay["advance"], "max_width": round(max(lay["widths"])),
                                     "total_height": lay["total"], "fits": lay["fits"],
                                     "text": ["".join(c for c, _ in line) for line in lay["lines"]]}
    (args.output / "help-preview.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
