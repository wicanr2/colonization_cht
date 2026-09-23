#!/usr/bin/env python3
"""獨立驗證姓名真視窗鍵盤路徑；原版與截圖僅保留本機。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def image(path):
    value = Image.open(path).convert("RGB")
    need(value.size == (1280, 800), f"畫面尺寸不符：{path}")
    return value


def masked_equal(left, right):
    # 兩次正常玩家收據在姓名欄上方／選國完成區的滑鼠座標不同，
    # 只排除這兩塊游標區，不排除任何遊戲文字或面板。
    probe = left.copy()
    for rect in ((64, 64, 128, 128), (260, 736, 304, 800)):
        probe.paste(right.crop(rect), rect)
    return ImageChops.difference(probe, right).getbbox() is None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據目錄不存在或擁有者不符")
    p = args.reports
    prior = args.prior
    live = json.loads((p / "live-name.json").read_text())
    control = json.loads((p / "live-name-control.json").read_text())
    inputs = json.loads((p / "live-name.inputs.json").read_text())
    need(live["control"] is False and control["control"] is True and
         live["all_menu"] is True and control["all_menu"] is True,
         "中英文／十四欄模式不符")
    need(inputs["end"] == 90000000 and not inputs.get("rejected"),
         "真視窗輸入結束點或拒絕事件不符")
    keyboard = [(e["step"], e["kind"], e.get("text")) for e in inputs["inputs"]
                if e["kind"] in ("text", "backspace", "enter")]
    need([e[1:] for e in keyboard] ==
         [("enter", None), ("text", "x"), ("backspace", None), ("enter", None)] and
         keyboard[0][0] < 4000000 and
         54000000 <= keyboard[1][0] < keyboard[2][0] < keyboard[3][0] < 68000000,
         "真視窗沒有依次送出開場 Enter、姓名 x、退格、姓名 Enter")
    need(live["state"] == control["state"] and live["opened"] == control["opened"] and
         live["input_hashes"] == control["input_hashes"],
         "同輸入中英文原版 CPU／RAM 雜湊／時間／開檔不一致")
    need((p / "live-name.memory").read_bytes() ==
         (p / "live-name-control.memory").read_bytes(), "完整原版 RAM 不一致")
    for suffix in ("idx", "pal"):
        need((p / f"live-name.final.{suffix}").read_bytes() ==
             (p / f"live-name-control.final.{suffix}").read_bytes(),
             f"最終原版索引／色盤不一致：{suffix}")
    need(sha(prior / "idle-a.55m.idx") ==
         "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e" and
         sha(prior / "idle-control.png") ==
         "f403556f7dcaf1961a735301d79bbf5376fe614b6a289738afc8109f21e202e9",
         "目標093原版姓名畫面基準不符")
    shots = {name: image(p / f"live-name.{name}.png")
             for name in ("idle", "letter", "backspace", "after-enter")}
    need(masked_equal(shots["idle"], image(prior / "idle-control.png")) and
         masked_equal(shots["after-enter"], image(prior / "enter-control.png")),
         "真視窗與目標093原版控制畫面在游標以外不一致")
    name_rect = (316, 392, 984, 448)
    prompt_rect = (400, 340, 876, 392)
    bbox_letter = ImageChops.difference(shots["idle"], shots["letter"]).getbbox()
    bbox_backspace = ImageChops.difference(shots["letter"], shots["backspace"]).getbbox()
    need(bbox_letter is not None and bbox_backspace is not None and
         all(name_rect[0] <= b[0] < b[2] <= name_rect[2] and
             name_rect[1] <= b[1] < b[3] <= name_rect[3]
             for b in (bbox_letter, bbox_backspace)),
         "字元／退格差分逃出原版姓名欄")
    need(all(ImageChops.difference(shots["idle"].crop(prompt_rect),
                                   shots[name].crop(prompt_rect)).getbbox() is None
             for name in ("letter", "backspace")),
         "原版姓名提示受到鍵盤輸入影響")
    need(ImageChops.difference(shots["backspace"], shots["after-enter"]).getbbox() !=
         bbox_backspace and live["opened"][-1] == "GAME.TXT",
         "Enter 未離開姓名畫面進入國家介紹")
    negative = json.loads((p / "live-negative.json").read_text())
    negative_control = json.loads((p / "live-negative-control.json").read_text())
    negative_inputs = json.loads((p / "live-negative.inputs.json").read_text())
    need(negative_inputs["end"] == 90000000 and negative_inputs.get("rejected") == ["!"],
         "真視窗不支援標點未記錄明確拒絕")
    negative_keys = [(e["kind"], e.get("text")) for e in negative_inputs["inputs"]
                     if e["kind"] in ("text", "backspace", "enter")]
    need(negative_keys == [("enter", None), ("text", "x"),
                           ("backspace", None), ("enter", None)],
         "失焦字元或標點意外進入 DOS 輸入收據")
    need(ImageChops.difference(image(p / "live-negative.idle.png"),
                               image(p / "live-negative.rejected-and-refocused.png")).getbbox() is None,
         "不支援標點或失焦按鍵改變了原版畫面")
    need(negative["state"] == negative_control["state"] and
         negative["opened"] == negative_control["opened"] and
         (p / "live-negative.memory").read_bytes() ==
         (p / "live-negative-control.memory").read_bytes(),
         "負例真視窗與英文控制原版狀態不同")
    for suffix in ("idx", "pal"):
        need((p / f"live-negative.final.{suffix}").read_bytes() ==
             (p / f"live-negative-control.final.{suffix}").read_bytes(),
             f"負例最終原版畫面不同：{suffix}")
    for name in ("name", "negative"):
        recheck = json.loads((p / f"recheck-{name}.json").read_text())
        baseline = control if name == "name" else negative_control
        need(recheck["state"] == baseline["state"] and
             recheck["opened"] == baseline["opened"] and
             (p / f"recheck-{name}.memory").read_bytes() ==
             (p / f"live-{name}-control.memory").read_bytes(),
             f"最終嚴格驗證版重播原版狀態回歸：{name}")
        for suffix in ("idx", "pal"):
            need((p / f"recheck-{name}.final.{suffix}").read_bytes() ==
                 (p / f"live-{name}-control.final.{suffix}").read_bytes(),
                 f"最終版索引／色盤回歸：{name}.{suffix}")
    report = {
        "result": "PASS",
        "scope": "固定 DOS 原版，真 Ebitengine 視窗姓名 x／退格／Enter、標點拒絕與失焦不補送；中文提示未接正式覆蓋",
        "input_keyboard": keyboard,
        "negative_rejected": negative_inputs["rejected"],
        "negative_keyboard": negative_keys,
        "final_code_replays": ["name", "negative"],
        "state_sha256": hashlib.sha256(json.dumps(live["state"], sort_keys=True).encode()).hexdigest(),
        "final_index_sha256": sha(p / "live-name.final.idx"),
        "prior_idle_control_sha256": sha(prior / "idle-control.png"),
        "name_diff_bbox": {"letter": bbox_letter, "backspace": bbox_backspace},
        "screenshots_sha256": {name: sha(p / f"live-name.{name}.png") for name in shots},
        "limitations": "僅此固定原版與 x／退格／Enter 正常路徑；標點只驗拒絕，未驗輸入法、其他字元的遊戲消費、正式中文提示",
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PASS：真視窗姓名鍵盤、原版對照畫面與中英文同狀態")


if __name__ == "__main__":
    main()
