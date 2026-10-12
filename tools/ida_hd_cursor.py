"""從唯讀原版新建IDA資料庫，核對游標合成分支；不修改名稱與原始定位。"""
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
            "operands": [{"text": idc.print_operand(ea, n), "type": int(op.type),
                          "register": int(op.reg), "address": int(op.addr),
                          "value": int(op.value), "phrase": int(op.phrase)}
                         for n, op in enumerate(insn.ops) if op.type != ida_ua.o_void]}


ida_auto.auto_wait()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
original = Path(ida_nalt.get_input_file_path())
assert sha(original) == "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3"
output = Path(os.environ["COLONIZATION_HD_IDA_OUTPUT"])
assert output.is_relative_to(Path("/out")) and not output.exists()
pattern = bytes.fromhex("26880547e2f007c3c800000006c44606")
matches = []
for start in idautils.Segments():
    seg = ida_segment.getseg(start)
    data = ida_bytes.get_bytes(seg.start_ea, seg.end_ea - seg.start_ea) or b""
    at = data.find(pattern)
    while at >= 0:
        ea = seg.start_ea + at
        fun = ida_funcs.get_func(ea)
        assert fun is not None
        heads = [h for h in idautils.Heads(fun.start_ea, fun.end_ea)
                 if ida_bytes.is_code(ida_bytes.get_full_flags(h))]
        assert len(heads) <= 128
        matches.append({"ida_ea": ea, "segment_base": ida_segment.get_segm_base(seg),
                        "segment_name": ida_segment.get_segm_name(seg),
                        "function": {"name": ida_funcs.get_func_name(fun.start_ea),
                                     "start_ea": fun.start_ea, "end_ea": fun.end_ea,
                                     "instructions": [instruction(h) for h in heads],
                                     "inference": "navigation-only IDA autoanalysis"}})
        assert len(matches) <= 64
        at = data.find(pattern, at + 1)
result = {
    "result": "IDA_CURSOR_BUFFER_QUERY", "kernel_version": idaapi.get_kernel_version(),
    "original_sha256": sha(original), "script_sha256": sha(Path(__file__)),
    "runtime_site": "0B68:0547",
    "patterns": {"cursor_writer": {"bytes": pattern.hex(), "matches": matches}},
    "address_spaces": {"runtime": "dosgolem real-mode CS:IP", "ida": "fresh MZ linear EA"},
    "inference": "instructions and original names only; semantic review is separate",
}
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
idaapi.qexit(0)
