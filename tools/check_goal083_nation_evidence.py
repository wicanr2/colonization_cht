#!/usr/bin/env python3
"""獨立核對國家選擇標題的來源載入、印字像素與真視窗同狀態。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


VERSIONS = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
}
SOURCE_INPUT = "bb86566b14d73136e27a096b35ba6b1e2e84ef011122ac817dd989dd7727e550"
GUI_INPUT = "67494a4ea961836e57b3c546638032497c3e019c30f0aa62a70f006dd96ec96d"
FIELDS = (
    ("select", 0x8D3, b"Select", 0x4DFB5, "before-select-source", "after-select-ink",
     (42, 36, 69, 44), 120, (39, 35, 73, 46), b"Select\0"),
    ("power", 0x8DB, b"European Power", 0x4DFBC, "before-power-source", "after-power-ink",
     (20, 49, 91, 57), 270, (17, 48, 95, 59), b"European Power\0"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def check(args):
    out = args.out
    for name, want in VERSIONS.items():
        require(sha((args.game / name).read_bytes()) == want, "原版檔案版本不符：" + name)
    label_bytes = (args.game / "LABELS.TXT").read_bytes()
    require(sha((out / "click.inputs.json").read_bytes()) == SOURCE_INPUT and
            sha((out / "goal083-window.inputs.json").read_bytes()) == GUI_INPUT,
            "受控或真視窗輸入版本不符")
    load_a = (out / "label-load-a.json").read_bytes()
    load_b = (out / "label-load-b.json").read_bytes()
    trace_a = (out / "nation-evidence-a.json").read_bytes()
    trace_b = (out / "nation-evidence-b.json").read_bytes()
    require(load_a == load_b and trace_a == trace_b, "原版雙次重播不一致")
    load, trace = json.loads(load_a), json.loads(trace_a)
    gui_trace = json.loads((out / "nation-evidence-gui.json").read_text())
    gui = json.loads((out / "goal083-window.json").read_text())
    control = json.loads((out / "goal083-window-control.json").read_text())
    require(load["version"] == "goal083-label-load-v1" and
            trace["version"] == gui_trace["version"] == "goal083-nation-text-probe-v1" and
            load["input_hashes"] == {name: VERSIONS[name] for name in load["input_hashes"]} and
            trace["input_hashes"] == VERSIONS and
            not trace["read_truncated"] and not trace["write_truncated"] and
            not gui_trace["read_truncated"] and not gui_trace["write_truncated"],
            "原版探針版本、輸入或事件完整性不符")
    require(load["transfers"] and len(load["transfers"]) == 1 and
            load["transfers"][0]["transfer_matched"], "缺少檔案至 DOS 緩衝的載入邊")
    require(trace["nation_art_open_step"] == 42032499 and
            gui_trace["nation_art_open_step"] > trace["nation_art_open_step"] and
            trace["opened"][-1].upper() == gui_trace["opened"][-1].upper() == "NATIONS.PIK",
            "原版未從正常輸入進入國家畫面")
    require(trace["read_counts"] == gui_trace["read_counts"] == {"source": 135, "display": 91} and
            trace["write_sites"]["0D21:012C"]["count"] ==
            gui_trace["write_sites"]["0D21:012C"]["count"] == 390,
            "來源或畫布印字數量不符")
    require(gui["state"] == control["state"] and
            gui["opened"] == control["opened"] and
            gui_trace["state"]["memory_sha256"] == control["state"]["memory_sha256"] and
            gui_trace["state"]["indexed_sha256"] == control["state"]["frame_sha256"] and
            gui_trace["state"]["palette_sha256"] == control["state"]["palette_sha256"] and
            (out / "click.final.idx").read_bytes() ==
            (out / "goal083-window.final.idx").read_bytes(),
            "真視窗、同輸入英文控制或受控索引畫面不一致")
    with Image.open(out / "goal083-window.after-finish.png") as shot, \
            Image.open(out / "goal083-window.final.png") as final:
        require(ImageChops.difference(shot.convert("RGB"), final.convert("RGB")).getbbox() is None,
                "真視窗擷取與最終輸出不同")
    indexed = (out / "click.final.idx").read_bytes()
    require(len(indexed) == 64000, "原版索引畫面長度不符")
    measured = {}
    for name, offset, original, linear, before_name, after_name, bbox, pixels, safe, display in FIELDS:
        require(label_bytes[offset:offset + len(original)] == original and
                load[name + "_bytes_sha256"] == sha(original) and
                load["target_" + name + "_hex"] == (original + b"\0").hex() and
                trace["candidate_ram"][name + "_hex"] == (original + b"\0").hex() and
                int(trace["candidate_ram"][name + "_linear"], 16) == linear,
                "原文檔案、載入目標與終點記憶體不符：" + name)
        transfer = load["transfers"][0]
        require(transfer[name + "_hex"] == original.hex() and
                transfer[name + "_buffer_linear"] == transfer["destination_linear"] +
                offset - transfer["file_offset"], "DOS 讀入偏移或位址不符：" + name)
        require(any(e["linear"] == transfer[name + "_buffer_linear"] and
                    e["value"] == original[0] for e in load["source_reads"]) and
                any(e["linear"] == linear and e["value"] == original[0] for e in load["target_writes"]),
                "來源緩衝讀取或目標寫入缺失：" + name)
        require(any(r["linear"] == linear and r["value"] == original[0] and
                    r["site"] == "0D3A:0015" for r in trace["reads"]) and
                any(r["linear"] == linear and r["value"] == original[0] and
                    r["site"] == "0D3A:0015" for r in gui_trace["reads"]),
                "正常玩家路徑的原文讀取缺失：" + name)
        before = (out / f"nation-evidence-a.{before_name}.canvas").read_bytes()
        after = (out / f"nation-evidence-a.{after_name}.canvas").read_bytes()
        require(len(before) == len(after) == 64000 and
                rect_bytes(after, safe) == rect_bytes(indexed, safe),
                "原版畫布、終點像素或安全區不符：" + name)
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        require(len(changed) == pixels and
                (min(i % 320 for i in changed), min(i // 320 for i in changed),
                 max(i % 320 for i in changed), max(i // 320 for i in changed)) == bbox and
                all(safe[0] <= i % 320 < safe[2] and safe[1] <= i // 320 < safe[3]
                    for i in changed) and
                set(after[i] for i in changed) == {0, 253, 254},
                "畫布差分不是限定原文墨跡：" + name)
        measured[name] = {"original_pixels": pixels, "bbox_inclusive": bbox,
                          "safe_half_open": safe, "background_palette_indices":
                          len(set(rect_bytes(before, safe)))}
        found = False
        display_reads = [r for r in trace["reads"] if r["site"] == "0D21:00C6"]
        for i in range(len(display_reads) - len(display) + 1):
            segment = display_reads[i:i + len(display)]
            if bytes(r["value"] for r in segment) == display and all(
                    segment[j]["linear"] == segment[0]["linear"] + j
                    for j in range(len(segment))):
                found = True
                break
        require(found, "缺少格式化後原文顯示讀取：" + name)
    receipt = {
        "result": "PASS", "scope": "正常玩家難度完成區至國家選擇標題兩行；只讀 RE 證據",
        "load_receipt_sha256": sha(load_a), "trace_receipt_sha256": sha(trace_a),
        "true_window_input_sha256": GUI_INPUT, "true_window_original_state_equal_control": True,
        "nation_art_opened": True, "fields": measured,
        "limitations": "本收據不證明中文覆蓋的執行期底圖與游標守門，也不證明 help 已可達",
    }
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    check(p.parse_args())
