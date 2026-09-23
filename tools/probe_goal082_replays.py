#!/usr/bin/env python3
"""以已記錄的真 Ebitengine 輸入，重播第二張卡片的譯文與游標反例。"""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


INPUT_SHA = "34d8ec6046830793b2e336ed41a638b533bb0782f5634263d0a1c338adda0f4b"
TITLE = "NAMES.TXT:0x00000C18"
SUBTITLE = "LABELS.TXT:0x000008B2"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--bin", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--only", choices=("zh", "control", "missing-title", "duplicate-title",
                                            "missing-subtitle", "duplicate-subtitle", "hover",
                                            "hover-control"))
    args = parser.parse_args()
    require(args.out.is_dir() and args.out.stat().st_uid == os.getuid() and
            args.font_dir.is_dir() and args.bin.is_file(), "執行檔、字模或輸出目錄不符")
    source = args.out / "goal082-window.inputs.json"
    require(hashlib.sha256(source.read_bytes()).hexdigest() == INPUT_SHA,
            "真視窗輸入指紋不符")
    inputs = json.loads(source.read_text())["inputs"]
    require(len(inputs) == 12 and inputs[-1]["step"] == 35200000 and
            inputs[-1]["kind"] == "move" and
            (inputs[-1]["x"], inputs[-1]["y"]) == (16, 16), "真視窗輸入尾端不符")
    catalog = args.repo / "text/draft.zh-Hant.tsv"
    with catalog.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        columns, rows = reader.fieldnames, list(reader)
    require(sum(row["candidate_id"] == TITLE for row in rows) == 1 and
            sum(row["candidate_id"] == SUBTITLE for row in rows) == 1,
            "原始第二張卡片 TSV 鍵不唯一")
    with tempfile.TemporaryDirectory(prefix="goal082-") as temporary:
        root = Path(temporary)
        catalogs = {"zh": catalog, "control": catalog, "hover": catalog,
                    "hover-control": catalog}
        for key, label in ((TITLE, "title"), (SUBTITLE, "subtitle")):
            for action in ("missing", "duplicate"):
                path = root / f"{action}-{label}.tsv"
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t",
                                            lineterminator="\n")
                    writer.writeheader()
                    if action == "missing":
                        writer.writerows(row for row in rows if row["candidate_id"] != key)
                    else:
                        writer.writerows(rows + [next(row for row in rows
                                                      if row["candidate_id"] == key)])
                catalogs[f"{action}-{label}"] = path
        ordinary = root / "ordinary.inputs.json"
        hover = root / "hover.inputs.json"
        ordinary.write_text(json.dumps({"inputs": inputs, "end": 40000000}))
        hover.write_text(json.dumps({"inputs": inputs + [
            {"step": 40000000, "kind": "move", "x": 265, "y": 55, "button": 0},
            {"step": 44000000, "kind": "move", "x": 16, "y": 16, "button": 0},
        ], "end": 48000000}))
        for name in ("zh", "control", "missing-title", "duplicate-title",
                     "missing-subtitle", "duplicate-subtitle", "hover", "hover-control"):
            if args.only and args.only != name:
                continue
            prefix = args.out / ("goal082-replay-" + name)
            require(not Path(str(prefix) + ".json").exists(), "收據已存在，不覆寫：" + name)
            command = [str(args.bin), "--window", "--all-menu", "--root", str(args.game),
                       "--catalog", str(catalogs[name]), "--font-dir", str(args.font_dir),
                       "--out", str(prefix), "--replay-inputs",
                       str(hover if name.startswith("hover") else ordinary),
                       "--window-steps", "48000000" if name.startswith("hover") else "40000000"]
            if name in ("control", "hover-control"):
                command.append("--control")
            result = subprocess.run(command, text=True, capture_output=True, timeout=120)
            Path(str(prefix) + ".log").write_text(result.stdout + result.stderr)
            require(result.returncode == 0, f"{name} 重播失敗；見 {prefix}.log")
            state = json.loads(Path(str(prefix) + ".json").read_text())["state"]
            print(name, state["steps"], flush=True)


if __name__ == "__main__":
    main()
