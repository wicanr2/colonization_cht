#!/usr/bin/env python3
"""目標117獨立正反例；竄改收據只寫入容器暫存目錄。"""

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal117_same_focus import FIXTURES, LABELS, check


def reject(name, action):
    try:
        result = action()
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        print("PASS", name)
        return
    raise AssertionError(f"{name} 應拒絕，卻回傳 {result}")


def clone(source, target, branch_names, variants, labels):
    target.mkdir()
    for branch in branch_names:
        for variant in variants:
            stem = f"{branch}-{variant}"
            shutil.copy2(source / f"{stem}.json", target / f"{stem}.json")
            for label in labels:
                for suffix in ("idx", "canvas", "pal"):
                    name = f"{stem}.{label}.{suffix}"
                    shutil.copy2(source / name, target / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--old-reports", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="colonization-goal117-") as temp:
        root = Path(temp)
        reports = root / "reports"
        clone(args.reports, reports, FIXTURES, ("a", "b", "control"), LABELS)
        old = root / "old"
        clone(args.old_reports, old,
              ("tutorial-then-first-row", "first-row-only"),
              ("explore",), ("1375m",))
        fixtures = root / "fixtures"
        fixtures.mkdir()
        for filename, _ in FIXTURES.values():
            shutil.copy2(args.fixtures / filename, fixtures / filename)

        def current():
            return check(args.game, args.inputs, fixtures, reports, old)

        assert current()["result"] == "PASS"
        print("PASS", "三分支雙冷啟動、控制與末列對照")

        path = reports / "fourth-b.json"
        path.write_bytes(path.read_bytes() + b" ")
        reject("雙冷啟動 byte 分歧", current)
        shutil.copy2(args.reports / path.name, path)

        path = reports / "seventh-control.json"
        data = json.loads(path.read_bytes())
        data["samples"]["1375m"]["memory_sha256"] = "0" * 64
        path.write_text(json.dumps(data) + "\n")
        reject("無監看控制 RAM 分歧", current)
        shutil.copy2(args.reports / path.name, path)

        path = reports / "fourth-a.1375m.canvas"
        data = bytearray(path.read_bytes())
        data[101 * 320 + 73] ^= 1
        path.write_bytes(data)
        reject("原版畫布竄改", current)
        shutil.copy2(args.reports / path.name, path)

        # 同時重算九份收據中該分支的原始像素與雜湊，不能只依 SHA 放行新幾何。
        for variant in ("a", "b", "control"):
            stem = f"fourth-{variant}"
            path = reports / f"{stem}.json"
            report = json.loads(path.read_bytes())
            for label in ("1375m", "1400m"):
                for suffix, field in (("canvas", "canvas_sha256"),
                                      ("idx", "indexed_sha256")):
                    raw_path = reports / f"{stem}.{label}.{suffix}"
                    data = bytearray(raw_path.read_bytes())
                    data[100 * 320 + 100] ^= 1
                    raw_path.write_bytes(data)
                    report["samples"][label][field] = hashlib.sha256(data).hexdigest()
            path.write_text(json.dumps(report, ensure_ascii=False) + "\n")
        reject("重算雜湊後仍偏離固定畫面與圖示", current)
        for variant in ("a", "b", "control"):
            stem = f"fourth-{variant}"
            shutil.copy2(args.reports / f"{stem}.json", reports / f"{stem}.json")
            for label in ("1375m", "1400m"):
                for suffix in ("canvas", "idx"):
                    name = f"{stem}.{label}.{suffix}"
                    shutil.copy2(args.reports / name, reports / name)

        path = old / "tutorial-then-first-row-explore.1375m.idx"
        data = bytearray(path.read_bytes())
        data[148 * 320 + 73] ^= 1
        path.write_bytes(data)
        reject("既有末列收據竄改", current)
        shutil.copy2(args.old_reports / path.name, path)

        filename = FIXTURES["seventh"][0]
        path = fixtures / filename
        path.write_bytes(path.read_bytes() + b" ")
        reject("玩家事件檔版本不符", current)
        shutil.copy2(args.fixtures / path.name, path)

        wrong = root / "wrong-game"
        wrong.mkdir()
        for name in (*FILE_SHA, "MENU.TXT"):
            if name == "GAME.TXT":
                data = (args.game / name).read_bytes()
                (wrong / name).write_bytes(data[:-1] + bytes((data[-1] ^ 1,)))
            else:
                (wrong / name).symlink_to(args.game / name)
        reject("原版檔案版本不符",
               lambda: check(wrong, args.inputs, fixtures, reports, old))
        assert check(root / "missing-game", args.inputs, fixtures,
                     reports, old)["result"] == "SKIP"
        print("PASS", "缺原版 SKIP 77")


if __name__ == "__main__":
    main()
