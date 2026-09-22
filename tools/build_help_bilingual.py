#!/usr/bin/env python3
"""由合法DOS原版建立／驗證選定help訊息的雙語草稿；不修改原版。"""

import argparse
import hashlib
import re
from pathlib import Path


SECTIONS = {
    "GAME.TXT": [f"TUTORIAL{i}" for i in range(1, 20)],
    "MAPEDIT.TXT": [f"HELP{i}" for i in range(1, 6)],
}
FIELDS = [
    "message_id", "source_file", "source_file_sha256", "section_offset",
    "text_offset", "text_byte_length", "source_bytes_sha256", "source_en",
    "zh_hant", "status", "notes",
]
PLACEHOLDER = re.compile(r"%[A-Z]+[0-9]*(?:\$)?")
CONTROLS = re.compile(r"[{}^~_\t]")
NOTES = "說明語料草稿；檔案來源已確認，執行事件與中文安全矩形尚未驗證"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded_lines(data):
    if b"\r\n" not in data or data.replace(b"\r\n", b"").find(b"\n") >= 0:
        raise ValueError("來源必須以CRLF換行")
    lines = data.splitlines(keepends=True)
    if any(not line.endswith(b"\r\n") for line in lines[:-1]):
        raise ValueError("來源有非CRLF換行")
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)
    return lines, offsets


def escape_text(text):
    if "\\" in text or "\r" in text:
        raise ValueError("來源含未支援的跳脫或欄位字元")
    return text.replace("\t", "\\t").replace("\n", "\\n")


def unescape_text(text):
    if "\n" in text or "\r" in text or "\t" in text:
        raise ValueError("TSV欄位含實際換行或Tab")
    if re.search(r"\\(?![nt])", text):
        raise ValueError("TSV含非\\n或\\t跳脫")
    return text.replace("\\t", "\t").replace("\\n", "\n")


def source_rows(game):
    rows = []
    for name, keys in SECTIONS.items():
        path = game / name
        if not path.is_file():
            print("SKIP：缺少合法原版：" + name)
            return None
        data = path.read_bytes()
        lines, offsets = encoded_lines(data)
        anchors = {}
        for i, line in enumerate(lines):
            marker = line.rstrip(b"\r\n")
            if marker.startswith(b"@"):
                anchors.setdefault(marker[1:].decode("ascii"), []).append(i)
        for key in keys:
            positions = anchors.get(key, [])
            if len(positions) != 1:
                raise ValueError(f"{name}:@{key} 不唯一或不存在")
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
                raise ValueError(f"{name}:@{key} 沒有文字")
            raw = b"".join(lines[start:end]).removesuffix(b"\r\n")
            original = raw.decode("ascii", errors="strict").replace("\r\n", "\n")
            row = {
                "message_id": f"{name}:@{key}", "source_file": name,
                "source_file_sha256": digest(data),
                "section_offset": f"0x{offsets[anchor]:08X}",
                "text_offset": f"0x{offsets[start]:08X}",
                "text_byte_length": str(len(raw)),
                "source_bytes_sha256": digest(raw),
                "source_en": escape_text(original), "status": "draft", "notes": NOTES,
            }
            rows.append(row)
    return rows


def read_tsv(path, header):
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        raise ValueError("TSV不接受BOM")
    lines = text.splitlines()
    if not lines or lines[0].split("\t") != header:
        raise ValueError("TSV欄位不符")
    result = []
    for number, line in enumerate(lines[1:], 2):
        fields = line.split("\t")
        if len(fields) != len(header):
            raise ValueError(f"第{number}行欄數不符")
        result.append(dict(zip(header, fields)))
    return result


def translations(rows, path, build):
    if build:
        pairs = read_tsv(path, ["message_id", "zh_hant"])
        values = {r["message_id"]: r["zh_hant"] for r in pairs}
        if len(values) != len(pairs):
            raise ValueError("翻譯鍵重複")
    else:
        pairs = read_tsv(path, FIELDS)
        values = {r["message_id"]: r["zh_hant"] for r in pairs}
        if len(values) != len(pairs):
            raise ValueError("目錄鍵重複")
    expected = {r["message_id"] for r in rows}
    if set(values) != expected:
        raise ValueError("help翻譯鍵有缺漏或孤兒")
    for row in rows:
        translated = values[row["message_id"]]
        if not translated.strip():
            raise ValueError(row["message_id"] + " 缺譯")
        original = unescape_text(row["source_en"])
        zh = unescape_text(translated)
        if PLACEHOLDER.findall(original) != PLACEHOLDER.findall(zh):
            raise ValueError(row["message_id"] + " 變數占位符不符")
        if CONTROLS.findall(original) != CONTROLS.findall(zh):
            raise ValueError(row["message_id"] + " 控制碼不符")
        row["zh_hant"] = translated
    return rows


def render(rows):
    return "\t".join(FIELDS) + "\n" + "".join("\t".join(row[field] for field in FIELDS) + "\n" for row in rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--translations", type=Path, help="僅建立時使用的本機雙欄譯文草稿")
    args = p.parse_args()
    rows = source_rows(args.game)
    if rows is None:
        return 77
    rows = translations(rows, args.translations or args.catalog, bool(args.translations))
    content = render(rows)
    if args.translations:
        if not args.catalog.parent.is_dir():
            raise ValueError("輸出目錄不存在")
        args.catalog.write_text(content, encoding="utf-8")
    elif args.catalog.read_text(encoding="utf-8") != content:
        raise ValueError("TSV與固定原版來源或欄位不符")
    print(f"驗證通過：{len(rows)} 則help原文／譯文；只確認檔案來源，未驗畫面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
