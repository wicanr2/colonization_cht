#!/usr/bin/env python3
"""用已驗 dosgolem 畫布建立姓名欄 A／B 可丟棄 Ebitengine 對照。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
NAME_SHA = "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
SAFE = (80, 100, 245, 111)
POSITION = (328, 404)
SIZE = 38
PLACEHOLDER = "中文譯名示意_"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def section(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def prepare(args):
    out = args.output
    need(out.is_dir() and out.stat().st_uid == os.getuid(), "輸出目錄不存在或擁有者不符")
    a_bytes = (args.reports / "idle-a.json").read_bytes()
    need(a_bytes == (args.reports / "idle-b.json").read_bytes(), "兩次冷啟動報告不同")
    record = json.loads(a_bytes)
    control = json.loads((args.reports / "idle-control.json").read_bytes())
    need(record["version"] == control["version"] == "goal097-name-field-v1" and
         record["input_sha256"] == control["input_sha256"] == INPUT_SHA and
         record["samples"] == control["samples"] and record["opened"] == control["opened"] and
         not control["reads"] and not control["writes"], "原版雙路收據不符")
    original_name = (args.game / "NAMES.TXT").read_bytes()
    need(sha(original_name) == NAME_SHA and
         original_name[0xB4B:0xB4B + 15] == b"Jacques Cartier", "原版姓名來源不符")
    before_ink = (args.reports / "idle-a.before_ink.canvas").read_bytes()
    after = (args.reports / "idle-a.after.canvas").read_bytes()
    indexed = (args.reports / "idle-a.55m.idx").read_bytes()
    palette = (args.reports / "idle-a.55m.pal").read_bytes()
    need(len(before_ink) == len(after) == len(indexed) == 64000 and
         len(palette) == 768 and max(palette) <= 63 and
         sha(indexed) == record["samples"]["55m"]["indexed_sha256"] and
         sha(palette) == record["samples"]["55m"]["palette_sha256"],
         "原版畫布／索引／色盤收據不符")
    changed = [(i % 320, i // 320) for i, (old, new) in enumerate(zip(before_ink, after))
               if old != new]
    need(len(changed) == 285 and
         (min(x for x, _ in changed), min(y for _, y in changed),
          max(x for x, _ in changed) + 1, max(y for _, y in changed) + 1) ==
         (82, 101, 164, 110) and
         all(SAFE[0] <= x < SAFE[2] and SAFE[1] <= y < SAFE[3] for x, y in changed) and
         section(after, SAFE) == section(indexed, SAFE),
         "姓名墨跡／安全區或穩定畫面不符")
    prompt = json.loads(args.prompt.read_bytes())
    need(prompt["prototype"] is True and len(prompt["layers"]) == 1 and
         prompt["layers"][0]["name"] == "player-name-prompt" and
         base64.b64decode(prompt["indexed"]) == indexed and
         base64.b64decode(prompt["palette"]) == palette,
         "已驗姓名提示圖層或同狀態畫布不符")
    font_bytes = args.font.read_bytes()
    need(sha(font_bytes) == FONT_SHA, "字型指紋不符")
    font = ImageFont.truetype(str(args.font), SIZE)
    left, top, right, bottom = font.getbbox(PLACEHOLDER)
    width, height = right - left, bottom - top
    need((width, height) == (268, 35) and
         SAFE[0] * 4 + 4 <= POSITION[0] and
         POSITION[0] + width + 4 <= SAFE[2] * 4 - 4 and
         SAFE[1] * 4 + 4 <= POSITION[1] and
         POSITION[1] + height <= SAFE[3] * 4 - 4,
         "姓名欄候選字級、位置或四邊內距不符")
    mask = Image.new("L", (width, height))
    ImageDraw.Draw(mask).text((-left, -top), PLACEHOLDER, font=font, fill=255)
    layer = {"name": "player-name-display-placeholder", "safe": SAFE,
             "ink_width": width, "ink_height": height, "position": POSITION,
             "background": base64.b64encode(section(before_ink, SAFE)).decode(),
             "mask": base64.b64encode(mask.tobytes()).decode(),
             "color_index": 68, "shadow_index": 47, "shadow_dx": 4}
    base = {"prototype": True, "indexed": prompt["indexed"],
            "palette": prompt["palette"]}
    for choice, layers in (("a", prompt["layers"]), ("b", prompt["layers"] + [layer])):
        (out / f"choice-{choice}.json").write_text(
            json.dumps({**base, "layers": layers}, ensure_ascii=False, indent=2) + "\n")
    formal = Image.open(args.formal_base).convert("RGB")
    need(formal.size == (1280, 800), "正式真視窗底圖尺寸不符")
    lut = [tuple((value << 2) | (value >> 4) for value in palette[i:i + 3])
           for i in range(0, len(palette), 3)]
    original_rgb = bytes(channel for index in indexed for channel in lut[index])
    original = Image.frombytes("RGB", (320, 200), original_rgb)
    original = original.resize((1280, 800), Image.Resampling.NEAREST)
    rect = (SAFE[0] * 4, SAFE[1] * 4, SAFE[2] * 4, SAFE[3] * 4)
    need(formal.crop(rect).tobytes() == original.crop(rect).tobytes(),
         "正式視窗的原名欄與同狀態 dosgolem 不同")
    (out / "choice-name-only.json").write_text(
        json.dumps({**base, "layers": [layer]}, ensure_ascii=False, indent=2) + "\n")
    metadata = {"status": "DISPOSABLE; no accepted name translation", "source": "NAMES.TXT:0xB4B",
                "source_sha256": NAME_SHA, "input_sha256": INPUT_SHA,
                "report_sha256": sha(a_bytes), "font_sha256": FONT_SHA,
                "placeholder": PLACEHOLDER, "placeholder_is_translation": False,
                "font_size": SIZE, "ink_size": [width, height], "safe": SAFE,
                "position": POSITION, "name_ink_bbox": [82, 101, 164, 110],
                "prompt_payload_sha256": sha(args.prompt.read_bytes()),
                "formal_base_sha256": sha(args.formal_base.read_bytes()),
                "rights": "local-only; original pixels and font must not enter Git"}
    (out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print("姓名欄 A／B 可丟棄圖層完成；中文名稱只是明示占位，不是譯稿")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--formal-base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
