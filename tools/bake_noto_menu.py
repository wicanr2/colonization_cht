#!/usr/bin/env python3
"""規格055：逐列量測並烘製主選單四地區Noto；輸出限私用workplace。"""
import argparse
import base64
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version, features

from check_language_font_coverage import FACES, LOCALES, font_charset
from language_catalog import BaseCatalog, ROOT, canonical, load_translation, new_output, require, sha, write_tsv
from render_language_font_sample import HASHES

GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
EXE_SHA = "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3"
FRAME_SHA = "559df11e83c1fb01e2d844a4379af6369e279bf4ea7b4b30c95cbf2d4062c4a1"
FIELDS = [(0x1b0,25,107,177,113,180),(0x1cb,23,115,169,121,163),
          (0x1e4,19,123,161,128,152),(0x1f9,9,131,121,136,77),(0x204,17,139,145,145,112)]
KEYS = [f"GAME.TXT:0x{f[0]:08X}" for f in FIELDS]


def raster(font, text):
    # Pillow完整文字布局，保留overhang及descender；足夠留白後再裁實際墨跡。
    box = font.getbbox(text, anchor="ls")
    im = Image.new("L", (box[2]-box[0]+16, box[3]-box[1]+16))
    ImageDraw.Draw(im).text((8-box[0], 8-box[1]), text, font=font, anchor="ls", fill=255)
    ink = im.getbbox()
    require(ink is not None, "空白譯文墨跡")
    return im.crop(ink), {"font_bbox": list(box), "baseline": 8-box[1]-ink[1],
                          "advance": font.getlength(text)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "native-frame", "noto", "license", "output"):
        p.add_argument("--"+name, type=Path, required=True)
    a = p.parse_args()
    require(Path("/.dockerenv").is_file() and pillow_version == "9.4.0", "需Docker及Pillow9.4.0")
    for path, expected in ((a.game/"GAME.TXT", GAME_SHA), (a.game/"VICEROY.EXE", EXE_SHA),
                           (a.native_frame, FRAME_SHA), (a.noto, HASHES["noto"]), (a.license, HASHES["license"])):
        require(path.is_file() and sha(path.read_bytes()) == expected, "來源或字型雜湊不同")
    frame, game = a.native_frame.read_bytes(), (a.game/"GAME.TXT").read_bytes()
    require(len(frame) == 64000, "索引畫面大小不同")
    base = BaseCatalog()
    baseline = (ROOT/"text/draft.zh-Hant.tsv").read_bytes()
    table, header, _, _ = next(t for t in base.tables if t[0]["catalog"] == "draft")
    products, report = {}, {}
    for locale in LOCALES:
        data = baseline if locale == "zh-Hant" else (ROOT/f"text/game.{locale}.tsv").read_bytes()
        entries = base.entries
        if locale != "zh-Hant":
            entries, missing = load_translation(base, data, locale)
            require(not missing, "完整譯稿不可缺列")
        rows = []
        for key, (off, length, *_) in zip(KEYS, FIELDS):
            row = base.entries["draft", key]["row"].copy()
            require(row["source_sha256"] == GAME_SHA and row["source_bytes_sha256"] == sha(game[off:off+length]), "原版來源片段不同")
            row[table["display_column"]] = entries["draft", key]["text"]
            require(row["zh_hant"].strip() and not any(ch in row["zh_hant"] for ch in "~#{}^%@\\\n\r\t"), "此五列只支援純文字")
            rows.append(row)
        draft = write_tsv(header, rows)
        face, family = FACES[locale]
        present, _ = font_charset(a.noto, face, family)
        bind = {"baseline": sha(baseline), "draft": sha(draft), "source": GAME_SHA,
                "frame": FRAME_SHA, "license": HASHES["license"],
                "locale_profile": sha(canonical({"locale": locale, "face": face, "family": family}))}
        masks, measurements = {}, []
        for key, row, (_, _, y, right, bottom, count) in zip(KEYS, rows, FIELDS):
            points = [(x, yy) for yy in range(y,y+7) for x in range(86,232) if frame[yy*320+x] == 254]
            bounds = [min(x for x,yy in points), min(yy for x,yy in points),
                      max(x for x,yy in points)+1, max(yy for x,yy in points)+1]
            require(bounds == [86,y,right,bottom] and len(points) == count, "原版字高或點數不同")
            text, target = row["zh_hant"], (bottom-y)*4
            require(all(ord(ch) in present and ord(ch)>=32 for ch in text), "缺字或控制字元")
            candidates, valid = [], []
            for px in range(14,29):
                font = ImageFont.truetype(str(a.noto), px, index=face)
                require(font.getname()[0] == family, "地區face不同")
                mask, detail = raster(font, text)
                fits = mask.width <= 580 and mask.height <= 24
                detail.update(font_px=px, ink=[mask.width,mask.height], fits=fits)
                candidates.append(detail)
                if fits:
                    valid.append((abs(mask.height-target), -px, mask, detail))
            require(bool(valid), "欄位無可用字級，維持原文")
            _, _, mask, chosen = min(valid, key=lambda item:item[:2])
            obj = {"candidate_id":key, "translation_sha256":sha(text.encode()), "catalog_sha256":sha(draft),
                   "font_sha256":HASHES["noto"], "font_size":chosen["font_px"],
                   "values_sha256":sha(mask.tobytes()), "width":mask.width, "height":mask.height,
                   "alpha":base64.b64encode(mask.tobytes()).decode(), "bindings":bind}
            masks[key] = (obj,mask)
            measurements.append({"key":key,"original_ink":bounds,"original_pixels":count,"target_height":target,
                                 "safe":[86,y,232,y+7],"chosen":chosen,"candidates":candidates})
        products[locale] = (draft,masks)
        report[locale] = {"source_catalog_sha256":sha(data), "rows":measurements}
    output = new_output(a.output, directory=True)
    for locale,(draft,masks) in products.items():
        (output/f"draft.{locale}.tsv").write_bytes(draft)
        folder = output/locale
        folder.mkdir()
        for key,(obj,mask) in masks.items():
            name = key.replace(":","-")
            (folder/f"{name}.json").write_bytes(canonical(obj)+b"\n")
            mask.save(folder/f"{name}.png")
    result = {"kind":"spec055-noto-menu", "script_sha256":sha(Path(__file__).read_bytes()),
              "pillow":pillow_version,"freetype":features.version_module("freetype2"),"locales":report,
              "outputs_sha256":{str(p.relative_to(output)):sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}
    (output/"bake-check.json").write_bytes(canonical(result)+b"\n")
    require(all((p.stat().st_uid,p.stat().st_gid)==(os.getuid(),os.getgid()) for p in output.rglob("*")), "輸出擁有權不同")
    print("BAKED_SPEC055", output, sha((output/"bake-check.json").read_bytes()))
    for locale,r in report.items():
        print(locale, [(v["chosen"]["font_px"],v["chosen"]["ink"],v["chosen"]["baseline"]) for v in r["rows"]])


if __name__ == "__main__":
    main()
