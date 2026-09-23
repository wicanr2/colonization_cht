#!/usr/bin/env python3
"""從固定真譯稿與字模建立難度標題逐欄失敗反例；只寫 workplace。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


CATALOG_SHA = "14b2cc51df1d42ccd938d8fab334c0b90b1cf63314746df19d80449c3865f3f1"
FIELDS = {
    "choose": "LABELS.TXT:0x00000888",
    "level": "LABELS.TXT:0x00000890",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--second-inputs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.output_dir.is_dir() or args.output_dir.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    raw = args.catalog.read_bytes()
    if sha(raw) != CATALOG_SHA:
        raise ValueError("正式 TSV 版本不符")
    lines = raw.splitlines(keepends=True)
    replay = json.loads(args.inputs.read_text())
    if replay["end"] != 100_000_000 or not replay["inputs"] or any(
            event["step"] >= 45_000_000 for event in replay["inputs"]):
        raise ValueError("真視窗輸入不適用45M反例")
    replay["end"] = 45_000_000
    trimmed = args.output_dir / "replay-45m.inputs.json"
    trimmed_bytes = (json.dumps(replay, ensure_ascii=False, indent=2) + "\n").encode()
    if trimmed.exists() and trimmed.read_bytes() != trimmed_bytes:
        raise ValueError("既有45M輸入不一致")
    if not trimmed.exists():
        trimmed.write_bytes(trimmed_bytes)
    second = json.loads(args.second_inputs.read_text())
    if second["end"] != 100_000_000 or len(second["inputs"]) != 16:
        raise ValueError("第二張卡片真視窗輸入版本不符")
    second["inputs"] = [event for event in second["inputs"] if event["step"] < 40_000_000]
    second["end"] = 40_000_000
    second_path = args.output_dir / "replay-second-40m.inputs.json"
    second_bytes = (json.dumps(second, ensure_ascii=False, indent=2) + "\n").encode()
    if second_path.exists() and second_path.read_bytes() != second_bytes:
        raise ValueError("既有第二張卡片40M輸入不一致")
    if not second_path.exists():
        second_path.write_bytes(second_bytes)
    for label, key in FIELDS.items():
        found = [i for i, line in enumerate(lines) if line.startswith((key + "\t").encode())]
        if len(found) != 1:
            raise ValueError("來源鍵不唯一：" + key)
        at = found[0]
        for action, variant in (("missing", lines[:at] + lines[at + 1:]),
                                ("duplicate", lines[:at + 1] + [lines[at]] + lines[at + 1:])):
            target = args.output_dir / f"catalog-{action}-{label}.tsv"
            content = b"".join(variant)
            if target.exists() and target.read_bytes() != content:
                raise ValueError("既有 TSV 反例不一致：" + str(target))
            if not target.exists():
                target.write_bytes(content)
        mask_name = key.replace(":", "-") + ".json"
        for action in ("missing-mask", "wrong-size"):
            target = args.output_dir / f"fonts-{action}-{label}"
            if target.exists():
                continue
            shutil.copytree(args.font_dir, target)
            mask = target / mask_name
            if action == "missing-mask":
                mask.unlink()
            else:
                payload = json.loads(mask.read_text())
                payload["font_size"] += 1
                mask.write_text(json.dumps(payload, ensure_ascii=False) + "\n")
    print("goal086-variants-ready")


if __name__ == "__main__":
    main()
