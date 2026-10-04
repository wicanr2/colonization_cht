#!/usr/bin/env python3
"""在 Docker 內驗證船隻命令清單及關閉恢復；不修改原版。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal134_window import load, same_state


LAYOUT_SHA = "d93d2a86a4340ab8ef5ed1b461dd406f1fdb6bdce5cdb1f58f9fd42d77055aa3"
ORIGINALS = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "MENU.TXT": "5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal_image(a, b):
    assert ImageChops.difference(Image.open(a).convert("RGB"), Image.open(b).convert("RGB")).getbbox() is None, (a, b)


def png_for(root, name, checkpoint):
    label = checkpoint["label"]
    assert label == "final" or label == f"cp-{checkpoint['step']}", "圖片標籤與步數不同"
    filename = f"{name}.{label}.png"
    assert Path(checkpoint["png"]).name == filename, "圖片名稱未綁定收據"
    return root / filename


def check(game, root, layout_path):
    for name, expected in ORIGINALS.items():
        assert sha(game / name) == expected, name
    assert sha(layout_path) == LAYOUT_SHA, "欄位量測不符"
    layout = json.loads(layout_path.read_text())
    expected_items = [x["Text"] for x in layout["original_lines"]]
    assert len(expected_items) == 14
    names = ("gui-colony", "replay-zh", "replay-control", "neg-noatlas", "baseline-v59")
    loaded = {n: load(root / n) for n in names}
    assert loaded["replay-control"][0]["control"] is True
    for name in (n for n in names if n != "replay-control"):
        same_state(loaded[name], loaded["replay-control"], name + "完整原版狀態不同")
    for report, files, _ in loaded.values():
        assert hashlib.sha256(files["memory"]).hexdigest() == report["state"]["memory_sha256"]
    reports = {n: loaded[n][0] for n in names}
    control = reports["replay-control"]
    for report in reports.values():
        for key in ("state", "opened", "input_hashes"):
            assert report[key] == control[key], key
    shots = [line.split() for line in (root / "gui-colony.shots").read_text().splitlines()]
    assert len(shots) == 10 and len({n for n, _ in shots}) == 10
    indices = {n: {x["step"]: x for x in reports[n]["checkpoints"] if x["label"] != "final"} for n in names[1:]}
    for name, index in indices.items():
        assert len(index) == 10, name
        for step, cp in index.items():
            for key in ("memory_sha256", "raw_sha256", "palette_sha256"):
                assert cp[key] == indices["replay-control"][step][key], (name, step, key)
    for name, step in shots:
        equal_image(root / ("gui-colony." + name + ".png"), root / ("replay-zh.cp-" + step + ".png"))
    for a, b in zip(control["checkpoints"], reports["neg-noatlas"]["checkpoints"]):
        assert a["step"] == b["step"]
        equal_image(png_for(root, "replay-control", a), png_for(root, "neg-noatlas", b))
    selected_step = int(dict(shots)["ship-orders"])
    for a, b in zip(reports["replay-zh"]["checkpoints"], reports["baseline-v59"]["checkpoints"]):
        assert a["step"] == b["step"]
        box = ImageChops.difference(Image.open(png_for(root, "replay-zh", a)).convert("RGB"), Image.open(png_for(root, "baseline-v59", b)).convert("RGB")).getbbox()
        if a["step"] == selected_step:
            assert box and 320 <= box[0] and 48 <= box[1] and box[2] <= 640 and box[3] <= 628, box
        else:
            assert box is None, (a["step"], box)
    sources = [e for e in reports["replay-zh"]["events"] if e.get("stage") == "source" and e.get("items") == expected_items and e["step"] <= selected_step]
    assert sources, "缺十四列原版來源"
    source = sources[-1]
    assert source["entry_ip"] == "0D21:00C6" and source["source_linear"] == 175684
    assert source["safe"] == [80, 12, 160, 157] and source["font_px"] == 21
    cp = indices["replay-zh"][selected_step]
    assert any(x.get("candidate_id") == source["candidate_id"] and x.get("applied") for x in cp["lines"])
    assert any(e.get("candidate_id") == source["candidate_id"] and e.get("stage") == "active" and source["step"] <= e["step"] <= selected_step for e in reports["replay-zh"]["events"])
    zh_image = Image.open(png_for(root, "replay-zh", cp)).convert("RGB")
    en_image = Image.open(png_for(root, "replay-control", indices["replay-control"][selected_step])).convert("RGB")
    palette_path = root / ("replay-control.cp-" + str(selected_step) + ".pal")
    palette = palette_path.read_bytes()
    assert len(palette) == 768 and max(palette) <= 63
    assert sha(palette_path) == cp["palette_sha256"]
    def rgb(index):
        return tuple(v << 2 | v >> 4 for v in palette[index * 3:index * 3 + 3])
    for line, layer in zip(layout["original_lines"], layout["layers"]):
        y = line["Box"]["Min"]["Y"] * 4
        rect = (320, y, 640, y + 24)
        assert ImageChops.difference(zh_image.crop(rect), en_image.crop(rect)).getbbox(), line["Text"]
        if layer == 1:
            colors = zh_image.crop(rect).getcolors(320 * 24)
            assert colors and any(color == rgb(8) for _, color in colors), "停用色丟失"
            assert all(color not in (rgb(68), rgb(149)) for _, color in colors), "停用列變可用色"
    seed = "d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77"
    for name in ("scratch", "replay-zh-save", "replay-control-save", "neg-noatlas-save", "baseline-v59-save"):
        saves = sorted((root / name).glob("COLONY*.SAV"))
        assert [s.name for s in saves] == ["COLONY03.SAV"] and sha(saves[0]) == seed, name
    return {"result": "PASS", "inputs_sha256": sha(root / "gui-colony.inputs.json"),
            "final_step": control["state"]["steps"], "final_memory_sha256": control["state"]["memory_sha256"],
            "gui_images_exact": 10, "original_checkpoints_equal": 10,
            "verified_fields": [{"candidate_id": source["candidate_id"], "shown": source["shown"], "safe": source["safe"]}],
            "scope": "只驗十四列船隻命令及關閉恢復；同文列不因此取得唯一原始來源"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--layout", type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game / n).is_file() for n in ORIGINALS):
        print("SKIP：缺合法原版輸入")
        return 77
    try:
        proof = check(a.game, a.reports, a.layout)
    except (AssertionError, OSError, KeyError, ValueError, TypeError) as error:
        print("FAIL：" + str(error))
        return 1
    print(json.dumps(proof, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
