#!/usr/bin/env python3
"""規格017：在容器 Xvfb 中重播第一張卡片的真 TSV 缺譯與游標反向條件。"""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


INPUT_SHA = "51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc"
TITLE = "NAMES.TXT:0x00000C0C"
SUBTITLE = "LABELS.TXT:0x000008A9"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("/out"))
    parser.add_argument("--repo", type=Path, default=Path("/repo"))
    parser.add_argument("--game", type=Path, default=Path("/game"))
    parser.add_argument("--bin", type=Path, default=Path("/app/window"))
    parser.add_argument("--only", choices=("zh", "control", "missing-title", "duplicate-title",
                                            "hover", "hover-control"))
    args = parser.parse_args()
    if args.out.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄擁有者不符")
    source = args.out / "goal059-ebiten.inputs.json"
    if hashlib.sha256(source.read_bytes()).hexdigest() != INPUT_SHA:
        raise ValueError("正常玩家九筆輸入指紋不符")
    inputs = json.loads(source.read_text())
    if len(inputs["inputs"]) != 9 or inputs["inputs"][-1]["step"] != 29800000:
        raise ValueError("輸入序列不是已驗證的真視窗路徑")
    with (args.repo / "text/draft.zh-Hant.tsv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        columns, rows = reader.fieldnames, list(reader)
    if sum(row["candidate_id"] == TITLE for row in rows) != 1 or sum(row["candidate_id"] == SUBTITLE for row in rows) != 1:
        raise ValueError("原始 TSV 卡片鍵不唯一")
    with tempfile.TemporaryDirectory(prefix="goal079-") as temp:
        root = Path(temp)
        missing = root / "missing-title.tsv"
        with missing.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(row for row in rows if row["candidate_id"] != TITLE)
        duplicate = root / "duplicate-title.tsv"
        with duplicate.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows + [next(row for row in rows if row["candidate_id"] == TITLE)])
        ordinary = root / "ordinary.inputs.json"
        hover = root / "hover.inputs.json"
        ordinary.write_text(json.dumps({"inputs": inputs["inputs"], "end": 40000000}))
        hover_inputs = inputs["inputs"] + [
            {"step": 32000000, "kind": "move", "x": 160, "y": 48, "button": 0},
            {"step": 36000000, "kind": "move", "x": 16, "y": 16, "button": 0},
        ]
        hover.write_text(json.dumps({"inputs": hover_inputs, "end": 40000000}))
        variants = (
            ("zh", ordinary, args.repo / "text/draft.zh-Hant.tsv", False),
            ("control", ordinary, args.repo / "text/draft.zh-Hant.tsv", True),
            ("missing-title", ordinary, missing, False),
            ("duplicate-title", ordinary, duplicate, False),
            ("hover", hover, args.repo / "text/draft.zh-Hant.tsv", False),
            ("hover-control", hover, args.repo / "text/draft.zh-Hant.tsv", True),
        )
        for name, replay, catalog, control in variants:
            if args.only and name != args.only:
                continue
            prefix = args.out / ("goal079-replay-" + name)
            if Path(str(prefix) + ".json").exists():
                raise ValueError("收據已存在，不覆寫：" + str(prefix))
            command = [str(args.bin), "--window", "--all-menu", "--root", str(args.game),
                       "--catalog", str(catalog), "--font-dir", str(args.out / "goal057-fonts"),
                       "--out", str(prefix), "--replay-inputs", str(replay),
                       "--window-steps", "40000000"]
            if control:
                command.append("--control")
            result = subprocess.run(command, text=True, capture_output=True, timeout=120)
            Path(str(prefix) + ".log").write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f"{name} 重播失敗，見 {prefix}.log")
            print(name, json.loads(Path(str(prefix) + ".json").read_text())["state"]["steps"], flush=True)


if __name__ == "__main__":
    main()
