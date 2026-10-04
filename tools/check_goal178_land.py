#!/usr/bin/env python3
"""在 Docker 內驗證正常陸地 ORDERS 十列及第一個 Fortify 的原始來源。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal134_window import load, same_state
from check_goal178_ship import ORIGINALS, equal_image, sha, png_for
from check_goal178_menu_sources import menu_sources

PINNED = {
    "source-query.log.matches.json": "17fec8bf2ff7046371e3f8f6242703b4a584f63ebf16730d81262533de8d38a8",
    "source-query.log.copies.json": "10fafc5b0a0946905458b4837ab3f41676a263c00473ad94fb1a9a581baced63",
}
LAYOUT_SHA = "d47f816c892764e1a4d64e118bdfe5ee7399a8b71741bafa08493ec1703d2ee5"
INPUT_SHA = "2bfc26e7fe9895a3a11dfca9e3135bf6e54119543a441dca5bb7e2bf9cd6d95c"
SEED_SHA = "cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e"
FIELD = [80, 12, 159, 125]


def verify(game, root, provenance, layout_path):
    for name, expected in ORIGINALS.items():
        assert sha(game / name) == expected, name
    for name, expected in PINNED.items():
        assert sha(provenance / name) == expected, "來源收據指紋不符：" + name
    assert sha(layout_path) == LAYOUT_SHA, "陸地欄位量測不符"
    assert sha(root / "gui-colony.inputs.json") == INPUT_SHA, "GUI 輸入不同"
    layout = json.loads(layout_path.read_text())
    items = [line["Text"] for line in layout["original_lines"]]
    assert len(items) == 10 and layout["layers"] == [0, 0, 0, 0, 0, 1, 1, 0, 0, 0]
    assert layout["dim_color"] == 8 and layout["selected_px"] == 21
    assert layout["candidate21_ink_height"] == 19 and layout["candidate22_ink_height"] == 21
    assert layout["output_safe_width"] == 316 and layout["output_safe_height"] == 452
    assert layout["longest_advance"] == max(layout["advance_widths"]) == 252
    assert layout["longest_advance"] + 8 <= 316
    ink = layout["mask_ink"]
    assert 0 <= ink["Min"]["X"] < ink["Max"]["X"] <= 316
    assert 0 <= ink["Min"]["Y"] < ink["Max"]["Y"] <= 452
    loaded = {name: load(root / name) for name in ("gui-colony", "replay-zh", "replay-control", "neg-noatlas")}
    control = loaded["replay-control"][0]
    assert control["control"] is True and control["state"]["steps"] == 77000000
    for name, value in loaded.items():
        if name != "replay-control":
            same_state(value, loaded["replay-control"], name + "完整原版不同")
        report, files, _ = value
        for key in ("state", "input_hashes", "opened"):
            assert report[key] == control[key], (name, key)
        assert hashlib.sha256(files["memory"]).hexdigest() == report["state"]["memory_sha256"]
    indices = {name: {cp["step"]: cp for cp in loaded[name][0]["checkpoints"] if cp["label"] != "final"}
               for name in ("replay-zh", "replay-control", "neg-noatlas")}
    shots = dict(line.split() for line in (root / "gui-colony.shots").read_text().splitlines())
    assert len(shots) == 7 and all(len(index) == 7 for index in indices.values())
    for name, step in shots.items():
        equal_image(root / f"gui-colony.{name}.png", root / f"replay-zh.cp-{step}.png")
    for step, cp in indices["replay-control"].items():
        for name in ("replay-zh", "neg-noatlas"):
            for key in ("memory_sha256", "raw_sha256", "palette_sha256"):
                assert indices[name][step][key] == cp[key], (name, step, key)
        equal_image(png_for(root, "replay-control", cp), png_for(root, "neg-noatlas", indices["neg-noatlas"][step]))
    step = int(shots["land-orders"])
    assert step == 69465000
    zh = loaded["replay-zh"][0]
    sources = [e for e in zh["events"] if e.get("stage") == "source" and e.get("items") == items and e["step"] < step]
    assert sources, "缺十列原始來源"
    source = sources[-1]
    assert source["candidate_id"] == "MENU.TXT:0x000003BC+list"
    assert source["entry_ip"] == "0D21:00C6" and source["source_linear"] == 175684
    assert source["safe"] == FIELD and source["font_px"] == 21
    assert any(e.get("stage") == "active" and e.get("candidate_id") == source["candidate_id"] and
               source["step"] <= e["step"] <= step for e in zh["events"])
    cp = indices["replay-zh"][step]
    assert any(line.get("candidate_id") == source["candidate_id"] and line.get("applied") for line in cp["lines"])
    en_image = Image.open(png_for(root, "replay-control", indices["replay-control"][step])).convert("RGB")
    zh_image = Image.open(png_for(root, "replay-zh", cp)).convert("RGB")
    palette_path = root / f"replay-control.cp-{step}.pal"
    palette = palette_path.read_bytes()
    assert len(palette) == 768 and max(palette) <= 63 and sha(palette_path) == cp["palette_sha256"]

    def rgb(index):
        return tuple(v << 2 | v >> 4 for v in palette[index * 3:index * 3 + 3])

    for line, layer in zip(layout["original_lines"], layout["layers"]):
        assert line["cap_h"] == 5
        y = line["Box"]["Min"]["Y"] * 4
        rect = (320, y, 636, y + 24)
        assert ImageChops.difference(en_image.crop(rect), zh_image.crop(rect)).getbbox(), line["Text"]
        if layer == 1:
            colors = zh_image.crop(rect).getcolors(316 * 24)
            assert colors and any(color == rgb(8) for _, color in colors), "停用灰色丟失"
            assert all(color not in (rgb(68), rgb(149)) for _, color in colors), "停用列變可用色"
    safe = tuple(v * 4 for v in FIELD)
    for shot in ("unit-ready", "orders-closed"):
        close_step = int(shots[shot])
        en = Image.open(png_for(root, "replay-control", indices["replay-control"][close_step])).convert("RGB").crop(safe)
        translated = Image.open(png_for(root, "replay-zh", indices["replay-zh"][close_step])).convert("RGB").crop(safe)
        assert ImageChops.difference(en, translated).getbbox() is None, "選單外仍有殘字：" + shot
    for folder in ("scratch", "replay-zh-save", "replay-control-save", "neg-noatlas-save"):
        saves = sorted((root / folder).glob("*.SAV"))
        assert [file.name for file in saves] == ["COLONY00.SAV"] and sha(saves[0]) == SEED_SHA, folder
    assert sha(provenance / "scratch/COLONY00.SAV") == SEED_SHA
    assert sha(provenance / "inputs.json") == INPUT_SHA
    ids, details, observation = menu_sources(game, provenance, {"@ORDERS": ((0x28D,), 63000000, step)})
    assert observation["inputs_sha256"] == INPUT_SHA and observation["final_step"] == control["state"]["steps"]
    assert observation["memory_sha256"] == control["state"]["memory_sha256"]
    assert (provenance / "source-query.log.memory").read_bytes() == (root / "replay-control.memory").read_bytes()
    return {"result": "PASS", "grade": "confirmed", "inputs_sha256": INPUT_SHA,
            "final_step": control["state"]["steps"], "final_memory_sha256": control["state"]["memory_sha256"],
            "gui_images_exact": 7, "original_checkpoints_equal": 7,
            "verified_fields": [{"candidate_id": source["candidate_id"], "shown": source["shown"],
                                 "safe": FIELD, "source_ids": ids["@ORDERS"]}],
            "source_details": details, "layout_sha256": sha(layout_path),
            "source_checker_sha256": sha(Path(__file__).with_name("check_goal178_menu_sources.py")),
            "evidence_sha256": {name: sha(provenance / name) for name in PINNED},
            "scope": "只驗此正常陸地十列及第一Fortify來源；其他單位／命令仍待驗"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "reports", "provenance", "layout"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if any(not (args.game / name).is_file() for name in ORIGINALS):
        print("SKIP：缺合法原版輸入")
        return 77
    try:
        result = verify(args.game, args.reports, args.provenance, args.layout)
    except (AssertionError, OSError, KeyError, ValueError, TypeError, StopIteration) as error:
        print("FAIL：" + str(error))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
