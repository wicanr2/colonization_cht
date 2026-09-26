#!/usr/bin/env python3
"""目標159（Issue #27）：把子代理的語料譯文逐筆驗證後合併進 text/corpus.zh-Hant.tsv；原版缺失回 SKIP 77。

驗證：鍵與批次一致、來源片段 SHA-256 與原版相符、控制碼數量不變（有編號的 %變數可依中文語序移動，^ 段落標記順序不變，大括號成對）、清單類檔案行數不變、
用字都在 Cubic 11 內、不含常見簡體字、英文引號已改成「」。任何一筆不過就整批不寫。
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from prep_corpus_batches import PROSE
from prototype_overlay import FONT_SHA, cmap_coverage

FIELDS = ["message_id", "source_file", "source_file_sha256", "text_offset", "text_byte_length",
          "source_bytes_sha256", "source_en", "zh_hant", "status", "notes"]
CONTROL = re.compile(r"%[A-Z]+\d*|%%|[{}]|\^+|~[\x21-\x7e]|@[a-z]+=\d+|\$[A-Za-z_]+")
SIMPLIFIED = set("们这说对为发时会个国学来过还没现问题实经动开关应该让写书头长门见网请车东马鸟龙乐从众优伤传农军将战击钱铁银"
                 "亲爱买卖岁节办边单质飞热权听觉称厂兰历级纪线组练运远进连选递钟阶队阳险陆难顺须领题风饭驾骑鱼鸡护贸价复务")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--batches", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版")
        return 77
    font = a.font.read_bytes()
    if sha(font) != FONT_SHA:
        raise ValueError("Cubic 11 指紋不符")
    coverage = cmap_coverage(font)
    existing = {}
    if a.catalog.is_file():
        lines = a.catalog.read_text(encoding="utf-8").rstrip("\n").split("\n")
        if lines[0].split("\t") != FIELDS:
            raise ValueError("語料清冊欄位不符")
        for l in lines[1:]:
            c = dict(zip(FIELDS, l.split("\t")))
            existing[c["message_id"]] = c
    errors, added = [], []
    for src in sorted(a.batches.glob("batch-*.json")):
        if src.name.endswith(".done.json"):
            continue
        done_path = src.with_name(src.stem + ".done.json")
        if not done_path.is_file():
            continue
        items = json.loads(src.read_text(encoding="utf-8"))
        done = json.loads(done_path.read_text(encoding="utf-8"))
        if [d["id"] for d in done] != [i["id"] for i in items]:
            errors.append(f"{src.name}：鍵或順序不符")
            continue
        for it, out in zip(items, done):
            where = f"{src.name}:{it['id']}"
            data = (a.game / it["file"]).read_bytes()
            off, n = int(it["offset"], 16), it["length"]
            if sha(data) != it["file_sha256"] or sha(data[off:off + n]) != it["bytes_sha256"]:
                errors.append(f"{where}：來源指紋不符")
            zh = out["zh"].replace("\r", "").replace("\n", "\\n")  # 子代理可能輸出實體換行；清冊一律用字面 \n
            if "\t" in zh or "\n" in zh or "\r" in zh:
                errors.append(f"{where}：譯文含實體 tab 或換行")
            # 占位符有編號，可依中文語序移動：%變數與熱鍵比多重集合；段落標記 ^ 與 @ 控制行比順序；大括號數量相同且成對。
            ce, cz = CONTROL.findall(it["en"]), CONTROL.findall(zh)
            movable = lambda xs: sorted(x for x in xs if x.startswith(("%", "~", "$")))
            fixed = lambda xs: [x for x in xs if x.startswith(("^", "@"))]
            depth, ok = 0, True
            for ch in (x for x in cz if x in "{}"):
                depth += 1 if ch == "{" else -1
                ok = ok and 0 <= depth <= 1
            if movable(ce) != movable(cz) or fixed(ce) != fixed(cz) or ce.count("{") != cz.count("{") or not ok or depth:
                errors.append(f"{where}：控制碼不同 {ce} → {cz}")
            if it["file"] not in PROSE and zh.count("\\n") != it["en"].count("\\n"):
                errors.append(f"{where}：清單項目行數不同")
            miss = sorted({c for c in zh if ord(c) > 0x7e and ord(c) not in coverage})
            if miss:
                errors.append(f"{where}：Cubic 11 缺字 {''.join(miss)}")
            simp = sorted({c for c in zh if c in SIMPLIFIED})
            if simp:
                errors.append(f"{where}：疑似簡體字 {''.join(simp)}")
            if '"' in zh:
                errors.append(f"{where}：殘留英文引號")
            omit = not zh.strip()
            if omit and not out.get("note", "").strip():  # 英文冠詞等中文不需要的片段可留空，但必須寫理由
                errors.append(f"{where}：譯文為空且未說明")
            added.append({"message_id": it["id"], "source_file": it["file"], "source_file_sha256": it["file_sha256"],
                          "text_offset": it["offset"], "text_byte_length": str(n), "source_bytes_sha256": it["bytes_sha256"],
                          "source_en": it["en"], "zh_hant": zh, "status": "omit" if omit else "draft",
                          "notes": ("目標159；" + out.get("note", "")).rstrip("；")})
    dup = [r["message_id"] for r in added if r["message_id"] in existing]
    report = {"result": "PASS" if not errors else "FAIL", "errors": errors, "added": len(added), "already_present": dup}
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({**report, "errors": errors[:30]}, ensure_ascii=False))
    if errors or not a.write:
        return 1 if errors else 0
    for r in added:
        existing[r["message_id"]] = r
    rows = sorted(existing.values(), key=lambda r: (r["source_file"], int(r["text_offset"], 16)))
    a.catalog.write_text("\n".join(["\t".join(FIELDS)] + ["\t".join(r[f] for f in FIELDS) for r in rows]) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
