#!/usr/bin/env python3
"""獨立核對三國介紹 B 頁留置、離頁和無觀測控制收據。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal101_nation_intro import EXPECTED, FILE_SHA, INPUT_SHA


NATIONS = {
    "england": "ENGLND1.SS",
    "spain": "SPAIN1.SS",
    "netherlands": "DUTCH1.SS",
}
LABELS = ("75m", "80m", "85m")
SUFFIXES = (("idx", "indexed_sha256", 64000),
            ("canvas", "canvas_sha256", 64000),
            ("pal", "palette_sha256", 768))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def raw_samples(prefix, record):
    for label in LABELS:
        sample = record["samples"][label]
        need(sample["step"] == int(label[:-1]) * 1_000_000,
             f"{prefix.name}/{label}: 虛擬步數不符")
        for suffix, field, size in SUFFIXES:
            raw = Path(f"{prefix}.{label}.{suffix}").read_bytes()
            need(len(raw) == size and sha(raw) == sample[field],
                 f"{prefix.name}/{label}: 原始 {suffix} 與報告不符")


def check(game, inputs, reports, baseline):
    if not game.is_dir() or not inputs.is_file():
        return {"result": "SKIP", "reason": "原版遊戲或固定玩家輸入缺失"}
    for name, expected in FILE_SHA.items():
        need(sha((game / name).read_bytes()) == expected,
             f"原版檔案版本不符：{name}")
    need(sha(inputs.read_bytes()) == INPUT_SHA, "固定玩家輸入版本不符")
    result = []
    for nation, following_asset in NATIONS.items():
        old = load(baseline / f"{nation}-a.json")
        b_sample = old["samples"]["75m"]
        need(b_sample["indexed_sha256"] == EXPECTED[nation][1][4],
             f"{nation}: 原版 B 頁基準不符")
        old_prefix = baseline / f"{nation}-a"
        for suffix, field, size in SUFFIXES:
            old_raw = Path(f"{old_prefix}.75m.{suffix}").read_bytes()
            need(len(old_raw) == size and sha(old_raw) == b_sample[field],
                 f"{nation}: 已驗 B 頁原始 {suffix} 不符")
        branches = {}
        for action in ("wait", "enter", "esc"):
            prefix = reports / f"{nation}-{action}"
            a_bytes = Path(f"{prefix}-a.json").read_bytes()
            b_bytes = Path(f"{prefix}-b.json").read_bytes()
            need(a_bytes == b_bytes,
                 f"{nation}/{action}: 兩次冷啟動報告不同")
            observed = json.loads(a_bytes)
            control = load(Path(f"{prefix}-control.json"))
            need(observed["version"] == control["version"] == "goal104-intro-exit-v1" and
                 observed["nation"] == control["nation"] == nation and
                 observed["after_b"] == control["after_b"] == action and
                 observed["next_enter"] is control["next_enter"] is True and
                 observed["control"] is False and control["control"] is True and
                 observed["input_sha256"] == control["input_sha256"] == INPUT_SHA and
                 observed["input_hashes"] == control["input_hashes"] == FILE_SHA and
                 all(observed[key] == control[key]
                     for key in ("route", "sources", "transfers", "samples", "opened")) and
                 not control["print_reads"] and not control["writers"],
                 f"{nation}/{action}: 無觀測控制的 CPU、RAM、虛擬時間或流程不同")
            need(observed["samples"]["75m"] == b_sample and
                 observed["opened"][:55] == old["opened"],
                 f"{nation}/{action}: B 頁共同起點不符")
            need(all(observed["samples"]["80m"][field] ==
                     observed["samples"]["85m"][field]
                     for _, field, _ in SUFFIXES),
                 f"{nation}/{action}: 80M–85M 畫面不穩定")
            for suffix in ("a", "b", "control"):
                raw_samples(Path(f"{prefix}-{suffix}"),
                            observed if suffix != "control" else control)
            for label in LABELS:
                for suffix, _, _ in SUFFIXES:
                    source = Path(f"{prefix}-a.{label}.{suffix}").read_bytes()
                    need(source == Path(f"{prefix}-b.{label}.{suffix}").read_bytes() ==
                         Path(f"{prefix}-control.{label}.{suffix}").read_bytes(),
                         f"{nation}/{action}/{label}: 雙重播或控制原始畫布不同")
                    if label == "75m":
                        need(source == Path(f"{old_prefix}.75m.{suffix}").read_bytes(),
                             f"{nation}/{action}: 原始 B 頁共同起點不符")
            need(all(75_000_000 <= item["step"] < 85_000_000
                     for item in observed["print_reads"] if item["step"] >= 75_000_000),
                 f"{nation}/{action}: 離頁印字時間窗不符")
            branches[action] = observed
        waiting = branches["wait"]
        b_hash = b_sample["indexed_sha256"]
        need(not any(key.startswith("after-b/") for key in waiting["writers"]) and
             not any(item["step"] >= 75_000_000 for item in waiting["print_reads"]) and
             all(waiting["samples"][label]["indexed_sha256"] == b_hash and
                 waiting["samples"][label]["opened_count"] == 55
                 for label in ("80m", "85m")),
             f"{nation}: 無輸入不應自行離開 B 頁")
        enter, esc = branches["enter"], branches["esc"]
        follow = enter["samples"]["85m"]["indexed_sha256"]
        need(follow != b_hash and
             all(enter["samples"][label][field] == esc["samples"][label][field]
                 for label in ("80m", "85m")
                 for field in ("indexed_sha256", "canvas_sha256", "palette_sha256")) and
             all(enter["samples"]["80m"][field] ==
                 enter["samples"]["85m"][field]
                 for field in ("indexed_sha256", "canvas_sha256", "palette_sha256")) and
             enter["samples"]["85m"]["memory_sha256"] !=
             esc["samples"]["85m"]["memory_sha256"],
             f"{nation}: Enter／ESC 的可見頁面或內部差異不符")
        for action, record in (("enter", enter), ("esc", esc)):
            clear = record["writers"].get("after-b/0C9F:00CA", {})
            print_ink = record["writers"].get("after-b/0D21:012C", {})
            need(record["opened"][-5:] ==
                 ["KINGLSS1.PIK", following_asset, "KING1.SS", "FONTKING.FF", "GAME.TXT"] and
                 all(record["samples"][label]["opened_count"] == 60
                     for label in ("80m", "85m")) and
                 clear.get("count") == 64000 and clear.get("bbox") == [0, 0, 320, 200] and
                 print_ink.get("count", 0) > 0 and
                 75_000_000 <= clear["first_step"] < clear["last_step"] < 80_000_000 and
                 75_000_000 <= print_ink["first_step"] < print_ink["last_step"] < 80_000_000,
                 f"{nation}/{action}: 後續畫面的開檔、清屏或印字事件不符")
        result.append({"nation": nation, "b_indexed_sha256": b_hash,
                       "following_indexed_sha256": follow,
                       "enter_esc_memory_equal": False,
                       "wait_report_sha256": sha((reports / f"{nation}-wait-a.json").read_bytes()),
                       "enter_report_sha256": sha((reports / f"{nation}-enter-a.json").read_bytes()),
                       "esc_report_sha256": sha((reports / f"{nation}-esc-a.json").read_bytes())})
    return {"result": "PASS", "scope": "英、西、荷三國 B 頁留置及 Enter／ESC 離頁",
            "input_sha256": INPUT_SHA, "file_sha256": FILE_SHA,
            "nations": result,
            "limitations": "僅原版正常玩家路徑的離頁守門證據；按鍵內部狀態不同，未驗中文長文覆蓋"}


def main(args):
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    receipt = check(args.game, args.inputs, args.reports, args.baseline)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(receipt["result"] + "：" + receipt.get("scope", receipt.get("reason", "")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
