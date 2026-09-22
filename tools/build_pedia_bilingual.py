#!/usr/bin/env python3
"""由合法 DOS 原版建立／驗證選定百科文章的雙語草稿；不修改原版。"""

import argparse
import re
from pathlib import Path

from build_help_bilingual import (
    FIELDS,
    digest,
    encoded_lines,
    escape_text,
    read_tsv,
    render,
    unescape_text,
)


FATHER_KEYS = [f"FATHER{i}" for i in range(25)]
CARGO_KEYS = [f"CARGO{i}" for i in range(16)]
UNIT_KEYS = [f"UNIT{i}" for i in range(24)]
KEYS = FATHER_KEYS + CARGO_KEYS + UNIT_KEYS
PLACEHOLDER = re.compile(r"%(?:[A-Z][a-z]|[A-Z]+[0-9]*(?:\$)?)")
CONTROLS = re.compile(r"[{}^~_]")
PERCENT_ESCAPES = re.compile(r"%%")
NOTES = "百科整段草稿；檔案來源已確認，執行事件與中文安全矩形尚未驗證"


def source_rows(game):
    path = game / "PEDIA.TXT"
    if not path.is_file():
        print("SKIP：缺少合法原版：PEDIA.TXT")
        return None
    data = path.read_bytes()
    lines, offsets = encoded_lines(data)
    anchors = {}
    for index, line in enumerate(lines):
        marker = line.rstrip(b"\r\n")
        if marker.startswith(b"@"):
            anchors.setdefault(marker[1:].decode("ascii"), []).append(index)

    rows = []
    for key in KEYS:
        positions = anchors.get(key, [])
        if len(positions) != 1:
            raise ValueError(f"PEDIA.TXT:@{key} 不唯一或不存在")
        anchor = positions[0]
        start = anchor + 1
        while start < len(lines) and lines[start].startswith((b"@width=", b"@x=", b"@y=", b"@smallfont")):
            start += 1
        end = start
        while end < len(lines) and not lines[end].startswith(b"@"):
            end += 1
        while end > start and lines[end - 1].strip() == b"":
            end -= 1
        if end == start:
            raise ValueError(f"PEDIA.TXT:@{key} 沒有文字")
        raw = b"".join(lines[start:end]).removesuffix(b"\r\n")
        original = raw.decode("ascii", errors="strict").replace("\r\n", "\n")
        rows.append({
            "message_id": f"PEDIA.TXT:@{key}",
            "source_file": "PEDIA.TXT",
            "source_file_sha256": digest(data),
            "section_offset": f"0x{offsets[anchor]:08X}",
            "text_offset": f"0x{offsets[start]:08X}",
            "text_byte_length": str(len(raw)),
            "source_bytes_sha256": digest(raw),
            "source_en": escape_text(original),
            "status": "draft",
            "notes": NOTES,
        })
    return rows


def translations(rows, path, build, existing_catalog=None):
    pairs = read_tsv(path, ["message_id", "zh_hant"] if build else FIELDS)
    values = {row["message_id"]: row["zh_hant"] for row in pairs}
    if len(values) != len(pairs):
        raise ValueError("百科翻譯鍵重複")
    if existing_catalog is not None:
        existing_pairs = read_tsv(existing_catalog, FIELDS)
        existing = {row["message_id"]: row["zh_hant"] for row in existing_pairs}
        if len(existing) != len(existing_pairs):
            raise ValueError("既有百科目錄鍵重複")
        overlap = set(existing) & set(values)
        if overlap:
            raise ValueError("既有目錄與新譯文鍵重複")
        values = existing | values
    expected = {row["message_id"] for row in rows}
    if set(values) != expected:
        raise ValueError("百科翻譯鍵有缺漏或孤兒")
    for row in rows:
        translated = values[row["message_id"]]
        if not translated.strip():
            raise ValueError(row["message_id"] + " 缺譯")
        original = unescape_text(row["source_en"])
        zh_hant = unescape_text(translated)
        if PLACEHOLDER.findall(original) != PLACEHOLDER.findall(zh_hant):
            raise ValueError(row["message_id"] + " 變數占位符不符")
        if CONTROLS.findall(original) != CONTROLS.findall(zh_hant):
            raise ValueError(row["message_id"] + " 控制碼不符")
        if PERCENT_ESCAPES.findall(original) != PERCENT_ESCAPES.findall(zh_hant):
            raise ValueError(row["message_id"] + " 百分比控制符號不符")
        row["zh_hant"] = translated
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--translations", type=Path, help="僅建立時使用的本機雙欄譯文草稿")
    args = parser.parse_args()
    rows = source_rows(args.game)
    if rows is None:
        return 77
    rows = translations(
        rows,
        args.translations or args.catalog,
        bool(args.translations),
        args.catalog if args.translations else None,
    )
    content = render(rows)
    if args.translations:
        if not args.catalog.parent.is_dir():
            raise ValueError("輸出目錄不存在")
        args.catalog.write_text(content, encoding="utf-8")
    elif args.catalog.read_text(encoding="utf-8") != content:
        raise ValueError("TSV與固定原版來源或欄位不符")
    print(f"驗證通過：{len(rows)} 篇百科原文／譯文；只確認檔案來源，未驗畫面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
