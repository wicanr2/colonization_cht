#!/usr/bin/env python3
"""規格053：核對完整語言譯稿，唯讀基準並產生私用文本相容檔。"""

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("locale", "catalog", "key", "base_sha256", "text", "status", "notes")
LOCALES = {"zh-Hans", "ja", "ko"}
SLOTS = re.compile(r"%Fs|%[A-Z_]+[0-9]*|%%|%(?:[0-9]+\$)?[-+ #0-9.]*[A-Za-z]|\{[A-Za-z][A-Za-z_0-9]*\}")
MARKUP = re.compile(r"[{}^~]|\\+(?:n|t|r|u[0-9a-fA-F]{4})")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_tsv(data, expected=None, legacy=False):
    require(len(data) <= 16 * 1024 * 1024, "TSV過大")
    source = data.decode("utf-8", errors="strict")
    require(not source.startswith("\ufeff") and "\x00" not in source, "TSV包含BOM或NUL")
    # 正式Go消費端以實體列及tab切欄。已固定基準中的引號是原文字元，不能跨列配對。
    reader = csv.reader(io.StringIO(source), delimiter="\t", strict=not legacy,
                        quoting=csv.QUOTE_NONE if legacy else csv.QUOTE_MINIMAL)
    header = next(reader, [])
    require(header and len(header) == len(set(header)), "TSV缺少欄名或欄名重複")
    if expected is not None:
        require(tuple(header) == tuple(expected), "TSV欄名或順序不同")
    rows = []
    for number, values in enumerate(reader, 2):
        require(len(values) == len(header), f"TSV第{number}列欄數不同")
        rows.append(dict(zip(header, values)))
    return header, rows


