#!/usr/bin/env python3
"""核對 Ebitengine 卡片預覽：原文基準、可逆底圖、安全矩形與兩欄變更。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--chinese", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    indexed = base64.b64decode(source["indexed"], validate=True)
    palette = base64.b64decode(source["palette"], validate=True)
    require(len(indexed) == 64000 and len(palette) == 768, "原始畫面大小不符")
    with Image.open(args.control) as image:
        control = image.convert("RGB")
    with Image.open(args.chinese) as image:
        chinese = image.convert("RGB")
    require(control.size == chinese.size == (1280, 800), "Ebitengine 畫面大小不符")
    base, final = control.load(), chinese.load()
    changed = {layer["name"]: 0 for layer in source["layers"]}
    for y in range(800):
        for x in range(1280):
            index = indexed[(y // 4) * 320 + x // 4] * 3
            original = tuple((v << 2) | (v >> 4) for v in palette[index:index + 3])
            require(base[x, y] == original, "原文控制圖不是原始畫布最近鄰：%d,%d" % (x, y))
            owners = [layer["name"] for layer in source["layers"]
                      if layer["safe"][0] * 4 <= x < layer["safe"][2] * 4
                      and layer["safe"][1] * 4 <= y < layer["safe"][3] * 4]
            require(len(owners) <= 1, "兩欄安全區重疊")
            if not owners:
                require(final[x, y] == original, "中文變更超出安全矩形：%d,%d" % (x, y))
            elif final[x, y] != original:
                changed[owners[0]] += 1
    for layer in source["layers"]:
        x0, y0, x1, y1 = layer["safe"]
        width, height = x1 - x0, y1 - y0
        background = base64.b64decode(layer["background"], validate=True)
        mask = base64.b64decode(layer["mask"], validate=True)
        require(len(background) == width * height and len(mask) == layer["ink_width"] * layer["ink_height"],
                "預覽資料長度不符")
        ink_x, ink_y = layer["position"]
        restored = 0
        for y in range(y0 * 4, y1 * 4):
            for x in range(x0 * 4, x1 * 4):
                mx, my = x - ink_x, y - ink_y
                if 0 <= mx < layer["ink_width"] and 0 <= my < layer["ink_height"]:
                    if mask[my * layer["ink_width"] + mx] != 0:
                        continue
                index = background[(y // 4 - y0) * width + x // 4 - x0] * 3
                expected = tuple((v << 2) | (v >> 4) for v in palette[index:index + 3])
                require(final[x, y] == expected, "透明中文字模下未恢復原始背景：%s %d,%d" %
                        (layer["name"], x, y))
                if final[x, y] != base[x, y]:
                    restored += 1
        require(changed[layer["name"]] > 0 and restored > 0, "欄位沒有實際中文與背景恢復：" + layer["name"])
    receipt = {"prototype": True, "result": "PASS", "changed_pixels_by_field": changed,
               "control_png_sha256": hashlib.sha256(args.control.read_bytes()).hexdigest(),
               "chinese_png_sha256": hashlib.sha256(args.chinese.read_bytes()).hexdigest(),
               "source_receipt_sha256": source["source_receipt_sha256"]}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
