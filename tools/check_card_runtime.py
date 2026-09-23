#!/usr/bin/env python3
"""驗證目標078的執行期原文背景、游標回退及不改動原版狀態。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from check_card_load import SOURCE_HASHES, verify as verify_card_load


STATE = ("end", "exited", "memory_sha256", "canvas_sha256", "indexed_sha256",
         "palette_sha256", "registers", "segments", "ip", "flags", "ticks",
         "frame_count", "cycles")
BASELINE = {
    "memory_sha256": "09e9fbf961b8b50115fa0c8b707d4a220cf7f12b3e2a359311073f85786ad109",
    "canvas_sha256": "08edaac74a54263b8e093010d8cbc97d3f9820c3c151f28d80beded5c5a8a650",
    "indexed_sha256": "6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae",
    "palette_sha256": "762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82",
}
EXPECTED_SOURCES = {
    "title": ("NAMES.TXT:0x00000C0C", 0x4CC6A, 29797568, 164, [141, 45, 182, 49],
              "before-first", (138, 44, 186, 51)),
    "subtitle": ("LABELS.TXT:0x000008A9", 0x4DF90, 29813172, 83, [150, 53, 174, 58],
                 "before-second", (146, 52, 180, 60)),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def read(path):
    raw = path.read_bytes()
    return raw, json.loads(raw)


def compare_state(left, right, label):
    require({key: left[key] for key in STATE} == {key: right[key] for key in STATE},
            "同輸入控制組與觀測組原版狀態不同：" + label)


def check_source(report, flow):
    snapshots = {key: base64.b64decode(data, validate=True)
                 for key, data in flow["snapshots"].items()}
    for name, (candidate, linear, read_step, count, bbox, snapshot, safe) in EXPECTED_SOURCES.items():
        row = report["sources"][name]
        require(row["candidate_id"] == candidate and row["source_linear"] == linear
                and row["read_site"] == "0E2D:11CF" and row["before_step"] == read_step
                and row["after_frame_step"] == 29865000 and row["patch_ready"]
                and row["expected_changed_pixels"] == count
                and row["expected_bbox_inclusive"] == bbox,
                "原版執行期擷取事件不符：" + name)
        require(row["before_rect_sha256"] == sha(rect_bytes(snapshots[snapshot], safe)),
                "執行期背景與目標075原版繪製前畫布不符：" + name)


def verify(args):
    verify_card_load(args.inputs, args.load_first, args.load_second,
                     args.flow_first, args.flow_second)
    raw_a, a = read(args.first)
    raw_b, b = read(args.second)
    _, control = read(args.control)
    _, hover = read(args.hover)
    _, hover_control = read(args.hover_control)
    require(raw_a == raw_b, "兩次獨立執行期觀測收據不同")
    preview_raw, preview = read(args.preview)
    flow = json.loads(args.flow_first.read_bytes())
    for name, report, is_hover, is_control, end in (
        ("第一次", a, False, False, 32000000),
        ("第二次", b, False, False, 32000000),
        ("無觀測", control, False, True, 32000000),
        ("游標", hover, True, False, 40000000),
        ("游標無觀測", hover_control, True, True, 40000000),
    ):
        require(report["version"] == "goal078-card-runtime-v2"
                and report["variant_hover"] is is_hover
                and report["control"] is is_control
                and report["end"] == end and report["exited"] is False
                and report["input_sha256"] == sha(args.inputs.read_bytes())
                and report["input_hashes"] == SOURCE_HASHES
                and report["preview_sha256"] == sha(preview_raw)
                and report["dos_address_space"] == "real-mode CS:IP and 20-bit linear RAM"
                and report["canvas_address_space"] == "320x200 logical indexed pixels",
                "報告版本、固定輸入或位址空間不符：" + name)
    require(preview["source_load_receipt_sha256"] == sha(args.load_first.read_bytes())
            and preview["catalog_sha256"] == sha(args.catalog.read_bytes())
            and preview["font_sha256"] ==
            "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
            and preview["prototype"] is True, "字模預覽未綁定已驗證來源與譯稿")
    compare_state(a, control, "固定正常玩家路徑")
    compare_state(hover, hover_control, "游標進出路徑")
    for key, want in BASELINE.items():
        require(a[key] == want, "觀測改變既有正常玩家終點：" + key)
    require(hover["indexed_sha256"] == a["indexed_sha256"]
            and hover["canvas_sha256"] == a["canvas_sha256"]
            and hover["palette_sha256"] == a["palette_sha256"],
            "移開游標後卡片畫面未恢復；不同輸入的 RAM 不要求相同")
    check_source(a, flow)
    check_source(hover, flow)
    require(a["negative_controls"] == hover["negative_controls"] ==
            {"missing-ink": "missing-ink", "missing-translation": "disabled",
             "source-or-context-changed": "disabled",
             "stale-frame": "frame-mismatch"}
            and a["negative_original_pixels_unchanged"] ==
            hover["negative_original_pixels_unchanged"] ==
            {"missing-ink": True, "missing-translation": True,
             "source-or-context-changed": True},
            "缺譯、缺字模或舊畫面反向條件沒有正確回退")
    require(a["first_both_applied"] and hover["first_both_applied"]
            and not control["first_both_applied"] and not hover_control["first_both_applied"],
            "合成組或控制組的首幀狀態不符")
    require(not control["frames"] and not hover_control["frames"], "控制組不應記錄合成幀")
    require(len(a["frames"]) == 14 and a["frames"][0]["reasons"] ==
            ["missing-patch", "missing-patch"], "原文尚未繪製的幀未回退")
    require(all(frame["applied"] == 2 and frame["reasons"] == ["applied", "applied"]
                and frame["source_and_context_valid"] == {"title": True, "subtitle": True}
                for frame in a["frames"][1:]), "固定路徑兩欄不是逐幀成功")
    require(hover["frames"][:14] == a["frames"], "游標變體在移入前已與基準分歧")
    over = [frame for frame in hover["frames"] if 32000000 <= frame["step"] < 36000000]
    away = [frame for frame in hover["frames"] if frame["step"] >= 36000000]
    require(len(over) == 25 and len(away) == 24, "游標進出未覆蓋預期的輸出幀")
    require(all(frame["mouse"] == [160, 48, 0]
                and frame["reasons"] == ["cursor-conservative-guard"] * 2
                and frame["unguarded_reasons"] == ["frame-mismatch"] * 2
                and frame["applied"] == 0
                and frame["source_and_context_valid"] == {"title": True, "subtitle": True}
                and frame["indexed_delta_from_first_applied"]["safe_intersections"]["title"] > 0
                and frame["indexed_delta_from_first_applied"]["safe_intersections"]["subtitle"] > 0
                and frame["indexed_delta_from_first_applied"]["count"] == 160
                and frame["indexed_delta_from_first_applied"]["bbox_inclusive"] ==
                [16, 16, 169, 61]
                and frame["indexed_delta_from_first_applied"]["safe_intersections"] ==
                {"title": 7, "subtitle": 60}
                and frame["canvas_sha256"] == BASELINE["canvas_sha256"] for frame in over),
            "游標遮擋不是原版索引像素變更，或未安全回退")
    require(all(frame["mouse"] == [16, 16, 0] and frame["applied"] == 2
                and frame["reasons"] == ["applied", "applied"]
                and frame["source_and_context_valid"] == {"title": True, "subtitle": True}
                and frame["indexed_delta_from_first_applied"]["count"] == 0
                for frame in away), "游標移開後未回到同一畫面並恢復合成")
    image_verify = json.loads(args.image_verify.read_bytes())
    require(image_verify["result"] == "PASS" and image_verify["prototype"] is True
            and image_verify["changed_pixels_by_field"] == {"title": 2752, "subtitle": 1860}
            and image_verify["control_png_sha256"] == sha(args.control_png.read_bytes())
            and image_verify["chinese_png_sha256"] == sha(args.chinese_png.read_bytes())
            and image_verify["source_receipt_sha256"] == sha(args.flow_first.read_bytes()),
            "執行期輸出像素或安全矩形驗收不符")
    result = {"result": "PASS", "receipt_sha256": sha(raw_a),
              "runtime_first_applied_step": a["frames"][1]["step"],
              "normal_applied_frames": 13, "hover_fallback_frames": len(over),
              "after_hover_applied_frames": len(away),
              "hover_indexed_changed_pixels": over[0]["indexed_delta_from_first_applied"]["count"],
              "hover_safe_intersections": over[0]["indexed_delta_from_first_applied"]["safe_intersections"],
              "conclusion": "執行期可丟棄原型通過；規格016仍 DRAFT，非正式中文顯示"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "load-first", "load-second", "flow-first", "flow-second",
                 "first", "second", "control", "hover", "hover-control", "preview",
                 "image-verify", "control-png", "chinese-png", "catalog"):
        parser.add_argument("--" + name, type=Path, required=True)
    verify(parser.parse_args())