def write_tsv(header, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=header, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


class BaseCatalog:
    def __init__(self, text_root=ROOT / "text", registry=ROOT / "tools/language-catalogs.json"):
        self.registry = json.loads(registry.read_text())
        require(self.registry["schema"] == 1, "語料登錄版本不同")
        self.entries, self.tables = {}, []
        bindings = []
        for table in self.registry["tables"]:
            name = table["file"]
            require(Path(name).name == name, "基準檔名不可含路徑")
            data = (text_root / name).read_bytes()
            require(sha(data) == table["sha256"], f"基準檔案指紋不同：{name}")
            header, rows = read_tsv(data, legacy=True)
            require(len(rows) == table["rows"], f"基準列數不同：{name}")
            resolved = []
            for row in rows:
                key = "/".join(row[column] for column in table["key_columns"])
                if table["catalog"] in ("terms", "values"):
                    key = "sha256:" + sha(key.encode("utf-8"))
                identity = table["catalog"], key
                require(identity not in self.entries, f"基準鍵重複：{identity}")
                entry = {"catalog": table["catalog"], "key": key, "base_sha256": sha(canonical(row)),
                         "text": row[table["display_column"]], "row": row, "table": table}
                self.entries[identity] = entry
                resolved.append(entry)
                bindings.append({column: entry[column] for column in ("catalog", "key", "base_sha256")})
            self.tables.append((table, header, resolved, data))
        require(len(self.entries) == self.registry["total"] == 2008, "基準語料不完整")
        require(sha(canonical(bindings)) == self.registry["source_binding_sha256"], "完整基準鍵指紋不同")


def check_translation(base, text, status, notes, partial):
    require(not any(char in text for char in "\x00\r\n\t"), "譯文含未跳脫控制字元")
    require(status in ({"translated", "omitted", "draft"} if partial else {"translated", "omitted"}), "譯文狀態不可組裝")
    if status == "omitted":
        require(base == "" and text == "" and notes.strip(), "省略只允許既有空白來源，且須附理由")
        return
    require(text.strip(), "空白譯文未明示省略")
    require(Counter(SLOTS.findall(base)) == Counter(SLOTS.findall(text)), "占位符或格式槽位不同")
    require(MARKUP.findall(base) == MARKUP.findall(text), "排版控制結構不同")


def check_row_translation(original, translated, partial):
    check_translation(original["text"], translated["text"], translated["status"], translated["notes"], partial)
    if original["catalog"] == "corpus" and original["row"].get("source_file") == "NAMES.TXT" and "," in original["text"]:
        before, after = original["text"].split(","), translated["text"].split(",")
        require(len(before) == len(after), "複合欄位項目數不同")
        for source, target in zip(before, after):
            source_code, target_code = source.split(";", 1)[0].strip(), target.split(";", 1)[0].strip()
            if re.fullmatch(r"[-+]?\d+|[A-Z]|-", source_code):
                require(source_code == target_code, "複合欄位數值或命令不同")


def load_translation(base, data, locale, partial=False):
    require(locale in LOCALES, "新譯稿語言不支援")
    _, rows = read_tsv(data, FIELDS)
    entries = {}
    for number, row in enumerate(rows, 2):
        require(row["locale"] == locale, f"第{number}列語言不同")
        identity = row["catalog"], row["key"]
        require(identity not in entries, f"譯稿鍵重複：{identity}")
        require(identity in base.entries, f"譯稿含未知鍵：{identity}")
        original = base.entries[identity]
        require(row["base_sha256"] == original["base_sha256"], f"譯稿基準過期：{identity}")
        try:
            check_row_translation(original, row, partial)
        except ValueError as error:
            raise ValueError(f"{identity}: {error}") from error
        entries[identity] = row
    missing = sorted(set(base.entries) - set(entries))
    require(partial or not missing, f"譯稿缺少{len(missing)}列")
    return entries, missing


def make_views(base, entries, locale):
    require(locale == "zh-Hant" or locale in LOCALES, "文本組裝語言不支援")
    if locale != "zh-Hant":
        require(set(entries) == set(base.entries), "禁止用不完整譯稿組裝")
    views = {}
    for table, header, resolved, original_data in base.tables:
        if locale == "zh-Hant":
            views[table["file"]] = original_data
            continue
        rows = []
        for entry in resolved:
            translated = entries[entry["catalog"], entry["key"]]
            require(translated["locale"] == locale and
                    all(translated[field] == entry[field] for field in ("catalog", "key", "base_sha256")),
                    "組裝前來源綁定不同")
            check_row_translation(entry, translated, False)
            row = entry["row"].copy()
            row[table["display_column"]] = translated["text"]
            rows.append(row)
        # 消費端不是CSV parser；保持每個非顯示欄位的原始引號與實體列，只替換顯示欄。
        require(all(not any(ch in value for ch in "\t\r\n") for row in rows for value in row.values()),
                "消費端TSV不能包含實體換行或tab")
        views[table["file"]] = ("\t".join(header) + "\n" +
                                "".join("\t".join(row[field] for field in header) + "\n" for row in rows)).encode("utf-8")
    return views


def new_output(path, directory=False):
    path = path.resolve()
    require(path.is_relative_to((ROOT / "workplace").resolve()) and not path.exists() and
            path.parent.is_dir() and path.parent.stat().st_uid == os.getuid(), "輸出須為新的workplace路徑")
    if directory:
        path.mkdir()
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "compile"))
    parser.add_argument("--locale", required=True, choices=("zh-Hant", "zh-Hans", "ja", "ko", "en"))
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file(), "請在Docker執行")
    base = BaseCatalog()
    entries, missing, catalog_sha = {}, [], None
    if args.locale in LOCALES:
        require(args.catalog is not None, "新語言需指定TSV譯稿")
        data = args.catalog.read_bytes()
        entries, missing = load_translation(base, data, args.locale, args.partial)
        catalog_sha = sha(data)
    else:
        require(args.catalog is None and not args.partial, "原文／繁中不得覆寫基準資料")
    result = {"kind": "language-text-only-not-runtime-bundle", "locale": args.locale,
              "source_binding_sha256": base.registry["source_binding_sha256"], "catalog_sha256": catalog_sha,
              "total": len(base.entries), "provided": len(entries) if args.locale in LOCALES else len(base.entries),
              "missing": [{"catalog": catalog, "key": key} for catalog, key in missing],
              "status_counts": dict(Counter(row["status"] for row in entries.values())),
              "limitations": ["Font coverage, layout, runtime switching and normal GUI are not proved by text assembly."]}
    if args.action == "compile":
        require(not args.partial and args.output is not None, "組裝需完整譯稿與新的輸出目錄")
        views = {} if args.locale == "en" else make_views(base, entries, args.locale)
        output = new_output(args.output, directory=True)
        result["original_rendering"] = args.locale == "en"
        result["input_sha256"] = {table["file"]: table["sha256"] for table, _, _, _ in base.tables}
        result["output_sha256"] = {name: sha(data) for name, data in views.items()}
        for name, data in views.items():
            (output / name).write_bytes(data)
        (output / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        require(all(p.stat().st_uid == os.getuid() for p in output.iterdir()), "輸出擁有者不同")
    elif args.output:
        new_output(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "missing"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
