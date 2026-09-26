#!/usr/bin/env python3
"""目標147：靜態內嵌文字覆蓋的可丟棄最小原型（製作名單橫幅「GAME DESIGN BY」）。

只讀已忽略 workplace 內的原版索引畫面；以文字區索引位元組 SHA-256 完全相符為唯一觸發條件，
命中時在四倍畫布的文字區填回卷軸底色並畫中文，未命中一律原樣輸出。不是正式功能。
"""

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from preview_goal102_nation_intro import FONT_SHA

RECT = (104, 173, 220, 186)  # 邏輯半開：指紋比對區（含上下邊框線）
BAND = (106, 176, 218, 182)  # 只在此文字帶內清除原文；上下邊框線保留
TEXT = "遊戲設計"
SIZE = 22


def sha(b):
    return hashlib.sha256(b).hexdigest()


def region(idx):
    x0, y0, x1, y1 = RECT
    return b"".join(idx[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def decode(idx, pal):
    im = Image.new("RGB", (320, 200))
    im.putdata([tuple(pal[v * 3 + k] * 255 // 63 for k in range(3)) for v in idx])
    return im.resize((1280, 800), Image.NEAREST)


def overlay(idx, pal, fingerprint, font):
    """回傳 (輸出圖, 是否命中, 原因)。"""
    out = decode(idx, pal)
    reg = region(idx)
    if sha(reg) != fingerprint:
        return out, False, "fingerprint-mismatch"
    counts = Counter(reg)
    lum = lambda v: sum(pal[v * 3:v * 3 + 3])
    color = lambda v: tuple(pal[v * 3 + k] * 255 // 63 for k in range(3))
    paper = counts.most_common(1)[0][0]
    ink = min((v for v, c in counts.items() if c >= 10), key=lum)  # 原版文字色：區內最暗的常見色
    dark = {v for v in counts if lum(v) < 122}  # 文字與其抗鋸齒（卷軸主要底色亮度 127 以上）
    x0, y0, x1, y1 = BAND
    clean = bytearray(idx)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if clean[y * 320 + x] in dark:
                # 以同列左右最近的非文字像素補回卷軸紋理。
                for dx in range(1, 40):
                    for nx in (x - dx, x + dx):
                        if x0 <= nx < x1 and idx[y * 320 + nx] not in dark:
                            clean[y * 320 + x] = idx[y * 320 + nx]
                            break
                    else:
                        continue
                    break
    patched = decode(bytes(clean), pal)
    box = (x0 * 4, y0 * 4, x1 * 4, y1 * 4)
    out.paste(patched.crop(box), box[:2])
    d = ImageDraw.Draw(out)
    w = font.getlength(TEXT)
    d.text(((box[0] + box[2] - w) / 2, (box[1] + box[3]) / 2), TEXT, font=font, fill=color(ink), anchor="lm")
    return out, True, "applied"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames", type=Path, required=True, help="目標146 開場檢查點（*.idx／*.pal）目錄")
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not (a.output.is_dir() and a.output.stat().st_uid == os.getuid()):
        raise ValueError("輸出目錄不存在或擁有者不符")
    if sha(a.font.read_bytes()) != FONT_SHA:
        raise ValueError("Cubic 11 指紋不符")
    font = ImageFont.truetype(str(a.font), SIZE)
    load = lambda step: ((a.frames / f"opening.cp-{step}.idx").read_bytes(), (a.frames / f"opening.cp-{step}.pal").read_bytes())
    hit_idx, hit_pal = load(450000000)
    fingerprint = sha(region(hit_idx))
    tampered = bytearray(hit_idx)
    tampered[(RECT[1] + 3) * 320 + RECT[0] + 5] ^= 1
    cases = {"hit-450m": (hit_idx, hit_pal), "other-300m": load(300000000), "other-500m": load(500000000),
             "tamper-450m": (bytes(tampered), hit_pal)}
    report = {"rect": RECT, "fingerprint_sha256": fingerprint, "text": TEXT, "font_px": SIZE, "cases": {}}
    for name, (idx, pal) in cases.items():
        out, applied, why = overlay(idx, pal, fingerprint, font)
        base = decode(idx, pal)
        diff = ImageChops.difference(out, base).getbbox()
        inside = diff is None or (diff[0] >= RECT[0] * 4 and diff[1] >= RECT[1] * 4 and
                                  diff[2] <= RECT[2] * 4 and diff[3] <= RECT[3] * 4)
        out.save(a.output / f"{name}.png")
        report["cases"][name] = {"applied": applied, "reason": why, "diff_bbox": list(diff) if diff else None,
                                 "diff_inside_rect": inside}
    ok = (report["cases"]["hit-450m"]["applied"] and report["cases"]["hit-450m"]["diff_inside_rect"] and
          report["cases"]["hit-450m"]["diff_bbox"] is not None and
          all(not report["cases"][k]["applied"] and report["cases"][k]["diff_bbox"] is None
              for k in ("other-300m", "other-500m", "tamper-450m")))
    report["result"] = "PASS" if ok else "FAIL"
    (a.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
