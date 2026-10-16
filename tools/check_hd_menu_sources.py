#!/usr/bin/env python3
"""規格069 DRAFT：核對冷啟動背景與三種底紋來源，不授予正式HD信用。"""
from pathlib import Path
import argparse, collections, hashlib, json, os

SOURCE_IDS = {1265: "OPENTILE.SS", 1287: "PARCH.SS", 1552: "WOODTILE.SS"}
WRITERS = {
    0x181: "268807035ef042fecc7402ebe7ebd03b",
    0x1b4: "268807035ef042fecc7403ebe790ebcc",
    0x1d2: "268807035ef042ebb5905a5b035efe79",
}
COPIES = {
    (0xcba, 0x9c): "f3a5a403f3790c81ee00808cd981c100",
    (0xcba, 0x9e): "a403f3790c81ee00808cd981c100088e",
    (0xcba, 0xca): "f3a503f3790c81ee00808cd981c10008",
}
MAIN, STAGE = 0x2cae0, 0x3c500

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def check(root, decoded, output, expected_points=12, expected_inputs=10):
    assert Path("/.dockerenv").is_file() and os.getuid() != 0
    assert output.parent.stat().st_uid == os.getuid() and not output.exists()
    observed, control = root / "observed", root / "control"
    a, b = read(observed / "draws.json"), read(control / "draws.json")
    assert a["end"] == b["end"] and a["dos_inputs"] == b["dos_inputs"] == expected_inputs
    assert (observed / "final.memory").read_bytes() == (control / "final.memory").read_bytes()
    assert len(a["checkpoints"]) == len(b["checkpoints"]) == expected_points
    for x, y in zip(a["checkpoints"], b["checkpoints"]):
        assert {k: v for k, v in x.items() if k != "event_count"} == y
        for suffix in [".idx", ".canvas", ".stage", ".palette"]:
            assert (observed / (x["snapshot_prefix"] + suffix)).read_bytes() == (control / (y["snapshot_prefix"] + suffix)).read_bytes()
    assert sha(decoded / "catalog.json") == "e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d"
    catalog = read(decoded / "catalog.json")
    frames = {f["research_id"]: f for f in catalog["frames"]}
    pixels = {}
    for n in SOURCE_IDS.keys() | {1181}:
        f = frames[n]
        p = decoded / "pixels" / f"{n:04d}.idx"
        assert sha(p) == f["indexed_sha256"]
        pixels[n] = p.read_bytes()
    trace = read(observed / "background.json")
    assert len(trace["calls"]) == 3
    calls = sorted(trace["calls"], key=lambda c: c["return_step"])
    assert {c["source_id"] for c in calls} == set(SOURCE_IDS)
    events = [json.loads(l) for l in (observed / "background-writes.jsonl").open()]
    assert len(events) == trace["events"]
    previous = -1
    mirror = {}
    for e in events:
        assert len(e) == 14 and previous <= e[0]
        previous = e[0]
        if e[1] in mirror:
            assert mirror[e[1]] == e[2], ("old byte differs", e)
        mirror[e[1]] = e[3]
    draw_checks = []
    for c in calls:
        n, start, end, base = c["source_id"], c["entry_step"], c["return_step"], c["base"]
        f = frames[n]
        assert f["file"] == SOURCE_IDS[n] and f["size"] == c["size"] == [32, 24]
        assert c["source_pixels_sha256"] == f["indexed_sha256"]
        assert c["entry"]["record_words"][4:6] == [32, 24]
        assert c["entry"]["ds_bx_words"][:2] == [24, 32]
        assert c["entry"]["registers"][0] == 1
        writes = [e for e in events if start <= e[0] < end and base <= e[1] < base + 768]
        assert len(writes) == 768 and {e[1] - base for e in writes} == set(range(768))
        for e in writes:
            assert e[4] == 0xd46 and e[5] in WRITERS and e[13] == WRITERS[e[5]]
            assert e[3] == pixels[n][e[1] - base]
        assert (observed / f"texture-{n}.after").read_bytes() == pixels[n]
        draw_checks.append({"source_id": n, "file": f["file"], "entry_step": start, "return_step": end, "base": base, "writes": 768, "indexed_sha256": f["indexed_sha256"]})
    pik_writes = [e for e in events if 17830466 <= e[0] < 18367087 and e[4] == 0x11b5 and e[5] in {0x4ee, 0x54a} and STAGE <= e[1] < STAGE + 64000]
    assert len(pik_writes) == 64000 and {e[1] - STAGE for e in pik_writes} == set(range(64000))
    actual = bytearray(64000)
    for e in pik_writes:
        actual[e[1] - STAGE] = e[3]
    assert bytes(actual) == pixels[1181]
    anchors = []
    for anchor in trace.get("anchors") or []:
        p = observed / anchor["pixels_file"]
        assert sha(p) == anchor["pixels_sha256"] and len(p.read_bytes()) == 64000
        different = sum(a != b for a, b in zip(p.read_bytes(), pixels[1181]))
        assert different == anchor["different_pixels"] and anchor["exact_pik"] == (different == 0)
        anchors.append({"step": anchor["step"], "different_pixels": different, "exact_pik": different == 0})
    owners, transfers, revoked = {}, collections.Counter(), collections.Counter()
    pending, cursor_pairs = {}, collections.Counter()
    underlays = {}
    unverified_copies = collections.Counter()
    at = done = 0
    points = []
    output.mkdir()
    for point in a["checkpoints"]:
        limit = point["steps"]
        while at < len(events) and events[at][0] < limit:
            e = events[at]
            while done < len(calls) and calls[done]["return_step"] <= e[0]:
                c = calls[done]
                for k, value in enumerate(pixels[c["source_id"]]):
                    owners[c["base"] + k] = (c["source_id"], k, value)
                done += 1
            step, addr, old, value, cs, ip, ds, si, es, di, ax, cx, flags, code = e
            if MAIN <= addr < MAIN + 64000:
                if (cs, ip) == (0xb68, 0x51c) and ds == 0xa000 and es == 0x2cae and code == "f3a48ac82bf92bf103f303fafecc75f0":
                    delta = addr - (es * 16 + di)
                    src = si + delta
                    if delta == 0 and 0xfa00 <= src < 0xfc00:
                        k = src & 255
                        if src >= 0xfb00:
                            cell = owners.pop(addr, None)
                            if cell is not None and cell[2] != old:
                                cell = None
                            under = underlays.pop(addr, None)
                            if under is not None and under[3] != old: under = None
                            pending[addr] = (cell, old, value, k, under)
                            at += 1
                            continue
                        prior = pending.pop(addr, None)
                        if prior is not None and prior[3] == k and old == prior[2] and value == prior[1]:
                            if prior[0] is not None:
                                owners[addr] = prior[0]
                                cursor_pairs[prior[0][0]] += 1
                            if prior[4] is not None: underlays[addr] = prior[4]
                            at += 1
                            continue
                pending.clear()
                if (cs, ip, code) == (0xd21,0x12c,"26882547feca740afecd75dfacb504eb"):
                    prior_cell=owners.get(addr)
                    under=underlays.get(addr)
                    if prior_cell is not None and prior_cell[2]==old:
                        underlays[addr]=(*prior_cell,value)
                    elif under is not None and under[3]==old:
                        underlays[addr]=(*under[:3],value)
                    else: underlays.pop(addr,None)
                else: underlays.pop(addr,None)
            cell = None
            if (cs, ip) in COPIES and addr < 0xa0000:
                delta = addr - (es * 16 + di)
                # OpAddr also survives internal writes during an instruction.
                # Only the exact, non-wrapping DS:SI -> ES:DI contract propagates.
                valid = code == COPIES[(cs, ip)] and not flags & 0x400
                valid = valid and delta in ({0} if ip == 0x9e else {0, 1})
                valid = valid and si + delta < 65536 and di + delta < 65536
                source = ds * 16 + si + delta
                valid = valid and 0 <= source < 0xa0000
                if valid:
                    cell = owners.get(source)
                    if cell:
                        assert value == cell[2], ("copy source byte differs", e, cell)
                        transfers[cell[0]] += 1
                else:
                    unverified_copies[(cs, ip)] += 1
            previous_cell = owners.pop(addr, None)
            if previous_cell and cell is None:
                revoked[(cs, ip, old == value)] += 1
            if cell:
                owners[addr] = cell
            at += 1
        canvas = (observed / (point["snapshot_prefix"] + ".canvas")).read_bytes()
        visible = {str(addr - MAIN): {"source_id": c[0], "local": c[1], "native": c[2]} for addr, c in owners.items() if MAIN <= addr < MAIN + 64000}
        for offset, cell in visible.items():
            assert canvas[int(offset)] == cell["native"]
        name = point["snapshot_prefix"] + ".texture-owners.json"
        (output / name).write_text(json.dumps(visible, sort_keys=True) + "\n")
        under = {str(addr-MAIN): {"source_id": c[0], "local":c[1], "native":c[2],"glyph_native":c[3]} for addr,c in underlays.items() if MAIN<=addr<MAIN+64000}
        for k,c in under.items(): assert canvas[int(k)]==c['glyph_native']
        under_name=point['snapshot_prefix']+'.texture-underlays.json'
        (output/under_name).write_text(json.dumps(under,sort_keys=True)+'\n')
        points.append({"step":limit,"owners_file":name,"underlays_file":under_name,"visible":dict(collections.Counter(c["source_id"] for c in visible.values())),"underlays":len(under)})
    assert transfers[1265] > 0
    print("VISIBLE_SOURCE_IDS",sorted({n for p in points for n in p["visible"]}),"TRANSFERS",dict(transfers),"CURSOR_PAIRS",dict(cursor_pairs),flush=True)
    assert len(points) == expected_points
    result = {
        "result": "PASS_MENU_INDEPENDENT_SOURCE_AND_UNDERLAY_MODELS",
        "production_connected": False, "checkpoints": expected_points, "dos_inputs": expected_inputs,
        "events": len(events), "texture_sources": draw_checks, "texture_transfer_writes": dict(transfers), "texture_cursor_pairs": dict(cursor_pairs),
        "unverified_copy_context_writes": {f"{cs:04X}:{ip:04X}":count for (cs,ip),count in sorted(unverified_copies.items())},
        "revocations": [{"cs_ip": f"{cs:04X}:{ip:04X}", "same_value": same, "count": count} for (cs, ip, same), count in sorted(revoked.items())],
        "points": points, "visible_source_ids":sorted({n for p in points for n in p["visible"]}), "opentile_positive_points":sum(p["visible"].get(1265,0)>0 for p in points), "pik_native_write_count": 64000,
        "pik_decoded_sha256": frames[1181]["indexed_sha256"],
        "pik_first_write_step": pik_writes[0][0], "pik_last_write_step": pik_writes[-1][0],
        "pik_video_memory_comparisons": anchors,
        "trace_sha256": sha(observed / "background.json"),
        "events_sha256": sha(observed / "background-writes.jsonl"),
        "checker_sha256": sha(Path(__file__)),
        "limitations": [
            "Original states and three source textures only; formal rendering is checked separately.",
            "PIK presentation is checked separately using full settled-frame pixel recognition; VGA round-trip ownership is not claimed.",
            "Visibility and cursor restoration are limited to the exact recorded source counts and checkpoints.",
            "One standard cursor pair contract inherited from spec066; other cursors, palette rendering, animations and full coverage remain unverified."
        ]
    }
    fixture_path=root/'fixture.json'
    if fixture_path.exists():
        fixture=read(fixture_path);comparisons=[]
        for sample in fixture['samples']:
            if 'proof' not in sample:continue
            proof=read(Path(sample['proof']));idx=sample['point']
            for source_id,prefix in [(1265,'texture'),(1552,'world_texture'),(1287,'parch')]:
                if prefix+'_cells' not in proof:continue
                for key,suffix in [(prefix+'_cells','owners'),(prefix+'_underlays','underlays')]:
                    model=read(output/f'point-{idx:03d}.texture-{suffix}.json')
                    model={k:v for k,v in model.items() if v['source_id']==source_id}
                    assert model==proof[key],(sample['label'],key)
            row={'sample':sample['label'],'owners':len(proof['texture_cells']),'underlays':len(proof['texture_underlays'])}
            if 'parch_cells' in proof:
                row.update(parch_owners=len(proof['parch_cells']),parch_underlays=len(proof['parch_underlays']))
            comparisons.append(row)
        assert len(comparisons)==sum('proof' in sample for sample in fixture['samples'])
        result['gui_model_comparisons']=comparisons
        result['fixture_sha256']=sha(fixture_path)
    (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["result"], result["texture_transfer_writes"], [p["visible"] for p in points], flush=True)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["root", "decoded", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument('--expected-points',type=int,default=12)
    parser.add_argument('--expected-inputs',type=int,default=10)
    args = parser.parse_args()
    assert 1<=args.expected_points<=100
    assert 1<=args.expected_inputs<=10000
    check(args.root, args.decoded, args.output,args.expected_points,args.expected_inputs)

if __name__ == "__main__":
    main()
