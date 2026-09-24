#!/usr/bin/env python3
"""目標107獨立驗證器的缺原版與破損收據反例。"""

import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from check_goal107_post_caption import check, main as check_main


def change_json(raw, mutate):
    report = json.loads(raw)
    mutate(report)
    return json.dumps(report, ensure_ascii=False, sort_keys=True).encode()


def reject(game, inputs, reports, replacements, expected):
    with tempfile.TemporaryDirectory(prefix="goal107-negative-", dir=reports.parent) as temp:
        fixture = Path(temp)
        for source in reports.iterdir():
            if source.is_file():
                (fixture / source.name).symlink_to(source.resolve())
        for name, mutate in replacements.items():
            target = fixture / name
            data = mutate(target.read_bytes())
            target.unlink()
            target.write_bytes(data)
        try:
            check(game, inputs, fixture)
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError(f"拒絕原因不符：{error}") from error
        else:
            raise AssertionError(f"破損收據未被拒絕：{list(replacements)}")


def main(args):
    assert check(args.game, args.inputs, args.reports)["result"] == "PASS"
    missing = args.game / "missing-original"
    assert check(missing, args.inputs, args.reports)["result"] == "SKIP"
    with tempfile.TemporaryDirectory(prefix="goal107-skip-", dir=args.reports.parent) as temp:
        output = Path(temp) / "skip.json"
        assert check_main(SimpleNamespace(game=missing, inputs=args.inputs,
                                          reports=args.reports, output=output)) == 77
        assert not output.exists()
    report_a = "england-no-extra-500m-a.json"
    report_b = "england-no-extra-500m-b.json"
    reject(args.game, args.inputs, args.reports,
           {report_a: lambda raw: change_json(raw, lambda d: d.update(version="wrong")),
            report_b: lambda raw: change_json(raw, lambda d: d.update(version="wrong"))},
           "500M 版本")
    reject(args.game, args.inputs, args.reports,
           {"england-no-extra-500m-a.430m.idx":
            lambda raw: bytes([raw[0] ^ 1]) + raw[1:]},
           "原始 idx 不符")
    def change_print(report):
        event = next(item for item in report["print_reads"]
                     if item["step"] == 427_644_076)
        event["value"] ^= 1
    reject(args.game, args.inputs, args.reports,
           {report_a: lambda raw: change_json(raw, change_print),
            report_b: lambda raw: change_json(raw, change_print)},
           "實際印字內容雜湊不符")
    reject(args.game, args.inputs, args.reports,
           {"england-no-extra-500m-control.json":
            lambda raw: change_json(raw, lambda d: d["samples"]["430m"].update(
                memory_sha256="0" * 64))},
           "觀測器改變原版狀態：samples")
    reject(args.game, args.inputs, args.reports,
           {report_a: lambda raw: change_json(raw, lambda d: d["key_events"][1].update(
                pending=1)),
            report_b: lambda raw: change_json(raw, lambda d: d["key_events"][1].update(
                pending=1))},
           "觀測器改變原版狀態：key_events")
    reject(args.game, args.inputs, args.reports,
           {"england-no-extra-1350m-explore.1200m.idx":
            lambda raw: bytes([raw[0] ^ 1]) + raw[1:]},
           "原始 idx 不符")
    def change_late_print(report):
        event = next(item for item in report["print_reads"]
                     if item["step"] == 536_921_911)
        event["value"] ^= 1
    reject(args.game, args.inputs, args.reports,
           {"england-no-extra-1350m-explore.json":
            lambda raw: change_json(raw, change_late_print),
            "england-no-extra-1350m-b.json":
            lambda raw: change_json(raw, change_late_print)},
           "實際印字內容雜湊不符")
    print("PASS：正常收據、缺原版 SKIP、錯版、畫布、印字、控制與鍵盤反例")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    main(parser.parse_args())
