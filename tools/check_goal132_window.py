#!/usr/bin/env python3
"""獨立核對遊戲選項標題 A 的同輸入前端收據；原版缺失回 SKIP 77。"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


KEY = "GAME.TXT:0x000004CD"
INPUT_SHA = "dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98"
PRE_SAFE_SHA = "358729d7a05203a18f1ea4882d5db540e90ed7edf83af3e11dc20f676e978e04"
AFTER_SAFE_SHA = "4cc2db436024b492e5eb7440dad60bb768e6c16e9cb2dcb16eddee0b2da83ca3"
SAFE = (260, 176, 1012, 236)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_bytes(indexed):
    need(len(indexed) == 64000, "原版索引畫面長度不符")
    return b"".join(indexed[y * 320 + 65:y * 320 + 253] for y in range(44, 59))


def load(prefix):
    data = json.loads(Path(str(prefix) + ".json").read_text())
    return data, {
        ext: Path(str(prefix) + "." + ext).read_bytes()
        for ext in ("memory", "final.idx", "final.pal")
    }, Image.open(str(prefix) + ".final.png").convert("RGB")


def check(active_live, active_control, mask):
    live, live_files, live_png = load(active_live)
    control, control_files, control_png = load(active_control)
    need(live["control"] is False and control["control"] is True and
         live["state"] == control["state"] and live["opened"] == control["opened"] and
         live["input_hashes"] == control["input_hashes"] and
         live_files == control_files and live["state"]["steps"] == 1280000000,
         "中文與英文控制的原版狀態、輸入或完整記憶體不同")
    need(live_png.size == control_png.size == (1280, 800), "正式視窗尺寸不符")
    need(sha(safe_bytes(live_files["final.idx"])) == AFTER_SAFE_SHA,
         "原版印後標題安全區不同")
    need(mask["candidate_id"] == KEY and mask["font_size"] == 34 and
         (mask["width"], mask["height"]) == (222, 32) and
         len(base64.b64decode(mask["alpha"], validate=True)) == 222 * 32 and
         mask["catalog_sha256"] == live["catalog_sha256"] and
         mask["font_sha256"] == live["font_sha256"],
         "A／34px 字模來源或尺寸不符")
    events = [event for event in live["events"] if event.get("candidate_id") == KEY]
    stages = [event["stage"] for event in events]
    need(stages == ["source-candidate", "source", "active"],
         "缺當次來源、逐字輸出或 VGA 同步事件")
    need(events[0]["safe_sha256"] == PRE_SAFE_SHA and events[0]["video_mode"] == 19 and
         events[0]["source_linear"] == 0x2AC78 and
         events[1]["entry_ip"] == "0D21:00C6" and
         events[1]["source_linear"] == 0x2AC78 and
         events[2]["read_count"] == 32 and events[2]["changed_pixels"] == 319 and
         events[0]["step"] <= events[1]["step"] < events[2]["step"],
         "標題事件時間序、局部底圖或畫布改色不符")
    records = [next((line for line in frame["lines"] if line["candidate_id"] == KEY), None)
               for frame in live["frames"]]
    need(len(records) == len(control["frames"]) and all(record is not None for record in records),
         "正式標題逐幀紀錄不完整")
    need(any(record["reason"] == "waiting-screen" for record in records) and
         any(record["applied"] for record in records) and
         records[-1]["applied"] and
         all(not record["applied"] for frame, record in zip(live["frames"], records)
             if frame["step"] < events[2]["step"]),
         "VGA 同步前套用或同步後沒有中文")
    outside = live_png.copy()
    outside.paste(control_png.crop(SAFE), SAFE)
    need(ImageChops.difference(outside, control_png).getbbox() is None and
         ImageChops.difference(live_png, control_png).getbbox() is not None,
         "中文像素越出標題安全區或完全未繪製")
    return {"result": "PASS", "state_sha256": live["state"]["memory_sha256"],
            "source_step": events[1]["step"], "active_step": events[2]["step"],
            "applied_frames": sum(record["applied"] for record in records),
            "last_frame_reason": records[-1]["reason"]}


def check_exit(full_live, full_control):
    live, live_files, live_png = load(full_live)
    control, control_files, control_png = load(full_control)
    need(live["control"] is False and control["control"] is True and
         live["state"] == control["state"] and live["opened"] == control["opened"] and
         live["input_hashes"] == control["input_hashes"] and live_files == control_files and
         live["state"]["steps"] == 1350000000 and
         len(live["frames"]) == len(control["frames"]),
         "ESC 離頁後中英原版狀態或完整記憶體不同")
    events = [event for event in live["events"] if event.get("candidate_id") == KEY]
    need([event["stage"] for event in events] ==
         ["source-candidate", "source", "active", "expired"] and
         events[-1]["step"] > events[-2]["step"],
         "ESC 離頁未永久撤銷標題權杖")
    records = [next((line for line in frame["lines"] if line["candidate_id"] == KEY), None)
               for frame in live["frames"]]
    need(all(record is not None for record in records) and
         any(record["applied"] for record in records) and
         all(not record["applied"] for frame, record in zip(live["frames"], records)
             if frame["step"] >= events[-1]["step"]) and
         records[-1]["reason"] == "expired" and
         ImageChops.difference(live_png, control_png).getbbox() is None,
         "ESC 離頁仍殘留中文字或原畫面差異")
    return {"exit_step": events[-1]["step"], "state_sha256": live["state"]["memory_sha256"]}


def check_cursor(cursor_prefix):
    report, files, screenshot = load(cursor_prefix)
    records = [next((line for line in frame["lines"] if line["candidate_id"] == KEY), None)
               for frame in report["frames"]]
    need(all(record is not None for record in records) and
         any(record["applied"] for record in records) and
         records[-1]["applied"] is False and
         records[-1]["reason"] == "cursor-or-button-over-title" and
         records[-1]["accepted_events"] == 1,
         "游標遮擋未暫時回英文，或誤撤銷來源權杖")
    index = files["final.idx"]
    palette = files["final.pal"]
    need(len(index) == 64000 and len(palette) == 768, "游標負例原版畫面格式不符")
    for y in range(44, 59):
        for x in range(65, 253):
            i = index[y * 320 + x] * 3
            expected = tuple((palette[i + channel] << 2) | (palette[i + channel] >> 4)
                             for channel in range(3))
            for dy in range(4):
                for dx in range(4):
                    need(screenshot.getpixel((x * 4 + dx, y * 4 + dy)) == expected,
                         "游標遮擋時標題安全區未完整保留當幀英文原畫面")
    return {"cursor_last_reason": records[-1]["reason"],
            "cursor_applied_before_move": sum(record["applied"] for record in records)}


def check_gui(gui_prefix, active_live):
    report = json.loads(Path(str(gui_prefix) + ".json").read_text())
    inputs_data = Path(str(gui_prefix) + ".inputs.json").read_bytes()
    inputs = json.loads(inputs_data)
    shot_data = Path(str(gui_prefix) + ".options.png").read_bytes()
    events = [event for event in report["events"] if event.get("candidate_id") == KEY]
    records = [next((line for line in frame["lines"] if line["candidate_id"] == KEY), None)
               for frame in report["frames"]]
    need(not inputs.get("rejected") and
         [event["stage"] for event in events] == ["source-candidate", "source", "active"] and
         events[0]["safe_sha256"] == PRE_SAFE_SHA and events[2]["read_count"] == 32 and
         events[2]["changed_pixels"] == 319 and
         all(record is not None for record in records) and records[-1]["applied"],
         "實際視窗未由當次來源事件啟用標題中文")
    shot = Image.open(str(gui_prefix) + ".options.png").convert("RGB")
    _, _, replay = load(active_live)
    need(shot.size == (1280, 800) and ImageChops.difference(shot, replay).getbbox() is None,
         "實際 Ebitengine 視窗截圖與已驗1280M中文重播不符")
    return {"real_gui_inputs_sha256": sha(inputs_data), "real_gui_input_count": len(inputs["inputs"]),
            "real_gui_screenshot_sha256": sha(shot_data),
            "real_gui_applied_frames": sum(record["applied"] for record in records)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--live", type=Path, required=True)
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--mask", type=Path, required=True)
    p.add_argument("--full-live", type=Path, required=True)
    p.add_argument("--full-control", type=Path, required=True)
    p.add_argument("--cursor", type=Path, required=True)
    p.add_argument("--gui-prefix", type=Path, required=True)
    args = p.parse_args()
    if not (args.game / "OPENING.EXE").is_file() or not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱正式視窗中文化通過")
        return 77
    need(sha(args.inputs.read_bytes()) == INPUT_SHA, "真玩家輸入來源雜湊不符")
    result = check(args.live, args.control, json.loads(args.mask.read_text()))
    result.update(check_exit(args.full_live, args.full_control))
    result.update(check_cursor(args.cursor))
    result.update(check_gui(args.gui_prefix, args.live))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
