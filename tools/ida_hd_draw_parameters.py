"""以新建 IDA 資料庫核對首座建築參數；只輸出研究證據。"""
import hashlib
import json
import os
from pathlib import Path

import ida_auto
import ida_bytes
import ida_funcs
import ida_nalt
import ida_segment
import ida_ua
import idaapi
import idautils
import idc


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instruction(ea):
    insn = ida_ua.insn_t()
    size = ida_ua.decode_insn(insn, ea)
    assert size > 0
    return {"ida_ea": ea, "bytes": ida_bytes.get_bytes(ea, size).hex(),
            "disassembly": idc.generate_disasm_line(ea, 0),
            "operands": [{"text": idc.print_operand(ea, n),
                          "type": int(op.type), "register": int(op.reg),
                          "address": int(op.addr), "value": int(op.value),
                          "phrase": int(op.phrase)}
                         for n, op in enumerate(insn.ops) if op.type != ida_ua.o_void]}


def matches(pattern):
    found = []
    for start in idautils.Segments():
        seg = ida_segment.getseg(start)
        data = ida_bytes.get_bytes(seg.start_ea, seg.end_ea - seg.start_ea) or b""
        at = data.find(pattern)
        while at >= 0:
            ea = seg.start_ea + at
            fun = ida_funcs.get_func(ea)
            row = {"ida_ea": ea, "segment_name": ida_segment.get_segm_name(seg),
                   "segment_base": ida_segment.get_segm_base(seg),
                   "segment_bitness": seg.bitness, "function": None}
            if fun is not None:
                heads = [h for h in idautils.Heads(fun.start_ea, fun.end_ea)
                         if ida_bytes.is_code(ida_bytes.get_full_flags(h))]
                row["function"] = {
                    "name": ida_funcs.get_func_name(fun.start_ea),
                    "start_ea": fun.start_ea, "end_ea": fun.end_ea,
                    "instructions": [instruction(h) for h in heads[:512]],
                    "instructions_truncated": len(heads) > 512,
                    "direct_callers": [instruction(h) for h in
                                       sorted(idautils.CodeRefsTo(fun.start_ea, False))[:64]],
                    "inference": "navigation-only IDA autoanalysis"}
            found.append(row)
            assert len(found) <= 64, "ambiguous pattern; narrow the research query"
            at = data.find(pattern, at + 1)
    return found


ida_auto.auto_wait()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
original = Path(ida_nalt.get_input_file_path())
boundary_path = Path(os.environ["COLONIZATION_HD_PARAMETERS"])
output = Path(os.environ["COLONIZATION_HD_IDA_OUTPUT"])
assert output.is_relative_to(Path("/out")) and not output.exists()
assert sha(original) == "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3"
assert sha(boundary_path) == "128cc274ae60f20042d16bb1b609395b5fce7ee6979400236eb9eb03d64ccf77"
boundary = json.loads(boundary_path.read_bytes())
assert boundary["entry_cs_ip"] == "0D46:000A"
assert boundary["return_cs_ip"] == "121D:1554"
assert boundary["source_encoded_sha256"] == "7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a"
patterns = {"writer": bytes.fromhex("268807035ef042ebb5905a5b035efe79"),
            "caller_after_return": bytes.fromhex(
                boundary["parameter_reads"]["caller_after_return_16_hex"])}
result = {
    "result": "IDA_SINGLE_BUILDING_PARAMETER_QUERY",
    "kernel_version": idaapi.get_kernel_version(),
    "original_exe": original.name, "original_exe_sha256": sha(original),
    "boundary_sha256": sha(boundary_path), "script_sha256": sha(Path(__file__)),
    "patterns": {name: {"bytes": pattern.hex(), "matches": matches(pattern)}
                 for name, pattern in patterns.items()},
    "address_spaces": {
        "runtime": "dosgolem real-mode CS:IP and 20-bit linear RAM",
        "ida": "fresh MZ loader linear ea; reported segment bases are IDA-only"},
    "limitations": [
        "No names, operands or bytes are changed; IDA generated names are navigation only.",
        "Raw operand numbers need instruction and runtime data-flow review.",
        "Caller bytes can differ after relocation or dynamic loading; a missing match is not evidence of absence.",
        "One native call does not prove general frame indexing, flips, clipping or HD lifecycle."]}
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
idaapi.qexit(0)
