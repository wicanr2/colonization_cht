#!/usr/bin/env python3
"""核對四國介紹印字前畫布；原版畫素與完整收據僅存 workplace。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


NATIONS = ("england", "france", "spain", "netherlands")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(old_dir, new_dir):
    rows = []
    backgrounds = set()
    for nation in NATIONS:
        old = json.loads((old_dir / f"{nation}-a.json").read_bytes())
        new = json.loads((new_dir / f"{nation}.json").read_bytes())
        require({key: value for key, value in new.items() if key != "preprint"} == old,
                f"{nation}: 新觀測擾動原版狀態或事件")
        require(set(new["preprint"]) == {"first", "second"},
                f"{nation}: 沒有取得兩頁印前底圖")
        for phase, sample in (("first", "60m"), ("second", "70m")):
            receipt = new["preprint"][phase]
            before = (new_dir / f"{nation}.{phase}.pre.canvas").read_bytes()
            after = (new_dir / f"{nation}.{sample}.canvas").read_bytes()
            palette = (new_dir / f"{nation}.{sample}.pal").read_bytes()
            writer = new["writers"][f"{phase}/0D21:012C"]
            require(len(before) == len(after) == 64000 and len(palette) == 768 and
                    max(palette) <= 63 and sha(before) == receipt["canvas_sha256"] and
                    sha(after) == new["samples"][sample]["canvas_sha256"] and
                    sha(palette) == new["samples"][sample]["palette_sha256"] and
                    receipt["step"] == writer["first_step"] and
                    receipt["writer_ip"] == "0D21:012C",
                    f"{nation}/{phase}: 畫布、色盤或首筆印字相位不符")
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            x0, y0, x1, y1 = writer["bbox"]
            require(changed and len(changed) == writer["count"] and
                    all(x0 <= i % 320 < x1 and y0 <= i // 320 < y1 for i in changed),
                    f"{nation}/{phase}: 印前底圖到穩定畫面的差分不只原版印字")
            backgrounds.add(sha(before))
            rows.append({"nation": nation, "phase": phase,
                         "preprint_canvas_sha256": sha(before),
                         "final_canvas_sha256": sha(after),
                         "palette_sha256": sha(palette),
                         "first_writer_step": receipt["step"],
                         "changed_pixels": len(changed), "bbox": writer["bbox"]})
    require(len(rows) == 8, "不是四國八頁")
    return {"result": "PASS", "scope": "四國八節正常玩家路徑的首字印前原始畫布；不含中文覆蓋",
            "same_background_across_pages": len(backgrounds) == 1,
            "background_sha256s": sorted(backgrounds), "pages": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
            "輸出目錄不存在或擁有者不符")
    result = verify(args.old, args.new)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS：四國八頁印前底圖；共 {len(result['background_sha256s'])} 種底圖")


if __name__ == "__main__":
    main()
