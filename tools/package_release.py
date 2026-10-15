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
    """規格061／062／063／064／065 READY：只收已驗生成素材，逐項核對，拒絕額外檔案。"""
    root = repo / "graphics"
    if root.is_symlink() or {p.name for p in root.iterdir()} != {"manifest.json", "building-032.png", "sea-148.png", "person-100.png", "building-024.png", "building-016.png", "building-021.png", "building-027.png", "building-035.png", "building-039.png", "building-042.png", "building-043.png", "building-044.png", "building-045.png", "building-009.png", "icons-022.png", "icons-024.png", "icons-025.png", "icons-026.png", "icons-027.png", "icons-028.png", "icons-029.png", "icons-030.png", "icons-031.png", "icons-032.png", "icons-033.png", "icons-034.png", "icons-035.png", "icons-036.png", "icons-037.png", "icons-038.png", "icons-005.png", "icons-023.png", "icons-042.png", "icons-053.png", "icons-056.png", "icons-059.png", "icons-062.png", "icons-067.png", "icons-068.png", "icons-069.png", "icons-094.png", "icons-122.png", "icons-123.png", "icons-124.png", "terrain-079.png"}:
        raise ValueError("HD素材目錄不同")
    files = {}
    for name, digest, limit in [
            ("manifest.json", "2d0e2ae15139151bcf0f5c9b8fdeb08a209602fd7c955705dfbc340aea109f84", 256 << 10),
            ("building-032.png", "c33885bd2570cc5ec0eb204aece69f1363b66fab5c1f16da82786f3b7e5139d8", 8 << 20),
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
            ("icons-024.png", "b4dfd073993baf0bfdeb2ebc54a8f729226fecda6f3ccbccc7c9bf2175740051", 8 << 20)]:
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise ValueError("HD素材不是有界檔案：" + name)
        raw = path.read_bytes()
        if sha(raw) != digest:
            raise ValueError("HD素材指紋不同：" + name)
        files["graphics/" + name] = (raw, 0o644)
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
