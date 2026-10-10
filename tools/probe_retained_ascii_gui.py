#!/usr/bin/env python3
"""規格052：沿已驗讀檔、城市、建造、購買及存檔路徑，以真X11鍵鼠抽驗英數。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time

from gui_auto import capture_frame_synced


ROOT = Path(__file__).resolve().parent.parent
SHOTS = [(63525000, "world"), (75900000, "colony"), (117150000, "choices"),
         (140910001, "wagon-return"), (163515001, "save-slots"), (172590001, "saved")]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "launcher", "game", "seed", "inputs", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file() and os.environ.get("DISPLAY"), "需Docker與有界Xvfb")
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
         output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "需新的workplace輸出")
    need(sha(args.seed) == "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b", "初始存檔不符")
    need(sha(args.inputs) == "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979", "正常玩家路徑不符")
    marker = "exec /out/issue56-source-connection-audit/colonization-window "
    source = args.launcher.read_text()
    need(source.count(marker) == 1, "啟動器版本不符")
    output.mkdir()
    (output / "save").mkdir()
    shutil.copy2(args.seed, output / "save/COLONY09.SAV")
    binary = output / "colonization-window"
    shutil.copy2(args.binary, binary)
    need(sha(binary) == sha(args.binary), "隔離執行檔副本不同")
    launcher = output / "launch.sh"
    launcher.write_text(source.replace(marker, "exec " + shlex.quote(str(binary)) + " ", 1))
    prefix = output / "gui"
    command = ["bash", str(launcher), "--game", str(args.game), "--play=false", "--audio-mute",
               "--window-steps", "210000000", "--retained-ascii-a", "--out", str(prefix)]
    (output / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    actions = []
    with (output / "process.log").open("wb") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   env={**os.environ, "COLONIZATION_CHT_SAVE": str(output / "save")},
                                   start_new_session=True)
        def status():
            need(process.poll() is None, f"前端已結束：{process.returncode}")
            try:
                return json.loads(prefix.with_suffix(".status.json").read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

        def wait_step(step):
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if status().get("step", -1) >= step:
                    return
                time.sleep(0.01)
            raise TimeoutError(f"原版未達步數{step}")

        def xdo(*parts):
            subprocess.run(["xdotool", *map(str, parts)], check=True, timeout=4,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            actions.append({"x11": list(map(str, parts)), "observed_step": status().get("step")})

        try:
            window = None
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                need(process.poll() is None, "開窗前已結束")
                result = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Colonization CHT"],
                                        capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and result.stdout.strip():
                    window = result.stdout.splitlines()[0]
                    break
                time.sleep(0.02)
            need(window is not None, "找不到遊戲視窗")
            xdo("windowfocus", window)
            tasks = [(e["step"], 0, e) for e in json.loads(args.inputs.read_text())["inputs"]]
            tasks += [(step, 1, name) for step, name in SHOTS]
            tasks.sort(key=lambda task: task[:2])
            for step, kind, task in tasks:
                wait_step(step)
                if kind == 1:
                    capture_frame_synced(str(prefix), window, task, process.pid)
                elif task["kind"] == "move":
                    xdo("mousemove", "--window", window, task["x"] * 4, task["y"] * 4)
                elif task["kind"] in ("press", "release"):
                    xdo("mousedown" if task["kind"] == "press" else "mouseup", task["button"] + 1)
                elif task["kind"] == "enter":
                    xdo("keydown", "Return")
                    start = status()["step"]
                    wait_step(start + 600000)
                    xdo("keyup", "Return")
                else:
                    raise ValueError("未驗X11事件")
            wait_step(173200000)
            subprocess.run([sys.executable, str(ROOT / "tools/gui_close_window.py"), "--window", window],
                           check=True, timeout=5)
            process.wait(timeout=20)
            need(process.returncode == 0, "前端沒有正常結束")
            need(prefix.with_suffix(".inputs.json").is_file() and (output / "save/COLONY00.SAV").is_file(),
                 "缺少正常輸入或存檔結尾")
            need(sha(output / "save/COLONY09.SAV") == sha(args.seed), "改寫原始存檔")
            result = {"result": "CAPTURED_RETAINED_ASCII_NORMAL_GUI_PENDING_REPLAY", "shots": SHOTS,
                      "binary_sha256": sha(args.binary), "actual_inputs_sha256": sha(prefix.with_suffix(".inputs.json")),
                      "actions": actions, "limitations": ["畫面與原版狀態仍須依當次實際輸入重播及審查。"]}
            (output / "gui-check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(result["result"], len(SHOTS), "shots", len(actions), "X11 actions")
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGCONT)
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
