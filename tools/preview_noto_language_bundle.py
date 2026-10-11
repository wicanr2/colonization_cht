#!/usr/bin/env python3
"""規格060 DRAFT：組裝完整顯示資源候選包，供隔離載入／交換驗證。"""

import argparse
import base64
import json
import os
from pathlib import Path

from check_language_font_coverage import FACES, LOCALES
from check_noto_fixed_masks import check as check_fixed
from language_catalog import BaseCatalog, ROOT, canonical, new_output, require, sha
from preview_noto_runtime_atlas import CONSUMERS
from render_language_font_sample import HASHES


def verify_atlas(atlas, views, consumer):
    require(atlas["font_sha256"] == HASHES["noto"] and atlas["font_px"] == 30 and atlas["floor_px"] == 12,
            "圖集字型或範圍不同")
    require(atlas["bindings"] == {name: sha(views[file]) for name, file in CONSUMERS[consumer].items()}, "圖集文本綁定不同")
    require(set(atlas["sizes"]) == {str(px) for px in range(12, 31)}, "圖集缺字級")
    charset = None
    for size in atlas["sizes"].values():
        height = size["height"]
        require(type(height) is int and 0 < height <= 128 and
                0 <= size["cjk_ink_top"] < size["cjk_ink_bottom"] <= height, "圖集高度不合法")
        keys = set(size["glyphs"])
        require({chr(code) for code in range(32, 127)} <= keys and
                (charset is None or charset == keys), "圖集缺ASCII或各級字集不同")
        charset = keys
        for key, glyph in size["glyphs"].items():
            raw = base64.b64decode(glyph["alpha"], validate=True)
            require(len(key) == 1 and type(glyph["w"]) is int and 0 < glyph["w"] <= 128 and
                    len(raw) == glyph["w"] * height, "圖集字格不合法")
    require(sha("".join(sorted(charset)).encode()) == atlas["charset_sha256"], "圖集字集指紋不同")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("fixed", "fields", "baseline-masks", "atlases", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file(), "需Docker隔離組裝")
    require(check_fixed(args.fixed, args.fields, args.baseline_masks) == 256, "四語固定欄位不完整")
    base = BaseCatalog()
    atlas_report = json.loads((args.atlases / "check.json").read_bytes())
    require(atlas_report["source_binding_sha256"] == base.registry["source_binding_sha256"] and
            atlas_report["font_sha256"] == HASHES["noto"] and atlas_report["license_sha256"] == HASHES["license"], "圖集來源版本不同")
    fields = json.loads(args.fields.read_bytes())["fields"]
    products, receipts = {}, {}
    for locale in LOCALES:
        face, family = FACES[locale]
        provenance = atlas_report["locales"][locale]
        require((provenance["face"], provenance["family"]) == (face, family), "圖集地區不同")
        views = {}
        for table, _, _, _ in base.tables:
            name = table["file"]
            data = (args.fixed / locale / "text" / name).read_bytes()
            require(data == (args.atlases / locale / "text" / name).read_bytes() and
                    sha(data) == provenance["text_sha256"][name], "圖集與固定欄位文本不同")
            views[name] = data
        files = {"text/" + name: data for name, data in views.items()}
        for field in fields:
            name = "masks/" + field["file"]
            files[name] = (args.fixed / locale / name).read_bytes()
        atlases = {}
        for consumer in ("dialog", "string"):
            name = consumer + "-atlas.json"
            data = (args.atlases / locale / name).read_bytes()
            require(sha(data) == provenance["atlas_sha256"][name], "圖集檔案指紋不同")
            atlas = json.loads(data)
            verify_atlas(atlas, views, consumer)
            atlas.update(locale=locale, face=face, family=family, license_sha256=HASHES["license"],
                         source_binding_sha256=base.registry["source_binding_sha256"])
            atlases[consumer] = atlas
            files["masks/" + name] = canonical(atlas) + b"\n"
        # 沿用既有海上圖集8級契約；字格來自已烘製的完整Noto圖集。
        # 這只證明字形及來源完整，海上各欄位仍須在原文重建後實測。
        full = atlases["string"]
        sizes = {str(px): full["sizes"][str(px)] for px in range(15, 23)}
        sea = {"font_sha256": HASHES["noto"], "font_px": 22, "floor_px": 15,
               "catalog_sha256": sha(views["sea-status.zh-Hant.tsv"]),
               "charset_sha256": full["charset_sha256"], "sizes": sizes, **sizes["22"],
               "locale": locale, "face": face, "family": family, "license_sha256": HASHES["license"],
               "source_binding_sha256": base.registry["source_binding_sha256"],
               "scope": "DRAFT；海上字形完整，各欄位原文重建及GUI未驗"}
        files["masks/sea-atlas.json"] = canonical(sea) + b"\n"
        require(len(files) == 80, "需13表及67份顯示資源")
        manifest = {"schema": 1, "kind": "DRAFT-display-language-bundle", "locale": locale,
                    "original_rendering": False, "face": face, "family": family,
                    "font_sha256": HASHES["noto"], "license_sha256": HASHES["license"],
                    "source_binding_sha256": base.registry["source_binding_sha256"],
                    "files_sha256": {name: sha(data) for name, data in sorted(files.items())},
                    "limitations": ["未連結正式後端；未驗原文快取重建、即時切換或正常GUI。"]}
        products[locale] = files, manifest
        receipts[locale] = {"files": len(files), "fixed_masks": 64, "atlases": 3, "tables": 13,
                            "manifest_sha256": sha(canonical(manifest) + b"\n")}
    products["en"] = {}, {"schema": 1, "kind": "DRAFT-display-language-bundle", "locale": "en",
                            "original_rendering": True, "files_sha256": {},
                            "source_binding_sha256": base.registry["source_binding_sha256"]}
    output = new_output(args.output, directory=True)
    for locale, (files, manifest) in products.items():
        folder = output / locale
        folder.mkdir()
        for name, data in files.items():
            path = folder / name
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_bytes(data)
        (folder / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    report = {"kind": "DRAFT-complete-resource-assembly-not-runtime-switching",
              "source_binding_sha256": base.registry["source_binding_sha256"], "locales": receipts,
              "inputs_sha256": {"fixed_check": sha((args.fixed / "check.json").read_bytes()),
                               "atlas_check": sha((args.atlases / "check.json").read_bytes()), "fields": sha(args.fields.read_bytes())},
              "source_sha256": {name: sha((ROOT / "tools" / name).read_bytes()) for name in
                                ("preview_noto_language_bundle.py", "preview_noto_fixed_masks.py", "check_noto_fixed_masks.py")}}
    (output / "check.json").write_bytes(canonical(report) + b"\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in output.rglob("*")), "輸出擁有權不同")
    print("ASSEMBLED_DRAFT_COMPLETE_LANGUAGE_RESOURCES", sha((output / "check.json").read_bytes()))


if __name__ == "__main__":
    main()
