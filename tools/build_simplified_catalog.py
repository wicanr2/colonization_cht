#!/usr/bin/env python3
"""以固定OpenCC版本產生簡體遊戲譯稿起點，不宣稱語言或畫面驗收。"""

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

from language_catalog import BaseCatalog, FIELDS, ROOT, load_translation, require, sha, write_tsv


WHEEL_SHA256 = "64994c68796d93cdba42f37e0c073fb8ed6f9d6707232be0ba84f24dc5a36bbb"
WHEEL_URL = "https://files.pythonhosted.org/packages/bb/07/4eef5a5c43221470af3a9e12fce024c5b9451618c4307c7980c2d6e298b3/OpenCC-1.1.9-cp311-cp311-manylinux2014_x86_64.whl"
CONFIG = "tw2sp.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file(), "請在Docker執行")
    require(sys.version_info[:2] == (3, 11), "固定wheel需Python3.11")
    wheel = args.wheel.read_bytes()
    require(sha(wheel) == WHEEL_SHA256, "OpenCC wheel指紋不同")
    output, report = args.output.resolve(), args.report.resolve()
    require(output.name == "game.zh-Hans.tsv" and
            (output.parent == ROOT / "text" or output.is_relative_to(ROOT / "workplace")), "譯稿輸出位置不同")
    require(report.is_relative_to(ROOT / "workplace"), "轉換收據只存workplace")
    for path in (output, report):
        require(not path.exists() and path.parent.is_dir() and path.parent.stat().st_uid == os.getuid(),
                "輸出必須是目前使用者擁有的新檔")
    base = BaseCatalog()
    with tempfile.TemporaryDirectory(prefix="opencc-1.1.9-", dir=report.parent) as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(args.wheel) as archive:
            require(sum(item.file_size for item in archive.infolist()) < 32 * 1024 * 1024, "wheel解壓過大")
            for item in archive.infolist():
                require((root / item.filename).resolve().is_relative_to(root), "wheel路徑不安全")
            archive.extractall(root)
        sys.path.insert(0, str(root))
        opencc = importlib.import_module("opencc")
        require(Path(opencc.__file__).resolve().is_relative_to(root), "OpenCC來源不同")
        converter = opencc.OpenCC(CONFIG)
        rows = []
        for entry in base.entries.values():
            text = converter.convert(entry["text"])
            notes = "OpenCC 1.1.9 tw2sp轉換起稿；尚未完成逐句人工校對。"
            if not text:
                notes = "沿基準省略英文冠詞；不加入原版畫面沒有的文字。"
            rows.append({"locale": "zh-Hans", **{key: entry[key] for key in ("catalog", "key", "base_sha256")},
                         "text": text, "status": "translated" if text else "omitted", "notes": notes})
        data = write_tsv(FIELDS, rows)
        entries, missing = load_translation(base, data, "zh-Hans")
        require(not missing, "簡體起稿不完整")
        hashes = {str(path.relative_to(root)): sha(path.read_bytes()) for path in sorted(root.rglob("*"))
                  if path.is_file() and path.suffix != ".pyc"}
        receipt = {"kind": "simplified-text-conversion-not-language-acceptance", "wheel_url": WHEEL_URL,
                   "wheel_sha256": WHEEL_SHA256, "config": CONFIG, "tool_files_sha256": hashes,
                   "source_binding_sha256": base.registry["source_binding_sha256"], "rows": len(entries),
                   "output_sha256": sha(data), "changed_display_rows": sum(
                       row["text"] != entry["text"] for row, entry in zip(rows, base.entries.values())),
                   "limitations": ["機械轉換不證明逐句翻譯、字形、排版或正式語言切換。"]}
    output.write_bytes(data)
    report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    require(output.stat().st_uid == report.stat().st_uid == os.getuid(), "輸出擁有者不同")
    print(json.dumps({key: value for key, value in receipt.items() if key != "tool_files_sha256"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
