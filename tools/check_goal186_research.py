#!/usr/bin/env python3
"""在Docker內重驗真實SS盤點、完整像素定位與失敗守門；不驗收正式HD。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image

from locate_hd_assets import locate


ROOT = Path(__file__).resolve().parent.parent
SOURCE_HASHES = {
    "BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",
    "PHYS0.SS": "deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16",
    "ICONS.SS": "a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716",
    "TERRAIN.SS": "a6de9353f2240c214051820369abacf3bb82affbb4736a89c589886fb306f4b6",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def run(script, *args, success=True):
    result = subprocess.run([sys.executable, str(ROOT / "tools" / script), *map(str, args)],
                            text=True, capture_output=True, timeout=90)
    need((result.returncode == 0) == success,
         f"{script}退出狀態不符：{result.returncode}\n{result.stdout}\n{result.stderr}")
    return {"tool": script, "exit": result.returncode,
            "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file(), "請在Docker內執行")
    if not args.game.is_dir() or not args.frame.is_file() or not args.decoder.is_dir():
        print("SKIP_GOAL186_RESEARCH：缺合法原版、原版收據或固定研究解碼器")
        return 77
    for name, expected in SOURCE_HASHES.items():
        need(sha((args.game / name).read_bytes()) == expected, f"原版版本失配：{name}")
    raw = args.frame.read_bytes()
    need(sha(raw) == "60c933b0fde14f3e7b966a4c232f28a112537081726b5a921c524afafae87b8b", "原版畫面指紋失配")
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists(), "輸出須為新的workplace子目錄")
    need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出父目錄擁有者不符")
    output.mkdir()
    checks = []
    inventory_dir = output / "inventory"
    checks.append(run("inventory_hd_assets.py", "--game-root", args.game,
                      "--decoder-root", args.decoder, "--output", inventory_dir))
    inventory_path = inventory_dir / "inventory.json"
    inventory = json.loads(inventory_path.read_text())
    need(inventory["source_count"] == 206 and inventory["frame_count"] == 1517 and
         not inventory["failed_files"], "實際SS盤點數量失配")
    placements_path = output / "placements.json"
    locate_args = ["--inventory", inventory_path, "--frame", args.frame]
    checks.append(run("locate_hd_assets.py", *locate_args, "--output", placements_path))
    placements = json.loads(placements_path.read_text())
    need((placements["candidates"], placements["matched_assets"], placements["placements"]) == (345, 42, 71),
         "實際殖民地定位結果失配")
    building = next(row for row in placements["assets"] if row["source"] == "BUILDING.SS" and row["ordinal"] == 32)
    need(building["matches"] == [[56, 13, 79, 40]], "建築032完整定位失配")

    # 用真實資產與真實畫面做一點遮擋負例，不用相似度接受殘缺圖像。
    image_path = inventory_dir / "BUILDING.SS.032.png"
    with Image.open(image_path) as image:
        pixels, (width, height) = image.tobytes(), image.size
    changed = bytearray(raw)
    pixel = next(i for i, value in enumerate(pixels) if value != 253)
    address = (13 + pixel // width) * 320 + 56 + pixel % width
    changed[address] ^= 1
    matches, _ = locate(pixels, width, height, 253, bytes(changed))
    need([56, 13, 79, 40] not in matches, "單一不透明像素被遮擋仍接受整張素材")
    checks.append({"case": "one-original-opaque-pixel-changed", "result": "rejected"})

    before = placements_path.read_bytes()
    checks.append(run("locate_hd_assets.py", *locate_args, "--output", placements_path, success=False))
    need(placements_path.read_bytes() == before, "拒絕覆寫時改動既有收據")
    bad_frame = output / "truncated.idx"
    bad_frame.write_bytes(raw[:-1])
    checks.append(run("locate_hd_assets.py", "--inventory", inventory_path, "--frame", bad_frame,
                      "--output", output / "bad-frame.json", success=False))

    moved = image_path.with_suffix(".disabled")
    image_path.rename(moved)
    try:
        checks.append(run("locate_hd_assets.py", *locate_args, "--output", output / "missing-image.json", success=False))
    finally:
        moved.rename(image_path)
    original_png = image_path.read_bytes()
    try:
        image_path.write_bytes(original_png[:32])
        checks.append(run("locate_hd_assets.py", *locate_args, "--output", output / "corrupt-image.json", success=False))
    finally:
        image_path.write_bytes(original_png)

    bad_decoder = output / "changed-decoder"
    bad_decoder.mkdir()
    (bad_decoder / "source-manifest.json").write_bytes((args.decoder / "source-manifest.json").read_bytes() + b" ")
    checks.append(run("inventory_hd_assets.py", "--game-root", args.game, "--decoder-root", bad_decoder,
                      "--output", output / "bad-decoder", success=False))
    with tempfile.TemporaryDirectory(prefix="colonization-hd-boundary-") as outside:
        target = Path(outside) / "forbidden.json"
        checks.append(run("locate_hd_assets.py", *locate_args, "--output", target, success=False))
        need(not target.exists(), "允許寫入workplace外")
    for path in ["bad-frame.json", "missing-image.json", "corrupt-image.json", "bad-decoder"]:
        need(not (output / path).exists(), f"失敗時仍建立輸出：{path}")
    result = {"result": "PASS_GOAL186_RESEARCH_GUARDS", "script_sha256": sha(Path(__file__).read_bytes()),
              "inventory_sha256": sha(inventory_path.read_bytes()), "placements_sha256": sha(before),
              "checks": checks, "scope": "Research only; no production HD, animation, input or language completion credit."}
    (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["result"], len(checks), "checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
