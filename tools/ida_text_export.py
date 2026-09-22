"""以 IDA Pro 9.4 匯出執行期段傾印的 16 位元 entrypoint bytes。

本工具僅供一次性、隔離的 IDAPython 容器使用。輸入是 dosgolem 的 runtime
segment dump，而非原始 EXE 或 overlay 的檔案位址；每筆結果保留 runtime
segment:offset 映射，避免把不同位址空間混為一談。
"""

import hashlib
import json
import os
import traceback

import ida_funcs
import ida_loader
import idautils
import ida_auto
import ida_bytes
import ida_ida
import ida_idp
import ida_nalt
import ida_pro
import ida_segment
import ida_ua
import idaapi
import idc


OUTPUT = os.environ["IDA_EXPORT"]
RUNTIME_SEGMENT = int(os.environ["IDA_RUNTIME_SEGMENT"], 16)
RUNTIME_OFFSET = int(os.environ["IDA_RUNTIME_OFFSET"], 16)
ENTRY_OFFSETS = [int(value, 16) for value in os.environ["IDA_ENTRY_OFFSETS"].split(",")]
WINDOW_BYTES = int(os.environ.get("IDA_WINDOW_BYTES", "128"), 10)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runtime_address(ea):
    return f"{RUNTIME_SEGMENT:04X}:{RUNTIME_OFFSET + ea:04X}"


def decode_window(entry_offset, limit):
    input_sha = sha256_file(ida_nalt.get_input_file_path())
    start = entry_offset - RUNTIME_OFFSET
    end = min(limit, start + WINDOW_BYTES)
    if start < 0 or start >= limit:
        raise ValueError(f"entrypoint {entry_offset:04X} 不在傾印範圍內")
    result = []
    ea = start
    while ea < end:
        instruction = ida_ua.insn_t()
        size = ida_ua.decode_insn(instruction, ea)
        if size <= 0 or ea + size > limit:
            result.append(
                {
                    "runtime_address": runtime_address(ea),
                    "raw_bytes": ida_bytes.get_bytes(ea, 1).hex(),
                    "decoded": None,
                    "size": 1,
                    "inference": "未知：未成功解碼",
                    "evidence": {"input_sha256": input_sha, "ida_raw_ea": ea},
                }
            )
            ea += 1
            continue
        ida_ua.create_insn(ea)
        result.append(
            {
                "runtime_address": runtime_address(ea),
                "raw_bytes": ida_bytes.get_bytes(ea, size).hex(),
                "decoded": idc.generate_disasm_line(ea, 0),
                "size": size,
                "inference": "已證實：原始位元組與 IDA 解碼；遊戲語意未知",
                "evidence": {"input_sha256": input_sha, "ida_raw_ea": ea},
            }
        )
        ea += size
    return result


def main():
    ida_auto.auto_wait()
    ida_idp.set_processor_type("metapc", ida_idp.SETPROC_LOADER)
    ida_ida.inf_set_app_bitness(16)
    segment = ida_segment.get_first_seg()
    if segment is not None:
        ida_segment.set_segm_addressing(segment, 0)
    ida_auto.auto_wait()

    input_path = ida_nalt.get_input_file_path()
    size = os.path.getsize(input_path)
    payload = {
        "schema": "ida-runtime-entrypoint-v1",
        "tool": "IDA Pro " + idaapi.get_kernel_version(),
        "address_space": "IDA raw-binary EA; every instruction includes runtime segment:offset",
        "input": {
            "path_basename": os.path.basename(input_path),
            "sha256": sha256_file(input_path),
            "size": size,
        },
        "runtime_mapping": {
            "segment": f"{RUNTIME_SEGMENT:04X}",
            "offset_range": f"{RUNTIME_OFFSET:04X}-{RUNTIME_OFFSET + size - 1:04X}",
            "entrypoints": [f"{RUNTIME_SEGMENT:04X}:{offset:04X}" for offset in ENTRY_OFFSETS],
        },
        "analysis": {
            "processor": "metapc",
            "bitness": 16,
            "confidence": "選定 runtime 位址與原始位元組；分析視窗不等於已證實函式入口，解碼不單獨主張語意",
        },
        "entrypoint_windows": [
            {
                "entrypoint": f"{RUNTIME_SEGMENT:04X}:{offset:04X}",
                "instructions": decode_window(offset, size),
            }
            for offset in ENTRY_OFFSETS
        ],
    }
    relations = []
    for entry in ENTRY_OFFSETS:
        ea = entry - RUNTIME_OFFSET
        ida_funcs.add_func(ea)
        function = ida_funcs.get_func(ea)
        relations.append({
            "runtime_entry": runtime_address(ea),
            "original_name": idc.get_func_name(ea),
            "function_start": runtime_address(function.start_ea) if function else None,
            "function_end_exclusive": runtime_address(function.end_ea) if function else None,
            "inference": "未知：IDA 函式邊界僅供導覽；語意需由動態收據支持",
            "evidence": {"input_sha256": payload["input"]["sha256"], "ida_raw_ea": ea},
            "incoming_xrefs": [{"runtime_from": runtime_address(x.frm), "type": x.type}
                               for x in idautils.XrefsTo(ea)],
        })
    payload["database_relations"] = relations
    ida_loader.save_database(os.environ["IDA_DATABASE"], 0)
    with open(OUTPUT, "w", encoding="utf-8") as target:
        json.dump(payload, target, ensure_ascii=False, indent=2)
        target.write("\n")


try:
    main()
except Exception as error:
    with open(OUTPUT, "w", encoding="utf-8") as target:
        json.dump(
            {
                "schema": "ida-runtime-entrypoint-error-v1",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            },
            target,
            ensure_ascii=False,
            indent=2,
        )
        target.write("\n")
    ida_pro.qexit(1)
else:
    ida_pro.qexit(0)
