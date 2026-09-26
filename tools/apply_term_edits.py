#!/usr/bin/env python3
"""目標156（Issue #27）：把子代理的套用術語改稿合併回譯稿 TSV，逐列驗證後才寫入。

驗證：鍵存在且唯一、現行譯文與切批時相同、ASCII 片段（占位符、控制碼、英文）完全不變、
應換術語已出現或有不換理由、短欄位不暴增、新字元都在 Cubic 11 字形內。任何一列不過就整批不寫。
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from prototype_overlay import FONT_SHA, cmap_coverage

ZH = {"draft.zh-Hant.tsv": ("candidate_id", "zh_hant"), "build-caption-values.zh-Hant.tsv": ("placeholder", "zh_hant"),
      "help-bilingual.tsv": ("message_id", "zh_hant"), "nation-card-fragments.zh-Hant.tsv": ("candidate_id", "zh_hant"),
      "nation-introduction.zh-Hant.tsv": ("message_id", "zh_hant_draft"), "pedia-bilingual.tsv": ("message_id", "zh_hant"),
      "readme-bilingual.tsv": ("message_id", "zh_hant"), "sea-status.zh-Hant.tsv": ("candidate_id", "zh_hant")}
ASCII = re.compile(r"[\x21-\x7e]+")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--batches", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--write", action="store_true", help="全部通過才寫回 TSV")
    a = p.parse_args()
    font = a.font.read_bytes()
    if hashlib.sha256(font).hexdigest() != FONT_SHA:
        raise ValueError("Cubic 11 指紋不符")
    coverage = cmap_coverage(font)
    tables = {}
    for name in ZH:
        lines = (a.text / name).read_text(encoding="utf-8").rstrip("\n").split("\n")
        tables[name] = [lines[0].split("\t")] + [l.split("\t") for l in lines[1:]]
    errors, changed, skipped, seen = [], [], [], set()
    for src in sorted(a.batches.glob("batch-*.json")):
        if src.name.endswith(".done.json"):
            continue
        items = json.loads(src.read_text(encoding="utf-8"))
        done = json.loads(src.with_name(src.stem + ".done.json").read_text(encoding="utf-8"))
        if len(done) != len(items):
            errors.append(f"{src.name}：筆數不符")
            continue
        for it, out in zip(items, done):
            where = f"{src.name}:{it['catalog']}:{it['key']}"
            if (out["catalog"], out["key"]) != (it["catalog"], it["key"]):
                errors.append(f"{where}：鍵或順序被改")
                continue
            ident = (it["catalog"], it["key"], it["zh"], out["zh_new"])
            if ident in seen:  # 同鍵同文同改法的重複項（字幕變數多列共用）只處理一次
                continue
            seen.add(ident)
            head, *body = tables[it["catalog"]]
            kcol, zcol = (head.index(c) for c in ZH[it["catalog"]])
            rows = [r for r in body if r[kcol] == it["key"]]
            if it["catalog"] == "build-caption-values.zh-Hant.tsv":
                # 字幕變數以 nation:caption:placeholder 為鍵；同占位符同譯文的多列一併改（例如四國共用的 %STRING0）
                rows = [r for r in body if r[kcol] == it["key"] and r[zcol] == it["zh"]]
            if not rows or (len(rows) != 1 and it["catalog"] != "build-caption-values.zh-Hant.tsv") or rows[0][zcol] != it["zh"]:
                errors.append(f"{where}：找不到唯一列或現行譯文已變")
                continue
            new = out["zh_new"]
            if ASCII.findall(new) != ASCII.findall(it["zh"]):
                errors.append(f"{where}：ASCII 片段改變")
            miss = [c for c in new if ord(c) > 0x7e and ord(c) not in coverage]
            if miss:
                errors.append(f"{where}：Cubic 11 缺字 {''.join(sorted(set(miss)))}")
            skip = {s["en"].lower() for s in out.get("skipped", [])}
            for t in it["expected"]:
                if not any(z in new for z in t["zh"]) and t["en"].lower() not in skip:
                    errors.append(f"{where}：未換 {t['en']} 也未說明")
            if len(it["zh"]) < 10 and len(new) > len(it["zh"]) + 3:
                errors.append(f"{where}：短欄位增長過多")
            skipped += [{"catalog": it["catalog"], "key": it["key"], **s} for s in out.get("skipped", [])]
            if new != it["zh"]:
                changed.append({"catalog": it["catalog"], "key": it["key"], "before": it["zh"], "after": new})
                for r in rows:
                    r[zcol] = new
    report = {"result": "PASS" if not errors else "FAIL", "errors": errors, "changed": len(changed),
              "skipped": skipped, "by_catalog": {n: sum(c["catalog"] == n for c in changed) for n in ZH}}
    a.report.write_text(json.dumps({**report, "changes": changed}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "skipped"} | {"skipped": len(skipped)}, ensure_ascii=False)[:3000])
    if errors:
        return 1
    if a.write:
        for name, (head, *body) in tables.items():
            (a.text / name).write_text("\n".join("\t".join(r) for r in [head] + body) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
