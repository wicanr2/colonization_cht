#!/usr/bin/env python3
"""獨立核對第一張旗卡游標、左鍵與相鄰旗卡切換的原版收據。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
SOURCE_SHA = "cc4221d50718fe981a8836672f7ee8eda07cb6b2fbc95894b5cacc3d0f63ec86"
BASE_CANVAS_SHA = "2e005b93f811c7e0eb557eb68d1f5c1721caf027e5f32220c3c62195e7c9100b"
BASE_INDEXED_SHA = "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835"
SAFES = {"upper": (125, 12, 190, 24), "lower": (125, 83, 190, 96)}
EXPECTED = {
    "hover": (
        ("settled", 43_000_000, [55, 83, 0], {"upper": 0, "lower": 0}, True),
        ("upper", 44_000_000, [156, 18, 0], {"upper": 24, "lower": 0}, True),
        ("lower", 45_000_000, [156, 90, 0], {"upper": 0, "lower": 24}, True),
        ("away", 46_000_000, [16, 16, 0], {"upper": 0, "lower": 0}, True),
    ),
    "left": (
        ("settled", 43_000_000, [55, 83, 0], {"upper": 0, "lower": 0}, True),
        ("lower", 44_000_000, [156, 90, 0], {"upper": 0, "lower": 24}, True),
        ("pressed", 45_000_000, [156, 90, 1], {"upper": 0, "lower": 24}, True),
        ("released", 46_000_000, [156, 90, 0], {"upper": 0, "lower": 24}, True),
    ),
    "next": (
        ("settled", 43_000_000, [55, 83, 0], {"upper": 0, "lower": 0}, True),
        ("neighbor", 44_000_000, [255, 50, 0], {"upper": 0, "lower": 0}, True),
        ("pressed", 45_000_000, [255, 50, 1], {"upper": 188, "lower": 221}, False),
        ("released", 46_000_000, [255, 50, 0], {"upper": 188, "lower": 221}, False),
    ),
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


def verify(args):
    source_raw, source = load(args.source)
    require(sha(source_raw) == SOURCE_SHA
            and source["version"] == "goal088-nation-background-v1"
            and source["input_sha256"] == INPUT_SHA and not source["control"],
            "目標088來源收據不符")
    require(sha(args.inputs.read_bytes()) == INPUT_SHA, "十六筆正常玩家輸入不符")
    base_indexed = (args.reports / "hover-a.settled.idx").read_bytes()
    base_canvas = (args.reports / "hover-a.settled.canvas").read_bytes()
    require(len(base_indexed) == len(base_canvas) == 64000
            and sha(base_indexed) == BASE_INDEXED_SHA
            and sha(base_canvas) == BASE_CANVAS_SHA,
            "原版第一張旗卡基準畫布不符")
    receipt_hashes = {}
    for scenario, samples in EXPECTED.items():
        paths = {kind: args.reports / f"{scenario}-{kind}.json"
                 for kind in ("a", "b", "control")}
        raw_a, a = load(paths["a"])
        raw_b, b = load(paths["b"])
        raw_control, control = load(paths["control"])
        require(raw_a == raw_b, "雙次冷啟動收據不同：" + scenario)
        receipt_hashes[scenario] = {"observed": sha(raw_a), "control": sha(raw_control)}
        for kind, report in (("a", a), ("b", b), ("control", control)):
            require(report["version"] == "goal089-nation-runtime-v2"
                    and report["scenario"] == scenario
                    and report["control"] is (kind == "control")
                    and report["input_sha256"] == INPUT_SHA
                    and report["input_hashes"] == source["input_hashes"]
                    and report["baseline_indexed_sha256"] == BASE_INDEXED_SHA
                    and report["address_space"] == source["address_space"]
                    and set(report["samples"]) == {row[0] for row in samples}
                    and len(report["opened"]) == 51
                    and report["opened"][-1] == "NATIONS.PIK"
                    and report["state"]["steps"] == 46_000_000
                    and not report["state"]["exited"]
                    and not report["state"]["halted"],
                    "收據版本、輸入或玩家路徑不符：" + scenario + "/" + kind)
        for field in ("state", "opened", "samples", "input_hashes"):
            require(a[field] == control[field], "觀測擾動原版：" + scenario + "/" + field)
        require(not control["frames"] and len(a["frames"]) == 18,
                "逐幀觀測數量不符：" + scenario)
        for position, (name, step, mouse, intersections, baseline_canvas) in enumerate(samples):
            expected_sample = a["samples"][name]
            require(expected_sample["step"] == step and expected_sample["mouse"] == mouse
                    and expected_sample["intersections"] == intersections
                    and expected_sample["video_mode"] == 0x13
                    and expected_sample["opened_count"] == 51
                    and not expected_sample["exited"] and not expected_sample["halted"]
                    and expected_sample["palette_sha256"] == source["state"]["palette_sha256"],
                    "欄位狀態不符：" + scenario + "/" + name)
            snapshots = []
            for kind in ("a", "b", "control"):
                prefix = args.reports / f"{scenario}-{kind}.{name}"
                indexed = Path(str(prefix) + ".idx").read_bytes()
                canvas = Path(str(prefix) + ".canvas").read_bytes()
                require(len(indexed) == len(canvas) == 64000
                        and sha(indexed) == expected_sample["indexed_sha256"]
                        and sha(canvas) == expected_sample["canvas_sha256"],
                        "原版快照與收據不符：" + scenario + "/" + name)
                snapshots.append((indexed, canvas))
            require(snapshots[0] == snapshots[1] == snapshots[2],
                    "雙次／控制組原版快照不同：" + scenario + "/" + name)
            indexed, canvas = snapshots[0]
            require({field: delta(base_indexed, indexed, rect)
                     for field, rect in SAFES.items()} == intersections,
                    "游標或切卡交集點數不符：" + scenario + "/" + name)
            require((canvas == base_canvas) is baseline_canvas,
                    "底層旗卡畫布變化不符：" + scenario + "/" + name)
            if position:
                frames = a["frames"][(position - 1) * 6:position * 6]
                require(len(frames) == 6, "逐幀觀測數量不符：" + scenario + "/" + name)
                for frame_index, frame in enumerate(frames):
                    visible = expected_sample
                    if scenario == "next" and name == "pressed" and frame_index == 0:
                        # 左鍵先被記錄；原版到下一輸出幀才換旗卡，不能假設同幀切換。
                        visible = a["samples"]["neighbor"]
                    require((position * 1_000_000 + 42_000_000)
                            <= frame["step"] < (position * 1_000_000 + 43_000_000)
                            and frame["mouse"] == mouse
                            and frame["intersections"] == visible["intersections"]
                            and frame["indexed_sha256"] == visible["indexed_sha256"]
                            and frame["canvas_sha256"] == visible["canvas_sha256"],
                            "逐幀游標／按鍵狀態不符：" + scenario + "/" + name)
        if scenario == "next":
            require(a["samples"]["pressed"]["canvas_sha256"] ==
                    a["samples"]["released"]["canvas_sha256"],
                    "相鄰旗卡左鍵放開後未保持新畫布")
    receipt = {"result": "PASS", "scope": "goal089 original-only runtime evidence",
               "input_sha256": INPUT_SHA, "source_receipt_sha256": SOURCE_SHA,
               "reports": receipt_hashes,
               "limits": "相鄰旗卡文字來源、正式覆蓋與完整玩家路徑未驗"}
    if args.output:
        require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
                "輸出目錄不存在或擁有者不符")
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    verify(parser.parse_args())


if __name__ == "__main__":
    main()
