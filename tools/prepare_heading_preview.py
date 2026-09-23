#!/usr/bin/env python3
"""從已核對的 dosgolem 收據產生可丟棄的難度標題 Ebitengine 預覽資料。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
PALETTE_SHA = "762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82"
SOURCE_SHA = "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204"
LINES = (
    ("choose", "選擇", (39, 14, 76, 26), (42, 16, 73, 24), "choose-before", "choose-after", 126),
    ("level", "難度", (20, 27, 96, 40), (23, 29, 92, 38), "level-before", "level-after", 284),
)
LAYOUTS = {"current": ((24, 24), "left"),
           "centered": ((34, 38), "center"),
           "left_scaled": ((34, 38), "left")}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def section(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha(args.font.read_bytes()) != FONT_SHA:
        raise ValueError("字型指紋不符")
    if sha((args.game / "LABELS.TXT").read_bytes()) != SOURCE_SHA:
        raise ValueError("原版 LABELS.TXT 指紋不符")
    source = (args.game / "LABELS.TXT").read_bytes()
    if source[0x888:0x88e] != b"Choose" or source[0x890:0x8a0] != b"Difficulty Level":
        raise ValueError("原版標題來源文字不符")
    palette = (args.reports / "goal079-headless-control.difficulty.pal").read_bytes()
    indexed = (args.reports / "goal079-headless-control.difficulty.idx").read_bytes()
    if len(palette) != 768 or sha(palette) != PALETTE_SHA or len(indexed) != 64000:
        raise ValueError("同狀態英文控制畫面／色盤不符")
    canvas = {name: (args.reports / f"goal061-difficulty-writes-replay.{name}.canvas").read_bytes()
              for name in ("choose-before", "choose-after", "level-before", "level-after")}
    if any(len(value) != 64000 for value in canvas.values()) or canvas["choose-after"] != canvas["level-before"]:
        raise ValueError("原版逐行畫布快照不完整")
    config = {name: [] for name in LAYOUTS}
    observed = []
    for line, content, safe, bbox, before_name, after_name, expected_pixels in LINES:
        before, after = canvas[before_name], canvas[after_name]
        changed = [(i % 320, i // 320) for i in range(64000) if before[i] != after[i]]
        actual = (min(x for x, _ in changed), min(y for _, y in changed),
                  max(x for x, _ in changed) + 1, max(y for _, y in changed) + 1)
        if len(changed) != expected_pixels or actual != bbox or section(indexed, safe) != section(canvas["level-after"], safe):
            raise ValueError("原版印字事件與穩定畫面不符：" + line)
        observed.append({"name": line, "bbox": bbox, "safe": safe,
                         "changed_pixels": len(changed), "center_x_scaled": (bbox[0] + bbox[2]) * 2,
                         "height_scaled": (bbox[3] - bbox[1]) * 4})
        for layout, (sizes, align) in LAYOUTS.items():
            size = sizes[0 if line == "choose" else 1]
            font = ImageFont.truetype(str(args.font), size)
            left, top, right, bottom = font.getbbox(content)
            width, height = right - left, bottom - top
            x = bbox[0] * 4 if align == "left" else (bbox[0] + bbox[2]) * 2 - width // 2
            y = bbox[1] * 4
            if not (safe[0] * 4 + 4 <= x and x + width <= safe[2] * 4 - 4 and
                    safe[1] * 4 + 4 <= y and y + height <= safe[3] * 4 - 4):
                raise ValueError("候選文字超出含內距的安全矩形：" + layout + "/" + line)
            mask = Image.new("L", (width, height))
            ImageDraw.Draw(mask).text((-left, -top), content, font=font, fill=255)
            config[layout].append({"name": line, "safe": safe, "original_ink_bbox": bbox,
                                   "font_size": size, "ink_width": width, "ink_height": height,
                                   "position": [x, y], "background": base64.b64encode(section(before, safe)).decode(),
                                   "mask": base64.b64encode(mask.tobytes()).decode()})
    args.output.mkdir(parents=True, exist_ok=True)
    for layout, layers in config.items():
        payload = {"prototype": True, "source_control_indexed_sha256": sha(indexed),
                   "palette_sha256": sha(palette), "font_sha256": FONT_SHA,
                   "indexed": base64.b64encode(indexed).decode(),
                   "palette": base64.b64encode(palette).decode(), "layers": layers}
        (args.output / f"{layout}.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")
    receipt = {"scope": "local disposable preview, not production", "source": observed,
               "control_indexed_sha256": sha(indexed), "palette_sha256": sha(palette),
               "font_sha256": FONT_SHA,
               "variants": {name: [{key: value for key, value in layer.items() if key not in ("background", "mask")}
                                   for layer in layers] for name, layers in config.items()}}
    (args.output / "measurements.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
