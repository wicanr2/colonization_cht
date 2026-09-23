#!/usr/bin/env python3
"""獨立核對目標081的 DOS 來源、字形畫布與原版控制組；不接正式顯示層。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


NAMES_SHA = "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"
LABELS_SHA = "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204"
FIELDS = (
    ("title", "NAMES.TXT", NAMES_SHA, 0xC18, b"Explorer", 0x2B01A, 0x4CC75,
     b"EXPLORER:\0", (250, 45, 283, 49), (247, 44, 287, 51), 134, 156),
    ("subtitle", "LABELS.TXT", LABELS_SHA, 0x8B2, b"Easy", 0x2B0B4, 0x4DF98,
     b"Easy\0", (260, 53, 275, 58), (256, 52, 279, 60), 55, 68),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def insist(condition, message):
    if not condition:
        raise ValueError(message)


def chunks(events, threshold=1000):
    result = []
    for event in events:
        if not result or event["step"] - result[-1][-1]["step"] > threshold:
            result.append([])
        result[-1].append(event)
    return result


def bbox(points):
    return (min(x for x, _ in points), min(y for _, y in points),
            max(x for x, _ in points), max(y for _, y in points))


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in ("NAMES.TXT", "LABELS.TXT")):
        print("SKIP：缺少合法原版來源，不能驗證第二張卡片")
        return 77
    p = args.reports
    raw_load = [(p / f"load-{name}.json").read_bytes() for name in ("a", "b")]
    raw_trace = [(p / f"trace-v3{name}.json").read_bytes() for name in ("a", "b")]
    insist(raw_load[0] == raw_load[1] and raw_trace[0] == raw_trace[1], "雙次原版收據不一致")
    load, trace = json.loads(raw_load[0]), json.loads(raw_trace[0])
    insist(load["version"] == "goal081-second-card-load-v1" and
           trace["version"] == "goal081-second-card-v3" and
           load["end"] == 32000000 and trace["end"] == 40000000 and
           not load["reads_truncated"] and not load["writes_truncated"] and
           trace["difficulty_art_opened"], "原版收據版本、終點或截斷不符")
    expected = json.loads((p / "click.json").read_text())["state"]
    for key in ("memory_sha256", "registers", "segments", "ip", "flags", "steps", "ticks", "frames", "cycles", "palette_sha256"):
        insist(trace["state"][key] == expected[key], "觀測與無觀測組原版狀態不同：" + key)
    insist(trace["state"]["indexed_sha256"] == expected["frame_sha256"] ==
           sha((p / "click.final.idx").read_bytes()), "第二張卡片原版索引畫面不同")
    insist((p / "control.final.idx").read_bytes() == (p / "hover.final.idx").read_bytes(),
           "只有滑鼠移入不應切換卡片")
    insist((p / "click.final.idx").read_bytes() != (p / "control.final.idx").read_bytes(),
           "點擊後仍未切換原版畫面")
    window_inputs = json.loads((p / "window-second-card.inputs.json").read_text())
    events = window_inputs["inputs"]
    insist(window_inputs["end"] == 100000000 and len(events) == 12 and
           events[8]["kind"] == "move" and (events[8]["x"], events[8]["y"]) == (265, 55) and
           events[9]["kind"] == "press" and events[10]["kind"] == "release" and
           events[11]["kind"] == "move" and (events[11]["x"], events[11]["y"]) == (16, 16),
           "真視窗不是實際第二張卡片滑鼠路徑")
    live = json.loads((p / "window-second-card.json").read_text())
    live_control = json.loads((p / "window-second-card-control.json").read_text())
    insist(live["state"] == live_control["state"] and
           (p / "window-second-card.final.idx").read_bytes() ==
           (p / "window-second-card-control.final.idx").read_bytes() ==
           (p / "click.final.idx").read_bytes() and
           (p / "window-second-card.final.pal").read_bytes() ==
           (p / "window-second-card-control.final.pal").read_bytes(),
           "真視窗、中英文控制或受控重播的原版狀態不同")
    live_image = Image.open(p / "window-second-card.final.png").convert("RGB")
    live_control_image = Image.open(p / "window-second-card-control.final.png").convert("RGB")
    shot = Image.open(p / "window-second-card.second-card.png").convert("RGB")
    insist(ImageChops.difference(live_image, shot).getbbox() is None,
           "真視窗抓圖與最終 Ebitengine 輸出不同")
    approved = ((39 * 4, 14 * 4, 76 * 4, 26 * 4),
                (20 * 4, 27 * 4, 96 * 4, 40 * 4),
                (10 * 4, 79 * 4, 105 * 4, 88 * 4))
    changed_output = 0
    for y in range(800):
        for x in range(1280):
            if live_image.getpixel((x, y)) == live_control_image.getpixel((x, y)):
                continue
            changed_output += 1
            insist(any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in approved),
                   f"真視窗既有中文覆蓋超出安全矩形：{x},{y}")
    insist(changed_output > 0, "真視窗沒有任何既有中文覆蓋")
    palette = (p / "click.final.pal").read_bytes()
    indexed = (p / "click.final.idx").read_bytes()
    insist(len(palette) == 768 and len(indexed) == 64000 and max(palette) <= 63, "索引畫面／色盤不符")
    colors = [tuple((palette[i * 3 + j] << 2) | (palette[i * 3 + j] >> 4) for j in range(3))
              for i in range(256)]
    im = Image.new("RGB", (320, 200))
    im.putdata([colors[i] for i in indexed])
    actual = Image.open(p / "click.final.png").convert("RGB")
    insist(ImageChops.difference(im.resize((1280, 800), Image.Resampling.NEAREST), actual).getbbox() is None,
           "Ebitengine 控制畫面與原版索引／色盤不一致")
    display_groups = chunks([e for e in trace["reads"] if e["site"] == "0D21:00C6"])
    ink_groups = chunks([e for e in trace["writes"] if e["site"] == "0D21:012C"])
    insist(len(display_groups) == len(ink_groups) == 6, "卡片格式化顯示或字形寫入次數不符")
    rows = []
    for n, field in enumerate(FIELDS):
        name, filename, source_sha, offset, original, ram, target, display, ink_box, safe, pixels, writer_count = field
        source = (args.game / filename).read_bytes()
        insist(sha(source) == source_sha and source[offset:offset + len(original)] == original,
               "原始 TXT 來源或位移不符：" + name)
        candidate = next((x for x in load["candidates"] if x["name"] == filename and
                          x["file_offset"] == offset and x["runtime_target"] == target), None)
        insist(candidate is not None and candidate["bytes_sha256"] == sha(original),
               "載入候選鍵不符：" + name)
        file_reads = [x for x in load["file_reads"] if x["name"] == filename and
                      x.get("candidate_offset") == offset and x["candidate_linear"] == ram]
        insist(file_reads and all(x["candidate_ram_match"] and x["candidate_ram_sha256"] == sha(original)
                                  for x in file_reads), "DOS 讀入來源位元組不符：" + name)
        source_reads = [e for e in load["source_reads"] if e["site"] == "0E2D:1F76" and
                        ram <= e["linear"] < ram + len(original)]
        insist(bytes(e["value"] for e in source_reads[:len(original)]) == original,
               "原版載入器未讀取來源：" + name)
        target_writes = [e for e in load["target_writes"] if e["site"] in ("0E2D:11A1", "0E2D:11A5") and
                         target <= e["linear"] < target + len(original)]
        insist(bytes(e["value"] for e in target_writes) == original,
               "執行期原文來源未直接由載入器寫入：" + name)
        run_reads = [e for e in trace["reads"] if e["site"] == "0E2D:11CF" and
                     target <= e["linear"] <= target + len(original)]
        insist(bytes(e["value"] for e in run_reads) == (original + b"\0") * 3,
               "第二張卡片來源讀取不符：" + name)
        for i in (n, n + 2, n + 4):
            insist(bytes(e["value"] for e in display_groups[i]) == display * 2,
                   "格式化顯示字節不符：" + name)
            writes = ink_groups[i]
            points = [((e["linear"] - 0x2CAE0) % 320, (e["linear"] - 0x2CAE0) // 320) for e in writes]
            insist(len(writes) == writer_count and bbox(points) == ink_box and
                   {e["value"] for e in writes} == {0, 9}, "原版文字寫畫布證據不符：" + name)
        before = (p / f"trace-v3a.before-{name}-ink.canvas").read_bytes()
        after = (p / f"trace-v3a.after-{name}-ink.canvas").read_bytes()
        insist(len(before) == len(after) == 64000, "畫布快照長度不符：" + name)
        changed = [(i % 320, i // 320) for i, (a, b) in enumerate(zip(before, after)) if a != b]
        insist(len(changed) == pixels and bbox(changed) == ink_box and
               all(safe[0] <= x < safe[2] and safe[1] <= y < safe[3] for x, y in changed),
               "兩行畫布差分或安全矩形不符：" + name)
        insist(rect_bytes(after, safe) == rect_bytes(indexed, safe) and
               len(set(rect_bytes(before, safe))) > 50, "文字底圖不可逆或最終畫面不穩：" + name)
        rows.append({"field": name, "source": f"{filename}:0x{offset:08X}",
                     "source_ram": f"0x{target:X}", "display": display.rstrip(b"\0").decode(),
                     "ink_bbox_inclusive": ink_box, "safe_half_open": safe,
                     "changed_canvas_pixels": pixels, "original_ink_height_scaled": (ink_box[3] - ink_box[1] + 1) * 4,
                     "background_palette_indices": len(set(rect_bytes(before, safe)))})
    result = {"scope": "目標081固定受控原版重播加真 Ebitengine 點擊；第二張卡片仍非正式中文覆蓋",
              "load_receipt_sha256": sha(raw_load[0]), "output_receipt_sha256": sha(raw_trace[0]),
              "same_state_as_unobserved_control": True, "hover_does_not_select": True,
              "ebitengine_control_matches_indexed": True,
              "live_window_input_sha256": sha((p / "window-second-card.inputs.json").read_bytes()),
              "live_window_same_state_as_control": True,
              "live_window_same_original_indexed_as_probe": True,
              "live_window_existing_zh_changed_pixels": changed_output,
              "live_window_existing_zh_only_approved_rectangles": True, "fields": rows}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
