"""規格070 DRAFT：獨立重建正常單位圖鑑的ICONS來源與逐寫；不安裝HD。"""
import argparse
import base64
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import struct

from check_hd_building_nine_lifecycle import event_stream, sha_file

WRITERS = {"0D46:0181": "268807035ef042fecc7402ebe7ebd03b",
           "0D46:01B4": "268807035ef042fecc7403ebe790ebcc",
           "0D46:01D2": "268807035ef042ebb5905a5b035efe79"}
SEED = "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b"


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check(observed, control, build, sources, entry_report, points):
    meta, entry, originals = read(build), read(entry_report), read(points)
    need(meta["source_receipt_sha256"]=="e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d","原版來源清冊不同")
    need(entry["original_pixels_only"] is True and entry["production_connected_new_sources"] is False,"不是正常原版GUI收據")
    need(originals==[f["state"] for f in entry["samples"]],"GUI截點與實際擷取不同")
    POINTS, INPUT=meta["gui_points_sha256"],meta["gui_inputs_sha256"]
    need(meta["entry_report_sha256"] == sha_file(entry_report)
         and sha_file(points) == POINTS and meta["source_count"] == 131, "固定來源或正常路徑不同")
    bindings = {f["research_id"]: f for f in meta["sources"]}
    need(len(bindings) == 131 and all(f["file"] == "ICONS.SS" for f in bindings.values()), "小圖像來源集合不同")
    raw, opaque = {}, {}
    for source_id, f in bindings.items():
        pixels = (sources / f"{source_id:04d}.idx").read_bytes()
        need(sha(pixels) == f["indexed_sha256"] and len(pixels) == f["size"][0]*f["size"][1], "完整索引來源不同")
        raw[source_id] = pixels
        opaque[source_id] = {i: v for i, v in enumerate(pixels) if v != 253}
        need(len(opaque[source_id]) == f["opaque_pixels"], "不透明點數不同")
    a, b = read(observed / "draws.json"), read(control / "draws.json")
    need(a["control"] is False and b["control"] is True and a["end"] == b["end"], "完整原版終點不同")
    need((observed / "final.memory").read_bytes() == (control / "final.memory").read_bytes()
         and sha_file(observed / "final.memory") == a["end"]["memory_sha256"], "完整原版RAM不同")
    for d in [a, b]:
        need(d["input_sha256"] == INPUT and d["seed_sha256"] == SEED and d["dos_inputs"] == meta["dos_inputs_at_end"]
             and d["end"]["steps"] == meta["end_step"], "輸入、seed或終點不同")
    need(len(a["checkpoints"]) == len(b["checkpoints"]) == len(originals) == meta["gui_points"], "正常檢查點缺漏")
    calls = a["calls"]
    need(len(calls)==a["source_matches"]>0 and set(c["research_id"] for c in calls).issubset(bindings),"來源呼叫集合不同")
    need(all(c["source_candidates"]==[c["research_id"]] for c in calls),"完整清冊的來源別名尚未解開")
    for c in calls:
        f = bindings[c["research_id"]]
        x, y, right, bottom = c["rect"]
        w, h = f["size"]
        need(c["selected"] and not c.get("geometry_or_write_mismatch")
             and c["source_encoded_sha256"] == f["encoded_sha256"]
             and c["record_words"][4:] == [w, h], "來源或完整繪製不同")
        need(c["canvas_linear"] == 0x2CAE0 and c["ds_bx_words"] == [200, 320, 0, 0x2CAE]
             and 0 <= x < right <= 320 and 0 <= y < bottom <= 200 and [right-x, bottom-y] == [w, h]
             and c["registers"][0] == f["ordinal"]+1 and c["registers"][2] == x
             and c["ss_sp_words"][2] == y, "原版參數、畫布或幾何不同")
        off = ((c["registers"][0] & 0x7FFF)*12+c["ss_sp_words"][3]+0x36) & 0xFFFF
        need(c["record_far"] == f'{c["ss_sp_words"][4]:04X}:{off:04X}'
             and c["source_far"] == f'{c["record_words"][1]:04X}:{c["record_words"][0]:04X}', "原始定位不同")
        need(c["entry_code12"] == "c828000052535057568b4702" and c["writer_code16"]
             and all(WRITERS.get(site) == code for site, code in c["writer_code16"].items()), "繪圖指令不同")
        need(0 < c["return_step"]-c["entry_step"] <= 100000
             and c["return_registers"][4] == (c["registers"][4]+10) & 0xFFFF
             and c["return_segments"][1] == c["ss_sp_words"][1] and c["return_ip"] == c["ss_sp_words"][0]
             and c["return_cs_ip"] == f'{c["ss_sp_words"][1]:04X}:{c["ss_sp_words"][0]:04X}', "返回邊界不同")
        expected = opaque[c["research_id"]]
        need(c["unique_writes"] == c["write_count"] == len(expected)
             and c["sorted_local_offset_value_sha256"] == sha(b"".join(struct.pack("<HB", i, v) for i, v in expected.items()))
             and c["transparent_background_unchanged"] and c["outside_rectangle_unchanged"], "完整寫入或底圖不同")
        before = base64.b64decode(c["private_before_roi"], validate=True)
        after = base64.b64decode(c["private_after_roi"], validate=True)
        need(len(before) == len(after) == w*h
             and all(after[i] == (before[i] if v == 253 else v) for i, v in enumerate(raw[c["research_id"]])), "透明底圖或返回圖不同")

    def position(call, local):
        w = bindings[call["research_id"]]["size"][0]
        return (call["rect"][1]+local//w)*320+call["rect"][0]+local%w

    owned, native = [{}, {}], [{}, {}]
    events = iter(event_stream(observed / "writes.json"))
    active, next_call, drawn, at, previous = None, 0, 0, 0, 0
    writes, sites, losses, same, kinds, summaries = {}, Counter(), Counter(), 0, Counter(), []
    for index, (point, counterpart, original) in enumerate(zip(a["checkpoints"], b["checkpoints"], originals)):
        need({k: v for k, v in point.items() if k != "event_count"} == counterpart, "觀測改變原版狀態")
        need(point["steps"] == original["step"] and all(point[k] == original[k] for k in
             ["memory_sha256", "indexed_sha256", "palette_sha256", "registers", "segments", "ip", "flags", "dos_input_count"]), "既有完整原版收據不同")
        name = point["snapshot_prefix"]
        for suffix, size in [(".idx", 64000), (".canvas", 64000), (".stage", 64000), (".palette", 768)]:
            data = (observed / (name+suffix)).read_bytes()
            need(len(data) == size and data == (control / (name+suffix)).read_bytes(), "原始像素或DAC不同")
        need(sha_file(observed / (name+".idx")) == point["indexed_sha256"]
             and sha_file(observed / (name+".palette")) == point["palette_sha256"], "原始像素指紋不同")
        need(at <= point["event_count"] <= a["raw_event_count"], "事件序號不同")
        while at < point["event_count"]:
            e = next(events)
            need(previous <= e["step"] <= point["steps"], "原始事件倒退")
            previous = e["step"]
            while next_call < len(calls) and calls[next_call]["entry_step"] <= e["step"]:
                need(active is None, "原版繪製重入")
                active = next_call
                c = calls[active]
                for local, value in enumerate(base64.b64decode(c["private_before_roi"], validate=True)):
                    pos = position(c, local)
                    need(pos not in native[0] or native[0][pos] == value, "繪製前底圖不能重建")
                    native[0][pos] = value
                next_call += 1
            kinds[e["kind"]] += 1
            if e["kind"] == "write":
                sid, pos = e["surface"], e["offset"]
                need(sid in [0, 1] and 0 <= pos < 64000 and 0 <= e["old"] <= 255 and 0 <= e["value"] <= 255
                     and len(bytes.fromhex(e["code16"])) == 16, "原始寫入欄位不同")
                need(pos in native[sid] and native[sid][pos] == e["old"], "原始寫入舊值不能重建")
                native[sid][pos] = e["value"]
                if pos in owned[sid]:
                    losses[e["site"]] += 1
                    same += e["old"] == e["value"]
                owned[sid].pop(pos, None)
                need(e["after_cell"] == {"call": 0, "local": 0, "native": 0}, "未知後畫保留過期來源")
                if active is not None:
                    c = calls[active]
                    w, h = bindings[c["research_id"]]["size"]
                    x, y = pos % 320-c["rect"][0], pos//320-c["rect"][1]
                    local = y*w+x
                    need(sid == 0 and e["step"] < c["return_step"] and 0 <= x < w and 0 <= y < h
                         and local not in writes and opaque[c["research_id"]].get(local) == e["value"]
                         and WRITERS.get(e["site"]) == e["code16"], "來源逐寫重複、超界或色號不同")
                    writes[local] = e["value"]
                    sites[e["site"]] += 1
            elif e["kind"] == "draw":
                need(active == drawn and e["call"] == drawn+1 and e["step"] == calls[drawn]["return_step"], "來源建立順序不同")
                c = calls[drawn]
                need(writes == opaque[c["research_id"]] and sites == c["writer_sites"], "完整逐寫不能重建")
                need(all(native[0][position(c, i)] == v for i, v in enumerate(base64.b64decode(c["private_after_roi"], validate=True))), "返回底圖不能重建")
                for local, value in writes.items():
                    owned[0][position(c, local)] = {"call": drawn+1, "local": local, "native": value}
                drawn += 1
                active, writes, sites = None, {}, Counter()
            else:
                raise ValueError("未知事件")
            at += 1
        expected_owners = {"main": {str(k): v for k, v in owned[0].items()}, "stage": {str(k): v for k, v in owned[1].items()}}
        need(read(observed / (name+".owners.json")) == expected_owners, "來源身分不能由逐寫重建")
        for sid, suffix in enumerate([".canvas", ".stage"]):
            canvas = (observed / (name+suffix)).read_bytes()
            need(all(canvas[k] == v for k, v in native[sid].items()), "全部追蹤底圖不能重建")
            need(all(canvas[k] == v["native"] == raw[calls[v["call"]-1]["research_id"]][v["local"]]
                     for k, v in owned[sid].items()), "有效來源過期")
        indexed = (observed / (name+".idx")).read_bytes()
        counts = Counter(calls[v["call"]-1]["research_id"] for v in owned[0].values())
        summaries.append({"point": index, "step": point["steps"], "main_owned": len(owned[0]),
                          "stage_owned": len(owned[1]), "by_research_id": dict(counts),
                          "indexed_matches": sum(indexed[k] == v["native"] for k, v in owned[0].items())})
    need(at == a["raw_event_count"] and next(events, None) is None and next_call == drawn == len(calls)
         and active is None, "未核對的繪製或寫入")
    need(losses == a["ownership_loss_sites"] and same == a["same_value_ownership_losses"]
         and a["verified_transferred_pixels"] == 0, "來源撤銷統計不同")
    need(all(p["main_owned"] == p["indexed_matches"] and p["stage_owned"] == 0 for p in summaries), "來源可見像素不同")
    saves = {}
    need({p.name for p in (observed / "saves").iterdir()} == {"COLONY09.SAV"}, "原版存檔清單不同")
    for path in (observed / "saves").iterdir():
        need(path.read_bytes() == (control / "saves" / path.name).read_bytes(), "原版存檔不同")
        saves[path.name] = sha_file(path)
    observations=[]
    for ident in sorted({c["research_id"] for c in calls}):
        group=[c for c in calls if c["research_id"]==ident]
        f=bindings[ident]
        observations.append({"research_id":ident,"ordinal":f["ordinal"],"calls":len(group),
                             "encoded_sha256":f["encoded_sha256"],"indexed_sha256":f["indexed_sha256"],
                             "size":f["size"],"opaque_pixels":f["opaque_pixels"],
                             "write_sha256":sorted({c["sorted_local_offset_value_sha256"] for c in group}),
                             "source_far":sorted({c["source_far"] for c in group}),
                             "record_far":sorted({c["record_far"] for c in group}),
                             "descriptors":sorted({tuple(c["ds_bx_words"]) for c in group}),
                             "writer_code16":{site:code for c in group for site,code in c["writer_code16"].items()},
                             "first_entry_step":min(c["entry_step"] for c in group)})
    return {"result": "PASS_UNIT_SOURCE_WRITES_NATIVE_GUI_POINTS", "production_connected": False,
            "candidate_sources": 131, "hit_sources":len(set(c["research_id"] for c in calls)), "source_calls": drawn, "source_observations":observations, "raw_events": at, "event_kinds": dict(kinds),
            "checkpoints": summaries, "dos_inputs": meta["dos_inputs_at_end"], "end": a["end"], "saves_sha256": saves,
            "ownership_loss_sites": dict(losses), "same_value_ownership_losses": same,
            "verified_transferred_pixels": 0,
            "limitations": ["131候選及本次實際命中幀；不授予未命中幀、世界行走、戰鬥或動畫信用。",
                            "未知後畫含同值撤銷；游標、RAM還原與HD合成另驗。"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["observed", "control", "build", "sources", "entry-report", "points", "output"]:
        parser.add_argument("--"+name, type=Path, required=True)
    a = parser.parse_args()
    out = a.output.resolve()
    need(Path("/.dockerenv").is_file() and os.getuid() != 0 and not out.exists()
         and out.parent.stat().st_uid == os.getuid(), "輸出路徑或擁有權不同")
    result = check(a.observed, a.control, a.build, a.sources, a.entry_report, a.points)
    result["checker_sha256"] = sha_file(Path(__file__))
    result["receipts_sha256"] = {str(p): sha_file(p) for p in
                                 [a.observed/"draws.json", a.observed/"writes.json", a.control/"draws.json", a.build, a.entry_report, a.points]}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(result["result"], result["source_calls"], result["raw_events"], sha_file(out), flush=True)
