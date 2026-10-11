#!/usr/bin/env python3
"""規格060 DRAFT：以真實X11輸入驗隔離視窗五語，不修改原版狀態。"""
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

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ["zh-Hant", "zh-Hans", "ja", "ko", "en"]
STATE_KEYS = ["step", "memory_sha256", "indexed_sha256", "palette_sha256", "registers",
              "segments", "ip", "flags", "dos_input_count", "dos_mouse"]


def need(value, message):
    if not value:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["binary", "launcher", "game", "seed", "inputs", "ui-font", "ui-catalog", "bundles", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--save-cycle", action="store_true", help="追加正常存檔插槽、成功通知及返回世界的五語驗證")
    parser.add_argument("--reload-save", type=Path, help="先前已驗正常存檔GUI目錄")
    parser.add_argument("--reload-proof", type=Path, help="該GUI的四側重播check.json")
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file() and os.environ.get("DISPLAY"), "需Docker與有界Xvfb")
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
         output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "需新的workplace輸出")
    seed, inputs = args.seed.read_bytes(), args.inputs.read_bytes()
    need(sha(seed) == "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b", "初始存檔不同")
    need(sha(inputs) == "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979", "正常讀檔路徑不同")
    marker = "exec /out/issue56-source-connection-audit/colonization-window "
    launcher = args.launcher.read_text()
    need(launcher.count(marker) == 1, "啟動器替換點不唯一")
    load_cycle, saved_bytes, saved_preferences = None, None, None
    need(bool(args.reload_save) == bool(args.reload_proof) and not (args.reload_save and args.save_cycle),
         "新行程讀回需成對提供來源與重播證明，且不得同時重新存檔")
    if args.reload_save:
        source_bytes, proof_bytes = (args.reload_save / "check.json").read_bytes(), args.reload_proof.read_bytes()
        source, proof = json.loads(source_bytes), json.loads(proof_bytes)
        saved_bytes = (args.reload_save / "save/COLONY00.SAV").read_bytes()
        saved_preferences = (args.reload_save / "preferences/display.json").read_bytes()
        expected_saves = {"COLONY00.SAV": sha(saved_bytes), "COLONY09.SAV": sha(seed)}
        need(source["result"] == "PASS_NATIVE_LIVE_FIVE_LANGUAGE_GUI" and
             source.get("normal_save_cycle") == {"kind": "normal-gui-save-slot-success-return",
                                                 "created": "COLONY00.SAV", "sha256": sha(saved_bytes)} and
             source["source_sha256"]["binary"] == sha(args.binary.read_bytes()), "正常存檔來源未通過")
        need(proof["result"] == "PASS_NATIVE_LIVE_GUI_FOUR_REPLAYS" and
             proof["source_sha256"]["gui"] == sha(source_bytes) and len(proof["runs"]) == 4 and
             proof["source_sha256"]["inputs"] == source["gui_inputs_sha256"] ==
             sha((args.reload_save / "gui.inputs.json").read_bytes()) and
             all(x["state"] == json.loads((args.reload_save / "gui.json").read_bytes())["state"]
                 for x in proof["runs"].values()) and
             all(x["save_sha256"] == expected_saves for x in proof["runs"].values()) and
             sha((args.reload_save / "save/COLONY09.SAV").read_bytes()) == sha(seed), "正常存檔四側證明不同")
        need(json.loads(saved_preferences) == {"language": "zh-Hant", "graphics": "original"}, "前次保存設定不同")
        load_cycle = {"kind": "new-process-normal-load-and-colony-return", "loaded": "COLONY00.SAV",
                      "initial_saves": expected_saves, "source_gui_sha256": sha(source_bytes),
                      "source_replay_sha256": sha(proof_bytes), "initial_preferences_sha256": sha(saved_preferences)}
    output.mkdir()
    save, preferences = output / "save", output / "preferences"
    save.mkdir()
    preferences.mkdir()
    (save / "COLONY09.SAV").write_bytes(seed)
    script = output / "launch.sh"
    script.write_text(launcher.replace(marker, "exec " + shlex.quote(str(args.binary)) + " ", 1))
    prefix, preference = output / "gui", preferences / "display.json"
    if load_cycle is not None:
        (save / "COLONY00.SAV").write_bytes(saved_bytes)
        preference.write_bytes(saved_preferences)
    env = os.environ.copy()
    env["COLONIZATION_CHT_SAVE"] = str(save)
    command = ["bash", str(script), "--game", str(args.game), "--play=false", "--audio-mute",
               "--window-steps", "500000000", "--display-settings", "--display-diagnostics",
               "--display-ui-font", str(args.ui_font), "--display-ui-catalog", str(args.ui_catalog),
               "--display-config", str(preference), "--draft-native-capture", "--draft-native-live",
               "--draft-native-bundles", str(args.bundles), "--audio-wav", str(output / "audio.wav"), "--out", str(prefix)]
    log = (output / "process.log").open("wb")
    process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
    started = time.monotonic()
    actions, checks = [], []

    def status():
        need(process.poll() is None, f"前端已結束：{process.returncode}")
        try:
            return json.loads(prefix.with_suffix(".status.json").read_bytes())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def wait(predicate, description, seconds=45):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            s = status()
            if predicate(s):
                return s
            time.sleep(0.025)
        raise TimeoutError(description)

    def xdo(*parts):
        subprocess.run(["xdotool", *map(str, parts)], check=True, timeout=4,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        actions.append({"x11": list(map(str, parts)), "seconds": time.monotonic() - started})

    def events():
        p = prefix.with_suffix(".display-events.json")
        return json.loads(p.read_bytes()) if p.exists() else []

    def phase(value):
        return wait(lambda s: s.get("display", {}).get("phase") == value, f"設定未進入狀態{value}")

    def live(s):
        return s.get("frame", {}).get("native_live", {})

    try:
        window = None
        until = time.monotonic() + 45
        while time.monotonic() < until:
            need(process.poll() is None, "開窗前已結束")
            found = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Colonization CHT"],
                                   capture_output=True, text=True, timeout=3)
            if found.returncode == 0 and found.stdout.strip():
                window = found.stdout.splitlines()[0]
                break
            time.sleep(0.025)
        need(window is not None, "找不到真實視窗")
        xdo("windowfocus", window)

        def move(x, y):
            xdo("mousemove", "--window", window, x, y)

        def click(x, y):
            move(x, y)
            xdo("mousedown", 1)
            time.sleep(0.08)
            xdo("mouseup", 1)
            time.sleep(0.08)

        def open_settings():
            first = len(events())
            move(115, 24)
            xdo("mousedown", 1)
            s = phase(1)
            xdo("mouseup", 1)
            phase(2)
            return first, s["step"]

        def same_state(first, step):
            group = events()[first:]
            need(group and group[0]["step"] == step, "缺少當次暫停事件")
            need(all(all(e[k] == group[0][k] for k in STATE_KEYS) for e in group), "切換更動原版狀態或DOS輸入")
            return [e["action"] for e in group]

        def switch_round(scene):
            before = status()["step"]
            for locale in ["zh-Hans", "ja", "ko", "en", "zh-Hant"]:
                first, step = open_settings()
                click(363 + 136 * LOCALES.index(locale), 374)
                move(912, 644)
                xdo("mousedown", 1)
                s = phase(3)
                need(s["display"]["current"] == {"language": locale, "graphics": "original"}, "完整語言包未套用")
                time.sleep(0.25)
                need(status()["step"] == step, "按住套用期間原版推進")
                e = events()[-1]
                need(e["action"] == "apply", "套用事件不同")
                shown_path = output / f"{scene}-{locale}.png"
                subprocess.run(["import", "-window", window, str(shown_path)], check=True, timeout=5)
                with Image.open(shown_path) as shown, Image.open(e["presentation_path"]) as presentation:
                    need(shown.size == (1280, 848) and shown.convert("RGB").crop((0, 48, 1280, 848)).tobytes() ==
                         presentation.convert("RGB").tobytes(), "真視窗遊戲區與當次畫面不同")
                    actual = presentation.convert("RGB")
                native = Image.frombytes("P", (320, 200), Path(e["indexed_path"]).read_bytes())
                native.putpalette([v << 2 | v >> 4 for v in Path(e["palette_path"]).read_bytes()])
                original = native.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
                record = live(s)
                need(record.get("locale") == locale, "畫面沿用前語言")
                if locale == "en":
                    need(actual.tobytes() == original.tobytes(), "英文沒有使用原版像素")
                else:
                    need(record.get("items") and actual.tobytes() != original.tobytes(), "非英文沒有任何已驗覆蓋")
                    if scene == "save-success":
                        need(any(i.get("kind") == "dialog" and i.get("id") == "GAME.TXT:0x000007B9"
                                 for i in record["items"]), "當次成功通知沒有實際重建")
                    if scene == "load-success":
                        need(any(i.get("kind") == "dialog" and i.get("id") == "GAME.TXT:0x00000854"
                                 for i in record["items"]), "當次讀檔通知沒有實際重建")
                    if scene == "colony":
                        numerals = {item.get("source") for item in record["items"]
                                    if item.get("id") == "STRING:retained-ascii" and item.get("font_px", 0) > 0}
                        need({"90", "10% (0)"}.issubset(numerals), "已驗進城數值未使用目標Noto字型")
                    safe = Image.new("1", actual.size)
                    draw = ImageDraw.Draw(safe)
                    for item in record["items"]:
                        r = item["safe"]
                        draw.rectangle((r["Min"]["X"] * 4, r["Min"]["Y"] * 4,
                                        r["Max"]["X"] * 4 - 1, r["Max"]["Y"] * 4 - 1), fill=1)
                    difference = ImageChops.difference(actual, original)
                    outside = Image.composite(difference, Image.new("RGB", actual.size), safe.point(lambda v: 0 if v else 255, "1"))
                    need(outside.getbbox() is None, "五語覆蓋超出安全區")
                xdo("mouseup", 1)
                phase(0)
                event_actions = same_state(first, step)
                need(json.loads(preference.read_bytes()) == {"language": locale, "graphics": "original"}, "保存的語言不同")
                checks.append({"scene": scene, "locale": locale, "step": step, "event_actions": event_actions,
                               "presentation_sha256": sha(Path(e["presentation_path"]).read_bytes()), "native_live": record})
                print("PASS_NATIVE_LIVE_GUI_SWITCH", scene, locale, step, len(record.get("items", [])), flush=True)
            return status()["step"] - before

        def send(event, offset=0):
            wait(lambda s: s.get("step", -1) >= event["step"] + offset, "未達正常輸入步數")
            if event["kind"] == "move":
                move(event["x"] * 4, event["y"] * 4 + 48)
            elif event["kind"] in ["press", "release"]:
                xdo("mousedown" if event["kind"] == "press" else "mouseup", event["button"] + 1)
            elif event["kind"] == "enter":
                xdo("keydown", "Return")
                time.sleep(0.08)
                xdo("keyup", "Return")
            else:
                raise ValueError("輸入來源含未驗操作")

        path = json.loads(inputs)["inputs"]
        for event in path[:5]:
            send(event)
        wait(lambda s: any(i.get("id") == "GAME.TXT:0x000001B0" for i in (live(s).get("items") or [])), "未到已驗主選單")
        offset = switch_round("main-menu")
        if load_cycle is None:
            for event in path[5:15]:
                send(event, offset)
            wait(lambda s: s.get("step", 0) >= 63000000 + offset and
                 any(i["kind"] == "sea-bar" for i in (live(s).get("items") or [])), "未到正常世界畫面")
            switch_round("world")
        else:
            # 已驗正常讀回操作：goal185-player-experience/play_reload_newgame.py。
            before = status()["step"]
            click(512, 536 + 48)
            wait(lambda s: s.get("step", 0) >= before + 3000000, "讀檔插槽未完成繪製")
            switch_round("load-slots")
            click(480, 310 + 48)
            wait(lambda s: any(i.get("id") == "GAME.TXT:0x00000854"
                              for i in live(s).get("items", [])), "新行程未正常讀回存檔")
            switch_round("load-success")
            before = status()["step"]
            xdo("keydown", "Return")
            time.sleep(0.08)
            xdo("keyup", "Return")
            wait(lambda s: s.get("step", 0) >= before + 4000000 and
                 any(i["kind"] == "sea-bar" for i in live(s).get("items", [])) and
                 not any(i.get("id") == "GAME.TXT:0x00000854" for i in live(s).get("items", [])),
                 "讀檔通知關閉後來源未撤銷")
            switch_round("loaded-world")
            # 新存檔讀回後尚無選取；第一次點擊只選船，原版側欄隨即出現。
            click(152 * 4, 112 * 4 + 48)
            wait(lambda s: any(i.get("kind") == "sea-panel" and i.get("source") == "Eng. Caravel"
                              for i in live(s).get("items", [])), "讀回後未正常選取船")
        before = status()["step"]
        click(152 * 4, 112 * 4 + 48)
        wait(lambda s: s.get("step", 0) >= before + 8000000, "切換後未繼續進城")
        switch_round("colony")
        before = status()["step"]
        xdo("keydown", "Escape")
        time.sleep(0.08)
        xdo("keyup", "Escape")
        wait(lambda s: s.get("step", 0) >= before + 4000000 and
             any(i["kind"] == "sea-bar" for i in (live(s).get("items") or [])), "返回世界後來源未恢復")
        save_cycle = None
        if args.save_cycle:
            # 已驗正常操作來源：goal185-player-experience/play_newgame_save.py。
            # 原有四倍畫布座標只增加畫面外設定列的48px高度。
            def settle_click(x, y):
                before = status()["step"]
                click(x, y + 48)
                wait(lambda s: s.get("step", 0) >= before + 3000000, "正常存檔操作未完成")

            settle_click(96, 12)
            settle_click(192, 252)
            switch_round("save-slots")
            settle_click(480, 310)
            wait(lambda s: any(i.get("kind") == "dialog" and i.get("id") == "GAME.TXT:0x000007B9"
                              for i in live(s).get("items", [])) and
                 (save / "COLONY00.SAV").is_file(), "未完成正常原版存檔")
            switch_round("save-success")
            before = status()["step"]
            xdo("keydown", "Return")
            time.sleep(0.08)
            xdo("keyup", "Return")
            wait(lambda s: s.get("step", 0) >= before + 4000000 and
                 any(i["kind"] == "sea-bar" for i in (live(s).get("items") or [])) and
                 not any(i.get("id") == "GAME.TXT:0x000007B9" for i in live(s).get("items", [])),
                 "存檔後未正常返回世界")
            switch_round("saved-world")
            save_cycle = {"kind": "normal-gui-save-slot-success-return",
                          "created": "COLONY00.SAV", "sha256": sha((save / "COLONY00.SAV").read_bytes())}
        final_live = live(status())
        subprocess.run([sys.executable, str(ROOT / "tools/gui_close_window.py"), "--window", window], check=True, timeout=5)
        process.wait(timeout=25)
        need(process.returncode == 0, "視窗未正常關閉")
        need(sha((save / "COLONY09.SAV").read_bytes()) == sha(seed), "顯示切換改動初始存檔")
        if load_cycle is not None:
            need(sha((save / "COLONY00.SAV").read_bytes()) == sha(saved_bytes), "新行程改動讀回存檔")
        need(prefix.with_suffix(".inputs.json").is_file(), "沒有實際DOS輸入收據")
        result = {"result": "PASS_NATIVE_LIVE_FIVE_LANGUAGE_GUI", "checks": checks, "final_live": final_live,
                  "source_sha256": {"binary": sha(args.binary.read_bytes()), "launcher": sha(args.launcher.read_bytes()),
                                    "seed": sha(seed), "normal_path": sha(inputs), "probe": sha(Path(__file__).read_bytes())},
                  "gui_inputs_sha256": sha(prefix.with_suffix(".inputs.json").read_bytes()),
                  "limitations": ["隔離視窗；完整來源生命週期、正式接線、HD及同輸入重播仍須另外驗證。"]}
        if save_cycle is not None:
            result["normal_save_cycle"] = save_cycle
        if load_cycle is not None:
            result["normal_load_cycle"] = load_cycle
        (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(result["result"], len(checks), flush=True)
    finally:
        for key in ["Return", "Escape"]:
            subprocess.run(["xdotool", "keyup", key], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        subprocess.run(["xdotool", "mouseup", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        log.close()
        (output / "x11-actions.json").write_text(json.dumps(actions, indent=2) + "\n")


if __name__ == "__main__":
    main()
