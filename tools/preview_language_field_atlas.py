#!/usr/bin/env python3
"""規格054 DRAFT：沿既有字模格式產生六列命令欄的四語私用圖集與Go探針。"""

import argparse
import base64
import json
import os
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageDraw, ImageFont, __version__ as pillow_version, features

from check_language_font_coverage import FACES, LOCALES
from language_catalog import BaseCatalog, ROOT, canonical, load_translation, require, sha
from preview_language_field_layout import visible_menu_text
from render_language_font_sample import HASHES


LAYOUT_SHA = "2023597c649abd7570a9e20737410c7635d8029a10e8aa6cbfcd8897114f755b"
COVERAGE_SHA = "8ddce673ba704cf37b9f5198d316b0e7e025ca0db909f0c2d4fb3c0847cb6aaf"
GO_SOURCE_SHA = {
    "tools/dialog_overlay.go": "b93dcf45c424b8aac175f71da0e05d54782d9ccc36774fdd1ac7f0bbd69e8a50",
    "tools/string_overlay.go": "072643055789eee243db8f0d2f4ccf929ee70b32d959058476151d23c9c8ac90",
}


def go_block(source, prefix, terminator="\n}\n"):
    require(source.count(prefix) == 1, f"Go來源定位不同：{prefix}")
    start = source.index(prefix)
    return source[start:source.index(terminator, start) + len(terminator)]


def menu_marked(text):
    text = re.sub(r"^~([A-Za-z])", r"({\1})", text.strip())
    return re.sub(r"~(.)", r"{\1}", text)


def raster_cell(font, character):
    ascent, descent = font.getmetrics()
    advance = round(font.getlength(character))
    require(advance > 0, "此欄字元沒有正字距")
    padded = Image.new("L", (128, 128))
    ImageDraw.Draw(padded).text((32, 32 + ascent), character, font=font, anchor="ls", fill=255)
    box = padded.getbbox()
    require(box is None or (box[0] > 0 and box[2] < 128 and 32 <= box[1] <= box[3] <= 32 + ascent + descent),
            "字形超出有界量測或垂直字格")
    left = min(0, box[0] - 32) if box else 0
    right = max(advance, box[2] - 32) if box else advance
    width = right - left
    cell = Image.new("L", (width, ascent + descent))
    ImageDraw.Draw(cell).text((-left, ascent), character, font=font, anchor="ls", fill=255)
    expected = padded.crop((32 + left, 32, 32 + right, 32 + ascent + descent))
    require(cell.tobytes() == expected.tobytes(), "擴展字格未完整保留原字形")
    old_clip = padded.copy()
    ImageDraw.Draw(old_clip).rectangle((32, 32, 32 + advance - 1, 32 + ascent + descent - 1), fill=0)
    return cell, {"native_advance": float(font.getlength(character)), "legacy_width": advance,
                  "width": width, "origin_x": -left,
                  "legacy_clipped_pixels": sum(value > 0 for value in old_clip.tobytes())}


def expected_masks(atlas, marked_rows, layout):
    size = atlas["sizes"]["18"]
    width, height = layout["safe_size"]
    masks = {name: Image.new("L", (width, height)) for name in ("normal", "accent", "dim")}
    bounds, advances = [], []
    for index, text in enumerate(marked_rows):
        x = 4
        top = (layout["native_row_tops"][index] - layout["native_safe"][1]) * 4
        y = top - size["cjk_ink_top"]
        row_mask = Image.new("L", (width + 64, height + 64))
        accent = False
        for character in text:
            if character in "{}":
                accent = character == "{"
                continue
            glyph = size["glyphs"][character]
            cell = Image.frombytes("L", (glyph["w"], size["height"]), base64.b64decode(glyph["alpha"]))
            row_mask.paste(cell, (32 + x, 32 + y))
            positioned = Image.new("L", (width, height))
            positioned.paste(cell, (x, y))
            name = "dim" if index in (1, 2, 3, 4) else "normal"
            masks[name] = ImageChops.lighter(masks[name], positioned)
            if accent and name != "dim":
                masks["accent"] = ImageChops.lighter(masks["accent"], positioned)
            x += glyph["w"]
        box = row_mask.getbbox()
        require(box is not None, "命令列沒有墨跡")
        ink = [value - 32 for value in box]
        bottom_limit = ((layout["native_row_tops"][index + 1] - layout["native_safe"][1]) * 4
                        if index < 5 else height - 4)
        require(ink[0] >= 4 and ink[1] >= 0 and ink[2] <= width - 4 and ink[3] <= bottom_limit and
                x + 4 <= width, "實際拼字後超界；不得靠裁切通過")
        bounds.append(ink)
        advances.append(x - 4)
    return masks, bounds, advances


