#!/usr/bin/env python3
"""第三張難度卡可逆預覽的錯版、來源、字型、缺字、溢出與底圖負例。"""

import argparse
import contextlib
import io
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

from prepare_goal121_card_preview import FIELDS, field_data, make_layer, prepare
from validate_translation_draft import read_catalog


def rejected(label, call, error=ValueError):
    try:
        call()
    except error:
        return
    raise AssertionError("未拒絕負例：" + label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reports", "catalog", "game", "font", "palette"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="colonization-goal121-") as temporary:
        root = Path(temporary)
        good = SimpleNamespace(**vars(args), out=root / "good")
        with contextlib.redirect_stdout(io.StringIO()):
            prepare(good)
        assert (good.out / "faithful.json").is_file() and (good.out / "readable.json").is_file()

        wrong_palette = root / "wrong.pal"
        wrong_palette.write_bytes(args.palette.read_bytes()[:-1] + b"\x00")
        rejected("錯色盤", lambda: prepare(SimpleNamespace(**{**vars(good), "palette": wrong_palette})))

        wrong_font = root / "wrong.ttf"
        wrong_font.write_bytes(args.font.read_bytes() + b"wrong version")
        rejected("錯字型", lambda: prepare(SimpleNamespace(**{**vars(good), "font": wrong_font})))

        wrong_catalog = root / "wrong.tsv"
        source_catalog = args.catalog.read_text(encoding="utf-8")
        assert source_catalog.count("NAMES.TXT:0x00000C22") == 1
        wrong_catalog.write_text(source_catalog.replace("NAMES.TXT:0x00000C22",
                                                        "NAMES.TXT:0x00000C23"), encoding="utf-8")
        rejected("錯來源鍵", lambda: prepare(SimpleNamespace(**{**vars(good), "catalog": wrong_catalog})))

        wrong_game = root / "wrong-game"
        wrong_game.mkdir()
        for name in ("OPENING.EXE", "VICEROY.EXE", "GAME.TXT", "NAMES.TXT", "LABELS.TXT"):
            (wrong_game / name).symlink_to(args.game / name)
        (wrong_game / "NAMES.TXT").unlink()
        shutil.copyfile(args.game / "NAMES.TXT", wrong_game / "NAMES.TXT")
        changed = bytearray((wrong_game / "NAMES.TXT").read_bytes())
        changed[0xC22] ^= 1
        (wrong_game / "NAMES.TXT").write_bytes(changed)
        rejected("錯原版", lambda: prepare(SimpleNamespace(**{**vars(good), "game": wrong_game})))
        rejected("缺原版", lambda: prepare(SimpleNamespace(**{**vars(good), "game": root / "absent"})),
                 FileNotFoundError)

        field = FIELDS[0]
        row = next(row for row in read_catalog(args.catalog) if row["candidate_id"] == field["key"])
        rejected("缺字", lambda: field_data(field, row, args.font, set(), args.reports,
                                         (args.reports / "click-v3-a.away-settled.canvas").read_bytes()))
        background = bytes((field["safe"][2] - field["safe"][0]) *
                           (field["safe"][3] - field["safe"][1]))
        rejected("文字溢出", lambda: make_layer(field, "征服者" * 30, background, args.font,
                                              "faithful", set()))

        altered = root / "altered-reports"
        altered.mkdir()
        for name in ("before-title-ink", "after-title-before-subtitle"):
            shutil.copyfile(args.reports / f"click-v3-a.{name}.canvas",
                            altered / f"click-v3-a.{name}.canvas")
        before = altered / "click-v3-a.before-title-ink.canvas"
        image = bytearray(before.read_bytes())
        image[139 * 320 + 29] ^= 1
        before.write_bytes(image)
        rejected("變造印前底圖", lambda: field_data(
            field, row, args.font, set(ord(c) for c in row["zh_hant"]), altered,
            (args.reports / "click-v3-a.away-settled.canvas").read_bytes()))

    print("PASS：A／B 正例與錯色盤、錯字型、錯來源鍵、錯原版、缺原版、缺字、溢出、變造底圖負例")


if __name__ == "__main__":
    main()
