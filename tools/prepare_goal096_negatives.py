#!/usr/bin/env python3
"""從真視窗收據產生姓名提示的本機失敗回退負例。"""

import argparse
import csv
import hashlib
import json
import os
import shutil
from pathlib import Path


def need(ok, message):
    if not ok:
        raise ValueError(message)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--inputs", type=Path, required=True)
parser.add_argument("--catalog", type=Path, required=True)
parser.add_argument("--fonts", type=Path, required=True)
parser.add_argument("--game", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
need(args.out.is_dir() and args.out.stat().st_uid == os.getuid() and
     not any(args.out.iterdir()), "負例輸出目錄不存在、非本人或非空")

receipt = json.loads(args.inputs.read_bytes())
need(receipt["end"] == 90_000_000 and
     [(e["kind"], e.get("text")) for e in receipt["inputs"]
      if e["kind"] in ("enter", "text", "backspace")] ==
     [("enter", None), ("text", "x"), ("backspace", None), ("enter", None)],
     "真視窗輸入收據不符")


def write_input(name, end, extra=()):
    inputs = [e for e in receipt["inputs"] if e["step"] < end]
    inputs.extend(extra)
    inputs.sort(key=lambda item: item["step"])
    path = args.out / f"{name}.inputs.json"
    path.write_text(json.dumps({"inputs": inputs, "end": end}, ensure_ascii=False,
                               indent=2) + "\n")
    return path


idle = write_input("idle", 55_000_000)
cursor = write_input("cursor", 58_000_000,
                     ({"step": 56_000_000, "kind": "move", "x": 159, "y": 91,
                       "button": 0},
                      {"step": 57_000_000, "kind": "move", "x": 16, "y": 16,
                       "button": 0}))

lines = args.catalog.read_text().splitlines(keepends=True)
key = "GAME.TXT:0x00000A7A\t"
target = [line for line in lines if line.startswith(key)]
need(len(target) == 1, "主譯稿姓名提示必須恰有一筆")
(args.out / "missing.tsv").write_text("".join(line for line in lines
                                              if not line.startswith(key)))
(args.out / "duplicate.tsv").write_text("".join(lines) + target[0])
for name in ("missing", "duplicate"):
    with (args.out / f"{name}.tsv").open(newline="") as handle:
        list(csv.DictReader(handle, delimiter="\t"))

bad_font = args.out / "wrong-size-fonts"
shutil.copytree(args.fonts, bad_font)
mask_path = bad_font / "GAME.TXT-0x00000A7A.json"
mask = json.loads(mask_path.read_bytes())
need(mask["font_size"] == 38 and (mask["width"], mask["height"]) == (328, 35),
     "正式字模幾何不符")
mask["font_size"] = 37
mask_path.write_text(json.dumps(mask, ensure_ascii=False) + "\n")

bad_game = args.out / "wrong-game"
bad_game.mkdir()
for source in args.game.iterdir():
    if source.name == "GAME.TXT":
        raw = bytearray(source.read_bytes())
        need(raw[0xA7C] == ord("P"), "原版提示位移不符")
        raw[0xA7C] ^= 1
        (bad_game / source.name).write_bytes(raw)
    else:
        (bad_game / source.name).symlink_to(Path("/game") / source.name,
                                             target_is_directory=source.is_dir())

result = {"inputs_sha256": hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
          "idle_sha256": hashlib.sha256(idle.read_bytes()).hexdigest(),
          "cursor_sha256": hashlib.sha256(cursor.read_bytes()).hexdigest(),
          "wrong_game_sha256": hashlib.sha256((bad_game / "GAME.TXT").read_bytes()).hexdigest(),
          "cases": ["missing-translation", "duplicate-translation", "missing-mask",
                    "wrong-font-size", "wrong-original-version", "cursor-occlusion"]}
(args.out / "manifest.json").write_text(json.dumps(result, ensure_ascii=False,
                                                   indent=2) + "\n")
print("姓名提示六個本機回退負例已備妥")
