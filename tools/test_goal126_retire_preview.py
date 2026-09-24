#!/usr/bin/env python3
"""目標126原型輸入的正反例；所有變造只在容器暫存目錄。"""

import argparse
import csv
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from prepare_goal126_retire_preview import validate


def reject(label, action):
    try:
        action()
    except (ValueError, OSError, KeyError, IndexError, TypeError):
        print("PASS", label)
        return
    raise AssertionError(label + " 應拒絕")


def linked_directory(source, target):
    target.mkdir()
    for file in source.iterdir():
        (target / file.name).symlink_to(file.resolve(), target_is_directory=file.is_dir())


def replace_link(path, data):
    path.unlink()
    path.write_bytes(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("game", "fixture", "font", "catalog", "reports"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix="goal126-preview-") as temporary:
        top = Path(temporary)
        game, reports = top / "game", top / "reports"
        linked_directory(args.game, game)
        linked_directory(args.reports, reports)
        fixture, font, catalog = top / "fixture.json", top / "font.ttf", top / "catalog.tsv"
        for target, source in ((fixture, args.fixture), (font, args.font),
                               (catalog, args.catalog)):
            target.symlink_to(source.resolve())
        output = top / "output"
        output.mkdir()
        config = SimpleNamespace(game=game, fixture=fixture, font=font,
                                 catalog=catalog, reports=reports, output=output,
                                 variant="center-34")
        for variant in ("center-34", "left-38"):
            config.variant = variant
            result = validate(config)
            assert result is not None and len(result["layers"]) == 3
            print("PASS 真原版與兩種 Ebitengine 版面", variant)
        config.variant = "center-34"

        missing = top / "missing"
        missing.mkdir()
        config.game = missing
        assert validate(config) is None
        print("PASS 缺合法原版 SKIP 77")
        config.game = game

        path = game / "GAME.TXT"
        raw = path.read_bytes()
        replace_link(path, raw[:0x122] + bytes([raw[0x122] ^ 1]) + raw[0x123:])
        reject("錯版 GAME.TXT", lambda: validate(config))
        path.unlink()
        path.symlink_to(args.game / "GAME.TXT")

        raw = fixture.read_bytes()
        replace_link(fixture, raw + b" ")
        reject("改變玩家事件", lambda: validate(config))
        fixture.unlink()
        fixture.symlink_to(args.fixture.resolve())

        raw = font.read_bytes()
        replace_link(font, raw[:-1] + bytes([raw[-1] ^ 1]))
        reject("錯版字型", lambda: validate(config))
        font.unlink()
        font.symlink_to(args.font.resolve())

        with catalog.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            rows, fields = list(reader), reader.fieldnames
        row = next(r for r in rows if r["candidate_id"] == "GAME.TXT:0x00000122")
        row["zh_hant"] = "別的譯文"
        catalog.unlink()
        with catalog.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        reject("主譯稿變造", lambda: validate(config))
        catalog.unlink()
        catalog.symlink_to(args.catalog.resolve())

        path = reports / "prompt-c.json"
        replace_link(path, path.read_bytes() + b" ")
        reject("雙重播報告不同", lambda: validate(config))
        path.unlink()
        path.symlink_to(args.reports / path.name)

        path = reports / "prompt-control.json"
        report = json.loads(path.read_bytes())
        report["samples"]["1275m"]["memory_sha256"] = "0" * 64
        replace_link(path, (json.dumps(report) + "\n").encode())
        reject("無監看控制 RAM 不同", lambda: validate(config))
        path.unlink()
        path.symlink_to(args.reports / path.name)

        path = reports / "prompt-b.before-question.canvas"
        raw = path.read_bytes()
        replace_link(path, bytes([raw[0] ^ 1]) + raw[1:])
        reject("印前底圖實檔變造", lambda: validate(config))
        path.unlink()
        path.symlink_to(args.reports / path.name)

        path = reports / "prompt-b.1275m.canvas"
        raw = path.read_bytes()
        replace_link(path, bytes([raw[0] ^ 1]) + raw[1:])
        reject("原版畫布實檔變造", lambda: validate(config))
        path.unlink()
        path.symlink_to(args.reports / path.name)
        print("PASS 所有變造只在容器暫存目錄")


if __name__ == "__main__":
    main()
