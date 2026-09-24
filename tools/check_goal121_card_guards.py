#!/usr/bin/env python3
"""獨立核對第三張卡滑鼠分欄遮擋、按放與移開的 dosgolem 收據。"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from check_goal120_third import load as load_baseline, validate as validate_baseline


INPUTS = {
    "title-cursor": ("95515a0df089ef09325c322925f7314789505876734fc2b83d816746a51d8d5f", 135),
    "title-only": ("634fe030424f2fee0138c930d0d5498c4f346a6382add11d68b0a1d27946e4fa", 132),
    "subtitle-cursor": ("bfc4543ae2909772c68d4eb7b4dd635c51791116aec12c47e27fbc173ec54734", 151),
}
RECTS = {"title": (29, 139, 84, 148), "subtitle": (38, 148, 76, 157)}
SNAPS = ("before-move", "before-press", "after-press", "click-settled", "before-away", "away-settled")
EXPECTED = {
    "title-cursor": ((67, 2), (67, 2), (62, 2), (62, 2)),
    "title-only": ((48, 0), (48, 0), (42, 0), (42, 0)),
    "subtitle-cursor": ((0, 26), (0, 26), (0, 23), (0, 23)),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def overlap(indexed, canvas, rect):
    require(len(indexed) == len(canvas) == 64000, "原始影像長度不符")
    x0, y0, x1, y1 = rect
    return sum(indexed[y * 320 + x] != canvas[y * 320 + x]
               for y in range(y0, y1) for x in range(x0, x1))


def validate(reports, inputs, images, baseline):
    result = {}
    for name, (want_sha, y) in INPUTS.items():
        events = inputs[name]
        require(sha(events) == want_sha, "固定滑鼠事件指紋不符：" + name)
        replay = json.loads(events)
        require(replay["end"] == 40000000 and len(replay["inputs"]) == 13 and
                [(e["step"], e["kind"], e["x"], e["y"]) for e in replay["inputs"][9:]] == [
                    (32000000, "move", 55, y), (33000000, "press", 0, 0),
                    (33800000, "release", 0, 0), (35000000, "move", 16, 16)],
                "滑鼠移入／按下／放開／移開事件不符：" + name)
        a, b, control = (reports[name + "-" + suffix] for suffix in ("a", "b", "control"))
        require(a == b and a["observed"] and not control["observed"],
                "雙冷啟動或觀測旗標不符：" + name)
        require(a["version"] == "goal120-third-card-v3" and a["end"] == 40000000 and
                a["input_sha256"] == control["input_sha256"] == want_sha and
                a["input_hashes"] == baseline["input_hashes"] and a["difficulty_art_opened"],
                "原版版本、卡片資產或事件不符：" + name)
        require(not control["reads"] and not control["writes"] and
                a["state"] == control["state"] and a["snapshots"] == control["snapshots"] and
                a["file_loads"] == control["file_loads"] and a["opened"] == control["opened"],
                "無監看控制改變原版狀態：" + name)
        for key in ("canvas_sha256", "palette_sha256"):
            require(a["state"][key] == baseline["state"][key], "終點不在同張第三卡：" + name)
        counts = {}
        for snap in SNAPS:
            c = images[(name, "a", snap, "canvas")]
            i = images[(name, "a", snap, "idx")]
            require(sha(c) == a["snapshots"][snap]["canvas_sha256"] and
                    sha(i) == a["snapshots"][snap]["indexed_sha256"],
                    "逐相位畫面收據不符：" + name + "/" + snap)
            for suffix in ("b", "control"):
                require(images[(name, suffix, snap, "canvas")] == c and
                        images[(name, suffix, snap, "idx")] == i,
                        "雙重播或控制畫面與收據不符：" + name + "/" + snap)
            counts[snap] = tuple(overlap(i, c, rect) for rect in RECTS.values())
        require(counts["before-move"] == counts["away-settled"] == (0, 0),
                "滑鼠移開後欄位仍被遮擋：" + name)
        require(tuple(counts[s] for s in ("before-press", "after-press", "click-settled", "before-away")) ==
                EXPECTED[name], "欄位遮擋相位不符：" + name)
        require(images[(name, "a", "click-settled", "canvas")] ==
                images[(name, "a", "before-away", "canvas")] ==
                images[(name, "a", "away-settled", "canvas")], "按鍵後底層卡片未穩定：" + name)
        result[name] = {"input_sha256": want_sha, "mouse": [55, y],
                        "normalized_report_sha256": sha(json.dumps(a, ensure_ascii=False, sort_keys=True).encode()),
                        "occlusion_by_phase": {key: list(value) for key, value in counts.items()},
                        "double_cold_boot": True, "no_observer_control": True}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        baseline_rows, baseline_images, original, baseline_inputs = load_baseline(args.baseline, args.game)
        validate_baseline(baseline_rows, baseline_images, original, baseline_inputs)
        reports = {name + "-" + suffix:
                   json.loads((args.reports / f"{name}-{suffix}.json").read_text())
                   for name in INPUTS for suffix in ("a", "b", "control")}
        inputs = {name: (args.reports / f"{name}.inputs.json").read_bytes() for name in INPUTS}
        images = {(name, suffix, snap, ext):
                  (args.reports / f"{name}-{suffix}.{snap}.{ext}").read_bytes()
                  for name in INPUTS for suffix in ("a", "b", "control")
                  for snap in SNAPS for ext in ("canvas", "idx")}
    except FileNotFoundError as exc:
        print("SKIP 77：缺合法原版或本機收據：", exc)
        raise SystemExit(77)
    result = validate(reports, inputs, images, baseline_rows["click-v3-a"])
    if args.self_test:
        mutated = dict(inputs)
        mutated["title-only"] = b"{}"
        try:
            validate(reports, mutated, images, baseline_rows["click-v3-a"])
        except ValueError:
            pass
        else:
            raise AssertionError("錯滑鼠事件未拒絕")
        mutated_images = dict(images)
        key = ("subtitle-cursor", "a", "click-settled", "idx")
        pixels = bytearray(mutated_images[key])
        pixels[151 * 320 + 55] ^= 1
        mutated_images[key] = bytes(pixels)
        try:
            validate(reports, inputs, mutated_images, baseline_rows["click-v3-a"])
        except ValueError:
            pass
        else:
            raise AssertionError("變造合成游標畫面未拒絕")
        mutated_reports = copy.deepcopy(reports)
        mutated_reports["title-only-control"]["state"]["ticks"] = -1
        try:
            validate(mutated_reports, inputs, images, baseline_rows["click-v3-a"])
        except ValueError:
            pass
        else:
            raise AssertionError("控制組狀態分歧未拒絕")
    if not args.output.parent.is_dir() or args.output.parent.stat().st_uid != os.getuid():
        raise ValueError("輸出目錄不存在或擁有者不符")
    receipt = {"result": "PASS", "scope": "第三張卡三個滑鼠位置的原版按放與移開；非正式中文覆蓋",
               "fields": result,
               "candidate_guard": "穩定幀逐欄比較 indexed 與 canvas 安全區；非零時該欄回退原文",
               "limits": "僅固定座標／時窗；印字中途不可由這些快照推斷合成幀安全；尚未接正式前端"}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS：第三張卡只遮上行／只遮下行／跨兩行；雙冷啟動、無監看控制、按放與移開")


if __name__ == "__main__":
    main()
