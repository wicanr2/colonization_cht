#!/usr/bin/env python3
"""目標165（Issue #41）：通用對話框整句中文的可丟棄版面預覽；原版像素只輸出到已忽略的 workplace。

輸入是 tools/probe_goal165_dialogs.go 的探針輸出：逐字事件（字元、步數、墨跡範圍）與印前／印後畫布。
流程與日後前端相同：以逐字事件重組原版顯示字串 → 對 GAME.TXT 模板整句比對 → 代入變數譯名 →
以色號 0 外框掃描出框內安全區 → 依框寬重排中文。
"""

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw

from preview_goal102_nation_intro import FONT_SHA, choose_size, draw_line, marked_chars, wrap

GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
ORIGINAL_INK_HEIGHT = 7     # 原版正文大寫字墨跡高（邏輯像素），與 help 相同
ORIGINAL_LINE_ADVANCE = 10  # 原版行距（邏輯像素）
NORMAL, HIGHLIGHT, SHADOW = 68, 149, 47
VARIANTS = (("A-30px", 0, 40), ("B-26px", -4, 34))
csv.field_size_limit(1 << 24)


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


def load_templates(path):
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))
    out = []
    for r in rows:
        if r["source_file"] != "GAME.TXT" or r["source_file_sha256"] != GAME_SHA or "^" in r["source_en"]:
            continue
        parts = r["source_en"].split("\\n\\n")
        zh = r["zh_hant"].split("\\n\\n")
        body = re.sub(r"\s+", " ", parts[0].replace("\\n", " ").replace("{", "").replace("}", "")).strip()
        pattern, names = "", []
        for token in re.split(r"(%STRING\d|%NUMBER\d|%COUNTRY)", body):
            if token.startswith("%NUMBER"):
                pattern += r"(\d+)"
                names.append(token)
            elif token.startswith("%"):
                pattern += "(.+?)"
                names.append(token)
            else:
                pattern += re.escape(token)
        out.append({"id": r["message_id"], "regex": re.compile("^" + pattern + "$"), "names": names,
                    "zh_body": zh[0], "options_en": parts[1].split("\\n") if len(parts) > 1 else [],
                    "options_zh": zh[1].split("\\n") if len(zh) > 1 else []})
    return out


def load_terms(path):
    terms = {}
    for r in csv.reader(io.StringIO(path.read_text(encoding="utf-8")), delimiter="\t"):
        if len(r) >= 2 and r[0] and r[1]:
            terms.setdefault(r[0], r[1])
    return terms


def runtime_lines(chars):
    """逐字事件依 x 回捲切行；空白字沒有墨跡，歸入目前行。"""
    lines, cur, last_x = [], "", None
    for c in chars:
        ch = chr(c["C"])
        if c["MaxX"] >= 0:
            if last_x is not None and c["MinX"] < last_x:
                lines.append(cur)
                cur = ""
            last_x = c["MinX"]
        cur += ch
    lines.append(cur)
    return [line for line in (l.rstrip("\x00") for l in lines) if line]


