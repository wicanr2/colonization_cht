#!/usr/bin/env python3
"""核對第一張國家旗卡 A 版與同輸入英文、舊十五欄畫面。"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


IDS = ("NAMES.TXT:0x000008EA", "LABELS.TXT:0x000008F2")
SAFES = ((500, 48, 760, 96), (500, 332, 760, 384))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(out, name):
    return json.loads((out / f"{name}.json").read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="核對真視窗新收據與同輸入重播")
    args = parser.parse_args()
    out = args.out
    names = (("live-card", "live-baseline", "live-control") if args.live else
             ("card43", "baseline43", "control43"))
    chinese, baseline, control = (load(out, name)
                                  for name in names)
    expected_frame = ("21461c4a6c05ac7d780951753b0ec8533db58e4e1ca69e72ff3e8cad05efc26c"
                      if args.live else
                      "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835")
    for report in (chinese, baseline, control):
        require(report["state"] == control["state"], "原版 CPU／RAM／時間狀態不同")
        require(report["opened"] == control["opened"], "原版開檔序列不同")
        require(report["state"]["frame_sha256"] == expected_frame, "原版索引畫面不符")
    for suffix in ("idx", "pal"):
        hashes = {digest(out / f"{name}.final.{suffix}") for name in names}
        require(len(hashes) == 1, f"原版 {suffix} 不同")
    card_events = [e for e in chinese["events"] if e.get("candidate_id") in IDS
                   and e.get("accepted")]
    require(len(card_events) == 2 and {e["candidate_id"] for e in card_events} == set(IDS),
            "兩欄原版印字事件不完整")
    require([e["changed_pixels"] for e in card_events] == [123, 156],
            "兩欄原版畫素差分不符")
    require(not any(e.get("candidate_id") in IDS for e in baseline["events"]),
            "十五欄基線誤裝旗卡監看")
    require(len(chinese["frames"]) == len(baseline["frames"]), "舊欄位逐幀數不同")
    for index, (new_frame, old_frame) in enumerate(zip(chinese["frames"], baseline["frames"])):
        old_lines = old_frame["lines"]
        new_old_lines = [line for line in new_frame["lines"]
                         if line["candidate_id"] not in IDS]
        require(new_old_lines == old_lines, f"第 {index} 幀舊十五欄回歸")
    lines = {line["candidate_id"]: line for line in chinese["checkpoints"][-1]["lines"]}
    require(all(lines[key]["applied"] and lines[key]["accepted_events"] == 1 for key in IDS),
            "旗卡兩欄未各自正式套用一次")
    with Image.open(out / f"{names[0]}.final.png") as source:
        chinese_image = source.convert("RGBA")
    with Image.open(out / f"{names[1]}.final.png") as source:
        baseline_image = source.convert("RGBA")
    require(chinese_image.size == baseline_image.size == (1280, 800), "輸出尺寸不符")
    a, b = chinese_image.load(), baseline_image.load()
    changed = [0, 0]
    for y in range(800):
        for x in range(1280):
            if a[x, y] == b[x, y]:
                continue
            owners = [i for i, (x0, y0, x1, y1) in enumerate(SAFES)
                      if x0 <= x < x1 and y0 <= y < y1]
            require(len(owners) == 1, f"旗卡安全區外像素遭改動：{x},{y}")
            changed[owners[0]] += 1
    require(all(count > 0 for count in changed), "兩欄畫素未變")
    negative_results = {}
    cases = (() if args.live else
             (("missing-upper", (False, True)),
              ("duplicate-lower", (True, False)),
              ("wrong-size-lower", (True, False)),
              ("missing-upper-font", (False, True))))
    for name, expected_applied in cases:
        negative = load(out, name)
        require(negative["state"] == control["state"] and
                negative["opened"] == control["opened"], name + " 改變原版狀態")
        negative_lines = {line["candidate_id"]: line
                          for line in negative["checkpoints"][-1]["lines"]}
        require(tuple(negative_lines[key]["applied"] for key in IDS) == expected_applied,
                name + " 未逐欄回退")
        with Image.open(out / f"{name}.final.png") as source:
            negative_image = source.convert("RGBA")
        require(negative_image.size == (1280, 800), name + " 畫面尺寸不符")
        pixels = negative_image.load()
        for y in range(800):
            for x in range(1280):
                owner = next((i for i, (x0, y0, x1, y1) in enumerate(SAFES)
                              if x0 <= x < x1 and y0 <= y < y1), None)
                expected = a[x, y] if owner is not None and expected_applied[owner] else b[x, y]
                require(pixels[x, y] == expected, f"{name} 畫素回退錯誤：{x},{y}")
        negative_results[name] = {"applied": expected_applied,
                                  "png_sha256": digest(out / f"{name}.final.png")}
    if args.live:
        with Image.open(out / "live-card.nation.png") as source:
            capture = source.convert("RGBA")
        require(capture.size == (1280, 800), "真視窗擷取尺寸不符")
        for y in range(800):
            for x in range(1280):
                require(capture.getpixel((x, y)) == a[x, y],
                        f"真視窗擷取與同畫面最終合成不同：{x},{y}")
    receipt = {"result": "PASS", "scope": ("live Ebitengine window plus same-input replays"
                                             if args.live else
                                             "recorded-input Ebitengine replay at step 43000000"),
               "changed_pixels_by_field": dict(zip(IDS, changed)),
               "negative_cases": negative_results,
               "original_state_sha256": control["state"]["memory_sha256"],
               "chinese_png_sha256": digest(out / f"{names[0]}.final.png"),
               "baseline_png_sha256": digest(out / f"{names[1]}.final.png"),
               "control_png_sha256": digest(out / f"{names[2]}.final.png")}
    output = out / ("verify-live-card-a.json" if args.live else "verify-card-a.json")
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
