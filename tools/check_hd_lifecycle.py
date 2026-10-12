"""核對首座建築的正常GUI生命週期與單一游標來源；不授權正式HD。"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def check(root, gui, ida_path, game):
    for name, fingerprint in {
        "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
        "BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",
    }.items():
        assert sha(game / name) == fingerprint, name
    build = read(root / "build.json")
    assert sha(root / "module/main.go") == build["generated_source_sha256"]
    assert sha(root / "lifecycle-probe") == build["binary_sha256"]
    assert sha(gui / "check.json") == build["gui_check_sha256"]
    assert sha(gui / "gui.inputs.json") == build["gui_inputs_sha256"] == "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"
    assert sha(gui / "gui.display-events.json") == build["gui_events_sha256"] == "842e59ed45429998c83112ac1c106023d47d1c5a77e5bf92b74059f83a6fc1a1"
    receipt = read(gui / "check.json")
    assert receipt["result"] == "PASS_NATIVE_GUI_BUILDING_LIFECYCLE_INPUTS"
    assert len(receipt["checks"]) == 55 and build["inputs"] == 53 and build["end"] == 134600000
    observed, control = root / "observed", root / "control"
    a, b = read(observed / "writes.json"), read(control / "writes.json")
    state = read(gui / "gui.json")["state"]
    keys = ["steps", "memory_sha256", "indexed_sha256", "palette_sha256",
            "registers", "segments", "ip", "flags"]
    assert all(a[k] == b[k] == state["frame_sha256" if k == "indexed_sha256" else k] for k in keys)
    assert a["steps"] == 134600000
    for name in ["COLONY09.SAV", "COLONY00.SAV"]:
        assert sha(observed / "saves" / name) == sha(control / "saves" / name) == sha(gui / "save" / name)
    points = read(observed / "gui-points.json")
    assert points == read(control / "gui-points.json") and len(points) == 49
    assert all(p["gui_state_equal"] for p in points)
    for p in points:
        for ext in [".idx", ".pal", ".canvas.idx", ".vga-tail.idx"]:
            name = p["snapshot_prefix"] + ext
            assert (observed / name).read_bytes() == (control / name).read_bytes(), name
    d = read(observed / "draw-boundary.json")
    assert d["source_encoded_sha256"] == "7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a"
    native_writes = d["writes"]
    assert len(native_writes) == 440
    before = (observed / "before-draw.idx").read_bytes()
    after = (observed / "after-draw.idx").read_bytes()
    assert len(before) == len(after) == 64000
    roi_indices = [y * 320 + x for y in range(13, 40) for x in range(56, 79)]

    def roi(data):
        return bytes(data[i] for i in roi_indices)

    assert all(after[int(addr) - 0x2CAE0] == row[1] for addr, row in native_writes.items())
    events, calls = d["post_return_write_events"], d["post_return_same_source_calls"]
    assert len(events) == 19463 and len(calls) == 9
    assert sum(e[4] == e[5] for e in events) == 5986
    for call in calls:
        selected = [e for e in events if call["entry_step"] <= e[0] < call["return_step"]]
        assert len(selected) == 440
        assert Counter(str(e[3]) for e in selected) == Counter({k: 1 for k in native_writes})
        assert all(e[5] == native_writes[str(e[3])][1] for e in selected)
    data = bytearray(after)
    timeline = [(e[0], 0, "write", e) for e in events]
    for call in calls:
        timeline.extend([(call["entry_step"], 1, "entry", call),
                         (call["return_step"], 1, "return", call)])
    timeline.extend((p["step"], 2, "point", p) for p in points if p["step"] >= d["return_step"])
    for _, _, kind, row in sorted(timeline, key=lambda r: (r[0], r[1])):
        if kind == "write":
            i = row[3] - 0x2CAE0
            assert i in roi_indices and data[i] == row[4], "write continuity"
            data[i] = row[5]
        elif kind in ["entry", "return"]:
            key = "before_roi_sha256" if kind == "entry" else "after_roi_sha256"
            assert hashlib.sha256(roi(data)).hexdigest() == row[key]
        else:
            assert roi(data) == roi((observed / (row["snapshot_prefix"] + ".canvas.idx")).read_bytes())
    assert roi(data) == roi((observed / "post-return-canvas.idx").read_bytes())
    cursor = read(observed / "cursor-writes.json")
    groups, writes = cursor["source_groups"], cursor["events"]
    source = bytes.fromhex(groups[0]["source_hex"])
    source_hash = hashlib.sha256(source).hexdigest()
    assert len(source) == 256 and source_hash == "47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03"
    assert sum(v != 255 for v in source) == 82
    assert len(groups) == 114 and len(writes) == 29184
    assert all(g["source_linear"] == 0x1CD74 and g["source_sha256"] == source_hash and
               g["source_hex"] == groups[0]["source_hex"] for g in groups)
    for n in range(114):
        group = writes[n * 256:(n + 1) * 256]
        assert [e[3] for e in group] == list(range(0xAFB00, 0xAFC00))
        assert all(e[1:3] == [0xB68, 0x547] and (v == 255 or e[5] == v)
                   for e, v in zip(group, source))
        assert group[0][0] == groups[n]["step"]
        if n:
            previous = writes[(n - 1) * 256:n * 256]
            assert all(a[5] == b[4] for a, b in zip(previous, group)), "cursor write continuity"
    ida = read(ida_path)
    assert ida["kernel_version"] == "9.4"
    assert ida["original_sha256"] == sha(game / "VICEROY.EXE")
    matches = ida["patterns"]["cursor_writer"]["matches"]
    assert len(matches) == 1 and matches[0]["ida_ea"] == 0x1AAC7
    insns = {r["ida_ea"]: r["bytes"] for r in matches[0]["function"]["instructions"]}
    for ea, code in {0x1AAB4: "bed406", 0x1AAB7: "bf00fb", 0x1AABA: "b90001",
                     0x1AABD: "ac", 0x1AABE: "3cff", 0x1AAC0: "7505",
                     0x1AAC2: "268a8500ff", 0x1AAC7: "268805"}.items():
        assert insns[ea] == code, hex(ea)
    cursor_roi = [e for e in events if e[1:3] == [0xB68, 0x51C]]
    assert len(cursor_roi) == 2100
    pairs = []
    for n in range(5):
        paint = cursor_roi[n * 420:n * 420 + 210]
        restore = cursor_roi[n * 420 + 210:(n + 1) * 420]
        assert [e[3] for e in paint] == [e[3] for e in restore]
        assert all(a[4] == b[5] and a[5] == b[4] for a, b in zip(paint, restore))
        assert [e for e in events if paint[0][0] <= e[0] <= restore[-1][0]] == paint + restore
        assert sum(e[4] != e[5] for e in paint) == 82
        assert all(not (paint[0][0] <= p["step"] <= restore[-1][0]) for p in points)
        pairs.append([paint[0][0], restore[-1][0]])
    gui_events = read(gui / "gui.display-events.json")
    differences = Counter()
    for p in points:
        e = next(e for e in gui_events if e["action"] == "apply" and
                 e["step"] == p["step"] and e["dos_input_count"] == p["dos_input_count"])
        x, y = e["dos_mouse"]["x"], e["dos_mouse"]["y"]
        prefix = p["snapshot_prefix"]
        idx = (observed / (prefix + ".idx")).read_bytes()
        canvas = (observed / (prefix + ".canvas.idx")).read_bytes()
        tail = (observed / (prefix + ".vga-tail.idx")).read_bytes()
        assert len(idx) == len(canvas) == 64000 and len(tail) == 1024
        latest = max(n for n, g in enumerate(groups) if g["step"] < p["step"])
        assert writes[(latest + 1) * 256 - 1][0] < p["step"]
        assert tail[256:512] == bytes(e[5] for e in writes[latest * 256:(latest + 1) * 256])
        assert all(tail[256 + i] == (tail[i] if v == 255 else v) for i, v in enumerate(source))
        for j in range(16):
            for i in range(16):
                if x + i >= 320 or y + j >= 200:
                    continue
                pos, k = (y + j) * 320 + x + i, j * 16 + i
                assert canvas[pos] == tail[k] and idx[pos] == tail[256 + k]
                if source[k] != 255:
                    assert idx[pos] == source[k]
        assert all(idx[i] == canvas[i] for i in range(64000)
                   if not (x <= i % 320 < x + 16 and y <= i // 320 < y + 16))
        differences[sum(a != b for a, b in zip(idx, canvas))] += 1
    return {
        "result": "PASS_NATIVE_GUI_BUILDING_LIFECYCLE_AND_CURSOR",
        "inference": "confirmed only for this normal GUI receipt and one cursor source",
        "gui_checks": 55, "native_state_points": 49, "dos_inputs": 53, "end": 134600000,
        "original_cpu_ram_vga_dac_and_saves_equal": True,
        "ordered_roi_writes": len(events), "same_value_writes": 5986, "redraw_calls": 9,
        "cursor_source_sha256": source_hash, "cursor_opaque_points": 82,
        "cursor_buffer_groups": 114, "cursor_roi_inverse_pairs": pairs,
        "native_cursor_difference_counts": dict(differences),
        "receipt_sha256": {"build": sha(root / "build.json"), "gui": sha(gui / "check.json"),
                          "stream": sha(observed / "draw-boundary.json"),
                          "cursor": sha(observed / "cursor-writes.json"), "ida": sha(ida_path)},
        "limits": ["No production HD or runtime HD-switch acceptance.",
                   "Only five completed inverse cursor-copy pairs were observed.",
                   "No audio equivalence, full language coverage, terrain or people acceptance."],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence-dir", type=Path, required=True)
    p.add_argument("--gui-dir", type=Path, required=True)
    p.add_argument("--cursor-ida", type=Path, required=True)
    p.add_argument("--game-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert Path("/.dockerenv").is_file() and os.getuid() != 0
    if not all((a.game_root / n).is_file() for n in ["VICEROY.EXE", "BUILDING.SS"]):
        print("SKIP: 缺少合法原版 VICEROY.EXE 或 BUILDING.SS")
        raise SystemExit(77)
    assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
    result = check(a.evidence_dir, a.gui_dir, a.cursor_ida, a.game_root)
    result["audit_source_sha256"] = sha(Path(__file__))
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
