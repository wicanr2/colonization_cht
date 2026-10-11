"""目標186：由既有建築寫入收據定位IDA函式；輸出不授權正式HD覆蓋。"""
import hashlib
import json
import os
from pathlib import Path

import ida_auto
import ida_bytes
import ida_funcs
import ida_nalt
import ida_segment
import idaapi
import idautils
import idc


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instruction(ea):
    size = ida_bytes.get_item_size(ea)
    return {"ida_ea": ea, "bytes": (ida_bytes.get_bytes(ea, size) or b"").hex(),
            "disassembly": idc.generate_disasm_line(ea, 0),
            "operands": [idc.print_operand(ea, n) for n in range(3)]}


ida_auto.auto_wait()
original = Path(ida_nalt.get_input_file_path())
trace_path = Path(os.environ["COLONIZATION_HD_TRACE"])
proof_path = Path(os.environ["COLONIZATION_HD_PROOF"])
output = Path(os.environ["COLONIZATION_HD_IDA_OUTPUT"])
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert output.is_relative_to(Path("/out")) and not output.exists()
assert sha(original) == "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3"
proof = json.loads(proof_path.read_bytes())
assert proof["result"] == "PASS_COMPLETE_SOURCE_AND_READONLY_STATE"
assert proof["frame_ordinal"] == 32 and sha(trace_path) == proof["probe_receipt_sha256"]
trace = json.loads(trace_path.read_bytes())
sample = next(row for row in trace["write_samples"]
              if row["cs_ip"] == proof["writer_cs_ip"] and row["step"] == proof["step"])
pattern = bytes.fromhex(sample["code_hex"])
assert len(pattern) == 16
matches = []
for start in idautils.Segments():
    segment = ida_segment.getseg(start)
    data = ida_bytes.get_bytes(segment.start_ea, segment.end_ea - segment.start_ea) or b""
    at = data.find(pattern)
    while at >= 0:
        ea = segment.start_ea + at
        row = {"ida_ea": ea, "segment_name": ida_segment.get_segm_name(segment),
               "segment_start_ea": segment.start_ea, "segment_end_ea": segment.end_ea,
               "segment_base": ida_segment.get_segm_base(segment), "segment_bitness": segment.bitness,
               "function": None}
        function = ida_funcs.get_func(ea)
        if function is not None:
            heads = [head for head in idautils.Heads(function.start_ea, function.end_ea)
                     if ida_bytes.is_code(ida_bytes.get_full_flags(head))]
            refs = sorted(idautils.CodeRefsTo(function.start_ea, False))
            row["function"] = {"name": ida_funcs.get_func_name(function.start_ea),
                               "start_ea": function.start_ea, "end_ea": function.end_ea,
                               "instructions": [instruction(head) for head in heads[:256]],
                               "instructions_truncated": len(heads) > 256,
                               "direct_callers": [instruction(ref) for ref in refs[:64]],
                               "direct_callers_truncated": len(refs) > 64,
                               "inference": "navigation-only IDA autoanalysis boundary"}
        matches.append(row)
        at = data.find(pattern, at + 1)
result = {"result": "IDA_SINGLE_BUILDING_WRITER_QUERY", "kernel_version": idaapi.get_kernel_version(),
          "original_exe": original.name, "original_exe_sha256": sha(original),
          "trace_sha256": sha(trace_path), "source_proof_sha256": sha(proof_path),
          "script_sha256": sha(Path(__file__)), "runtime_sample": sample,
          "pattern_matches": matches,
          "address_spaces": {"runtime": "dosgolem real-mode CS:IP and 20-bit linear RAM",
                             "ida": "fresh DOS EXE loader database linear ea; segment bases are reported separately"},
          "limitations": ["Bytes identify candidates; IDA names and function boundaries are navigation, not confirmed semantics.",
                          "Direct xrefs omit indirect calls. Runtime entry, arguments, return and draw order remain to verify."]}
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
idaapi.qexit(0)
