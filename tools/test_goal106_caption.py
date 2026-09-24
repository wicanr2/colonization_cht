#!/usr/bin/env python3
"""目標106收據負例；原版缺失時只回 SKIP，不假裝 PASS。"""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from check_goal106_caption import check
from check_goal101_nation_intro import FILE_SHA


def rejected(action, label):
    try:
        action()
    except (ValueError, KeyError):
        return
    raise AssertionError(label + " 未失敗即關閉")


def main(args):
    good = check(args.game, args.inputs, args.reports, args.preview,
                 args.catalog, args.font)
    assert good["result"] == "PASS", "真實收據未通過"
    with tempfile.TemporaryDirectory(prefix="colonization-goal106-") as base:
        root = Path(base)
        skipped = check(root / "no-game", root / "no-input", args.reports,
                        args.preview, args.catalog, root / "no-font")
        assert skipped["result"] == "SKIP", "缺原版未明確 SKIP"
        bad_game = root / "bad-game"
        bad_game.mkdir()
        for name in FILE_SHA:
            if name != "GAME.TXT":
                (bad_game / name).symlink_to(args.game / name)
        damaged_game = bytearray((args.game / "GAME.TXT").read_bytes())
        damaged_game[0] ^= 1
        (bad_game / "GAME.TXT").write_bytes(damaged_game)
        rejected(lambda: check(bad_game, args.inputs, args.reports, args.preview,
                               args.catalog, args.font), "錯版原版")
        preview = root / "preview"
        shutil.copytree(args.preview, preview)
        receipt = json.loads((preview / "preview.json").read_text())
        receipt["font_size"] = 24
        (preview / "preview.json").write_text(json.dumps(receipt))
        rejected(lambda: check(args.game, args.inputs, args.reports, preview,
                               args.catalog, args.font), "錯字級")
        shutil.copytree(args.reports, root / "reports")
        reports = root / "reports"
        path = reports / "england-enter-a.after-follow.pre.canvas"
        damaged = bytearray(path.read_bytes())
        damaged[30 * 320 + 16] ^= 1
        path.write_bytes(damaged)
        rejected(lambda: check(args.game, args.inputs, reports, args.preview,
                               args.catalog, args.font), "原版印前畫布破損")
        path.write_bytes((args.reports / path.name).read_bytes())
        path = reports / "england-enter-b.json"
        report = json.loads(path.read_text())
        report["version"] = "unexpected"
        path.write_text(json.dumps(report))
        rejected(lambda: check(args.game, args.inputs, reports, args.preview,
                               args.catalog, args.font), "第二次重播不同")
    print("PASS：真實收據、缺原版 SKIP、錯版、錯字級、印前畫布破損與雙重播變異")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    main(parser.parse_args())
