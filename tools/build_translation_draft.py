#!/usr/bin/env python3
"""由受限的單行譯文提案建立既有主譯稿；不修改原版或建立執行期鍵。"""

import argparse
import csv
import hashlib
import io
import re
from pathlib import Path

from validate_translation_draft import FIELDS, HASH, OFFSET, Invalid, read_catalog, validate_sources


PROPOSAL_FIELDS = ["source_file", "byte_offset", "zh_hant", "notes"]
FILENAME = re.compile(r"[A-Z0-9_-]+\.TXT\Z")


def require(condition, message):
    if not condition:
        raise Invalid(message)


def read_proposals(path):
    raw = path.read_bytes()
    require(not raw.startswith(b"\xef\xbb\xbf"), "提案 TSV 不接受 BOM")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="strict")), delimiter="\t", strict=True)
    require(reader.fieldnames == PROPOSAL_FIELDS, "提案欄位順序或數量錯誤")
    rows = list(reader)
    require(bool(rows), "提案不可為空")
    seen = set()
    for number, row in enumerate(rows, 2):
        prefix = f"提案第 {number} 列："
        require(None not in row and all(value is not None for value in row.values()), prefix + "欄數不符")
        require(all(not any(char in value for char in "\r\n\t\x00") for value in row.values()), prefix + "欄位含不允許的控制字元")
        require(FILENAME.fullmatch(row["source_file"]) is not None, prefix + "來源檔名不合法")
        require(OFFSET.fullmatch(row["byte_offset"]) is not None, prefix + "位移格式錯誤")
        require(bool(row["zh_hant"].strip()), prefix + "譯文不可為空")
        require(bool(row["notes"].strip()), prefix + "缺少來源限制註記")
        candidate = row["source_file"] + ":" + row["byte_offset"]
        require(candidate not in seen, prefix + "候選重複")
        seen.add(candidate)
    return rows


def line_at(data, offset, candidate):
    require(0 <= offset < len(data), candidate + "：來源位移越界")
    require(offset == 0 or data[offset - 2:offset] == b"\r\n", candidate + "：候選不在原始 CRLF 行首")
    end = data.find(b"\r\n", offset)
    require(end != -1, candidate + "：候選沒有 CRLF 行尾")
    source = data[offset:end]
    require(bool(source), candidate + "：候選不可為空行")
    return source


def build_rows(game, catalog_path, proposal_path):
    existing = read_catalog(catalog_path)
    existing_ids = {row["candidate_id"] for row in existing}
    cache = {}
    additions = []
    for proposal in read_proposals(proposal_path):
        filename = proposal["source_file"]
        path = game / filename
        require(path.is_file(), filename + "：缺少合法原版輸入")
        data = cache.setdefault(filename, path.read_bytes())
        candidate = filename + ":" + proposal["byte_offset"]
        require(candidate not in existing_ids, candidate + "：既有目錄已含此候選")
        offset = int(proposal["byte_offset"], 16)
        source = line_at(data, offset, candidate)
        require(not source.lstrip().startswith((b";", b"@")), candidate + "：註解或指令不可作譯稿候選")
        require(b"," not in source, candidate + "：逗號複合資料不可套用單行候選模型")
        source.decode("ascii", errors="strict")
        additions.append({
            "candidate_id": candidate,
            "source_file": filename,
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "byte_offset": proposal["byte_offset"],
            "source_bytes_sha256": hashlib.sha256(source).hexdigest(),
            "source_byte_length": str(len(source)),
            "zh_hant": proposal["zh_hant"],
            "status": "draft",
            "notes": proposal["notes"],
        })
    rows = existing + additions
    validate_sources(rows, game)
    return rows


def render(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        rows = build_rows(args.game, args.catalog, args.translations)
        require(args.output.parent.is_dir(), "輸出目錄不存在")
        args.output.write_text(render(rows), encoding="utf-8", newline="")
    except (OSError, UnicodeError, csv.Error, Invalid) as error:
        raise SystemExit("建立失敗：" + str(error))
    print(f"建立通過：原有 {len(rows) - len(read_proposals(args.translations))} 筆，加上 {len(read_proposals(args.translations))} 筆，合計 {len(rows)} 筆草稿；未驗畫面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
