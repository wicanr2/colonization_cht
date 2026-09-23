#!/usr/bin/env python3
"""獨立核對相鄰旗卡精確印字收據；原版像素只留 workplace。"""

import argparse
import hashlib
import json
from pathlib import Path


FIELDS = (
    ("upper", (225, 12, 290, 24), (242, 15, 267, 19)),
    ("lower", (225, 83, 290, 96), (235, 87, 275, 92)),
)
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rect_bytes(canvas, rect):
    x0, y0, x1, y1 = rect
    return b"".join(canvas[y * 320 + x0:y * 320 + x1] for y in range(y0, y1))


def check(reports):
    raw = [(reports / f"goal091-{variant}.json").read_bytes()
           for variant in ("a", "b", "control")]
    a, b, control = (json.loads(item) for item in raw)
    require(raw[0] == raw[1] and not a["control"] and control["control"]
            and a["input_sha256"] == control["input_sha256"] == INPUT_SHA
            and a["input_hashes"] == control["input_hashes"]
            and a["state"] == control["state"] and a["samples"] == control["samples"]
            and a["precise_snapshots"] == control["precise_snapshots"]
            and a["opened"] == control["opened"]
            and not a["read_truncated"] and not a["write_truncated"]
            and not b["read_truncated"] and not b["write_truncated"],
            "雙次重播或無監看控制不同狀態")
    expected_steps = {"before-upper": 44123301, "after-upper": 44129564,
                      "before-lower": 44133138, "after-lower": 44142300}
    require(set(a["precise_snapshots"]) == set(expected_steps), "精確截點不完整")
    final = (reports / "goal091-a.final.idx").read_bytes()
    palette = (reports / "goal091-a.final.pal").read_bytes()
    require(len(final) == 64000 and sha(final) == a["state"]["indexed_sha256"]
            and len(palette) == 768 and sha(palette) == a["state"]["palette_sha256"]
            and max(palette) <= 63 and palette[:3] == b"\0\0\0", "最終索引／色盤不符")
    require((reports / "goal091-a.after-lower.canvas").read_bytes()
            == (reports / "goal091-a.45000000.canvas").read_bytes(), "印字後畫布未穩定")
    result_fields = {}
    for name, safe, expected_bbox in FIELDS:
        captures = {}
        for moment in ("before", "after"):
            label = f"{moment}-{name}"
            sample = a["precise_snapshots"][label]
            require(sample["step"] == expected_steps[label], "印字截點不符：" + label)
            captures[moment] = (reports / f"goal091-a.{label}.canvas").read_bytes()
            require(len(captures[moment]) == 64000
                    and sha(captures[moment]) == sample["canvas_sha256"],
                    "畫布雜湊不符：" + label)
            for variant in ("b", "control"):
                other = (reports / f"goal091-{variant}.{label}.canvas").read_bytes()
                require(rect_bytes(other, safe) == rect_bytes(captures[moment], safe),
                        "原版雙次／無監看畫布不一致：" + label)
        before, after = captures["before"], captures["after"]
        changed = [(i % 320, i // 320) for i, (left, right) in
                   enumerate(zip(before, after)) if left != right]
        require(changed, "沒有原文差分：" + name)
        bbox = (min(x for x, _ in changed), min(y for _, y in changed),
                max(x for x, _ in changed), max(y for _, y in changed))
        require(bbox == expected_bbox and all(safe[0] <= x < safe[2] and
                safe[1] <= y < safe[3] for x, y in changed), "原文差分超出預期：" + name)
        require(rect_bytes(after, safe) == rect_bytes(final, safe),
                "最終索引畫面與印字結果不符：" + name)
        background = rect_bytes(before, safe)
        require(len(set(background)) >= 40, "底圖紋理不足：" + name)
        result_fields[name] = {"safe": safe, "original_bbox": bbox,
                               "changed_pixels": len(changed),
                               "background_palette_indices": len(set(background)),
                               "background_sha256": sha(background)}
    return {"result": "PASS", "prototype_only": True,
            "source_receipt_sha256": sha(raw[0]),
            "control_receipt_sha256": sha(raw[2]),
            "input_sha256": INPUT_SHA, "indexed_sha256": sha(final),
            "palette_sha256": sha(palette), "fields": result_fields}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.output.parent.is_dir(), "輸出目錄不存在")
    result = check(args.reports)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
