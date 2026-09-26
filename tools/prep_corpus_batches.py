#!/usr/bin/env python3
"""目標159（Issue #27）：把目標158 的未建檔遊戲畫面行切成訊息單位並分批，供子代理翻譯；原版缺失回 SKIP 77。

散文檔（GAME／PEDIA／MAPEDIT）：同一段落（@NAME）內相鄰且中間沒有已建檔行的未建檔行合成一則，
範圍從第一行起點到最後一行終點（含其間的控制行）。清單檔（NAMES／LABELS／MENU 等）每行一則。
輸出只寫到已忽略的 workplace；含原文。
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from text_inventory import CLASSES, CATALOGS, units

PROSE = {"GAME.TXT", "PEDIA.TXT", "MAPEDIT.TXT"}
SECTION = re.compile(rb"^@[A-Z][A-Z0-9_]*")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def covered_ranges(text_dir):
    import csv
    import io
    from collections import defaultdict
    ranges = defaultdict(list)
    for cat, (fcol, ocol, lcol, _) in CATALOGS.items():
        for r in csv.DictReader(io.StringIO((text_dir / cat).read_text(encoding="utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
            off = int(r[ocol], 0)
            ranges[Path(r[fcol]).name].append((off, off + int(r[lcol])))
    extra = text_dir / "corpus.zh-Hant.tsv"
    if extra.is_file():
        for r in csv.DictReader(io.StringIO(extra.read_text(encoding="utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
            off = int(r["text_offset"], 0)
            ranges[r["source_file"]].append((off, off + int(r["text_byte_length"])))
    return ranges


def sections(data):
    """回傳 [(位移, 段名)]，依位移遞增。"""
    out, pos = [], 0
    for raw in data.split(b"\n"):
        m = SECTION.match(raw)
        if m:
            out.append((pos, m.group().decode()))
        pos += len(raw) + 1
    return out


def section_at(secs, off):
    name = "(head)"
    for start, s in secs:
        if start > off:
            break
        name = s
    return name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--batch-lines", type=int, default=120)
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版")
        return 77
    ranges = covered_ranges(a.text)
    messages = []
    for f in sorted(a.game.glob("*.TXT")):
        if CLASSES.get(f.name, "game") != "game":
            continue
        data = f.read_bytes()
        secs = sections(data)
        run = []

        def flush():
            if run:
                start, end = run[0][0], run[-1][0] + run[-1][1]
                frag = data[start:end]
                messages.append({"id": f"{f.name}:{section_at(secs, start)}:0x{start:08X}", "file": f.name,
                                 "file_sha256": sha(data), "offset": f"0x{start:08X}", "length": end - start,
                                 "bytes_sha256": sha(frag), "lines": len(run),
                                 "en": frag.decode("cp437").replace("\r", "").replace("\n", "\\n")})
                run.clear()

        for off, n, _ in units(f.name, data):
            hit = any(r0 < off + max(n, 1) and off < r1 for r0, r1 in ranges[f.name])
            if hit:
                flush()
                continue
            if run and (f.name not in PROSE or section_at(secs, off) != section_at(secs, run[0][0])):
                flush()
            run.append((off, n))
            if f.name not in PROSE:
                flush()
        flush()
    batches, cur, lines = [], [], 0
    for m in messages:
        if cur and lines + m["lines"] > a.batch_lines:
            batches.append(cur)
            cur, lines = [], 0
        cur.append(m)
        lines += m["lines"]
    if cur:
        batches.append(cur)
    a.output.mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(batches, 1):
        (a.output / f"batch-{i:02d}.json").write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"messages": len(messages), "lines": sum(m["lines"] for m in messages), "batches": len(batches),
                      "per_batch": [len(b) for b in batches]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
