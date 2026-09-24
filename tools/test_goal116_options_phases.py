#!/usr/bin/env python3
"""目標116獨立正反例；竄改資料只存在容器暫存目錄。"""

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal116_options_phases import LABELS, check


def reject(name, action):
    try:
        result = action()
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        print("PASS", name)
        return
    raise AssertionError(f"{name} 應拒絕，卻回傳 {result}")


def copy_reports(source, target):
    target.mkdir()
    for branch in ("hover-first", "hover-last", "exit"):
        for variant in ("a", "b", "control"):
            prefix = f"{branch}-{variant}"
            shutil.copy2(source / f"{prefix}.json", target / f"{prefix}.json")
            for label in LABELS:
                for suffix in ("idx", "canvas", "pal"):
                    name = f"{prefix}.{label}.{suffix}"
                    shutil.copy2(source / name, target / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--old-reports", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="colonization-goal116-") as temp:
        root = Path(temp)
        reports = root / "reports"
        copy_reports(args.reports, reports)
        old = root / "old"
        old.mkdir()
        for variant in ("explore", "replay2", "control"):
            name = f"tutorial-then-first-row-{variant}.json"
            shutil.copy2(args.old_reports / name, old / name)
        for suffix in ("idx", "canvas", "pal"):
            name = f"tutorial-then-first-row-explore.1325m.{suffix}"
            shutil.copy2(args.old_reports / name, old / name)
        fixtures = root / "fixtures"
        fixtures.mkdir()
        for name in ("hover-first", "hover-last", "exit"):
            filename = f"goal116-{name}.inputs.json"
            shutil.copy2(args.fixtures / filename, fixtures / filename)

        def current():
            return check(args.game, args.inputs, fixtures, reports, old)

        assert current()["result"] == "PASS"
        print("PASS", "三分支雙重播、控制與舊點擊對照")
        path = reports / "hover-last-b.json"
        path.write_bytes(path.read_bytes() + b" ")
        reject("雙冷啟動 byte 分歧", current)
        shutil.copy2(args.reports / path.name, path)

        path = reports / "hover-first-control.json"
        data = json.loads(path.read_bytes())
        data["samples"]["1325m"]["memory_sha256"] = "0" * 64
        path.write_text(json.dumps(data) + "\n")
        reject("無監看控制 RAM 分歧", current)
        shutil.copy2(args.reports / path.name, path)

        path = reports / "hover-last-a.1325m.idx"
        raw = bytearray(path.read_bytes())
        raw[149 * 320 + 140] ^= 1
        path.write_bytes(raw)
        reject("原版索引畫面竄改", current)
        shutil.copy2(args.reports / path.name, path)

        modified = bytearray((reports / "hover-last-a.1325m.canvas").read_bytes())
        modified[100 * 320 + 100] ^= 1
        digest = hashlib.sha256(modified).hexdigest()
        for variant in ("a", "b", "control"):
            prefix = f"hover-last-{variant}"
            (reports / f"{prefix}.1325m.canvas").write_bytes(modified)
            data = json.loads((reports / f"{prefix}.json").read_bytes())
            data["samples"]["1325m"]["canvas_sha256"] = digest
            (reports / f"{prefix}.json").write_text(json.dumps(data) + "\n")
        reject("純移鼠竟改變底層畫布", current)
        for variant in ("a", "b", "control"):
            prefix = f"hover-last-{variant}"
            for suffix in ("json", "1325m.canvas"):
                name = f"{prefix}.{suffix}"
                shutil.copy2(args.reports / name, reports / name)

        for variant in ("a", "b", "control"):
            path = reports / f"exit-{variant}.json"
            data = json.loads(path.read_bytes())
            for event in data["key_events"]:
                if event["step"] >= 1_351_000_000:
                    event["pending"] = 1
            path.write_text(json.dumps(data) + "\n")
        reject("ESC 未被原版消費", current)
        for variant in ("a", "b", "control"):
            name = f"exit-{variant}.json"
            shutil.copy2(args.reports / name, reports / name)

        path = old / "tutorial-then-first-row-explore.1325m.canvas"
        raw = bytearray(path.read_bytes())
        raw[0] ^= 1
        path.write_bytes(raw)
        reject("既有末列點擊畫布竄改", current)
        shutil.copy2(args.old_reports / path.name, path)

        path = fixtures / "goal116-exit.inputs.json"
        path.write_bytes(path.read_bytes() + b" ")
        reject("玩家事件檔版本不符", current)
        shutil.copy2(args.fixtures / path.name, path)

        wrong = root / "wrong-game"
        wrong.mkdir()
        for name in (*FILE_SHA, "MENU.TXT"):
            if name == "GAME.TXT":
                content = (args.game / name).read_bytes()
                (wrong / name).write_bytes(content[:-1] + bytes((content[-1] ^ 1,)))
            else:
                (wrong / name).symlink_to(args.game / name)
        reject("原版檔案版本不符",
               lambda: check(wrong, args.inputs, fixtures, reports, old))
        assert check(root / "missing-game", args.inputs, fixtures, reports, old)["result"] == "SKIP"
        print("PASS", "缺原版 SKIP 77")


if __name__ == "__main__":
    main()
