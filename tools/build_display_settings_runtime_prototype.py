#!/usr/bin/env python3
"""規格056：沿用舊入口，在新workplace目錄組裝正式設定列驗收版。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE_HASHES = {'tools/live_menu.go': '2f5ab4b81a9608a14f05280cfaba5027472e648fda6e34d3db4ba8855d0a0a53', 'tools/window_prototype.go': '088d2a3f933e99df2ecdc5d348972fc52fb64d3a9794a2c1ecd2ebe8f1f89140', 'tools/build_window_prototype.py': '4e16cca620b654915d59c044796ace6ce408d66f66623161ff53096c6fbd3a85', 'tools/display_ui.go': '946de52ef784c3a2df9b0fb4b3478bec37f885fdd16192fd7bb58bfc9e36d811', 'tools/display_ui_test.go': '730a174c8cc129dbe4a2e0a6cbaac8ab31532203fdddd563bc1af47ced42bfd3', 'tools/display_preferences.go': '29f6684666f89abc3741a518800b152944d039a6b3ebc016036cb085d4466848', 'tools/display_preferences_test.go': 'b9d51da367507ab21fc8f4487f2d86142515032d4174b64cfd36bc98d3287298'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


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
        raise SystemExit("輸出須為新的workplace目錄，父目錄擁有者須相同")
    for name, expected in SOURCE_HASHES.items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise SystemExit(f"正式來源版本不符：{name}")
    subprocess.run([sys.executable, str(ROOT / "tools/build_window_prototype.py"), "--repo", str(ROOT),
                    "--output", str(output), "--reference", str(args.reference)], check=True, timeout=30)
    sources = {name: sha((ROOT / name).read_bytes()) for name in SOURCE_HASHES}
    sources["tools/" + Path(__file__).name] = sha(Path(__file__).read_bytes())
    sources["text/frontend-ui.tsv"] = sha((ROOT / "text/frontend-ui.tsv").read_bytes())
    result = {"kind": "formal-display-settings-verification-build-not-release", "source_sha256": sources,
              "assembled_sha256": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
              "limitations": ["Only existing zh-Hant and original English gameplay can activate.",
                              "Complete language packs and HD are not installed."]}
    (output / "prototype-sources.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("ASSEMBLED_FORMAL_DISPLAY_SETTINGS", output)


if __name__ == "__main__":
    main()
