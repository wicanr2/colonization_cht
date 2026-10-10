#!/usr/bin/env python3
"""規格051：以真GUI收據比較設定原型、正式前端與原文控制的原版狀態。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


ROOT = Path(__file__).resolve().parent.parent


def need(value, message):
    if not value:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree(path):
    return {str(p.relative_to(path)): sha(p.read_bytes()) for p in sorted(path.rglob("*")) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["gui", "prototype", "formal", "launcher", "game", "seed", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    need(Path("/.dockerenv").is_file(), "請在Docker內執行")
    output = args.output.resolve()
    need(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists(), "需新的workplace輸出目錄")
    need(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(), "輸出父目錄擁有者不符")
    gui_check = json.loads((args.gui / "check.json").read_text())
    need(gui_check["result"] == "PASS_SETTINGS_NORMAL_GUI_PROTOTYPE", "GUI驗證未通過")
    seed = args.seed.read_bytes()
    need(sha(seed) == gui_check["source_sha256"]["seed"], "初始存檔不符GUI")
    need(sha(args.prototype.read_bytes()) == gui_check["source_sha256"]["binary"], "原型程式不符GUI")
    launcher_source = args.launcher.read_text()
    need(sha(args.launcher.read_bytes()) == gui_check["source_sha256"]["launcher"], "啟動器不符GUI")
    marker = "exec /out/issue56-source-connection-audit/colonization-window "
    need(launcher_source.count(marker) == 1, "啟動器替換點不唯一")
    inputs = args.gui / "gui.inputs.json"
    need(sha(inputs.read_bytes()) == gui_check["gui_inputs_sha256"], "GUI輸入收據不符")
    receipt = json.loads(inputs.read_text())
    baseline = json.loads((args.gui / "gui.json").read_text())["state"]
    need(receipt["end"] == baseline["steps"], "GUI原版終點與輸入收據不符")
    events = json.loads((args.gui / "gui.display-events.json").read_text())
    need(sha((args.gui / "gui.display-events.json").read_bytes()) == gui_check["events_sha256"],
         "設定事件收據不符GUI摘要")
    need(all(x["kind"] in ["move", "press", "release", "enter"] for x in receipt["inputs"]),
         "設定測試鍵流入原版收據")
    output.mkdir()
    runs = {}
    for name, binary, control in [("prototype", args.prototype, False),
                                  ("formal", args.formal, False), ("original-control", args.formal, True)]:
        run = output / name
        run.mkdir()
        save = run / "save"
        save.mkdir()
        (save / "COLONY09.SAV").write_bytes(seed)
        launcher = run / "launch.sh"
        launcher.write_text(launcher_source.replace(marker, "exec " + shlex.quote(str(binary)) + " ", 1))
        env = os.environ.copy()
        env["COLONIZATION_CHT_SAVE"] = str(save)
        cmd = ["bash", str(launcher), "--game", str(args.game), "--play=false", "--audio-mute",
               "--window-steps", str(receipt["end"]), "--replay-inputs", str(inputs),
               "--audio-wav", str(run / "audio.wav"), "--out", str(run / "run")]
        if control:
            cmd.append("--control")
        with (run / "process.log").open("wb") as log:
            subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=90)
        state = json.loads((run / "run.json").read_text())["state"]
        need(state == baseline, f"{name}原版CPU／記憶體／影像／時鐘與真GUI不相同")
        for extension in ["memory", "final.idx", "final.pal"]:
            need((run / ("run." + extension)).read_bytes() == (args.gui / ("gui." + extension)).read_bytes(),
                 f"{name}/{extension}原版bytes不相同")
        need(tree(save) == tree(args.gui / "save"), f"{name}存檔不相同")
        if not control:
            need((run / "run.final.png").read_bytes() == (args.gui / "gui.final.png").read_bytes(),
                 f"{name}繁中合成與GUI終點不同")
        runs[name] = {"binary_sha256": sha(binary.read_bytes()), "state": state,
                      "memory_sha256": sha((run / "run.memory").read_bytes()),
                      "wav_sha256": sha((run / "audio.wav").read_bytes()), "save_sha256": tree(save)}
        print("PASS", name, receipt["end"], flush=True)
    need(len({r["wav_sha256"] for r in runs.values()}) == 1, "三種重播的原版音訊不同")
    result = {"result": "PASS_SETTINGS_GUI_THREE_REPLAYS", "gui_state": baseline, "runs": runs,
              "source_sha256": {"inputs": sha(inputs.read_bytes()), "events": sha((args.gui / "gui.display-events.json").read_bytes()),
                                "seed": sha(seed), "probe": sha(Path(__file__).read_bytes())},
              "settings_events": len(events), "dos_inputs": len(receipt["inputs"]),
              "limitations": ["No hardware audio or macOS runtime validation.",
                              "Replay WAV equality does not prove wall-clock GUI audio synchronization.",
                              "Only existing Chinese and original English presentation; not full five-language or HD completion."]}
    (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["result"])


if __name__ == "__main__":
    main()
