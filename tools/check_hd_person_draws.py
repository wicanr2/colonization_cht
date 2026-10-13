#!/usr/bin/env python3
"""規格063 DRAFT：獨立重建人物來源，核對原版49點與同輸入對照；不授權正式HD。"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent
ENCODED = "36d3a8e51b4bce57a879d96703d5fad70797f9e940e13aa3abc4d6f830e4d832"
PIXELS = "d2b48efd38ba4d2a0f3a90f85cf6f4e0b218ce1fcf5d264f3c86b0636f956502"
ORIGINAL = "a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716"
INPUT = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"
SEED = "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b"
POINTS = "821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901"
WRITERS = {"0D46:01B4": "268807035ef042fecc7403ebe790ebcc",
           "0D46:01D2": "268807035ef042ebb5905a5b035efe79"}

def need(value, message):
    if not value:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def check(observed, control, source, pixels, points):
    a, b, proof = read(observed / "draws.json"), read(control / "draws.json"), read(source)
    raw = pixels.read_bytes()
    need(len(raw) == 96 and sha(raw) == PIXELS, "完整人物索引不同")
    need(proof["original_file"] == "ICONS.SS" and proof["original_sha256"] == ORIGINAL
         and proof["ordinal"] == 100 and proof["size"] == [6, 16]
         and proof["decoded_part3_offset"] == 11311 and proof["encoded_length"] == 101
         and proof["encoded_sha256"] == ENCODED and proof["unique_in_part3"] is True
         and proof["decoded_indexed_sha256"] == PIXELS
         and proof["opaque_pixels"] == 60 and proof["transparent_index"] == 253,
         "人物原始來源證明不同")
    need(sha(points.read_bytes()) == POINTS, "既有49點原版收據不同")
    originals = read(points)
    need(a["control"] is False and b["control"] is True, "觀測或對照身分不同")
    for receipt in [a, b]:
        need(receipt["input_sha256"] == INPUT and receipt["seed_sha256"] == SEED
             and receipt["dos_inputs"] == 53 and receipt["end"]["steps"] == 134600000,
             "正常輸入、初始存檔或終點不同")
    need(a["end"] == b["end"], "原版完整終點不同")
    memory = (observed / "final.memory").read_bytes()
    need(memory == (control / "final.memory").read_bytes()
         and sha(memory) == a["end"]["memory_sha256"], "原版完整RAM不同")
    need(len(a["checkpoints"]) == len(b["checkpoints"]) == len(originals) == 49,
         "正常檢查點數不同")
    calls = a["calls"]
    need(len(calls) == a["source_matches"] == 13, "人物完整來源命中數不同")
    opaque = {i: v for i, v in enumerate(raw) if v != 253}
    write_sha = sha(b"".join(struct.pack("<HB", i, v) for i, v in opaque.items()))
    for c in calls:
        need(c["selected"] and not c.get("geometry_or_write_mismatch"), "人物呼叫未驗證")
        need(c["source_first_101_sha256"] == ENCODED
             and c["source_far"] == "587E:0008" and c["record_far"] == "4F22:6825"
             and c["record_words"] == [8, 0x587E, 234, 20, 6, 16],
             "完整來源與原始遠指標不同")
        need(c["entry_code12"] == "c828000052535057568b4702"
             and c["writer_code16"] == WRITERS
             and c["writer_sites"] == {"0D46:01B4": 8, "0D46:01D2": 52},
             "原始入口或寫入碼不同")
        x, y, right, bottom = c["rect"]
        need(c["registers"][0] == 101 and c["registers"][2] == x
             and c["ss_sp_words"][2] == y and right - x == 6 and bottom - y == 16
             and c["canvas_linear"] == 0x2CAE0 and c["ds_bx_words"] == [200, 320, 0, 0x2CAE]
             and c["rect"] in [[238, 38, 244, 54], [12, 142, 18, 158]],
             "原版畫布或人物幾何不同")
        need(0 < c["return_step"] - c["entry_step"] <= 100000
             and c["return_registers"][4] == (c["registers"][4] + 10) & 0xFFFF
             and c["return_segments"][1] == c["ss_sp_words"][1]
             and c["return_ip"] == c["ss_sp_words"][0]
             and c["return_cs_ip"] in ["023B:01B3", "121D:1554"],
             "人物原版返回與堆疊未驗")
        need(c["unique_writes"] == c["write_count"] == 60
             and c["sorted_local_offset_value_sha256"] == write_sha
             and c["transparent_background_unchanged"] and c["outside_rectangle_unchanged"],
             "完整寫入或底圖未驗")
        before = base64.b64decode(c["private_before_roi"], validate=True)
        after = base64.b64decode(c["private_after_roi"], validate=True)
        need(len(before) == len(after) == 96, "人物矩形原始像素長度不同")
        need(all(after[i] == (before[i] if v == 253 else v) for i, v in enumerate(raw)),
             "人物來源像素或透明背景不同")
    events = read(observed / "writes.json")
    need(len(events) == 4558 and sum(e["kind"] == "write" for e in events) == 4545,
         "人物矩形原始寫入數不同")
    owned = [{}, {}]
    native_values = [{}, {}]
    next_call = 0
    losses = {}
    same = 0
    at = 0
    last_step = 0
    drawn = []
    summaries = []
    for index, (point, counterpart, original) in enumerate(zip(a["checkpoints"], b["checkpoints"], originals)):
        need({k: v for k, v in point.items() if k != "event_count"} == counterpart,
             "人物觀測改變原版檢查點")
        for key in ["memory_sha256", "indexed_sha256", "palette_sha256", "registers", "segments", "ip", "flags", "dos_input_count"]:
            need(point[key] == original[key], "既有原版檢查點不同：" + key)
        need(point["steps"] == original["step"], "既有原版步數不同")
        name = point["snapshot_prefix"]
        need(name == f"point-{index:03d}", "檢查點檔名不同")
        for suffix, size in [(".idx", 64000), (".canvas", 64000), (".stage", 64000), (".palette", 768)]:
            data = (observed / (name + suffix)).read_bytes()
            need(len(data) == size and data == (control / (name + suffix)).read_bytes(),
                 "原版畫布／調色盤不同")
        need(sha((observed / (name + ".idx")).read_bytes()) == point["indexed_sha256"]
             and sha((observed / (name + ".palette")).read_bytes()) == point["palette_sha256"],
             "檢查點原始索引指紋不同")
        need(at <= point["event_count"] <= len(events), "寫入事件序號倒退或越界")
        while at < point["event_count"]:
            e = events[at]
            need(last_step <= e["step"] <= point["steps"], "人物寫入步數倒退")
            last_step = e["step"]
            while next_call < len(calls) and calls[next_call]["entry_step"] <= e["step"]:
                call = calls[next_call]
                x, y, _, _ = call["rect"]
                before = base64.b64decode(call["private_before_roi"], validate=True)
                for k, value in enumerate(before):
                    key = str((y + k // 6) * 320 + x + k % 6)
                    need(key not in native_values[0] or native_values[0][key] == value,
                         "人物繪製前底圖不能由原始寫入重建")
                    native_values[0][key] = value
                next_call += 1
            if e["kind"] == "draw":
                call_id = e["call"]
                need(call_id == len(drawn) + 1 and calls[call_id - 1]["return_step"] == e["step"],
                     "人物來源建立順序不同")
                c = calls[call_id - 1]
                x, y, _, _ = c["rect"]
                after = base64.b64decode(c["private_after_roi"], validate=True)
                need(all(native_values[0][str((y + k // 6) * 320 + x + k % 6)] == value
                         for k, value in enumerate(after)), "人物返回底圖不能由逐筆寫入重建")
                for k, v in opaque.items():
                    owned[0][str((y + k // 6) * 320 + x + k % 6)] = {"call": call_id, "local": k, "native": v}
                drawn.append(call_id)
            elif e["kind"] == "write":
                surface, offset = e["surface"], e["offset"]
                need(surface in [0, 1] and 0 <= offset < 64000
                     and 0 <= e["old"] <= 255 and 0 <= e["value"] <= 255
                     and len(bytes.fromhex(e["code16"])) == 16, "原始寫入欄位越界")
                key = str(offset)
                need(key in native_values[surface] and native_values[surface][key] == e["old"],
                     "原始寫入舊值不同")
                native_values[surface][key] = e["value"]
                if key in owned[surface]:
                    losses[e["site"]] = losses.get(e["site"], 0) + 1
                    same += e["old"] == e["value"]
                owned[surface].pop(key, None)
                need(e["after_cell"] == {"call": 0, "local": 0, "native": 0},
                     "本收據未驗的複製來源被保留")
            else:
                raise ValueError("未知寫入事件")
            at += 1
        actual = read(observed / (name + ".owners.json"))
        need(actual == {"main": owned[0], "stage": owned[1]}, "來源身分不能由原始寫入重建")
        canvas = (observed / (name + ".canvas")).read_bytes()
        indexed = (observed / (name + ".idx")).read_bytes()
        need(all(canvas[int(key)] == value for key, value in native_values[0].items()),
             "人物矩形全部像素不能由原始寫入重建")
        for key, cell in owned[0].items():
            need(canvas[int(key)] == raw[cell["local"]] == cell["native"],
                 "人物來源已過期")
        visible = sum(indexed[int(key)] == cell["native"] for key, cell in owned[0].items())
        summaries.append({"point": index, "step": point["steps"], "main_owned": len(owned[0]),
                          "stage_owned": len(owned[1]), "indexed_matches": visible})
    # 最後檢查點至終點無新人物；原始寫入亦不可偷偷建立來源。
    need(at == len(events) and next_call == 13 and drawn == list(range(1, 14)),
         "終點仍有未核對的人物寫入")
    need(losses == a["ownership_loss_sites"] and same == a["same_value_ownership_losses"]
         and a["verified_transferred_pixels"] == 0, "來源撤銷或轉送統計不同")
    need(all(s["main_owned"] in [0, 120] and s["stage_owned"] == 0
             and s["indexed_matches"] == s["main_owned"] for s in summaries),
         "本次人物可見來源不完整")
    need([s["main_owned"] for s in summaries[44:]] == [120, 120, 120, 0, 0],
         "正常重進／離城生命週期不同")
    saves = {}
    need({p.name for p in (observed / "saves").iterdir()} == {"COLONY00.SAV", "COLONY09.SAV"},
         "存檔清單不同")
    for p in (observed / "saves").iterdir():
        data = p.read_bytes()
        need(data == (control / "saves" / p.name).read_bytes(), "原版存檔不同")
        saves[p.name] = sha(data)
    return {"result": "PASS_PERSON_100_SOURCE_WRITES_49_NATIVE_POINTS",
            "production_connected": False, "source_calls": 13, "opaque_per_call": 60,
            "checkpoints": summaries, "dos_inputs": 53, "end": a["end"]["steps"],
            "writes": 4545, "draw_events": 13, "ownership_loss_sites": losses,
            "same_value_ownership_losses": same, "verified_transferred_pixels": 0,
            "final_memory_sha256": a["end"]["memory_sha256"], "saves_sha256": saves,
            "limitations": ["單一人物與既有正常路徑；未驗直接懸停、拖曳、游標還原、動畫或其他來源。",
                            "兩版生成候選未採用；本收據沒有HD合成、WAV或正式接線信用。"]}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["observed", "control", "source", "pixels", "points", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists()
         and output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
         "輸出須為workplace內的新檔案且擁有權相符")
    result = check(args.observed, args.control, args.source, args.pixels, args.points)
    result["checker_sha256"] = sha(Path(__file__).read_bytes())
    result["receipts_sha256"] = {str(p): sha(p.read_bytes()) for p in
        [args.observed / "draws.json", args.observed / "writes.json",
         args.control / "draws.json", args.source, args.points]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["result"], sha(output.read_bytes()))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise SystemExit("人物來源驗證拒絕：" + str(error))
