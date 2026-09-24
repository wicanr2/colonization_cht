#!/usr/bin/env python3
"""目標119原版細相位檢查器的正反例；所有複本只寫 Docker /tmp。"""

import argparse
import json
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal119_options_click import (FIXTURES, LABELS, check, check_visual,
                                         frame)


def expect_reject(label, fn):
    try:
        fn()
    except ValueError:
        print("PASS：拒絕" + label)
        return
    raise AssertionError("未拒絕" + label)


def link_files(source, target, names):
    target.mkdir()
    for name in names:
        (target / name).symlink_to(source / name)


def replace(path, data):
    path.unlink()
    path.write_bytes(data)


def relink(path, original):
    path.unlink()
    path.symlink_to(original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--legacy-baseline", type=Path, required=True)
    args = parser.parse_args()
    if not args.game.is_dir() or not args.inputs.is_file():
        need_skip = check(Path("/nonexistent-colonization-original"), args.inputs,
                          args.fixtures, args.reports)
        assert need_skip["result"] == "SKIP"
        print("SKIP 77：合法原版或正常玩家輸入不存在")
        return 77
    assert check(args.game, args.inputs, args.fixtures, args.reports)["result"] == "PASS"
    print("PASS：固定原版正例")
    legacy = (args.reports / "legacy-default.json").read_bytes()
    assert legacy == args.legacy_baseline.read_bytes()
    print("PASS：額外取樣關閉時舊版 JSON 逐位元組不變")

    scenes = {}
    for branch in FIXTURES:
        report = json.loads((args.reports / f"{branch}-a.json").read_text())
        scenes[branch] = {label: frame(args.reports / f"{branch}-a", label,
                                       report["samples"][label]) for label in LABELS}
    check_visual(scenes)
    changed = {branch: {label: raw.copy() for label, raw in scene.items()}
               for branch, scene in scenes.items()}
    extra = bytearray(changed["eighth"]["phase-07"]["canvas"])
    extra[10 * 320 + 200] ^= 1
    changed["eighth"]["phase-07"]["canvas"] = bytes(extra)
    expect_reject("安全區外的第五個畫素", lambda: check_visual(changed))

    with tempfile.TemporaryDirectory(prefix="colonization-goal119-") as scratch:
        root = Path(scratch)
        game = root / "game"
        fixtures = root / "fixtures"
        reports = root / "reports"
        link_files(args.game, game, (*FILE_SHA, "MENU.TXT"))
        link_files(args.fixtures, fixtures, (name for name, _ in FIXTURES.values()))
        link_files(args.reports, reports, (path.name for path in args.reports.iterdir()
                                         if path.is_file()))
        expect_reject("錯原版 GAME.TXT", lambda: (
            replace(game / "GAME.TXT", b"wrong"),
            check(game, args.inputs, fixtures, reports)))
        relink(game / "GAME.TXT", args.game / "GAME.TXT")

        fixture = fixtures / FIXTURES["first"][0]
        original_fixture = fixture.read_bytes()
        missing_release = original_fixture.replace(
            b'"step": 1303000000, "kind": "release"',
            b'"step": 1303000000, "kind": "move"', 1)
        assert missing_release != original_fixture
        replace(fixture, missing_release)
        expect_reject("缺點擊放開事件", lambda: check(game, args.inputs, fixtures, reports))
        relink(fixture, args.fixtures / fixture.name)

        observed = reports / "first-a.json"
        old = json.loads(observed.read_text())
        old["version"] = "wrong"
        replace(observed, json.dumps(old).encode())
        expect_reject("錯探針版本", lambda: check(game, args.inputs, fixtures, reports))
        relink(observed, args.reports / observed.name)

        control = reports / "first-control.json"
        old = json.loads(control.read_text())
        old["samples"]["phase-07"]["memory_sha256"] = "0" * 64
        replace(control, json.dumps(old).encode())
        expect_reject("無監看控制 RAM 分歧", lambda: check(game, args.inputs, fixtures, reports))
        relink(control, args.reports / control.name)

        raw = reports / "eighth-a.phase-07.canvas"
        old_raw = bytearray(raw.read_bytes())
        old_raw[10 * 320 + 200] ^= 1
        replace(raw, old_raw)
        expect_reject("原始畫布遭改動", lambda: check(game, args.inputs, fixtures, reports))

    skipped = check(Path("/nonexistent-colonization-original"), args.inputs,
                    args.fixtures, args.reports)
    assert skipped["result"] == "SKIP"
    print("PASS：缺合法原版明示 SKIP 77")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
