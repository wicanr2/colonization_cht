#!/usr/bin/env python3
"""目標154／155（Issue #27）：以第三波說明書術語表或定稿譯名表核對既有譯稿，列出英文原文含術語、但譯文未用說明書譯名的列。

只列衝突，不改譯稿。可提交的摘要只含鍵、術語對照與數量；含英文原文的明細寫到已忽略的 workplace。
原版缺失時，需讀原版位元組才能取得原文的清冊記為 unverifiable。
"""

import argparse
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path

# 清冊 → (鍵欄, 原文欄；None 表示依來源檔位移讀原版位元組, 譯文欄)
CATALOGS = {
    "draft.zh-Hant.tsv": ("candidate_id", None, "zh_hant"),
    "build-caption-values.zh-Hant.tsv": ("placeholder", "source_text", "zh_hant"),
    # colony-bilingual.tsv（殖民地地名）不套術語：地名是專有名詞，Fort／Indian 等字在地名中不按術語譯。
    "help-bilingual.tsv": ("message_id", "source_en", "zh_hant"),
    "nation-card-fragments.zh-Hant.tsv": ("candidate_id", "source_text", "zh_hant"),
    "nation-introduction.zh-Hant.tsv": ("message_id", "source_en_display", "zh_hant_draft"),
    "pedia-bilingual.tsv": ("message_id", "source_en", "zh_hant"),
    "readme-bilingual.tsv": ("message_id", "source_en", "zh_hant"),
    "sea-status.zh-Hant.tsv": ("candidate_id", "source_text", "zh_hant"),
    "static-overlay.zh-Hant.tsv": ("candidate_id", "source_text", "zh_hant"),
}


def rows(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glossary", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--detail", type=Path, required=True)
    a = p.parse_args()
    # 同一英文（不分大小寫）在說明書有多個譯名時全部接受；歷史背景名詞（other）不列入。
    # 定稿表（有 basis 欄，每個英文一個譯名）全部採用；說明書術語表只取印出對照。
    groups = {}
    for r in rows(a.glossary):
        if r["en"] and r["zh"] and ("basis" in r or (r["evidence"] == "印出對照" and r["category"] != "other")):
            g = groups.setdefault(r["en"].lower(), {"en": r["en"], "zh": [], "image": r["image"]})
            for z in re.split(r"[，,/／]", r["zh"]):
                if z.strip() and z.strip() not in g["zh"]:
                    g["zh"].append(z.strip())
    terms = list(groups.values())
    patterns = [(t, re.compile(r"(?<![A-Za-z])" + re.escape(t["en"]) + r"(?:s|es)?(?![A-Za-z])", re.I)) for t in terms]
    summary, detail = {"glossary_rows": len(rows(a.glossary)), "printed_terms": len(terms), "catalogs": {}}, []
    per_term = Counter()
    for name, (key_col, en_col, zh_col) in CATALOGS.items():
        stats = {"rows": 0, "matched": 0, "conflicts": 0, "unverifiable": 0}
        conflicts = []
        for r in rows(a.text / name):
            stats["rows"] += 1
            if en_col:
                en = r[en_col]
            else:
                src = a.game / r["source_file"]
                if not src.is_file():
                    stats["unverifiable"] += 1
                    continue
                off, n = int(r["byte_offset"], 0), int(r["source_byte_length"])
                en = src.read_bytes()[off:off + n].decode("latin1")
            hits = [t for t, pat in patterns if pat.search(en)]
            if not hits:
                continue
            stats["matched"] += 1
            # 較長術語優先：若長術語已對上，其中的短術語不另算（例如 Royal Expeditionary Force 內的 Force）
            hits.sort(key=lambda t: -len(t["en"]))
            covered, bad = [], []
            for t in hits:
                if any(t["en"].lower() in c.lower() for c in covered):
                    continue
                covered.append(t["en"])
                if not any(z in r[zh_col] for z in t["zh"]):
                    bad.append(t)
            if bad:
                stats["conflicts"] += 1
                key = r[key_col]
                conflicts.append({"key": key, "terms": [f"{t['en']}={'／'.join(t['zh'])}" for t in bad]})
                for t in bad:
                    per_term[f"{t['en']}={'／'.join(t['zh'])}"] += 1
                detail.append({"catalog": name, "key": key, "en": en, "zh": r[zh_col],
                               "expected": [{"en": t["en"], "zh": t["zh"], "image": t["image"]} for t in bad]})
        stats["conflict_keys"] = conflicts
        summary["catalogs"][name] = stats
    summary["total_conflicts"] = sum(s["conflicts"] for s in summary["catalogs"].values())
    summary["conflicts_by_term"] = dict(sorted(per_term.items(), key=lambda kv: (-kv[1], kv[0])))
    a.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    a.detail.write_text(json.dumps(detail, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "catalogs"} | {"per_catalog": {k: (v["matched"], v["conflicts"]) for k, v in summary["catalogs"].items()}},
                     ensure_ascii=False)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
