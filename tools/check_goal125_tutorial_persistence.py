#!/usr/bin/env python3
"""獨立核對教學選項真玩家退出、DOS 暫存層及跨次冷啟動。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA
from check_goal123_retire_route import EXTRA_FILES


PROBE_SHA = "a279704294eed71e7331a1e6cf227553877b7ca157574c239698a5afff6b6486"
FIXTURES = {
    "none": ("goal125-untouched-retire.inputs.json",
             "673e993f1618992c5ea4bc7bcd83cdd73ad9eba022aba3cc6082847d23506cdb",
             21, 1_601_103_496, "1350m", 47),
    "once": ("goal125-toggle-once-retire.inputs.json",
             "1a1ceca23621176f56bd48320da5336bd0c98955b51c29f76b3fc584dd9c031f",
             24, 1_601_103_503, "1350m", 149),
    "twice": ("goal125-toggle-twice-retire.inputs.json",
              "d96ef260e11232c9cf4bda61cf2f230b14a812c36bc27c6c50b00842c9131a90",
              27, 1_626_215_180, "1375m", 47),
}
SCRATCH = {
    "COLONY09.SAV": "52bfd407b7c3b0a0cfce9362a0b352d1e7296b3ee85f715e4b904703064e3696",
    "HALLFAME.DAT": "886a85752b852d15ffdd1b689eb0c8c72b653c2e1f7a6af3f4b0844371a00838",
}
CONTROL_FIELDS = ("route", "sources", "transfers", "samples", "opened",
                  "key_events", "game_inputs", "input_hashes", "write_intents")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def check_scratch(path):
    need(path.is_dir() and {p.name for p in path.iterdir()} == set(SCRATCH),
         f"暫存層檔案清單不符：{path}")
    for name, digest in SCRATCH.items():
        need(sha((path / name).read_bytes()) == digest,
             f"暫存檔案雜湊不符：{path.name}/{name}")


def check_frames(prefix, samples):
    for label, sample in samples.items():
        for suffix, field, length in (("idx", "indexed_sha256", 64000),
                                      ("canvas", "canvas_sha256", 64000),
                                      ("pal", "palette_sha256", 768)):
            data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
            need(len(data) == length and sha(data) == sample[field],
                 f"原版畫面實檔不符：{prefix.name}/{label}.{suffix}")


def icon(path, sample):
    data = Path(f"{path}.{sample}.idx").read_bytes()
    return tuple(data[y * 320 + x] for x, y in
                 ((73, 148), (74, 148), (73, 149), (74, 149)))


def printed_bytes(report):
    return bytes(e["value"] for e in report["print_reads"] if e["value"])


def check(game, inputs, fixtures, source, reports, output=None):
    originals = {**FILE_SHA, "MENU.TXT": MENU_SHA, **EXTRA_FILES}
    if not inputs.is_file() or not all((game / n).is_file() for n in originals):
        return {"result": "SKIP", "reason": "合法 DOS 原版或固定開局輸入缺失"}
    if output is not None:
        need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
             "輸出目錄不存在或擁有者不符")
    for name, digest in originals.items():
        need(sha((game / name).read_bytes()) == digest, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "開局玩家輸入版本不符")
    need(sha(source.read_bytes()) == PROBE_SHA, "dosgolem 玩家探針版本不符")
    need(not (game / "COLONY09.SAV").exists() and
         not (game / "HALLFAME.DAT").exists(),
         "原版 Root 混入目標125實驗暫存檔")

    receipts = {}
    restarts = {}
    start_same = None
    for branch, (fixture, fixture_sha, count, terminal_step, label, color) in FIXTURES.items():
        need(sha((fixtures / fixture).read_bytes()) == fixture_sha,
             branch + " 玩家事件版本不符")
        reports_for_branch = {}
        for phase in ("", "restart-"):
            prefix = phase + branch
            paths = [reports / f"{prefix}-{variant}.json"
                     for variant in ("a", "b", "control")]
            a_bytes, b_bytes = paths[0].read_bytes(), paths[1].read_bytes()
            need(a_bytes == b_bytes, f"{prefix} 兩次冷啟動 JSON 不同")
            a, control = json.loads(a_bytes), read_json(paths[2])
            expected_version = ("goal110-game-input-audit-v1" if phase else
                                "goal123-retire-terminal-v1")
            expected_until = 1_400_000_000 if phase else (
                1_675_000_000 if branch == "twice" else 1_650_000_000)
            expected_fixture = ("goal111-first-row-only.inputs.json" if phase else fixture)
            expected_hash = sha((fixtures / expected_fixture).read_bytes())
            for report, is_control in ((a, False), (control, True)):
                need(report["version"] == expected_version and
                     report["control"] is is_control and report["scratch"] is True and
                     report["nation"] == "england" and report["next_enter"] is True and
                     report["after_b"] == report["after_follow"] == "enter" and
                     report["follow_until"] == expected_until and
                     report["input_sha256"] == INPUT_SHA and
                     report["game_inputs_sha256"] == expected_hash and
                     report["input_hashes"]["MENU.TXT"] == MENU_SHA,
                     f"{prefix} 報告版本、原版或事件輸入不符")
                if phase:
                    need("game_terminal" not in report and
                         len(report["opened"]) == 95 and
                         report["samples"]["1400m"]["step"] == 1_400_000_000,
                         f"{prefix} 第二次開局未到固定選項頁")
                else:
                    need(report["game_terminal"] == {
                        "observed": True, "step": terminal_step,
                        "dos_exited": True, "cpu_halted": True,
                        "events_delivered": count, "events_total": count,
                    } and len(report["opened"]) == 99,
                         f"{prefix} 不是預期的原版正常退出")
                need({w["Name"] for w in report["write_intents"]} ==
                     ({"COLONY09.SAV"} if phase else
                      {"COLONY09.SAV", "HALLFAME.DAT"}),
                     f"{prefix} 出現未登錄的原版寫檔意圖")
            need(not control["print_reads"] and not control["writers"],
                 f"{prefix} 無監看控制仍收錄印字或畫布觀測")
            for field in CONTROL_FIELDS:
                need(a[field] == control[field],
                     f"{prefix} 無監看控制原版狀態不同：{field}")
            if not phase:
                need(a["game_terminal"] == control["game_terminal"],
                     branch + " 退出旗標與控制不同")
            check_scratch(reports / f"{prefix}-a-scratch")
            check_scratch(reports / f"{prefix}-b-scratch")
            check_scratch(reports / f"{prefix}-control-scratch")
            for variant in ("a", "b", "control"):
                check_frames(reports / f"{prefix}-{variant}", a["samples"])
            need(b"carrying a pioneer" not in printed_bytes(a),
                 f"{prefix} 已命中首則 help，需另建中文顯示驗收")
            if phase:
                need(icon(reports / f"{prefix}-a", "1400m") == (47,) * 4,
                     f"{prefix} 第二次開局教學圖示不是固定初始狀態")
                restarts[branch] = a_bytes
            else:
                need(icon(reports / f"{prefix}-a", label) == (color,) * 4,
                     f"{prefix} 當局教學點選沒有預期的同焦點圖示")
                before = a["samples"]["1300m"]
                if start_same is None:
                    start_same = before
                else:
                    need(before == start_same, "三支教學操作前不是同一原版狀態")
                receipts[branch] = sha(a_bytes)
            reports_for_branch[phase or "first"] = a
    need(len(set(restarts.values())) == 1,
         "三支第二局原版完整報告沒有逐位元組合流")
    result = {
        "result": "PASS",
        "scope": "固定英格蘭正常玩家路徑：教學選項未點／點一次／點兩次，退休退出後再冷啟動新局",
        "first_receipt_sha256": receipts,
        "restart_receipt_sha256": sha(next(iter(restarts.values()))),
        "scratch_file_sha256": SCRATCH,
        "finding": "三支退出後暫存檔逐 byte 相同，第二局同輸入完整報告逐 byte 相同；固定觀測點未見首則 help",
        "limitation": "只限 Retire→下一次開新局；不能排除載入存檔、其他新局入口或檢查點間瞬時畫面",
    }
    if output is not None:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--source", type=Path, default=Path(__file__).parent / "probe_goal098_intro.go")
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures, args.source, args.reports, args.output)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(1, f"FAIL：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(77 if result["result"] == "SKIP" else 0)
