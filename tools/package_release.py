#!/usr/bin/env python3
"""組裝 Linux tar.gz／AppImage、Windows 或 macOS ZIP 到 dist-all/<版本>/patch/，只在容器內執行。

包內只放本作品與第三方允許散布的元件：前端執行檔、啟動器、五語譯稿 TSV、Noto及既有Cubic 11字模、設定列字型、
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
from pathlib import Path, PurePosixPath

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


def language_bundle_files(root, repo, ui_font, ui_license, mask_names):
    """收取已驗五語包；內容與manifest逐位元組保持一致，執行期另做完整型別核對。"""
    registry = json.loads((repo / "tools/language-catalogs.json").read_bytes())
    font_hash = "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"
    license_hash = "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2"
    if ui_font.is_symlink() or ui_license.is_symlink() or sha(ui_font.read_bytes()) != font_hash or sha(ui_license.read_bytes()) != license_hash:
        raise ValueError("Noto字型或授權指紋不同")
    files = {"ui/NotoSansCJK-Regular.ttc": (ui_font.read_bytes(), 0o644),
             "LICENSES/NotoSansCJK-OFL.txt": (ui_license.read_bytes(), 0o644),
             "text/frontend-ui.tsv": ((repo / "text/frontend-ui.tsv").read_bytes(), 0o644)}
    expected = {"text/" + name for name in TEXT} | set(mask_names)
    if len(expected) != 80 or len(mask_names) != 67:
        raise ValueError("既有顯示資源清冊不完整")
    locales = {"zh-Hant": (3, "Noto Sans CJK TC"), "zh-Hans": (2, "Noto Sans CJK SC"),
               "ja": (0, "Noto Sans CJK JP"), "ko": (1, "Noto Sans CJK KR"), "en": (0, "")}
    if root.is_symlink() or {p.name for p in root.iterdir()} not in (set(locales), set(locales) | {"check.json"}):
        raise ValueError("五語根目錄集合不同")
    for locale, (face, family) in locales.items():
        directory = root / locale
        source = directory / "manifest.json"
        if directory.is_symlink() or source.is_symlink():
            raise ValueError("語言包不得為符號連結")
        manifest_bytes = source.read_bytes()
        manifest = json.loads(manifest_bytes)
        names = manifest.get("files_sha256", {})
        if manifest.get("schema") != 1 or manifest.get("kind") != "DRAFT-display-language-bundle" or \
                manifest.get("locale") != locale or manifest.get("original_rendering") != (locale == "en") or \
                manifest.get("source_binding_sha256") != registry["source_binding_sha256"] or \
                (locale != "en" and (manifest.get("font_sha256") != font_hash or manifest.get("license_sha256") != license_hash or \
                 manifest.get("face") != face or manifest.get("family") != family)) or set(names) != (set() if locale == "en" else expected):
            raise ValueError("語言包清冊或來源不同：" + locale)
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
        if actual != set(names) | {"manifest.json"}:
            raise ValueError("語言包有缺件或額外檔案：" + locale)
        for name, digest in names.items():
            relative = PurePosixPath(name)
            path = directory / name
            if not relative.parts or relative.is_absolute() or ".." in relative.parts or \
                    any(p.is_symlink() for p in [path, *path.parents]) or path.stat().st_size > 64 << 20:
                raise ValueError("不合法的語言資源路徑：" + name)
            data = path.read_bytes()
            if sha(data) != digest:
                raise ValueError("語言資源指紋不同：" + locale + "/" + name)
            if locale == "zh-Hant" and name.startswith("text/") and data != (repo / name).read_bytes():
                raise ValueError("繁中包譯稿不同於目前來源：" + name)
            files["languages/" + locale + "/" + name] = (data, 0o644)
        files["languages/" + locale + "/manifest.json"] = (manifest_bytes, 0o644)
    return files


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


def hd_asset_files(repo):
    """規格061至070 READY：只收已驗生成素材，逐項核對，拒絕額外檔案。"""
    root = repo / "graphics"
    if root.is_symlink() or {p.name for p in root.iterdir()} != {"portraits-king-1.png", "kinglose-000.png", "kingwin-000.png", "portraits-leaders-1.png", "portraits-leaders-2.png", "portraits-leaders-3.png", "portraits-leaders-4.png", "portraits-cc-1.png", "portraits-cc-2.png", "portraits-cc-3.png", "openbonk-poses-1.png", "openbonk-poses-2.png", "openguy-poses-1.png", "openguy-poses-2.png", "openguy-poses-3.png", "openguy-poses-4.png", "portraits-mayors.png", "opening-credits-1.png", "opening-credits-2.png", "opening-credits-3.png", "building-047.png", "icons-remaining-1.png", "icons-remaining-2.png", "icons-remaining-3.png", "clos-bkg-000.png", "declarat-000.png", "decoind-000.png", "kinglss2-000.png", "report9-000.png", "woodpan2-000.png", "mss2-000.png", "mss5-000.png", "openmon3-poses.png", "openfish-poses.png", "icons-113.png", "manifest.json", "mss0-000.png", "mss1-000.png", "mss3-000.png", "mss4-000.png", "nameplat-000.png", "nameplat-001.png", "nameplat-002.png", "wdcut01-000.png", "wdcut03-000.png", "wdcut07-000.png", "woodfram-000.png", "icons-003.png", "icons-011.png", "icons-118.png", "terrain-037.png", "terrain-038.png", "terrain-039.png", "terrain-041.png", "terrain-042.png", "terrain-043.png", "terrain-045.png", "terrain-046.png", "terrain-047.png", "terrain-053.png", "terrain-054.png", "terrain-055.png", "terrain-057.png", "terrain-058.png", "terrain-059.png", "terrain-061.png", "terrain-062.png", "terrain-063.png", "terrain-069.png", "terrain-070.png", "terrain-073.png", "terrain-075.png", "terrain-090.png", "terrain-091.png", "terrain-092.png", "terrain-093.png", "terrain-094.png", "terrain-095.png", "terrain-097.png", "terrain-098.png", "terrain-099.png", "terrain-101.png", "terrain-102.png", "terrain-022.png", "terrain-026.png", "terrain-064.png", "terrain-081.png", "terrain-082.png", "terrain-084.png", "terrain-085.png", "terrain-149.png", "terrain-texture-000.png", "terrain-texture-001.png", "terrain-texture-002.png", "terrain-texture-003.png", "terrain-texture-004.png", "terrain-texture-005.png", "terrain-texture-006.png", "terrain-texture-007.png", "terrain-texture-008.png", "terrain-texture-009.png", "terrain-texture-010.png", "terrain-texture-011.png", "icons-054.png", "building-032.png", "sea-148.png", "person-100.png", "building-024.png", "building-016.png", "building-021.png", "building-027.png", "building-035.png", "building-039.png", "building-042.png", "building-043.png", "building-044.png", "building-045.png", "building-009.png", "icons-022.png", "icons-024.png", "icons-025.png", "icons-026.png", "icons-027.png", "icons-028.png", "icons-029.png", "icons-030.png", "icons-031.png", "icons-032.png", "icons-033.png", "icons-034.png", "icons-035.png", "icons-036.png", "icons-037.png", "icons-038.png", "icons-005.png", "icons-023.png", "icons-042.png", "icons-053.png", "icons-056.png", "icons-059.png", "icons-062.png", "icons-067.png", "icons-068.png", "icons-069.png", "icons-094.png", "icons-122.png", "icons-123.png", "icons-124.png", "terrain-079.png", "cursor-000.png", "terrain-006.png", "terrain-009.png", "terrain-017.png", "terrain-066.png", "terrain-071.png", "terrain-074.png", "terrain-077.png", "terrain-078.png", "terrain-080.png", "terrain-096.png", "terrain-147.png", "terrain-150.png", "terrain-112.png", "terrain-113.png", "terrain-116.png", "terrain-119.png", "terrain-126.png", "terrain-127.png", "terrain-136.png", "terrain-139.png", "opentile-000.png", "openmenu-000.png", "woodtile-000.png", "parch-000.png", "difficul-000.png", "nations-000.png", "customiz-000.png", "icons-006.png", "icons-007.png", "icons-014.png", "icons-015.png", "icons-127.png", "icons-008.png", "icons-009.png", "icons-016.png", "icons-058.png", "icons-060.png", "icons-066.png", "icons-081.png", "icons-082.png", "icons-083.png", "icons-084.png", "icons-085.png", "icons-086.png", "icons-087.png", "icons-088.png", "icons-089.png", "icons-090.png", "icons-091.png", "icons-092.png", "icons-093.png", "icons-095.png", "icons-096.png", "icons-097.png", "icons-098.png", "icons-106.png", "icons-107.png", "icons-065.png", "icons-073.png", "icons-074.png", "icons-075.png", "icons-076.png", "icons-077.png", "icons-101.png", "icons-102.png", "icons-103.png", "icons-104.png", "icons-105.png", "icons-109.png", "icons-110.png", "icons-111.png", "icons-112.png", "icons-125.png", "icons-126.png", "icons-128.png", "icons-129.png", "colony-000.png", "europe-000.png", "report1-000.png", "report2-000.png", "report3-000.png", "report4-000.png", "report5-000.png", "report6-000.png", "report7-000.png", "report8-000.png", "ccbkgd-000.png", "woodpanl-000.png", "openbord-000.png", "opening-000.png", "opening-sun-000.png", "opening-ship-static-000.png", "opening-dragon-000.png", "opening-compass-000.png", "opening-fish-top-000.png", "opening-squid-000.png", "opening-fish-bottom-000.png", "opening-galley-000.png", "opening-volcano-000.png", "opening-wind-000.png", "opening-mermaid-000.png", "openship-000.png", "openship-001.png", "openship-002.png", "openship-003.png", "openship-004.png", "openship-005.png", "openship-006.png", "openship-007.png", "opening-sun-base-000.png", "opensun-000.png", "opensun-001.png", "opensun-002.png", "opensun-003.png", "opensun-004.png", "opensun-005.png", "opensun-006.png", "openwnd1-000.png", "openwnd1-001.png", "openwnd1-002.png", "openwnd1-003.png", "openwnd1-004.png", "openwnd1-005.png", "openwnd1-006.png", "openwnd1-007.png", "openwnd1-008.png", "openwnd1-009.png", "openwnd2-000.png", "openwnd2-001.png", "openwnd2-002.png", "openwnd2-003.png", "openwnd2-004.png", "openwnd2-005.png", "openwnd2-006.png", "openwnd2-007.png", "openwnd2-008.png", "openwnd2-009.png", "openwnd2-010.png", "openmon1-000.png", "openmon1-001.png", "openmon1-002.png", "openmon1-003.png", "openmon1-004.png", "openmon1-005.png", "openmon1-006.png", "openmon1-007.png", "openmon1-008.png", "openmon1-009.png", "openmon1-010.png", "openmon1-011.png", "openmon1-012.png", "openmon1-013.png", "openmon1-014.png", "openmon2-000.png", "openmon2-001.png", "openmon2-002.png", "openmon2-003.png", "openmon2-004.png", "openmon2-005.png", "opening-fish-clear-000.png", "king1-000.png", "kinglss1-000.png", "levn0001-000.png", "levn0002-000.png", "levn0003-000.png", "levn0004-000.png", "levn0005-000.png", "levn0006-000.png", "levn0007-000.png", "levn0008-000.png", "levn0009-000.png", "levn0010-000.png", "building-000.png", "building-001.png", "building-002.png", "building-003.png", "building-004.png", "building-005.png", "building-006.png", "building-007.png", "building-008.png", "building-012.png", "building-013.png", "building-014.png", "building-015.png", "building-018.png", "building-019.png", "building-020.png", "building-022.png", "building-023.png", "building-025.png", "building-026.png", "building-028.png", "building-029.png", "building-033.png", "building-034.png", "building-036.png", "building-037.png", "building-038.png", "building-040.png", "building-041.png", "building-046.png"}:
        raise ValueError("HD素材目錄不同")
    files = {}
    for name, digest, limit in [
            ("manifest.json", "3ada0eaac7d0a684377ed7934d4ff360afdcffd675f0894901738f5032a1ea52", 16 << 20),
            ("kinglose-000.png", "bbee76741ab0738c568a652b4f878d677f7c7f56b48e6b9b83ac8befa0debdb1", 8 << 20),
            ("kingwin-000.png", "cf932a5e425ab773fe6d5cd89531ec51a32738c7b9f4a8e57a2f566e706c72f1", 8 << 20),
            ("portraits-king-1.png", "2f95cfc8d5fd8dbb691fe4fd36f4bb6ff8f8dc2429e02972d0ed14e7459d968b", 8 << 20),

            ("portraits-leaders-1.png", "b5d7472d8a503408f0b4d269f46710fdedcbf7c99f7e9056415dea20397265dd", 8 << 20),
            ("portraits-leaders-2.png", "f7f7126825de4916e746fee692c9f7a7225bd4a3c4d7513975d6acf09cecab17", 8 << 20),
            ("portraits-leaders-3.png", "99447d399cd13ffff064d7362043069de2c756ca1815a35a65c843fca0436d3c", 8 << 20),
            ("portraits-leaders-4.png", "489943b661fdd8d18752e5345d4817cbfd6d57de88b904fb00adf260f28818de", 8 << 20),
            ("portraits-cc-1.png", "f0cc47e0877a5d80a5807d7bf87884fb555c0bf416fddc156bf72f53152059aa", 8 << 20),
            ("portraits-cc-2.png", "a7343fe4bbb7c275e9115911d909a683bc368a0e6ec6bec50e00bcd85cf657fc", 8 << 20),
            ("portraits-cc-3.png", "bfe5b3c56c5af1b67886936f07005906a5827f8d98076b3f65a011c1669001d9", 8 << 20),
            ("openbonk-poses-1.png", "d3f17c0fd9f9c859df6168d60c111a433a452eb04d1dd7ed129d99486968687e", 8 << 20),
            ("openbonk-poses-2.png", "227e6ecb0a653ef073afcd0e0ae13a9ca38519af16a8bfa6528e625db2e131c8", 8 << 20),
            ("openguy-poses-1.png", "39aeb0fb329e0845a9ec71f5ac7b906ccea3b6e5ab211e6bd4700912f70d7f9c", 8 << 20),
            ("openguy-poses-2.png", "63d7f1e73003c14420283589114cf3ffeee9a872f7fa87d4187950292e860b45", 8 << 20),
            ("openguy-poses-3.png", "1a4b1beada849f2dd75cc896cf1611f03a6dc487a6010add2c91be2eed0bc7bc", 8 << 20),
            ("openguy-poses-4.png", "5b85488fa9771ea63518cbd4dc9a5eb3396f0934cb322ec08d46aed99a5d9cc2", 8 << 20),
            ("portraits-mayors.png", "e01ab16bd8b07fbee2429b806b37d4b4fe998e79776c6a1b2eee2f53a78e76d7", 8 << 20),
            ("opening-credits-1.png", "13d729a4cf5065e803020b443093c4f8f6c76f4b2ab95bdafdeb2ef8328c6136", 8 << 20),
            ("opening-credits-2.png", "f08bfa35abda18cba402b83a202a3428c22fd6f52518becf1377e6bcb1dbc3ee", 8 << 20),
            ("opening-credits-3.png", "21f41f2ecf9310f8176d0c08ce30867c03ca9779fedad2f6ea20ac3eb7059476", 8 << 20),
            ("building-047.png", "31225a16cea5cba6b723958871834e6e998d46242a070ac9b8703a0efa13c69e", 8 << 20),
            ("icons-remaining-1.png", "d552f0fddb682daa079541e77f90457e30e0d40b97153f60aad7ee1712e80013", 8 << 20),
            ("icons-remaining-2.png", "53c3ff8224229d44bba6206aa5b79ace4c5e26bc2c0ba6efa565359ad75c1577", 8 << 20),
            ("icons-remaining-3.png", "1c5ac8f02545fcd75a55a61c86afac05ef285714dbe28b06f39f1f20f1e7a140", 8 << 20),
            ("clos-bkg-000.png", "255cd12373413df49522af80e6ac1e47341c386262bf6ba56ec8d4a1da9b1176", 8 << 20),
            ("declarat-000.png", "f664b8d249a5cbb3d41ea407320a22a12d38cdf6113475cec33d01ebe6d2b619", 8 << 20),
            ("decoind-000.png", "95084427c84814bc916de08365a257798d79be4481d0b44b340d561cb7dc4dc0", 8 << 20),
            ("kinglss2-000.png", "12128d43a2d92be70a1c7d71c204d94de7aa5668816cae23578fc6f66db7fdb1", 8 << 20),
            ("report9-000.png", "c877a2dd3047d3f5c39e14d45a37dae9c49962996ed09aaafd2982706a2be3cc", 8 << 20),
            ("woodpan2-000.png", "a82b4a52c01d2fad381bd2d1b28ca682f69a98f4818349ddadcae49fbf5c8420", 8 << 20),
            ("mss2-000.png", "1fc1d5a58b8184028b4ea40069128309b8af3ff967d69527547c33b6c91912dc", 8 << 20),
            ("mss5-000.png", "9a5108a7aa542407cc2b6033f585fe0704acdd323ab8efc65a1994530075d344", 8 << 20),
            ("openmon3-poses.png", "d3332db373c91fd060aa51eda6a07b7f3c79ae85a8e9f0143b18188289843a42", 8 << 20),
            ("openfish-poses.png", "044e246edab2fd9ae4d68a89a5d62a3f6e1a7e8c706da4c6597134d9ecb35fd1", 8 << 20),
            ("icons-113.png", "7e6c49b20af1e32e3f031775a79e2568ad72e2e7b9086f31e59d365bf1c81a78", 8 << 20),
            ("mss0-000.png", "4eb7b99e24ff63edfd696966100cb235b4f3ad6bc5e932c35cd041373c515f0a", 8 << 20),
            ("mss1-000.png", "df8102fb1c85913fd5f9e6d59aad2e6810c28082e8211620832347f77c1385e3", 8 << 20),
            ("mss3-000.png", "4baaf1bbbb33d582244cd1d32151fcc0d43990686997d71016c263ac337d25a5", 8 << 20),
            ("mss4-000.png", "bccf173205bb238826ddd1f3320f73833bcef8d29d39c6ff57098567dad7bb24", 8 << 20),
            ("nameplat-000.png", "a83f8d877119865c57bd7cde8e2cca719195a2241dd8cf90324d2b13c26fe559", 8 << 20),
            ("nameplat-001.png", "7ed710283c6417e93d46b6a9b0e517e50a24086a2843043beacfae41d4d76c17", 8 << 20),
            ("nameplat-002.png", "aceea09addd5a3ea6da1a6b7ec94e31023210c5c1f8a1458257b0a814e2bae9f", 8 << 20),
            ("wdcut01-000.png", "0365f7da88cd03f09e8ea61300fd88a455fea01d18a3495bd0d09206797623b0", 8 << 20),
            ("wdcut03-000.png", "0b636747daa2268c93a3922804fdae7734416e578fb68524f33df14942494bb4", 8 << 20),
            ("wdcut07-000.png", "995c910786dffb6894b46c9fc1b2536fd6b150e66450da531a3b1a3af659f803", 8 << 20),
            ("woodfram-000.png", "f4fa697e0572d98c80ff45ee89a3f5c1b52893400f2ed1e2c815e72f3b59b13f", 8 << 20),
            ("icons-003.png", "98e35a733d1741b3d14ae7dace783d5eafedf0aff89afae05fe1ede6878a3c5b", 8 << 20),
            ("icons-011.png", "858d4962dba4b24075dca0bc2c3845ef8c0d8af2537bea5137f02554a4060044", 8 << 20),
            ("icons-118.png", "0a447fb0f0381c35b4598aec52daf36bb3f2e4bfea3075500e26c98879d9a22a", 8 << 20),
            ("terrain-037.png", "c2b06c63785427142d5e3ea2f7a718d0bdf7500b46df2ca9194c0269cba3ccd9", 8 << 20),
            ("terrain-038.png", "d799c54b7a71c0dfde816c9de1f3068ed26e4e92fd6fa9e6970e8d769582fc74", 8 << 20),
            ("terrain-039.png", "fb2d33135e4a630a9c7e0884fc63debf8603005658a8959c70c34b99cd2fdfa6", 8 << 20),
            ("terrain-041.png", "8d8157639c193133d8afff4c5d4afca96ccf28ceb678ccbeb77a46e15dadda8c", 8 << 20),
            ("terrain-042.png", "0ca4df1ccc4d794dc16594e45c1d35208de12ee5aaf19b9b1198a472ccd396a4", 8 << 20),
            ("terrain-043.png", "ddf6e5018d0a8ad2ebb8e523e4e35e32bf3384f1fbefb98e3c6f3b6607aaf550", 8 << 20),
            ("terrain-045.png", "89bf5e5dfe662cf94deffd63965e667877f3ade8b195803b54edb7d946cefd14", 8 << 20),
            ("terrain-046.png", "f8fa324b09c6aab381b7a6e5b49070b271f2d57620f4dff6557741e25f4da17e", 8 << 20),
            ("terrain-047.png", "a2676ebeadfd2f11d97e9eb597ec9cae5fef2c3a75e4bb4f2e08b2e8e4b358f2", 8 << 20),
            ("terrain-053.png", "757ad7b4e0388aee65ec731e3f656163314d4ba691d116a3ab300cd3823c1f49", 8 << 20),
            ("terrain-054.png", "2eb31fd902b492ed31dd8fa14c94ccc7472471888195a9d52c581f0d29112b79", 8 << 20),
            ("terrain-055.png", "0a634ad05e1e5c882abd842019eb7e320db56ff2258ce8fe333d87f29342a693", 8 << 20),
            ("terrain-057.png", "c6af971a11f59289288b018480ba97644f269437b107b32ddb196795fe6c6989", 8 << 20),
            ("terrain-058.png", "99e97180d76520e3b4664fb020c1e62af6526db71694db4a18c2f76472a94b24", 8 << 20),
            ("terrain-059.png", "637f83ac10285a1322fb76f06bbb14f92b1b79b27c9271f961bdc5fe6f2181f1", 8 << 20),
            ("terrain-061.png", "b07c2a1e00d28a65ff84d467c9116a4343add09fea5be6e821a116c790e9a185", 8 << 20),
            ("terrain-062.png", "8b62e33be3e02f7aac09f6d5064e3fb18dbc63597036ec4a94c885b91b89b02f", 8 << 20),
            ("terrain-063.png", "df74d3ed20779069d029f5fa7ef5b915d48037e78fd6a432952da5269b092690", 8 << 20),
            ("terrain-069.png", "b9e2c4de052ce8f2a2f44fd8a1ac20513f40e763f608a0d87b3d4a8207b6327d", 8 << 20),
            ("terrain-070.png", "5463ed8462332505dbde8097a6fc1cc88e39f95f9959742beb0cf5dfcca92f71", 8 << 20),
            ("terrain-073.png", "7f3d72597956f6d1b1dc6135069d385f6bbe3421f901564385acdefcb2a01201", 8 << 20),
            ("terrain-075.png", "e0e9e714a10d30b1e37844af45156085a0c5d7fbe9fd03f39eb2798e193e4b27", 8 << 20),
            ("terrain-090.png", "995e77309f26810e8fa09a2868d07618d5d66f20685c8a2706a8692f4e793481", 8 << 20),
            ("terrain-091.png", "75f0a1395caeef409f6858948d64db9bb2456d96452799230b8a7d6ff77d9437", 8 << 20),
            ("terrain-092.png", "d9e6182355f41bf658507605c24ffabd7f1f209fc9121ef6b643e24b89cf8669", 8 << 20),
            ("terrain-093.png", "de064f3aa6e92233aa03754e573e1370f893b34b5ce7c451ad67197e8cb06eff", 8 << 20),
            ("terrain-094.png", "6cc545c3cd830c6cc0020bc516af9bd02f9f29ddf2cc07e2a5e136788ad331e7", 8 << 20),
            ("terrain-095.png", "c64c82ecd84b683607500a42b24d6196a2bc465b6ba52695b4a338bd5c713b3e", 8 << 20),
            ("terrain-097.png", "c2b8a678eb4cd66f1f448dcb49a3b5688889125d228e7f36f04451230dfaa7fc", 8 << 20),
            ("terrain-098.png", "5d6a62e17fffaf38ea51afb16fecc2af49939c956b1c4100511dfc2d4fb0340c", 8 << 20),
            ("terrain-099.png", "5653f44b1ed294b72c11f0cf9758d3c36cd182e075e061917ec3e0386e4508b7", 8 << 20),
            ("terrain-101.png", "f71be657a47bc57c40d45419969848604a6d6c099f8d41aa000e8f9ddfbde9a0", 8 << 20),
            ("terrain-102.png", "d802420c4c2b105e94fc418b40e81063ad49c1c017fac66511158ab95508abf7", 8 << 20),
            ("terrain-022.png", "8f63f587cb984ca099d1a30d884753dbb5d043c1339dce1fa3fba922c845b690", 8 << 20),
            ("terrain-026.png", "02f8b2bfddee72008a69a409d077fa499f9c251ce1948f5d13c7c65354189856", 8 << 20),
            ("terrain-064.png", "f9d0f991bb6675b90da0ba74caa631c4245024dbf93afc320cf197782b78c0f5", 8 << 20),
            ("terrain-081.png", "64c10fcc14668cac6c34609ab01728c6535415f9d3bafd31e1e63fb70f0b8cb8", 8 << 20),
            ("terrain-082.png", "e9f630a2a5f8a67d8e0f61a7f348648807d4bfd88288815bcd49aa58feeb8751", 8 << 20),
            ("terrain-084.png", "a9dc9f403b5d20ce70d5d76f49ab02892613ff5c472045268080d880fe4be34b", 8 << 20),
            ("terrain-085.png", "6bd00650c24cc3a1c6bbe08d5184121ed2bec9e9bc538c6e0df630ec3dec18e5", 8 << 20),
            ("terrain-149.png", "6392b90ac606b3a5b30ed384c57bc64a6a6766d1116d85aadf440fd215dcd4a0", 8 << 20),
            ("terrain-texture-000.png", "1cef0ad5f9c5fca566f10f23f6b92e28bc169c515615ebad2868dc93812ef1f2", 8 << 20),
            ("terrain-texture-001.png", "ec509b042efc8d561bd975460b7f3183fcfffa0aa20979417f7d5b8ec490d2fd", 8 << 20),
            ("terrain-texture-002.png", "0ec35827e02d910b63218b2b3d8ac46618d45984ba47a790fcd19813b30069ea", 8 << 20),
            ("terrain-texture-003.png", "19bd3b79998db01e26cb8d36bfc8549a23381281436f544d4cc6147a55401944", 8 << 20),
            ("terrain-texture-004.png", "7eb28c6927c45c8cf316e894876afc90d578532ad185ec5072699eac898345c7", 8 << 20),
            ("terrain-texture-005.png", "aed5b8739b8aae9bede8e3b24fb99b0984c1683a3c450648ed111f6016198fb4", 8 << 20),
            ("terrain-texture-006.png", "a06bd0f8d717c68589ff2be53d11b488ba886b768509c989013b8ceca9010621", 8 << 20),
            ("terrain-texture-007.png", "5139e0ac0f4d9373fc2ac98d66379a5fea9cc01a4e9e6fe5291455f6e3a7dcbf", 8 << 20),
            ("terrain-texture-008.png", "ace86713539fbc3071393d5bae9719bd9bcc4352e04008b55d33b88f57f38eb2", 8 << 20),
            ("terrain-texture-009.png", "70d84cba2a017956e75114222aab68201c91595aea5519fcc424ea1d3d372f08", 8 << 20),
            ("terrain-texture-010.png", "b99151ec34ca369beb34fa41e8fbea3fed582f37b078f3528c955380522c7386", 8 << 20),
            ("terrain-texture-011.png", "2fbd9b54cff243599b43d441b154da5d1d85aefd2d7cabe0d6e54150c474c562", 8 << 20),
            ("icons-054.png", "0abb719aa0518b9ef295d8b9a7aa865105dfb1b1facd9333a6a8c06e0955868a", 8 << 20),
            ("building-000.png", "be73e486cc1a2251df5b77b001268404e3aa9149f1a0d613215953b974951f07", 8 << 20),
            ("building-001.png", "fbb98fe74f66c1e71223868888d7e2f03d025af7813899a68490160c8901f8de", 8 << 20),
            ("building-002.png", "28d992b808439e4ec0a9117f14ca645eec903e6ebde631b324894f8caf5d952f", 8 << 20),
            ("building-003.png", "7d7ba364a4c80631d8d17a21c999d64b17fbe9c94958498b9f1926e43b04858b", 8 << 20),
            ("building-004.png", "c7150437bc61edddc4491c85cfd28a283d832eb8eb1e3735495c0fbb0c9bd01b", 8 << 20),
            ("building-005.png", "600455bdefddde32395477711a0b0b6bd619dad98dd940d65b729bb526f51b88", 8 << 20),
            ("building-006.png", "5ece7efa3f4f0d5b644a19fd7dd2e8cf85a16fc16328fd6472886674d9b9e587", 8 << 20),
            ("building-007.png", "37722b6edb876c96b6fc2f186fc98ac211292973e3fcd909f0f67a4a7165feef", 8 << 20),
            ("building-008.png", "2dcbd2f491626e43ef19f19b4f504138aa28f7b3c61865eea55feb9e243ca2be", 8 << 20),
            ("building-012.png", "0a209fc01aba2700476081cef9c21a45350a57cb459269845aeb98ec220ba63e", 8 << 20),
            ("building-013.png", "111a5a75f2ba31f6cc788a53f3b70d847349f6abd17a661d7aa2bee88282e57a", 8 << 20),
            ("building-014.png", "e61345a39b9f68d3623cb50ce089f99d1619ff0aec038172c0b8859ea9974d85", 8 << 20),
            ("building-015.png", "de7baee7faf1ec9ef725b74dbb22e244cefc101209bb5c3912107965044f4202", 8 << 20),
            ("building-018.png", "b00bd9cde6e143b3307f670f70899cefa20c02dc87e3073b9adc9d755f130968", 8 << 20),
            ("building-019.png", "fdabcccc60857158ef61b5fcfa63d7371dc4f60d3d0e01fd1766064f2dc37fd5", 8 << 20),
            ("building-020.png", "f14a40b5750c9c0ed1cc6f72594cf7e50415a43b9449a8083d85ad04c222fa4a", 8 << 20),
            ("building-022.png", "e3c9e76f560b741e6bfcdc545959c0b883d945614c21c0396f3dfd0508aa0b3b", 8 << 20),
            ("building-023.png", "c50fc75b33e60e5a6092688f0c03cff5d5eea024b85fde18cb4039726eceaafb", 8 << 20),
            ("building-025.png", "1ec3dc44f3a942e3bec47b824c9fbc96ad37f162f2c34078b46f25bccb46e086", 8 << 20),
            ("building-026.png", "7346b1ce2df7b0a586e25b2b51501dc5472abb0801b54b22ceeb679cebc8879e", 8 << 20),
            ("building-028.png", "40f608ea2942f2b1d28d8656b8dffce085d78cd63e652493570f23c6e4bfbefa", 8 << 20),
            ("building-029.png", "f8d614256699f655cb03234442a6c9f54f50e748a823a1a5d79dffc6efa70700", 8 << 20),
            ("building-033.png", "727e709cfea47ed0b39e17177b2d1a466179a35deb92899f0cac9a631bbcb704", 8 << 20),
            ("building-034.png", "cf141a3eee4401f15f3298ecc107aded316d4e16b5836b38f02338788d2b520c", 8 << 20),
            ("building-036.png", "f11c3b4b58a8768f39a28bc9c5d086e20018e0374846adf6fa9594fab6c7246c", 8 << 20),
            ("building-037.png", "f73e86dad84756ebc730c411a1c5a5463ae2c53a2361757b0305542a2973ed94", 8 << 20),
            ("building-038.png", "0efcf5e97bc578a901c0d5a79bdec7ffd57d9b5fe77e36ed946252d6a0e50979", 8 << 20),
            ("building-040.png", "462163db5c17fcc5cd561c1eafcfd18330bf0cc1129e298e356a618e27abd0c6", 8 << 20),
            ("building-041.png", "ab4ec26b3db95262bac5e0bdba170bd56e4bf26f3684187789c6401dba7b9cc6", 8 << 20),
            ("building-046.png", "21a027f4373c9432668675a2e2a0deb89c5d67977c8dbe1fd20fa4ed5407b68d", 8 << 20),
            ("king1-000.png", "c703753a240057c7379a4c192e3d97349d45ef5d12a8e27beddd1bf1468e504b", 8 << 20),
            ("kinglss1-000.png", "1c57a5064823e0c0e249d1d05a3fe8fe60cf82909213b7b87283af77a654bdde", 8 << 20),
            ("levn0001-000.png", "a84dd22420d8e7ccae6b946c726a95f06a76f1b0203348f503b45a642c387934", 8 << 20),
            ("levn0002-000.png", "4ffe42db8bb35f335ccefc119d67abc8db4b4ccc0443ea1481afabc6aa66d6f4", 8 << 20),
            ("levn0003-000.png", "eb67be5269b10bdd06ae684c5a765e8eab6eff1db1c2b0bf3e1ac735a7341651", 8 << 20),
            ("levn0004-000.png", "d6bc3d180ded72fad9bff9bf635042547318882efa65db28e75196ff4d5ffae8", 8 << 20),
            ("levn0005-000.png", "0b68ffd8701d8da18ddbbaa2a6213836decdcf161102c29960b36adc0bb2e962", 8 << 20),
            ("levn0006-000.png", "a6107a6fd2894978c6df67a909e72591129d6b7445c0d0f55920f5375f56d495", 8 << 20),
            ("levn0007-000.png", "38376c3261d238fe1acd65003f3baf2a455f10ac83d891be44261f13877c394e", 8 << 20),
            ("levn0008-000.png", "a4a654d6206274d71c35c1ec90dbc5a78c09536b4bf727642e25722499dab50a", 8 << 20),
            ("levn0009-000.png", "d283d17b5144bd5f76980acb4580f5a25fa62caaffe1aa08d9f992c2c489167a", 8 << 20),
            ("levn0010-000.png", "5352ea8ac04f4aa173e7e1bb6bb90e169ecf3e63e14251a7a15bc96ee2f7bfe7", 8 << 20),
            ("openmon1-000.png", "4be2225b476ccb248856408a2b4a04e98970ead6109364e4efacb6adfd03f41f", 8 << 20),
            ("openmon1-001.png", "c3a11ea6464b0b8e6bc7525f4e2cac990d84d8412a09d7bf29ba6d25f4beb337", 8 << 20),
            ("openmon1-002.png", "c0abf16e75a15203b0a7bd9b206605bb0141af36ed4b6619aabedd17f2cf61eb", 8 << 20),
            ("openmon1-003.png", "c0abf16e75a15203b0a7bd9b206605bb0141af36ed4b6619aabedd17f2cf61eb", 8 << 20),
            ("openmon1-004.png", "c3a11ea6464b0b8e6bc7525f4e2cac990d84d8412a09d7bf29ba6d25f4beb337", 8 << 20),
            ("openmon1-005.png", "8a7e4987b6311cb92e759a0039f33dab525fd28dfc8bb5f4b466f5441bb7349f", 8 << 20),
            ("openmon1-006.png", "fda0184b21d1d2a7121a4df161930dc8be9cdacb64ee7fca01236edfeb815993", 8 << 20),
            ("openmon1-007.png", "f31fde8d6f5001b60c9d3739dc25e444f43bcdd0fbaea755c2a3f7aeb398dd70", 8 << 20),
            ("openmon1-008.png", "6e58348513ac0b23763ad4c4eeacff38ae71d7c17aeb3262a00c2f6d063de9db", 8 << 20),
            ("openmon1-009.png", "3e1e9e69ef9b1e5316dc675cecf6f12763419ccc6e03701f5ff5040abcbcec44", 8 << 20),
            ("openmon1-010.png", "74047eec81fd866e8b0e86172802f956502f6c3964904d904a519e2fee89aaa3", 8 << 20),
            ("openmon1-011.png", "2fa3f725f40c5605631747506482fcdf4f916e4520623e170f91000f12794fa2", 8 << 20),
            ("openmon1-012.png", "6d405f7fc0520592090e68c6e77bf9474d16c0b77adaa5ba66c201d60de76d00", 8 << 20),
            ("openmon1-013.png", "4cda4b2c1d0c7c1c7b856fca859a012851fb989e8256cb6422ac65b980cadd46", 8 << 20),
            ("openmon1-014.png", "a19437e2265404a4decc585023d5a4249f9f516c1b682d49873bf1031d24d9c9", 8 << 20),
            ("openmon2-000.png", "4df21248859a401ef388740f6089a102f9c5184a2532ba39cd3ddf18f8364d02", 8 << 20),
            ("openmon2-001.png", "aa6f665b8a66e3374fc9b01043d7cd534f2864f3a99e30b007f4590d0f9f568a", 8 << 20),
            ("openmon2-002.png", "5c4079882c28e4603d227184043b6f863b52c9be2b8c127fff72c8061eb505f2", 8 << 20),
            ("openmon2-003.png", "00176841dffebde08636fa70d8014873802c8509e7904b6eb800e1c218118903", 8 << 20),
            ("openmon2-004.png", "d679f6b15e1121a215c5f322edb0102123359a31a528aee6538a730f7cb037cd", 8 << 20),
            ("openmon2-005.png", "486dcad244e17e78ca4df20506865016c5fa7f0d7d1054f229353e9b76677660", 8 << 20),
            ("opening-fish-clear-000.png", "96d98080dec2b7f0cdac9fea3e42a0ca093dc7ca6dee90f0c16f4a783ad62ada", 8 << 20),
            ("openwnd1-000.png", "640eae91aa2d7c5c0b2458ca2ed5878a7eb1d8dd25ceee25798c7ab3d9dc4728", 8 << 20),
            ("openwnd1-001.png", "126bb44afc8a1c2738206c06d1e7151751c18fd2ef53bd7f34555afb69f832ee", 8 << 20),
            ("openwnd1-002.png", "1d6c3505856bf540dafbd274d397436b7da9f9fc94328b282c218c6779220cfc", 8 << 20),
            ("openwnd1-003.png", "711f736403512f20b7719c8707dd8e6c50c4fb0a0c76536e09c48981a08e403a", 8 << 20),
            ("openwnd1-004.png", "71214636aaef151352e438304af57d56734f0622ef0bb33e9dee51b6b5cfc5c3", 8 << 20),
            ("openwnd1-005.png", "126bb44afc8a1c2738206c06d1e7151751c18fd2ef53bd7f34555afb69f832ee", 8 << 20),
            ("openwnd1-006.png", "1d6c3505856bf540dafbd274d397436b7da9f9fc94328b282c218c6779220cfc", 8 << 20),
            ("openwnd1-007.png", "711f736403512f20b7719c8707dd8e6c50c4fb0a0c76536e09c48981a08e403a", 8 << 20),
            ("openwnd1-008.png", "71214636aaef151352e438304af57d56734f0622ef0bb33e9dee51b6b5cfc5c3", 8 << 20),
            ("openwnd1-009.png", "640eae91aa2d7c5c0b2458ca2ed5878a7eb1d8dd25ceee25798c7ab3d9dc4728", 8 << 20),
            ("openwnd2-000.png", "50f262a6de52be427996b88e039dea5954088d1aefcd4a00f55ffdc96e8523ba", 8 << 20),
            ("openwnd2-001.png", "7e8c61222ee8ab952983489d48dfd12a99cd586f3b3c0309e8313df523887bc6", 8 << 20),
            ("openwnd2-002.png", "8b6b7709028b1ad8a96e646e33c58ddb110c16d38145cc7952bfd536f4a699a9", 8 << 20),
            ("openwnd2-003.png", "20febf81ab3c84f9d59ce5d72e9eb57c7cf721098f84366b4c030d29af353dcf", 8 << 20),
            ("openwnd2-004.png", "9f886e5ae1b5ef59461de70ff614c8a41ab6a0584f1ad7d19c76ee1ce5f531ba", 8 << 20),
            ("openwnd2-005.png", "d3afd12231840a64e4e7eaca824b326f67ad3f44eae1ee9cb961103eda7db230", 8 << 20),
            ("openwnd2-006.png", "c623311dd0ed2a4e26397a7f4d9db7710911537d2b39ddff5133a042de763415", 8 << 20),
            ("openwnd2-007.png", "f96ab63b7d87175c656465af86f010cf1414810a97fc86923755aaa8806b2c13", 8 << 20),
            ("openwnd2-008.png", "26d8d9cbe543da4e5b29fe47db07175acb30fab0398e15086fbb163d6fb22c18", 8 << 20),
            ("openwnd2-009.png", "900819304747b7c2384f8d17165b7c3872c201eb376ad43cff7425437fbc2959", 8 << 20),
            ("openwnd2-010.png", "50f262a6de52be427996b88e039dea5954088d1aefcd4a00f55ffdc96e8523ba", 8 << 20),
            ("openship-000.png", "09e14223e2be64d9ef5d5906c096a830a45e236518aff711ae8497f395f811d6", 8 << 20),
            ("openship-001.png", "a23c30a4dfa47a1e4d33c620259b28f759b755847884c3f6a0912952b7be40bc", 8 << 20),
            ("openship-002.png", "3ce31e1cbd82324d62db9479e6045de9ccddf2d24421739ccf6c01455e17a1a0", 8 << 20),
            ("openship-003.png", "00cdfabed868febc55315a234e238adf44948c0d3f7bc0327dd7d3ec4db13a40", 8 << 20),
            ("openship-004.png", "f7f66a5d46e290809519063fc960db169b9a658cb6ea3009e4aa68b813195241", 8 << 20),
            ("openship-005.png", "56aeed9475ba88425638c4d64a9f7890e61b53ac4ba08e53b1e89be22e302c04", 8 << 20),
            ("openship-006.png", "10144ef24645a17e5faf35743ee55344abd13696fc0ccdc1cbee8d64c120059c", 8 << 20),
            ("openship-007.png", "c41c401191e532b8b19906fd36660e85bd34d05136c8911e42cbfdb6cb6785bd", 8 << 20),
            ("opening-sun-base-000.png", "854022582cadedcd346ec41cb963d2119e29c07c39605c6366b9028b5aa40410", 8 << 20),
            ("opensun-000.png", "c69a393d6af9ba22b5aea32ce1efe6b26a78ed6b737900ece5f1eb915546623c", 8 << 20),
            ("opensun-001.png", "873ce284ab4069b0408af60e73ab4778f58443f7b864a10c331f89d5c06cc8c9", 8 << 20),
            ("opensun-002.png", "49114d551ee4bc0369255363438004104165f30722b165104b007114a25a504d", 8 << 20),
            ("opensun-003.png", "9769956c3ddfc0e037d8e869b92fa0edee5ed67378ac72f011d725cbdef35d08", 8 << 20),
            ("opensun-004.png", "a9b519f01c4a86228b6bd85d2c8b99614d52ed439b2a2fa18a138c2a678007ef", 8 << 20),
            ("opensun-005.png", "b0377d7fcf53ef8cd68a7f8545fc7ddcf685ce83dd3ce58ee63c074ce18308a7", 8 << 20),
            ("opensun-006.png", "c137d13d87a7a9091fc84ccc1f8ab618cbefe344fac054b1cadbea2bfafbb93e", 8 << 20),
            ("openbord-000.png", "4764f149760efcd2bee209e0b625270c1257a1e04d56e36d8bd86b150e919c18", 8 << 20),
            ("opening-000.png", "d06c24c54a5c8957973495a359261c4436adf71ab5e828b3e74c9bceda737ea3", 8 << 20),
            ("opening-sun-000.png", "c69a393d6af9ba22b5aea32ce1efe6b26a78ed6b737900ece5f1eb915546623c", 8 << 20),
            ("opening-ship-static-000.png", "8af9b41cc6fa3727c2b79626e5dea27cf65d5a902d6adae0d3f2857e0f52284f", 8 << 20),
            ("opening-dragon-000.png", "6848b9e631d10121cc8b2c195e6edad273d12640cf69a8719571cc39f5482850", 8 << 20),
            ("opening-compass-000.png", "6ba308b116f64055f2fe4c99608edea0823d49e0914b7c7a4481e0bf5ce8f7ed", 8 << 20),
            ("opening-fish-top-000.png", "fc41e7d2fc68792db4cbad80087b17b21379d6ee06803fb2a0e00a199ac7109a", 8 << 20),
            ("opening-squid-000.png", "ccccbee3c531f4fe4705c9f2187babc8201dbdf0843caaff0c388dc267e1290b", 8 << 20),
            ("opening-fish-bottom-000.png", "e2b4bb5a7dca58f00fefedba777f73d764ceff68e76e07ccf65b2d9600fb2f97", 8 << 20),
            ("opening-galley-000.png", "fc8271c73682bd54ccadffaf105c783324f1d5202a2643466a18dfefc522f283", 8 << 20),
            ("opening-volcano-000.png", "24ef3ca78240d8fd7f893ba0026773665e2c1f29ac033a232577cae9734ac09b", 8 << 20),
            ("opening-wind-000.png", "ec223225bcab1d069845e2ba6f908e1fc44027f5bd865abaf1cee846786de521", 8 << 20),
            ("opening-mermaid-000.png", "d01062a7f075f8d83ee00ff0db63eb1c5d7c6e7a08f3110cfe78f1b10265e238", 8 << 20),
            ("opentile-000.png", "cb2a8af8077d1e6fd0082d753e7cc0251192df0705ebe34496f1954f5cdc4547", 8 << 20),
            ("openmenu-000.png", "2d688773ecc1bf1a1555d53d632f33fa571cf25a0ea930d38b5219b61ddc819f", 8 << 20),
            ("woodtile-000.png", "8580efcf85a45fa879938b5b73e8d54c58853dd9297e8ecd1f10801e637bb5d9", 8 << 20),
            ("parch-000.png", "4ef702ede0e2d0a46ea94b54fdca602f01071a36a16a83dd57918b8fab15847e", 8 << 20),
            ("customiz-000.png", "b01bdf7d2c3fe51a971319c42a1f46981939df5556060bb1796fbc89d72479bb", 8 << 20),
            ("difficul-000.png", "5777b23b5238c486824089fbb007b3bee4b514d248455553fbed559599830e57", 8 << 20),
            ("nations-000.png", "5ff2c9e794edde09433279fc1b610e1cbc95e24c4af0e08a649e82e959fec98c", 8 << 20),
            ("building-032.png", "c33885bd2570cc5ec0eb204aece69f1363b66fab5c1f16da82786f3b7e5139d8", 8 << 20),
            ("cursor-000.png", "2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4", 8 << 20),
            ("terrain-006.png", "53405c0a1fc73b5ec49fbe761a7e1e6c72046d48d64dea1a55a7f013458e29ff", 8 << 20),
            ("terrain-009.png", "c25474e28eaa8545a400714bc15053d6bcf2b420e0e2aeb834d89b692f5e654b", 8 << 20),
            ("terrain-017.png", "db2e8cc629d569f43d43f80fc9d04fae10a8719562149dcec514bb451a1edbbe", 8 << 20),
            ("terrain-066.png", "a9c86687d36b3960dac157d89ddf2cc1aa59491e5c26adf9a265c4e52ed016ab", 8 << 20),
            ("terrain-071.png", "3ac8bcc578422e026e0ac62344a86d709fa24d7ffa13a6ea104766118353a072", 8 << 20),
            ("terrain-074.png", "7153858ccb7c6121b71cb49ba74567403df777368557352e9f6f22a4ccc18a81", 8 << 20),
            ("terrain-077.png", "deaaa4e10ef707f8d4b58a108b48fdedce441c5e47e3711ab157e4928519e21f", 8 << 20),
            ("terrain-078.png", "1f9011c2eeb1a564a1a92ca7efb9785505e7599df59e2e31da65713883df5d79", 8 << 20),
            ("terrain-080.png", "3c00f1e33f831e32253da286c2637b64ee350d2f5c27221975f265eed838dc44", 8 << 20),
            ("terrain-096.png", "e5f5da26ea5bb831ebc7de78b1ef63f41ab72846a26044ae173983bbbf962367", 8 << 20),
            ("terrain-147.png", "091b73d1442dad61cc9b60ba6c796c477d8ed4298905272e35776c1bc4ae5a26", 8 << 20),
            ("terrain-150.png", "7be4837b98142b085e1f13da61eda97820819d2db727b73e1299faede4250bb6", 8 << 20),
            ("terrain-112.png", "68815b2980e61c1a97409f13bf22f43b7fc2b78cc4fc025e3f4fc6be0327e743", 8 << 20),
            ("terrain-113.png", "e8028a09d0f73ea70b3f391506d9434404fb3cfd2b7051f61343edc591ee3f97", 8 << 20),
            ("terrain-116.png", "afa949a845f2884360cb784dc786a598f913f78e32dbb93f61359202ebd19e6b", 8 << 20),
            ("terrain-119.png", "c2aa727fda0ed14153a65bdb20f619e05c93627a3069a1844eb9911ba2c41274", 8 << 20),
            ("terrain-126.png", "1bcf543164b4ad4e67b15ad008bb82132d7640b1af1e061db4d249b715302561", 8 << 20),
            ("terrain-127.png", "f530a6c574d45f0d333c9ed934e6a4a95df087b21e48687161d4407eb456c7ec", 8 << 20),
            ("terrain-136.png", "8acc65b9f0cffe5951642d6ba1e9049ce8af3d4f0f8ec795c3fd80a71d81c07e", 8 << 20),
            ("terrain-139.png", "38fa1e5ad7074e0da3e36a69284c1c136619b24dc9cc13ae067a517024068787", 8 << 20),
            ("terrain-079.png", "081ffb5506aa7aca0e80571053b85f0bdc920cb5e7884cf028521a1dd7ffaa58", 8 << 20),
            ("sea-148.png", "2c5d3edc8d38e44dc02d7ccb88e79e4f749edd8a0b1d3dfd54ec04b467ba61ff", 8 << 20),
            ("person-100.png", "be2ace90ee85444af2fdaabb568a4ec1c67b3d327e30122c1b30ac471f514346", 8 << 20),
            ("building-024.png", "cb83a56cde5f06bb13bc69237fe5476efb6b40eb8ea6cfb2fe0942f3fd3da462", 8 << 20),
            ("building-016.png", "4378783b1ea54f32af12047fb06f260b496d68459f1eaacb5d42d5231c11ecd1", 8 << 20),
            ("building-021.png", "f81583f35c5102290424fd6575b67f08e47ab2488af61ed67eea0244fafe46f7", 8 << 20),
            ("building-027.png", "59d78ffbe53983600336fa7b0919032fcb95f79f744f31c03242e6c2f7f4f4b1", 8 << 20),
            ("building-035.png", "05832b749f1cca7e97af3a8cdd3417c12284df2d6db43e4e6656de65c7a44e58", 8 << 20),
            ("building-039.png", "2c2f7f9c3c325c64b919b02ca37fd8876ad74850fa7f7e737ef96d15f6a1b8c0", 8 << 20),
            ("building-042.png", "34f7ee08d3429ed6a6659b5c5eb6aa1ecfdf1656a814a494658368c475fdd8d4", 8 << 20),
            ("building-043.png", "0d9ad7021e2ddf5a2062e6705ba0be869e4ac3781046262eec0b4984a371b928", 8 << 20),
            ("building-044.png", "004fdb0045fc47653fd40beef438d0f2922933639a68c95a1d7b504ed908afed", 8 << 20),
            ("building-045.png", "07049354109ff9bee01f103a2b408d227a607b8bba138cefc9de5af840f99915", 8 << 20),
            ("building-009.png", "bc7057fa60db21a120f3d2fd81d59f7ae77cfa56ac351aa6df9d455f7bac29b6", 8 << 20),
            ("icons-025.png", "5856ff32bdf7ef16ad2a47f548313ea3e19009f4386ab82b9a51bb4cf81e1d6a", 8 << 20),
            ("icons-026.png", "27aa649ab52f07522d05608b53b39cfb0b7e5a974e69060f197b6ddcc6ae20b2", 8 << 20),
            ("icons-027.png", "02210ba22e632b688253442b8df6c89bb1d909308ac4174b3679ebdd58798dac", 8 << 20),
            ("icons-028.png", "5ce1c6b9c5e01b95273bbc01bab79ec9f0441b93aabee89ca87385c129b14da1", 8 << 20),
            ("icons-029.png", "24b862d6f3f1ca8157b03757803891566331006688ef9f45b75d75941ecd2216", 8 << 20),
            ("icons-030.png", "c3b187d8aab2f608da297d4924846e9008dbd5344fa85d28f755ea5b43862ab9", 8 << 20),
            ("icons-031.png", "71d212dfcdcca9dd6685196a1afe237784f7674409e2f24e914af811f131ef9c", 8 << 20),
            ("icons-032.png", "ff9047b9f5f17e2f777146ca98e19b912e69e5a4258a0ddc9d94919a34d0a3f2", 8 << 20),
            ("icons-033.png", "83255fe1b54a440377de39a9986eeb006c20a1ea1bec029285a0765be2a7cb83", 8 << 20),
            ("icons-034.png", "31b17472008c841982e39c58661f12c6360fd43c69bb2162d9140dcaba69ab7e", 8 << 20),
            ("icons-035.png", "016841a1ce6ee72170fb4a846e462eac95457c5491a2e6f00182aa67fb3d044b", 8 << 20),
            ("icons-036.png", "43d1a5a0078f788d25583937514eba6d8eac8f96b398f4f950156d4c6e7bc5af", 8 << 20),
            ("icons-037.png", "5ec0f2a0c3cdd4369d76899a93ffe675346ebf8b65cdf2ac4080956dbaffbd44", 8 << 20),
            ("icons-038.png", "25eb4306ca4b8510b3cf6487106d138885048df5bfb6588bb39d08e7d16b29f5", 8 << 20),
            ("icons-006.png", "c862cdfa55ab3de416018c3450dc90c392ed7fd54c7fb5f2a9c31538f23442bb", 8 << 20),
            ("icons-007.png", "191f23d8ec4b49fbeff41864c0fd812f08b88fd0abbb83255955e3625da647a8", 8 << 20),
            ("icons-014.png", "22e18c47baaf6f5188d9dcfadd4e69ab41812acaf39274b3f377ae7bba059c39", 8 << 20),
            ("icons-015.png", "4b938de1299c6c0f5895993715325ad66b8328b9616f5c98fc0f2bce8f09c3a9", 8 << 20),
            ("icons-127.png", "c18b01f9ab0af49f84184c9fb11bcd582af71b5b8bccd7f3e07b01b2d7e5b235", 8 << 20),
            ("icons-008.png", "19045ad0de2cd24bf172f0dcbb5466ee677e1d3270b741dee66df81e7b2b5203", 8 << 20),
            ("icons-009.png", "9ae2a857a9f143a9747753d36e5d16dd506b0d2984fac310b20056c926d47ec2", 8 << 20),
            ("icons-016.png", "edfb3e4e2eed371c6d8fe5fb9c905af05dd62b515fd4b81455e0f50d037e8889", 8 << 20),
            ("icons-005.png", "94ebc3642cd0b069229f2e23fa633085ed53d89cf5c9965eafde74d56af99619", 8 << 20),
            ("icons-023.png", "305d74bd95d0c8bcfba54832a35398b1dd0f367f85bd1a9702cb3b6e968b1c18", 8 << 20),
            ("icons-042.png", "7f6f1eec0482e8751abf75e120d26d559e1edac12a1c3415061bdcc302be4d04", 8 << 20),
            ("icons-053.png", "e1fa16b2b82b837c47fb363df377e3710957ea46a92cd2bf4adfba0c676ea3b8", 8 << 20),
            ("icons-056.png", "6daf183dc19f65c5a692bd00eea66bbb8706d20dab05ff445b57615a40a06564", 8 << 20),
            ("icons-059.png", "2057be1b92f182c4a4b029c77d2d4184117a8d67e7a3d3cec72e80f5ab911dba", 8 << 20),
            ("icons-062.png", "e77fc69ec546250f2131cac885f7e7d5eaaa6789650e3455eeb298385c335680", 8 << 20),
            ("icons-067.png", "895de84eead2ce925dc3d4aa0c0caa75c2654558a3c3d08c858b0dc90e5fd50b", 8 << 20),
            ("icons-068.png", "9cc4ee823734a13f16defc12252e60d1cb679c2200c392b823269eba4a98dd8b", 8 << 20),
            ("icons-069.png", "0b379205f3b0c83e2af2dd93ad9d8b2eaf6f24a7c2a86a33063899ce5e202e56", 8 << 20),
            ("icons-094.png", "e82953c98cc131d7298651a5b3d1bb227a542e324dc7833d54b4cb6927d4413d", 8 << 20),
            ("icons-122.png", "6f85e33891c499da120ae419f0d206c618f6bd9af5d6bfd37a9ad95fb51c7da7", 8 << 20),
            ("icons-123.png", "4458545d6806f17d12b68ba634f5bf617bed20bb78f11fae7da0796cc8296fc1", 8 << 20),
            ("icons-124.png", "4e69339b0740bc0c732363eea1eb4bbbe8009aa9a15fda2f1e81bfbb70dca62f", 8 << 20),
            ("icons-022.png", "aa2230fc41fa34ccf782fd8b9c3311390add4c33bf380dd31099a63b3b5c44d8", 8 << 20),
            ("icons-024.png", "b4dfd073993baf0bfdeb2ebc54a8f729226fecda6f3ccbccc7c9bf2175740051", 8 << 20),
            ("icons-058.png", "61743ce80d8c32b180b1cc8c778af73cde0935115f1a83cd0099f2e8cd6179ce", 8 << 20),
            ("icons-060.png", "5422ec86e9c250d02fcdfaa731a3d8fdc34fcd3a74ceec5586aae72bd6836224", 8 << 20),
            ("icons-066.png", "2ee09b5d97a813fe09b714f45c6ef302b5a9021ba5b260ce7b7c66976cd930de", 8 << 20),
            ("icons-081.png", "860dbb88125bf15711a9cec5f79429de211203f5a25119834200f01557b570f0", 8 << 20),
            ("icons-082.png", "6064d0f3c204d227e3cc202a131b65777a19920f6db007f22889359d412f39c2", 8 << 20),
            ("icons-083.png", "daebfb120f397c41f2fc68e1e1ea8edf570a27a1f1dff300553234de119100da", 8 << 20),
            ("icons-084.png", "0bc1b2bf46b52a2d038cc4abddcb8617da9b111d6cebabbaeb6dd41336dae201", 8 << 20),
            ("icons-085.png", "f19cd765d4b288c2b56af2d20abaa1bdd0fe0c026da11f98088fe85078c5e203", 8 << 20),
            ("icons-086.png", "0eb43567c95ccf81cfcc107db10cacaa67d341b358da2043456a7793da8ef8c2", 8 << 20),
            ("icons-087.png", "9e440f2b86014f715a2ba92a9ab583ff71299d0d00f8e66eb77728c98cf460cd", 8 << 20),
            ("icons-088.png", "418541b1e716f9ff84bdc962eaa1f3c927ff5e7f18aab689b07e96eba55431f7", 8 << 20),
            ("icons-089.png", "e8c3874a0308134a36a634cd33201d2fc5350fa5fb8d42517e743e8f371733ad", 8 << 20),
            ("icons-090.png", "304baa75c942ea22384ccddf23edb50556ce87bc5f0fafa9092a6386478d42b7", 8 << 20),
            ("icons-091.png", "6733d1909558a3d29136749d19c79b47489a9ee01869a55220cbcfdb603ddc53", 8 << 20),
            ("icons-092.png", "9941464e8109e280301c26a6fdcacce810e9caa93931c547d3cb39de4b2b3806", 8 << 20),
            ("icons-093.png", "c1a16585d2424e742a00bc77824ebbcb54e98b786a99dce7bcd93331a8bf465d", 8 << 20),
            ("icons-095.png", "8103c8a0a1c837df57c1f31fa6c37ff24203684f3f16315b47218ada3b84232e", 8 << 20),
            ("icons-096.png", "1d7d88bc8004429571398c5f58e9528967e9565a1c5e5688a11389a7019e683c", 8 << 20),
            ("icons-097.png", "fc64e8b372dd064311e6e817a6a5b6bfcfdfc6515c8391e83c5297e5e359a38c", 8 << 20),
            ("icons-098.png", "5561bf7138e91d27e89698b83431c7dd46bc5708f28b7fc6fe76bf66f26b562d", 8 << 20),
            ("icons-106.png", "dbae8283bf2236b5b69e457f78d278c2df78f640f6a79010f6b0f33314ae8417", 8 << 20),
            ("icons-107.png", "fd6afc141275a481ac18631e86dcf0394c56fbdf8b578e83ba3afc360338dc9b", 8 << 20),
            ("icons-065.png", "c1186be2b4127c33eb7464480c506691a0164a7d331cd18fbc051bc4ca76ce73", 8 << 20),
            ("icons-073.png", "76bfd672ac14bbb9a68b81ab893efdf7a675d5c40733efa16d40331635ffe372", 8 << 20),
            ("icons-074.png", "74cca71efadd04f8697ba0a6cedec6506cc52eed8a3925c69fce61c2ff1b1e79", 8 << 20),
            ("icons-075.png", "f8861eab6bb9a69be1ea6314b2963978fd8be15ec27a0fc1ddb0f4ee71af2c25", 8 << 20),
            ("icons-076.png", "94a1b242e72c4ef31f1f344e9e9eaca13b430edbd57e6fbdad203370eb691f83", 8 << 20),
            ("icons-077.png", "6b64925d8335b5f3250e49696da2a9b50d18b0c3d63d31d1b4ef14c1797e31b7", 8 << 20),
            ("icons-101.png", "d82df85384a2a6c75d7cb98184e1d593a78346ed55134a32d6a4fbea510bc9f9", 8 << 20),
            ("icons-102.png", "dc55590e45ecc9c95f56ba37125612b9a5f814bc7ff17527251a0f6b2129aaaf", 8 << 20),
            ("icons-103.png", "dd0d8180853e005b01d9580fa538e12613fb0cb2f8dd189f85d6345817aa8da1", 8 << 20),
            ("icons-104.png", "44fd32a1b1701a173f23f437bbbbceba4e8087c7f45c644192314902f78f18ba", 8 << 20),
            ("icons-105.png", "c586c4f2d047be8fda3b847dca871665e1252bfed3b6030fcf0c655276b2c973", 8 << 20),
            ("icons-109.png", "81eee3e5b950fb663133bbdb3950800289972d618257c685181f965c50d46a9f", 8 << 20),
            ("icons-110.png", "05618744e0295a442dad9a816beb5565fd0173dd2f666a82d1d720b9f84d886e", 8 << 20),
            ("icons-111.png", "b2dd50563f2b1caf610b2f26061c398c54412354e779654e3a50080249046076", 8 << 20),
            ("icons-112.png", "2610ec1263fd3e534cfb522c25c70f7e6d56cfb485d030bb181dc6677e7aa254", 8 << 20),
            ("icons-125.png", "7237926576e6612c297e7359afcc0e3cb47705be6f2b3eda3112d0f0bbfc2dd9", 8 << 20),
            ("icons-126.png", "b49397ae191453cefb55113049b342779cfb079c4e7028fb37b5cc82174b405c", 8 << 20),
            ("icons-128.png", "7056fdc8859c79758cbd41041f4b9f6075e3495a78d09d3db97af8651376680f", 8 << 20),
            ("icons-129.png", "fb55e840e9a47eebda26348b2ce1c08f935227c32a32a17b86d49def1e8968af", 8 << 20),
            ("colony-000.png", "9a213f4f928becd7197f44ff20b2353dd94a1d222458f1fe51d802eeaecdd756", 8 << 20),
            ("europe-000.png", "fc4d8dfaa46b16ee1e03914b9a48eff84a1407dbd32ea9d045a2ad8ada7d5087", 8 << 20),
            ("report1-000.png", "529b8a8392f94c46a593970870801371daf70e851446343b086a6ad8063d8f56", 8 << 20),
            ("report2-000.png", "b7e52eafdf9f830b8103807b89139c2efa7cfdc4eb08e53c258433718583272b", 8 << 20),
            ("report3-000.png", "aa876913f682d2fd07657d53f53b8f179636c7a148d440bef61ca3e70a896be3", 8 << 20),
            ("report4-000.png", "ecfa6da65042c6878ac52a6ee5846d31096137b57e5c787f0650bee8aef69edc", 8 << 20),
            ("report5-000.png", "e319fa13165df66a36d05d7cf734849a40758a3214630cad4071b4e2e638eaf1", 8 << 20),
            ("report6-000.png", "2772fac9aa4798b2e8de8c0220cb76a9707c23e4b79c81b4275f252f1a546bbb", 8 << 20),
            ("report7-000.png", "68905d1be031d6b61321f21a47ce5acb64a38562b4bedbf189dcb89999d346ab", 8 << 20),
            ("report8-000.png", "809973e7312530c84ee4f41ad983d317ccab18fd97650b7270886e37cda65d2b", 8 << 20),
            ("ccbkgd-000.png", "777dbf6db416dee4872a7f8dfa86adce85aeca0d03c92ba216d349ce8e2a8c34", 8 << 20),
            ("woodpanl-000.png", "20a9e807bb330501e83565704a039134e4344a7550208c8813533ceb422d19d2", 8 << 20),
            ]:
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise ValueError("HD素材不是有界檔案：" + name)
        raw = path.read_bytes()
        if sha(raw) != digest:
            raise ValueError("HD素材指紋不同：" + name)
        files["graphics/" + name] = (raw, 0o644)
    if {Path(name).name for name in files} != {p.name for p in root.iterdir()}:
        raise ValueError("HD素材清單與封裝輸出不一致")
    return files


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language-bundles", type=Path, required=True)
    p.add_argument("--ui-font", type=Path, required=True)
    p.add_argument("--ui-license", type=Path, required=True)
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
    files.update(language_bundle_files(a.language_bundles, a.repo, a.ui_font, a.ui_license,
                                     {name for name in files if name.startswith("masks/")}))
    hd_files = hd_asset_files(a.repo)
    files.update(hd_files)
    for bad in files:
        if re.search(r"\.(png|idx|pal|memory|sav|exe|ss|pik|ttf)$", bad, re.I) and bad not in {"bin/" + native_name, *hd_files}:
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
