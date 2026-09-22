#!/usr/bin/env python3
"""由唯讀 DOS ZIP 的 README.TXT 建立／驗證玩家說明雙語草稿。"""

import argparse
import hashlib
import re
import zipfile
from pathlib import Path

from build_help_bilingual import escape_text, read_tsv, unescape_text


ARCHIVE_NAME = "Sid Meier's Colonization (1994).zip"
ARCHIVE_SHA256 = "8aa93f219a6166712933bc60e402fe78024df1de821605c3036e1ae14e619867"
SOURCE_MEMBER = "SMColoni/COLONIZE/README.TXT"
SOURCE_MEMBER_SHA256 = "d78a219bfd041e3d4f3327d6b012dc433fd3734472c68cbace0490b9e46ac19e"
SPANS = [
    ("README.TXT:VERSION_INTRO", 0x0000, 0x0180),
    ("README.TXT:VERSION_3_FIXES", 0x0180, 0x0712),
    ("README.TXT:MAP_EDITOR", 0x0B76, 0x0E7E),
    ("README.TXT:CHEAT_OVERVIEW", 0x0E7E, 0x10A0),
    ("README.TXT:CHEAT_MAIN_MAP", 0x10A0, 0x176B),
    ("README.TXT:CHEAT_COLONY", 0x176B, 0x19F8),
    ("README.TXT:CHEAT_EUROPE", 0x19F8, 0x1A79),
]
FIELDS = [
    "message_id", "source_archive", "source_archive_sha256", "source_member",
    "source_member_sha256", "span_offset", "span_byte_length", "source_bytes_sha256",
    "source_en", "zh_hant", "status", "notes",
]
NOTES = "README玩家補充說明草稿；檔案來源已確認，執行事件與中文安全矩形尚未驗證"
KEY_LITERAL = re.compile(
    r"Alt-[WIN]|[Ss]hift-(?:F[1-7]|D)|(?m:^(?:T|S|\$|%|\^|!|Space|\[|\]) =)"
)
SYMBOL_LITERAL = re.compile(r"[$%^!\[\]]")
TAB_CONTROL = re.compile(r"\t")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_spans(spans):
    previous_end = 0
    seen = set()
    for message_id, start, end in spans:
        if message_id in seen:
            raise ValueError("README訊息鍵重複")
        if not isinstance(start, int) or not isinstance(end, int) or start < previous_end or end <= start:
            raise ValueError("README位元組範圍無效、重疊或未排序")
        seen.add(message_id)
        previous_end = end


def verify_crlf(data):
    if b"\r\n" not in data or data.replace(b"\r\n", b"").find(b"\n") >= 0:
        raise ValueError("README來源必須以CRLF換行")


def source_rows(archive, expected_archive_sha=ARCHIVE_SHA256, expected_member_sha=SOURCE_MEMBER_SHA256):
    validate_spans(SPANS)
    if not archive.is_file():
        print("SKIP：缺少合法原版封存檔：" + ARCHIVE_NAME)
        return None
    archive_sha = digest_file(archive)
    if archive_sha != expected_archive_sha:
        raise ValueError("原版封存檔SHA-256不符")
    with zipfile.ZipFile(archive) as source:
        members = [info for info in source.infolist() if info.filename == SOURCE_MEMBER]
        if len(members) != 1:
            raise ValueError("README來源成員不存在或不唯一")
        data = source.read(members[0])
    if digest(data) != expected_member_sha:
        raise ValueError("README來源成員SHA-256不符")
    verify_crlf(data)
    rows = []
    for message_id, start, end in SPANS:
        if end > len(data):
            raise ValueError(message_id + " 位元組範圍越界")
        raw = data[start:end]
        if not raw or any(byte >= 0x80 for byte in raw):
            raise ValueError(message_id + " 含空白或未確認非ASCII來源")
        trimmed = raw.rstrip(b"\r\n")
        if not trimmed:
            raise ValueError(message_id + " 沒有可翻譯文字")
        original = trimmed.decode("ascii", errors="strict").replace("\r\n", "\n")
        rows.append({
            "message_id": message_id,
            "source_archive": ARCHIVE_NAME,
            "source_archive_sha256": archive_sha,
            "source_member": SOURCE_MEMBER,
            "source_member_sha256": digest(data),
            "span_offset": f"0x{start:08X}",
            "span_byte_length": str(len(raw)),
            "source_bytes_sha256": digest(raw),
            "source_en": escape_text(original),
            "status": "draft",
            "notes": NOTES,
        })
    return rows


def translations(rows, path, build):
    pairs = read_tsv(path, ["message_id", "zh_hant"] if build else FIELDS)
    values = {row["message_id"]: row["zh_hant"] for row in pairs}
    if len(values) != len(pairs):
        raise ValueError("README翻譯鍵重複")
    expected = {row["message_id"] for row in rows}
    if set(values) != expected:
        raise ValueError("README翻譯鍵有缺漏或孤兒")
    for row in rows:
        translated = values[row["message_id"]]
        if not translated.strip():
            raise ValueError(row["message_id"] + " 缺譯")
        original = unescape_text(row["source_en"])
        zh_hant = unescape_text(translated)
        if TAB_CONTROL.findall(original) != TAB_CONTROL.findall(zh_hant):
            raise ValueError(row["message_id"] + " Tab格式不符")
        if KEY_LITERAL.findall(original) != KEY_LITERAL.findall(zh_hant):
            raise ValueError(row["message_id"] + " 操作按鍵或符號不符")
        if SYMBOL_LITERAL.findall(original) != SYMBOL_LITERAL.findall(zh_hant):
            raise ValueError(row["message_id"] + " 操作符號不符")
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
    print(f"驗證通過：{len(rows)} 則README玩家補充說明原文／譯文；只確認檔案來源，未驗畫面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
