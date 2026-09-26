#!/usr/bin/env python3
"""目標158（Issue #27）：全遊戲 TXT 訊息分母與譯稿覆蓋率；原版缺失回 SKIP 77。

單位是「含英文字母的顯示行」：排除 `;` 註解（含資料行尾的註解）、`@` 段落與控制行、不含字母的資料行（數字、座標）。
NAMES.TXT 等「名稱,數值…」資料行只取第一個逗號前的名稱。
各行依所屬檔案分類；遊戲畫面分母只含 game 類，安裝說明、記憶體警告、除錯訊息與 README 另列。
既有譯稿以來源檔位移範圍對照：與某筆清冊範圍重疊即「已抽取」，該筆譯文非空即「已翻譯」。
可提交的摘要只含數量；含原文的明細與未建檔清單只寫到已忽略的 workplace。
"""

import argparse
import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from pathlib import Path

# 檔案分類：game＝遊戲畫面文字；其餘不計入遊戲畫面分母。
CLASSES = {"AUTOEXEC.TXT": "install", "CONFIG.TXT": "install", "MEMORY.TXT": "memory-warning",
           "MEMORY2.TXT": "memory-warning", "DEBUG.TXT": "debug", "README.TXT": "readme"}
# 清冊 → (來源檔欄, 位移欄, 長度欄, 譯文欄)；來源欄可能是封存成員路徑，取檔名。
CATALOGS = {
    "draft.zh-Hant.tsv": ("source_file", "byte_offset", "source_byte_length", "zh_hant"),
    "build-caption-values.zh-Hant.tsv": ("source_file", "byte_offset", "source_byte_length", "zh_hant"),
    "colony-bilingual.tsv": ("source_member", "text_offset", "text_byte_length", "zh_hant"),
    "help-bilingual.tsv": ("source_file", "text_offset", "text_byte_length", "zh_hant"),
    "nation-card-fragments.zh-Hant.tsv": ("source_file", "byte_offset", "source_byte_length", "zh_hant"),
    "nation-introduction.zh-Hant.tsv": ("source_file", "section_offset", "section_byte_length", "zh_hant_draft"),
    "pedia-bilingual.tsv": ("source_file", "text_offset", "text_byte_length", "zh_hant"),
    "readme-bilingual.tsv": ("source_member", "span_offset", "span_byte_length", "zh_hant"),
    "sea-status.zh-Hant.tsv": ("source_file", "byte_offset", "source_byte_length", "zh_hant"),
}
DATA_TAIL = re.compile(r",[\s\d,.\-+]*$")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def units(name, data):
    """逐行切出候選單位：(位移, 長度, 顯示文字)。"""
    out, pos = [], 0
    for raw in data.split(b"\n"):
        start, line = pos, raw.rstrip(b"\r")
        pos += len(raw) + 1
        text = line.decode("cp437")
        s = text.strip()
        if not s or s.startswith(";") or (s.startswith("@") and name != "AUTOEXEC.TXT"):
            continue
        if ";" in s and not re.search(r"[A-Za-z]", s[:s.index(";")]):  # 資料行尾的註解（例如動畫參數表）
            continue
        if "," in s and DATA_TAIL.search(s):
            s = s[:s.index(",")].strip()
        if not re.search(r"[A-Za-z]", s):
            continue
        out.append((start, len(line), s))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--detail", type=Path, required=True)
    a = p.parse_args()
    files = sorted(a.game.glob("*.TXT"))
    if not files:
        print("SKIP：缺合法原版，未產生分母")
        return 77
    ranges = defaultdict(list)  # 檔名 → [(起, 迄, 已翻譯, 清冊)]
    for cat, (fcol, ocol, lcol, zcol) in CATALOGS.items():
        for r in csv.DictReader(io.StringIO((a.text / cat).read_text(encoding="utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
            off, n = int(r[ocol], 0), int(r[lcol])
            ranges[Path(r[fcol]).name].append((off, off + n, bool(r[zcol].strip()), cat))
    per_file, detail, pending = {}, [], []
    for f in files:
        data = f.read_bytes()
        cls = CLASSES.get(f.name, "game")
        stats = {"class": cls, "sha256": sha(data), "units": 0, "extracted": 0, "translated": 0}
        for off, n, text in units(f.name, data):
            hits = [r for r in ranges[f.name] if r[0] < off + max(n, 1) and off < r[1]]
            stats["units"] += 1
            stats["extracted"] += bool(hits)
            done = any(h[2] for h in hits)
            stats["translated"] += done
            row = {"file": f.name, "class": cls, "offset": f"0x{off:08X}", "length": n, "text": text,
                   "catalogs": sorted({h[3] for h in hits}), "translated": done}
            detail.append(row)
            if cls == "game" and not hits:
                pending.append(row)
        per_file[f.name] = stats
    total = defaultdict(lambda: {"units": 0, "extracted": 0, "translated": 0})
    for s in per_file.values():
        for k in ("units", "extracted", "translated"):
            total[s["class"]][k] += s[k]
    summary = {"unit": "含英文字母的顯示行（排除註解、控制行、資料數值）", "files": per_file, "by_class": dict(total),
               "game_pending_units": len(pending),
               "game_pending_by_file": {k: sum(r["file"] == k for r in pending) for k in sorted({r["file"] for r in pending})}}
    a.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    a.detail.write_text(json.dumps({"units": detail, "pending": pending}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"by_class": summary["by_class"], "game_pending_by_file": summary["game_pending_by_file"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
