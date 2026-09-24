#!/usr/bin/env python3
"""目標124真視窗收據的正反例；竄改僅在容器暫存目錄。"""

import argparse
import json
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal124_keyboard import CYCLE_SHA, check
from check_goal112_options_source import MENU_SHA


def reject(name, action):
    try:
        action()
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        print("PASS", name)
        return
    raise AssertionError(name + " 應失敗卻通過")


def linked_files(source, target):
    target.mkdir()
    for file in source.iterdir():
        if file.is_file():
            (target / file.name).symlink_to(file.resolve())


def replace(path, data):
    path.unlink()
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.game, args.reports, args.source)
    assert result["result"] == "PASS"
    print("PASS 真視窗、英文控制、兩個少一鍵對照與失焦負例")

    with tempfile.TemporaryDirectory(prefix="colonization-goal124-") as temp:
        root = Path(temp)
        assert check(root / "missing-game", args.reports, args.source)["result"] == "SKIP"
        print("PASS 缺合法原版 SKIP 77")

        wrong_game = root / "wrong-game"
        wrong_game.mkdir()
        for name in (*FILE_SHA, "MENU.TXT", "CYCLE.DAT"):
            source = args.game / name
            target = wrong_game / name
            if name == "CYCLE.DAT":
                data = source.read_bytes()
                target.write_bytes(data[:-1] + bytes((data[-1] ^ 1,)))
            else:
                target.symlink_to(source)
        assert CYCLE_SHA and MENU_SHA
        reject("錯版遊戲資料", lambda: check(wrong_game, args.reports, args.source))

        bad_source = root / "window.go"
        bad_source.write_bytes(args.source.read_bytes() + b"\n")
        reject("錯版視窗程式", lambda: check(args.game, args.reports, bad_source))

        copies = root / "copies"
        linked_files(args.reports, copies)
        input_path = copies / "live-route-b.inputs.json"
        original = (args.reports / input_path.name).read_bytes()
        receipt = json.loads(original)
        next(e for e in receipt["inputs"] if e["kind"] == "left")["kind"] = "right"
        replace(input_path, json.dumps(receipt).encode())
        reject("真視窗左鍵被換成右鍵", lambda: check(args.game, copies, args.source))
        input_path.unlink()
        input_path.symlink_to((args.reports / input_path.name).resolve())

        memory_path = copies / "live-route-b-control.memory"
        data = bytearray(memory_path.read_bytes())
        data[0] ^= 1
        replace(memory_path, data)
        reject("英文控制完整 RAM 差異", lambda: check(args.game, copies, args.source))
        memory_path.unlink()
        memory_path.symlink_to((args.reports / memory_path.name).resolve())

        variant_path = copies / "without-escape.inputs.json"
        replace(variant_path, original)
        reject("反向對照沒有真正移除 Esc", lambda: check(args.game, copies, args.source))
        variant_path.unlink()
        variant_path.symlink_to((args.reports / variant_path.name).resolve())

        focus_path = copies / "focus-left.inputs.json"
        focus = json.loads(focus_path.read_bytes())
        focus["inputs"].append({"step": 4_000_000, "kind": "left", "x": 0, "y": 0, "button": 0})
        replace(focus_path, json.dumps(focus).encode())
        reject("失焦左鍵被延後送入", lambda: check(args.game, copies, args.source))
        focus_path.unlink()
        focus_path.symlink_to((args.reports / focus_path.name).resolve())

        png_path = copies / "live-route-b.sea-before.png"
        data = bytearray(png_path.read_bytes())
        data[0] ^= 1
        replace(png_path, data)
        reject("真視窗畫面檔竄改", lambda: check(args.game, copies, args.source))
        print("PASS 所有竄改僅留容器暫存目錄")


if __name__ == "__main__":
    main()
