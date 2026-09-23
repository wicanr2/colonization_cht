#!/usr/bin/env python3
"""從固定原版收據與真 TSV 製作姓名提示的可丟棄 Ebitengine 預覽。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from prototype_overlay import cmap_coverage
from validate_translation_draft import read_catalog, validate_sources


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
KEY = "GAME.TXT:0x00000A7A"
SAFE = (100, 85, 219, 98)
BBOX = (104, 88, 215, 97)
SIZE = 38
INK = (328, 35)
POSITION = (474, 352)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def section(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def prepare(args):
    p = args.reports
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(),
            "輸出目錄不存在或擁有者不符")
    source_a = (p / "a.json").read_bytes()
    require(source_a == (p / "b.json").read_bytes(), "兩次原版冷啟動不一致")
    report = json.loads(source_a)
    control = json.loads((p / "control.json").read_bytes())
    require(report["version"] == control["version"] == "goal094-prompt-v1" and
            report["input_sha256"] == INPUT_SHA and control["input_sha256"] == INPUT_SHA and
            len(report["writes"]) == 415 and len(report["reads"]) == 45 and
            not control["writes"] and not control["reads"] and
            report["samples"] == control["samples"] and
            report["opened"] == control["opened"], "原版探針／無觀測控制不符")
    for name in report["samples"]:
        for extension in ("idx", "canvas", "pal"):
            require((p / f"a.{name}.{extension}").read_bytes() ==
                    (p / f"control.{name}.{extension}").read_bytes(),
                    "原版索引／畫布／色盤與控制不符：" + name)
    before = (p / "a.before.canvas").read_bytes()
    after = (p / "a.after.canvas").read_bytes()
    stable = (p / "a.55m.idx").read_bytes()
    palette = (p / "a.55m.pal").read_bytes()
    require(len(before) == len(after) == len(stable) == 64000 and
            len(palette) == 768 and max(palette) <= 63, "原版畫布或色盤尺寸不符")
    changed = [(i % 320, i // 320) for i, (x, y) in enumerate(zip(before, after)) if x != y]
    require(len(changed) == 415 and
            (min(x for x, _ in changed), min(y for _, y in changed),
             max(x for x, _ in changed) + 1, max(y for _, y in changed) + 1) == BBOX and
            all(SAFE[0] <= x < SAFE[2] and SAFE[1] <= y < SAFE[3]
                for x, y in changed) and
            all(w["cs_ip"] == "0D21:012C" and
                before[w["y"] * 320 + w["x"]] == w["old"] and
                after[w["y"] * 320 + w["x"]] == w["new"]
                for w in report["writes"]), "提示印字事件或安全矩形不符")
    require(section(after, SAFE) == section(stable, SAFE),
            "印字後安全區與穩定畫面不符")
    require(section(after, (SAFE[0], 98, SAFE[2], 99)) !=
            section(stable, (SAFE[0], 98, SAFE[2], 99)),
            "姓名欄上緣的晚期重繪負例不存在，應重新審查安全區")
    game = (args.game / "GAME.TXT").read_bytes()
    require(sha(game) == GAME_SHA, "原版 GAME.TXT 指紋不符")
    rows = read_catalog(args.catalog)
    validate_sources(rows, args.game)
    matches = [row for row in rows if row["candidate_id"] == KEY]
    require(len(matches) == 1 and matches[0]["source_file"] == "GAME.TXT" and
            matches[0]["source_sha256"] == GAME_SHA and
            int(matches[0]["byte_offset"], 0) == 0xA7A and
            int(matches[0]["source_byte_length"]) == 25 and
            sha(game[0xA7A:0xA7A + 25]) == matches[0]["source_bytes_sha256"] and
            game[0xA7A:0xA7A + 25] == b"^^Please Enter Your Name." and
            matches[0]["status"] == "draft", "真 TSV 與原始提示行不符")
    translation = matches[0]["zh_hant"]
    require(translation.startswith("^^") and len(translation) > 2 and
            "^" not in translation[2:], "譯文控制碼或可見段不符")
    display = translation[2:]
    font_bytes = args.font.read_bytes()
    require(sha(font_bytes) == FONT_SHA, "Cubic 11 字型指紋不符")
    require(all(ord(char) in cmap_coverage(font_bytes) for char in display), "譯文字型缺字")
    font = ImageFont.truetype(str(args.font), SIZE)
    left, top, right, bottom = font.getbbox(display)
    width, height = right - left, bottom - top
    require((width, height) == INK and
            POSITION[0] == (BBOX[0] + BBOX[2]) * 2 - width // 2 and
            POSITION[1] == BBOX[1] * 4 and
            SAFE[0] * 4 + 4 <= POSITION[0] and
            POSITION[0] + width + 4 <= SAFE[2] * 4 - 4 and
            SAFE[1] * 4 + 4 <= POSITION[1] and
            POSITION[1] + height <= SAFE[3] * 4 - 4,
            "候選字級、共同中心線或四邊內距不符")
    mask = Image.new("L", (width, height))
    ImageDraw.Draw(mask).text((-left, -top), display, font=font, fill=255)
    layer = {"name": "player-name-prompt", "safe": SAFE,
             "ink_width": width, "ink_height": height, "position": POSITION,
             "background": base64.b64encode(section(before, SAFE)).decode(),
             "mask": base64.b64encode(mask.tobytes()).decode(),
             "color_index": 68, "shadow_index": 47, "shadow_dx": 4}
    same_prompt = section(stable, SAFE)
    for scene, sample in (("idle", "55m"), ("letter", "57m"), ("backspace", "65m")):
        old_report = json.loads((args.prior / f"{scene}-a.json").read_bytes())
        indexed = (args.prior / f"{scene}-a.{sample}.idx").read_bytes()
        scene_palette = (args.prior / f"{scene}-a.{sample}.pal").read_bytes()
        require(old_report["version"] == "goal093-name-v1" and
                old_report["input_sha256"] == INPUT_SHA and
                sha(indexed) == old_report["samples"][sample]["indexed_sha256"] and
                sha(scene_palette) == old_report["samples"][sample]["palette_sha256"] and
                scene_palette == palette and section(indexed, SAFE) == same_prompt,
                "編輯情境的提示安全區與原版不符：" + scene)
        payload = {"prototype": True, "layers": [layer],
                   "source_receipt_sha256": sha(source_a), "catalog_sha256": sha(args.catalog.read_bytes()),
                   "font_sha256": FONT_SHA, "scenario": scene, "sample": sample,
                   "indexed": base64.b64encode(indexed).decode(),
                   "palette": base64.b64encode(palette).decode()}
        (args.output / f"{scene}.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")
    receipt = {"scope": "本機可丟棄原型，非正式中文覆蓋", "source_receipt_sha256": sha(source_a),
               "font_sha256": FONT_SHA, "catalog_sha256": sha(args.catalog.read_bytes()),
               "source_key": KEY, "translation_sha256": sha(translation.encode()),
               "original_ink_bbox": BBOX, "original_ink_height_scaled": 36,
               "original_changed_pixels": len(changed), "background_palette_indices": len(set(section(before, SAFE))),
               "safe": SAFE, "font_size": SIZE, "ink_size": INK, "position": POSITION,
               "color_index": 68, "shadow_index": 47, "shadow_dx": 4,
               "scenarios": ["idle", "letter", "backspace"]}
    (args.output / "measurements.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())
