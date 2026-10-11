#!/usr/bin/env python3
"""規格054：烘製四語六列正式Noto圖集及既有格式的七列私用TSV。"""
import argparse
import base64
import json
import os
from pathlib import Path

from PIL import ImageFont, __version__ as pillow_version, features

from check_language_font_coverage import FACES, LOCALES, font_charset
from language_catalog import BaseCatalog, ROOT, canonical, load_translation, new_output, require, sha, write_tsv
from preview_language_field_atlas import expected_masks, menu_marked, raster_cell
from preview_language_field_layout import MEASUREMENT_SHA, REVIEW_SHA, visible_menu_text
from render_language_font_sample import HASHES

KEYS = ["MENU.TXT:" + key for key in ("0x00000264", "0x00000276", "0x00000299", "0x000002A5", "0x00000384", "0x000003BC")]
ALIAS = "MENU.TXT:0x0000028D"
MENU_SHA = "5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("noto", "license", "measurement", "review", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file() and pillow_version == "9.4.0", "需Docker內Pillow9.4.0")
    for path, expected in ((args.noto, HASHES["noto"]), (args.license, HASHES["license"]),
                           (args.measurement, MEASUREMENT_SHA), (args.review, REVIEW_SHA)):
        require(path.is_file() and sha(path.read_bytes()) == expected, "固定字型、授權或原版欄位證據不符")
    measurement = json.loads(args.measurement.read_text())
    require(measurement["source_keys"] == KEYS and measurement["safe"] == [80, 12, 159, 77] and
            measurement["row_tops"] == [13, 21, 29, 37, 53, 69] and measurement["original_cap"] == 5,
            "原版欄位量測不同")
    base = BaseCatalog()
    baseline = (ROOT / "text/draft.zh-Hant.tsv").read_bytes()
    table, header, _, _ = next(t for t in base.tables if t[0]["catalog"] == "draft")
    products, reports = {}, {}
    for locale in LOCALES:
        data = baseline if locale == "zh-Hant" else (ROOT / f"text/game.{locale}.tsv").read_bytes()
        entries = base.entries
        if locale != "zh-Hant":
            entries, missing = load_translation(base, data, locale)
            require(not missing, "不可使用不完整語言譯稿")
        require(entries["draft", ALIAS]["text"].strip() == entries["draft", KEYS[2]]["text"].strip(),
                "Fortify同文來源的譯文不同，無法安全覆蓋")
        rows = []
        for key in KEYS + [ALIAS]:
            row = base.entries["draft", key]["row"].copy()
            require(row["source_sha256"] == MENU_SHA, "MENU來源不符")
            row[table["display_column"]] = entries["draft", key]["text"]
            rows.append(row)
        draft = write_tsv(header, rows)
        face, family = FACES[locale]
        font = ImageFont.truetype(str(args.noto), 18, index=face)
        require(font.getname()[0] == family, "Noto地區face不符")
        raw_rows = [row["zh_hant"].strip() for row in rows[:6]]
        marked = [menu_marked(text) for text in raw_rows]
        chars = sorted(set("".join(visible_menu_text(text) for text in raw_rows)) | {chr(c) for c in range(32, 127)})
        present, _ = font_charset(args.noto, face, family)
        require(all(ord(ch) in present for ch in chars), "正式字型缺字")
        glyphs, audit = {}, {}
        for ch in chars:
            cell, details = raster_cell(font, ch)
            glyphs[ch] = {"w": cell.width, "alpha": base64.b64encode(cell.tobytes()).decode()}
            audit[ch] = details
        ascent, descent = font.getmetrics()
        cap = font.getbbox("國", anchor="ls")
        bind = {"draft": sha(draft), "baseline": sha(baseline), "source": MENU_SHA,
                "layout": MEASUREMENT_SHA, "license": HASHES["license"],
                "locale_profile": sha(canonical({"locale": locale, "face": face, "family": family}))}
        atlas = {"font_sha256": HASHES["noto"], "font_px": 18, "floor_px": 18, "bindings": bind,
                 "sizes": {"18": {"height": ascent + descent, "ascent": ascent,
                                    "cjk_ink_top": ascent + cap[1], "cjk_ink_bottom": ascent + cap[3], "glyphs": glyphs}},
                 "charset_sha256": sha("".join(chars).encode()), "scope": "spec054 compact orders only"}
        masks, bounds, advances = expected_masks(atlas, marked, {
            "safe_size": [316, 260], "native_safe": [80, 12, 159, 77], "native_row_tops": measurement["row_tops"]})
        products[locale] = (draft, atlas, masks)
        reports[locale] = {"source_catalog_sha256": sha(data), "draft_sha256": sha(draft), "glyphs": len(chars),
                           "row_ink": bounds, "row_advances": advances, "glyph_audit": audit,
                           "expected_mask_sha256": {name: sha(mask.tobytes()) for name, mask in masks.items()}}
    output = new_output(args.output, directory=True)
    for locale, (draft, atlas, masks) in products.items():
        (output / f"draft.{locale}.tsv").write_bytes(draft)
        (output / f"atlas.{locale}.json").write_bytes(canonical(atlas) + b"\n")
        for name, mask in masks.items():
            mask.save(output / f"mask.{locale}.{name}.png")
    report = {"kind": "spec054-noto-orders", "pillow": pillow_version, "freetype": features.version_module("freetype2"),
              "script_sha256": sha(Path(__file__).read_bytes()), "source_binding_sha256": base.registry["source_binding_sha256"],
              "locales": reports, "outputs_sha256": {p.name: sha(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output / "bake-check.json").write_bytes(canonical(report) + b"\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in output.iterdir()), "輸出擁有權不同")
    print("BAKED_SPEC054_ORDERS", output, sha((output / "bake-check.json").read_bytes()))


if __name__ == "__main__":
    main()
