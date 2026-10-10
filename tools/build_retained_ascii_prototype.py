#!/usr/bin/env python3
"""規格052：核對正式來源後，在workplace加入私有英數觀測。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PINS = {
    "tools/live_menu.go": "a1133c636f8ab46c89c6edb4a467b3ba561bd874d070e4adb1ffce77d6f3797e",
    "tools/window_prototype.go": "cd287840cfd35cdac4846eb93b5c0dff78860e58a0ecd05d1cd1be119d338fd2",
    "tools/string_overlay.go": "543afd88d0cdebb3723dd08e39745c883208bfa6af121f0ccffa24955b5ae59e",
    "tools/dialog_overlay.go": "2522405d5306d7170e151f5152f6b81bfb2ec6a60069a4cb4cea9ac0b4d9a3d0",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"替換點不唯一：{old[:100]!r}")
    return source.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not Path("/.dockerenv").is_file():
        raise SystemExit("請在Docker內執行")
    output = args.output.resolve()
    if (not output.is_relative_to((ROOT / "workplace").resolve()) or output.exists() or
            not output.parent.is_dir() or output.parent.stat().st_uid != os.getuid()):
        raise SystemExit("需新的workplace目錄且父目錄擁有者相符")
    for name, expected in PINS.items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise SystemExit(f"來源版本不符：{name}")
    subprocess.run([sys.executable, str(ROOT / "tools/build_window_prototype.py"), "--repo", str(ROOT),
                    "--reference", str(args.reference), "--output", str(output)], check=True, timeout=30)
    source = (output / "adapter.go").read_text()
    source = replace_once(source, "\tflag.Parse()\n", "\tflag.Parse()\n\tdefer saveRetainedASCIIObservations(*out)\n")
    source = replace_once(source, "\t\t\t\tdone := str.onRead(a, m.Mem[a], m.Steps)\n",
                          "\t\t\t\tobserveRetainedASCIIRead(a, m.Mem[a], m.Steps, c.R, c.Seg)\n"
                          "\t\t\t\tdone := str.onRead(a, m.Mem[a], m.Steps)\n")
    marker = '\t\tif it == nil {\n\t\t\tif why != "" {\n\t\t\t\tstr.misses[why+"\\t"+text]++'
    source = replace_once(source, marker,
                          "\t\tobserveRetainedASCII(str, r, m.Steps, it, baselineWhy, why)\n" + marker)
    source = replace_once(source, "\t\t\t\tit.appliedFrame++\n\t\t\t\tshown++\n",
                          "\t\t\t\tif it.id == \"STRING:retained-ascii\" && label != \"\" {\n"
                          "\t\t\t\t\tlineRecords = append(lineRecords, map[string]any{\"candidate_id\": it.id, \"applied\": true, \"shown\": it.text, \"safe\": it.safe, \"complete_step\": it.complete, \"font_px\": it.size})\n"
                          "\t\t\t\t}\n"
                          "\t\t\t\tit.appliedFrame++\n\t\t\t\tshown++\n")
    (output / "adapter.go").write_text(source)
    (output / "retained_ascii_observer.go").write_bytes((ROOT / "tools/retained_ascii_prototype.go").read_bytes())
    subprocess.run(["gofmt", "-w", *map(str, sorted(output.glob("*.go")))], check=True, timeout=30)
    sources = {name: sha((ROOT / name).read_bytes()) for name in PINS}
    for name in ["tools/build_window_prototype.py", "tools/retained_ascii_prototype.go",
                 "tools/retained_ascii_overlay.go", "tools/retained_ascii_overlay_test.go", "tools/build_retained_ascii_prototype.py"]:
        sources[name] = sha((ROOT / name).read_bytes())
    result = {"kind": "draft-retained-ascii-prototype-not-release", "source_sha256": sources,
              "assembled_sha256": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
              "limitations": ["Existing Chinese font only; other gameplay locales and HD graphics are incomplete.",
                              "Candidate activation requires --retained-ascii-a; source observations are always private."]}
    (output / "prototype-sources.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("ASSEMBLED_DRAFT_RETAINED_ASCII_PROTOTYPE", output)


if __name__ == "__main__":
    main()
