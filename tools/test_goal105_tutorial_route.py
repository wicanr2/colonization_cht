#!/usr/bin/env python3
"""目標105收據的錯版、壞畫布及印字串改動負例。"""

import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from check_goal105_tutorial_route import check, main as check_main


def reject(game, inputs, reports, baseline, replacements, expected):
    with tempfile.TemporaryDirectory(prefix="goal105-negative-", dir=reports.parent) as temporary:
        fixture = Path(temporary)
        for source in reports.iterdir():
            if source.is_file():
                (fixture / source.name).symlink_to(source.resolve())
        for name, mutate in replacements.items():
            target = fixture / name
            raw = target.read_bytes()
            target.unlink()
            target.write_bytes(mutate(raw))
        try:
            check(game, inputs, fixture, baseline)
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError(f"拒絕理由不符：{error}") from error
        else:
            raise AssertionError(f"錯誤收據未被拒絕：{list(replacements)}")


def change_field(raw, field, value):
    report = json.loads(raw)
    report[field] = value
    return json.dumps(report, ensure_ascii=False).encode()


def change_print(raw):
    report = json.loads(raw)
    target = next(event for event in report["print_reads"]
                  if event["step"] >= 85_000_000 and event["cs_ip"] == "0D21:00C6")
    target["value"] = ord("X")
    return json.dumps(report, ensure_ascii=False, sort_keys=True).encode()


def main(args):
    assert check(args.game, args.inputs, args.reports, args.baseline)["result"] == "PASS"
    assert check(args.game / "missing-original", args.inputs, args.reports,
                 args.baseline)["result"] == "SKIP"
    with tempfile.TemporaryDirectory(prefix="goal105-skip-", dir=args.reports.parent) as temporary:
        output = Path(temporary) / "skip.json"
        assert check_main(SimpleNamespace(game=args.game / "missing-original",
                                          inputs=args.inputs, reports=args.reports,
                                          baseline=args.baseline, output=output)) == 77
        assert not output.exists()
    reject(args.game, args.inputs, args.reports, args.baseline,
           {"england-enter-v4-control.json":
            lambda raw: change_field(raw, "version", "wrong-version")},
           "觀測／無觀測控制")
    reject(args.game, args.inputs, args.reports, args.baseline,
           {"england-esc-v4-a.90m.idx":
            lambda raw: bytes([raw[0] ^ 1]) + raw[1:]},
           "原始 idx 與 JSON 不符")
    reject(args.game, args.inputs, args.reports, args.baseline,
           {"england-enter-v4-a.json": change_print,
            "england-enter-v4-b.json": change_print},
           "當次實際印字不是 @BUILD1 字幕")
    print("PASS：正常收據、原版缺失 SKIP、錯版、畫布破損與改字失敗即關閉")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    main(parser.parse_args())
