#!/usr/bin/env python3
"""由固定原版收據建立第一張旗卡兩欄的本機 Ebitengine 可丟棄預覽。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate_nation_card_fragments import validate


FIELDS = (
    ("upper", "NAMES.TXT:0x000008EA", (125, 12, 190, 24),
     (141, 15, 170, 19), 123, 21, (92, 19), "before-upper", "after-upper"),
    ("lower", "LABELS.TXT:0x000008F2", (125, 83, 190, 96),
     (135, 87, 177, 92), 156, 25, (54, 23), "before-lower", "after-lower"),
)
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def prepare(args):
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "本機輸出目錄不存在或擁有者不符")
    rows = {row["candidate_id"]: row for row in validate(args.catalog, args.game, args.font)}
    a_bytes = (args.reports / "goal088-a.json").read_bytes()
    b_bytes = (args.reports / "goal088-b.json").read_bytes()
    control_bytes = (args.reports / "goal088-control.json").read_bytes()
    require(a_bytes == b_bytes, "兩次獨立冷啟動收據不一致")
    a, control = json.loads(a_bytes), json.loads(control_bytes)
    require(a["version"] == control["version"] == "goal088-nation-background-v1"
            and not a["control"] and control["control"]
            and a["input_sha256"] == control["input_sha256"] == INPUT_SHA
            and a["input_hashes"] == control["input_hashes"]
            and a["state"] == control["state"]
            and a["opened"] == control["opened"]
            and a["write_counts"] == {"upper": 144, "lower": 172}
            and control["write_counts"] == {"upper": 0, "lower": 0},
            "原版旗卡印字事件或同輸入對照不符")
    previous = args.reports.parent / "goal085-nation-card"
    old = json.loads((previous / "goal085-a.json").read_bytes())
    require(old["version"] == "goal085-nation-card-probe-v1"
            and old["input_sha256"] == INPUT_SHA
            and not old["write_truncated"] and not old["read_truncated"],
            "前一輪原版畫布收據不符")
    indexed = (args.reports / "goal088-a.settled.idx").read_bytes()
    palette = (args.reports / "goal088-a.final.pal").read_bytes()
    require(len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63
            and sha(indexed) == a["state"]["indexed_sha256"]
            and sha(palette) == a["state"]["palette_sha256"]
            and indexed == (previous / "goal085-a.settled-43m.idx").read_bytes(),
            "原版最終畫面或色盤不符")
    require(palette[12 * 3:12 * 3 + 3] == bytes((61, 0, 0))
            and palette[:3] == b"\0\0\0", "原版紅字／陰影色盤不符")
    require((args.reports / "goal088-a.after-lower.canvas").read_bytes()
            == (args.reports / "goal088-a.settled.canvas").read_bytes(),
            "兩欄印字後畫布尚未穩定")
    layers = []
    for name, key, safe, bbox, pixels, size, ink, before_name, after_name in FIELDS:
        before = (args.reports / f"goal088-a.{before_name}.canvas").read_bytes()
        after = (args.reports / f"goal088-a.{after_name}.canvas").read_bytes()
        require(len(before) == len(after) == 64000, "原版畫布大小不符")
        require(all(rect_bytes(before, safe) == rect_bytes(
                    (args.reports / f"goal088-{variant}.{before_name}.canvas").read_bytes(), safe)
                    and rect_bytes(after, safe) == rect_bytes(
                    (args.reports / f"goal088-{variant}.{after_name}.canvas").read_bytes(), safe)
                    for variant in ("b", "control")), "兩次與對照組底圖不同：" + name)
        changed = [(i % 320, i // 320) for i, (left, right) in enumerate(zip(before, after))
                   if left != right]
        require(len(changed) == pixels and
                (min(x for x, _ in changed), min(y for _, y in changed),
                 max(x for x, _ in changed), max(y for _, y in changed)) == bbox and
                all(safe[0] <= x < safe[2] and safe[1] <= y < safe[3] for x, y in changed),
                "原版文字差分點數／bbox／安全區不符：" + name)
        require(rect_bytes(after, safe) == rect_bytes(indexed, safe),
                "原版最終畫面沒有保留當次印字：" + name)
        background_colors = len(set(rect_bytes(before, safe)))
        require(background_colors >= 50, "底圖不是已量測的多色紋理：" + name)
        site = old["write_sites"][name + "/0D21:012C"]
        require(site["count"] == a["write_counts"][name]
                and (site["min_x"], site["min_y"], site["max_x"], site["max_y"]) == bbox,
                "前一輪原版寫入者與當次差分不符：" + name)
        translated = rows[key]["zh_hant"] + ("：" if name == "upper" else "")
        if args.variant == "readable":
            size, ink = ((25, (108, 23)) if name == "upper" else (29, (62, 27)))
        font = ImageFont.truetype(str(args.font), size)
        left, top, right, bottom = font.getbbox(translated)
        width, height = right - left, bottom - top
        max_height_delta = 1 if args.variant == "faithful" else 4
        require((width, height) == ink and
                abs(height - (bbox[3] - bbox[1] + 1) * 4) <= max_height_delta,
                "逐欄候選字級未對齊原版墨跡：" + name)
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-left, -top), translated, font=font, fill=255)
        x, y = 624 - width // 2, bbox[1] * 4
        require(safe[0] * 4 + 4 <= x and x + width + 4 <= safe[2] * 4 - 4
                and safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4,
                "中文或原版式一像素陰影超出安全內距：" + name)
        layers.append({"name": name, "candidate_id": key, "safe": safe,
                       "original_ink_bbox": bbox, "original_ink_height_scaled":
                       (bbox[3] - bbox[1] + 1) * 4,
                       "original_changed_pixels": pixels,
                       "background_palette_indices": background_colors,
                       "font_size": size, "ink_width": width, "ink_height": height,
                       "position": [x, y], "color_index": 12, "shadow_index": 0,
                       "shadow_dx": 4, "translation_sha256": sha(translated.encode()),
                       "background": base64.b64encode(rect_bytes(before, safe)).decode(),
                       "mask": base64.b64encode(mask.tobytes()).decode()})
    payload = {"prototype": True, "variant": args.variant,
               "source_receipt_sha256": sha(a_bytes),
               "control_receipt_sha256": sha(control_bytes),
               "previous_canvas_receipt_sha256": sha((previous / "goal085-a.json").read_bytes()),
               "catalog_sha256": sha(args.catalog.read_bytes()),
               "font_sha256": sha(args.font.read_bytes()),
               "indexed": base64.b64encode(indexed).decode(),
               "palette": base64.b64encode(palette).decode(), "layers": layers}
    args.output.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"prototype": True, "variant": args.variant,
                      "layers": [{k: v for k, v in layer.items() if k not in ("background", "mask")}
                                 for layer in layers]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("faithful", "readable"), default="faithful")
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
