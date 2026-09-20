#!/usr/bin/env python3
"""輸出 Windows NE 執行檔的載入、區段、匯入與資源中繼資料。

工具刻意不擷取區段內容、原文文字或圖像；輸出只供固定雜湊版本的
載入面研究。它不是 NE loader，也不推論任何 API 是否在玩家流程中執行。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class NEFormatError(ValueError):
    """輸入不符合本工具可安全盤點的 NE 結構。"""


def _span(data: bytes, offset: int, size: int, label: str) -> memoryview:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise NEFormatError(
            f"{label} 超出檔案範圍：offset=0x{offset:X} size=0x{size:X} "
            f"file_size=0x{len(data):X}"
        )
    return memoryview(data)[offset : offset + size]


def _u8(data: bytes, offset: int, label: str) -> int:
    return _span(data, offset, 1, label)[0]


def _u16(data: bytes, offset: int, label: str) -> int:
    return int.from_bytes(_span(data, offset, 2, label), "little")


def _u32(data: bytes, offset: int, label: str) -> int:
    return int.from_bytes(_span(data, offset, 4, label), "little")


def _pascal_ascii(data: bytes, offset: int, label: str) -> str:
    length = _u8(data, offset, f"{label}.length")
    raw = _span(data, offset + 1, length, f"{label}.bytes").tobytes()
    return raw.decode("ascii", errors="backslashreplace")


def _ordinal_or_offset(value: int) -> dict[str, int | str]:
    if value & 0x8000:
        return {"kind": "ordinal", "value": value & 0x7FFF}
    return {"kind": "string_offset", "value": value}


def _segment_file_length(length: int) -> int:
    # NE stores a 64 KiB segment length as zero.
    return 0x10000 if length == 0 else length


def inventory(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if _span(data, 0, 2, "MZ signature").tobytes() != b"MZ":
        raise NEFormatError("檔案不是 MZ 可執行檔")

    ne = _u32(data, 0x3C, "MZ.e_lfanew")
    if _span(data, ne, 2, "NE signature").tobytes() != b"NE":
        raise NEFormatError(f"MZ.e_lfanew=0x{ne:X} 未指向 NE signature")

    def rel16(relative: int, label: str) -> int:
        return ne + _u16(data, ne + relative, f"NE.{label}")

    entry_table = rel16(0x04, "entry_table_offset")
    entry_table_size = _u16(data, ne + 0x06, "entry_table_size")
    segment_table = rel16(0x22, "segment_table_offset")
    resource_table = rel16(0x24, "resource_table_offset")
    resident_names = rel16(0x26, "resident_name_table_offset")
    module_reference_table = rel16(0x28, "module_reference_table_offset")
    imported_name_table = rel16(0x2A, "imported_name_table_offset")
    nonresident_names = _u32(data, ne + 0x2C, "NE.nonresident_name_table_offset")
    segment_count = _u16(data, ne + 0x1C, "NE.segment_count")
    module_count = _u16(data, ne + 0x1E, "NE.module_reference_count")
    alignment_shift = _u16(data, ne + 0x32, "NE.logical_sector_alignment_shift")
    if alignment_shift > 31:
        raise NEFormatError(f"NE.logical_sector_alignment_shift 不合理：{alignment_shift}")

    _span(data, entry_table, entry_table_size, "NE entry table")
    _span(data, segment_table, segment_count * 8, "NE segment table")
    _span(data, module_reference_table, module_count * 2, "NE module reference table")
    # These table starts must at least be representable even when the tables are empty.
    _span(data, resource_table, 2, "NE resource table alignment")
    _span(data, resident_names, 1, "NE resident name table")
    _span(data, imported_name_table, 1, "NE imported name table")
    if nonresident_names:
        _span(data, nonresident_names, 1, "NE nonresident name table")

    segments: list[dict[str, int | bool]] = []
    for index in range(segment_count):
        row = segment_table + index * 8
        sector_offset = _u16(data, row, f"segment[{index + 1}].sector_offset")
        declared_length = _u16(data, row + 2, f"segment[{index + 1}].length")
        flags = _u16(data, row + 4, f"segment[{index + 1}].flags")
        minimum_allocation = _u16(data, row + 6, f"segment[{index + 1}].minimum_allocation")
        file_offset = sector_offset << alignment_shift
        file_length = _segment_file_length(declared_length)
        _span(data, file_offset, file_length, f"segment[{index + 1}]")
        segments.append(
            {
                "index": index + 1,
                "file_offset": file_offset,
                "declared_length": declared_length,
                "file_length": file_length,
                "flags": flags,
                "minimum_allocation": minimum_allocation,
                "has_relocations": bool(flags & 0x0100),
            }
        )

    modules: list[str] = []
    for index in range(module_count):
        offset = _u16(data, module_reference_table + index * 2, f"module[{index + 1}].name_offset")
        modules.append(_pascal_ascii(data, imported_name_table + offset, f"module[{index + 1}].name"))

    resources: list[dict[str, Any]] = []
    resource_shift = _u16(data, resource_table, "resource.alignment_shift")
    if resource_shift > 31:
        raise NEFormatError(f"resource.alignment_shift 不合理：{resource_shift}")
    cursor = resource_table + 2
    while True:
        type_raw = _u16(data, cursor, "resource.type")
        if type_raw == 0:
            cursor += 2
            break
        count = _u16(data, cursor + 2, "resource.count")
        _span(data, cursor, 8 + count * 12, "resource.type_info")
        entries: list[dict[str, Any]] = []
        entry_start = cursor + 8
        for entry_index in range(count):
            row = entry_start + entry_index * 12
            offset_units = _u16(data, row, "resource.offset")
            length_units = _u16(data, row + 2, "resource.length")
            file_offset = offset_units << resource_shift
            file_length = length_units << resource_shift
            if file_length:
                _span(data, file_offset, file_length, "resource.data")
            entries.append(
                {
                    "id": _ordinal_or_offset(_u16(data, row + 6, "resource.id")),
                    "file_offset": file_offset,
                    "file_length": file_length,
                    "flags": _u16(data, row + 4, "resource.flags"),
                }
            )
        resources.append({"type": _ordinal_or_offset(type_raw), "entries": entries})
        cursor = entry_start + count * 12

    relocations: list[dict[str, Any]] = []
    for segment in segments:
        if not segment["has_relocations"]:
            continue
        relocation_table = int(segment["file_offset"]) + int(segment["file_length"])
        count = _u16(data, relocation_table, f"segment[{segment['index']}].relocation_count")
        _span(data, relocation_table + 2, count * 8, f"segment[{segment['index']}].relocation_records")
        for record_index in range(count):
            row = relocation_table + 2 + record_index * 8
            source_type = _u8(data, row, "relocation.source_type")
            flags = _u8(data, row + 1, "relocation.flags")
            target_type = flags & 0x03
            target_module = _u16(data, row + 4, "relocation.target_module")
            target_value = _u16(data, row + 6, "relocation.target_value")
            record: dict[str, Any] = {
                "segment": segment["index"],
                "source_type": source_type,
                "source_offset": _u16(data, row + 2, "relocation.source_offset"),
                "target_type": target_type,
            }
            if target_type in (1, 2):
                record["module_index"] = target_module
                record["module"] = (
                    modules[target_module - 1]
                    if 1 <= target_module <= len(modules)
                    else f"<invalid module index {target_module}>"
                )
                if target_type == 1:
                    record["target"] = {"kind": "ordinal", "value": target_value}
                else:
                    record["target"] = {
                        "kind": "name",
                        "value": _pascal_ascii(
                            data,
                            imported_name_table + target_value,
                            "relocation.import_name",
                        ),
                    }
            else:
                record["target"] = {"kind": "raw", "value": target_value}
            relocations.append(record)

    named_imports: dict[str, set[str]] = {module: set() for module in modules}
    ordinal_imports: dict[str, set[int]] = {module: set() for module in modules}
    for relocation in relocations:
        if relocation["target_type"] not in (1, 2):
            continue
        module = str(relocation["module"])
        target = relocation["target"]
        if target["kind"] == "name":
            named_imports.setdefault(module, set()).add(str(target["value"]))
        elif target["kind"] == "ordinal":
            ordinal_imports.setdefault(module, set()).add(int(target["value"]))

    return {
        "tool": "tools/ne_inventory.py",
        "input": {
            "name": path.name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "address_space": {
            "file_offsets": "all offsets are absolute file offsets unless stated otherwise",
            "ne_relative_offsets": "NE header table offsets are parsed relative to NE header",
        },
        "mz": {"new_executable_header_file_offset": ne},
        "ne": {
            "linker_version": _u8(data, ne + 2, "NE.linker_version"),
            "linker_revision": _u8(data, ne + 3, "NE.linker_revision"),
            "flags": _u16(data, ne + 0x0C, "NE.flags"),
            "target_os": _u8(data, ne + 0x36, "NE.target_os"),
            "initial_cs": _u16(data, ne + 0x16, "NE.initial_cs"),
            "initial_ip": _u16(data, ne + 0x14, "NE.initial_ip"),
            "segment_count": segment_count,
            "module_reference_count": module_count,
            "logical_sector_alignment_shift": alignment_shift,
            "tables": {
                "entry": {"file_offset": entry_table, "size": entry_table_size},
                "segment": {"file_offset": segment_table, "size": segment_count * 8},
                "resource": {"file_offset": resource_table},
                "resident_names": {"file_offset": resident_names},
                "module_references": {"file_offset": module_reference_table, "size": module_count * 2},
                "imported_names": {"file_offset": imported_name_table},
                "nonresident_names": {"file_offset": nonresident_names},
            },
        },
        "segments": segments,
        "modules": modules,
        "resources": resources,
        "relocations": {
            "total_records": len(relocations),
            "named_imports": {module: sorted(names) for module, names in named_imports.items() if names},
            "ordinal_imports": {module: sorted(values) for module, values in ordinal_imports.items() if values},
            "records": relocations,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path, help="唯讀 NE 輸入檔")
    parser.add_argument("--output", required=True, type=Path, help="JSON 報告輸出位置")
    args = parser.parse_args()

    report = inventory(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"已盤點 {report['input']['name']}：{report['ne']['segment_count']} 個區段、"
        f"{report['ne']['module_reference_count']} 個模組、"
        f"{report['relocations']['total_records']} 筆 relocation"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
