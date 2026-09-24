#!/usr/bin/env python3
"""目標125獨立正反例；竄改僅在容器暫存目錄進行。"""

import argparse
import json
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal112_options_source import MENU_SHA
from check_goal123_retire_route import EXTRA_FILES
from check_goal125_tutorial_persistence import check


def reject(label, action):
    try:
        result = action()
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        print("PASS", label)
        return
    raise AssertionError(f"{label} 應拒絕，卻回傳 {result}")


def linked_files(source, target):
    target.mkdir()
    for path in source.iterdir():
        (target / path.name).symlink_to(path.resolve(), target_is_directory=path.is_dir())


def replace_link(path, data):
    path.unlink()
    path.write_bytes(data)


def restore_link(path, source):
    path.unlink()
    path.symlink_to(source.resolve())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()

    def current(game=None, inputs=None, fixtures=None, source=None, reports=None):
        return check(game or args.game, inputs or args.inputs,
                     fixtures or args.fixtures, source or args.source,
                     reports or args.reports)
    result = current()
    assert result["result"] == "PASS" and len(result["first_receipt_sha256"]) == 3
    print("PASS 三支首輪、跨次冷啟動、雙重播、無監看與原版實檔")

    with tempfile.TemporaryDirectory(prefix="colonization-goal125-") as tmp:
        root = Path(tmp)
        assert current(game=root / "missing") == {"result": "SKIP",
                                                    "reason": "合法 DOS 原版或固定開局輸入缺失"}
        print("PASS 缺合法原版 SKIP 77")

        game = root / "wrong-game"
        game.mkdir()
        for name in {**FILE_SHA, "MENU.TXT": MENU_SHA, **EXTRA_FILES}:
            (game / name).symlink_to((args.game / name).resolve())
        target = game / "GAME.TXT"
        data = bytearray((args.game / "GAME.TXT").read_bytes())
        data[-1] ^= 1
        replace_link(target, data)
        reject("錯版原版資料", lambda: current(game=game))

        wrong_source = root / "wrong-probe.go"
        wrong_source.write_bytes(args.source.read_bytes() + b" ")
        reject("錯版探針", lambda: current(source=wrong_source))

        fixtures = root / "fixtures"
        linked_files(args.fixtures, fixtures)
        fixture = fixtures / "goal125-toggle-once-retire.inputs.json"
        replace_link(fixture, fixture.read_bytes() + b" ")
        reject("玩家事件內容變造", lambda: current(fixtures=fixtures))
        restore_link(fixture, args.fixtures / fixture.name)

        reports = root / "reports"
        linked_files(args.reports, reports)
        overlay = lambda: current(reports=reports)
        target = reports / "once-b.json"
        replace_link(target, target.read_bytes() + b" ")
        reject("雙次冷啟動報告分歧", overlay)
        restore_link(target, args.reports / target.name)

        target = reports / "once-control.json"
        report = json.loads(target.read_bytes())
        report["samples"]["1350m"]["memory_sha256"] = "0" * 64
        replace_link(target, (json.dumps(report) + "\n").encode())
        reject("無監看控制完整 RAM 分歧", overlay)
        restore_link(target, args.reports / target.name)

        scratch = reports / "none-a-scratch"
        scratch.unlink()
        scratch.mkdir()
        save = bytearray((args.reports / "none-a-scratch/COLONY09.SAV").read_bytes())
        save[-1] ^= 1
        (scratch / "COLONY09.SAV").write_bytes(save)
        (scratch / "HALLFAME.DAT").symlink_to(
            (args.reports / "none-a-scratch/HALLFAME.DAT").resolve())
        reject("保存檔像素以外的原版位元組竄改", overlay)
        for path in scratch.iterdir():
            path.unlink()
        scratch.rmdir()
        scratch.symlink_to((args.reports / "none-a-scratch").resolve(),
                           target_is_directory=True)

        frame = reports / "restart-none-a.1400m.idx"
        data = bytearray(frame.read_bytes())
        data[100 * 320 + 100] ^= 1
        replace_link(frame, data)
        reject("第二局原版畫面實檔竄改", overlay)
        restore_link(frame, args.reports / frame.name)

        for variant in ("a", "b", "control"):
            target = reports / f"once-{variant}.json"
            report = json.loads(target.read_bytes())
            report["game_terminal"]["dos_exited"] = False
            replace_link(target, (json.dumps(report) + "\n").encode())
        reject("偽造 DOS 正常退出旗標", overlay)
        for variant in ("a", "b", "control"):
            target = reports / f"once-{variant}.json"
            restore_link(target, args.reports / target.name)

        for variant in ("a", "b", "control"):
            target = reports / f"restart-once-{variant}.json"
            report = json.loads(target.read_bytes())
            report["unobserved_note"] = "本分支未合流"
            replace_link(target, (json.dumps(report, ensure_ascii=False) + "\n").encode())
        reject("三支第二局完整報告未合流", overlay)
        print("PASS 所有竄改只在容器暫存目錄")


if __name__ == "__main__":
    main()
