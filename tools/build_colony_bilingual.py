#!/usr/bin/env python3
"""由唯讀 DOS ZIP 的 COLONY.TXT 建立／驗證分欄殖民地名稱雙語草稿。"""

import argparse
import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path

from build_help_bilingual import encoded_lines, read_tsv


ARCHIVE_NAME = "Sid Meier's Colonization (1994).zip"
ARCHIVE_SHA256 = "8aa93f219a6166712933bc60e402fe78024df1de821605c3036e1ae14e619867"
SOURCE_MEMBER = "SMColoni/COLONIZE/COLONY.TXT"
SOURCE_MEMBER_SHA256 = "2996f8a9d53a7f7a93e4a238bfd2ba727c4cf5cdabc334c4059c6860c9e4ae36"
NATIONS = ("ENGLISH", "FRENCH", "SPANISH", "DUTCH")
EXPECTED_COUNTS = {"ENGLISH": 36, "FRENCH": 66, "SPANISH": 39, "DUTCH": 32}
FIELDS = [
    "message_id", "source_archive", "source_archive_sha256", "source_member",
    "source_member_sha256", "nation", "section_offset", "text_offset", "text_byte_length",
    "source_bytes_sha256", "source_record", "source_name", "source_year", "zh_hant",
    "status", "notes",
]
NOTES = "殖民地預設名稱顯示草稿；罕見歷史地名待術語審查，原始名稱與年份只作來源，不是執行期鍵或畫面驗證"
RECORD = re.compile(r"(?P<name>[^,\r\n]+?)(?:,(?P<year>[0-9]{4}))?$")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_record(raw):
    if any(byte >= 0x80 for byte in raw):
        raise ValueError("COLONY.TXT含未確認非ASCII位元組")
    try:
        text = raw.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("COLONY.TXT名稱不是ASCII") from error
    matched = RECORD.fullmatch(text)
    if matched is None:
        raise ValueError("COLONY.TXT資料列不是名稱或名稱,四位年份")
    name, year = matched.group("name"), matched.group("year") or ""
    if not name or len(name) > 23:
        raise ValueError("COLONY.TXT原始名稱長度不符")
    return text, name, year


def source_rows(
    archive,
    expected_archive_sha=ARCHIVE_SHA256,
    expected_member_sha=SOURCE_MEMBER_SHA256,
    expected_counts=EXPECTED_COUNTS,
):
    if not archive.is_file():
        print("SKIP：缺少合法原版封存檔：" + ARCHIVE_NAME)
        return None
    archive_sha = digest_file(archive)
    if archive_sha != expected_archive_sha:
        raise ValueError("原版封存檔SHA-256不符")
    with zipfile.ZipFile(archive) as source:
        members = [info for info in source.infolist() if info.filename == SOURCE_MEMBER]
        if len(members) != 1:
            raise ValueError("COLONY來源成員不存在或不唯一")
        data = source.read(members[0])
    member_sha = digest(data)
    if member_sha != expected_member_sha:
        raise ValueError("COLONY來源成員SHA-256不符")
    lines, offsets = encoded_lines(data)
    section = None
    section_offsets = {}
    indices = Counter()
    rows = []
    for line, offset in zip(lines, offsets):
        raw = line.rstrip(b"\r\n")
        if not raw or raw.startswith(b";"):
            continue
        if raw.startswith(b"@"):
            marker = raw[1:].decode("ascii", errors="strict")
            if marker == "STOP":
                if section is None:
                    raise ValueError("COLONY.TXT有沒有開始章節的@STOP")
                section = None
            elif marker in NATIONS:
                if section is not None or marker in section_offsets:
                    raise ValueError("COLONY.TXT章節重複或巢狀")
                section = marker
                section_offsets[section] = offset
            else:
                raise ValueError("COLONY.TXT含未知章節：" + marker)
            continue
        if section is None:
            raise ValueError("COLONY.TXT名稱不在國籍章節中")
        record, name, year = parse_record(raw)
        index = indices[section]
        indices[section] += 1
        rows.append({
            "message_id": f"COLONY.TXT:@{section}:{index:02d}",
            "source_archive": ARCHIVE_NAME,
            "source_archive_sha256": archive_sha,
            "source_member": SOURCE_MEMBER,
            "source_member_sha256": member_sha,
            "nation": section,
            "section_offset": f"0x{section_offsets[section]:08X}",
            "text_offset": f"0x{offset:08X}",
            "text_byte_length": str(len(raw)),
            "source_bytes_sha256": digest(raw),
            "source_record": record,
            "source_name": name,
            "source_year": year,
            "status": "draft",
            "notes": NOTES,
        })
    if section is not None or set(section_offsets) != set(NATIONS) or dict(indices) != dict(expected_counts):
        raise ValueError("COLONY.TXT國籍章節或名稱筆數不符")
    return rows


def expected_display(chinese_name, source_name, source_year):
    if source_year:
        return f"{chinese_name}（{source_name}，{source_year}）"
    return f"{chinese_name}（{source_name}）"


def has_cjk(text):
    return any("\u3400" <= char <= "\u4dbf" or "\u4e00" <= char <= "\u9fff" for char in text)


def translations(rows, path, build):
    pairs = read_tsv(path, ["message_id", "zh_hant"] if build else FIELDS)
    values = {row["message_id"]: row["zh_hant"] for row in pairs}
    if len(values) != len(pairs):
        raise ValueError("殖民地翻譯鍵重複")
    expected = {row["message_id"] for row in rows}
    if set(values) != expected:
        raise ValueError("殖民地翻譯鍵有缺漏或孤兒")
    for row in rows:
        translated = values[row["message_id"]]
        suffix = expected_display("", row["source_name"], row["source_year"])
        if not translated.endswith(suffix):
            raise ValueError(row["message_id"] + " 不符中文名稱（原名，年份）格式")
        chinese_name = translated[:-len(suffix)]
        if not chinese_name or not has_cjk(chinese_name):
            raise ValueError(row["message_id"] + " 缺少中文名稱")
        row["zh_hant"] = translated
    return rows


def render(rows):
    return "\t".join(FIELDS) + "\n" + "".join(
        "\t".join(row[field] for field in FIELDS) + "\n" for row in rows
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--translations", type=Path, help="僅建立時使用的本機雙欄譯文草稿")
    args = parser.parse_args()
    rows = source_rows(args.archive)
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
    print(f"驗證通過：{len(rows)} 筆殖民地預設名稱原文／譯文；只確認來源與格式，未驗畫面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
