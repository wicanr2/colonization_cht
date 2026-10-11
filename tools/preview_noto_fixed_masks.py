#!/usr/bin/env python3
"""規格060 DRAFT：逐欄量測四語64份固定字模；不連結正式前端。"""

import argparse
import base64
import csv
import io
import json
import os
import platform
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, __version__ as pillow_version, features

from check_language_font_coverage import FACES, LOCALES, font_charset
from language_catalog import BaseCatalog, ROOT, canonical, load_translation, make_views, new_output, require, sha
from prepare_goal113_options_preview import FIELDS as OPTION_FIELDS
from preview_goal102_nation_intro import marked_chars, wrap
from render_language_font_sample import HASHES

FIELD_SHA = "2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d"
EVIDENCE = {
    "tools/live_menu.go": "2f5ab4b81a9608a14f05280cfaba5027472e648fda6e34d3db4ba8855d0a0a53",
    "tools/prepare_goal113_options_preview.py": "680a5254cf3c33e1298eff43a7e9a769bad70f5d8fe93a54767dd7157e1800b3",
    "docs/spec/025-first-nation-introduction-draft.md": "8e734410c358828ac003458bd4dc748fe5cc62d6269be1f16d00518117785512",
    "docs/spec/034-static-text-overlay-draft.md": "bc68bb2b8d723cbf652f81bbc7de611b8568a2f7faf6ec8114960657ca30e9f8",
    "tools/preview_goal142_help.py": "1279bc1db7e9323f7806681be3a3f028324d54a5e533ffb21cc9cc4678591b8a",
}


def rectangle(value):
    return [value["Min"]["X"], value["Min"]["Y"], value["Max"]["X"], value["Max"]["Y"]]


def table_rows(views, name):
    return list(csv.DictReader(io.StringIO(views[name].decode()), delimiter="\t", strict=True))


def field_text(field, old, views):
    """與正式載入器相同的TSV鍵、變數及控制碼處理；不複製顯示文案。"""
    key, group = field["id"], field["group"]
    if group in ("intro", "help", "static"):
        filename, column, display = {
            "intro": ("nation-introduction.zh-Hant.tsv", "message_id", "zh_hant_draft"),
            "help": ("help-bilingual.tsv", "message_id", "zh_hant"),
            "static": ("static-overlay.zh-Hant.tsv", "candidate_id", "zh_hant"),
        }[group]
    else:
        filename = "nation-card-fragments.zh-Hant.tsv" if group in ("card", "cards-rest") else "draft.zh-Hant.tsv"
        column, display = "candidate_id", "zh_hant"
    index = {row[column]: row for row in table_rows(views, filename)}
    keys = old.get("keys", [key])
    require(all(k in index for k in keys), "欄位缺少TSV來源：" + key)
    parts = [index[k][display].removeprefix("^^").replace("~", "") for k in keys]
    if group == "captions":
        values = [r for r in table_rows(views, "build-caption-values.zh-Hant.tsv")
                  if r["nation"] == "england" and r["caption"] == old["caption"]]
        for row in values:
            parts = [part.replace(row["placeholder"], row["zh_hant"]) for part in parts]
    text = "\n".join(parts)
    if group in ("card", "cards-rest") and key.startswith("NAMES.TXT:"):
        text += "："
    if group == "help":
        terms = [r["zh"] for r in table_rows(views, "terms.zh-Hant.tsv")
                 if r["en"] == "Caravel" and r["category"] == "ship"]
        require(len(terms) == 1, "教學術語缺件")
        text = text.replace("%STRING0", terms[0])
    require("%STRING" not in text and "^^" not in text and "~" not in text, "控制碼未展開：" + key)
    return text, filename


def native_evidence(field):
    group, key = field["group"], field["id"]
    box = rectangle(field["native_ink"])
    source = "tools/live_menu.go"
    if group == "option-rows":
        row = next(r for r in OPTION_FIELDS if key == f"GAME.TXT:0x{r[0]:08X}")
        box, source = list(row[2]), "tools/prepare_goal113_options_preview.py"
    if group == "intro":
        return {"title_height": 8, "body_height": 9, "line_advance": 10,
                "source": "docs/spec/025-first-nation-introduction-draft.md", "level": "confirmed"}
    if group == "help":
        return {"body_height": 7, "line_advance": 10, "source": "tools/preview_goal142_help.py", "level": "confirmed"}
    if group == "static":
        return {"body_height": 7 if key.startswith("OPENING.TXT:") else 5,
                "source": "docs/spec/034-static-text-overlay-draft.md", "level": "confirmed"}
    require(box[3] > box[1], "缺少原文逐欄墨跡：" + key)
    lines = 2 if group == "retire" and key.endswith("00000122") else 1
    if group == "captions":
        # BUILD2原版兩行，9列字高、10列行距；不是把19列合併當字高。
        lines = 2 if key.endswith("0001542B") else 1
    height = box[3] - box[1] - (10 if lines == 2 else 0)
    return {"ink_bbox": box, "body_height": height, "line_count": lines,
            "line_advance": 10, "source": source, "level": "confirmed",
            "qualification": "bbox為原版改色聯集；含陰影時不推定前景獨立高度"}


