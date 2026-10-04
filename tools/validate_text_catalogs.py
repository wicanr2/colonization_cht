#!/usr/bin/env python3
"""核對現行全部譯稿；只驗文字來源、格式與缺字，不授權畫面覆蓋。

在專案容器執行：
python3 tools/validate_text_catalogs.py --game /game --font /font/Cubic_11.ttf \
    --report workplace/reports/goal160-coverage/current-text-validation.json
原版或字型缺失回 SKIP 77；任何缺譯、來源或格式錯誤回 1。
"""

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

from coverage_report import CATALOGS
from prototype_overlay import FONT_SHA, cmap_coverage
from text_inventory import CATALOGS as LINE_CATALOGS, CLASSES, units
from validate_translation_draft import PLACEHOLDER, read_catalog, validate_sources

# 只有已登錄的三個冠詞可以省略。其他空白即使有 notes 仍算缺譯。
OMITTED = {
    "LABELS.TXT:@MISC:0x000000E7": b"a",
    "LABELS.TXT:@MISC:0x000000EA": b"an",
    "LABELS.TXT:@MISC:0x0000029D": b"The",
}
CONTROL_CATALOGS = {
    "draft.zh-Hant.tsv", "corpus.zh-Hant.tsv", "help-bilingual.tsv",
    "pedia-bilingual.tsv", "nation-card-fragments.zh-Hant.tsv",
}
EXTRA_CATALOGS = {
    "string-templates.zh-Hant.tsv": ("template_id", "zh_hant"),
    "static-overlay.zh-Hant.tsv": ("candidate_id", "zh_hant"),
    "terms.zh-Hant.tsv": ("en", "zh"),
    "variable-values.zh-Hant.tsv": ("en", "zh"),
}
SLOT = re.compile(r"\{[a-z][a-z0-9]*\}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_rows(path):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{path.name}：不接受 BOM")
    # 專案 TSV 的雙引號是原文內容，不是 CSV 引號。使用預設 CSV 方言會吞列。
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="strict")),
                            delimiter="\t", quoting=csv.QUOTE_NONE)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError(f"{path.name}：欄位缺失或重複")
    rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}：清冊為空")
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f"{path.name}：欄數不符")
    return rows


def validate_controls(en, zh):
    if Counter(PLACEHOLDER.findall(en)) != Counter(PLACEHOLDER.findall(zh)):
        return "占位符數量或名稱不符"
    if Counter(re.findall(r"[{}^~]", en)) != Counter(re.findall(r"[{}^~]", zh)):
        return "樣式控制碼數量不符"
    if Counter(re.findall(r"~[\x21-\x7e]", en)) != Counter(re.findall(r"~[\x21-\x7e]", zh)):
        return "ASCII 熱鍵不符"
    depth = 0
    for c in zh:
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth < 0 or depth > 1:
            return "強調括號未成對"
    return "強調括號未成對" if depth else ""


