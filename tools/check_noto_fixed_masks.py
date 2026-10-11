#!/usr/bin/env python3
"""規格060 DRAFT：獨立核對四語固定字模的完整性、TSV綁定與安全區。"""

import argparse
import base64
import json
from pathlib import Path

from PIL import Image

from check_language_font_coverage import FACES, LOCALES
from language_catalog import BaseCatalog, ROOT, load_translation, make_views, require, sha
from preview_noto_fixed_masks import FIELD_SHA, field_text, native_evidence, rectangle
from render_language_font_sample import HASHES


def check(folder, field_path, baseline_masks):
    require(sha(field_path.read_bytes()) == FIELD_SHA, "固定欄位收據不同")
    fields = json.loads(field_path.read_bytes())["fields"]
    receipt = json.loads((folder / "check.json").read_bytes())
    require(receipt["kind"] == "DRAFT-four-locale-fixed-masks-not-runtime-bundle" and
            receipt["fields_sha256"] == FIELD_SHA and set(receipt["locales"]) == set(LOCALES), "收據種類或語言不同")
    require(receipt["font_sha256"] == HASHES["noto"] and receipt["license_sha256"] == HASHES["license"], "字型或授權不同")
    files = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() and p != folder / "check.json"}
    require(files == set(receipt["outputs_sha256"]), "缺檔或多檔")
    for name, digest in receipt["outputs_sha256"].items():
        require(sha((folder / name).read_bytes()) == digest, "輸出指紋不同：" + name)
    base, count = BaseCatalog(), 0
    require(receipt["source_binding_sha256"] == base.registry["source_binding_sha256"], "來源版本不同")
    for locale in LOCALES:
        entries = base.entries
        if locale != "zh-Hant":
            entries, missing = load_translation(base, (ROOT / f"text/game.{locale}.tsv").read_bytes(), locale)
            require(not missing, "譯稿缺件")
        views = make_views(base, entries, locale)
        face, family = FACES[locale]
        audits = receipt["locales"][locale]
        require(audits["face"] == face and audits["family"] == family and len(audits["fields"]) == 64, "地區或欄位數不同")
        audit_by_file = {item["file"]: item for item in audits["fields"]}
        require(set(audit_by_file) == {field["file"] for field in fields}, "欄位重複或缺件")
        for name, data in views.items():
            require((folder / locale / "text" / name).read_bytes() == data, "文本視圖不同")
        for field in fields:
            path = folder / locale / "masks" / field["file"]
            mask = json.loads(path.read_bytes())
            old = json.loads((baseline_masks / field["file"]).read_bytes())
            text, filename = field_text(field, old, views)
            require((mask.get("candidate_id") or mask.get("message_id")) == field["id"], "來源鍵不同")
            require((mask["locale"], mask["face"], mask["family"]) == (locale, face, family) and
                    mask["font_sha256"] == HASHES["noto"], "字模語言或地區不同")
            require(mask["catalog_sha256"] == sha(views[filename]) and
                    mask["translation_sha256"] == sha(text.encode()), "譯文或目錄綁定不同")
            require(mask["bindings"] == {"source_binding_sha256": base.registry["source_binding_sha256"],
                    "fields_sha256": FIELD_SHA, "license_sha256": HASHES["license"],
                    "text": {name: sha(data) for name, data in views.items()}}, "完整來源綁定不同")
            evidence, audit = native_evidence(field), mask["measurement"]
            require(mask["native_evidence"] == evidence and audit["chosen"]["fits"] is True and
                    audit["chosen"]["font_px"] == mask["font_size"], "逐欄證據或字級不同")
            expected_audit = {k: v for k, v in audit_by_file[field["file"]].items()
                              if k not in ("id", "group", "file", "native_evidence")}
            require(audit == expected_audit, "字模與量測收據不同")
            visible = text.split("\\n", 1)[1] if field["group"] == "intro" else text
            visible = visible.replace("{", "").replace("}", "").replace("\n", "")
            require("".join(audit["line_texts"]) == visible, "文字遺失、重複或截斷")
            width, height = mask["width"], mask["height"]
            require(type(width) is int and type(height) is int and 0 < width <= 1280 and 0 < height <= 800, "字模尺寸不合法")
            safe = [v * 4 for v in rectangle(field["safe"])]
            require(audit["safe_scaled"] == safe and audit["position"] == [mask["x"], mask["y"]], "定位不同")
            if field["group"] in ("intro", "help"):
                require([mask["x"], mask["y"], mask["x"]+width, mask["y"]+height] == safe, "長文字模超出欄位")
                names = ("normal", "shadow", "highlight")
            else:
                require(safe[0] <= mask["x"] and mask["x"]+width+field["shadow_offset"] <= safe[2] and
                        safe[1] <= mask["y"] and mask["y"]+height+field["shadow_offset"] <= safe[3], "固定字模或陰影越界")
                names = ("alpha",)
            for name in names:
                raw = base64.b64decode(mask[name], validate=True)
                require(len(raw) == width * height, "Alpha長度不同")
                image = Image.frombytes("L", (width, height), raw)
                box = image.getbbox()
                layer = "normal" if name == "alpha" else name
                require((list(box) if box else None) == audit["layer_ink"].get(layer), "墨跡範圍不同")
                if layer == "normal":
                    require(box is not None, "缺少前景")
                    with Image.open(path.with_suffix(".png")) as preview:
                        require(preview.mode == "L" and preview.size == image.size and preview.tobytes() == raw, "預覽與字模不同")
            count += 1
    require(count == 256, "四語欄位不完整")
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("folder", "fields", "baseline-masks"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    require(Path("/.dockerenv").is_file(), "需Docker隔離檢查")
    print("CHECKED_DRAFT_FIXED_NOTO", check(a.folder, a.fields, a.baseline_masks), "fields")


if __name__ == "__main__":
    main()
