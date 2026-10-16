#!/usr/bin/env python3
"""規格069 R69：獨立核對新遊戲背景、原文字形及選取框像素。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import argparse, base64, collections, hashlib, json, os

parser = argparse.ArgumentParser(description=__doc__)
for name in ["root", "model", "generation", "output"]:
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--expected-samples", type=int, default=46)
args = parser.parse_args()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert 1 <= args.expected_samples <= 100 and not args.output.exists()
assert args.output.resolve().is_relative_to("/out")
assert args.output.parent.stat().st_uid == os.getuid()
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
fixture = read(args.root / "fixture.json")
model = read(args.model / "check.json")
assert model["source_fixture_sha256"] == sha(args.root / "fixture.json")
assert len(fixture["samples"]) == args.expected_samples
generation = read(args.generation)


def unpack(value):
    data = base64.b64decode(value, validate=True)
    assert len(data) == 8000
    return {k for k in range(64000) if data[k >> 3] & (1 << (k & 7))}


arts, contracts = {}, {}
for contract in model["source_contracts"]:
    source_id = contract["source_id"]
    name = "difficulty" if source_id == 819 else "nations"
    path = Path(generation[name]["file"])
    assert sha(path) == contract["asset_sha256"]
    raw = Image.open(path).convert("RGBA")
    assert raw.size == (1586, 992) and raw.getextrema()[3] == (255, 255)
    art = raw.resize((1280, 800), Image.Resampling.NEAREST)
    source_boxes = Image.new("1", raw.size)
    native_boxes = Image.new("1", (1280, 800))
    for rect in contract["art_rects"]:
        ImageDraw.Draw(source_boxes).rectangle(
            (rect[0], rect[1], rect[2] - 1, rect[3] - 1), fill=1)
    for rect in contract["native_rects"]:
        ImageDraw.Draw(native_boxes).rectangle(
            (rect[0] * 4, rect[1] * 4, rect[2] * 4 - 1, rect[3] * 4 - 1), fill=1)
    extra = ImageChops.logical_and(
        source_boxes.resize((1280, 800), Image.Resampling.NEAREST),
        ImageChops.invert(native_boxes))
    wood = raw.crop((32, 0, 33, 992)).resize((1280, 800), Image.Resampling.NEAREST)
    art.paste(wood, (0, 0), extra)
    for native, source in zip(contract["native_rects"], contract["art_rects"]):
        size = ((native[2] - native[0]) * 4, (native[3] - native[1]) * 4)
        art.paste(raw.crop(tuple(source)).resize(size, Image.Resampling.NEAREST),
                  (native[0] * 4, native[1] * 4))
    arts[source_id], contracts[source_id] = art.load(), contract

results = []
positive = collections.Counter()
total = original_total = 0
formal = True
for sample in fixture["samples"]:
    state = sample["state"]
    point = sample["point"]
    prefix = args.root / "observed" / ("point-%03d" % point)
    native = prefix.with_suffix(".idx").read_bytes()
    palette = prefix.with_suffix(".palette").read_bytes()
    assert hashlib.sha256(native).hexdigest() == state["indexed_sha256"]
    assert hashlib.sha256(palette).hexdigest() == state["palette_sha256"]
    expected_model = read(args.model / ("point-%03d.json" % point))
    live = sample["native_live"]
    locale, graphics = sample["locale"], sample["graphics"]
    shown = Image.open(sample["image"]).convert("RGBA")
    assert shown.size == (1280, 800)
    pixels = shown.load()
    unsafe = set()
    if locale != "en":
        for item in live["items"]:
            for key in ["safe", "source_safe"]:
                if key not in item:
                    continue
                r = item[key]
                unsafe.update(y * 320 + x
                              for y in range(r["Min"]["Y"], r["Max"]["Y"])
                              for x in range(r["Min"]["X"], r["Max"]["X"]))
    mouse = state["dos_mouse"]
    hd = live.get("hd") or {}
    mask = set()
    source_id = 0
    if graphics == "hd":
        group = hd.get("new_game_picture") or {}
        source_id = group.get("source_id", 0)
        assert source_id == expected_model["source_id"], sample["label"]
        mask = unpack(group["mask"])
        assert mask == unpack(expected_model["paint_mask"])
        assert len(mask) == group["painted"]
        assert unpack(group["glyph_mask"]) == unpack(expected_model["glyph_mask"])
        bg = unpack(group["background_mask"])
        assert len(bg) == group["background_repaints"] and bg <= unsafe
        if source_id:
            formal = formal and group["formal"] and not group["prototype"]
            positive[(source_id, locale)] += 1
        else:
            assert not mask and not bg
    else:
        assert not hd
    count = retained = 0
    # Other formal HD layers are inherited; an unmatched new-game source receives
    # no new credit. Native20 separately checks the unchanged complement.
    if graphics == "original" or source_id:
        for k, value in enumerate(native):
            x, y = k % 320, k // 320
            if k in unsafe or (mouse["x"] <= x < mouse["x"] + 16 and
                               mouse["y"] <= y < mouse["y"] + 16):
                continue
            color = tuple((v << 2) | (v >> 4) for v in palette[value * 3:value * 3 + 3]) + (255,)
            for dy in range(4):
                for dx in range(4):
                    target = arts[source_id][x * 4 + dx, y * 4 + dy] if k in mask else color
                    assert pixels[x * 4 + dx, y * 4 + dy] == target, (
                        sample["label"], x, y, dx, dy,
                        pixels[x * 4 + dx, y * 4 + dy], target)
                    if k in mask:
                        count += 1
                    else:
                        retained += 1
    total += count
    original_total += retained
    results.append({"sample": sample["label"], "source_id": source_id,
                    "locale": locale, "graphics": graphics,
                    "picture_rgba_pixels": count, "preserved_original_rgba_pixels": retained})
assert set(positive) == {(n, l) for n in [819, 1073]
                         for l in ["en", "zh-Hant", "zh-Hans", "ja", "ko"]}
result = {"result": "PASS_NEW_GAME_INDEPENDENT_GUI_RGBA_AND_ORIGINAL_TEXT",
          "samples": results, "rgba_pixels": total,
          "preserved_original_rgba_pixels": original_total,
          "positive_source_languages": {str(k): v for k, v in positive.items()},
          "fixture_sha256": sha(args.root / "fixture.json"),
          "model_sha256": sha(args.model / "check.json"),
          "checker_sha256": sha(Path(__file__)),
          "production_connected": formal}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(result["result"], len(results), total, original_total, flush=True)
