#!/usr/bin/env python3
"""核對 Game Options 原版固定相位，產生逐欄回退矩陣及可丟棄預覽輸入。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from check_goal111_tutorial_state import check as check111
from check_goal116_options_phases import check as check116
from check_goal117_same_focus import check as check117
from check_goal118_remaining_rows import check as check118
from check_goal119_options_click import check as check119
from prepare_goal113_options_preview import FIELDS, checked_receipt, rect


PREVIEW_SHA = {
    "faithful": "b0b635296af3f488015d607904d019a2bd742ce5a6eb36be5b924833df861dbf",
    "readable": "f0a0b8290773314e53cf25300edb26d59fb1e6dd100bf4d99baac416cb71cce4",
}
STABLE = ("1300m", "1325m", "1350m", "1375m", "1400m")
BRANCHES = {
    "goal116-options": ("hover-first", "hover-last", "exit"),
    "goal117-options": ("baseline", "fourth", "seventh"),
    "goal118-options": ("second", "third", "fifth", "sixth"),
    "goal119-options": ("first", "eighth"),
    "goal111-help": ("tutorial-then-first-row",),
}
PREVIEW_STATES = (
    ("goal118-options", "second", "1325m"),
    ("goal119-options", "eighth", "1325m"),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def diff_count(left, right):
    need(len(left) == len(right), "欄位尺寸不同")
    return sum(a != b for a, b in zip(left, right))


def classify(base_canvas, current_canvas, current_indexed, safe,
             *, exiting=False, transitional=False):
    """只在固定已驗相位標可用；沒有同時點證據的細相位一律未知。"""
    before = rect(base_canvas, safe)
    canvas = rect(current_canvas, safe)
    indexed = rect(current_indexed, safe)
    underlying = diff_count(before, canvas)
    cursor = diff_count(canvas, indexed)
    if exiting:
        status = "window-exited"
    elif transitional:
        status = "unknown-transition"
    elif underlying:
        status = "background-changed"
    elif cursor:
        status = "cursor-occluded"
    else:
        status = "safe-at-sample"
    return {"status": status, "underlying_pixels_vs_preprint": underlying,
            "composited_pixels_vs_canvas": cursor,
            "preprint_patch_matches": underlying == 0}


def checked_existing(game, inputs, fixtures, root):
    checks = {
        "goal111": check111(game, inputs, fixtures, root / "goal111-help"),
        "goal116": check116(game, inputs, fixtures, root / "goal116-options",
                             root / "goal111-help"),
        "goal117": check117(game, inputs, fixtures, root / "goal117-options",
                             root / "goal111-help"),
        "goal118": check118(game, inputs, fixtures, root / "goal118-options",
                             root / "goal117-options"),
        "goal119": check119(game, inputs, fixtures, root / "goal119-options"),
    }
    need(all(value["result"] == "PASS" for value in checks.values()),
         "舊原版收據未全部通過")
    return checks


def read_frame(folder, stem, label):
    prefix = folder / stem
    report = json.loads(Path(f"{prefix}.json").read_bytes())
    sample = report["samples"][label]
    frame = {}
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == size and sha(data) == sample[field],
             f"{folder.name}/{stem}/{label}: {suffix} 原版位元組不符")
        frame[suffix] = data
    return frame


def load_preview(folder, variant, original, palette, original_receipt_sha):
    raw = (folder / f"options-{variant}.json").read_bytes()
    need(sha(raw) == PREVIEW_SHA[variant], "目標113預覽輸入版本不符：" + variant)
    data = json.loads(raw)
    need(data["prototype"] is True and data["variant"] == variant and
         data["source_receipt_sha256"] == original_receipt_sha and
         base64.b64decode(data["indexed"], validate=True) == original and
         base64.b64decode(data["palette"], validate=True) == palette and
         len(data["layers"]) == len(FIELDS), "目標113預覽來源不符")
    for index, layer in enumerate(data["layers"]):
        safe = FIELDS[index][1]
        need(layer["name"] == f"option-{index:02d}" and
             layer["safe"] == list(safe) and
             len(base64.b64decode(layer["background"], validate=True)) ==
             (safe[2] - safe[0]) * (safe[3] - safe[1]),
             "目標113候選安全矩形或底圖不符")
    return data


def build_matrix(root, original_canvas):
    matrix = {}
    frames = {}
    baseline = {}
    for label in STABLE:
        baseline[label] = read_frame(root / "goal117-options", "baseline-a", label)
    for group, branches in BRANCHES.items():
        for branch in branches:
            stem = (f"{branch}-explore" if group == "goal111-help" else f"{branch}-a")
            labels = (STABLE if group != "goal119-options" else
                      ("1300m",) + tuple(f"phase-{i:02d}" for i in range(12)) +
                      ("1325m", "1350m"))
            for label in labels:
                frame = read_frame(root / group, stem, label)
                key = f"{group}/{branch}/{label}"
                exiting = group == "goal116-options" and branch == "exit" and label in ("1375m", "1400m")
                transitional = label.startswith("phase-")
                fields = {}
                for index, (_, safe, *_) in enumerate(FIELDS):
                    field = classify(original_canvas, frame["canvas"], frame["idx"],
                                     safe, exiting=exiting, transitional=transitional)
                    if label in baseline:
                        need(frame["pal"] == baseline[label]["pal"],
                             key + ": 同時點色盤不符")
                        field["underlying_pixels_vs_same_phase_baseline"] = diff_count(
                            rect(baseline[label]["canvas"], safe),
                            rect(frame["canvas"], safe))
                    else:
                        field["underlying_pixels_vs_same_phase_baseline"] = None
                    fields[f"option-{index:02d}"] = field
                matrix[key] = {"palette_sha256": sha(frame["pal"]),
                               "indexed_sha256": sha(frame["idx"]),
                               "canvas_sha256": sha(frame["canvas"]),
                               "sample_kind": "bounded-transition" if transitional else "fixed-sample",
                               "fields": fields}
                frames[key] = frame
    return matrix, frames


def preview_payload(source, frame, key, fields):
    allowed = [layer for layer in source["layers"]
               if fields[layer["name"]]["status"] == "safe-at-sample"]
    need(allowed, "沒有可安全預覽的欄位：" + key)
    result = dict(source)
    result["indexed"] = base64.b64encode(frame["idx"]).decode("ascii")
    result["palette"] = base64.b64encode(frame["pal"]).decode("ascii")
    result["layers"] = allowed
    result["state_guard_sample"] = key
    result["state_guard_excluded"] = [layer["name"] for layer in source["layers"]
                                       if layer not in allowed]
    return result


def check(game, inputs, fixtures, root, output=None, preview_dir=None):
    from check_goal101_nation_intro import FILE_SHA
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    if output is not None:
        need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
             "收據輸出目錄不存在或擁有者不符")
    if preview_dir is not None:
        need(preview_dir.is_dir() and preview_dir.stat().st_uid == os.getuid(),
             "預覽輸出目錄不存在或擁有者不符")
    checks = checked_existing(game, inputs, fixtures, root)
    a, raw_a, original, palette = checked_receipt(root / "goal113-options")
    original_frame = read_frame(root / "goal113-options", "preprint-a", "1300m")
    need(original_frame["idx"] == original and original_frame["pal"] == palette,
         "目標113原版起點畫面不符")
    sources = {variant: load_preview(root / "goal113-options", variant, original,
                                     palette, sha(raw_a)) for variant in PREVIEW_SHA}
    matrix, frames = build_matrix(root, original_frame["canvas"])
    safe_previews = {}
    for group, branch, label in PREVIEW_STATES:
        key = f"{group}/{branch}/{label}"
        fields = matrix[key]["fields"]
        safe = [name for name, field in fields.items() if field["status"] == "safe-at-sample"]
        need(0 < len(safe) < 9, "預覽狀態沒有逐欄回退：" + key)
        safe_previews[f"{branch}-{label}"] = {"safe": safe,
            "fallback_original": [name for name in fields if name not in safe]}
        if preview_dir is not None:
            for variant, source in sources.items():
                payload = preview_payload(source, frames[key], key, fields)
                path = preview_dir / f"{branch}-{label}-{variant}.json"
                path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    result = {"result": "PASS", "prototype_only": True,
              "scope": "僅固定已驗相位；細相位與未抽樣幀未知，正式圖層維持原文",
              "original_preprint_receipt_sha256": sha(raw_a),
              "existing_checks": checks, "preview_candidates": safe_previews,
              "matrix": matrix}
    if output is not None:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures, args.reports_root,
                       args.output, args.preview_dir)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        parser.exit(1, f"FAIL：{exc}\n")
    summary = {key: result[key] for key in ("result", "scope", "preview_candidates")
               if key in result}
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
