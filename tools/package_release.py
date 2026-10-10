#!/usr/bin/env python3
"""組裝 Linux tar.gz／AppImage、Windows 或 macOS ZIP 到 dist-all/<版本>/patch/，只在容器內執行。

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
import subprocess
import tarfile
from pathlib import Path

VERSION = re.compile(r"^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$")
TEXT = ["draft.zh-Hant.tsv", "nation-card-fragments.zh-Hant.tsv", "nation-introduction.zh-Hant.tsv",
        "build-caption-values.zh-Hant.tsv", "help-bilingual.tsv", "sea-status.zh-Hant.tsv", "static-overlay.zh-Hant.tsv",
        "corpus.zh-Hant.tsv", "terms.zh-Hant.tsv", "pedia-bilingual.tsv", "variable-values.zh-Hant.tsv",
        "string-templates.zh-Hant.tsv", "colony-bilingual.tsv"]
# 包內路徑 → workplace/reports 下的來源（目錄只收 *.json）
MASKS = {"menu": "goal181-colony-rest/slot-fonts-v66/menu", "card": ["goal099-card-fonts/NAMES.TXT-0x000008EA.json",
                                                     "goal099-card-fonts/LABELS.TXT-0x000008F2.json"],
         "cards-rest": "goal140-nation-cards/fonts", "third-card": "goal139-third-card/fonts",
         "intro": "goal136-nation-intro/masks", "build1.json": "goal181-colony-rest/slot-fonts-v66/release/build1-font.json",
         "captions": "goal181-colony-rest/slot-fonts-v66/release/captions", "help": "goal142-help/fonts",
         "sea-atlas.json": "goal150-dynamic/atlas/sea-atlas.json", "options-title.json": "goal181-colony-rest/slot-fonts-v66/release/title-font.json",
         "option-rows": "goal181-colony-rest/slot-fonts-v66/release/row-fonts", "retire": "goal181-colony-rest/slot-fonts-v66/release/retire", "static": "goal166-spots/static-masks",
         "dialog-atlas.json": "goal181-colony-rest/slot-fonts-v66/dialog/dialog-atlas.json",
         "string-atlas.json": "goal181-colony-rest/20261004-port-fields/font/string-atlas.json"}
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


def verify_atlas_bindings(path, repo, names):
    """封裝前核對圖集與隨包譯稿，避免過期圖集令正式啟動回退原文。"""
    atlas = json.loads(path.read_text(encoding="utf-8"))
    expected = {key: sha((repo / "text" / name).read_bytes()) for key, name in names.items()}
    if atlas.get("bindings") != expected:
        raise ValueError("圖集與隨包譯稿綁定不同：" + str(path))
    if atlas.get("font_sha256") != "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c":
        raise ValueError("圖集字型指紋不同：" + str(path))


def reusable_masks(root, repo, manifest_sha):
    """只接受指紋固定且與現行譯文相同的已驗正式包字模。"""
    source = root / 'MANIFEST.json'
    if not manifest_sha or sha(source.read_bytes()) != manifest_sha:
        raise ValueError('字模來源 manifest 指紋不同')
    manifest = json.loads(source.read_text())
    if not VERSION.fullmatch(manifest['version']):
        raise ValueError('字模來源版本不合法')
    for name in TEXT:
        data = (root / 'text' / name).read_bytes()
        if data != (repo / 'text' / name).read_bytes() or manifest['files']['text/' + name] != {
                'sha256': sha(data), 'bytes': len(data)}:
            raise ValueError('字模來源譯文不同：' + name)
    paths = sorted((root / 'masks').rglob('*'))
    files = {}
    for path in paths:
        if path.is_symlink():
            raise ValueError('字模不得為符號連結')
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if path.suffix != '.json' or manifest['files'].get(name) != {'sha256': sha(data), 'bytes': len(data)}:
            raise ValueError('字模來源清冊不同：' + name)
        files[name] = (mask_bytes(path), 0o644)
    expected = {name for name in manifest['files'] if name.startswith('masks/')}
    if set(files) != expected or {name.split('/')[1] for name in files} != set(MASKS):
        raise ValueError('字模集合不完整')
    return files, {'version': manifest['version'], 'manifest_sha256': manifest_sha, 'files': len(files)}


def dependency_notices(binary, repo, target=("linux", "amd64")):
    """由實際二進位列出的依賴收取授權，缺來源時停止封裝。只在固定 Go 工具映像內執行。"""
    metadata = subprocess.run(["go", "version", "-m", str(binary)], check=True, capture_output=True, text=True).stdout
    runtime = metadata.splitlines()[0].split()[-1]
    build = dict(line.split()[1].split("=", 1) for line in metadata.splitlines()
                 if line.split() and line.split()[0] == "build" and "=" in line.split()[1])
    if (build.get("GOOS"), build.get("GOARCH")) != target:
        raise ValueError("封裝平台與二進位不同，預期：" + "/".join(target))
    env = subprocess.run(["go", "env", "GOROOT", "GOMODCACHE", "GOVERSION"], check=True, capture_output=True, text=True).stdout.splitlines()
    goroot, cache, version = env
    if runtime != version:
        raise ValueError("封裝 Go 工具版本與執行檔不同，不能套用其他版本的授權來源")
    files = {"LICENSES/Go-LICENSE.txt": ((Path(goroot) / "LICENSE").read_bytes(), 0o644)}
    dependencies = {"Go": {"version": runtime, "license_file": "LICENSES/Go-LICENSE.txt"}}
    for line in metadata.splitlines():
        fields = line.split()
        if not fields or fields[0] != "dep":
            continue
        module, revision = fields[1:3]
        if module == "github.com/wicanr2/dosgolem" and revision == "(devel)":
            directory = repo / "workplace/dosgolem"
            revision = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"],
                                      check=True, capture_output=True, text=True).stdout.strip()
            dirty = subprocess.run(["git", "-C", str(directory), "status", "--porcelain"],
                                   check=True, capture_output=True, text=True).stdout
            if dirty:
                raise ValueError("dosgolem 隔離副本尚有未提交修改，無法只以 commit 記錄封包來源")
        else:
            if revision == "(devel)":
                raise ValueError("未固定的第三方模組：" + module)
            escape = lambda s: "".join("!" + c.lower() if c.isupper() else c for c in s)
            directory = Path(cache) / (escape(module) + "@" + escape(revision))
        licenses = [p for p in directory.iterdir() if p.is_file() and p.name.lower() in
                    {"license", "license.txt", "license.md", "copying", "notice", "notice.txt", "notice.md"}]
        if not any(p.name.lower().startswith(("license", "copying")) for p in licenses):
            raise ValueError("模組授權缺失：" + module)
        names = []
        for source in sorted(licenses):
            name = "LICENSES/" + module.replace("/", "_") + "-" + source.name + ".txt"
            files[name] = (source.read_bytes(), 0o644)
            names.append(name)
        dependencies[module] = {"version": revision, "license_files": names}
    return files, dependencies


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True)
    p.add_argument("--repo", type=Path, default=Path("/repo"))
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--version-inspector", type=Path, help="容器內建置的inspect_release_version工具")
    p.add_argument("--readme", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True, help="dist-all 根目錄")
    p.add_argument("--format", choices=["tar.gz", "appimage", "windows-zip", "macos-zip"], default="tar.gz")
    p.add_argument('--mask-bundle', type=Path)
    p.add_argument('--mask-manifest-sha256')
    a = p.parse_args()
    if not VERSION.fullmatch(a.version):
        raise SystemExit("版號不符 v.X.Y.Z-YYYYMMDD")
    if (a.output / a.version).exists():
        raise SystemExit("交付版本目錄已存在；請用新的版號，禁止覆寫既有封包")
    embedded_version = None
    if a.version != "v.0.0.0-19700101":
        if a.version_inspector is None:
            raise SystemExit("正式封包必須檢查實際內嵌版號，請指定--version-inspector")
        embedded_version = json.loads(subprocess.run(
            [str(a.version_inspector), str(a.binary), a.version],
            check=True, capture_output=True, text=True).stdout)
    reports = a.repo / "workplace/reports"
    if bool(a.mask_bundle) != bool(a.mask_manifest_sha256):
        raise ValueError('字模來源與 manifest 指紋必須一起指定')
    mask_files, mask_source = reusable_masks(a.mask_bundle, a.repo, a.mask_manifest_sha256) if a.mask_bundle else ({}, None)
    dialog_path = a.mask_bundle / 'masks/dialog-atlas.json' if a.mask_bundle else reports / MASKS['dialog-atlas.json']
    string_path = a.mask_bundle / 'masks/string-atlas.json' if a.mask_bundle else reports / MASKS['string-atlas.json']
    verify_atlas_bindings(dialog_path, a.repo,
                          {"corpus": "corpus.zh-Hant.tsv", "terms": "terms.zh-Hant.tsv",
                           "draft": "draft.zh-Hant.tsv", "values": "variable-values.zh-Hant.tsv",
                           "help": "help-bilingual.tsv", "pedia": "pedia-bilingual.tsv"})
    verify_atlas_bindings(string_path, a.repo,
                          {"templates": "string-templates.zh-Hant.tsv", "sea": "sea-status.zh-Hant.tsv",
                           "corpus": "corpus.zh-Hant.tsv", "draft": "draft.zh-Hant.tsv",
                           "terms": "terms.zh-Hant.tsv", "colony": "colony-bilingual.tsv"})
    windows = a.format == "windows-zip"
    macos = a.format == "macos-zip"
    platform = "macos-universal" if macos else "windows-x86_64" if windows else "linux-x86_64"
    native_name = "colonization-window.exe" if windows else "colonization-window"
    top = f"colonization-cht-{a.version}-{platform}"
    files = {}  # 包內路徑 → (bytes, mode)
    files["bin/" + native_name] = (a.binary.read_bytes(), 0o755)
    files["colonization-cht.sh"] = ((a.repo / "tools/release/colonization-cht.sh").read_bytes(), 0o755)
    files["LICENSE"] = ((a.repo / "LICENSE").read_bytes(), 0o644)
    files["LICENSES/Cubic-11-OFL.txt"] = ((a.repo / "font/Cubic-11-OFL.txt").read_bytes(), 0o644)
    files["LICENSES/ymfm-BSD-3-Clause.txt"] = ((a.repo / "workplace/dosgolem/audio/opl/LICENSE.ymfm").read_bytes(), 0o644)
    if macos:
        from macos_bundle import macos_notices
        notices, dependencies, binary_validation = macos_notices(a.binary, a.repo, dependency_notices)
    else:
        notices, dependencies = dependency_notices(a.binary, a.repo, ("windows" if windows else "linux", "amd64"))
    files.update(notices)
    files["README.txt"] = (a.readme.read_text(encoding="utf-8").replace("{VERSION}", a.version).encode("utf-8"), 0o644)
    for name in TEXT:
        files[f"text/{name}"] = ((a.repo / "text" / name).read_bytes(), 0o644)
    for dest, src in MASKS.items():
        if a.mask_bundle:
            continue
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
    files.update(mask_files)
    for bad in files:
        if re.search(r"\.(png|idx|pal|memory|sav|exe|ss|pik|ttf)$", bad, re.I) and bad != "bin/" + native_name:
            raise SystemExit("包內不得有原版或畫面檔：" + bad)
    manifest = {"version": a.version, "platform": platform, "license": "LicenseRef-RRSAL-1.0（第三方元件依各自授權）",
                "requires_original": {"note": "需自備合法取得的 DOS 版原版 COLONIZE 目錄；以下檔案 SHA-256 不符時前端拒絕啟動",
                                      "files": ORIGINAL},
                "dependencies": dependencies,
                "files": {k: {"sha256": sha(v[0]), "bytes": len(v[0])} for k, v in sorted(files.items())}}
    if macos:
        manifest["binary_validation"] = binary_validation
    if mask_source:
        manifest['mask_source'] = mask_source
    if embedded_version is not None:
        manifest["frontend_version"] = embedded_version
    files["MANIFEST.json"] = ((json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode(), 0o644)
    if a.format in {"appimage", "windows-zip", "macos-zip"}:
        if macos:
            from macos_bundle import build_macos_zip
            package_data, bundled_manifest = build_macos_zip(
                files, manifest, top, (a.repo / "tools/release/colonization-cht.sh").read_text(encoding="utf-8"))
            suffix = "zip"
        elif windows:
            from windows_bundle import build_windows_zip
            package_data, bundled_manifest = build_windows_zip(
                files, manifest, top, (a.repo / "tools/release/colonization-cht.sh").read_text(encoding="utf-8"))
            suffix = "zip"
        else:
            from appimage_bundle import build_appimage
            package_data, bundled_manifest = build_appimage(files, manifest, a.repo, top)
            suffix = "AppImage"
        a.output.mkdir(parents=True, exist_ok=True)
        version_dir = a.output / a.version
        version_dir.mkdir()
        out = version_dir / "patch"
        out.mkdir()
        pkg = out / f"{top}.{suffix}"
        pkg.write_bytes(package_data)
        pkg.chmod(0o755)
        sums = {"version": a.version, "packages": {f"patch/{pkg.name}":
                {"sha256": sha(package_data), "bytes": len(package_data)}}}
        (version_dir / "SHA256SUMS.json").write_text(json.dumps(sums, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"package": str(pkg), **sums["packages"][f"patch/{pkg.name}"],
                          "files": len(bundled_manifest["files"]) + 1}, ensure_ascii=False))
        return 0
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
    # 最後以排他建立版本目錄再次守門，避免兩個並行封裝互相覆寫。
    a.output.mkdir(parents=True, exist_ok=True)
    version_dir = a.output / a.version
    version_dir.mkdir()
    out = version_dir / "patch"
    out.mkdir()
    pkg = out / f"{top}.tar.gz"
    pkg.write_bytes(gz.getvalue())
    sums = {"version": a.version, "packages": {f"patch/{pkg.name}": {"sha256": sha(pkg.read_bytes()), "bytes": pkg.stat().st_size}}}
    (a.output / a.version / "SHA256SUMS.json").write_text(json.dumps(sums, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"package": str(pkg), **sums["packages"][f"patch/{pkg.name}"], "files": len(files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
