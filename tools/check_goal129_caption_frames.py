#!/usr/bin/env python3
"""核對 @BUILD1 當次印字、逐幀生命週期及無監看原版控制；非正式覆蓋。"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
SOURCE_SHA = "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6"
PREPRINT_SHA = "d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab"
CAPTION_SHA = "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"
PALETTE_SHA = "92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b"
NEXT_SHA = "69859c61c490112c333982957339c23f09df22f2e2918ca881c44d8911dc54c3"
KEY = "GAME.TXT:0x000153CC"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def eligible(event, writes, bbox, mode, canvas_sha, palette_sha, translation):
    """DRAFT 守門候選；真視窗尚未接此函式。"""
    return (event and writes == 1040 and bbox == [16, 30, 303, 39]
            and mode == 0x13 and canvas_sha == CAPTION_SHA
            and palette_sha == PALETTE_SHA and bool(translation))


def validate(a, b, control, game, inputs, catalog, preprint, reports):
    need(digest(game) == GAME_SHA and digest(inputs) == INPUT_SHA,
         "原版 GAME.TXT 或玩家輸入版本不符")
    source = game[0x153ce:0x1540b]
    need(len(source) == 61 and digest(source) == SOURCE_SHA
         and game[0x153cc:0x153ce] == b"^^", "字幕來源位移或 bytes 不符")
    rows = [row for row in csv.DictReader(catalog.splitlines(), delimiter="\t")
            if row["candidate_id"] == KEY]
    need(len(rows) == 1, "字幕來源鍵缺失或重複")
    row = rows[0]
    translation = row["zh_hant"]
    need(row["source_file"] == "GAME.TXT" and row["source_sha256"] == GAME_SHA
         and row["byte_offset"] == "0x000153CC"
         and row["source_byte_length"] == "63"
         and row["source_bytes_sha256"] == digest(game[0x153cc:0x1540b])
         and row["status"] == "draft" and translation.startswith("^^")
         and translation.count("^") == 2 and len(translation) > 2,
         "字幕 TSV 譯文、控制碼或版本不符")
    need(digest(preprint) == PREPRINT_SHA and len(preprint) == 64000,
         "字幕原版印前底圖不符")
    need(a == b and a["control"] is False and control["control"] is True,
         "兩次冷啟動或無監看控制旗標不符")
    need(a["version"] == b["version"] == control["version"] ==
         "goal129-caption-frame-audit-v1", "探針版本不符")
    need(a["input_sha256"] == control["input_sha256"] == INPUT_SHA
         and a["input_hashes"] == control["input_hashes"]
         and a["opened"] == control["opened"]
         and a["samples"] == control["samples"],
         "原版 CPU／完整 RAM／畫布／索引／色盤／時間／開檔同狀態失敗")
    samples = a["samples"]
    need(len(samples) == 34 and samples["85m"]["canvas_sha256"] != CAPTION_SHA
         and all(samples[f"{at}m"]["canvas_sha256"] == CAPTION_SHA
                 and samples[f"{at}m"]["palette_sha256"] == PALETTE_SHA
                 for at in (90, 95, 175, 195))
         and all(samples[f"{at}m"]["canvas_sha256"] == NEXT_SHA
                 for at in (200, 205, 210)),
         "原版畫面取樣相位不符")
    for name in ("observed-a", "observed-b", "control"):
        for label, sample in samples.items():
            for suffix, key in (("canvas", "canvas_sha256"),
                                ("idx", "indexed_sha256"), ("pal", "palette_sha256")):
                path = reports / f"{name}.{label}.{suffix}"
                need(path.is_file() and digest(path.read_bytes()) == sample[key],
                     f"原版取樣檔與 JSON 不符：{name}/{label}/{suffix}")
    after = (reports / "observed-a.90m.canvas").read_bytes()
    changed = [i for i, (old, new) in enumerate(zip(preprint, after)) if old != new]
    need(len(changed) == 1040 and
         [min(i % 320 for i in changed), min(i // 320 for i in changed),
          max(i % 320 for i in changed) + 1, max(i // 320 for i in changed) + 1]
         == [16, 30, 303, 39], "當次原版畫布改色不符")
    reads = [x for x in a["print_reads"]
             if 88600000 <= x["step"] < 88900000 and x["cs_ip"] == "0D21:00C6"]
    expected = [(0x2a560 if i % 2 == 0 else 0x2a561,
                 source[i // 2] if i % 2 == 0 else 0)
                for i in range(2 * len(source))]
    need([(x["linear"], x["value"]) for x in reads] == expected,
         "61 字元與交錯零位的當次印字事件不符")
    audit = a["caption_frame_audit"]
    control_audit = control["caption_frame_audit"]
    need(audit["source_sha256"] == SOURCE_SHA and audit["read_start_step"] == 88689021
         and audit["read_end_step"] == 88754524 and audit["read_match_bytes"] == 61
         and audit["read_mismatches"] == 0 and audit["write_count"] == 1040
         and audit["write_bbox"] == [16, 30, 303, 39]
         and audit["write_first_step"] == 88689058
         and audit["write_last_step"] == 88754477,
         "當次讀字與畫布寫入計數不符")
    transitions = audit["transitions"]
    need(audit["phase_at_end"] == "expired" and audit["frames"] == 757
         and audit["eligible_frames"] == audit["signature_frames"] == 647
         and audit["signature_first_step"] == 88770000
         and audit["signature_last_step"] == 195360000
         and [(x["event"], x["step"], x["frames"]) for x in transitions]
         == [("ready", 88770000, 538), ("expired", 195525000, 1185)]
         and transitions[0]["canvas_sha256"] == CAPTION_SHA
         and transitions[0]["palette_sha256"] == PALETTE_SHA
         and transitions[1]["canvas_sha256"] != CAPTION_SHA,
         "逐幀首次可顯示或離頁失效不符")
    need(control_audit["frames"] == audit["frames"]
         and control_audit["signature_frames"] == audit["signature_frames"]
         and control_audit["signature_first_step"] == audit["signature_first_step"]
         and control_audit["signature_last_step"] == audit["signature_last_step"]
         and control_audit["eligible_frames"] == 0
         and control_audit["transitions"] == [],
         "無監看控制的畫面幀與觀測組不符")
    need(eligible(True, 1040, [16, 30, 303, 39], 0x13,
                  CAPTION_SHA, PALETTE_SHA, translation)
         and not eligible(False, 1040, [16, 30, 303, 39], 0x13,
                          CAPTION_SHA, PALETTE_SHA, translation),
         "DRAFT 守門基本正反例不符")
    return {"result": "PASS", "scope": "@BUILD1 DRAFT 原版逐幀證據，非正式中文覆蓋",
            "ready_step": 88770000, "expired_step": 195525000,
            "eligible_frames": 647, "original_state_control": "identical",
            "report_sha256": digest((reports / "observed-a.json").read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=Path("/game/GAME.TXT"))
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--preprint", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.game, args.inputs, args.catalog, args.preprint]
    paths += [args.reports / f"{name}.json" for name in ("observed-a", "observed-b", "control")]
    if not all(path.is_file() for path in paths):
        print(json.dumps({"result": "SKIP", "reason": "合法原版或本機收據缺失"}, ensure_ascii=False))
        raise SystemExit(77)
    reports = [json.loads((args.reports / f"{name}.json").read_bytes())
               for name in ("observed-a", "observed-b", "control")]
    result = validate(*reports, args.game.read_bytes(), args.inputs.read_bytes(),
                      args.catalog.read_text(encoding="utf-8"),
                      args.preprint.read_bytes(), args.reports)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
