#!/usr/bin/env python3
"""用固定真實字型重生四語與英數比較圖；只作候選樣張，不作正式排版。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


ROOT = Path(__file__).resolve().parent.parent
HASHES = {
    "cubic": "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c",
    "noto": "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a",
    "license": "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2",
}
SAMPLES = [
    ("zh-Hant", "繁體中文", 3, "殖民地：Jamestown　1492年 春", "建造倉庫　黃金：1000　稅率：25%"),
    ("zh-Hans", "简体中文", 2, "殖民地：Jamestown　1492年 春", "建造仓库　黄金：1000　税率：25%"),
    ("ja", "日本語", 0, "植民地：Jamestown　1492年 春", "倉庫を建設　金：1000　税率：25%"),
    ("ko", "한국어", 1, "식민지: Jamestown　1492년 봄", "창고 건설　금: 1000　세율: 25%"),
]
ASCII_SAMPLE = "Abc 0123456789  $1000  25%"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def missing(font, text):
    tofu = font.getmask("\U0010ffff")
    key = (tofu.size, bytes(tofu))
    return sorted({ch for ch in text if not ch.isspace() and
                   (font.getmask(ch).size, bytes(font.getmask(ch))) == key})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cubic", type=Path, required=True)
    parser.add_argument("--noto", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not Path("/.dockerenv").is_file() or pillow_version != "9.4.0":
        raise SystemExit("需Docker內固定Pillow9.4.0候選工具鏈")
    for field, expected in HASHES.items():
        if sha(getattr(args, field).read_bytes()) != expected:
            raise SystemExit(f"字型或授權指紋失配：{field}")
    output = args.output.resolve()
    if (not output.is_relative_to((ROOT / "workplace").resolve()) or output.exists() or
            not output.parent.is_dir() or output.parent.stat().st_uid != os.getuid()):
        raise SystemExit("輸出須為新的workplace子目錄，父目錄擁有者須相同")
    image = Image.new("RGB", (1440, 900), "#f2ecdf")
    draw = ImageDraw.Draw(image)
    ui = ImageFont.truetype(str(args.noto), 23, index=3)
    heading = ImageFont.truetype(str(args.noto), 30, index=3)
    draw.text((28, 18), "非英文模式字型候選", font=heading, fill="#272d2c")
    draw.text((28, 64), "同一字型繪製文字、英文字母與數字；英文模式保留原版字體。", font=ui, fill="#4e5553")
    draw.text((28, 103), "現行 Cubic 11", font=ui, fill="#272d2c")
    draw.text((748, 103), "高清 Noto Sans CJK", font=ui, fill="#272d2c")
    rows = []
    for row, (language, label, face, first, second) in enumerate(SAMPLES):
        y = 145 + row * 180
        draw.line((28, y - 4, 1412, y - 4), fill="#c7beab", width=1)
        left = ImageFont.truetype(str(args.cubic), 29)
        right = ImageFont.truetype(str(args.noto), 29, index=face)
        strings = [first, second, ASCII_SAMPLE]
        absent_left = missing(left, "".join(strings))
        absent_right = missing(right, "".join(strings) + label)
        if absent_right:
            raise SystemExit(f"候選字型缺樣張文字：{language} {absent_right}")
        draw.text((28, y), label, font=ImageFont.truetype(str(args.noto), 22, index=face), fill="#516455")
        draw.text((748, y), label, font=ImageFont.truetype(str(args.noto), 22, index=face), fill="#516455")
        if absent_left:
            draw.text((28, y + 40), "此字型缺少樣張所需字形", font=ui, fill="#9a382a")
            draw.text((28, y + 120), ASCII_SAMPLE, font=left, fill="#272d2c")
        else:
            for n, text in enumerate(strings):
                draw.text((28, y + 36 + n * 40), text, font=left, fill="#272d2c")
        for n, text in enumerate(strings):
            draw.text((748, y + 36 + n * 40), text, font=right, fill="#272d2c")
            if draw.textbbox((748, y + 36 + n * 40), text, font=right)[2] > 1412:
                raise SystemExit("樣張欄位超界")
        rows.append({"language": language, "noto_face_index": face, "text": strings,
                     "cubic_missing": absent_left, "noto_missing": absent_right,
                     "noto_text_boxes": [right.getbbox(text) for text in strings]})
    output.mkdir()
    path = output / "font-comparison.png"
    image.save(path)
    evidence = {"kind": "font-choice-prototype-not-production-layout", "pillow": pillow_version,
                "script_sha256": sha(Path(__file__).read_bytes()), "inputs_sha256": HASHES,
                "image_sha256": sha(path.read_bytes()), "size": list(image.size), "rows": rows,
                "source": "https://github.com/notofonts/noto-cjk/tree/523d033d6cb47f4a80c58a35753646f5c3608a78",
                "limits": "Sample glyph checks only; not full-corpus coverage or per-field production layout."}
    (output / "sample-evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(path, evidence["image_sha256"])


if __name__ == "__main__":
    main()
