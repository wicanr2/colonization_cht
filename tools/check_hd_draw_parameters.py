"""稽核首座建築參數、逐筆重畫及原版唯讀對照；不授權正式 HD。"""
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


def roi(data):
    return bytes(data[y * 320 + x] for y in range(13, 40) for x in range(56, 79))


def check(root, ida_path, game):
    original = {"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
                "BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4"}
    for name, expected in original.items():
        assert sha(game / name) == expected, "original fingerprint: " + name
    build = read(root / "build.json")
    assert sha(root / "hd-parameter-probe") == build["binary_sha256"]
    assert sha(root / "module/main.go") == build["source_sha256"]
    assert sha(Path(__file__).with_name("probe_hd_canvas_writes.go")) == build["source_sha256"]
    assert build["original_exe_sha256"] == original["VICEROY.EXE"]
    legacy = root / "legacy/draw-boundary.json"
    assert sha(legacy) == "f91890d9c4b9c72c6a252c3aed12c9e09ce1cfb89bac521c92149a7f39bc458a"
    parameters = root / "parameters/draw-boundary.json"
    assert sha(parameters) == "128cc274ae60f20042d16bb1b609395b5fce7ee6979400236eb9eb03d64ccf77"
    assert sha(ida_path) == "f891aeed6b49d0aab9448cb10bfc7b63ead2762360e62b31f8c99abcc4ab08eb"
    ida = read(ida_path)
    assert ida["kernel_version"] == "9.4"
    assert ida["boundary_sha256"] == sha(parameters)
    assert ida["original_exe_sha256"] == original["VICEROY.EXE"]
    assert ida["script_sha256"] == sha(Path(__file__).with_name("ida_hd_draw_parameters.py"))
    matches = ida["patterns"]["writer"]["matches"]
    assert len(matches) == 1 and matches[0]["ida_ea"] == 0x1C532
    fun = matches[0]["function"]
    assert not fun["instructions_truncated"]
    insns = {r["ida_ea"]: r for r in fun["instructions"]}
    # 原始指令與數值位移交叉核對，保留 IDA 名稱及 operands 原樣。
    expected_code = {
        0x1C36A: "c8280000", 0x1C36E: "52", 0x1C36F: "53", 0x1C370: "50",
        0x1C373: "8b4702", 0x1C37A: "8b07", 0x1C383: "8b46d2",
        0x1C390: "25ff7f", 0x1C396: "8b5ed2", 0x1C399: "8bc3",
        0x1C39B: "d1e3", 0x1C39D: "03d8", 0x1C39F: "c1e302",
        0x1C3A2: "035e08", 0x1C3A5: "8e460a", 0x1C3A8: "83c336",
        0x1C3B1: "268b07", 0x1C3B4: "268b5702", 0x1C3BE: "8b76d4",
        0x1C3C1: "8b4404", 0x1C3C4: "8b5406", 0x1C3CD: "8b4402",
        0x1C3D3: "268b4708", 0x1C3DA: "268b470a", 0x1C3E7: "8b46d6",
        0x1C433: "8b4606", 0x1C45E: "c45ee8", 0x1C480: "c576e4",
        0x1C53E: "035efe", 0x1C560: "ca0600"}
    for ea, code in expected_code.items():
        assert insns[ea]["bytes"] == code, hex(ea)
    for ea, offset in [(0x1C383, -46), (0x1C3A2, 8), (0x1C3A5, 10),
                       (0x1C3BE, -44), (0x1C3E7, -42), (0x1C433, 6)]:
        address = insns[ea]["operands"][1]["address"]
        signed = address - (1 << 64) if address >= 1 << 63 else address
        assert signed == offset, hex(ea)
    boundary = read(root / "stream/draw-boundary.json")
    assert all(boundary[k] == v for k, v in read(parameters).items())
    reads = boundary["parameter_reads"]
    ax, _, dx, bx, sp, _, _, _ = boundary["entry_registers"]
    args = reads["ss_sp_plus4_words"]
    assert (ax, dx, bx, sp, args) == (33, 56, 11688, 59358, [13, 42692, 20258])
    assert (ax & 0x7FFF) * 12 + args[1] + 0x36 == 0xA886
    assert reads["ds_bx_far"] == "1C6A:2DA8"
    assert reads["ds_bx_words"][:4] == [200, 320, 0, 0x2CAE]
    assert reads["record_far"] == "4F22:A886"
    assert reads["record_first_far"] == "5F3B:000E"
    assert reads["record_words"][4:] == [23, 27]
    assert reads["record_first_534_sha256"] == boundary["source_encoded_sha256"]
    assert boundary["return_sp"] - boundary["entry_sp"] == 10
    state_keys = ["steps", "input_sha256", "seed_sha256", "memory_sha256",
                  "indexed_sha256", "palette_sha256", "registers", "segments", "ip", "flags"]
    control = read(root / "control/writes.json")
    for name in ["stream", "parameters", "legacy"]:
        state = read(root / name / "writes.json")
        assert all(state[k] == control[k] for k in state_keys), name
    assert sha(root / "control/writes.json") == "6f6f7446956d170a33608f006c4c5de4eb489dfbf23fc63a00177b542eeb51e1"
    data = bytearray((root / "stream/after-draw.idx").read_bytes())
    final = (root / "stream/post-return-canvas.idx").read_bytes()
    assert len(data) == len(final) == 64000
    initial_roi = roi(data)
    original_background = hashlib.sha256(roi((root / "stream/before-draw.idx").read_bytes())).hexdigest()
    original_draw = hashlib.sha256(initial_roi).hexdigest()
    events = boundary["post_return_write_events"]
    assert boundary["post_return_event_columns"] == ["step", "cs", "ip", "linear_address", "old", "value"]
    assert 0 < len(events) <= 100000
    aggregates = {}
    same = 0
    for n, (step, cs, ip, addr, old, value) in enumerate(events):
        assert boundary["return_step"] <= step < boundary["observed_end_step"]
        assert not n or events[n - 1][0] <= step
        i = addr - 0x2CAE0
        assert 56 <= i % 320 < 79 and 13 <= i // 320 < 40
        assert data[i] == old and 0 <= value <= 255, "write stream discontinuity"
        data[i] = value
        same += old == value
        r = aggregates.setdefault(str(addr), {"count": 0, "first_step": step, "first_old_value": old})
        r.update(count=r["count"] + 1, last_step=step, last_cs_ip=f"{cs:04X}:{ip:04X}", last_value=value)
    assert aggregates == boundary["post_return_writes"]
    assert roi(data) == roi(final), "write stream does not reconstruct final native rectangle"
    native_writes = read(legacy)["writes"]
    calls = boundary["post_return_same_source_calls"] or []
    assert calls, "no later matching-source call was observed"
    redraws = []
    caller_code_changes = []
    for call in calls:
        start, end = call["entry_step"], call["return_step"]
        assert boundary["return_step"] < start < end < boundary["observed_end_step"]
        current = call["parameter_reads"]
        for key, value in reads.items():
            if key not in ["caller_before_return_16_hex", "caller_after_return_16_hex"]:
                assert current[key] == value, key
        changed = [key for key in ["caller_before_return_16_hex", "caller_after_return_16_hex"]
                   if current[key] != reads[key]]
        if changed:
            caller_code_changes.append({"entry_step": start, "changed_fields": changed})
        selected = [e for e in events if start <= e[0] < end]
        assert len(selected) == 440
        assert Counter(str(e[3]) for e in selected) == Counter({k: 1 for k in native_writes})
        assert all(e[5] == native_writes[str(e[3])][1] for e in selected)
        at_entry = bytearray((root / "stream/after-draw.idx").read_bytes())
        for e in events:
            if e[0] >= end:
                break
            if e[0] < start:
                at_entry[e[3] - 0x2CAE0] = e[5]
        assert hashlib.sha256(roi(at_entry)).hexdigest() == call["before_roi_sha256"]
        for e in selected:
            at_entry[e[3] - 0x2CAE0] = e[5]
        assert hashlib.sha256(roi(at_entry)).hexdigest() == call["after_roi_sha256"]
        assert call["before_roi_sha256"] == original_background
        assert call["after_roi_sha256"] == original_draw
        redraws.append({"entry_step": start, "return_step": end, "native_pixels": len(selected),
                        "before_equals_original_background": True, "after_equals_original_draw": True})
    return {
        "result": "PASS_SINGLE_BUILDING_PARAMETERS_AND_ORDERED_REDRAWS",
        "inference": "confirmed for the observed unclipped building calls only",
        "original_sha256": original, "probe_source_sha256": build["source_sha256"],
        "probe_binary_sha256": build["binary_sha256"], "ida_query_sha256": sha(ida_path),
        "stream_sha256": sha(root / "stream/draw-boundary.json"),
        "state_runs": 4, "original_state_equal_control": True,
        "legacy_and_parameters_byte_compatible": True,
        "native_rect": [56, 13, 79, 40], "post_return_write_events": len(events),
        "post_return_written_points": len(aggregates), "same_value_events": same,
        "write_sites": dict(Counter(f"{e[1]:04X}:{e[2]:04X}" for e in events)),
        "final_rectangle_equals_first_draw": roi(final) == initial_roi,
        "ordered_write_reconstruction": True, "redraws": redraws,
        "caller_pattern_matches": len(ida["patterns"]["caller_after_return"]["matches"]),
        "caller_code_changes": caller_code_changes,
        "limitations": ["General indexing, flips, clipping and other assets remain unverified.",
                        "The historical GUI RAM difference and unmatched caller code remain unknown.",
                        "Modal occlusion, scene exit/re-entry and a selected HD asset need normal GUI evidence.",
                        "No production behavior or READY HD contract is authorized by this research receipt."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--ida-query", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert Path("/.dockerenv").is_file() and os.getuid() != 0
    assert not args.output.exists() and args.output.parent.stat().st_uid == os.getuid()
    result = check(args.evidence_dir, args.ida_query, args.game_root)
    result["audit_source_sha256"] = sha(Path(__file__))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
