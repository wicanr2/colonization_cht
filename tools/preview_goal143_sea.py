#!/usr/bin/env python3
"""目標143：海上主畫面選單列與狀態欄的可丟棄字級預覽（22px／20px）；原版像素只輸出到已忽略的 workplace。"""

import argparse
import hashlib
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from preview_goal102_nation_intro import FONT_SHA

# (印字開始步數, 原版墨跡半開 bbox, 草擬中文, 色號)；步數對應探針 a.print-<步數>.before.canvas。
STATUS = [
    (643677156, (242, 51, 281, 57), "1492年春季", 68),
    (643689895, (242, 58, 305, 63), "金錢：300$　稅率：0%", 68),
    (643709137, (260, 70, 290, 75), "行動：1", 68),
    (643716588, (260, 77, 313, 83), "位置：(45, 28)", 68),
    (643724978, (242, 86, 285, 92), "英．卡拉維爾帆船", 68),
    (643731991, (242, 93, 275, 98), "無命令", 149),
    (643738170, (243, 100, 268, 105), "（海洋）", 68),
    (643753677, (260, 114, 286, 120), "老兵", 149),
    (643758332, (260, 120, 282, 126), "警戒", 149),
    (643769442, (261, 132, 291, 137), "100 工具", 149),
    (643774665, (260, 138, 282, 144), "警戒", 149),
]
MENU = [((13, 1, 31, 6), "G", "遊戲"), ((45, 1, 63, 6), "V", "檢視"), ((77, 1, 101, 6), "O", "命令"),
        ((115, 1, 143, 6), "R", "報告"), ((157, 1, 177, 6), "T", "貿易"), ((255, 1, 307, 6), "C", "殖民百科")]
MENU_START = 582117206
BACKGROUND = 689291756


def rgb(pal, i):
    return tuple(pal[i * 3 + k] * 255 // 63 for k in range(3))


def image_of(canvas, pal):
    im = Image.new("RGB", (320, 200))
    im.putdata([rgb(pal, v) for v in canvas])
    return im.resize((1280, 800), Image.NEAREST)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.output.is_dir() and a.output.stat().st_uid == os.getuid()):
        raise ValueError("輸出目錄不存在或擁有者不符")
    if hashlib.sha256(a.font.read_bytes()).hexdigest() != FONT_SHA:
        raise ValueError("Cubic 11 指紋不符")
    pal = (a.probe / "a.final.pal").read_bytes()
    after = image_of((a.probe / f"a.print-{BACKGROUND}.after.canvas").read_bytes(), pal)
    after.save(a.output / "sea-control.png")
    for size in (22, 20):
        font = ImageFont.truetype(str(a.font), size)
        im = after.copy()
        # 每行先換回該行印字前的原版畫布，再以原版左緣、墨跡頂端對齊畫中文（陰影色號 0 向右下 2px）。
        for step, box, text, color in STATUS:
            before = image_of((a.probe / f"a.print-{step}.before.canvas").read_bytes(), pal)
            r = (box[0] * 4, box[1] * 4 - 2, 318 * 4, box[1] * 4 + 26)
            im.paste(before.crop(r), r[:2])
        menu_before = image_of((a.probe / f"a.print-{MENU_START}.before.canvas").read_bytes(), pal)
        im.paste(menu_before.crop((0, 0, 1280, 28)), (0, 0))
        d = ImageDraw.Draw(im)
        for step, box, text, color in STATUS:
            top = box[1] * 4 - 1
            d.text((box[0] * 4 + 2, top + 2), text, font=font, fill=rgb(pal, 0), anchor="lt")
            d.text((box[0] * 4, top), text, font=font, fill=rgb(pal, color), anchor="lt")
        for box, key, zh in MENU:
            x, top = box[0] * 4, 2
            d.text((x, top), f"({key})", font=font, fill=rgb(pal, 149), anchor="lt")
            d.text((x + round(font.getlength(f"({key})")), top), zh, font=font, fill=rgb(pal, 68), anchor="lt")
        im.save(a.output / f"sea-{size}px.png")
        print(size, "px 完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
