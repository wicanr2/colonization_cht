#!/usr/bin/env python3
"""目標162（Issue #15）：組裝 Linux 技術預覽可散布包到 dist-all/<版本>/patch/，只在容器內執行。

包內只放本作品與第三方允許散布的元件：前端執行檔、啟動器、執行期譯稿 TSV、由 Cubic 11 烘製的字模、
授權檔與清單；不放任何原版檔案、截圖、存檔或解包資料。字模複本的 scope 聲明改寫成隨包散布的授權說明，
其餘內容不動。封裝可重現：固定時間戳、擁有者與檔案順序，gzip 不寫時間。
"""

import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

VERSION = re.compile(r"^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$")
TEXT = ["draft.zh-Hant.tsv", "nation-card-fragments.zh-Hant.tsv", "nation-introduction.zh-Hant.tsv",
        "build-caption-values.zh-Hant.tsv", "help-bilingual.tsv", "sea-status.zh-Hant.tsv", "static-overlay.zh-Hant.tsv"]
# 包內路徑 → workplace/reports 下的來源（目錄只收 *.json）
MASKS = {"menu": "goal096-fonts-verified", "card": ["goal099-card-fonts/NAMES.TXT-0x000008EA.json",
                                                     "goal099-card-fonts/LABELS.TXT-0x000008F2.json"],
         "cards-rest": "goal140-nation-cards/fonts", "third-card": "goal139-third-card/fonts",
         "intro": "goal136-nation-intro/masks", "build1.json": "goal133-options-rows/build1-font.json",
         "captions": "goal141-captions/fonts", "help": "goal142-help/fonts",
         "sea-atlas.json": "goal150-dynamic/atlas/sea-atlas.json", "options-title.json": "goal133-options-rows/title-font.json",
         "option-rows": "goal134-options-rows/row-fonts", "retire": "goal138-retire/fonts", "static": "goal151-static/masks"}
SCOPE = "依俐方體11號（Cubic 11）授權隨發行包散布；見 LICENSES/Cubic-11-OFL.txt"
ORIGINAL = {"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
            "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
            "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
            "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
            "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mask_bytes(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    if "scope" in d:
        d["scope"] = SCOPE
    d.pop("local_only", None)
    return (json.dumps(d, ensure_ascii=False) + "\n").encode("utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True)
    p.add_argument("--repo", type=Path, default=Path("/repo"))
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--readme", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True, help="dist-all 根目錄")
    a = p.parse_args()
    if not VERSION.match(a.version):
        raise SystemExit("版號不符 v.X.Y.Z-YYYYMMDD")
    reports = a.repo / "workplace/reports"
    top = f"colonization-cht-{a.version}-linux-x86_64"
    files = {}  # 包內路徑 → (bytes, mode)
    files["bin/colonization-window"] = (a.binary.read_bytes(), 0o755)
    files["colonization-cht.sh"] = ((a.repo / "tools/release/colonization-cht.sh").read_bytes(), 0o755)
    files["LICENSE"] = ((a.repo / "LICENSE").read_bytes(), 0o644)
    files["LICENSES/Cubic-11-OFL.txt"] = ((a.repo / "font/Cubic-11-OFL.txt").read_bytes(), 0o644)
    files["README.txt"] = (a.readme.read_text(encoding="utf-8").replace("{VERSION}", a.version).encode("utf-8"), 0o644)
    for name in TEXT:
        files[f"text/{name}"] = ((a.repo / "text" / name).read_bytes(), 0o644)
    for dest, src in MASKS.items():
        srcs = src if isinstance(src, list) else [src]
        for s in srcs:
            path = reports / s
            if path.is_dir():
                for f in sorted(path.glob("*.json")):
                    files[f"masks/{dest}/{f.name}"] = (mask_bytes(f), 0o644)
            elif dest.endswith(".json"):
                files[f"masks/{dest}"] = (mask_bytes(path), 0o644)
            else:
                files[f"masks/{dest}/{path.name}"] = (mask_bytes(path), 0o644)
    for bad in files:
        if re.search(r"\.(png|idx|pal|memory|sav|exe|ss|pik|ttf)$", bad, re.I) and not bad.endswith("colonization-window"):
            raise SystemExit("包內不得有原版或畫面檔：" + bad)
    manifest = {"version": a.version, "platform": "linux-x86_64", "license": "LicenseRef-RRSAL-1.0（第三方元件依各自授權）",
                "requires_original": {"note": "需自備合法取得的 DOS 版原版 COLONIZE 目錄；以下檔案 SHA-256 不符時前端拒絕啟動",
                                      "files": ORIGINAL},
                "files": {k: {"sha256": sha(v[0]), "bytes": len(v[0])} for k, v in sorted(files.items())}}
    files["MANIFEST.json"] = ((json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode(), 0o644)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        dirs = sorted({str(Path(top, k).parent) for k in files} | {top})
        for d in sorted({str(p) for d in dirs for p in [Path(d), *Path(d).parents] if str(p) not in ("", ".")}):
            info = tarfile.TarInfo(d)
            info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, 0
            tar.addfile(info)
        for k in sorted(files):
            data, mode = files[k]
            info = tarfile.TarInfo(f"{top}/{k}")
            info.size, info.mode, info.mtime = len(data), mode, 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    gz = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gz, mtime=0) as g:
        g.write(buf.getvalue())
    out = a.output / a.version / "patch"
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / f"{top}.tar.gz"
    pkg.write_bytes(gz.getvalue())
    sums = {"version": a.version, "packages": {f"patch/{pkg.name}": {"sha256": sha(pkg.read_bytes()), "bytes": pkg.stat().st_size}}}
    (a.output / a.version / "SHA256SUMS.json").write_text(json.dumps(sums, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"package": str(pkg), **sums["packages"][f"patch/{pkg.name}"], "files": len(files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
