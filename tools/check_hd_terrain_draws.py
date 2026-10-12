#!/usr/bin/env python3
"""核對本機海洋來源、原版兩側狀態與主畫布逐點身分，不授權正式HD。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parent.parent
ENCODED_SHA = "192698d118f87f0f0c4f1605962c000a63db80c935510cef2b4087bf2bd8399f"
PIXELS_SHA = "4f040c4dd1172b8c81c2f0a21b42cf21c5c14bdac7db5fe6ebc9a45d4e4f693a"
PHYS_SHA = "deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16"
INPUT_SHA = "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979"
SEED_SHA = "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def check(observed, control, source, pixels, placements):
    a, b, proof = load(observed / "draws.json"), load(control / "draws.json"), load(source)
    raw = pixels.read_bytes()
    require(len(raw) == 256 and digest(raw) == PIXELS_SHA, "完整來源像素不同")
    require(proof["original_file"] == "PHYS0.SS" and proof["original_sha256"] == PHYS_SHA,
            "原版素材指紋不同")
    require(proof["decoded_part3_offset"] == 22005 and proof["encoded_length"] == 263
            and proof["encoded_sha256"] == ENCODED_SHA and proof["unique_in_part3"] is True,
            "完整編碼來源不同")
    require(not a["control"] and b["control"] is True, "觀測與對照身分不同")
    for receipt in [a, b]:
        require(receipt["input_sha256"] == INPUT_SHA and receipt["seed_sha256"] == SEED_SHA,
                "正常玩家輸入或初始存檔不同")
    require(a["checkpoints"] == b["checkpoints"], "完整原版狀態不同")
    require([c["steps"] for c in a["checkpoints"]] == [63525000, 75900000], "檢查點不同")
    calls = a["calls"]
    selected = [c for c in calls if c["source_first_263_sha256"] == ENCODED_SHA]
    require(len(selected) == a["source_matches"] == 293, "來源命中數不同")
    write_sha = digest(b"".join(struct.pack("<HB", i, value) for i, value in enumerate(raw)))
    for call in selected:
        require(call["selected"] and not call.get("geometry_or_write_mismatch"), "繪製幾何或寫入未驗")
        require(call["ds_bx_words"] == [200, 320, 0, 0x3C50]
                and call["record_words"][4:] == [16, 16], "畫布或尺寸不同")
        require(call["return_cs_ip"] == "121D:1554"
                and 0 < call["return_step"] - call["entry_step"] <= 100000, "返回未驗")
        require(call["unique_writes"] == call["write_count"] == 256
                and call["sorted_local_offset_value_sha256"] == write_sha
                and call["after_roi_sha256"] == PIXELS_SHA, "完整逐點寫入不同")
        require(call["writer_sites"] == {"0D46:01B4": 68, "0D46:01D2": 188}, "原版寫入點不同")
    require(any(s["cs_ip"] == "0CBA:00CA"
                and s["code_hex"] == "f3a503f3790c81ee00808cd981c10008"
                for s in a["main_canvas_write_samples"]), "缺少複製指令原始樣本")

    summaries = []
    full_world_rects = set()
    for checkpoint in a["checkpoints"]:
        step = checkpoint["steps"]
        prefix = f"cp-{step}"
        for suffix in [".idx", ".canvas", ".stage"]:
            observed_bytes = (observed / (prefix + suffix)).read_bytes()
            require(len(observed_bytes) == 64000
                    and observed_bytes == (control / (prefix + suffix)).read_bytes(), "原版畫布不同")
        canvas = (observed / (prefix + ".canvas")).read_bytes()
        indexed = (observed / (prefix + ".idx")).read_bytes()
        require(digest(indexed) == checkpoint["indexed_sha256"], "VGA收據指紋不同")
        owners = load(observed / (prefix + ".main-owners.json"))
        origins = load(observed / (prefix + ".main-origins.json"))
        require(len(owners) == len(origins) == 64000, "來源身分表尺寸不同")
        counts, shifts = {}, set()
        for i, owner in enumerate(owners):
            require(type(owner) is int and 0 <= owner <= len(calls), "來源身分越界")
            if owner == 0:
                continue
            call = calls[owner - 1]
            require(call["selected"] and call["source_first_263_sha256"] == ENCODED_SHA,
                    "未驗素材進入主畫布")
            origin = origins[i]
            require(type(origin) is int and 0 <= origin < 64000, "來源位移越界")
            x, y = origin % 320 - call["rect"][0], origin // 320 - call["rect"][1]
            require(0 <= x < 16 and 0 <= y < 16, "來源位移離開原版圖塊")
            require(canvas[i] == indexed[i] == raw[y * 16 + x], "主畫布、VGA與來源像素不同")
            shifts.add((i % 320 - origin % 320, i // 320 - origin // 320))
            counts[owner] = counts.get(owner, 0) + 1
        require(not shifts or shifts == {(0, 8)}, "轉送座標差不同")
        if step == 63525000:
            require(len(counts) == 131 and sum(counts.values()) == 32867, "世界可見來源範圍不同")
            for owner, count in counts.items():
                if count == 256:
                    x0, y0, x1, y1 = calls[owner - 1]["rect"]
                    full_world_rects.add((x0, y0 + 8, x1, y1 + 8))
        else:
            require(not counts, "進城後海洋來源仍留在主畫布")
        summaries.append({"step": step, "visible_draws": len(counts), "owned_pixels": sum(counts.values())})

    locator = load(placements)
    require(locator["frame_sha256"] == a["checkpoints"][0]["indexed_sha256"], "定位畫面不同")
    sea = next(c for c in locator["assets"] if c["source"] == "PHYS0.SS" and c["ordinal"] == 148)
    require(sea["source_sha256"] == PHYS_SHA and sea["decoded_indexed_sha256"] == PIXELS_SHA,
            "定位素材不同")
    require(len(full_world_rects) == 108
            and full_world_rects == {tuple(rect) for rect in sea["matches"]}, "來源鏈與108個完整像素定位不同")
    require(a["verified_transferred_pixels"] == 69896, "逐點轉送數不同")
    require(a["same_value_ownership_losses"] > 0, "缺少同值後畫撤銷證據")
    return {"result": "PASS_SEA_SOURCE_STAGE_TRANSFER_AND_READONLY_STATE", "draws": len(selected),
            "transferred_pixels": a["verified_transferred_pixels"], "full_world_tiles": len(full_world_rects),
            "checkpoints": summaries, "source_write_sha256": write_sha,
            "stage_same_value_losses": a["same_value_ownership_losses"],
            "limitations": ["Existing normal GUI input replay, not a new HD GUI receipt.",
                            "No production HD, new artwork acceptance, animation, general clipping or cursor restore claim.",
                            "CPU, full RAM, VGA and DAC compared; no WAV or wall-clock audio comparison."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["observed", "control", "source", "pixels", "placements", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists(),
            "輸出須為workplace內的新檔案")
    require(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出父目錄或擁有者不同")
    result = check(args.observed, args.control, args.source, args.pixels, args.placements)
    result["inputs_sha256"] = {str(path): digest(path.read_bytes()) for path in [
        args.observed / "draws.json", args.control / "draws.json", args.source, args.pixels, args.placements]}
    result["checker_sha256"] = digest(Path(__file__).read_bytes())
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
