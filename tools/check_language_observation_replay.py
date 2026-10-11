#!/usr/bin/env python3
"""規格060 DRAFT：完整原文觀測器與既有GUI、前版及原文控制的同輸入比較。"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree(path):
    return {str(p.relative_to(path)): sha(p.read_bytes()) for p in sorted(path.rglob("*")) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "formal", "gui", "launcher", "seed", "game", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--bundles", type=Path, help="另驗停止DOS後的對話／字串四語重建切片")
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file() and os.environ.get("DISPLAY"), "需Docker及有界Xvfb")
    root = args.output.resolve()
    require(root.is_relative_to((ROOT / "workplace").resolve()) and not root.exists() and
            root.parent.is_dir() and root.parent.stat().st_uid == os.getuid(), "需新的workplace輸出")
    gui = json.loads((args.gui / "check.json").read_bytes())
    require(gui["result"] == "PASS_SETTINGS_NORMAL_GUI_PROTOTYPE", "正常GUI基準未驗證")
    require(sha(args.formal.read_bytes()) == gui["source_sha256"]["binary"], "前版程式不同於GUI基準")
    seed = args.seed.read_bytes()
    require(sha(seed) == gui["source_sha256"]["seed"], "初始存檔不同")
    launcher = args.launcher.read_text()
    require(sha(args.launcher.read_bytes()) == gui["source_sha256"]["launcher"], "啟動器不同")
    marker = "exec /out/issue56-source-connection-audit/colonization-window "
    require(launcher.count(marker) == 1, "啟動器替換點不唯一")
    inputs = args.gui / "gui.inputs.json"
    require(sha(inputs.read_bytes()) == gui["gui_inputs_sha256"], "正常玩家輸入不同")
    baseline = json.loads((args.gui / "gui.json").read_bytes())["state"]
    receipt = json.loads(inputs.read_bytes())
    require(receipt["end"] == baseline["steps"], "原版終點不同")
    root.mkdir()
    results = {}
    observed_extra = ["--draft-native-capture"]
    if args.bundles:
        observed_extra.extend(["--draft-native-bundles", str(args.bundles)])
    for name, binary, extra in [("observed", args.binary, observed_extra),
                                ("disabled", args.binary, []), ("formal", args.formal, []),
                                ("original-control", args.formal, ["--control"])]:
        run = root / name
        (run / "save").mkdir(parents=True)
        (run / "save/COLONY09.SAV").write_bytes(seed)
        script = run / "launch.sh"
        script.write_text(launcher.replace(marker, "exec " + shlex.quote(str(binary)) + " ", 1))
        env = os.environ.copy()
        env["COLONIZATION_CHT_SAVE"] = str(run / "save")
        command = ["bash", str(script), "--game", str(args.game), "--play=false", "--audio-mute",
                   "--window-steps", str(receipt["end"]), "--replay-inputs", str(inputs),
                   "--audio-wav", str(run / "audio.wav"), "--out", str(run / "run"), *extra]
        with (run / "process.log").open("wb") as log:
            subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=90)
        report = json.loads((run / "run.json").read_bytes())
        require(report["state"] == baseline, name + "完整原版狀態不同")
        for suffix in ("memory", "final.idx", "final.pal"):
            require((run / ("run." + suffix)).read_bytes() == (args.gui / ("gui." + suffix)).read_bytes(), name + "原版bytes不同")
        require(tree(run / "save") == tree(args.gui / "save"), name + "存檔不同")
        if name != "original-control":
            with Image.open(run / "run.final.png") as a, Image.open(args.gui / "gui.final.png") as b:
                require(a.size == b.size and a.convert("RGB").tobytes() == b.convert("RGB").tobytes(), name + "合成RGB不同")
        results[name] = {"state": report["state"], "binary_sha256": sha(binary.read_bytes()),
                         "wav_sha256": sha((run / "audio.wav").read_bytes()), "save_sha256": tree(run / "save")}
        print("PASS_NATIVE_OBSERVATION_REPLAY", name, baseline["steps"], flush=True)
    require(len({v["wav_sha256"] for v in results.values()}) == 1, "四側WAV不同")
    captured = json.loads((root / "observed/run.native.json").read_bytes())
    require(captured["kind"] == "DRAFT-native-observations-not-language-rebuild" and
            captured["cost"] <= captured["max_cost"] and len(captured["items"]) <= captured["max_items"], "觀測種類或容量不同")
    require(captured["accepted"] > 0 and captured["items"], "未捕捉任何原文")
    require(not (root / "disabled/run.native.json").exists(), "關閉觀測仍輸出收據")
    memory = (root / "observed/run.memory").read_bytes()
    counts, visible = Counter(), Counter()
    for item in captured["items"]:
        counts[item["kind"]] += 1
        require(len(item["after_pixels"]) == item["source_pixels"] > 0, "來源像素數不同")
        require(all(0 <= int(i) < 64000 and 0 <= v <= 255 for i, v in item["after_pixels"].items()), "來源像素越界")
        require(item["text"] and item["step"] <= baseline["steps"], "原文或事件步數不同")
        if item["visible"]:
            base = 0x3bb00 if item["kind"] == "string-map" else 0x2cae0
            require(captured["video_mode"] == 0x13 and
                    all(memory[base + int(i)] == v for i, v in item["after_pixels"].items()), "宣告可見的原文與完整RAM不符")
            visible[item["kind"]] += 1
    require(any(visible.values()), "終點沒有完整來源像素可核對")
    rebuilds = {}
    if args.bundles:
        report = json.loads((root / "observed/run.json").read_bytes())
        require(report.get("draft_rebuild_native_state_unchanged") is True, "缺少重建前後完整原版狀態核對")
        with Image.open(root / "original-control/run.final.png") as original:
            original_rgb = original.convert("RGB")
        for locale in ("zh-Hant", "zh-Hans", "ja", "ko", "en"):
            prefix = root / ("observed/run.rebuild-" + locale)
            record = json.loads(Path(str(prefix) + ".json").read_bytes())
            require(record["kind"] == "DRAFT-paused-dialog-string-rebuild" and record["locale"] == locale and
                    record["step"] == baseline["steps"], "目標語言或重建步數不同")
            with Image.open(Path(str(prefix) + ".png")) as im:
                rgba, rgb = im.convert("RGBA"), im.convert("RGB")
            require(rgba.size == (1280, 800) and sha(rgba.tobytes()) == record["rgba_sha256"], "重建RGBA不同")
            if locale == "en":
                require(rgb.size == original_rgb.size and rgb.tobytes() == original_rgb.tobytes(), "英文重建不同於原版控制")
            else:
                require(record["items"], "四語重建沒有任何實際欄位")
                safe = Image.new("1", rgb.size)
                from PIL import ImageDraw
                draw = ImageDraw.Draw(safe)
                for item in record["items"]:
                    r = item["safe"]
                    x0, y0, x1, y1 = r["Min"]["X"] * 4, r["Min"]["Y"] * 4, r["Max"]["X"] * 4, r["Max"]["Y"] * 4
                    require(0 <= x0 < x1 <= 1280 and 0 <= y0 < y1 <= 800 and item["font_px"] > 0 and item["text"], "重建欄位越界或空白")
                    draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=1)
                from PIL import ImageChops
                difference = ImageChops.difference(rgb, original_rgb)
                require(difference.getbbox() is not None, "重建仍為原文")
                outside = Image.composite(difference, Image.new("RGB", rgb.size), safe.point(lambda v: 0 if v else 255, "1"))
                require(outside.getbbox() is None, "重建改動畫面安全區以外")
            rebuilds[locale] = {"items": len(record["items"]), "rgba_sha256": record["rgba_sha256"],
                               "receipt_sha256": sha(Path(str(prefix) + ".json").read_bytes())}
    result = {"result": "PASS_NATIVE_OBSERVATIONS_FOUR_REPLAYS", "runs": results,
              "dos_inputs": len(receipt["inputs"]), "source_counts": dict(counts), "visible_source_counts": dict(visible),
              "accepted": captured["accepted"], "rejected": captured["rejected"], "evicted_by_limit": captured["evicted_by_limit"],
              "draft_dialog_string_rebuilds": rebuilds,
              "source_sha256": {"inputs": sha(inputs.read_bytes()), "seed": sha(seed), "launcher": sha(args.launcher.read_bytes()),
                                "probe": sha(Path(__file__).read_bytes()), "capture": sha((root / "observed/run.native.json").read_bytes())},
              "limitations": ["原文觀測與可選的對話／字串重建切片；完整畫面重建及正式快取交換尚未驗收。",
                               "沿既有正常GUI輸入重播，本輪沒有新增現場GUI或HD驗收。"]}
    (root / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in root.rglob("*")), "輸出擁有權不同")
    print(result["result"], sha((root / "check.json").read_bytes()))


if __name__ == "__main__":
    main()
