#!/usr/bin/env python3
"""沿規格035已驗命令清單量測四語Noto候選；只產生私用排版原型。"""

import argparse
import json
import os
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version, features

from check_language_font_coverage import FACES, LOCALES
from language_catalog import BaseCatalog, ROOT, load_translation, require, sha
from render_language_font_sample import HASHES


MEASUREMENT_SHA = "35cecc614308c691b82b817b12e4717486986a5a39b95adf67714a1c743870e9"
REVIEW_SHA = "dc0a9b0ae43c8953d2e8845066e682e20df735b07ba460f2482eb9ef04ef32f8"


def visible_menu_text(text):
    text = text.strip()
    # 沿既有六列譯稿的首字快捷鍵顯示方式；其餘波浪號只標示熱鍵色。
    text = re.sub(r"^~([A-Za-z])", r"(\1)", text)
    return re.sub(r"~(.)", r"\1", text)


def plan(font_path, face, text_rows, measurement):
    safe = measurement["safe"]
    width, height = (safe[2] - safe[0]) * 4, (safe[3] - safe[1]) * 4
    tops = [(y - safe[1]) * 4 for y in measurement["row_tops"]]
    original_ink_height = measurement["original_cap"] * 4
    candidates = []
    for pixels in range(measurement["candidate_range"][0], measurement["candidate_range"][1] - 1, -1):
        font = ImageFont.truetype(str(font_path), pixels, index=face)
        rows, valid = [], True
        for index, (key, text) in enumerate(text_rows):
            box = font.getbbox(text, anchor="ls")
            advance = float(font.getlength(text))
            origin = [4 - box[0], tops[index] - box[1]]
            ink = [4, tops[index], 4 + box[2] - box[0], tops[index] + box[3] - box[1]]
            bottom_limit = tops[index + 1] if index + 1 < len(tops) else height - 4
            fits = ink[2] <= width - 4 and ink[3] <= bottom_limit and advance <= width - 8
            valid = valid and fits
            rows.append({"key": key, "text": text, "advance": advance, "origin_baseline": origin,
                         "ink": ink, "bottom_limit": bottom_limit, "fits": fits})
        max_ink_height = max(row["ink"][3] - row["ink"][1] for row in rows)
        candidates.append({"font_px": pixels, "fits": valid, "max_ink_height": max_ink_height,
                           "distance_from_original_ink": abs(max_ink_height - original_ink_height), "rows": rows})
    fitting = [candidate for candidate in candidates if candidate["fits"]]
    require(fitting, "六列最長譯文無可容納字級；原型不得截斷或擅自換行")
    chosen = min(fitting, key=lambda candidate: (candidate["distance_from_original_ink"], -candidate["font_px"]))
    return {"safe_size": [width, height], "original_cap_scaled": original_ink_height,
            "padding_left_right": 4, "candidates": candidates, "chosen": chosen,
            "longest_key": max(chosen["rows"], key=lambda row: row["advance"])["key"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurement", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--noto", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file() and pillow_version == "9.4.0", "需Docker內Pillow9.4.0候選工具鏈")
    for path, expected in ((args.measurement, MEASUREMENT_SHA), (args.review, REVIEW_SHA),
                           (args.noto, HASHES["noto"]), (args.license, HASHES["license"])):
        require(path.is_file() and sha(path.read_bytes()) == expected, "量測、審查、字型或授權指紋不符")
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
            output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
            "輸出須為新的workplace目錄")
    measurement = json.loads(args.measurement.read_text())
    review = json.loads(args.review.read_text())
    require(measurement["result"] == "PASS_ACTUAL_COMPACT_ORDERS_LAYOUT" and
            review["status"] == "PASS_COMPACT_ORDERS_FORMAL", "缺少既有原版欄位驗證")
    keys = measurement["source_keys"]
    require(len(keys) == 6 and measurement["safe"] == review["verified_fields"][0]["safe"],
            "來源鍵或安全區不同")
    base = BaseCatalog()
    views, bindings = {}, {}
    for locale in LOCALES:
        entries = base.entries
        if locale != "zh-Hant":
            data = (ROOT / f"text/game.{locale}.tsv").read_bytes()
            entries, missing = load_translation(base, data, locale)
            require(not missing, "不接受部分譯稿")
            bindings[locale] = sha(data)
        text_rows = [(key, visible_menu_text(entries["draft", key]["text"])) for key in keys]
        if locale == "zh-Hant":
            require([text for _, text in text_rows] ==
                    [text.replace("{", "").replace("}", "") for text in measurement["items"]],
                    "既有熱鍵顯示結構不符")
        face, family = FACES[locale]
        require(ImageFont.truetype(str(args.noto), 22, index=face).getname()[0] == family, "區域字型不符")
        views[locale] = {"face_index": face, "family": family,
                         **plan(args.noto, face, text_rows, measurement)}
    image = Image.new("RGB", (720, 680), "#f2ecdf")
    draw = ImageDraw.Draw(image)
    heading = ImageFont.truetype(str(args.noto), 22, index=3)
    for index, locale in enumerate(LOCALES):
        x, y = 24 + (index % 2) * 360, 54 + (index // 2) * 320
        result = views[locale]
        draw.text((x, y - 34), f"{locale}  Noto {result['chosen']['font_px']}px", font=heading, fill="#272d2c")
        pane = Image.new("RGB", tuple(result["safe_size"]), "#161d27")
        pd = ImageDraw.Draw(pane)
        font = ImageFont.truetype(str(args.noto), result["chosen"]["font_px"], index=result["face_index"])
        for row in result["chosen"]["rows"]:
            pd.text(tuple(row["origin_baseline"]), row["text"], font=font, anchor="ls", fill="#eee4cc")
        pd.rectangle((0, 0, pane.width - 1, pane.height - 1), outline="#688078")
        image.paste(pane, (x, y))
    output.mkdir()
    image_path = output / "compact-orders-noto.png"
    image.save(image_path)
    report = {"kind": "private-field-layout-prototype-not-normal-gui",
              "source_binding_sha256": base.registry["source_binding_sha256"],
              "measurement_sha256": MEASUREMENT_SHA, "review_sha256": REVIEW_SHA,
              "source_rows_sha256": {key: base.entries["draft", key]["base_sha256"] for key in keys},
              "catalog_sha256": bindings, "font_sha256": HASHES["noto"], "license_sha256": HASHES["license"],
              "pillow": pillow_version, "freetype": features.version_module("freetype2"),
              "script_sha256": sha(Path(__file__).read_bytes()), "image_sha256": sha(image_path.read_bytes()),
              "native_safe": measurement["safe"], "native_row_tops": measurement["row_tops"],
              "native_cap": measurement["original_cap"], "locales": views,
              "limits": [measurement["source_identity_limit"],
                         "Uses existing confirmed field geometry; no new original execution or GUI receipt.",
                         "Only this six-row field is measured; disabled colors, hotkey colors and interaction are not rendered.",
                         "No production size or atlas is changed; other fields need their own measurements."]}
    report_path = output / "layout.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    require(all(path.stat().st_uid == os.getuid() and path.stat().st_gid == os.getgid()
                for path in output.iterdir()), "輸出擁有權不符")
    print(json.dumps({"report": str(report_path), "sha256": sha(report_path.read_bytes()),
                      "locales": {locale: {"font_px": row["chosen"]["font_px"],
                                           "max_ink_height": row["chosen"]["max_ink_height"],
                                           "longest_key": row["longest_key"]} for locale, row in views.items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