def line_plan(text, font, width, max_lines, advance):
    """保留全部字元及強調片段；候選不合格時回原文。"""
    rows, bad = [], []
    for paragraph in text.split("\n"):
        chars = marked_chars(paragraph)
        if max_lines == 1:
            rows.append(chars)
        else:
            lines, _, invalid = wrap(chars, font, width)
            rows.extend(lines)
            bad.extend(invalid)
    boxes = [font.getbbox("".join(c for c, _ in row), anchor="ls") for row in rows]
    require(rows and all(row for row in rows), "空白行不屬於固定欄位契約")
    left = min(box[0] for box in boxes)
    top = min(box[1] + i * advance for i, box in enumerate(boxes))
    right = max(box[2] for box in boxes)
    bottom = max(box[3] + i * advance for i, box in enumerate(boxes))
    return {"rows": rows, "boxes": boxes, "bounds": [left, top, right, bottom],
            "advance": advance, "bad_breaks": bad, "fits_lines": len(rows) <= max_lines}


def paint(plan, font, size, offset, shadow):
    layers = {key: Image.new("L", size) for key in ("normal", "highlight", "shadow")}
    # 使用有餘白的驗證畫布，先畫後量，不能由裁切後的bbox宣稱不越界。
    pad = 128
    scratch = {key: Image.new("L", (size[0] + 2 * pad, size[1] + 2 * pad)) for key in layers}
    draws = {key: ImageDraw.Draw(im) for key, im in scratch.items()}
    x, y = offset
    for i, row in enumerate(plan["rows"]):
        value = "".join(c for c, _ in row)
        baseline = y + i * plan["advance"]
        draws["normal"].text((x + pad, baseline + pad), value, font=font, anchor="ls", fill=255)
        if shadow:
            draws["shadow"].text((x + pad + shadow, baseline + pad + shadow), value, font=font, anchor="ls", fill=255)
        start = 0
        while start < len(row):
            if not row[start][1]:
                start += 1
                continue
            end = start + 1
            while end < len(row) and row[end][1]:
                end += 1
            prefix = "".join(c for c, _ in row[:start])
            segment = "".join(c for c, _ in row[start:end])
            draws["highlight"].text((x + pad + round(font.getlength(prefix)), baseline + pad),
                                    segment, font=font, anchor="ls", fill=255)
            start = end
    bounds = {}
    for key, im in scratch.items():
        box = im.getbbox()
        if box:
            require(pad <= box[0] < box[2] <= pad + size[0] and
                    pad <= box[1] < box[3] <= pad + size[1], "實際墨跡越界：" + key)
            bounds[key] = [box[0] - pad, box[1] - pad, box[2] - pad, box[3] - pad]
        layers[key] = im.crop((pad, pad, pad + size[0], pad + size[1]))
    require(layers["normal"].getbbox() is not None, "沒有前景墨跡")
    return layers, bounds


