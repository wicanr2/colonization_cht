#!/usr/bin/env python3
"""規格064 DRAFT：從原始寫入獨立重建十種城內建築，不授予正式HD信用。"""
import argparse
import base64
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "a7457d86c0e587b8e06a2d94db0ade8c88a8167e4cf74a8d2910ff734f15be72"
POINTS = "821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901"
INPUT = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"
SEED = "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b"
WRITERS = {"0D46:0181": "268807035ef042fecc7402ebe7ebd03b",
           "0D46:01B4": "268807035ef042fecc7403ebe790ebcc",
           "0D46:01D2": "268807035ef042ebb5905a5b035efe79"}
RECTS = {16: [[123, 106, 196, 124]], 21: [[173, 18, 196, 45]],
         24: [[37, 45, 60, 72]], 27: [[145, 15, 168, 42]],
         35: [[128, 53, 172, 75]], 39: [[67, 54, 90, 81]],
         42: [[66, 87, 119, 124]],
         43: [[6, 14, 50, 36], [10, 76, 54, 98], [15, 102, 59, 124]],
         44: [[8, 41, 31, 68], [96, 53, 119, 80]], 45: [[123, 55, 198, 103]]}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def surface(call):
    need(call["canvas_linear"] in [0x2CAE0, 0x3C500], "未知原版畫布")
    return [0x2CAE0, 0x3C500].index(call["canvas_linear"])


