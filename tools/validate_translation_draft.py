#!/usr/bin/env python3
"""驗證譯稿候選來源；不建立正式執行期識別，不修改原版資料。

用法：python3 tools/validate_translation_draft.py --game /game
原版缺失時明確 SKIP，退出碼 77；格式或來源不符時退出 1。
來源片段不含 CR/LF，但驗證片段必須是原始行，且原檔 SHA-256 包含
完整 CRLF 與控制碼。不將字元索引當成位元組位移，不改寫來源編碼。
"""

import argparse
from collections import Counter
import csv
import hashlib
import io
import pathlib
import re
import sys


FIELDS = [
    "candidate_id", "source_file", "source_sha256", "byte_offset",
    "source_bytes_sha256", "source_byte_length", "zh_hant", "status", "notes",
]
HASH = re.compile(r"[0-9a-f]{64}\Z")
OFFSET = re.compile(r"0x[0-9A-F]{8}\Z")
# `%STRING0` 等為一般執行期變數；`%Fs` 是原版用於名稱組合的
# 特殊拼接占位符。兩者都屬顯示模板，譯文不得把其中任一部分吞掉。
PLACEHOLDER = re.compile(r"%(?:[A-Z][a-z]|[A-Z]+[0-9]*(?:\$)?)")
CONTROLS = re.compile(r"[{}^~_#]")
HOTKEY = re.compile(r"~([\x21-\x7e])")


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def read_catalog(path):
    raw = path.read_bytes()
    require(not raw.startswith(b"\xef\xbb\xbf"), "TSV 不接受 BOM")
    text = raw.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t", strict=True)
    require(reader.fieldnames == FIELDS, "欄位順序或數量錯誤")
    rows = list(reader)
    require(bool(rows), "草稿不可為空")
    seen = set()
    for number, row in enumerate(rows, 2):
        prefix = f"第 {number} 列："
        require(None not in row and all(value is not None for value in row.values()), prefix + "欄數不符")
        require(all("\n" not in value and "\r" not in value and "\t" not in value and "\x00" not in value for value in row.values()), prefix + "欄位含不允許的控制字元")
        require(re.fullmatch(r"[A-Z0-9_-]+\.TXT", row["source_file"]) or
                (row["source_file"] == "VICEROY.EXE" and row["candidate_id"] == "VICEROY.EXE:0x0001FA8E"), prefix + "來源檔名不合法")
        if row["source_file"] == "VICEROY.EXE":
            require(row["source_sha256"] == "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3" and
                    row["byte_offset"] == "0x0001FA8E" and row["source_byte_length"] == "7" and
                    row["source_bytes_sha256"] == "9251e2d6e3d0ccd4ce35aa27a82a36251ad36af2cb17b229c34a3daa2f0cdaa7",
                    prefix + "槽位空欄來源定位不符")
        require(HASH.fullmatch(row["source_sha256"]) and HASH.fullmatch(row["source_bytes_sha256"]), prefix + "SHA-256 格式錯誤")
        require(OFFSET.fullmatch(row["byte_offset"]), prefix + "位移格式錯誤")
        require(re.fullmatch(r"[1-9][0-9]*", row["source_byte_length"]), prefix + "長度不是正整數")
        candidate = row["source_file"] + ":" + row["byte_offset"]
        require(row["candidate_id"] == candidate, prefix + "候選名稱與來源不符")
        require(candidate not in seen, prefix + "候選重複")
        seen.add(candidate)
        require(row["status"] == "draft", prefix + "此目錄只接受 draft")
        require(bool(row["zh_hant"].strip()), prefix + "譯文不可為空")
        require(bool(row["notes"].strip()), prefix + "缺少來源限制註記")
    return rows


def validate_sources(rows, game):
    cache = {}
    for row in rows:
        filename = row["source_file"]
        if filename not in cache:
            cache[filename] = (game / filename).read_bytes()
        data = cache[filename]
        prefix = row["candidate_id"] + "："
        require(hashlib.sha256(data).hexdigest() == row["source_sha256"], prefix + "原版檔案 SHA-256 不符")
        start = int(row["byte_offset"], 16)
        end = start + int(row["source_byte_length"])
        require(0 <= start < end <= len(data), prefix + "來源範圍越界")
        if filename == "VICEROY.EXE":
            # READY 規格038只開放這一個已驗零結尾片段，其他來源仍使用 CRLF 完整行。
            require(row["candidate_id"] == "VICEROY.EXE:0x0001FA8E" and start == 129678 and
                    end == 129685 and data[start - 1:start] == b"\x00" and
                    data[end:end + 1] == b"\x00" and data[start:end] == b"(EMPTY)", prefix + "槽位空欄邊界不符")
        else:
            require(start == 0 or data[start - 2:start] == b"\r\n", prefix + "片段不在原始 CRLF 行首")
            require(data[end:end + 2] == b"\r\n", prefix + "片段未完整涵蓋原始行")
        source = data[start:end]
        require(b"\r" not in source and b"\n" not in source, prefix + "片段不應包含換行")
        require(hashlib.sha256(source).hexdigest() == row["source_bytes_sha256"], prefix + "來源片段 SHA-256 不符")
        original = source.decode("ascii", errors="strict")
        translated = row["zh_hant"]
        require(re.match(r" *", original).group() == re.match(r" *", translated).group(), prefix + "前置縮排不符")
        # 具名變數可因中文語序調換位置，但種類與出現次數必須完全相同。
        require(Counter(PLACEHOLDER.findall(original)) == Counter(PLACEHOLDER.findall(translated)),
                prefix + "變數占位符不符")
        require(CONTROLS.findall(original) == CONTROLS.findall(translated), prefix + "大括號或控制符號不符")
        require(HOTKEY.findall(original) == HOTKEY.findall(translated), prefix + "熱鍵 ASCII 標記不符")
    return len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=pathlib.Path, required=True, help="原版 COLONIZE 目錄（唯讀）")
    parser.add_argument("--catalog", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1] / "text/draft.zh-Hant.tsv")
    args = parser.parse_args(argv)
    try:
        rows = read_catalog(args.catalog)
        missing = sorted({row["source_file"] for row in rows if not (args.game / row["source_file"]).is_file()})
        if missing:
            print("SKIP：缺少合法原版輸入：" + "、".join(missing))
            return 77
        count = validate_sources(rows, args.game)
    except (OSError, UnicodeError, csv.Error, Invalid) as exc:
        print(f"驗證失敗：{exc}", file=sys.stderr)
        return 1
    print(f"驗證通過：{count} 筆草稿；來源指紋、位元組範圍、片段邊界、變數及控制符號一致。")
    print("此結果不代表畫面事件、字型覆蓋或術語已定案；candidate_id 不是正式執行期識別。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
