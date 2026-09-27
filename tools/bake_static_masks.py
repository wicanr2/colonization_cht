#!/usr/bin/env python3
"""目標151（規格034）：由靜態覆蓋 TSV、原版檢查點畫面與固定字型烘製職稱橫幅中文字模；只輸出本機研究產物。

每列以指紋矩形 SHA-256 在 --frames 下的檢查點索引畫面中找到命中影格，量出原文色號（文字帶內最暗的常見色），
中文由 22px 起縮到能放進文字帶為止（下限 15px，使用者 2026-09-26 決定的 2/3 規則），置中於文字帶。
"""

import argparse
import base64
import csv
import hashlib
import io
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from preview_goal102_nation_intro import FONT_SHA

FIELDS = ["candidate_id", "image_file", "image_sha256", "fingerprint_rect", "fingerprint_sha256", "text_band",
          "source_text", "zh_hant", "status", "notes", "ink_indices"]
FIELD_PX, FLOOR_PX = 22, 15


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rect(text):
    return tuple(int(v) for v in text.split(","))


def region(idx, r):
    x0, y0, x1, y1 = r
    return b"".join(idx[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("/repo/text/static-overlay.zh-Hant.tsv"))
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--frames", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺少合法原版，未產生字模")
        return 77
    require(a.output.is_dir() and a.output.stat().st_uid == os.getuid(), "本機輸出目錄不存在或擁有者不符")
    require(sha(a.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    catalog = a.catalog.read_bytes()
    rows = list(csv.DictReader(io.StringIO(catalog.decode("utf-8")), delimiter="\t", strict=True))
    require(rows and list(rows[0]) == FIELDS and len({r["candidate_id"] for r in rows}) == len(rows), "靜態覆蓋 TSV 欄位或鍵不符")
    frames = [(f, f.read_bytes()) for f in sorted(a.frames.rglob("*.idx"))]
    for r in rows:
        require(sha((a.game / r["image_file"]).read_bytes()) == r["image_sha256"] and r["zh_hant"] and r["status"] == "draft",
                "圖檔指紋或譯文不符：" + r["candidate_id"])
        fp, band = rect(r["fingerprint_rect"]), rect(r["text_band"])
        hit = next(((f, idx) for f, idx in frames if sha(region(idx, fp)) == r["fingerprint_sha256"]), None)
        require(hit is not None, "檢查點中找不到命中影格：" + r["candidate_id"])
        pal = hit[0].with_suffix(".pal").read_bytes()
        counts = Counter(region(hit[1], band))
        lum = lambda v: sum(pal[v * 3:v * 3 + 3])
        # 目標166：有 ink_indices 時以列出的色號為原文（第一個為中文字色）；否則沿用最暗色號。
        ink = int(r["ink_indices"].split(",")[0]) if r["ink_indices"] else min((v for v, c in counts.items() if c >= 10), key=lum)
        width, height = (band[2] - band[0]) * 4 - 8, (band[3] - band[1]) * 4
        # 製作名單橫幅量得 22px；目標166 起帶 ink_indices 的列另依原版大寫字高 7 邏輯像素從 28px 起算。
        start = 28 if r["ink_indices"] else FIELD_PX
        for size in range(start, FLOOR_PX - 1, -1):
            font = ImageFont.truetype(str(a.font), size)
            l, t, rr, b = font.getbbox(r["zh_hant"])
            if rr - l <= width and b - t <= height:
                break
        else:
            raise ValueError("譯文縮到 15px 仍放不下：" + r["candidate_id"])
        mask = Image.new("L", (rr - l, b - t))
        ImageDraw.Draw(mask).text((-l, -t), r["zh_hant"], font=font, fill=255)
        x = band[0] * 4 + ((band[2] - band[0]) * 4 - mask.width) // 2
        y = band[1] * 4 + ((band[3] - band[1]) * 4 - mask.height) // 2
        payload = {"candidate_id": r["candidate_id"], "catalog_sha256": sha(catalog),
                   "translation_sha256": sha(r["zh_hant"].encode()), "font_sha256": FONT_SHA, "font_px": size,
                   "width": mask.width, "height": mask.height, "x": x, "y": y, "ink_index": ink,
                   "reference_frame": hit[0].name, "alpha": base64.b64encode(mask.tobytes()).decode(),
                   "scope": "local-only；衍生字模不加入 Git 或散布包"}
        (a.output / (r["candidate_id"].replace(":", "-") + ".json")).write_text(json.dumps(payload, ensure_ascii=False) + "\n")
        print(f"{r['candidate_id']}：{size}px {mask.width}×{mask.height}，色號 {ink}，命中 {hit[0].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
