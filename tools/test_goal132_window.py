#!/usr/bin/env python3
"""對正式標題驗收器做來源、記憶體、字模、像素與 ESC 篡改負例。"""

import argparse
import copy
import json
from pathlib import Path
import tempfile

from PIL import Image

from check_goal132_window import KEY, check, check_exit, check_gui


EXTENSIONS = ("json", "memory", "final.idx", "final.pal", "final.png")


def clone(prefix, target):
    for ext in EXTENSIONS:
        src = Path(str(prefix) + "." + ext).resolve()
        if not src.is_file():
            raise ValueError(f"缺收據：{src}")
        Path(str(target) + "." + ext).symlink_to(src)


def replace(prefix, ext, data):
    target = Path(str(prefix) + "." + ext)
    target.unlink()
    target.write_bytes(data)


def must_reject(name, action):
    try:
        action()
    except ValueError:
        print(name, "PASS：拒絕篡改")
        return
    raise AssertionError(f"{name}：錯誤收據未被拒絕")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", type=Path, required=True)
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--mask", type=Path, required=True)
    p.add_argument("--full-live", type=Path, required=True)
    p.add_argument("--full-control", type=Path, required=True)
    p.add_argument("--gui-prefix", type=Path, required=True)
    args = p.parse_args()
    mask = json.loads(args.mask.read_text())
    check(args.live, args.control, mask)
    check_exit(args.full_live, args.full_control)
    check_gui(args.gui_prefix, args.live)
    with tempfile.TemporaryDirectory(prefix="goal132-window-") as temp:
        temp = Path(temp)
        paths = {}
        for name in ("live", "control", "full_live", "full_control"):
            target = temp / name
            clone(getattr(args, name), target)
            paths[name] = target

        def active():
            return check(paths["live"], paths["control"], mask)

        live = json.loads(Path(str(args.live) + ".json").read_text())
        bad = copy.deepcopy(live)
        next(event for event in bad["events"] if event.get("candidate_id") == KEY and
             event.get("stage") == "active")["read_count"] = 31
        replace(paths["live"], "json", json.dumps(bad).encode())
        must_reject("讀字數", active)
        replace(paths["live"], "json", json.dumps(live).encode())

        bad = bytearray(Path(str(args.live) + ".memory").read_bytes())
        bad[0] ^= 1
        replace(paths["live"], "memory", bad)
        must_reject("原版 RAM", active)
        paths["live"].with_suffix(".memory").unlink()
        paths["live"].with_suffix(".memory").symlink_to(Path(str(args.live) + ".memory").resolve())

        bad_mask = dict(mask)
        bad_mask["font_size"] = 38
        must_reject("字級", lambda: check(paths["live"], paths["control"], bad_mask))

        screenshot = Image.open(str(args.live) + ".final.png").convert("RGB")
        r, g, b = screenshot.getpixel((0, 0))
        screenshot.putpixel((0, 0), (r ^ 1, g, b))
        target = Path(str(paths["live"]) + ".final.png")
        target.unlink()
        screenshot.save(target)
        must_reject("安全區外像素", active)

        full = json.loads(Path(str(args.full_live) + ".json").read_text())
        bad = copy.deepcopy(full)
        bad["events"] = [event for event in bad["events"]
                         if not (event.get("candidate_id") == KEY and event.get("stage") == "expired")]
        replace(paths["full_live"], "json", json.dumps(bad).encode())
        must_reject("ESC 失效事件", lambda: check_exit(paths["full_live"], paths["full_control"]))

        gui = temp / "gui"
        for ext in ("json", "inputs.json"):
            Path(str(gui) + "." + ext).symlink_to(Path(str(args.gui_prefix) + "." + ext).resolve())
        shot = Image.open(str(args.gui_prefix) + ".options.png").convert("RGB")
        r, g, b = shot.getpixel((300, 200))
        shot.putpixel((300, 200), (r ^ 1, g, b))
        shot.save(str(gui) + ".options.png")
        must_reject("現場截圖", lambda: check_gui(gui, args.live))
    print("goal132-window：六項篡改負例 PASS")


if __name__ == "__main__":
    main()
