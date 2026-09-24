#!/usr/bin/env python3
"""目標114資料流獨立正反例；所有竄改只在容器暫存目錄。"""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from check_goal114_options_dataflow import check
from check_goal112_options_source import FILE_SHA


def expect_fail(label, call):
    try:
        result = call()
    except (OSError, ValueError, KeyError, IndexError, StopIteration):
        print("PASS", label)
        return
    raise AssertionError(f"{label} 應拒絕，卻回傳 {result}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="colonization-goal114-") as temp:
        root = Path(temp)
        reports = root / "reports"
        reports.mkdir()
        for variant in ("a", "b", "control"):
            for suffix in ("json", "1300m.idx", "1300m.pal"):
                name = f"writer-v4-{variant}.{suffix}"
                shutil.copy2(args.reports / name, reports / name)
                resident_name = f"resident-{variant}.{suffix}"
                shutil.copy2(args.reports / resident_name, reports / resident_name)
        for variant in ("a", "b"):
            for index in range(9):
                name = f"writer-v4-{variant}.option-before-{index:02d}.canvas"
                shutil.copy2(args.reports / name, reports / name)

        def current():
            return check(args.game, args.inputs, args.fixture, reports)

        assert current()["result"] == "PASS"
        print("PASS", "固定原版雙重播與無監看控制")
        variant_b = reports / "writer-v4-b.json"
        variant_b.write_bytes(variant_b.read_bytes() + b" ")
        expect_fail("雙重播 byte 分歧", current)
        shutil.copy2(args.reports / variant_b.name, variant_b)

        def alter_both(change):
            source = json.loads((args.reports / "writer-v4-a.json").read_bytes())
            change(source)
            data = (json.dumps(source, ensure_ascii=False) + "\n").encode()
            for variant in ("a", "b"):
                (reports / f"writer-v4-{variant}.json").write_bytes(data)

        alter_both(lambda data: data["option_source_reads"][0].__setitem__("value", 0))
        expect_fail("錯原版解析 byte", current)
        alter_both(lambda data: data["option_print_writes"][6].__setitem__("value", 0))
        expect_fail("錯印字緩衝寫入", current)
        alter_both(lambda data: data["option_writer_reads"].pop(0))
        expect_fail("漏近端讀取", current)
        for variant in ("a", "b"):
            shutil.copy2(args.reports / f"writer-v4-{variant}.json",
                         reports / f"writer-v4-{variant}.json")
        resident_source = json.loads((args.reports / "resident-a.json").read_bytes())
        title_write = next(entry for entry in resident_source["option_resident_writes"]
                           if entry["cs_ip"] == "0E2D:11A5" and entry["linear"] == 476096)
        title_write["value"] ^= 1
        for variant in ("a", "b"):
            (reports / f"resident-{variant}.json").write_text(
                json.dumps(resident_source, ensure_ascii=False) + "\n")
        expect_fail("高位址來源 byte 竄改", current)
        for variant in ("a", "b"):
            shutil.copy2(args.reports / f"resident-{variant}.json",
                         reports / f"resident-{variant}.json")
        control = reports / "writer-v4-control.json"
        data = json.loads(control.read_bytes())
        data["samples"]["1300m"]["memory_sha256"] = "0" * 64
        control.write_text(json.dumps(data))
        expect_fail("無監看控制 RAM 分歧", current)
        shutil.copy2(args.reports / control.name, control)
        bad_fixture = root / "bad-inputs.json"
        bad_fixture.write_bytes(args.fixture.read_bytes() + b" ")
        expect_fail("錯玩家輸入", lambda: check(args.game, args.inputs, bad_fixture, reports))
        bad_game = root / "bad-game"
        bad_game.mkdir()
        for name in (*FILE_SHA, "MENU.TXT"):
            if name == "GAME.TXT":
                source = (args.game / name).read_bytes()
                (bad_game / name).write_bytes(source[:-1] + bytes((source[-1] ^ 1,)))
            else:
                (bad_game / name).symlink_to(args.game / name)
        expect_fail("錯原版 GAME.TXT", lambda: check(bad_game, args.inputs, args.fixture, reports))
        assert check(root / "missing-game", args.inputs, args.fixture, reports)["result"] == "SKIP"
        print("PASS", "缺原版 SKIP 77")


if __name__ == "__main__":
    main()