def measure(field, text, evidence, font_path, face):
    safe = [v * 4 for v in rectangle(field["safe"])]
    width, height = safe[2] - safe[0], safe[3] - safe[1]
    group, key = field["group"], field["id"]
    shadow = field["shadow_offset"]
    multiline = group in ("intro", "help")
    target = evidence["body_height"] * 4
    # 候選範圍依原版字高，不沿用既有Cubic欄位字級。
    candidates, valid = [], []
    for pixels in range(max(12, target * 2 // 3), target + 13):
        font = ImageFont.truetype(str(font_path), pixels, index=face)
        if multiline:
            title, body = text.split("\\n", 1) if group == "intro" else (None, text)
            margin = 16 if group == "intro" else 4
            limit = width - margin * 2 - shadow - 4
            advance = max(evidence["line_advance"] * 4, pixels + 6)
            plan = line_plan(body, font, limit, 64, advance)
            box = plan["bounds"]
            body_height = box[3] - box[1]
            title_font, title_plan, title_px, title_height = None, None, None, 0
            gap = 48 if title is not None else 0
            if title is not None:
                title_target = evidence["title_height"] * 4
                title_choices = []
                for px in range(max(12, title_target * 2 // 3), title_target + 13):
                    tf = ImageFont.truetype(str(font_path), px, index=face)
                    tp = line_plan(title, tf, limit, 1, 0)
                    tb = tp["bounds"]
                    if tb[2] - tb[0] <= limit and tb[3] - tb[1] <= title_target:
                        title_choices.append((abs(tb[3] - tb[1] - title_target), -px, tf, tp))
                require(title_choices, "標題沒有相稱字級")
                _, negative, title_font, title_plan = min(title_choices, key=lambda x: x[:2])
                title_px = -negative
                title_height = title_plan["bounds"][3] - title_plan["bounds"][1]
            total = title_height + gap + body_height + shadow
            fits = box[2] - box[0] <= limit and total <= height - 16 and not plan["bad_breaks"]
            detail = {"font_px": pixels, "title_font_px": title_px, "body_ink_height": max(b[3]-b[1] for b in plan["boxes"]),
                      "line_count": len(plan["rows"]), "line_advance": advance, "total_height": total, "fits": fits}
            if fits:
                top = (height - total) // 2
                layers, bounds = paint(plan, font, (width, height),
                                       (margin - box[0], top + title_height + gap - box[1]), shadow)
                if title is not None:
                    tb = title_plan["bounds"]
                    tl, _ = paint(title_plan, title_font, (width, height),
                                  ((width - (tb[2]-tb[0])) // 2 - tb[0], top - tb[1]), shadow)
                    for name in layers:
                        # 同一層的標題與正文不相交，不用alpha加總造成溢位。
                        layers[name] = ImageChops.lighter(layers[name], tl[name])
                    bounds = {name: list(im.getbbox()) for name, im in layers.items() if im.getbbox()}
                pos = safe[:2]
        else:
            left = group in ("option-rows", "options-title") or key.endswith("0000086E") or \
                (group == "menu" and field["cubic_font_size"] == 0)
            if group == "static":
                max_width, max_height, y = width - 8, height - 4, None
                center = (safe[0] + safe[2]) / 2
            else:
                x0, y = field["position"]["X"], field["position"]["Y"]
                center = x0 + field["cubic_mask_size"]["X"] / 2
                max_width = safe[2] - 4 - shadow - x0 if left else 2 * min(center-safe[0]-4, safe[2]-4-shadow-center)
                max_height = safe[3] - 4 - shadow - y
            lines = evidence.get("line_count", 1)
            plan = line_plan(text, font, max_width, lines, evidence["line_advance"] * 4 if lines > 1 else 0)
            box = plan["bounds"]
            ink_w, ink_h = box[2]-box[0], box[3]-box[1]
            fits = ink_w <= max_width and ink_h <= max_height and plan["fits_lines"] and not plan["bad_breaks"]
            detail = {"font_px": pixels, "ink": [ink_w, ink_h], "fits": fits, "line_count": len(plan["rows"])}
            if fits:
                pos = [field["position"]["X"] if left else round(center-ink_w/2),
                       round((safe[1]+safe[3]-ink_h)/2) if y is None else y]
                # 固定字模只含前景；正式繪製器依原版色號另畫陰影。
                layers, bounds = paint(plan, font, (ink_w, ink_h), (-box[0], -box[1]), 0)
                require(safe[0] <= pos[0] and pos[0]+ink_w+shadow <= safe[2] and
                        safe[1] <= pos[1] and pos[1]+ink_h+shadow <= safe[3], "候選位置越界")
                detail["baseline"] = -box[1]
        candidates.append(detail)
        if fits:
            visible_height = detail.get("body_ink_height", max(b[3]-b[1] for b in plan["boxes"]))
            valid.append((abs(visible_height-target), -pixels, detail, layers, bounds, pos, plan))
    require(valid, "欄位沒有合格候選，維持原文：" + key)
    _, _, chosen, layers, bounds, pos, plan = min(valid, key=lambda item: item[:2])
    return {"chosen": chosen, "candidates": candidates, "position": pos, "safe_scaled": safe,
            "layer_ink": bounds, "line_texts": ["".join(c for c, _ in row) for row in plan["rows"]],
            "alignment": "原版欄位頂端／既有中心；靜態及長文垂直置中",
            "overflow_policy": "回原文並記錄；不裁切、不截斷"}, layers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("fields", "baseline-masks", "noto", "license", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file() and platform.python_version().startswith("3.11.") and
            pillow_version == "9.4.0" and features.version("freetype2") == "2.12.1", "需固定Docker量測工具鏈")
    for name in ("noto", "license"):
        require(sha(getattr(args, name).read_bytes()) == HASHES[name], "字型或授權指紋不同")
    for name, digest in EVIDENCE.items():
        require(sha((ROOT / name).read_bytes()) == digest, "欄位證據不同：" + name)
    require(sha(args.fields.read_bytes()) == FIELD_SHA, "逐欄匯出收據不同")
    fields = json.loads(args.fields.read_bytes())["fields"]
    require(len(fields) == 64 and len({f["file"] for f in fields}) == 64, "固定欄位數目或鍵不同")
    base = BaseCatalog()
    products, report = {}, {"kind": "DRAFT-four-locale-fixed-masks-not-runtime-bundle",
        "source_binding_sha256": base.registry["source_binding_sha256"], "fields_sha256": FIELD_SHA,
        "font_sha256": HASHES["noto"], "license_sha256": HASHES["license"], "evidence_sha256": EVIDENCE,
        "tool": {"python": platform.python_version(), "pillow": pillow_version, "freetype": features.version("freetype2")},
        "limitations": ["尚未連結正式載入器、切換快取或正常GUI；量測通過不等於玩家路徑驗收。"], "locales": {}}
    for locale in LOCALES:
        entries = base.entries
        if locale != "zh-Hant":
            entries, missing = load_translation(base, (ROOT / f"text/game.{locale}.tsv").read_bytes(), locale)
            require(not missing, "四語固定字模不可缺譯")
        views = make_views(base, entries, locale)
        face, family = FACES[locale]
        charset, _ = font_charset(args.noto, face, family)
        measured, masks = [], {}
        for field in fields:
            old = json.loads((args.baseline_masks / field["file"]).read_bytes())
            text, filename = field_text(field, old, views)
            if locale == "zh-Hant":
                require(text == field["text"] and sha(text.encode()) == old["translation_sha256"], "TSV解析與正式前端不符：" + field["id"])
            require(all(ord(ch) in charset for ch in text if ord(ch) >= 32), "固定欄位缺字：" + field["id"])
            evidence = native_evidence(field)
            audit, layers = measure(field, text, evidence, args.noto, face)
            obj = {k: old[k] for k in ("candidate_id", "message_id", "section_sha256", "caption", "keys", "ink_index") if k in old}
            obj.update({"font_sha256": HASHES["noto"], "locale": locale, "face": face, "family": family,
                "catalog_sha256": sha(views[filename]), "translation_sha256": sha(text.encode()),
                "width": layers["normal"].width, "height": layers["normal"].height,
                "x": audit["position"][0], "y": audit["position"][1], "font_size": audit["chosen"]["font_px"],
                "scope": "DRAFT；只留workplace，未授權正式載入", "measurement": audit, "native_evidence": evidence,
                "bindings": {"source_binding_sha256": base.registry["source_binding_sha256"], "fields_sha256": FIELD_SHA,
                             "license_sha256": HASHES["license"], "text": {name: sha(data) for name, data in views.items()}}})
            if field["group"] in ("intro", "help"):
                obj.update({name: base64.b64encode(im.tobytes()).decode() for name, im in layers.items()})
                obj["body_font_px"] = obj["font_size"]
                if field["group"] == "intro":
                    obj["title_font_px"] = audit["chosen"]["title_font_px"]
                    obj["panel"] = audit["safe_scaled"]
            else:
                obj["alpha"] = base64.b64encode(layers["normal"].tobytes()).decode()
            masks[field["file"]] = obj, layers
            measured.append({"id": field["id"], "group": field["group"], "file": field["file"],
                             "native_evidence": evidence, **audit})
        products[locale] = views, masks
        report["locales"][locale] = {"face": face, "family": family, "fields": measured}
        print(locale, len(masks), "fields measured", flush=True)
    output = new_output(args.output, directory=True)
    for locale, (views, masks) in products.items():
        folder = output / locale
        (folder / "text").mkdir(parents=True)
        for name, data in views.items():
            (folder / "text" / name).write_bytes(data)
        for name, (obj, layers) in masks.items():
            path = folder / "masks" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical(obj) + b"\n")
            layers["normal"].save(path.with_suffix(".png"))
    report["outputs_sha256"] = {str(p.relative_to(output)): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "check.json").write_bytes(canonical(report) + b"\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in output.rglob("*")), "輸出擁有權不同")
    print("MEASURED_DRAFT_FIXED_NOTO", sha((output / "check.json").read_bytes()))


if __name__ == "__main__":
    main()
