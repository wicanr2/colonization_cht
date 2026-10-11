#!/usr/bin/env python3
"""規格060 DRAFT：在隔離工作目錄連結固定欄位匯出器，不修改正式來源。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PINS = {
    "tools/live_menu.go": "2f5ab4b81a9608a14f05280cfaba5027472e648fda6e34d3db4ba8855d0a0a53",
    "tools/build_window_prototype.py": "5e655dd9e0ea92869376205e92f7c4edbd7c24b26bf6b464b75c9de25776f04c",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not Path("/.dockerenv").is_file() or not output.is_relative_to((ROOT / "workplace").resolve()):
        raise ValueError("需Docker及workplace隔離目錄")
    if output.exists() or not output.parent.is_dir() or output.parent.stat().st_uid != os.getuid():
        raise ValueError("需新的輸出目錄，父目錄擁有者須相同")
    for name, digest in PINS.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("正式來源不同：" + name)
    subprocess.run([sys.executable, str(ROOT / "tools/build_window_prototype.py"), "--repo", str(ROOT),
                    "--reference", str(args.reference), "--output", str(output), "--legacy-source"], check=True, timeout=30)
    source = (output / "adapter.go").read_text()
    marker = "\tseaOn := sea != nil && sea.glyphs != nil\n"
    if source.count(marker) != 1:
        raise ValueError("匯出接點不唯一")
    code = "\tif *resourceExportPath != \"\" {\n\t\texportDisplayResources(*resourceExportPath, lines, difficulty, captions, title, rows, retire, intro, help, statics)\n\t\treturn\n\t}\n"
    (output / "adapter.go").write_text(source.replace(marker, code + marker, 1))
    (output / "resource_probe.go").write_bytes((ROOT / "tools/language_resource_probe.go").read_bytes())
    subprocess.run(["gofmt", "-w", str(output / "adapter.go"), str(output / "resource_probe.go")], check=True, timeout=30)
    sources = {name: sha((ROOT / name).read_bytes()) for name in [*PINS, "tools/language_resource_probe.go", "tools/build_language_resource_probe.py"]}
    (output / "probe-sources.json").write_text(json.dumps({"kind": "DRAFT-fixed-resource-export-probe", "source_sha256": sources}, indent=2) + "\n")
    print("ASSEMBLED_DRAFT_FIXED_RESOURCE_PROBE", output)


if __name__ == "__main__":
    main()
