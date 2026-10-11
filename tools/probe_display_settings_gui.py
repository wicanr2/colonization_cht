#!/usr/bin/env python3
"""規格056：以X11真實鍵鼠驗證正式設定列、保存及重開，原版狀態只讀。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
STATE_KEYS = ["step", "memory_sha256", "indexed_sha256", "palette_sha256",
              "registers", "segments", "ip", "flags", "dos_input_count", "dos_mouse"]


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["binary", "launcher", "game", "seed", "inputs", "ui-font", "ui-catalog", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file() and os.environ.get("DISPLAY"), "需Docker與有界Xvfb")
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists(), "輸出須為新的workplace目錄")
    need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出父目錄擁有者不符")
    seed = args.seed.read_bytes()
    need(sha(seed) == "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b", "正常初始存檔指紋不符")
    input_bytes = args.inputs.read_bytes()
    need(sha(input_bytes) == "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979", "正常路徑輸入指紋不符")
    launcher_source = args.launcher.read_text()
    marker = "exec /out/issue56-source-connection-audit/colonization-window "
    need(launcher_source.count(marker) == 1, "已驗啟動器替換點不唯一")
    output.mkdir()
    save = output / "save"
    save.mkdir()
    (save / "COLONY09.SAV").write_bytes(seed)
    launcher = output / "launch.sh"
    launcher.write_text(launcher_source.replace(marker, "exec " + shlex.quote(str(args.binary)) + " ", 1))
    prefix = output / "gui"
    preference_dir = output / "preferences"
    preference_dir.mkdir()
    preference = preference_dir / "display.json"
    env = os.environ.copy()
    env["COLONIZATION_CHT_SAVE"] = str(save)
    cmd = ["bash", str(launcher), "--game", str(args.game), "--play=false", "--audio-mute",
           "--window-steps", "200000000", "--display-settings", "--display-diagnostics",
           "--display-ui-font", str(args.ui_font), "--display-ui-catalog", str(args.ui_catalog),
           "--display-config", str(preference), "--out", str(prefix)]
    process_log = (output / "process.log").open("wb")
    process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=process_log, stderr=subprocess.STDOUT,
                               env=env, start_new_session=True)
    started = time.monotonic()
    actions, checks = [], []

    def status():
        need(process.poll() is None, f"前端已結束：{process.returncode}")
        try:
            return json.loads(prefix.with_suffix(".status.json").read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def wait(predicate, description, seconds=20):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            current = status()
            if predicate(current):
                return current
            time.sleep(0.015)
        raise TimeoutError(description)

    def xdo(*parts):
        subprocess.run(["xdotool", *map(str, parts)], check=True, timeout=4,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        actions.append({"x11": list(map(str, parts)), "seconds": time.monotonic() - started})

    def events():
        return json.loads(prefix.with_suffix(".display-events.json").read_text())

    def phase(value):
        return wait(lambda s: s.get("display", {}).get("phase") == value, f"設定未進入狀態{value}")

    def frozen(step, wanted_phase):
        time.sleep(0.3)
        s = status()
        need(s.get("step") == step and s.get("display", {}).get("phase") == wanted_phase,
             f"設定期間原版推進或按鍵穿透：{s}")

    def same_state(group, label):
        baseline = group[0]
        for event in group[1:]:
            need(all(event[key] == baseline[key] for key in STATE_KEYS),
                 f"{label}更動原版狀態或DOS輸入：{event['action']}")
        checks.append({"case": label, "step": baseline["step"], "event_actions": [e["action"] for e in group],
                       "equal_fields": STATE_KEYS})

    try:
        deadline = time.monotonic() + 20
        window = None
        while time.monotonic() < deadline:
            need(process.poll() is None, "開窗前已結束")
            result = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Colonization CHT"],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode == 0 and result.stdout.strip():
                window = result.stdout.splitlines()[0]
                break
            time.sleep(0.02)
        need(window is not None, "找不到真實前端視窗")
        xdo("windowfocus", window)

        def move(x, y):
            xdo("mousemove", "--window", window, x, y)

        def click(x, y):
            move(x, y)
            xdo("mousedown", 1)
            time.sleep(0.075)
            xdo("mouseup", 1)
            time.sleep(0.075)

        def capture(name):
            path = output / (name + ".png")
            subprocess.run(["import", "-window", window, str(path)], check=True, timeout=5)
            with Image.open(path) as image:
                need(image.size == (1280, 848), f"視窗比例改變：{image.size}")
            return path

        def open_settings():
            first = len(events()) if prefix.with_suffix(".display-events.json").exists() else 0
            move(115, 24)
            xdo("mousedown", 1)
            s = phase(1)
            frozen(s["step"], 1)
            return first, s["step"]

        # 重用已驗正常玩家路徑的前15個鍵鼠事件；轉為真實X11輸入，沒有記憶體或輸入佇列注入。
        for event in json.loads(input_bytes)["inputs"][:15]:
            wait(lambda s: s.get("step", -1) >= event["step"], f"未達原版步數{event['step']}")
            if event["kind"] == "move":
                move(event["x"] * 4, event["y"] * 4 + 48)
            elif event["kind"] in ("press", "release"):
                xdo("mousedown" if event["kind"] == "press" else "mouseup", event["button"] + 1)
            elif event["kind"] == "enter":
                xdo("keydown", "Return")
                time.sleep(0.075)
                xdo("keyup", "Return")
            else:
                raise ValueError("路徑含未驗X11輸入")
        wait(lambda s: s.get("step", 0) >= 63000000, "未到世界畫面")
        capture("world-before")

        # 真實拖曳越過工具列不開設定，不提前放開已送入原版的按鈕。
        move(64, 144)
        xdo("mousedown", 1)
        down = wait(lambda s: s.get("dos_mouse", {}).get("buttons", 0) & 1, "原版未收到拖曳按下")
        before_events = len(events()) if prefix.with_suffix(".display-events.json").exists() else 0
        move(115, 24)
        drag = wait(lambda s: s.get("step", 0) >= down["step"] + 1000000, "拖曳經工具列後原版未繼續")
        need(drag["display"]["phase"] == 0 and drag["dos_mouse"]["buttons"] & 1, "工具列中斷原版拖曳或誤開設定")
        need((len(events()) if prefix.with_suffix(".display-events.json").exists() else 0) == before_events,
             "拖曳經工具列產生設定事件")
        xdo("mouseup", 1)
        wait(lambda s: not s.get("dos_mouse", {}).get("buttons", 1), "工具列實體放開未送入原版")
        checks.append({"case": "original-drag-across-toolbar", "held_step": drag["step"],
                       "mouse_buttons": drag["dos_mouse"]["buttons"], "phase": drag["display"]["phase"]})

        first, step = open_settings()
        move(240, 600)
        xdo("keydown", "a")
        xdo("keydown", "Escape")
        frozen(step, 1)
        xdo("mouseup", 1)
        frozen(step, 1)
        xdo("keyup", "a")
        xdo("keyup", "Escape")
        phase(2)
        capture("settings-held-release")
        xdo("keydown", "Escape")
        phase(3)
        frozen(step, 3)
        xdo("keyup", "Escape")
        phase(0)
        same_state(events()[first:], "open-hold-keyboard-escape-cancel-release")

        # 設定開啟、編輯與等待恢復時失焦，原版仍暫停；回焦且全部放開才恢復。
        first, step = open_settings()
        xdo("windowfocus", 0)
        frozen(step, 1)
        xdo("mouseup", 1)
        frozen(step, 1)
        xdo("windowfocus", window)
        phase(2)
        xdo("windowfocus", 0)
        frozen(step, 2)
        xdo("windowfocus", window)
        xdo("keydown", "Escape")
        phase(3)
        xdo("windowfocus", 0)
        frozen(step, 3)
        xdo("keyup", "Escape")
        frozen(step, 3)
        xdo("windowfocus", window)
        phase(0)
        same_state(events()[first:], "focus-loss-opening-editing-resuming")
        need(not preference.exists(), "取消或唯讀啟動建立了設定檔")

        first, step = open_settings()
        xdo("mouseup", 1)
        phase(2)
        click(771, 374)  # 韓文資料包未安裝，應整包拒絕。
        click(912, 644)
        s = phase(2)
        need(s["display"]["problem"] == "ui.error.unavailable" and s["display"]["current"]["language"] == "zh-Hant",
             "失敗語言套用沒有保留目前設定")
        capture("language-load-error")
        click(363, 374)
        click(808, 480)  # HD資料包未安裝，應保留目前圖像。
        click(912, 644)
        s = phase(2)
        need(s["display"]["problem"] == "ui.error.unavailable" and s["display"]["current"]["graphics"] == "original",
             "失敗HD套用更動目前圖像")
        capture("hd-load-error")
        need(not preference.exists(), "失敗的語言或HD套用保存了設定")
        click(464, 480)
        click(907, 374)
        move(912, 644)
        xdo("mousedown", 1)
        s = phase(3)
        need(s["display"]["current"]["language"] == "en", "英文沒有套用")
        need(json.loads(preference.read_text()) == {"language": "en", "graphics": "original"}, "英文套用未保存")
        need(preference.stat().st_mode & 0o777 == 0o600, "保存檔權限錯誤")
        frozen(step, 3)
        english_capture = capture("english-applied-held")
        english_event = events()[-1]
        with Image.open(english_capture) as actual, Image.open(english_event["presentation_path"]) as presentation:
            need(actual.convert("RGB").crop((0, 48, 1280, 848)).tobytes() == presentation.convert("RGB").tobytes(),
                 "真視窗英文區沒有呈現當次重合成畫面")
        native = Path(english_event["indexed_path"]).read_bytes()
        palette = Path(english_event["palette_path"]).read_bytes()
        expected = Image.frombytes("P", (320, 200), native)
        expected.putpalette([value << 2 | value >> 4 for value in palette])
        expected = expected.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
        with Image.open(english_event["presentation_path"]) as presentation:
            need(expected.tobytes() == presentation.convert("RGB").tobytes(), "英文不是原版像素與字體")
        xdo("mouseup", 1)
        phase(0)
        same_state(events()[first:], "language-hd-load-failure-and-English-apply")

        first, step = open_settings()
        xdo("mouseup", 1)
        phase(2)
        click(363, 374)
        saved_english = preference.read_bytes()
        preference_dir.chmod(0o500)
        try:
            click(912, 644)
            s = phase(2)
            need(s["display"]["problem"] == "ui.error.save" and s["display"]["current"]["language"] == "en",
                 "保存失敗仍切換了語言")
            need(preference.read_bytes() == saved_english, "保存失敗損毀舊設定")
            capture("preference-save-error")
        finally:
            preference_dir.chmod(0o755)
        move(912, 644)
        xdo("mousedown", 1)
        s = phase(3)
        need(s["display"]["current"]["language"] == "zh-Hant", "無法切回繁中")
        need(json.loads(preference.read_text()) == {"language": "zh-Hant", "graphics": "original"}, "切回繁中未保存")
        frozen(step, 3)
        chinese_capture = capture("chinese-applied-held")
        chinese_event = events()[-1]
        with Image.open(chinese_capture) as actual, Image.open(chinese_event["presentation_path"]) as presentation:
            need(actual.convert("RGB").crop((0, 48, 1280, 848)).tobytes() == presentation.convert("RGB").tobytes(),
                 "真視窗繁中區沒有呈現當次重合成畫面")
        xdo("mouseup", 1)
        phase(0)
        same_state(events()[first:], "return-to-Chinese-without-original-redraw")

        # 切換後繼續正常進城，確認遊戲座標沒有被設定列挪動。
        before = status()["step"]
        click(152 * 4, 112 * 4 + 48)
        wait(lambda s: s.get("step", 0) >= before + 8000000, "切換後未繼續原版指令")
        capture("colony-after-settings")
        first, step = open_settings()
        saved_chinese = preference.read_bytes()
        xdo("mouseup", 1)
        phase(2)
        click(768, 644)
        phase(0)
        same_state(events()[first:], "colony-mouse-cancel")
        need(preference.read_bytes() == saved_chinese, "取消更動已保存設定")
        subprocess.run([sys.executable, str(ROOT / "tools/gui_close_window.py"), "--window", window],
                       check=True, timeout=5)
        process.wait(timeout=15)
        need(process.returncode == 0, f"前端未正常關閉：{process.returncode}")
        need(prefix.with_suffix(".inputs.json").is_file(), "沒有正常GUI輸入收據")
        need(sha((save / "COLONY09.SAV").read_bytes()) == sha(seed), "設定更動原始存檔")
        primary_prefix = prefix
        restart_checks = []
        # 重新啟動同一正式程式，使用正常開場輸入到選單；不以人工JSON代替套用。
        for name, wanted, apply_english in [("restart-chinese", "zh-Hant", True), ("restart-english", "en", False)]:
            prefix = output / name
            process_log.close()
            process_log = (output / (name + ".log")).open("wb")
            before = preference.read_bytes()
            restart_cmd = cmd.copy()
            restart_cmd[-1] = str(prefix)
            process = subprocess.Popen(restart_cmd, stdin=subprocess.DEVNULL, stdout=process_log,
                                       stderr=subprocess.STDOUT, env=env, start_new_session=True)
            deadline = time.monotonic() + 20
            window = None
            while time.monotonic() < deadline:
                need(process.poll() is None, "重開視窗前已結束")
                found = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Colonization CHT"],
                                       capture_output=True, text=True, timeout=3)
                if found.returncode == 0 and found.stdout.strip():
                    window = found.stdout.splitlines()[0]
                    break
                time.sleep(0.02)
            need(window is not None, "找不到重開視窗")
            xdo("windowfocus", window)
            s = wait(lambda s: "display" in s, "重開沒有顯示設定狀態")
            need(s["display"]["current"] == {"language": wanted, "graphics": "original"}, "重開未讀取保存設定")
            need(preference.read_bytes() == before, "重開讀取寫回了設定")
            for event in json.loads(input_bytes)["inputs"][:5]:
                wait(lambda s: s.get("step", -1) >= event["step"], "重開未到正常輸入步數")
                if event["kind"] == "move":
                    move(event["x"] * 4, event["y"] * 4 + 48)
                elif event["kind"] in ("press", "release"):
                    xdo("mousedown" if event["kind"] == "press" else "mouseup", event["button"] + 1)
                else:
                    xdo("keydown", "Return")
                    time.sleep(0.075)
                    xdo("keyup", "Return")
            wait(lambda s: s.get("step", 0) >= 28000000, "重開未到正常選單")
            first, step = open_settings()
            xdo("mouseup", 1)
            phase(2)
            if apply_english:
                click(907, 374)
                click(912, 644)
            else:
                event = events()[first]
                native = Image.frombytes("P", (320, 200), Path(event["indexed_path"]).read_bytes())
                native.putpalette([v << 2 | v >> 4 for v in Path(event["palette_path"]).read_bytes()])
                expected = native.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
                with Image.open(event["presentation_path"]) as shown:
                    need(expected.tobytes() == shown.convert("RGB").tobytes(), "重開英文未維持原版字體")
                capture("restart-english-settings")
                click(768, 644)
            phase(0)
            same_state(events()[first:], name + "-settings")
            need(json.loads(preference.read_text()) == {"language": "en", "graphics": "original"}, "重開套用或取消破壞保存設定")
            restart_checks.append({"case": name, "loaded": wanted, "before_sha256": sha(before),
                                   "after_sha256": sha(preference.read_bytes())})
            subprocess.run([sys.executable, str(ROOT / "tools/gui_close_window.py"), "--window", window],
                           check=True, timeout=5)
            process.wait(timeout=15)
            need(process.returncode == 0, "重開未正常關閉")
        prefix = primary_prefix
        result = {"result": "PASS_SETTINGS_NORMAL_GUI_PROTOTYPE", "checks": checks,
                  "preference_restart_checks": restart_checks,
                  "preference_sha256": sha(preference.read_bytes()),
                  "source_sha256": {"binary": sha(args.binary.read_bytes()), "launcher": sha(args.launcher.read_bytes()),
                                    "seed": sha(seed), "normal_path": sha(input_bytes), "ui_tsv": sha(args.ui_catalog.read_bytes()),
                                    "ui_font": sha(args.ui_font.read_bytes()), "probe": sha(Path(__file__).read_bytes())},
                  "gui_inputs_sha256": sha(prefix.with_suffix(".inputs.json").read_bytes()),
                  "events_sha256": sha(prefix.with_suffix(".display-events.json").read_bytes()), "actions": actions,
                  "limitations": ["Display settings only; no full five-language gameplay or HD completion.",
                                  "No hardware audio or macOS runtime validation.",
                                  "Original frontend replay comparison still required."]}
        (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(result["result"], len(checks), "same-state sessions")
        return 0
    finally:
        preference_dir.chmod(0o755)
        for key in ["a", "Escape", "Return"]:
            subprocess.run(["xdotool", "keyup", key], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        subprocess.run(["xdotool", "mouseup", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        process_log.close()
        (output / "x11-actions.json").write_text(json.dumps(actions, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
