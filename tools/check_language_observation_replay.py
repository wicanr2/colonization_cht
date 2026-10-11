#!/usr/bin/env python3
"""規格060 DRAFT：完整原文觀測器與既有GUI、前版及原文控制的同輸入比較。"""
import argparse
from collections import Counter
import base64
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


def check_transactions(run, state, rebuilds):
    path = run / "run.language-transactions.json"
    record = json.loads(path.read_bytes())
    require(record["kind"] == "DRAFT-language-bundle-transactions" and record["step"] == state["steps"],
            "交易收據種類或原版步數不同")
    memory = (run / "run.memory").read_bytes()
    native = b"".join([memory[0x2cae0:0x2cae0 + 64000], memory[0x3bb00:0x3bb00 + 64000],
                       (run / "run.final.idx").read_bytes(), (run / "run.final.pal").read_bytes()])
    require(record["native_before_sha256"] == record["native_after_sha256"] == sha(native),
            "交易前後原版畫面來源與完整RAM不同")
    entries = record["transactions"]
    require([e["locale"] for e in entries] == ["zh-Hant", "zh-Hans", "ja", "ko", "en"], "五語交易次序或數量不同")
    for entry in entries:
        require(all(entry[k] is True for k in ["cancel_kept_active", "save_failure_kept_active_and_preferences",
                                               "whole_target_committed"]) and
                entry["saved"] == {"language": entry["locale"], "graphics": "original"} and
                entry["rgba_sha256"] == rebuilds[entry["locale"]]["rgba_sha256"],
                "取消、保存失敗或整包提交未驗證：" + entry["locale"])
    saved = run / "run.display-preferences.json"
    require(json.loads(saved.read_bytes()) == {"language": "en", "graphics": "original"} and
            saved.stat().st_mode & 0o777 == 0o600 and not list(run.glob(".display-*.tmp")),
            "交易結束的設定檔、權限或暫存檔不同")
    return {"receipt_sha256": sha(path.read_bytes()), "preference_sha256": sha(saved.read_bytes()),
            "native_sha256": sha(native), "languages": len(entries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "formal", "gui", "launcher", "seed", "game", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--bundles", type=Path, help="另驗停止DOS後的對話／字串／海上四語重建切片")
    parser.add_argument("--fontless", action="store_true", help="觀測側用原文控制，所有舊遊戲字模與圖集參數指向實際缺檔")
    parser.add_argument("--rebuild-reference", type=Path, help="另核對同原版狀態的既有五語RGBA收據")
    parser.add_argument("--transactions", action="store_true", help="獨立核對五語整包交易、取消與保存失敗收據")
    parser.add_argument("--checkpoint", type=int, help="僅重播正常GUI輸入的前綴，與前版及原文控制互核；不冒充原GUI終點")
    parser.add_argument("--idle-until", type=int, help="沿完整設定GUI輸入延長停留，不新增輸入；四側互核，不冒充原GUI終點")
    parser.add_argument("--checkpoint-source", choices=("settings", "newgame"), default="settings",
                        help="checkpoint輸入來源；newgame僅接受既有已驗證新局GUI指紋")
    parser.add_argument("--expect-fixed", action="append", default=[], help="checkpoint應重建的固定原版欄位鍵，可重複指定")
    args = parser.parse_args()
    require(args.idle_until is None or (args.checkpoint is None and args.checkpoint_source == "settings"),
            "延長停留不能混用前綴停點或其他輸入來源")
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
    checkpoint_provenance = None
    if args.checkpoint_source == "newgame":
        require(args.checkpoint is not None, "newgame來源只用於明示checkpoint")
        source = ROOT / "workplace/reports/goal185-player-experience"
        review = source / "newgame-save-review.json"
        require(sha(review.read_bytes()) == "a775ea0ef731e80c4fb3f3d4e754c87e2fbcafde3858cc5fa2ebd2e4af330073",
                "新局正常GUI驗證收據不同")
        verified = json.loads(review.read_bytes())
        inputs = source / "newgame-save-20261008/gui.inputs.json"
        require(verified["result"] == "PASS_NORMAL_NEWGAME_SAVE_RELOAD" and
                sha(inputs.read_bytes()) == verified["inputs_sha256"] ==
                "bfaf3f2caf06d804bdf4d79376eb057c15fa4a5e157cb7df24a187aa2b1a9e74",
                "新局正常玩家輸入不同")
        receipt = json.loads(inputs.read_bytes())
        require(receipt["end"] == verified["end"], "新局輸入終點不同")
        checkpoint_provenance = {"review_sha256": sha(review.read_bytes()),
                                 "historical_gui_binary_sha256": verified["binary_sha256"],
                                 "scope": "只沿用已驗GUI輸入；不宣稱與歷史新局程式或GUI同狀態"}
    root.mkdir()
    absent_masks = {}
    if args.fontless:
        require(args.bundles, "無字模觀測反例需要完整目標包")
        absent = root / "absent-legacy-masks"
        absent.mkdir()
        for flag in ("font-mask", "font-dir", "nation-card-font-dir", "nation-cards-rest-font-dir",
                     "third-card-font-dir", "intro-mask-dir", "build1-font", "build-caption-font-dir",
                     "help-mask-dir", "sea-atlas", "game-options-title-font", "game-options-rows-font-dir",
                     "retire-font-dir", "static-mask-dir", "dialog-atlas", "string-atlas"):
            absent_masks[flag] = str(absent / flag)
        require(not any(Path(p).exists() for p in absent_masks.values()), "舊字模反例路徑實際存在")
    source_input_sha = sha(inputs.read_bytes())
    source_end = receipt["end"]
    reference_dir, reference_stem = args.gui, "gui"
    expected_end = receipt["end"]
    if args.checkpoint is not None:
        require(args.bundles and args.expect_fixed and 0 < args.checkpoint < expected_end,
                "checkpoint需完整包、預期固定欄位及有效的正常輸入前綴停點")
        expected_end = args.checkpoint
        receipt = {"inputs": [i for i in receipt["inputs"] if i["step"] < expected_end], "end": expected_end}
        inputs = root / "checkpoint.inputs.json"
        inputs.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        baseline, reference_dir, reference_stem = None, None, "run"
    else:
        require(not args.expect_fixed, "expect-fixed只用於明示checkpoint")
    if args.idle_until is not None:
        require(args.bundles and expected_end < args.idle_until <= expected_end + 600000000,
                "停留終點須在既有GUI終點之後，最多增加六億步")
        expected_end = args.idle_until
        receipt = {"inputs": receipt["inputs"], "end": expected_end}
        inputs = root / "idle.inputs.json"
        inputs.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        baseline, reference_dir, reference_stem = None, None, "run"
    results = {}
    observed_extra = ["--draft-native-capture"]
    if args.bundles:
        observed_extra.extend(["--draft-native-bundles", str(args.bundles)])
    if args.fontless:
        observed_extra.append("--control")
        for flag, path in absent_masks.items():
            observed_extra.extend(["--" + flag, path])
    legacy_rgb = None
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
                           check=True, timeout=max(90, 90 * expected_end / source_end))
        report = json.loads((run / "run.json").read_bytes())
        require(report["state"]["steps"] == expected_end, name + "重播步數不同")
        if baseline is None:
            baseline, reference_dir = report["state"], run
        require(report["state"] == baseline, name + "完整原版狀態不同")
        for suffix in ("memory", "final.idx", "final.pal"):
            require((run / ("run." + suffix)).read_bytes() == (reference_dir / (reference_stem + "." + suffix)).read_bytes(), name + "原版bytes不同")
        require(tree(run / "save") == tree(reference_dir / "save"), name + "存檔不同")
        if name != "original-control" and not (name == "observed" and args.fontless):
            with Image.open(run / "run.final.png") as im:
                actual = (im.size, im.convert("RGB").tobytes())
            if args.fontless and (args.checkpoint is not None or args.idle_until is not None):
                if legacy_rgb is None:
                    legacy_rgb = actual
                require(actual == legacy_rgb, name + "既有繁中合成RGB不同")
            else:
                with Image.open(reference_dir / (reference_stem + ".final.png")) as im:
                    require(actual == (im.size, im.convert("RGB").tobytes()), name + "合成RGB不同")
        results[name] = {"state": report["state"], "binary_sha256": sha(binary.read_bytes()),
                         "wav_sha256": sha((run / "audio.wav").read_bytes()), "save_sha256": tree(run / "save")}
        print("PASS_NATIVE_OBSERVATION_REPLAY", name, baseline["steps"], flush=True)
    require(len({v["wav_sha256"] for v in results.values()}) == 1, "四側WAV不同")
    if args.fontless:
        require(not any(Path(p).exists() for p in absent_masks.values()), "重播產生了舊字模反例路徑")
        with Image.open(root / "observed/run.final.png") as a, Image.open(root / "original-control/run.final.png") as b:
            require(a.size == b.size and a.convert("RGB").tobytes() == b.convert("RGB").tobytes(), "無字模觀測側不是原版畫面")
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
        if item["kind"] == "fixed":
            r = item["safe"]
            x0, y0, x1, y1 = r["Min"]["X"], r["Min"]["Y"], r["Max"]["X"], r["Max"]["Y"]
            before = base64.b64decode(item["before_safe"], validate=True)
            after = base64.b64decode(item["after_safe"], validate=True)
            require(0 <= x0 < x1 <= 320 and 0 <= y0 < y1 <= 200 and
                    len(before) == len(after) == (x1 - x0) * (y1 - y0) and before != after and
                    item["surface"] in ("vga", "canvas") and item["id"] == item["text"], "固定欄原文快照不同")
        if item["visible"]:
            base = 0xa0000 if item.get("surface") == "vga" else (0x3bb00 if item["kind"] == "string-map" else 0x2cae0)
            require(captured["video_mode"] == 0x13 and
                    all(memory[base + int(i)] == v for i, v in item["after_pixels"].items()), "宣告可見的原文與完整RAM不符")
            visible[item["kind"]] += 1
            if item["kind"] == "fixed":
                observed = b"".join(memory[base + y * 320 + x0:base + y * 320 + x1] for y in range(y0, y1))
                require(not item["expired"] and observed == after, "固定欄宣告可見但整個安全區不同")
                if "fingerprint" in item:
                    fp = item["fingerprint"]
                    a, b = fp["Min"], fp["Max"]
                    require(0 <= a["X"] <= x0 < x1 <= b["X"] <= 320 and
                            0 <= a["Y"] <= y0 < y1 <= b["Y"] <= 200, "靜態指紋不含完整文字帶")
                    region = b"".join(memory[base+y*320+a["X"]:base+y*320+b["X"]] for y in range(a["Y"], b["Y"]))
                    require(sha(region) == item["fingerprint_sha256"] and
                            sha((root / "observed/run.final.pal").read_bytes()) == item["source_palette_sha256"],
                            "可見靜態欄的獨立RAM指紋或DAC不同")
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
            require(record["kind"] == "DRAFT-paused-native-text-rebuild" and record["locale"] == locale and
                    record["step"] == baseline["steps"], "目標語言或重建步數不同")
            with Image.open(Path(str(prefix) + ".png")) as im:
                rgba, rgb = im.convert("RGBA"), im.convert("RGB")
            require(rgba.size == (1280, 800) and sha(rgba.tobytes()) == record["rgba_sha256"], "重建RGBA不同")
            if locale == "en":
                require(rgb.size == original_rgb.size and rgb.tobytes() == original_rgb.tobytes(), "英文重建不同於原版控制")
            else:
                require(record["items"], "四語重建沒有任何實際欄位")
                if args.checkpoint is None:
                    require(any(item["kind"] == "sea-bar" for item in record["items"]) and
                            any(item["kind"] == "sea-panel" and item["source"].startswith("Spring ") for item in record["items"]) and
                            any(item["kind"] == "sea-panel" and item["source"].startswith("Gold:") for item in record["items"]),
                            "正常GUI基準的頂列、日期或金額未重建")
                else:
                    require({item["id"] for item in record["items"] if item["kind"] == "fixed"} == set(args.expect_fixed),
                            "固定欄位的當次原文重建集合不同於預期")
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
    rebuild_reference = None
    transactions = None
    if args.transactions:
        require(args.bundles, "語言包交易需要完整目標包")
        transactions = check_transactions(root / "observed", baseline, rebuilds)
    if args.rebuild_reference:
        require(args.bundles, "RGBA比較需要完整目標包")
        reference = json.loads(args.rebuild_reference.read_bytes())
        require(reference["result"].startswith("PASS_NATIVE_") and
                reference["runs"]["observed"]["state"] == results["observed"]["state"], "RGBA參考的原版狀態不同")
        for locale, record in rebuilds.items():
            require(record["rgba_sha256"] == reference["draft_native_text_rebuilds"][locale]["rgba_sha256"], locale + "重建與既有RGBA不同")
        rebuild_reference = sha(args.rebuild_reference.read_bytes())
    result = {"result": "PASS_NATIVE_OBSERVATIONS_FOUR_REPLAYS", "runs": results,
              "dos_inputs": len(receipt["inputs"]), "source_counts": dict(counts), "visible_source_counts": dict(visible),
              "accepted": captured["accepted"], "rejected": captured["rejected"], "evicted_by_limit": captured["evicted_by_limit"],
              "draft_native_text_rebuilds": rebuilds,
              "source_sha256": {"inputs": sha(inputs.read_bytes()), "seed": sha(seed), "launcher": sha(args.launcher.read_bytes()),
                                "probe": sha(Path(__file__).read_bytes()), "capture": sha((root / "observed/run.native.json").read_bytes())},
              "limitations": ["原文觀測與可選的停止重建切片；固定欄正常GUI抽樣、完整畫面重建及正式快取交換尚未驗收。",
                               "沿既有正常GUI輸入重播，本輪沒有新增現場GUI或HD驗收。"]}
    if args.checkpoint is not None:
        result["result"] = "PASS_NATIVE_FIXED_CHECKPOINT_FOUR_REPLAYS"
        result["checkpoint"] = {"step": expected_end, "expected_fixed": args.expect_fixed,
                                "source": args.checkpoint_source,
                                "source_gui_inputs_sha256": source_input_sha,
                                "comparison": "正常GUI輸入前綴；四側同狀態，沒有此停點的新增現場GUI信用"}
        if checkpoint_provenance:
            result["checkpoint"]["provenance"] = checkpoint_provenance
    if args.fontless:
        result["fontless_observation"] = {"legacy_mask_overrides": absent_masks, "all_paths_absent": True,
                                          "observed_rgb_equals_native_control": True}
    if args.idle_until is not None:
        result["result"] = "PASS_NATIVE_IDLE_FOUR_REPLAYS"
        result["idle"] = {"step": expected_end, "source_gui_inputs_sha256": source_input_sha,
                          "comparison": "完整正常GUI輸入後延長停留；沒有新增輸入或現場GUI信用"}
    if rebuild_reference:
        result["rebuild_reference_sha256"] = rebuild_reference
    if transactions:
        result["language_bundle_transactions"] = transactions
    (root / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    require(all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in root.rglob("*")), "輸出擁有權不同")
    print(result["result"], sha((root / "check.json").read_bytes()))


if __name__ == "__main__":
    main()
