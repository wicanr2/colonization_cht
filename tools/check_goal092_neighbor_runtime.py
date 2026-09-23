#!/usr/bin/env python3
"""獨立驗證右側旗卡輸入相位及 Ebitengine 原版控制畫面。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
SOURCE_SHA = "e8117aa5df32811e2ae60f23b126fc9904b5a6af17bff02d3dcb6636cadb8d57"
RIGHT_INDEXED = "c867bee2f4c5b7a0af07415d68bccb8d028c905fba53d830b01bfb300672af74"
RIGHT_CANVAS = "9e2be3fc35e842afbb03b128a7fedce353f3874d60f0c2101de79b75a366a87b"
LEFT_CANVAS = "2e005b93f811c7e0eb557eb68d1f5c1721caf027e5f32220c3c62195e7c9100b"
NAME_CANVAS = "4182cf7454d507e9dda76e4d81bde65ded7508314c5c518892508f8cddfb1b37"
NAME_INDEXED = "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e"
SAFES = {"upper": (225, 12, 290, 24), "lower": (225, 83, 290, 96)}
EXPECTED = {
    "hover": (("base", 46_000_000, [255, 50, 0], (0, 0), RIGHT_CANVAS),
              ("upper", 47_000_000, [255, 18, 0], (24, 0), RIGHT_CANVAS),
              ("lower", 48_000_000, [255, 90, 0], (0, 25), RIGHT_CANVAS),
              ("away", 49_000_000, [16, 16, 0], (0, 0), RIGHT_CANVAS)),
    "press": (("base", 46_000_000, [255, 50, 0], (0, 0), RIGHT_CANVAS),
              ("target", 47_000_000, [255, 50, 0], (0, 0), RIGHT_CANVAS),
              ("pressed", 48_000_000, [255, 50, 1], (0, 0), RIGHT_CANVAS),
              ("released", 49_000_000, [255, 50, 0], (0, 0), RIGHT_CANVAS)),
    "back": (("base", 46_000_000, [255, 50, 0], (0, 0), RIGHT_CANVAS),
             ("target", 47_000_000, [156, 50, 0], (0, 0), RIGHT_CANVAS),
             ("pressed", 48_000_000, [156, 50, 1], (165, 201), LEFT_CANVAS),
             ("released", 49_000_000, [156, 50, 0], (165, 201), LEFT_CANVAS)),
    "finish": (("base", 46_000_000, [255, 50, 0], (0, 0), RIGHT_CANVAS),
               ("target", 47_000_000, [65, 184, 0], (0, 0), RIGHT_CANVAS),
               ("pressed", 48_000_000, [65, 184, 1], (0, 0), RIGHT_CANVAS),
               ("released", 49_000_000, [65, 184, 0], (763, 816), NAME_CANVAS),
               ("settled", 55_000_000, [65, 184, 0], (763, 816), NAME_CANVAS)),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def delta(left, right, rect):
    x0, y0, x1, y1 = rect
    return sum(left[y * 320 + x] != right[y * 320 + x]
               for y in range(y0, y1) for x in range(x0, x1))


def load(path):
    raw = path.read_bytes()
    return raw, json.loads(raw)


def verify_frames(scenario, report):
    frames = report["frames"]
    require(len(frames) == (55 if scenario == "finish" else 18),
            "逐幀數量不符：" + scenario)
    require(all(frames[i]["step"] < frames[i + 1]["step"]
                for i in range(len(frames) - 1)), "逐幀步數未遞增：" + scenario)
    samples = report["samples"]
    groups = [frames[i:i + 6] for i in range(0, len(frames), 6)]
    for group_index, (name, _, mouse, _, _) in enumerate(EXPECTED[scenario][1:]):
        group = groups[group_index]
        require(all(frame["mouse"] == mouse for frame in group),
                "逐幀滑鼠狀態不符：" + scenario + "/" + name)
        if (scenario == "hover" or (scenario == "press" and name != "pressed") or
                (scenario == "back" and name == "target") or
                (scenario == "finish" and name in ("target", "pressed"))):
            require(all(frame["canvas_sha256"] == samples[name]["canvas_sha256"]
                        and frame["indexed_sha256"] == samples[name]["indexed_sha256"]
                        for frame in group), "逐幀穩定相位不符：" + scenario + "/" + name)
    if scenario == "press":
        group = groups[1]
        require(group[0]["canvas_sha256"] == RIGHT_CANVAS
                and group[1]["canvas_sha256"] != RIGHT_CANVAS
                and all(frame["canvas_sha256"] == RIGHT_CANVAS for frame in group[2:])
                and all(frame["indexed_sha256"] == RIGHT_INDEXED for frame in group),
                "再點右卡的短暫底層重繪相位不符")
    if scenario == "back":
        group = groups[1]
        require(group[0]["canvas_sha256"] == RIGHT_CANVAS
                and group[1]["canvas_sha256"] not in (RIGHT_CANVAS, LEFT_CANVAS)
                and all(frame["canvas_sha256"] == LEFT_CANVAS for frame in group[2:])
                and all(frame["indexed_sha256"] == samples["pressed"]["indexed_sha256"]
                        for frame in group[1:])
                and all(frame["canvas_sha256"] == LEFT_CANVAS and
                        frame["indexed_sha256"] == samples["released"]["indexed_sha256"]
                        for frame in groups[2]), "切回左卡的兩階段重繪不符")
    if scenario == "finish":
        group = groups[2]
        require(group[0]["canvas_sha256"] == RIGHT_CANVAS
                and group[1]["canvas_sha256"] not in (RIGHT_CANVAS, NAME_CANVAS)
                and group[2]["canvas_sha256"] == group[1]["canvas_sha256"]
                and group[3]["canvas_sha256"] not in (RIGHT_CANVAS, NAME_CANVAS)
                and group[4]["canvas_sha256"] == group[3]["canvas_sha256"]
                and group[5]["canvas_sha256"] == NAME_CANVAS
                and [frame["opened_count"] for frame in group] == [51, 52, 52, 52, 53, 53]
                and all(frame["canvas_sha256"] == NAME_CANVAS and
                        frame["indexed_sha256"] == NAME_INDEXED and
                        frame["opened_count"] == 53
                        for frame in frames[18:]), "選國離頁的載入／穩定相位不符")


def verify_png(reports, sample):
    payload = json.loads((reports / f"finish-{sample}.preview.json").read_text())
    require(payload["prototype"] is True and payload["layers"] == [] and
            payload["scenario"] == "finish" and payload["sample"] == sample and
            payload["source_receipt_sha256"] == sha((reports / "finish-a.json").read_bytes()),
            "Ebitengine 控制資料不符：" + sample)
    indexed = base64.b64decode(payload["indexed"], validate=True)
    palette = base64.b64decode(payload["palette"], validate=True)
    require(len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63,
            "控制資料的原版影像大小不符：" + sample)
    source = reports / f"finish-a.{sample}"
    require(indexed == Path(str(source) + ".idx").read_bytes() and
            palette == Path(str(source) + ".pal").read_bytes(),
            "Ebitengine 控制資料不是原版快照：" + sample)
    colors = [tuple((v << 2) | (v >> 4) for v in palette[i * 3:i * 3 + 3])
              for i in range(256)]
    expected = Image.new("RGB", (320, 200))
    expected.putdata([colors[index] for index in indexed])
    expected = expected.resize((1280, 800), Image.Resampling.NEAREST)
    png = reports / f"finish-{sample}.png"
    with Image.open(png) as image:
        actual = image.convert("RGB")
    require(actual.size == (1280, 800) and ImageChops.difference(actual, expected).getbbox() is None,
            "Ebitengine 控制圖不是原版四倍最近鄰：" + sample)
    return sha(png.read_bytes())


def verify(args):
    source_raw, source = load(args.source)
    require(sha(source_raw) == SOURCE_SHA and source["result"] == "PASS" and
            source["input_sha256"] == INPUT_SHA and
            source["indexed_sha256"] == RIGHT_INDEXED,
            "目標091來源收據不符")
    require(sha(args.inputs.read_bytes()) == INPUT_SHA, "真視窗輸入指紋不符")
    baseline = (args.reports / "hover-a.base.idx").read_bytes()
    require(len(baseline) == 64000 and sha(baseline) == RIGHT_INDEXED,
            "右卡基準索引畫面不符")
    receipt_hashes = {}
    for scenario, expected in EXPECTED.items():
        receipts = {variant: load(args.reports / f"{scenario}-{variant}.json")
                    for variant in ("a", "b", "control")}
        raw_a, a = receipts["a"]
        raw_b, b = receipts["b"]
        raw_control, control = receipts["control"]
        require(raw_a == raw_b and not a["control"] and control["control"],
                "雙次獨立冷啟動收據不符：" + scenario)
        receipt_hashes[scenario] = {"observed": sha(raw_a), "control": sha(raw_control)}
        for variant, (_, report) in receipts.items():
            require(report["version"] == "goal092-neighbor-runtime-v1"
                    and report["scenario"] == scenario
                    and report["input_sha256"] == INPUT_SHA
                    and report["input_hashes"].get("WOODPANL.PIK") ==
                    "0858856ad5b5dd0b6ab8e7a8f815fa602a9cf0237d8d323cd2b5ca141b32bc69"
                    and len(report["input_hashes"]) == 7
                    and report["baseline_indexed_sha256"] == RIGHT_INDEXED
                    and report["address_space"] ==
                    "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas"
                    and set(report["samples"]) == {row[0] for row in expected}
                    and report["state"]["steps"] == expected[-1][1]
                    and not report["state"]["exited"] and not report["state"]["halted"]
                    and len(report["opened"]) == (53 if scenario == "finish" else 51),
                    "原版版本、流程或取樣不符：" + scenario + "/" + variant)
        for field in ("state", "opened", "samples", "input_hashes"):
            require(a[field] == control[field], "逐幀觀測擾動原版：" + scenario + "/" + field)
        require(not control["frames"], "控制組意外啟用逐幀觀測：" + scenario)
        verify_frames(scenario, a)
        for name, step, mouse, intersections, canvas_sha in expected:
            sample = a["samples"][name]
            require(sample["step"] == step and sample["mouse"] == mouse
                    and (sample["intersections"]["upper"],
                         sample["intersections"]["lower"]) == intersections
                    and sample["canvas_sha256"] == canvas_sha
                    and sample["video_mode"] == 0x13
                    and not sample["exited"] and not sample["halted"],
                    "游標或原版畫布狀態不符：" + scenario + "/" + name)
            snapshots = []
            for variant in ("a", "b", "control"):
                prefix = args.reports / f"{scenario}-{variant}.{name}"
                indexed = Path(str(prefix) + ".idx").read_bytes()
                canvas = Path(str(prefix) + ".canvas").read_bytes()
                palette = Path(str(prefix) + ".pal").read_bytes()
                require(len(indexed) == len(canvas) == 64000 and len(palette) == 768
                        and sha(indexed) == sample["indexed_sha256"]
                        and sha(canvas) == sample["canvas_sha256"]
                        and sha(palette) == sample["palette_sha256"],
                        "畫布／索引／色盤與收據不符：" + scenario + "/" + name)
                snapshots.append((indexed, canvas, palette))
            require(snapshots[0] == snapshots[1] == snapshots[2],
                    "雙次／控制組原版畫面不符：" + scenario + "/" + name)
            indexed = snapshots[0][0]
            require((delta(baseline, indexed, SAFES["upper"]),
                     delta(baseline, indexed, SAFES["lower"])) == intersections,
                    "右卡逐欄安全區差分不符：" + scenario + "/" + name)
        if scenario == "finish":
            require(a["opened"][-3:] == ["NATIONS.PIK", "WOODPANL.PIK", "GAME.TXT"]
                    and a["samples"]["released"]["indexed_sha256"] == NAME_INDEXED
                    and a["samples"]["settled"]["indexed_sha256"] == NAME_INDEXED
                    and a["samples"]["released"]["palette_sha256"] !=
                    a["samples"]["base"]["palette_sha256"],
                    "選國後的原版新畫面／開檔未成立")
    png_hashes = {name: verify_png(args.reports, name) for name in ("base", "settled")}
    result = {"result": "PASS", "scope": "goal092 original runtime and first post-nation screen",
              "input_sha256": INPUT_SHA, "source_receipt_sha256": SOURCE_SHA,
              "reports": receipt_hashes, "ebitengine_png_sha256": png_hashes,
              "limits": "新姓名畫面文字來源、輸入與正式中文覆蓋尚未取證"}
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "收據輸出目錄不存在或擁有者不符")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args())


if __name__ == "__main__":
    main()