def scan_box(canvas, x, y):
    px = lambda x, y: canvas[y * 320 + x]
    l, r, t, b = x, x, y, y
    while l > 0 and px(l, y) != 0:
        l -= 1
    while r < 319 and px(r, y) != 0:
        r += 1
    while t > 0 and px(x, t) != 0:
        t -= 1
    while b < 199 and px(x, b) != 0:
        b += 1
    return l, t, r, b


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe", type=Path, required=True, help="探針輸出前綴（例如 .../r6/a）")
    p.add_argument("--corpus", type=Path, default=Path("/repo/text/corpus.zh-Hant.tsv"))
    p.add_argument("--terms", type=Path, default=Path("/repo/text/terms.zh-Hant.tsv"))
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    require(a.output.is_dir() and a.output.stat().st_uid == os.getuid(), "輸出目錄不存在或擁有者不符")
    require(sha(a.font.read_bytes()) == FONT_SHA, "Cubic 11 指紋不符")
    templates, terms = load_templates(a.corpus), load_terms(a.terms)
    report = json.loads(Path(str(a.probe) + ".json").read_text())
    prints = [p for p in report["prints"] if p.get("Chars") and
              (p["Colors"].get("47") or p["Colors"].get("128"))]
    receipt = []
    for i, pr in enumerate(prints):
        lines = runtime_lines(pr["Chars"])
        shown = re.sub(r"\s+", " ", " ".join(lines)).strip()
        hits = [(t, m) for t in templates for m in [t["regex"].match(shown)] if m]
        entry = {"start": pr["Start"], "runtime_lines": lines, "shown": shown, "matches": [t["id"] for t, _ in hits]}
        receipt.append(entry)
        if len(hits) != 1:
            continue
        t, m = hits[0]
        values = {}
        for name, value in zip(t["names"], m.groups()):
            zh = value if name.startswith("%NUMBER") else terms.get(value)
            values[name] = zh
        entry["variables"] = {n: [v, values[n]] for n, v in zip(t["names"], m.groups())}
        if any(v is None for v in values.values()):
            entry["fallback"] = "variable-without-term"
            continue
        body = t["zh_body"].replace("\\n", "")
        for name, zh in values.items():
            body = body.replace(name, zh)
        prefix = f"{a.probe}.print-{pr['Start']}"
        before, after = Path(prefix + ".before.canvas").read_bytes(), Path(prefix + ".after.canvas").read_bytes()
        palette = Path(prefix + ".pal").read_bytes()
        first = next(c for c in pr["Chars"] if c["MaxX"] >= 0)
        l, top, r, b = scan_box(before, first["MinX"] + 1, (first["MinY"] + first["MaxY"]) // 2)
        nxt = prints[i + 1] if i + 1 < len(prints) else None
        bottom = b - 3
        if nxt and nxt["Start"] - pr["Chars"][-1]["Step"] < 400000 and nxt["MinY"] > pr["MaxY"]:
            bottom = nxt["MinY"] - 2  # 正文後緊接選項段；中文不得侵入選項列
        safe = ((l + 3) * 4, (top + 3) * 4, (r - 3) * 4, bottom * 4)
        entry.update({"id": t["id"], "box": [l, top, r, b], "safe_4x": list(safe), "zh": body,
                      "ink": [pr["MinX"], pr["MinY"], pr["MaxX"] + 1, pr["MaxY"] + 1], "variants": {}})
        control = indexed_image(after, palette)
        control.save(a.output / f"{t['id'].split(':')[1][1:]}-control.png")
        clean = control.copy()
        clean.paste(indexed_image(before, palette).crop(safe), safe[:2])
        for name, delta, pitch in VARIANTS:
            font, size, _, _, height = choose_size((a.font, "國"), ORIGINAL_INK_HEIGHT * 4, delta)
            limit = safe[2] - safe[0] - 8
            wrapped, widths, bad = wrap(marked_chars(body), font, limit)
            total = (len(wrapped) - 1) * pitch + height + 4
            fits = total <= safe[3] - safe[1] and not bad and max(widths) <= limit
            image = clean.copy()
            draw = ImageDraw.Draw(image)
            ref = draw.textbbox((0, 0), "國", font=font, anchor="ls")
            y0 = safe[1] + 4
            for k, line in enumerate(wrapped):
                draw_line(draw, line, font, safe[0] + 4, y0 + k * pitch - ref[1],
                          rgb(palette, NORMAL), rgb(palette, HIGHLIGHT), rgb(palette, SHADOW))
            image.save(a.output / f"{t['id'].split(':')[1][1:]}-{name}.png")
            entry["variants"][name] = {"size": size, "ink_height": height, "pitch": pitch, "lines": len(wrapped),
                                       "max_width": round(max(widths)), "total_height": total,
                                       "safe_height": safe[3] - safe[1], "fits": fits,
                                       "text": ["".join(c for c, _ in line) for line in wrapped]}
    (a.output / "preview.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