def gallery(font_path, masks):
    image = Image.new("RGB", (720, 680), "#f2ecdf")
    draw = ImageDraw.Draw(image)
    heading = ImageFont.truetype(str(font_path), 22, index=3)
    for index, locale in enumerate(LOCALES):
        x, y = 24 + index % 2 * 360, 54 + index // 2 * 320
        draw.text((x, y - 34), f"{locale}  Noto atlas 18px", font=heading, fill="#272d2c")
        pane = Image.new("RGB", masks[locale]["normal"].size, "#161d27")
        # 這是色層辨讀用配色，不是原版DAC色盤收據。
        for name, color in (("normal", "#eee4cc"), ("dim", "#828b94"), ("accent", "#ffd264")):
            pane.paste(color, (0, 0, pane.width, pane.height), masks[locale][name])
        ImageDraw.Draw(pane).rectangle((0, 0, pane.width - 1, pane.height - 1), outline="#688078")
        image.paste(pane, (x, y))
    return image


GO_MAIN = r'''
type probeLocale struct {
    Atlas string `json:"atlas"`
    Bindings map[string]string `json:"bindings"`
    Rows []string `json:"rows"`
    Expected map[string]string `json:"expected_masks"`
}
func main() {
    data, err := os.ReadFile("../probe-input.json"); must(err)
    var input struct { Font string `json:"font_sha256"`; Locales map[string]probeLocale `json:"locales"` }
    must(json.Unmarshal(data, &input))
    results := map[string]any{}
    for locale, entry := range input.Locales {
        raw, err := os.ReadFile("../"+entry.Atlas); must(err)
        fonts, why := loadAtlasFonts(raw, input.Font, entry.Bindings, 18, 18)
        check(why == "", "actual loader rejected atlas: "+why)
        check(len(entry.Rows) == 6, "wrong row count")
        rows := make([]runLine, 6); items := make([]string, 6)
        tops := []int{13,21,29,37,53,69}; rights := []int{123,141,105,103,157,155}
        for i, text := range entry.Rows {
            rows[i] = runLine{box:image.Rect(81,tops[i],rights[i],tops[i]+6),capH:5}
            items[i] = menuZh(text)
        }
        c := &dialogCatalog{fonts:fonts}
        safe := image.Rect(80,12,159,77)
        layers := []int{layerNormal,layerDim,layerDim,layerDim,layerDim,layerNormal}
        sh,n,ac,dm,size := c.lineLayerMasks(items,rows,safe,8,false,layers)
        check(size == 18 && sh != nil && n != nil && ac != nil && dm != nil, "actual layout failed")
        hashes := map[string]string{}
        for name, mask := range map[string]*image.Alpha{"normal":n,"accent":ac,"dim":dm} {
            hashes[name] = fmt.Sprintf("%x",sha256.Sum256(mask.Pix))
            check(hashes[name] == entry.Expected[name], "mask differs from padded Python reference: "+name)
            f,err := os.OpenFile("../go-"+locale+"-"+name+".png",os.O_WRONLY|os.O_CREATE|os.O_EXCL,0644); must(err)
            must(png.Encode(f,mask)); must(f.Close())
        }
        _,why = loadAtlasFonts(raw,"wrong-font",entry.Bindings,18,18)
        check(why == "font-binding-mismatch", "wrong font accepted")
        wrong := map[string]string{}; for k,v := range entry.Bindings { wrong[k]=v }; wrong["locale_profile"]="wrong-region"
        _,why = loadAtlasFonts(raw,input.Font,wrong,18,18)
        check(why == "font-binding-mismatch", "wrong region binding accepted")
        _,why = loadAtlasFonts(raw,input.Font,entry.Bindings,19,18)
        check(why == "font-binding-mismatch", "wrong size accepted")
        longItems := append([]string(nil),items...); longItems[0]=strings.Repeat("W",1000)
        _,_,_,_,s := c.lineLayerMasks(longItems,rows,safe,8,false,layers)
        check(s == 0, "overlong row accepted")
        width := fonts[18].widths['A']; delete(fonts[18].widths,'A')
        _,_,_,_,s = c.lineLayerMasks(items,rows,safe,8,false,layers)
        check(s == 0, "missing glyph accepted"); fonts[18].widths['A']=width
        results[locale]=map[string]any{"font_px":size,"glyphs":len(fonts[18].glyphs),"negative_checks":5,"mask_sha256":hashes}
    }
    out,err := json.MarshalIndent(map[string]any{"status":"PASS","scope":"actual loader and field masks; no original execution or GUI","locales":results},"","  "); must(err)
    f,err := os.OpenFile("../go-check.json",os.O_WRONLY|os.O_CREATE|os.O_EXCL,0644); must(err)
    _,err=f.Write(append(out,'\n')); must(err); must(f.Close())
    fmt.Println("PASS_ACTUAL_GO_LOADER_AND_FIELD_MASKS",len(results))
}
func check(ok bool, message string) { if !ok { panic(message) } }
func must(err error) { if err != nil { panic(err) } }
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("layout", "coverage", "noto", "license", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file() and pillow_version == "9.4.0", "需Docker內Pillow9.4.0")
    for name, expected in (("layout", LAYOUT_SHA), ("coverage", COVERAGE_SHA),
                           ("noto", HASHES["noto"]), ("license", HASHES["license"])):
        path = getattr(args, name)
        require(path.is_file() and sha(path.read_bytes()) == expected, f"固定輸入指紋不符：{name}")
    for name, expected in GO_SOURCE_SHA.items():
        require(sha((ROOT / name).read_bytes()) == expected, f"Go消費端來源指紋不符：{name}")
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
            output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "需新的workplace輸出")
    layout = json.loads(args.layout.read_text())
    coverage = json.loads(args.coverage.read_text())
    base = BaseCatalog()
    require(layout["source_binding_sha256"] == coverage["source_binding_sha256"] ==
            base.registry["source_binding_sha256"], "原始來源綁定不同")
    keys = list(layout["source_rows_sha256"])
    require(len(keys) == 6 and layout["native_safe"] == [80, 12, 159, 77] and
            layout["native_row_tops"] == [13, 21, 29, 37, 53, 69], "欄位定位不同")
    atlases, audits, masks, probe = {}, {}, {}, {"font_sha256": HASHES["noto"], "locales": {}}
    for locale in LOCALES:
        data = (ROOT / ("text/draft.zh-Hant.tsv" if locale == "zh-Hant" else f"text/game.{locale}.tsv")).read_bytes()
        entries = base.entries
        if locale != "zh-Hant":
            entries, missing = load_translation(base, data, locale, False)
            require(not missing and sha(data) == layout["catalog_sha256"][locale], "譯稿不同或未完整")
        raw_rows = [entries["draft", key]["text"].strip() for key in keys]
        marked = [menu_marked(text) for text in raw_rows]
        require([re.sub(r"[{}]", "", text) for text in marked] ==
                [row["text"] for row in layout["locales"][locale]["chosen"]["rows"]], "標記轉換不同")
        require([visible_menu_text(text) for text in raw_rows] ==
                [re.sub(r"[{}]", "", text) for text in marked], "實際選單字串不符")
        require(layout["locales"][locale]["chosen"]["font_px"] == 18, "此原型只驗18px欄位")
        face, family = FACES[locale]
        font = ImageFont.truetype(str(args.noto), 18, index=face)
        require(font.getname()[0] == family, "地區字型不同")
        chars = sorted(set("".join(visible_menu_text(text) for text in raw_rows)) | {chr(c) for c in range(32, 127)})
        present = set(coverage["locales"][locale]["game_codepoints"])
        require(all(f"U+{ord(ch):04X}" in present for ch in chars), "欄位字元未經完整字集核對")
        glyphs, glyph_audit = {}, {}
        for character in chars:
            cell, details = raster_cell(font, character)
            glyphs[character] = {"w": cell.width, "alpha": base64.b64encode(cell.tobytes()).decode()}
            glyph_audit[character] = details
        ascent, descent = font.getmetrics()
        cap = font.getbbox("國", anchor="ls")
        bindings = {"source_binding": base.registry["source_binding_sha256"], "catalog": sha(data),
                    "layout": LAYOUT_SHA, "coverage": COVERAGE_SHA, "license": HASHES["license"],
                    "locale_profile": sha(canonical({"locale": locale, "face": face, "family": family}))}
        atlas = {"font_sha256": HASHES["noto"], "font_px": 18, "floor_px": 18, "bindings": bindings,
                 "sizes": {"18": {"height": ascent + descent, "ascent": ascent,
                                    "cjk_ink_top": ascent + cap[1], "cjk_ink_bottom": ascent + cap[3],
                                    "glyphs": glyphs}}, "charset_sha256": sha("".join(chars).encode()),
                 "scope": "DRAFT private compact-orders only; existing integer-cell schema; no production atlas"}
        field = {"safe_size": layout["locales"][locale]["safe_size"], **layout}
        rendered, bounds, advances = expected_masks(atlas, marked, field)
        atlases[locale], masks[locale] = atlas, rendered
        audits[locale] = {"glyphs": len(chars), "glyph_audit": glyph_audit, "row_ink": bounds,
                          "row_advances": advances, "font_px": 18, "ascii_count": 95,
                          "legacy_clipped_characters": [ch for ch, row in glyph_audit.items() if row["legacy_clipped_pixels"]]}
        probe["locales"][locale] = {"atlas": f"atlas.{locale}.json", "bindings": bindings, "rows": raw_rows,
                                     "expected_masks": {name: sha(mask.tobytes()) for name, mask in rendered.items()}}
    source = (ROOT / "tools/dialog_overlay.go").read_text()
    string_source = (ROOT / "tools/string_overlay.go").read_text()
    prefixes = ["type dialogFont struct {", "type dialogGlyph struct {", "type runLine struct {",
                "func loadAtlasFonts(", "func menuZh(", "func dialogMarked(", "func dialogBlit(",
                "func dialogSizes(", "func (c *dialogCatalog) lineLayerMasks("]
    blocks = [go_block(source, prefix) for prefix in prefixes]
    blocks += [go_block(source, "const (\n\tdialogFontPx", "\n)\n"),
               go_block(source, "const (\n\tlayerNormal", "\n)\n"),
               go_block(string_source, "func stringStartPx(")]
    go_source = ('package main\nimport ("crypto/sha256"; "encoding/base64"; "encoding/json"; "fmt"; '
                 '"image"; "image/png"; "math"; "os"; "strconv"; "strings")\n'
                 'type dialogCatalog struct { fonts map[int]*dialogFont }\n' + "\n".join(blocks) + GO_MAIN)
    output.mkdir()
    for locale, atlas in atlases.items():
        (output / f"atlas.{locale}.json").write_bytes(canonical(atlas) + b"\n")
        for name, mask in masks[locale].items():
            mask.save(output / f"python-{locale}-{name}.png")
    gallery(args.noto, masks).save(output / "field-atlas-noto.png")
    (output / "probe-input.json").write_bytes(canonical(probe) + b"\n")
    go_dir = output / "go-probe"
    go_dir.mkdir()
    (go_dir / "go.mod").write_text("module colonization-field-probe\n\ngo 1.26.7\n")
    (go_dir / "main.go").write_text(go_source)
    report = {"kind": "draft-field-atlas-and-source-extracted-probe-not-production", "layout_sha256": LAYOUT_SHA,
              "coverage_sha256": COVERAGE_SHA, "go_source_sha256": GO_SOURCE_SHA, "go_blocks_sha256": sha("\n".join(blocks).encode()),
              "script_sha256": sha(Path(__file__).read_bytes()), "font_sha256": HASHES["noto"],
              "pillow": pillow_version, "freetype": features.version_module("freetype2"), "locales": audits,
              "outputs_sha256": {str(p.relative_to(output)): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()},
              "limits": ["Only six measured menu rows and printable ASCII; no complete runtime font package.",
                         "Integer cells include native overhang; spacing differs from fractional font advances.",
                         "Existing Go function bodies are copied verbatim into a private probe; no game or GUI runs.",
                         "Gallery colors illustrate layer separation; no original DAC palette or screenshot is used.",
                         "Native source identity limits from spec035 remain; 18px is not a global size."]}
    (output / "atlas-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in output.rglob("*")), "輸出擁有權不同")
    print(json.dumps({"output": str(output), "report_sha256": sha((output / "atlas-check.json").read_bytes()),
                      "locales": {locale: {k: row[k] for k in ("glyphs", "font_px", "legacy_clipped_characters")}
                                  for locale, row in audits.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
