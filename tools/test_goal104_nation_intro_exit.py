#!/usr/bin/env python3
"""目標104收據的錯版、錯相位與原始畫布負例。"""

import argparse
import json
import tempfile
from pathlib import Path

from check_goal104_nation_intro_exit import check


def need_rejection(game, inputs, reports, baseline, filename, mutate, expected):
    with tempfile.TemporaryDirectory(prefix="goal104-negative-", dir=reports.parent) as temporary:
        fixture = Path(temporary)
        for source in reports.iterdir():
            if source.is_file():
                (fixture / source.name).symlink_to(source.resolve())
        target = fixture / filename
        original = target.read_bytes()
        target.unlink()
        target.write_bytes(mutate(original))
        try:
            check(game, inputs, fixture, baseline)
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError(f"拒絕理由不符：{error}") from error
        else:
            raise AssertionError(f"錯誤收據未被拒絕：{filename}")


def mutate_json(raw, key, value):
    record = json.loads(raw)
    record[key] = value
    return json.dumps(record, ensure_ascii=False).encode()


def main(args):
    assert check(args.game, args.inputs, args.reports, args.baseline)["result"] == "PASS"
    assert check(args.game / "missing-original", args.inputs, args.reports,
                 args.baseline)["result"] == "SKIP"
    need_rejection(args.game, args.inputs, args.reports, args.baseline,
                   "england-enter-a.json",
                   lambda raw: mutate_json(raw, "version", "unknown-version"),
                   "兩次冷啟動報告不同")
    need_rejection(args.game, args.inputs, args.reports, args.baseline,
                   "spain-esc-control.json",
                   lambda raw: mutate_json(raw, "version", "unknown-version"),
                   "無觀測控制")
    need_rejection(args.game, args.inputs, args.reports, args.baseline,
                   "netherlands-wait-a.75m.idx",
                   lambda raw: bytes([raw[0] ^ 1]) + raw[1:],
                   "原始 idx 與報告不符")
    print("PASS：正常收據、原版缺失 SKIP、錯版及畫布位元錯誤失敗即關閉")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    main(parser.parse_args())
