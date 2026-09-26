#!/usr/bin/env python3
"""目標145：可重跑的文本清冊與覆蓋率報表（Issue #7）；原版缺失回 SKIP 77。

- 已抽取：各譯稿 TSV 中來源綁定（檔案 SHA、位移、片段 SHA）與原版逐字核對通過的列。
- 已翻譯：已抽取且 zh_hant 非空。
- 正常路徑中文顯示：各目標同輸入重播收據中，前端實際套用過中文的鍵。
- 正常路徑命中但未建檔：規格033 參考實作把探針事件歸不到任何鍵的字串。
- 重複／別名：同一英文原文出現在多筆清冊列。
完整明細（含原文）只寫到已忽略的 workplace；可提交的摘要只含數量與鍵。
"""

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path

from text_model import classify, load_dictionary

CATALOGS = {  # 檔名 → (鍵欄, 來源檔欄, 檔案雜湊欄, 位移欄, 長度欄, 片段雜湊欄, 譯文欄)
    "draft.zh-Hant.tsv": ("candidate_id", "source_file", "source_sha256", "byte_offset", "source_byte_length", "source_bytes_sha256", "zh_hant"),
    "nation-card-fragments.zh-Hant.tsv": ("candidate_id", "source_file", "source_sha256", "byte_offset", "source_byte_length", "source_bytes_sha256", "zh_hant"),
    "sea-status.zh-Hant.tsv": ("candidate_id", "source_file", "source_sha256", "byte_offset", "source_byte_length", "source_bytes_sha256", "zh_hant"),
    "help-bilingual.tsv": ("message_id", "source_file", "source_file_sha256", "text_offset", "text_byte_length", "source_bytes_sha256", "zh_hant"),
    "pedia-bilingual.tsv": ("message_id", "source_file", "source_file_sha256", "text_offset", "text_byte_length", "source_bytes_sha256", "zh_hant"),
    "nation-introduction.zh-Hant.tsv": ("message_id", "source_file", "source_file_sha256", "section_offset", "section_byte_length", "section_sha256", "zh_hant_draft"),
    "build-caption-values.zh-Hant.tsv": (None, "source_file", "source_file_sha256", "byte_offset", "source_byte_length", "source_bytes_sha256", "zh_hant"),
    "colony-bilingual.tsv": ("message_id", "source_member", "source_member_sha256", "text_offset", "text_byte_length", "source_bytes_sha256", "zh_hant"),
    "readme-bilingual.tsv": ("message_id", "source_member", "source_member_sha256", "span_offset", "span_byte_length", "source_bytes_sha256", "zh_hant"),
}
# 各目標同輸入重播的中文收據（前端 frames.lines 記錄每幀每欄是否套用）。
RECEIPTS = [
    "goal143-sea/regress/regression-title-1280m.json", "goal143-sea/regress/regression-build1-82m.json",
    "goal143-sea/regress/rows-1280m.json", "goal143-sea/regress135/zh-53m.json", "goal143-sea/regress135/zh-62m.json",
    "goal143-sea/regress135/zh-72m.json", "goal138-retire/dialog-zh.json", "goal139-third-card/card-zh.json",
    "goal140-nation-cards/france-zh.json", "goal140-nation-cards/spain-zh.json",
    "goal140-nation-cards/netherlands-zh.json", "goal141-captions/replay-zh.json", "goal142-help/replay-zh.json",
    "goal143-sea/replay-zh.json", "goal136-nation-intro/france-zh-56m.json", "goal136-nation-intro/spain-zh-56m.json",
    "goal136-nation-intro/netherlands-zh-56m.json", "goal136-nation-intro/france-zh-64m.json",
    "goal136-nation-intro/spain-zh-64m.json", "goal136-nation-intro/netherlands-zh-64m.json",
]
PROBES = {"captions": ("goal141-captions/full/a.json", 76000000), "help": ("goal142-help/discoverer/a.json", 76000000),
          "sea": ("goal143-sea/probe/a.json", 548000000)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_bytes(game, archive_members, name):
    path = game / name
    if path.is_file():
        return path.read_bytes()
    return archive_members.get(name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--detail", type=Path, required=True, help="含原文的完整明細（workplace）")
    p.add_argument("--summary", type=Path, required=True, help="只含數量與鍵的可提交摘要")
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未產生覆蓋率報表")
        return 77
    extracted, translated, english = {}, {}, defaultdict(list)
    per_catalog = {}
    for name, (key_col, file_col, fsha_col, off_col, len_col, bsha_col, zh_col) in CATALOGS.items():
        rows = list(csv.DictReader(io.StringIO((a.text / name).read_text(encoding="utf-8")), delimiter="\t"))
        stats = {"rows": len(rows), "extracted": 0, "translated": 0, "unverifiable": 0}
        for i, r in enumerate(rows):
            key = r[key_col] if key_col else f"{r['nation']}:{r['caption']}:{r['placeholder']}"
            data = (a.game / Path(r[file_col]).name).read_bytes() if (a.game / Path(r[file_col]).name).is_file() else None
            if data is None:
                stats["unverifiable"] += 1  # 來源在封存檔內（如 README、COLONY 原始封存），本報表不解包
                continue
            off, n = int(r[off_col], 0), int(r[len_col])
            frag = data[off:off + n]
            if sha(data) != r[fsha_col] or sha(frag) != r[bsha_col]:
                continue
            stats["extracted"] += 1
            extracted[(name, key)] = frag
            english[frag.strip()].append(f"{name}:{key}")
            if r[zh_col].strip():
                stats["translated"] += 1
                translated[(name, key)] = r[zh_col]
        per_catalog[name] = stats
    shown, missing = set(), []
    for path in RECEIPTS:
        f = a.reports / path
        if not f.is_file():
            missing.append(path)
            continue
        for frame in json.loads(f.read_text())["frames"]:
            for line in frame["lines"]:
                if line["applied"] and not line["candidate_id"].startswith("sea:"):
                    shown.add(line["candidate_id"])
    dictionary = load_dictionary(a.text / "sea-status.zh-Hant.tsv")
    traced, untraced = set(), defaultdict(int)
    for name, (path, start) in PROBES.items():
        report = json.loads((a.reports / path).read_text())
        report["prints"] = [x for x in report["prints"] if x["Start"] >= start]
        known, unknown = classify(report, dictionary)
        for e in known:
            traced.update(e["keys"])
        for u in unknown:
            untraced[u["text"]] += 1
    sea_applied = json.loads((a.reports / "goal143-sea/replay-zh.json").read_text())["frames"]
    if any(l["candidate_id"].startswith("sea:") and l["applied"] for fr in sea_applied for l in fr["lines"]):
        shown |= {k for k in traced if k.startswith(("NAMES.TXT", "LABELS.TXT", "MENU.TXT"))}
    aliases = {t.decode("latin1"): keys for t, keys in english.items() if len(keys) > 1}
    summary = {
        "catalogs": per_catalog,
        "extracted": len(extracted), "translated": len(translated),
        "normal_path_traced_keys": len(traced), "normal_path_shown_keys": len(shown),
        "traced_but_uncataloged_texts": len(untraced), "alias_groups": len(aliases),
        "shown_keys": sorted(shown), "missing_receipts": missing, "note": "英文原文與未建檔字串只在已忽略的明細檔",
    }
    a.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    detail = {**summary, "untraced": dict(untraced), "aliases": aliases}
    a.detail.write_text(json.dumps(detail, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "shown_keys"}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
