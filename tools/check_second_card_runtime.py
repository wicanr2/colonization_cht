#!/usr/bin/env python3
"""獨立驗證目標082第二張卡片的可丟棄逐幀守門與原版同狀態。"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops


SOURCE_HASHES = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
}
STATE = ("end", "exited", "memory_sha256", "canvas_sha256", "indexed_sha256",
         "palette_sha256", "registers", "segments", "ip", "flags", "ticks",
         "frame_count", "cycles")
FIELDS = (
    ("title", "NAMES.TXT:0x00000C18", 0x4CC75, 33089491, 134,
     (250, 45, 283, 49), (247, 44, 287, 51)),
    ("subtitle", "LABELS.TXT:0x000008B2", 0x4DF98, 33101076, 55,
     (260, 53, 275, 58), (256, 52, 279, 60)),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def same_state(left, right):
    return all(left[key] == right[key] for key in STATE)


def verify(args):
    if not all((args.game / name).is_file() for name in SOURCE_HASHES):
        print("SKIP：缺少合法原版來源，不能驗證第二張卡片執行期")
        return 77
    require(all(sha((args.game / name).read_bytes()) == expected
                for name, expected in SOURCE_HASHES.items()), "原版版本指紋不符")
    p = args.reports
    raw = {name: (p / f"runtime-{name}.json").read_bytes()
           for name in ("a", "b", "control", "hover", "hover-control")}
    require(raw["a"] == raw["b"], "雙次正常原版收據不同")
    reports = {name: json.loads(data) for name, data in raw.items()}
    a, control, hover, hover_control = (reports[name] for name in
                                        ("a", "control", "hover", "hover-control"))
    preview_bytes = (p / "preview.json").read_bytes()
    preview = json.loads(preview_bytes)
    inputs = (args.previous / "click.inputs.json").read_bytes()
    require(sha(inputs) == "7e89bf0edabb8b26df5168342bfd42226b7a467b8e7c8abdab87e83275a32e7e" and
            preview["prototype"] and
            preview["source_load_receipt_sha256"] == sha((args.previous / "load-a.json").read_bytes()) and
            preview["source_receipt_sha256"] == sha((args.previous / "trace-v3a.json").read_bytes()) and
            preview["font_sha256"] == "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c" and
            preview["catalog_sha256"] == sha(args.catalog.read_bytes()),
            "可丟棄預覽未固定原始收據、字型或 TSV")
    for name, report, end, variant_control, variant_hover in (
        ("a", a, 40000000, False, False),
        ("b", reports["b"], 40000000, False, False),
        ("control", control, 40000000, True, False),
        ("hover", hover, 48000000, False, True),
        ("hover-control", hover_control, 48000000, True, True),
    ):
        require(report["version"] == "goal082-second-card-runtime-v1" and
                report["variant_second"] and report["variant_hover"] is variant_hover and
                report["control"] is variant_control and report["end"] == end and
                not report["exited"] and report["input_hashes"] == SOURCE_HASHES and
                report["input_sha256"] == sha(inputs) and
                report["preview_sha256"] == sha(preview_bytes) and
                report["dos_address_space"] == "real-mode CS:IP and 20-bit linear RAM" and
                report["canvas_address_space"] == "320x200 logical indexed pixels",
                "收據版本、輸入或位址空間不符：" + name)
    require(same_state(a, control) and same_state(hover, hover_control),
            "有觀測與無觀測原版狀態不同")
    require(not control["frames"] and not hover_control["frames"] and
            not control["first_both_applied"] and not hover_control["first_both_applied"],
            "英文控制組執行了合成或觀測")
    original = json.loads((args.previous / "click.json").read_text())["state"]
    for key, old_key in (("memory_sha256", "memory_sha256"),
                         ("indexed_sha256", "frame_sha256"),
                         ("palette_sha256", "palette_sha256"),
                         ("registers", "registers"), ("segments", "segments"),
                         ("ip", "ip"), ("flags", "flags"),
                         ("ticks", "ticks"), ("cycles", "cycles")):
        require(a[key] == original[old_key], "新探針與目標081無觀測原版終點不同：" + key)
    for report in (a, hover):
        require(report["first_both_applied"] and report["negative_controls"] ==
                {"missing-ink": "missing-ink", "missing-translation": "disabled",
                 "source-or-context-changed": "disabled", "stale-frame": "frame-mismatch"} and
                report["negative_original_pixels_unchanged"] ==
                {"missing-ink": True, "missing-translation": True,
                 "source-or-context-changed": True}, "缺譯、缺字模或舊背景沒有回退原文")
        for name, key, linear, step, count, bbox, safe in FIELDS:
            source = report["sources"][name]
            before = (args.previous / f"trace-v3a.before-{name}-ink.canvas").read_bytes()
            require(source["candidate_id"] == key and source["source_linear"] == linear and
                    source["read_site"] == "0E2D:11CF" and source["before_step"] == step and
                    source["after_frame_step"] == 33165000 and source["patch_ready"] and
                    source["expected_changed_pixels"] == count and
                    source["expected_bbox_inclusive"] == list(bbox) and
                    source["before_rect_sha256"] == sha(rect_bytes(before, safe)),
                    "當次來源讀取／背景／畫素證據不符：" + name)
    require(len(a["frames"]) == 49 and hover["frames"][:49] == a["frames"],
            "普通與游標路徑在新增輸入前已分歧")
    normal_counts = Counter(tuple(frame["reasons"]) for frame in a["frames"])
    require(normal_counts == {("applied", "applied"): 30,
                              ("cursor-conservative-guard",) * 2: 14,
                              ("mouse-button-held",) * 2: 5} and
            all(frame["applied"] == 2 and frame["source_and_context_valid"] ==
                {"title": True, "subtitle": True} for frame in a["frames"] if frame["step"] >= 35000000),
            "正常點擊後兩欄未穩定套用或按鍵保持未回退")
    over = [frame for frame in hover["frames"] if 40000000 <= frame["step"] < 44000000]
    away = [frame for frame in hover["frames"] if frame["step"] >= 44000000]
    require(len(over) == len(away) == 24 and
            all(frame["mouse"] == [265, 55, 0] and frame["applied"] == 0 and
                frame["reasons"] == ["cursor-conservative-guard"] * 2 and
                frame["unguarded_reasons"] == ["applied", "frame-mismatch"] and
                frame["indexed_delta_from_first_applied"]["safe_intersections"] ==
                {"title": 0, "subtitle": 17} for frame in over) and
            all(frame["mouse"] == [16, 16, 0] and frame["applied"] == 2 and
                frame["reasons"] == ["applied", "applied"] and
                frame["indexed_delta_from_first_applied"]["count"] == 0 for frame in away),
            "游標遮住第二張卡片或移開後未安全恢復")
    require(hover["indexed_sha256"] == a["indexed_sha256"] and
            hover["canvas_sha256"] == a["canvas_sha256"] and
            hover["palette_sha256"] == a["palette_sha256"],
            "游標離開後原版畫面未恢復")
    image_receipt = json.loads((p / "runtime-image-verify.json").read_text())
    require(image_receipt["result"] == "PASS" and
            image_receipt["changed_pixels_by_field"] == {"title": 2280, "subtitle": 1233} and
            image_receipt["control_png_sha256"] == sha((p / "runtime-a.control.png").read_bytes()) and
            image_receipt["chinese_png_sha256"] == sha((p / "runtime-a.zh.png").read_bytes()) and
            image_receipt["source_receipt_sha256"] == preview["source_receipt_sha256"],
            "執行期原文／中文逐像素驗證缺失或不符")
    baseline_image = Image.open(args.previous / "click.final.png").convert("RGB")
    control_image = Image.open(p / "runtime-a.control.png").convert("RGB")
    require(ImageChops.difference(baseline_image, control_image).getbbox() is None,
            "執行期英文圖與目標081 Ebitengine 原版控制畫面不同")
    result = {"result": "PASS", "scope": "第二張難度卡片可丟棄執行期守門；尚非正式中文前端",
              "runtime_receipt_sha256": sha(raw["a"]), "normal_applied_frames": 30,
              "mouse_button_fallback_frames": 5, "cursor_fallback_frames": len(over),
              "after_cursor_applied_frames": len(away),
              "hover_original_indexed_intersections": {"title": 0, "subtitle": 17},
              "unchanged_original_state_vs_control": True,
              "source_background_matches_prior_probe": True}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(verify(parser.parse_args()))
