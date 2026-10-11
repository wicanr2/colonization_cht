#!/usr/bin/env python3
"""規格060 DRAFT：沿隔離五語GUI的真實輸入核對四側原版狀態。"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess

from PIL import Image

from check_language_observation_replay import check_transactions, require, sha, tree

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["binary", "formal", "gui", "launcher", "seed", "game", "bundles", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file() and os.environ.get("DISPLAY"), "需Docker與有界Xvfb")
    root = args.output.resolve()
    require(root.is_relative_to((ROOT / "workplace").resolve()) and not root.exists() and
            root.parent.is_dir() and root.parent.stat().st_uid == os.getuid(), "需新的workplace輸出")
    gui_path = args.gui / "check.json"
    gui = json.loads(gui_path.read_bytes())
    scenes = ["main-menu", "world", "colony"]
    if "normal_save_cycle" in gui:
        saved = gui["normal_save_cycle"]
        require(saved.get("kind") == "normal-gui-save-slot-success-return" and
                saved.get("created") == "COLONY00.SAV" and
                saved.get("sha256") == sha((args.gui / "save/COLONY00.SAV").read_bytes()), "正常存檔收據不同")
        scenes += ["save-slots", "save-success", "saved-world"]
    initial_extra = {}
    if "normal_load_cycle" in gui:
        loaded = gui["normal_load_cycle"]
        require("normal_save_cycle" not in gui and loaded.get("kind") == "new-process-normal-load-and-colony-return" and
                loaded.get("loaded") == "COLONY00.SAV" and
                loaded.get("initial_saves") == tree(args.gui / "save"), "新行程讀回存檔收據不同")
        require(set(loaded["initial_saves"]) == {"COLONY00.SAV", "COLONY09.SAV"}, "新行程初始存檔清冊不同")
        initial_extra["COLONY00.SAV"] = (args.gui / "save/COLONY00.SAV").read_bytes()
        scenes = ["main-menu", "load-slots", "load-success", "loaded-world", "colony"]
    if any(c.get("scene") == "input-original" for c in gui.get("checks", [])):
        scenes += ["input-original", "input-backspace", "input-restored", "input-cancelled"]
    require(gui["result"] == "PASS_NATIVE_LIVE_FIVE_LANGUAGE_GUI" and
            sorted((c["scene"], c["locale"]) for c in gui["checks"]) ==
            sorted((s, l) for s in scenes for l in ["zh-Hant", "zh-Hans", "ja", "ko", "en"]),
            "隔離五語GUI尚未通過")
    require(sha(args.binary.read_bytes()) == gui["source_sha256"]["binary"], "GUI二進位不同")
    launcher = args.launcher.read_text()
    marker = "exec /out/issue56-source-connection-audit/colonization-window "
    require(launcher.count(marker) == 1 and sha(args.launcher.read_bytes()) == gui["source_sha256"]["launcher"], "啟動器不同")
    seed = args.seed.read_bytes()
    require(sha(seed) == gui["source_sha256"]["seed"], "初始存檔不同")
    inputs = args.gui / "gui.inputs.json"
    require(sha(inputs.read_bytes()) == gui["gui_inputs_sha256"], "實際GUI輸入不同")
    receipt = json.loads(inputs.read_bytes())
    baseline = json.loads((args.gui / "gui.json").read_bytes())["state"]
    require(receipt["end"] == baseline["steps"], "GUI終點不同")
    root.mkdir()
    results = {}
    shared = ["--draft-native-capture", "--draft-native-bundles", str(args.bundles)]
    for name, binary, extra in [("live", args.binary, shared + ["--draft-native-live", "--display-settings",
                                                             "--display-language", "zh-Hant", "--display-graphics", "original"]),
                                ("observed", args.binary, shared), ("formal", args.formal, []),
                                ("original-control", args.formal, ["--control"])]:
        run = root / name
        (run / "save").mkdir(parents=True)
        (run / "save/COLONY09.SAV").write_bytes(seed)
        for save_name, contents in initial_extra.items():
            (run / "save" / save_name).write_bytes(contents)
        script = run / "launch.sh"
        script.write_text(launcher.replace(marker, "exec " + shlex.quote(str(binary)) + " ", 1))
        env = os.environ.copy()
        env["COLONIZATION_CHT_SAVE"] = str(run / "save")
        command = ["bash", str(script), "--game", str(args.game), "--play=false", "--audio-mute",
                   "--window-steps", str(receipt["end"]), "--replay-inputs", str(inputs),
                   "--audio-wav", str(run / "audio.wav"), "--out", str(run / "run"), *extra]
        if name == "live":
            command.extend(["--display-config", str(run / "display.json")])
        with (run / "process.log").open("wb") as log:
            subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=max(90, baseline["steps"] / 750000))
        report = json.loads((run / "run.json").read_bytes())
        require(report["state"] == baseline, name + "完整原版狀態不同於GUI")
        for suffix in ["memory", "final.idx", "final.pal"]:
            require((run / ("run." + suffix)).read_bytes() == (args.gui / ("gui." + suffix)).read_bytes(),
                    name + "原版bytes不同於GUI")
        require(tree(run / "save") == tree(args.gui / "save"), name + "存檔不同")
        if name == "live":
            with Image.open(run / "run.final.png") as a, Image.open(args.gui / "gui.final.png") as b:
                require(a.size == b.size and a.convert("RGBA").tobytes() == b.convert("RGBA").tobytes(),
                        "隔離視窗重播畫面不同於GUI終點")
        results[name] = {"state": report["state"], "binary_sha256": sha(binary.read_bytes()),
                         "wav_sha256": sha((run / "audio.wav").read_bytes()), "save_sha256": tree(run / "save")}
        print("PASS_NATIVE_LIVE_REPLAY", name, baseline["steps"], flush=True)
    require(len({x["wav_sha256"] for x in results.values()}) == 1, "四側重播WAV不同")
    with Image.open(root / "formal/run.final.png") as a, Image.open(root / "observed/run.final.png") as b:
        require(a.size == b.size and a.convert("RGBA").tobytes() == b.convert("RGBA").tobytes(),
                "觀測模式改變既有前版畫面")
    rebuilds, transactions = {}, {}
    for name in ["live", "observed"]:
        rebuilt = {}
        for locale in ["zh-Hant", "zh-Hans", "ja", "ko", "en"]:
            prefix = root / name / ("run.rebuild-" + locale)
            record = json.loads(Path(str(prefix) + ".json").read_bytes())
            with Image.open(Path(str(prefix) + ".png")) as im:
                rgba, rgb = im.convert("RGBA").tobytes(), im.convert("RGB").tobytes()
                require(sha(rgba) == record["rgba_sha256"], "五語重建RGBA指紋不同")
            if locale == "en":
                with Image.open(root / "original-control/run.final.png") as original:
                    require(rgb == original.convert("RGB").tobytes(), "英文重建不同於原版")
            else:
                require(record.get("items"), "非英文終點沒有實際重建欄位")
            rebuilt[locale] = {"rgba_sha256": record["rgba_sha256"], "items": len(record.get("items") or [])}
        rebuilds[name] = rebuilt
        transactions[name] = check_transactions(root / name, baseline, rebuilt)
    require(rebuilds["live"] == rebuilds["observed"], "即時與停止重建的五語畫面不同")
    result = {"result": "PASS_NATIVE_LIVE_GUI_FOUR_REPLAYS", "runs": results, "rebuilds": rebuilds,
              "language_transactions": transactions, "dos_inputs": len(receipt["inputs"]),
              "source_sha256": {"gui": sha(gui_path.read_bytes()), "inputs": sha(inputs.read_bytes()),
                                "probe": sha(Path(__file__).read_bytes()),
                                "transaction_checker": sha((ROOT / "tools/check_language_observation_replay.py").read_bytes())},
              "limitations": ["隔離視窗及本次正常路徑；完整來源生命週期、正式接線及HD未完成。"]}
    (root / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in root.rglob("*")), "輸出擁有權不同")
    print(result["result"], sha((root / "check.json").read_bytes()), flush=True)


if __name__ == "__main__":
    main()
