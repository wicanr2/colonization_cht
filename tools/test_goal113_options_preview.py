#!/usr/bin/env python3
"""目標113可丟棄預覽的獨立正反例；測試資料只寫容器暫存區。"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from prepare_goal113_options_preview import prepare


def expect_failure(label, call):
    try:
        result = call()
    except (OSError, ValueError, KeyError, IndexError):
        print("PASS", label)
        return
    raise AssertionError(f"{label} 應拒絕，卻回傳 {result}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--chinese", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="colonization-goal113-") as temp:
        root = Path(temp)
        reports = root / "reports"
        reports.mkdir()
        for name in ("preprint-a.json", "preprint-b.json", "preprint-control.json",
                     "preprint-a.1300m.idx", "preprint-a.1300m.pal",
                     "preprint-b.1300m.idx", "preprint-b.1300m.pal",
                     "preprint-control.1300m.idx", "preprint-control.1300m.pal"):
            shutil.copy2(args.reports / name, reports / name)
        for variant in ("a", "b"):
            for index in range(9):
                name = f"preprint-{variant}.option-before-{index:02d}.canvas"
                shutil.copy2(args.reports / name, reports / name)
        options = SimpleNamespace(reports=reports, catalog=args.catalog,
                                  game=args.game, font=args.font,
                                  output=root / "preview.json", variant="faithful")
        assert prepare(options) == 0
        options.variant = "readable"
        assert prepare(options) == 0
        print("PASS", "A/B真實來源與九欄安全矩形")
        options.variant = "faithful"
        damaged = reports / "preprint-b.json"
        damaged.write_bytes(damaged.read_bytes() + b" ")
        expect_failure("兩次冷啟動分歧", lambda: prepare(options))
        shutil.copy2(args.reports / damaged.name, damaged)
        damaged = reports / "preprint-a.option-before-03.canvas"
        pixels = bytearray(damaged.read_bytes())
        pixels[85 * 320 + 82] ^= 1
        damaged.write_bytes(pixels)
        expect_failure("印前底圖遭竄改", lambda: prepare(options))
        shutil.copy2(args.reports / damaged.name, damaged)
        damaged = reports / "preprint-control.1300m.idx"
        pixels = bytearray(damaged.read_bytes())
        pixels[0] ^= 1
        damaged.write_bytes(pixels)
        expect_failure("無監看控制畫面分歧", lambda: prepare(options))
        shutil.copy2(args.reports / damaged.name, damaged)
        wrong_font = root / "wrong-font.ttf"
        wrong_font.write_bytes(args.font.read_bytes() + b"x")
        options.font = wrong_font
        expect_failure("錯字型", lambda: prepare(options))
        options.font = args.font
        wrong_catalog = root / "wrong.tsv"
        wrong_catalog.write_text(args.catalog.read_text().replace("遊戲選項設定", "遊戲選項設定" * 20, 1))
        options.catalog = wrong_catalog
        expect_failure("過長譯文", lambda: prepare(options))
        wrong_catalog.write_text("\n".join(line for line in args.catalog.read_text().splitlines()
                                           if not line.startswith("GAME.TXT:0x000004FD\t")) + "\n")
        expect_failure("九欄缺鍵", lambda: prepare(options))
        options.catalog = args.catalog
        wrong_game = root / "wrong-game"
        wrong_game.mkdir()
        original = (args.game / "GAME.TXT").read_bytes()
        (wrong_game / "GAME.TXT").write_bytes(original[:-1] + bytes((original[-1] ^ 1,)))
        options.game = wrong_game
        expect_failure("錯原版", lambda: prepare(options))
        options.game = root / "missing-game"
        assert prepare(options) == 77
        print("PASS", "缺原版 SKIP 77")
        with Image.open(args.chinese) as image:
            altered = image.convert("RGB")
        original = altered.getpixel((0, 0))
        altered.putpixel((0, 0), tuple(value ^ 1 for value in original))
        altered_path = root / "outside-safe.png"
        altered.save(altered_path)
        verifier = Path(__file__).with_name("verify_card_preview.py")
        result = subprocess.run([sys.executable, str(verifier), "--input",
                                 str(args.reports / "options-faithful.json"), "--control",
                                 str(args.control), "--chinese", str(altered_path), "--output",
                                 str(root / "invalid-receipt.json")], capture_output=True, text=True,
                                check=False)
        assert result.returncode != 0 and "超出安全矩形" in result.stderr
        print("PASS", "安全矩形外改色拒絕")


if __name__ == "__main__":
    main()
