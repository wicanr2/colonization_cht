#!/usr/bin/env python3
"""規格057 DRAFT：烘完整四語字元圖集，只輸出新的workplace原型。"""

import argparse
import base64
import json
import os
from pathlib import Path
import platform

from PIL import ImageFont, __version__ as pillow_version, features

from check_language_font_coverage import FACES, LOCALES, font_charset
from language_catalog import BaseCatalog, ROOT, canonical, load_translation, make_views, require, sha
from preview_language_field_atlas import raster_cell
from render_language_font_sample import HASHES


GO_PINS = {
    "tools/dialog_overlay.go": "b93dcf45c424b8aac175f71da0e05d54782d9ccc36774fdd1ac7f0bbd69e8a50",
    "tools/string_overlay.go": "543afd88d0cdebb3723dd08e39745c883208bfa6af121f0ccffa24955b5ae59e",
}
CONSUMERS = {
    "dialog": {"corpus": "corpus.zh-Hant.tsv", "terms": "terms.zh-Hant.tsv",
               "draft": "draft.zh-Hant.tsv", "values": "variable-values.zh-Hant.tsv",
               "help": "help-bilingual.tsv", "pedia": "pedia-bilingual.tsv"},
    "string": {"templates": "string-templates.zh-Hant.tsv", "sea": "sea-status.zh-Hant.tsv",
               "corpus": "corpus.zh-Hant.tsv", "draft": "draft.zh-Hant.tsv",
               "terms": "terms.zh-Hant.tsv", "colony": "colony-bilingual.tsv"},
}


def full_charset(entries):
    # 保留ASCII全字集；控制碼與模板標記由消費端處理，不將字元存在當作排版通過。
    return sorted({ch for row in entries.values() for ch in row["text"] if ord(ch) >= 32} |
                  {chr(code) for code in range(32, 127)})


def make_sizes(path, face, family, characters):
    sizes, audit = {}, {}
    for pixels in range(30, 11, -1):
        font = ImageFont.truetype(str(path), pixels, index=face)
        require(font.getname()[0] == family, "地區字型不同")
        ascent, descent = font.getmetrics()
        probe = font.getbbox("國", anchor="ls")
        glyphs, overhang = {}, {}
        bounds = None
        for character in characters:
            cell, details = raster_cell(font, character)
            glyphs[character] = {"w": cell.width, "alpha": base64.b64encode(cell.tobytes()).decode()}
            box = cell.getbbox()
            if box and ord(character) >= 127:
                bounds = [min(bounds[0], box[1]), max(bounds[1], box[3])] if bounds else [box[1], box[3]]
            if details["legacy_clipped_pixels"] or details["width"] != details["legacy_width"]:
                overhang[character] = details
        sizes[str(pixels)] = {
            "height": ascent + descent, "ascent": ascent,
            "cjk_ink_top": ascent + probe[1], "cjk_ink_bottom": ascent + probe[3], "glyphs": glyphs,
        }
        audit[str(pixels)] = {
            "glyphs": len(glyphs), "height": ascent + descent, "ascent": ascent,
            "reference_cjk_ink": [ascent + probe[1], ascent + probe[3]],
            "all_non_ascii_ink": bounds, "expanded_cells": overhang,
        }
    return sizes, audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("noto", "license", "output"):
        p.add_argument("--" + field, type=Path, required=True)
    args = p.parse_args()
    require(Path("/.dockerenv").is_file() and platform.python_version().startswith("3.11.") and
            pillow_version == "9.4.0" and features.version("freetype2") == "2.12.1",
            "需固定Docker、Python3.11、Pillow9.4.0與FreeType2.12.1")
    for field in ("noto", "license"):
        path = getattr(args, field)
        require(path.is_file() and sha(path.read_bytes()) == HASHES[field], f"固定輸入不同：{field}")
    for path, expected in GO_PINS.items():
        require(sha((ROOT / path).read_bytes()) == expected, f"消費端來源不同：{path}")
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
            output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
            "需新的workplace輸出，父目錄擁有者須相同")
    base = BaseCatalog()
    loaded = {}
    for locale in LOCALES:
        if locale == "zh-Hant":
            entries, catalog_hash = base.entries, None
        else:
            data = (ROOT / f"text/game.{locale}.tsv").read_bytes()
            entries, missing = load_translation(base, data, locale, False)
            require(not missing, "完整圖集不可使用部分譯稿")
            catalog_hash = sha(data)
        loaded[locale] = entries, catalog_hash, make_views(base, entries, locale)
    output.mkdir()
    report = {
        "kind": "draft-full-noto-atlas-not-runtime-language-bundle",
        "source_binding_sha256": base.registry["source_binding_sha256"],
        "tool": {"python": platform.python_version(), "pillow": pillow_version,
                 "freetype": features.version("freetype2")},
        "source_sha256": {path: sha((ROOT / path).read_bytes()) for path in [
            *GO_PINS, "tools/preview_noto_runtime_atlas.py", "tools/preview_language_field_atlas.py",
            "tools/language_catalog.py", "tools/language-catalogs.json"]},
        "font_sha256": HASHES["noto"], "license_sha256": HASHES["license"], "locales": {},
        "limitations": ["No original execution, field layout, normal GUI or runtime switching proof.",
                        "Static masks and hardcoded display fragments are not part of these atlases."],
    }
    for locale, (entries, catalog_hash, views) in loaded.items():
        face, family = FACES[locale]
        characters = full_charset(entries)
        mapped, font_info = font_charset(args.noto, face, family)
        require(all(ord(character) in mapped for character in characters), "全文含缺字，不生成圖集")
        target = output / locale
        target.mkdir()
        text = target / "text"
        text.mkdir()
        for name, data in views.items():
            (text / name).write_bytes(data)
        sizes, audit = make_sizes(args.noto, face, family, characters)
        files = {}
        for consumer, bindings in CONSUMERS.items():
            atlas = {"font_sha256": HASHES["noto"], "font_px": 30, "floor_px": 12,
                     "bindings": {key: sha(views[name]) for key, name in bindings.items()},
                     "charset_sha256": sha("".join(characters).encode()), "sizes": sizes,
                     "scope": "DRAFT full Noto CJK atlas; OFL source: font/README.md"}
            data = canonical(atlas) + b"\n"
            name = consumer + "-atlas.json"
            (target / name).write_bytes(data)
            files[name] = sha(data)
        report["locales"][locale] = {
            "face": face, "family": family, "catalog_sha256": catalog_hash, "game_entries": len(entries),
            "font_metadata": font_info,
            "characters": len(characters), "charset_sha256": sha("".join(characters).encode()),
            "text_sha256": {name: sha(data) for name, data in views.items()},
            "atlas_sha256": files, "sizes": audit,
        }
        print(locale, len(entries), len(characters), "19 sizes; layout unverified", flush=True)
    (output / "check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    require(all(p.stat().st_uid == os.getuid() and p.stat().st_gid == os.getgid()
                for p in output.rglob("*")), "輸出擁有者不同")
    print("GENERATED_DRAFT_FULL_NOTO_ATLASES", sha((output / "check.json").read_bytes()))


if __name__ == "__main__":
    main()
