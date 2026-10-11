#!/usr/bin/env python3
"""規格054：核對四語真GUI、同輸入四側與六列範圍，不執行或改寫遊戲。"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops

from language_catalog import ROOT, canonical, new_output, require, sha

LOCALES = ("zh-Hant", "zh-Hans", "ja", "ko")
MODES = ("locale", "control", "default", "invalid")
OPEN = {"compact-menu", "compact-hover-disabled", "compact-reopened", "compact-second-open",
        "compact-hover-active", "compact-third-open"}
CLOSED = {"compact-disabled-dismissed", "compact-cancel", "compact-second-cancel", "compact-activate-result"}
SAFE = (320, 48, 636, 308)
FIELD = "MENU.TXT:0x000003BC+list"


def read(path):
    return json.loads(path.read_text())


def pixels(path):
    with Image.open(path) as im:
        require(im.size == (1280, 800), "遊戲畫布大小不同")
        return im.convert("RGBA").tobytes()


def check(reports, build, atlas):
    for assembled, source in {"adapter.go": "live_menu.go", "dialog.go": "dialog_overlay.go",
                              "strings.go": "string_overlay.go", "noto_orders.go": "noto_orders.go",
                              "noto_orders_test.go": "noto_orders_test.go"}.items():
        require((build / assembled).read_bytes() == (ROOT / "tools" / source).read_bytes(), "建置來源不同")
    tests = [json.loads(line) for line in (build / "tests-with-fixtures.json").read_text().splitlines()]
    require(not any(e["Action"] in ("fail", "skip") for e in tests), "Go測試失敗或略過")
    passed = {e.get("Test") for e in tests if e["Action"] == "pass" and e.get("Test")}
    require(all("TestNotoOrdersActualCatalogAndMasks/" + locale in passed for locale in LOCALES) and
            "TestNotoOrdersFieldIsolation" in passed and not (build / "vet.log").read_text().strip(), "缺少正式回歸")
    inputs = read(reports / "input-sources.json")
    require(inputs["binary"] == sha((build / "colonization-window").read_bytes()), "GUI使用不同建置")
    baked = read(atlas / "bake-check.json")
    for name, digest in baked["outputs_sha256"].items():
        require(Path(name).name == name and sha((atlas / name).read_bytes()) == digest, "圖集產物指紋不同")
    result = {}
    for locale in LOCALES:
        gui = reports / ("gui-" + locale)
        g = read(gui / "gui.json")
        require(g["noto_orders"] == {"locale": locale, "reason": "", "font_px": 18}, "GUI未載入指定Noto")
        events = [e for e in g["events"] if e.get("stage") == "source" and e.get("candidate_id") == FIELD and e.get("font_px") == 18]
        require(events and all(e["safe"] == [80, 12, 159, 77] and len(e["items"]) == 6 and
                              e["entry_ip"] == "0D21:00C6" and e["source_linear"] == 175684 for e in events), "缺原版完整來源事件")
        require(any(e.get("stage") == "active" and e.get("candidate_id") == FIELD for e in g["events"]), "沒有實際啟用遮罩")
        peers = {mode: reports / ("replay-" + locale + "-" + mode) for mode in MODES}
        data = {mode: read(path / "run.json") for mode, path in peers.items()}
        for mode, path in peers.items():
            command = read(path / "command.json")
            require(Path(command[command.index("--replay-inputs") + 1]).samefile(gui / "gui.inputs.json"), "不是GUI實際輸入")
            require(("--control" in command) == (mode == "control") and
                    ("--noto-orders-locale" in command) == (mode != "default"), "重播模式不同")
            require(data[mode]["state"] == g["state"] and data[mode]["input_hashes"] == g["input_hashes"], "原版完整狀態不同")
            require((path / "run.memory").read_bytes() == (gui / "gui.memory").read_bytes() and
                    (path / "raw.wav").read_bytes() == (gui / "raw.wav").read_bytes(), "RAM或WAV不同")
            saves = {p.name: sha(p.read_bytes()) for p in (path / "save").glob("*.SAV")}
            require(saves == inputs["seed"] == {p.name: sha(p.read_bytes()) for p in (gui / "save").glob("*.SAV")}, "存檔不同")
        require(data["invalid"]["noto_orders"]["reason"] == "font-binding-mismatch" and
                any(k.startswith("noto-orders-font-binding-mismatch") for k in data["invalid"]["dialog_misses"]), "錯區域未記錄回退")
        points = {mode: {c["label"]: c for c in j["checkpoints"]} for mode, j in data.items()}
        captures = {e["name"]: e for e in map(json.loads, (gui / "gui.capture-attempts.jsonl").read_text().splitlines()) if e.get("aligned")}
        shots = [line.split() for line in (gui / "gui.shots").read_text().splitlines()]
        require(len(shots) == 15 and OPEN | CLOSED <= {name for name, _ in shots}, "正常玩家路徑缺少操作")
        changes = []
        for name, step in shots:
            stem = "run.cp-" + step
            image = gui / ("gui." + name + ".png")
            require(pixels(image) == pixels(peers["locale"] / (stem + ".png")), "GUI與重播像素不同")
            require(captures[name]["frame_step"] == int(step) and captures[name]["capture_rgba_sha256"] == sha(pixels(image)), "截圖未同步")
            for key in ("memory_sha256", "raw_sha256", "palette_sha256"):
                require(len({points[m]["cp-" + step][key] for m in MODES}) == 1, "取樣原版狀態不同")
            for extension in ("idx", "pal"):
                require(len({(p / (stem + "." + extension)).read_bytes() for p in peers.values()}) == 1, "原版VGA或色盤不同")
            new = Image.open(peers["locale"] / (stem + ".png")).convert("RGB")
            old = Image.open(peers["default"] / (stem + ".png")).convert("RGB")
            fallback = Image.open(peers["invalid"] / (stem + ".png")).convert("RGB")
            control = Image.open(peers["control"] / (stem + ".png")).convert("RGB")
            diff = ImageChops.difference(new, old)
            if name in OPEN:
                require(diff.getbbox(), "命令欄未替換Noto")
                outside = diff.copy(); outside.paste((0, 0, 0), SAFE)
                require(not outside.getbbox(), "六列外發生變更")
                require(fallback.crop(SAFE).tobytes() == control.crop(SAFE).tobytes(), "錯圖集未整欄回原文")
                outside = ImageChops.difference(fallback, old); outside.paste((0, 0, 0), SAFE)
                require(not outside.getbbox(), "回退影響六列外顯示")
                idx = (peers["control"] / (stem + ".idx")).read_bytes()
                for top in (21, 29, 37, 53):
                    x, y = next((x, y) for y in range(top, top + 6) for x in range(81, 158) if idx[y * 320 + x] == 8)
                    color = control.getpixel((x * 4, y * 4))
                    require(sum(new.getpixel((x, y)) == color for y in range(top * 4, (top + 6) * 4)
                                for x in range(324, 636)) > 20, "停用色層遺失")
                changes.append({"name": name, "safe": list(SAFE), "difference": list(diff.getbbox())})
            else:
                require(not diff.getbbox() and fallback.tobytes() == old.tobytes(), "關單或其他畫面留有Noto差異")
            if name in CLOSED:
                border = [(x * 4, y * 4) for x in range(76, 164) for y in (9, 77)]
                border += [(x * 4, y * 4) for y in range(9, 78) for x in (76, 163)]
                require(not all(new.getpixel(p) == (0, 0, 0) for p in border), "命令單未關閉")
        result[locale] = {"samples": len(shots), "source_events": len(events), "changes": changes,
                          "inputs_sha256": sha((gui / "gui.inputs.json").read_bytes()),
                          "final_step": g["state"]["steps"], "final_memory_sha256": g["state"]["memory_sha256"]}
    return {"status": "PASS_SPEC054_NORMAL_GUI_AND_NATIVE_STATE", "binary_sha256": inputs["binary"],
            "go_tests": len(passed), "skip": 0, "locales": result,
            "script_sha256": sha(Path(__file__).read_bytes()), "bake_check_sha256": sha((atlas / "bake-check.json").read_bytes()),
            "limitations": ["Only six measured compact ORDERS rows; no full language or settings integration.",
                            "Native seed comes from recorded COLONY02 load; no rules or RNG comparison points are added.",
                            "Fortify source offsets remain indistinguishable; equal display text is required.",
                            "Saves are compared unchanged; this field test does not claim a new save/load format."]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("reports", "build", "atlas", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    require(Path("/.dockerenv").is_file(), "請在Docker內驗證")
    result = check(args.reports, args.build, args.atlas)
    new_output(args.output).write_bytes(canonical(result) + b"\n")
    print(result["status"], result["go_tests"], sum(r["samples"] for r in result["locales"].values()))


if __name__ == "__main__":
    main()
