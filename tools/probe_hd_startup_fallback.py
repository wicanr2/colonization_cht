#!/usr/bin/env python3
"""規格061：以正式啟動器及真X11驗保存HD後缺件／錯件與恢復。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from probe_language_live_gui import STATE_KEYS


def need(ok, reason):
    if not ok:
        raise AssertionError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["bundle", "game", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--cases", nargs="+", help="只驗指定的既有案例；省略時驗全部案例")
    parser.add_argument("--startup-timeout", type=float, default=45, help="開窗等待秒數；只適用資產初始化，範圍1至180")
    args = parser.parse_args()
    need(1 <= args.startup_timeout <= 180, "開窗等待範圍不同")
    root = args.output.resolve()
    need(Path("/.dockerenv").is_file() and os.environ.get("DISPLAY") and os.getuid() != 0,
         "需非root Docker及有界Xvfb")
    need(root.is_relative_to(Path("/out")) and not root.exists() and
         root.parent.stat().st_uid == os.getuid(), "需新的自有輸出目錄")
    root.mkdir()
    preference = root / "display.json"
    saved = b'{"language":"ja","graphics":"hd"}\n'
    preference.write_bytes(saved)
    results = []
    cases = ["missing-directory", "missing-image", "bad-image", "bad-manifest",
                 "missing-sea", "bad-sea", "linked-sea", "missing-person", "bad-person", "linked-person", "missing-shelter", "bad-shelter", "linked-shelter"]
    cases += [kind+"-building-%03d"%n for n in [16,21,27,35,39,42,43,44,45,9] for kind in ["missing","bad","linked"]]
    cases += [kind+"-icons-%03d"%n for n in [8, 9, 16, 6, 7, 14, 15, 127, 5, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 42, 53, 56, 59, 62, 67, 68, 69, 94, 122, 123, 124, 58, 60, 66, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 95, 96, 97, 98, 106, 107] for kind in ["missing","bad","linked"]]
    cases += ["missing-terrain079","bad-terrain079","linked-terrain079"]
    terrain_batch = [6, 9, 17, 66, 71, 74, 77, 78, 80, 96, 147, 150,
                     112, 113, 116, 119, 126, 127, 136, 139]
    cases += [kind+"-terrain-%03d"%n for n in terrain_batch for kind in ["missing", "bad", "linked"]]
    cases += ["missing-terrain-source", "bad-terrain-source", "linked-terrain-source"]
    cases += [kind+'-'+name for name in ['opentile-000','openmenu-000','woodtile-000','parch-000','difficul-000','nations-000','customiz-000','menu-source','texture-source','wood-source','parch-source','difficulty-source','nations-source','custom-source'] for kind in ['missing','bad','linked']]
    cases += ["missing-cursor-image","bad-cursor-image","linked-cursor-image",
              "missing-cursor-source","bad-cursor-source","linked-cursor-source","restored"]
    if args.cases:
        need(len(args.cases)==len(set(args.cases)) and set(args.cases)<=set(cases), "指定的缺件案例不同")
        cases = [case for case in cases if case in args.cases]
    for case in cases:
        out = root / case
        out.mkdir()
        assets = out / "graphics"
        case_game = args.game
        if any(case.endswith('-'+name+'-source') for name in ['cursor','terrain','menu','texture','wood','parch','difficulty','nations','custom']):
            case_game = out / "game"
            shutil.copytree(args.game, case_game)
            source_name = next(filename for name,filename in [('terrain','PHYS0.SS'),('cursor','CURSOR.SS'),('menu','OPENMENU.PIK'),('texture','OPENTILE.SS'),('wood','WOODTILE.SS'),('parch','PARCH.SS'),('difficulty','DIFFICUL.PIK'),('nations','NATIONS.PIK'),('custom','CUSTOMIZ.PIK')] if case.endswith('-'+name+'-source'))
            cursor_source = case_game / source_name
            cursor_source.unlink()
            if case.startswith("bad-"):
                cursor_source.write_bytes(b"damaged")
            if case.startswith("linked-"):
                cursor_source.symlink_to(args.game / source_name)
        if case != "missing-directory":
            shutil.copytree(args.bundle / "graphics", assets)
        if case == "missing-image":
            (assets / "building-032.png").unlink()
        if case == "bad-image":
            (assets / "building-032.png").write_bytes(b"damaged")
        if case == "bad-manifest":
            (assets / "manifest.json").write_bytes(b"{}\n")
        for name in ['opentile-000','openmenu-000','woodtile-000','parch-000','difficul-000','nations-000','customiz-000']:
            path=assets/(name+'.png')
            if case=='missing-'+name:path.unlink()
            if case=='bad-'+name:path.write_bytes(b'damaged')
            if case=='linked-'+name:
                path.unlink();path.symlink_to(args.bundle/'graphics'/path.name)
        if case == "missing-sea":
            (assets / "sea-148.png").unlink()
        if case == "bad-sea":
            (assets / "sea-148.png").write_bytes(b"damaged")
        if case == "linked-sea":
            (assets / "sea-148.png").unlink()
            (assets / "sea-148.png").symlink_to(args.bundle / "graphics/sea-148.png")
        if case == "missing-person":
            (assets / "person-100.png").unlink()
        if case == "bad-person":
            (assets / "person-100.png").write_bytes(b"damaged")
        if case == "linked-person":
            (assets / "person-100.png").unlink()
            (assets / "person-100.png").symlink_to(args.bundle / "graphics/person-100.png")
        if case == "missing-shelter":
            (assets / "building-024.png").unlink()
        if case == "bad-shelter":
            (assets / "building-024.png").write_bytes(b"damaged")
        if case == "linked-shelter":
            (assets / "building-024.png").unlink()
            (assets / "building-024.png").symlink_to(args.bundle / "graphics/building-024.png")
        if case=="missing-terrain079": (assets/"terrain-079.png").unlink()
        if case=="bad-terrain079": (assets/"terrain-079.png").write_bytes(b"damaged")
        if case=="linked-terrain079":
            (assets/"terrain-079.png").unlink(); (assets/"terrain-079.png").symlink_to(args.bundle/"graphics/terrain-079.png")
        for n in terrain_batch:
            name = "terrain-%03d.png"%n
            if case == "missing-terrain-%03d"%n: (assets/name).unlink()
            if case == "bad-terrain-%03d"%n: (assets/name).write_bytes(b"damaged")
            if case == "linked-terrain-%03d"%n:
                (assets/name).unlink(); (assets/name).symlink_to(args.bundle/"graphics"/name)
        if case=="missing-cursor-image": (assets/"cursor-000.png").unlink()
        if case=="bad-cursor-image": (assets/"cursor-000.png").write_bytes(b"damaged")
        if case=="linked-cursor-image":
            (assets/"cursor-000.png").unlink(); (assets/"cursor-000.png").symlink_to(args.bundle/"graphics/cursor-000.png")
        for n in [16,21,27,35,39,42,43,44,45,9]:
            name="building-%03d.png"%n
            if case=="missing-building-%03d"%n: (assets/name).unlink()
            if case=="bad-building-%03d"%n: (assets/name).write_bytes(b"damaged")
            if case=="linked-building-%03d"%n:
                (assets/name).unlink(); (assets/name).symlink_to(args.bundle/"graphics"/name)
        for n in [8, 9, 16, 6, 7, 14, 15, 127, 5, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 42, 53, 56, 59, 62, 67, 68, 69, 94, 122, 123, 124, 58, 60, 66, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 95, 96, 97, 98, 106, 107]:
            name="icons-%03d.png"%n
            if case=="missing-icons-%03d"%n: (assets/name).unlink()
            if case=="bad-icons-%03d"%n: (assets/name).write_bytes(b"damaged")
            if case=="linked-icons-%03d"%n:
                (assets/name).unlink(); (assets/name).symlink_to(args.bundle/"graphics"/name)
        prefix = out / "gui"
        command = ["bash", str(args.bundle / "colonization-cht.sh"), "--game", str(case_game),
                   "--play=false", "--audio-mute", "--window-steps", "100000000",
                   "--display-config", str(preference), "--display-diagnostics", "--native-text-diagnostics",
                   "--hd-assets", str(assets), "--out", str(prefix)]
        env = dict(os.environ, COLONIZATION_CHT_SAVE=str(out / "save"), GOMEMLIMIT="1200MiB", GOMAXPROCS="2")
        log = (out / "process.log").open("wb")
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
        window = None

        def status():
            need(process.poll() is None, "正式前端提前結束：" + case)
            try:
                return json.loads(prefix.with_suffix(".status.json").read_bytes())
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

        def wait(predicate, reason):
            until = time.monotonic() + 45
            while time.monotonic() < until:
                current = status()
                if predicate(current):
                    return current
                time.sleep(0.025)
            raise TimeoutError(reason + ":" + case)

        def xdo(*parts):
            subprocess.run(["xdotool", *map(str, parts)], check=True, timeout=4,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        def click(x, y):
            xdo("mousemove", "--window", window, x, y)
            xdo("mousedown", 1)
            time.sleep(0.08)
            xdo("mouseup", 1)
            time.sleep(0.08)

        try:
            window_wait_started = time.monotonic()
            until = window_wait_started + args.startup_timeout
            while time.monotonic() < until:
                status()
                found = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Colonization CHT"],
                                       capture_output=True, text=True, timeout=3)
                if found.returncode == 0 and found.stdout.strip():
                    window = found.stdout.splitlines()[0]
                    break
                time.sleep(0.025)
            need(window is not None, "找不到正式視窗")
            startup_window_seconds = time.monotonic() - window_wait_started
            xdo("windowfocus", window)
            wait(lambda s: s.get("step", 0) >= 4000000, "冷啟動未推進")
            xdo("mousemove", "--window", window, 115, 24)
            xdo("mousedown", 1)
            wait(lambda s: s.get("display", {}).get("phase") == 1, "設定未暫停")
            xdo("mouseup", 1)
            current = wait(lambda s: s.get("display", {}).get("phase") == 2, "設定未開啟")
            effective = {"language": "ja", "graphics": "hd" if case == "restored" else "original"}
            need(current["display"]["current"] == effective, "啟動有效選項不同")
            live = current.get("frame", {}).get("native_live", {})
            need(live.get("hd_available") == (case == "restored"), "HD可用性不同")
            if case != "restored":
                need(live.get("hd_asset_reason"), "缺件沒有原因收據")
                click(808, 480)
                click(912, 644)
                current = wait(lambda s: s.get("display", {}).get("problem") == "ui.error.unavailable",
                               "缺件仍允許HD套用")
                need(current["display"]["current"] == effective, "失敗交易改變生效選項")
            need(preference.read_bytes() == saved, "啟動或失敗交易改寫HD偏好")
            subprocess.run(["import", "-window", window, str(out / "settings.png")], check=True, timeout=5)
            xdo("keydown", "Escape")
            time.sleep(0.08)
            xdo("keyup", "Escape")
            wait(lambda s: s.get("display", {}).get("phase") == 0, "取消後未恢復")
            events = json.loads(prefix.with_suffix(".display-events.json").read_bytes())
            expected = ["open", "ready"] + ([] if case == "restored" else ["apply-error"]) + ["cancel-escape", "resume"]
            need([e["action"] for e in events] == expected, "設定事件不同")
            need(all(all(e[k] == events[0][k] for k in STATE_KEYS) for e in events),
                 "暫停交易改變原版或輸入")
            subprocess.run([sys.executable, "/repo/tools/gui_close_window.py", "--window", window],
                           check=True, timeout=5, stdout=subprocess.DEVNULL)
            process.wait(timeout=15)
            need(process.returncode == 0 and preference.read_bytes() == saved, "正常結束改寫偏好")
            results.append({"case": case, "effective": effective, "events": len(events),
                            "startup_window_seconds": startup_window_seconds,
                            "reason": live.get("hd_asset_reason"), "command": command,
                            "preferences_unchanged": True, "native_state_unchanged_during_settings": True})
            print("PASS_FORMAL_HD_STARTUP", case, flush=True)
        finally:
            for key in ["Escape", "Return"]:
                try:
                    subprocess.run(["xdotool", "keyup", key], timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.SubprocessError:
                    pass
            try:
                subprocess.run(["xdotool", "mouseup", "1"], timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if process.poll() is None and window is not None:
                    subprocess.run([sys.executable, "/repo/tools/gui_close_window.py", "--window", window],
                                   check=True, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    process.wait(timeout=10)
            except subprocess.SubprocessError:
                pass
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            log.close()
    result = {"result": "PASS_FORMAL_HD_STARTUP_FALLBACK_GUI", "cases": results,
              "binary_sha256": hashlib.sha256((args.bundle / "bin/colonization-window").read_bytes()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
