#!/usr/bin/env python3
"""審查首張字幕的原版 VGA／底圖相位及正式覆蓋守門候選。"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
SOURCE_SHA = "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6"
PREPRINT_SHA = "d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab"
SCREEN_SHA = "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"
PALETTE_SHA = "92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b"
NEXT_SHA = "69859c61c490112c333982957339c23f09df22f2e2918ca881c44d8911dc54c3"
KEY = "GAME.TXT:0x000153CC"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def candidate(event, writes, bbox, before_sha, canvas_sha, indexed_sha,
              palette_sha, mode, translation, mask_ok):
    """限定 READY 審查候選；只有規格升 READY 後才可進正式適配器。"""
    return (event and writes == 1040 and bbox == [16, 30, 303, 39]
            and before_sha == PREPRINT_SHA and canvas_sha == SCREEN_SHA
            and indexed_sha == SCREEN_SHA and palette_sha == PALETTE_SHA
            and mode == 0x13 and bool(translation) and mask_ok)


def verify_reports(a, b, control, game, inputs, catalog, before, reports):
    need(sha(game) == GAME_SHA and sha(inputs) == INPUT_SHA,
         "原版 GAME.TXT 或正常玩家輸入版本不符")
    source = game[0x153ce:0x1540b]
    need(len(source) == 61 and sha(source) == SOURCE_SHA
         and game[0x153cc:0x153ce] == b"^^", "原版字幕來源不符")
    rows = [row for row in csv.DictReader(catalog.splitlines(), delimiter="\t")
            if row["candidate_id"] == KEY]
    need(len(rows) == 1, "TSV 字幕鍵缺失或重複")
    row = rows[0]
    need(row["source_file"] == "GAME.TXT" and row["source_sha256"] == GAME_SHA
         and row["byte_offset"] == "0x000153CC" and row["source_byte_length"] == "63"
         and row["source_bytes_sha256"] == sha(game[0x153cc:0x1540b])
         and row["status"] == "draft" and row["zh_hant"].startswith("^^")
         and row["zh_hant"].count("^") == 2 and len(row["zh_hant"]) > 2,
         "TSV 來源、控制碼或譯文不符")
    need(len(before) == 64000 and sha(before) == PREPRINT_SHA,
         "原版印前多色底圖不符")
    need(a == b and not a["control"] and control["control"],
         "兩次冷啟動或無監看控制旗標不符")
    need(a["version"] == control["version"] == "goal130-caption-screen-audit-v2"
         and a["input_sha256"] == control["input_sha256"] == INPUT_SHA
         and a["input_hashes"] == control["input_hashes"]
         and a["opened"] == control["opened"]
         and a["samples"] == control["samples"],
         "原版 CPU／完整 RAM／畫面／色盤／時間／開檔同狀態不符")
    samples = a["samples"]
    need(len(samples) == 34 and samples["85m"]["canvas_sha256"] != SCREEN_SHA,
         "取樣清單或初始相位不符")
    for moment in (90, 95, 175, 195):
        sample = samples[f"{moment}m"]
        need(sample["canvas_sha256"] == sample["indexed_sha256"] == SCREEN_SHA
             and sample["palette_sha256"] == PALETTE_SHA,
             f"{moment}M 字幕實際 VGA 畫面不符")
    for moment in (200, 205, 210):
        sample = samples[f"{moment}m"]
        need(sample["canvas_sha256"] == sample["indexed_sha256"] == NEXT_SHA,
             f"{moment}M 離頁未失效")
    for name in ("operands-a", "operands-b", "operands-control"):
        for label, sample in samples.items():
            for suffix, key in (("canvas", "canvas_sha256"),
                                ("idx", "indexed_sha256"), ("pal", "palette_sha256")):
                path = reports / f"{name}.{label}.{suffix}"
                need(path.is_file() and sha(path.read_bytes()) == sample[key],
                     f"原版取樣實檔不符：{name}/{label}/{suffix}")
    after = (reports / "operands-a.90m.canvas").read_bytes()
    changed = [(i % 320, i // 320, after[i]) for i in range(64000)
               if before[i] != after[i]]
    need(len(changed) == 1040 and
         [min(x for x, _, _ in changed), min(y for _, y, _ in changed),
          max(x for x, _, _ in changed) + 1, max(y for _, y, _ in changed) + 1]
         == [16, 30, 303, 39] and {color for _, _, color in changed} == {14, 47, 54},
         "原版印前／印後多色畫素不符")
    audit = a["caption_frame_audit"]
    screen = a["caption_screen_audit"]
    control_screen = control["caption_screen_audit"]
    reads = [x for x in a["print_reads"]
             if 88600000 <= x["step"] < 88900000 and x["cs_ip"] == "0D21:00C6"]
    operands = screen["read_operands"]
    expected = [(0x2a560 if i % 2 == 0 else 0x2a561,
                 source[i // 2] if i % 2 == 0 else 0) for i in range(122)]
    need(len(reads) == len(operands) == 122 and
         [(x["linear"], x["value"]) for x in reads] == expected and
         [(x["linear"], x["value"]) for x in operands] == expected and
         all(x["ss_bx_linear"] == x["linear"] and x["step"] == reads[i]["step"]
             for i, x in enumerate(operands)),
         "122 筆真印字讀取與 SS:BX 指令前運算元不符")
    need(screen["first_read_canvas_sha256"] == screen["first_write_canvas_sha256"] == PREPRINT_SHA
         and screen["safe_logical"] == [12, 27, 307, 42]
         and screen["indexed_mismatch_frames"] == screen["safe_mismatch_frames"] == 6
         and screen["first_safe_mismatch_step"] == 88770000
         and screen["last_safe_mismatch_step"] == 89595000,
         "原版 VGA 早於底層畫布穩定的6幀差異不符")
    need(audit["source_sha256"] == SOURCE_SHA and audit["read_match_bytes"] == 61
         and audit["read_mismatches"] == 0 and audit["write_count"] == 1040
         and audit["write_bbox"] == [16, 30, 303, 39]
         and audit["frames"] == 757 and audit["signature_frames"] == 647
         and audit["eligible_frames"] == 641
         and [(x["event"], x["step"], x["frames"]) for x in audit["transitions"]]
         == [("ready", 89760000, 544), ("expired", 195525000, 1185)]
         and audit["phase_at_end"] == "expired",
         "真正 VGA 螢幕的字幕啟用／離頁逐幀相位不符")
    need(control_screen["safe_mismatch_frames"] == 6
         and control_screen["indexed_mismatch_frames"] == 6
         and control["caption_frame_audit"]["eligible_frames"] == 0
         and control["caption_frame_audit"]["transitions"] == [],
         "無讀寫監看控制的 VGA 同步相位不符")
    need(candidate(True, 1040, [16, 30, 303, 39], PREPRINT_SHA,
                   SCREEN_SHA, SCREEN_SHA, PALETTE_SHA, 0x13,
                   row["zh_hant"][2:], True), "完整正例被拒絕")
    return {"result": "PASS", "scope": "@BUILD1 固定原版 READY 審查證據，非正式覆蓋",
            "first_safe_frame": 544, "first_safe_step": 89760000,
            "safe_frames": 641, "exit_frame": 1185,
            "report_sha256": sha((reports / "operands-a.json").read_bytes())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, default=Path("/game/GAME.TXT"))
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--preprint", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    paths = ([a.game, a.inputs, a.catalog, a.preprint] +
             [a.reports / f"operands-{name}.json" for name in ("a", "b", "control")])
    if not all(path.is_file() for path in paths):
        print(json.dumps({"result": "SKIP", "reason": "合法原版或本機逐幀收據缺失"}, ensure_ascii=False))
        raise SystemExit(77)
    reports = [json.loads((a.reports / f"operands-{name}.json").read_bytes())
               for name in ("a", "b", "control")]
    result = verify_reports(*reports, a.game.read_bytes(), a.inputs.read_bytes(),
                            a.catalog.read_text(encoding="utf-8"),
                            a.preprint.read_bytes(), a.reports)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
