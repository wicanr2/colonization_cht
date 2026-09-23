#!/usr/bin/env python3
"""獨立驗證姓名提示原版印前底圖與 Ebitengine 單欄原型。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image


SAFE = (100, 85, 219, 98)
BBOX = (104, 88, 215, 97)
PROMPT = b"Please Enter Your Name."
SCENES = {"idle": "55m", "letter": "57m", "backspace": "65m"}


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def section(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def rgba_from_original(indexed, palette):
    need(len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63,
         "索引／色盤尺寸不符")
    colors = [tuple((palette[i * 3 + c] << 2) | (palette[i * 3 + c] >> 4)
                    for c in range(3)) + (255,) for i in range(256)]
    image = Image.new("RGBA", (320, 200))
    image.putdata([colors[index] for index in indexed])
    return image.resize((1280, 800), Image.Resampling.NEAREST), colors


def verify(args):
    p = args.reports
    a_raw = (p / "a.json").read_bytes()
    need(a_raw == (p / "b.json").read_bytes(), "原版雙次冷啟動收據不一致")
    a = json.loads(a_raw)
    control = json.loads((p / "control.json").read_bytes())
    need(a["version"] == control["version"] == "goal094-prompt-v1" and
         a["input_sha256"] == control["input_sha256"] and
         a["samples"] == control["samples"] and a["opened"] == control["opened"] and
         control["reads"] == control["writes"] == [], "無觀測控制改變原版狀態")
    for sample in a["samples"]:
        for extension, key in (("idx", "indexed_sha256"), ("canvas", "canvas_sha256"),
                               ("pal", "palette_sha256")):
            data = (p / f"a.{sample}.{extension}").read_bytes()
            need(data == (p / f"b.{sample}.{extension}").read_bytes() ==
                 (p / f"control.{sample}.{extension}").read_bytes() and
                 sha(data) == a["samples"][sample][key], "畫布控制不符：" + sample + "/" + extension)
    before = (p / "a.before.canvas").read_bytes()
    after = (p / "a.after.canvas").read_bytes()
    stable = (p / "a.55m.idx").read_bytes()
    diff = [(i % 320, i // 320) for i, (old, new) in enumerate(zip(before, after)) if old != new]
    need(len(diff) == 415 and
         (min(x for x, _ in diff), min(y for _, y in diff),
          max(x for x, _ in diff) + 1, max(y for _, y in diff) + 1) == BBOX and
         all(SAFE[0] <= x < SAFE[2] and SAFE[1] <= y < SAFE[3] for x, y in diff),
         "原版提示印字畫素超出安全區")
    need(len(a["writes"]) == 415 and all(
        w["cs_ip"] == "0D21:012C" and
        before[w["y"] * 320 + w["x"]] == w["old"] and
        after[w["y"] * 320 + w["x"]] == w["new"] for w in a["writes"]),
        "畫布寫入與印字前後差分不符")
    need(bytes(r["value"] for r in a["reads"] if r["value"] != 0) == PROMPT and
         len(a["reads"]) == 45 and
         all(r["cs_ip"] == "0D21:00C6" for r in a["reads"]),
         "逐字輸出不等於固定姓名提示")
    need(section(after, SAFE) == section(stable, SAFE),
         "安全區在穩定畫面已被其他事件改寫")
    border = (100, 98, 219, 99)
    need(section(after, border) != section(stable, border),
         "姓名欄上緣應屬後續重繪，不能擴大提示安全區")
    measure = json.loads((args.preview / "measurements.json").read_bytes())
    need(measure["source_receipt_sha256"] == sha(a_raw) and
         tuple(measure["safe"]) == SAFE and tuple(measure["original_ink_bbox"]) == BBOX and
         measure["original_changed_pixels"] == 415 and
         measure["background_palette_indices"] == len(set(section(before, SAFE))) == 10 and
         measure["font_size"] == 38 and tuple(measure["ink_size"]) == (328, 35) and
         tuple(measure["position"]) == (474, 352), "預覽量測與原版證據不符")
    previews = {}
    for scene, sample in SCENES.items():
        payload = json.loads((args.preview / f"{scene}.json").read_bytes())
        indexed = (args.prior / f"{scene}-a.{sample}.idx").read_bytes()
        palette = (args.prior / f"{scene}-a.{sample}.pal").read_bytes()
        need(payload["scenario"] == scene and len(payload["layers"]) == 1 and
             base64.b64decode(payload["indexed"]) == indexed and
             base64.b64decode(payload["palette"]) == palette and
             payload["source_receipt_sha256"] == sha(a_raw),
             "Ebitengine 原型輸入不是原版固定收據：" + scene)
        layer = payload["layers"][0]
        need(tuple(layer["safe"]) == SAFE and tuple(layer["position"]) == (474, 352) and
             (layer["ink_width"], layer["ink_height"]) == (328, 35) and
             base64.b64decode(layer["background"]) == section(before, SAFE) and
             layer["color_index"] == 68 and layer["shadow_index"] == 47 and
             layer["shadow_dx"] == 4, "候選字模、配色或印前底圖不符：" + scene)
        control_image = Image.open(args.preview / f"{scene}-control.png").convert("RGBA")
        zh_image = Image.open(args.preview / f"{scene}-zh.png").convert("RGBA")
        original_image, colors = rgba_from_original(indexed, palette)
        need(control_image.size == zh_image.size == (1280, 800) and
             control_image.tobytes() == original_image.tobytes(),
             "Ebitengine 英文控制不等於 dosgolem 原版四倍畫面：" + scene)
        control_pixels = control_image.load()
        zh_pixels = zh_image.load()
        x0, y0, x1, y1 = (SAFE[0] * 4, SAFE[1] * 4, SAFE[2] * 4, SAFE[3] * 4)
        changed = 0
        foreground = 0
        for y in range(800):
            for x in range(1280):
                if zh_pixels[x, y] == control_pixels[x, y]:
                    continue
                need(x0 <= x < x1 and y0 <= y < y1,
                     "中文原型改動姓名欄或提示安全區外畫素：" + scene)
                changed += 1
                if zh_pixels[x, y] == colors[68]:
                    foreground += 1
        need(changed > 2000 and foreground > 300,
             "中文字形沒有在安全區正常顯示：" + scene)
        previews[scene] = {"changed_pixels": changed, "foreground_pixels": foreground,
                           "control_png_sha256": sha((args.preview / f"{scene}-control.png").read_bytes()),
                           "zh_png_sha256": sha((args.preview / f"{scene}-zh.png").read_bytes())}
    need(section((args.prior / "enter-a.65m.idx").read_bytes(), SAFE) !=
         section(stable, SAFE), "Enter 後提示畫面應已離開")
    result = {"result": "PASS", "scope": "提示可逆底圖、38px 候選及本機三情境原型；未驗正式前端回退",
              "original_receipt_sha256": sha(a_raw), "changed_pixels_original": len(diff),
              "safe": SAFE, "late_border_y98_excluded": True,
              "scenes": previews,
              "limitations": "僅可丟棄 Ebitengine 原型；正式事件守門、游標、缺鍵／缺字、真前端離頁回退未驗"}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())
