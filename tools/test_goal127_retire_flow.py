#!/usr/bin/env python3
"""目標127獨立資料流檢查器的正反例；所有變造只在容器暫存目錄。"""

import argparse
import json
import tempfile
from pathlib import Path

from check_goal127_retire_flow import FILE_SHA, MENU_SHA, check


def reject(name, action):
    try:
        action()
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        print("PASS：拒絕" + name)
        return
    raise AssertionError(name + " 應拒絕")


def link_report_files(source, target):
    target.mkdir()
    for mode in ("flow", "resident"):
        for variant in ("a", "b", "control"):
            for suffix in ("json", "1275m.idx", "1275m.pal"):
                name = f"{mode}-{variant}.{suffix}"
                (target / name).symlink_to((source / name).resolve())


def replace_link(path, data):
    path.unlink()
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "inputs", "fixture", "reports"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="goal127-flow-") as temporary:
        top = Path(temporary)
        game = top / "game"
        game.mkdir()
        for name in (*FILE_SHA, "MENU.TXT"):
            (game / name).symlink_to((args.game / name).resolve())
        inputs, fixture = top / "inputs.json", top / "fixture.json"
        inputs.symlink_to(args.inputs.resolve())
        fixture.symlink_to(args.fixture.resolve())
        reports = top / "reports"
        link_report_files(args.reports, reports)

        def verify():
            return check(game, inputs, fixture, reports)

        assert verify()["result"] == "PASS"
        print("PASS：真原版與資料流雙重播")
        missing = top / "missing"
        missing.mkdir()
        assert check(missing, inputs, fixture, reports)["result"] == "SKIP"
        print("PASS：缺合法原版明示 SKIP 77")

        path = game / "GAME.TXT"
        raw = path.read_bytes()
        replace_link(path, raw[:0x122] + bytes([raw[0x122] ^ 1]) + raw[0x123:])
        reject("錯版 GAME.TXT", verify)
        path.unlink()
        path.symlink_to((args.game / "GAME.TXT").resolve())

        raw = fixture.read_bytes()
        replace_link(fixture, raw + b" ")
        reject("改變玩家輸入", verify)
        fixture.unlink()
        fixture.symlink_to(args.fixture.resolve())

        path = reports / "flow-b.json"
        replace_link(path, path.read_bytes() + b" ")
        reject("雙重播位元組不同", verify)
        path.unlink()
        path.symlink_to((args.reports / path.name).resolve())

        def mutate_pair(mode, change, name):
            original = json.loads((args.reports / f"{mode}-a.json").read_bytes())
            change(original)
            mutated = json.dumps(original, ensure_ascii=False, sort_keys=True).encode()
            paths = [reports / f"{mode}-{variant}.json" for variant in ("a", "b")]
            for item in paths:
                replace_link(item, mutated)
            reject(name, verify)
            for item in paths:
                item.unlink()
                item.symlink_to((args.reports / item.name).resolve())

        mutate_pair("flow", lambda data: data["retire_flow_reads"].pop(),
                    "來源讀取缺筆")
        mutate_pair("flow", lambda data: data["retire_flow_reads"].extend(
            data["retire_flow_reads"] * 4), "監看事件超限")
        mutate_pair("flow", lambda data: data["retire_flow_writes"].pop(),
                    "近端寫入缺筆")
        mutate_pair("resident", lambda data: data["retire_resident_writes"].pop(),
                    "高位址寫入缺筆")

        path = reports / "flow-control.json"
        data = json.loads(path.read_bytes())
        data["samples"]["1275m"]["memory_sha256"] = "0" * 64
        replace_link(path, json.dumps(data, sort_keys=True).encode())
        reject("無監看控制 RAM 變動", verify)
        path.unlink()
        path.symlink_to((args.reports / path.name).resolve())

        path = reports / "resident-a.1275m.idx"
        raw = path.read_bytes()
        replace_link(path, bytes([raw[0] ^ 1]) + raw[1:])
        reject("原版索引畫面變造", verify)

    print("PASS：目標127全部正反例")


if __name__ == "__main__":
    main()
