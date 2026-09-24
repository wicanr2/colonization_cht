#!/usr/bin/env python3
"""目標118獨立正反例；竄改收據只寫入容器暫存目錄。"""

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal118_remaining_rows import EXPECTED, FIXTURES, LABELS, check


def reject(name, action):
    try:
        result = action()
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        print("PASS", name)
        return
    raise AssertionError(f"{name} 應拒絕，卻回傳 {result}")


def copy_prefix(source, target, stem, labels):
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
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="colonization-goal118-") as temp:
        root = Path(temp)
        reports = root / "reports"
        reports.mkdir()
        for branch in FIXTURES:
            for variant in ("a", "b", "control"):
                copy_prefix(args.reports, reports, f"{branch}-{variant}", LABELS)
        baseline = root / "baseline"
        baseline.mkdir()
        copy_prefix(args.baseline, baseline, "baseline-a", LABELS)
        fixtures = root / "fixtures"
        fixtures.mkdir()
        for filename, _, _, _ in FIXTURES.values():
            shutil.copy2(args.fixtures / filename, fixtures / filename)

        def current():
            return check(args.game, args.inputs, fixtures, reports, baseline)

        assert current()["result"] == "PASS"
        print("PASS", "四列雙冷啟動、控制與固定基線")

        path = reports / "second-b.json"
        path.write_bytes(path.read_bytes() + b" ")
        reject("雙冷啟動 byte 分歧", current)
        shutil.copy2(args.reports / path.name, path)

        path = reports / "third-control.json"
        data = json.loads(path.read_bytes())
        data["samples"]["1375m"]["memory_sha256"] = "0" * 64
        path.write_text(json.dumps(data) + "\n")
        reject("無監看控制 RAM 分歧", current)
        shutil.copy2(args.reports / path.name, path)

        path = reports / "fifth-a.1375m.canvas"
        data = bytearray(path.read_bytes())
        data[113 * 320 + 73] ^= 1
        path.write_bytes(data)
        reject("原版畫布竄改", current)
        shutil.copy2(args.reports / path.name, path)

        # 同時改同分支的雙重播及控制畫面並重算報告雜湊；幾何越出仍要拒絕。
        for variant in ("a", "b", "control"):
            stem = f"sixth-{variant}"
            path = reports / f"{stem}.json"
            report = json.loads(path.read_bytes())
            for label in ("1325m", "1350m"):
                for suffix, field in (("canvas", "canvas_sha256"),
                                      ("idx", "indexed_sha256")):
                    raw_path = reports / f"{stem}.{label}.{suffix}"
                    data = bytearray(raw_path.read_bytes())
                    data[10 * 320 + 10] ^= 1
                    raw_path.write_bytes(data)
                    report["samples"][label][field] = hashlib.sha256(data).hexdigest()
            path.write_text(json.dumps(report, ensure_ascii=False) + "\n")
        original_expected = EXPECTED["sixth"].copy()
        modified = (reports / "sixth-a.json").read_bytes()
        modified_report = json.loads(modified)
        EXPECTED["sixth"]["receipt"] = hashlib.sha256(modified).hexdigest()
        EXPECTED["sixth"]["mid"] = (
            modified_report["samples"]["1325m"]["indexed_sha256"],
            modified_report["samples"]["1325m"]["canvas_sha256"])
        try:
            reject("重算雜湊後仍越出選項列", current)
        finally:
            EXPECTED["sixth"] = original_expected
        for variant in ("a", "b", "control"):
            stem = f"sixth-{variant}"
            shutil.copy2(args.reports / f"{stem}.json", reports / f"{stem}.json")
            for label in ("1325m", "1350m"):
                for suffix in ("canvas", "idx"):
                    name = f"{stem}.{label}.{suffix}"
                    shutil.copy2(args.reports / name, reports / name)

        path = baseline / "baseline-a.1375m.canvas"
        data = bytearray(path.read_bytes())
        data[100 * 320 + 100] ^= 1
        path.write_bytes(data)
        reject("既有基線畫布竄改", current)
        shutil.copy2(args.baseline / path.name, path)

        filename = FIXTURES["second"][0]
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
               lambda: check(wrong, args.inputs, fixtures, reports, baseline))
        assert check(root / "missing-game", args.inputs, fixtures,
                     reports, baseline)["result"] == "SKIP"
        print("PASS", "缺原版 SKIP 77")


if __name__ == "__main__":
    main()
