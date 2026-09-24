#!/usr/bin/env python3
"""目標123獨立正反例；只在容器暫存目錄竄改，不碰合法原版。"""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from check_goal123_retire_route import BRANCHES, EXTRA_FILES, check
from check_goal101_nation_intro import FILE_SHA


def reject(name, action):
    try:
        result = action()
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        print("PASS", name)
        return
    raise AssertionError(f"{name} 應拒絕，卻回傳 {result}")


def linked_files(source, target):
    target.mkdir()
    for file in source.iterdir():
        if file.is_file():
            (target / file.name).symlink_to(file.resolve())


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
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports-root", type=Path, required=True)
    args = parser.parse_args()

    result = check(args.game, args.inputs, args.fixtures, args.reports_root)
    assert result["result"] == "PASS" and result["terminal"]["dos_exited"] is True
    assert result["terminal"]["step"] == 1_451_193_903
    assert result["final_scenes"]["yes"] != result["final_scenes"]["no"]
    print("PASS 四分支正常玩家原版收據、同焦點差異與 DOS 正常結束")

    with tempfile.TemporaryDirectory(prefix="colonization-goal123-") as temp:
        root = Path(temp)
        assert check(root / "missing-game", args.inputs, args.fixtures,
                     args.reports_root)["result"] == "SKIP"
        print("PASS 缺合法原版 SKIP 77")

        wrong_game = root / "wrong-game"
        wrong_game.mkdir()
        for name in (*FILE_SHA, "MENU.TXT", *EXTRA_FILES):
            source = args.game / name
            target = wrong_game / name
            if name == "WOODPANL.PIK":
                data = source.read_bytes()
                target.write_bytes(data[:-1] + bytes((data[-1] ^ 1,)))
            else:
                target.symlink_to(source)
        reject("錯版退休畫面圖檔", lambda: check(wrong_game, args.inputs,
                                               args.fixtures, args.reports_root))

        wrong_input = root / "wrong-input.json"
        wrong_input.write_bytes(args.inputs.read_bytes() + b" ")
        reject("錯開局玩家輸入", lambda: check(args.game, wrong_input,
                                            args.fixtures, args.reports_root))

        fixtures = root / "fixtures"
        linked_files(args.fixtures, fixtures)
        fixture = BRANCHES["yes"]["fixture"]
        replace_link(fixtures / fixture, (args.fixtures / fixture).read_bytes() + b" ")
        reject("錯 Yes 點擊事件", lambda: check(args.game, args.inputs,
                                             fixtures, args.reports_root))

        reports = root / "reports"
        reports.mkdir()
        (reports / "goal111-help").symlink_to((args.reports_root / "goal111-help").resolve())
        replay = reports / "goal123-retire"
        linked_files(args.reports_root / "goal123-retire", replay)
        current = lambda: check(args.game, args.inputs, args.fixtures, reports)
        assert current()["result"] == "PASS"

        second = replay / "yes-b.json"
        source = args.reports_root / "goal123-retire" / second.name
        replace_link(second, source.read_bytes() + b" ")
        reject("雙冷啟動 JSON 分歧", current)
        restore_link(second, source)

        first = replay / "yes-explore.json"
        source = args.reports_root / "goal123-retire" / first.name
        replace_link(first, (args.reports_root / "goal123-retire/no-a.json").read_bytes())
        reject("把 No 收據冒充 Yes", current)
        restore_link(first, source)

        control = replay / "no-control.json"
        source = args.reports_root / "goal123-retire" / control.name
        report = json.loads(source.read_bytes())
        report["samples"]["1350m"]["memory_sha256"] = "0" * 64
        replace_link(control, (json.dumps(report) + "\n").encode())
        reject("無監看控制 RAM 分歧", current)
        restore_link(control, source)

        frame = replay / "hall-control.terminal.idx"
        source = args.reports_root / "goal123-retire" / frame.name
        data = bytearray(source.read_bytes())
        data[100 * 320 + 100] ^= 1
        replace_link(frame, data)
        reject("原版終止畫面實檔竄改", current)
        restore_link(frame, source)

        for name in ("hall-a", "hall-b", "hall-control"):
            path = replay / f"{name}.json"
            source = args.reports_root / "goal123-retire" / path.name
            report = json.loads(source.read_bytes())
            report["game_terminal"]["dos_exited"] = False
            replace_link(path, (json.dumps(report, ensure_ascii=False) + "\n").encode())
        old_sha = BRANCHES["hall"]["sha"]
        BRANCHES["hall"]["sha"] = hashlib.sha256((replay / "hall-a.json").read_bytes()).hexdigest()
        try:
            reject("終止旗標偽造且重算 JSON SHA", current)
        finally:
            BRANCHES["hall"]["sha"] = old_sha
        print("PASS 所有竄改僅留容器暫存目錄")


if __name__ == "__main__":
    main()