def validate(game, text, font):
    font_bytes = font.read_bytes()
    if sha(font_bytes) != FONT_SHA:
        raise ValueError("Cubic 11 字型指紋不符")
    cmap = cmap_coverage(font_bytes)
    catalogs, errors, omitted, source_files = {}, [], [], {}
    ranges = {}

    def error(where, reason):
        errors.append({"key": where, "reason": reason})

    def glyphs(where, zh):
        missing = sorted({f"U+{ord(c):04X}" for c in zh
                          if ord(c) > 126 and not c.isspace() and ord(c) not in cmap})
        if missing:
            error(where, "字型缺字：" + ", ".join(missing))

    for name, fields in CATALOGS.items():
        keycol, filecol, hashcol, offcol, lencol, fragcol, zhcol = fields
        rows = read_rows(text / name)
        seen = set()
        stats = {"rows": len(rows), "source_verified": 0, "translated": 0, "omitted": 0}
        for row in rows:
            key = row[keycol] if keycol else ":".join(row[k] for k in ("nation", "caption", "placeholder"))
            where = name + ":" + key
            if not key or key in seen:
                error(where, "鍵為空或重複")
                continue
            seen.add(key)
            filename = Path(row[filecol]).name
            if filename not in source_files:
                data = (game / filename).read_bytes()
                source_files[filename] = (data, sha(data))
            data, digest = source_files[filename]
            off, n = int(row[offcol], 0), int(row[lencol])
            frag = data[off:off + n]
            if not 0 <= off < off + n <= len(data) or digest != row[hashcol] or sha(frag) != row[fragcol]:
                error(where, "來源雜湊或位元組範圍不符")
                continue
            stats["source_verified"] += 1
            zh = row[zhcol]
            if name in LINE_CATALOGS:
                ranges.setdefault(filename, []).append((off, off + n, bool(zh.strip())))
            if not zh.strip():
                if (name == "corpus.zh-Hant.tsv" and OMITTED.get(key) == frag
                        and row.get("status") == "omit" and row.get("notes", "").strip()):
                    omitted.append({"catalog": name, "key": key})
                    stats["omitted"] += 1
                else:
                    error(where, "缺譯文")
                continue
            stats["translated"] += 1
            glyphs(where, zh)
            if name in CONTROL_CATALOGS:
                reason = validate_controls(frag.decode("cp437"), zh)
                if reason:
                    error(where, reason)
        catalogs[name] = stats

    for name, (keycol, zhcol) in EXTRA_CATALOGS.items():
        rows, seen = read_rows(text / name), set()
        for row in rows:
            key, zh = row[keycol], row[zhcol]
            where = name + ":" + key
            if not key or key in seen:
                error(where, "鍵為空或重複")
            seen.add(key)
            if not zh.strip():
                error(where, "缺譯文")
            glyphs(where, zh)
            if name == "string-templates.zh-Hant.tsv" and Counter(SLOT.findall(row["pattern_en"])) != Counter(SLOT.findall(zh)):
                error(where, "字串模板槽位不符")
        catalogs[name] = {"rows": len(rows), "translated": sum(bool(r[zhcol].strip()) for r in rows)}

    # 保留既有單行譯稿的更嚴格契約：CRLF 邊界、縮排與控制碼順序。
    try:
        validate_sources(read_catalog(text / "draft.zh-Hant.tsv"), game)
    except ValueError as exc:
        error("draft.zh-Hant.tsv", str(exc))
    game_lines = {"total": 0, "extracted": 0, "translated": 0, "omitted": 0}
    for path in sorted(game.glob("*.TXT")):
        if CLASSES.get(path.name, "game") != "game":
            continue
        for off, n, _ in units(path.name, path.read_bytes()):
            hits = [r for r in ranges.get(path.name, []) if r[0] < off + max(n, 1) and off < r[1]]
            game_lines["total"] += 1
            game_lines["extracted"] += bool(hits)
            game_lines["translated"] += any(r[2] for r in hits)
            if not hits:
                error(f"{path.name}:0x{off:08X}", "遊戲文字未建檔")
            elif not any(r[2] for r in hits):
                key = f"LABELS.TXT:@MISC:0x{off:08X}"
                if path.name != "LABELS.TXT" or key not in OMITTED:
                    error(f"{path.name}:0x{off:08X}", "遊戲文字缺譯")
                else:
                    game_lines["omitted"] += 1
    return {
        "result": "FAIL" if errors else "PASS", "catalogs": catalogs,
        "source_rows": sum(v["rows"] for k, v in catalogs.items() if k in CATALOGS),
        "translated_source_rows": sum(v["translated"] for k, v in catalogs.items() if k in CATALOGS),
        "omitted": omitted, "errors": errors, "font_sha256": FONT_SHA,
        "game_lines": game_lines,
        "validator_sha256": sha(Path(__file__).read_bytes()),
        "catalog_sha256": {name: sha((text / name).read_bytes()) for name in catalogs},
        "source_sha256": {name: digest for name, (_, digest) in source_files.items()},
        "scope": "譯稿來源、鍵、欄數、占位符、樣式、熱鍵與字型；不代表畫面接線或全遊戲對拍完成",
        "limitations": "國家介紹、地名、字幕變數與README有各自來源／顯示格式；此工具核對其來源及缺字，未通用化其排版。靜態圖只核對譯文，圖像定位由原規格驗收。",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--text", type=Path, default=Path(__file__).resolve().parents[1] / "text")
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        report = validate(a.game, a.text, a.font)
    except FileNotFoundError as exc:
        print(f"SKIP：缺少驗證輸入 {exc.filename}")
        return 77
    except (OSError, ValueError, KeyError, UnicodeError, csv.Error) as exc:
        print(f"FAIL：{exc}")
        return 1
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("result", "game_lines", "source_rows", "translated_source_rows", "errors")}, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
