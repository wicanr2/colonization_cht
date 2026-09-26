#!/usr/bin/env python3
"""目標148：示範「超界自動縮字」版面規則：從欄位字級逐級縮小到下限，仍放不下則回原文。

以首則 help 已驗的文字安全區為框，放入最長的教學 help 譯文（壓力測試，非該則的真實視窗）。
原版像素只輸出到已忽略的 workplace。
"""

import argparse
import csv
import io
import json
import os
from pathlib import Path

from PIL import ImageDraw

from preview_goal142_help import TEXT, indexed_image, layout, rgb, NORMAL, HIGHLIGHT, SHADOW
from preview_goal102_nation_intro import draw_line

FIELD_PX, FLOOR_PX = 30, 20  # 欄位字級（使用者選 A）與縮字下限


def fit(body, font_path):
    """回傳 (版面, 字級)；到下限仍放不下回傳 (None, None)。"""
    for delta in range(0, FIELD_PX - FLOOR_PX + 1):
        lay = layout(body, font_path, -delta)
        if lay["fits"] and lay["size"] >= FLOOR_PX:
            return lay, lay["size"]
    return None, None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/help-bilingual.tsv"))
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.output.is_dir() and a.output.stat().st_uid == os.getuid()):
        raise ValueError("輸出目錄不存在或擁有者不符")
    rows = {r["message_id"]: r for r in csv.DictReader(io.StringIO(a.catalog.read_text(encoding="utf-8")), delimiter="\t")}
    before = (a.reports / "a.print-565076913.before.canvas").read_bytes()
    pal = (a.reports / "a.final.pal").read_bytes()
    base = indexed_image(before, pal)
    report = {}
    for key in ("GAME.TXT:@TUTORIAL1", "GAME.TXT:@TUTORIAL4", "GAME.TXT:@TUTORIAL17"):
        body = rows[key]["zh_hant"].replace("\\n", "").replace("%STRING0", "卡拉維爾帆船").replace("%STRING1", "毛皮")
        body = body.replace("%NUMBER0", "100")
        lay, size = fit(body, a.font)
        report[key] = {"chars": len(body), "fitted_px": size, "lines": len(lay["lines"]) if lay else None}
        if lay is None:
            continue
        im = base.copy()
        d = ImageDraw.Draw(im)
        ref = d.textbbox((0, 0), "國", font=lay["font"], anchor="ls")
        top = TEXT[1] + (TEXT[3] - TEXT[1] - lay["total"]) // 2
        for i, line in enumerate(lay["lines"]):
            draw_line(d, line, lay["font"], TEXT[0] + 4, top + i * lay["advance"] - ref[1],
                      rgb(pal, NORMAL), rgb(pal, HIGHLIGHT), rgb(pal, SHADOW))
        im.crop((240, 390, 1050, 700)).save(a.output / f"{key.split('@')[1]}.png")
    (a.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