def offset(call, local):
    width = call["rect"][2] - call["rect"][0]
    return (call["rect"][1] + local // width) * 320 + call["rect"][0] + local % width


def check(observed, control, source, sources, points):
    need(sha(source.read_bytes()) == SOURCE, "固定十種建築來源清冊不同")
    proof = read(source)
    need(proof["original_file"] == "BUILDING.SS"
         and proof["original_sha256"] == "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",
         "原版建築檔案不同")
    bindings = {r["ordinal"]: r for r in proof["sources"]}
    need(set(bindings) == set(RECTS), "建築來源集合不同")
    raw = {}
    for ordinal, binding in bindings.items():
        pixels = (sources / f"building-{ordinal:03}.pixels").read_bytes()
        encoded = (sources / f"building-{ordinal:03}.encoded").read_bytes()
        need(sha(pixels) == binding["decoded_indexed_sha256"]
             and len(pixels) == binding["size"][0] * binding["size"][1]
             and sum(v != 253 for v in pixels) == binding["opaque_pixels"]
             and sha(encoded) == binding["encoded_sha256"]
             and len(encoded) == binding["encoded_length"] and binding["unique_in_part3"],
             "建築完整編碼或索引不同")
        raw[ordinal] = pixels
    need(sha(points.read_bytes()) == POINTS, "既有49點原版收據不同")
    originals = read(points)
    a, b = read(observed / "draws.json"), read(control / "draws.json")
    need(a["control"] is False and b["control"] is True, "觀測與對照身分不同")
    for receipt in [a, b]:
        need(receipt["input_sha256"] == INPUT and receipt["seed_sha256"] == SEED
             and receipt["dos_inputs"] == 53 and receipt["end"]["steps"] == 134600000,
             "正常輸入、存檔或終點不同")
    need(a["end"] == b["end"], "原版完整終點不同")
    memory = (observed / "final.memory").read_bytes()
    need(memory == (control / "final.memory").read_bytes()
         and sha(memory) == a["end"]["memory_sha256"], "原版完整RAM不同")
    need(len(a["checkpoints"]) == len(b["checkpoints"]) == len(originals) == 49,
         "原版檢查點數不同")
    calls = a["calls"]
    need(len(calls) == a["source_matches"] == 130, "原版來源命中數不同")
    need(Counter(c["ordinal"] for c in calls) ==
         {ordinal: 10 * len(rects) for ordinal, rects in RECTS.items()}, "各來源命中數不同")
    for call in calls:
        ordinal = call["ordinal"]
        binding, pixels = bindings[ordinal], raw[ordinal]
        width, height = binding["size"]
        x, y, right, bottom = call["rect"]
        need(call["selected"] and not call.get("geometry_or_write_mismatch"), "未驗完整繪製")
        need(call["source_encoded_sha256"] == binding["encoded_sha256"]
             and call["record_words"][4:] == [width, height], "來源或原始紀錄不同")
        need(call["entry_code12"] == "c828000052535057568b4702"
             and call["writer_code16"]
             and all(WRITERS.get(site) == code for site, code in call["writer_code16"].items()),
             "原始入口或寫入端不同")
        need(call["registers"][0] == ordinal + 1 and call["registers"][2] == x
             and call["ss_sp_words"][2] == y and [right-x, bottom-y] == [width, height]
             and call["rect"] in RECTS[ordinal] and surface(call) == 0
             and call["ds_bx_words"] == [200, 320, 0, 0x2CAE], "原版參數或幾何不同")
        record_offset = ((call["registers"][0] & 0x7FFF) * 12 + call["ss_sp_words"][3] + 0x36) & 0xFFFF
        need(call["record_far"] == f'{call["ss_sp_words"][4]:04X}:{record_offset:04X}'
             and call["source_far"] == f'{call["record_words"][1]:04X}:{call["record_words"][0]:04X}',
             "原始遠指標不同")
        need(0 < call["return_step"] - call["entry_step"] <= 100000
             and call["return_registers"][4] == (call["registers"][4] + 10) & 0xFFFF
             and call["return_segments"][1] == call["ss_sp_words"][1]
             and call["return_ip"] == call["ss_sp_words"][0]
             and call["return_cs_ip"] == "121D:1554", "返回與原始堆疊不同")
        opaque = {i: v for i, v in enumerate(pixels) if v != 253}
        need(call["unique_writes"] == call["write_count"] == binding["opaque_pixels"]
             and call["sorted_local_offset_value_sha256"] ==
             sha(b"".join(struct.pack("<HB", i, v) for i, v in opaque.items()))
             and call["transparent_background_unchanged"]
             and call["outside_rectangle_unchanged"], "完整寫入或底圖未驗")
        before = base64.b64decode(call["private_before_roi"], validate=True)
        after = base64.b64decode(call["private_after_roi"], validate=True)
        need(len(before) == len(after) == len(pixels)
             and all(after[i] == (before[i] if v == 253 else v) for i, v in enumerate(pixels)),
             "返回圖像或透明底圖不同")
    events = read(observed / "writes.json")
    need(len(events) == 344190 and sum(e["kind"] == "write" for e in events) == 344060,
         "原始事件數不同")
    owned, native = [{}, {}], [{}, {}]
    call_writes = [dict() for _ in calls]
    writer_counts = [Counter() for _ in calls]
    active, next_call, drawn, at, last_step = None, 0, 0, 0, 0
    losses, same, summaries = Counter(), 0, []
    for index, (point, counterpart, original) in enumerate(zip(a["checkpoints"], b["checkpoints"], originals)):
        need({k: v for k, v in point.items() if k != "event_count"} == counterpart,
             "觀測改變原版檢查點")
        for key in ["memory_sha256", "indexed_sha256", "palette_sha256", "registers",
                    "segments", "ip", "flags", "dos_input_count"]:
            need(point[key] == original[key], "既有完整原版狀態不同：" + key)
        need(point["steps"] == original["step"], "原版步數不同")
        name = point["snapshot_prefix"]
        need(name == f"point-{index:03}", "檢查點檔名不同")
        for suffix, size in [(".idx", 64000), (".canvas", 64000), (".stage", 64000), (".palette", 768)]:
            data = (observed / (name + suffix)).read_bytes()
            need(len(data) == size and data == (control / (name + suffix)).read_bytes(),
                 "原版畫布或調色盤不同")
        need(sha((observed / (name + ".idx")).read_bytes()) == point["indexed_sha256"]
             and sha((observed / (name + ".palette")).read_bytes()) == point["palette_sha256"],
             "原始索引或調色盤指紋不同")
        need(at <= point["event_count"] <= len(events), "事件序號越界或倒退")
        while at < point["event_count"]:
            event = events[at]
            need(last_step <= event["step"] <= point["steps"], "原始寫入步數倒退")
            last_step = event["step"]
            while next_call < len(calls) and calls[next_call]["entry_step"] <= event["step"]:
                need(active is None, "原版繪製重入")
                active = next_call
                call = calls[active]
                sid = surface(call)
                for local, value in enumerate(base64.b64decode(call["private_before_roi"], validate=True)):
                    key = str(offset(call, local))
                    need(key not in native[sid] or native[sid][key] == value,
                         "繪製前底圖不能由原始寫入重建")
                    native[sid][key] = value
                next_call += 1
            if event["kind"] == "write":
                sid, pos = event["surface"], event["offset"]
                need(sid in [0, 1] and 0 <= pos < 64000
                     and 0 <= event["old"] <= 255 and 0 <= event["value"] <= 255
                     and len(bytes.fromhex(event["code16"])) == 16, "原始寫入欄位越界")
                key = str(pos)
                need(key in native[sid] and native[sid][key] == event["old"], "原始寫入舊值不同")
                native[sid][key] = event["value"]
                if key in owned[sid]:
                    losses[event["site"]] += 1
                    same += event["old"] == event["value"]
                owned[sid].pop(key, None)
                need(event["after_cell"] == {"call": 0, "local": 0, "native": 0},
                     "未驗的游標或複製身分被保留")
                if active is not None:
                    call = calls[active]
                    need(sid == surface(call) and event["step"] < call["return_step"],
                         "繪製寫入畫布或步數不同")
                    x, y = pos % 320 - call["rect"][0], pos // 320 - call["rect"][1]
                    width, height = bindings[call["ordinal"]]["size"]
                    local = y * width + x
                    need(0 <= x < width and 0 <= y < height
                         and local not in call_writes[active]
                         and raw[call["ordinal"]][local] == event["value"] != 253
                         and WRITERS.get(event["site"]) == event["code16"],
                         "逐筆繪製重複、超界、透明或來源不同")
                    call_writes[active][local] = event["value"]
                    writer_counts[active][event["site"]] += 1
            elif event["kind"] == "draw":
                need(active == drawn and event["call"] == drawn + 1
                     and event["step"] == calls[drawn]["return_step"], "來源建立順序不同")
                call = calls[drawn]
                sid, pixels = surface(call), raw[call["ordinal"]]
                expected = {i: v for i, v in enumerate(pixels) if v != 253}
                need(call_writes[drawn] == expected
                     and writer_counts[drawn] == call["writer_sites"], "原始繪製寫入不能重建")
                after = base64.b64decode(call["private_after_roi"], validate=True)
                need(all(native[sid][str(offset(call, i))] == value for i, value in enumerate(after)),
                     "返回底圖不能由全部寫入重建")
                for local, value in expected.items():
                    owned[sid][str(offset(call, local))] = {"call": drawn+1, "local": local, "native": value}
                active = None
                drawn += 1
            else:
                raise ValueError("未知原始事件")
            at += 1
        need(read(observed / (name + ".owners.json")) == {"main": owned[0], "stage": owned[1]},
             "來源身分不能由原始寫入重建")
        canvas = (observed / (name + ".canvas")).read_bytes()
        stage = (observed / (name + ".stage")).read_bytes()
        indexed = (observed / (name + ".idx")).read_bytes()
        for sid, data in enumerate([canvas, stage]):
            need(all(data[int(k)] == v for k, v in native[sid].items()), "檢查點全部底圖不能重建")
            for key, cell in owned[sid].items():
                ordinal = calls[cell["call"]-1]["ordinal"]
                need(data[int(key)] == cell["native"] == raw[ordinal][cell["local"]], "來源已過期")
        counts = Counter(calls[cell["call"]-1]["ordinal"] for cell in owned[0].values())
        summaries.append({"point": index, "step": point["steps"], "main_owned": len(owned[0]),
                          "stage_owned": len(owned[1]), "by_ordinal": dict(counts),
                          "indexed_matches": sum(indexed[int(k)] == v["native"] for k, v in owned[0].items())})
    need(at == len(events) and next_call == drawn == 130 and active is None, "有未核對的繪製或寫入")
    need(dict(losses) == a["ownership_loss_sites"] and same == a["same_value_ownership_losses"]
         and a["verified_transferred_pixels"] == 0, "來源撤除或轉送統計不同")
    need(all(s["stage_owned"] == 0 and s["indexed_matches"] == s["main_owned"] for s in summaries),
         "有效來源與原版可見像素不同")
    need(summaries[45]["main_owned"] == summaries[46]["main_owned"] == 6192
         and summaries[47]["main_owned"] == summaries[48]["main_owned"] == 0,
         "重進、百科返回或離城後的來源不同")
    saves = {}
    need({p.name for p in (observed/"saves").iterdir()} == {"COLONY00.SAV", "COLONY09.SAV"},
         "原版存檔清單不同")
    for path in (observed/"saves").iterdir():
        data = path.read_bytes()
        need(data == (control/"saves"/path.name).read_bytes(), "原版存檔不同")
        saves[path.name] = sha(data)
    return {"result": "PASS_BUILDING_BATCH_SOURCE_WRITES_49_NATIVE_POINTS",
            "production_connected": False, "source_count": 10, "source_calls": drawn,
            "writes": 344060, "checkpoints": summaries, "dos_inputs": 53, "end": a["end"]["steps"],
            "ownership_loss_sites": dict(losses), "same_value_ownership_losses": same,
            "verified_transferred_pixels": 0, "final_memory_sha256": a["end"]["memory_sha256"],
            "saves_sha256": saves,
            "limitations": ["十種建築與既有正常路徑；直接懸停、拖曳、游標及背景RAM還原未驗。",
                            "原版收據不授予HD合成、WAV、動畫、完整HD或正式接線信用。"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["observed", "control", "source", "sources", "points", "output"]:
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    need(output.is_relative_to((ROOT/"workplace").resolve()) and not output.exists()
         and output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出路徑或擁有權不符")
    result = check(args.observed, args.control, args.source, args.sources, args.points)
    result["checker_sha256"] = sha(Path(__file__).read_bytes())
    result["receipts_sha256"] = {str(p): sha(p.read_bytes()) for p in
        [args.observed/"draws.json", args.observed/"writes.json", args.control/"draws.json", args.source, args.points]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(result["result"], sha(output.read_bytes()))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit("建築來源驗證拒絕："+str(error))
