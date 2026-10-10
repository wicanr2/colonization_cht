#!/usr/bin/env python3
"""規格052：核對英數候選三側原版狀態及逐畫格顯示差異。只在Docker執行。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
ITEM_ID = "STRING:retained-ascii"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rect(value):
    need(isinstance(value, dict) and set(value) == {"Min", "Max"}, "缺少矩形")
    result = tuple(value[k][axis] for k, axis in (("Min", "X"), ("Min", "Y"), ("Max", "X"), ("Max", "Y")))
    need(all(type(v) is int for v in result) and 0 <= result[0] < result[2] <= 320 and
         0 <= result[1] < result[3] <= 200, "非法安全區")
    return result


def source_key(event):
    return event["complete_step"], event.get("text", event.get("shown")), rect(event["safe"]), event["font_px"]


def compare_images(observed, candidate, lines, observations):
    permitted = Image.new("L", (1280, 800))
    painter = ImageDraw.Draw(permitted)
    regions = []
    for line in lines:
        if line.get("candidate_id") != ITEM_ID or not line.get("applied"):
            continue
        need(source_key(line) in observations, "顯示項沒有當次原版來源")
        bounds = rect(line["safe"])
        scaled = tuple(v * 4 for v in bounds)
        painter.rectangle((scaled[0], scaled[1], scaled[2] - 1, scaled[3] - 1), fill=255)
        regions.append({"safe": list(bounds), "text": line["shown"], "font_px": line["font_px"],
                        "complete_step": line["complete_step"]})
    with Image.open(observed) as a, Image.open(candidate) as b:
        need(a.size == b.size == (1280, 800), "畫面尺寸不同")
        difference = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    red, green, blue = difference.split()
    changed = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    outside = ImageChops.multiply(changed, ImageChops.invert(permitted))
    need(outside.getbbox() is None, f"數字安全區外有差異：{outside.getbbox()}")
    return {"changed_pixels": sum(changed.histogram()[1:]), "difference_bounds": changed.getbbox(),
            "regions": regions, "outside_changed_pixels": 0}


def compare_gui(folder, candidate, report):
    original = json.loads((folder / "gui.json").read_text())
    need(original["state"] == report["state"], "真GUI與重播原版狀態不同")
    command = json.loads((candidate / "command.json").read_text())
    need(command.count("--replay-inputs") == 1, "重播輸入參數不唯一")
    inputs = Path(command[command.index("--replay-inputs") + 1])
    need(inputs.resolve() == (folder / "gui.inputs.json").resolve(), "沒有使用當次GUI實際輸入")
    source_saves = {p.name: sha(p) for p in (folder / "save").iterdir() if p.is_file()}
    replay_saves = {p.name: sha(p) for p in (candidate / "save").iterdir() if p.is_file()}
    need(source_saves == replay_saves, "真GUI與重播存檔不同")
    captures = [json.loads(line) for line in (folder / "gui.capture-attempts.jsonl").read_text().splitlines()]
    checkpoints = {cp["step"]: cp for cp in report["checkpoints"] if cp.get("label", "").startswith("cp-")}
    pictures = []
    for row in (folder / "gui.shots").read_text().splitlines():
        name, raw_step = row.split()
        step = int(raw_step)
        need(step in checkpoints, "真GUI抓圖步數缺少重播檢查點")
        receipt = next((r for r in captures if r["name"] == name and r["aligned"]), None)
        need(receipt is not None and receipt["frame_step"] == step, "真GUI缺少同步抓圖收據")
        with Image.open(folder / ("gui." + name + ".png")) as gui, Image.open(candidate / Path(checkpoints[step]["png"]).name) as replay:
            need(gui.size == replay.size == (1280, 800), "真GUI尺寸不同")
            pixels = gui.convert("RGBA").tobytes()
            need(pixels == replay.convert("RGBA").tobytes(), f"真GUI與重播像素不同：{name}")
            need(hashlib.sha256(pixels).hexdigest() == receipt["canvas_rgba_sha256"] == receipt["capture_rgba_sha256"],
                 "真GUI畫布指紋不同")
        pictures.append({"name": name, "step": step, "rgba_sha256": receipt["canvas_rgba_sha256"]})
    need(len(pictures) >= 3, "真GUI抽樣不足")
    return {"original_state_equal": True, "inputs_sha256": sha(inputs), "pictures": pictures,
            "saves_sha256": source_saves}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("observed", "candidate", "control", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--gui", type=Path)
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file(), "請在Docker內執行")
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
         output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出需為新的workplace檔案")
    folders = [args.observed.resolve(), args.candidate.resolve(), args.control.resolve()]
    reports = [json.loads((p / "run.json").read_text()) for p in folders]
    need(all(r["state"] == reports[0]["state"] for r in reports), "原版完整狀態不同")
    observations = json.loads((folders[1] / "run.retained-ascii.json").read_text())
    need(observations["enabled"] and observations["overflow"] == observations["read_overflow"] == 0,
         "候選未啟用或觀測溢出")
    sources = {source_key(e) for e in observations["events"] if e.get("item_id") == ITEM_ID}
    need(sources, "沒有候選來源")
    file_hashes = {}
    for name in ("run.memory", "run.final.idx", "run.final.pal", "raw.wav"):
        hashes = [sha(p / name) for p in folders]
        need(len(set(hashes)) == 1, f"原版輸出不同：{name}")
        file_hashes[name] = hashes[0]
    saves = [{p.name: sha(p) for p in (folder / "save").iterdir() if p.is_file()} for folder in folders]
    need(saves[0] and saves[0] == saves[1] == saves[2], "存檔不同")
    checkpoints = [{cp["step"]: cp for cp in r["checkpoints"] if cp.get("label", "").startswith("cp-")}
                   for r in reports]
    need(len(checkpoints[0]) >= 3 and all(set(cp) == set(checkpoints[0]) for cp in checkpoints), "檢查點不同或不足")
    pictures = []
    for step in sorted(checkpoints[0]):
        points = [cp[step] for cp in checkpoints]
        for field in ("memory_sha256", "raw_sha256", "palette_sha256"):
            need(len({p[field] for p in points}) == 1, f"檢查點原版資料不同：{step} {field}")
        images = [folder / Path(cp["png"]).name for folder, cp in zip(folders, points)]
        for image, point in zip(images, points):
            need(sha(image.with_suffix(".idx")) == point["raw_sha256"] and
                 sha(image.with_suffix(".pal")) == point["palette_sha256"], "檢查點索引或色盤檔不符")
        native = Image.frombytes("P", (320, 200), images[2].with_suffix(".idx").read_bytes())
        native.putpalette([v << 2 | v >> 4 for v in images[2].with_suffix(".pal").read_bytes()])
        expected = native.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
        with Image.open(images[2]) as original:
            need(original.convert("RGB").tobytes() == expected.tobytes(), "英文控制不是原版像素與字體")
        checked = compare_images(images[0], images[1], points[1]["lines"], sources)
        pictures.append({"step": step, **checked, "image_sha256": [sha(p) for p in images]})
    need(any(p["changed_pixels"] for p in pictures), "候選未產生可見差異")
    result = {"result": "PASS_RETAINED_ASCII_REPLAY", "scope": "Observed single-color main-canvas ASCII only",
              "original_state_equal": True, "original_files_sha256": file_hashes, "saves_sha256": saves[0],
              "report_sha256": [sha(p / "run.json") for p in folders], "checkpoints": pictures}
    if args.gui:
        result["gui"] = compare_gui(args.gui.resolve(), folders[1], reports[1])
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    need(output.stat().st_uid == os.getuid(), "輸出擁有者不同")
    print(result["result"], len(pictures), "checkpoints", sum(p["changed_pixels"] for p in pictures), "changed pixels")


if __name__ == "__main__":
    main()
