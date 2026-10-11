#!/usr/bin/env python3
"""規格055：四語正常GUI、五列游標及同輸入四側狀態驗收。"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops

from bake_noto_menu import FIELDS, KEYS
from check_noto_orders import MODES, pixels, read
from language_catalog import ROOT, canonical, new_output, require, sha

LOCALES = ("zh-Hant", "zh-Hans", "ja", "ko")
OPEN = {"main-menu", "menu-cleared", "menu-returned"} | {f"hover-{i}" for i in range(1,6)}
CLOSED = {"load-slots", "new-game"}
SAFES = [(344,y*4,928,(y+7)*4) for _,_,y,_,_,_ in FIELDS]


def check(reports, build, atlas, repeat):
    for assembled, source in {"adapter.go":"live_menu.go", "noto_menu.go":"noto_menu.go",
                              "noto_menu_test.go":"noto_menu_test.go", "noto_orders.go":"noto_orders.go",
                              "dialog.go":"dialog_overlay.go"}.items():
        require((build/assembled).read_bytes() == (ROOT/"tools"/source).read_bytes(), "建置來源不同")
    tests = [json.loads(line) for line in (build/"tests-with-fixtures.json").read_text().splitlines()]
    require(not any(e["Action"] in ("fail","skip") for e in tests), "測試失敗或略過")
    passed = {e.get("Test") for e in tests if e["Action"] == "pass" and e.get("Test")}
    require(all("TestNotoMenuActualFields/"+loc in passed and "TestNotoOrdersActualCatalogAndMasks/"+loc in passed for loc in LOCALES)
            and not (build/"vet.log").read_text().strip(), "缺少正式回歸")
    inputs = read(reports/"input-sources.json")
    require(inputs["binary"] == sha((build/"colonization-window").read_bytes()), "GUI建置不同")
    baked = read(atlas/"bake-check.json")
    products = dict(baked["outputs_sha256"], **{"bake-check.json":sha((atlas/"bake-check.json").read_bytes())})
    for name,digest in products.items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and
                sha((atlas/name).read_bytes()) == sha((repeat/name).read_bytes()) == digest, "重生字模不同")
    result = {}
    for locale in LOCALES:
        gui = reports/("gui-"+locale); g = read(gui/"gui.json")
        require(g["noto_menu"] == {"locale":locale,"reason":"","font_px":[24,24,20,20,24]}, "未載入指定Noto")
        source_counts = {}
        for key,(_,_,_,_,_,count) in zip(KEYS,FIELDS):
            es = [e for e in g["events"] if e.get("candidate_id") == key and e.get("accepted")]
            require(len(es)>=2 and all(e["entry_ip"] == "937C:0538" and e["return_ip"] == "937C:1D50" and
                    e["return_sp"] == (e["entry_sp"]+10)&65535 and e["changed_pixels"] == count and
                    e["descriptor_hex"] == "0000fe000800fc00fd0000000000" for e in es), "缺初始或重畫來源事件")
            source_counts[key] = len(es)
        peers = {mode:reports/("replay-"+locale+"-"+mode) for mode in MODES}
        data = {mode:read(path/"run.json") for mode,path in peers.items()}
        for mode,path in peers.items():
            command = read(path/"command.json")
            require(Path(command[command.index("--replay-inputs")+1]).samefile(gui/"gui.inputs.json") and
                    ("--control" in command) == (mode=="control") and ("--noto-menu-locale" in command) == (mode!="default"), "非GUI實際輸入或模式不同")
            require(data[mode]["state"] == g["state"] and data[mode]["input_hashes"] == g["input_hashes"], "原版完整狀態不同")
            require((path/"run.memory").read_bytes() == (gui/"gui.memory").read_bytes() and
                    (path/"raw.wav").read_bytes() == (gui/"raw.wav").read_bytes(), "RAM或WAV不同")
            require({p.name:sha(p.read_bytes()) for p in (path/"save").glob("*.SAV")} == inputs["seed"] ==
                    {p.name:sha(p.read_bytes()) for p in (gui/"save").glob("*.SAV")}, "既有存檔不同")
        require(data["invalid"]["noto_menu"]["reason"] == "font-binding", "錯地區未記錄回退")
        captures = {e["name"]:e for e in map(json.loads,(gui/"gui.capture-attempts.jsonl").read_text().splitlines()) if e.get("aligned")}
        shots = dict(line.split() for line in (gui/"gui.shots").read_text().splitlines())
        moves = [e for e in read(gui/"gui.inputs.json")["inputs"] if e["kind"] == "move"]
        require(len(shots)==10 and set(shots)==OPEN|CLOSED, "缺正常操作")
        checkpoints = {mode:{c["label"]:c for c in j["checkpoints"]} for mode,j in data.items()}
        changes, cursor_counts = [], []
        for name,step in shots.items():
            stem = "run.cp-"+step
            require(pixels(gui/("gui."+name+".png")) == pixels(peers["locale"]/(stem+".png")), "GUI與重播像素不同")
            require(captures[name]["frame_step"] == int(step) and captures[name]["capture_rgba_sha256"] == sha(pixels(gui/("gui."+name+".png"))), "截圖未同步")
            for k in ("memory_sha256","raw_sha256","palette_sha256"):
                require(len({checkpoints[m]["cp-"+step][k] for m in MODES})==1, "取樣原版狀態不同")
            for ext in ("idx","pal"):
                require(len({(p/(stem+"."+ext)).read_bytes() for p in peers.values()})==1, "原版VGA或DAC不同")
            ims = {m:Image.open(path/(stem+".png")).convert("RGB") for m,path in peers.items()}
            diff = ImageChops.difference(ims["locale"],ims["default"])
            ls = {l["candidate_id"]:l for l in checkpoints["locale"]["cp-"+step]["lines"]}
            if name in OPEN:
                require(all(ls[key]["applied"] for key in KEYS), "主選單有欄未啟用")
                outside = diff.copy()
                for safe in SAFES:
                    require(diff.crop(safe).getbbox(), "某列未替換Noto")
                    require(ims["invalid"].crop(safe).tobytes() == ims["control"].crop(safe).tobytes(), "錯地區未整組回原文")
                    outside.paste((0,0,0),safe)
                require(not outside.getbbox(), "五列外出現變更")
                outside = ImageChops.difference(ims["invalid"],ims["default"])
                for safe in SAFES:outside.paste((0,0,0),safe)
                require(not outside.getbbox(), "回退影響其他欄位")
                fallback = {l["candidate_id"]:l for l in checkpoints["invalid"]["cp-"+step]["lines"]}
                require(all(not fallback[key]["applied"] and fallback[key]["reason"] == "noto-menu-font-binding" for key in KEYS), "回退未逐列記錄")
                changes.append({"name":name,"difference":list(diff.getbbox())})
                if name.startswith("hover-"):
                    raw = (peers["control"]/(stem+".idx")).read_bytes()
                    clean = (peers["control"]/("run.cp-"+shots["menu-cleared"]+".idx")).read_bytes()
                    points = [(i%320,i//320) for i,(a,b) in enumerate(zip(raw,clean)) if a!=b]
                    # 兩幀各有游標；差分含目前sprite及移開後sprite的兩個16×16區域。
                    current = next(e for e in reversed(moves) if e["step"] <= int(step))
                    away = next(e for e in reversed(moves) if e["step"] <= int(shots["menu-cleared"]))
                    inside = lambda x,y,e: e["x"] <= x < e["x"]+16 and e["y"] <= y < e["y"]+16
                    require(points and all(inside(x,y,current) or inside(x,y,away) for x,y in points), "游標差異超出兩個16×16位置")
                    active = [(x,y) for x,y in points if inside(x,y,current)]
                    require(active, "目前游標無可核對像素")
                    for x,y in points:
                        rect=(x*4,y*4,x*4+4,y*4+4)
                        require(ims["locale"].crop(rect).tobytes() == ims["control"].crop(rect).tobytes(), "游標像素被文字覆蓋")
                    cursor_counts.append(len(active))
            else:
                require(not diff.getbbox() and ims["invalid"].tobytes() == ims["default"].tobytes() and
                        not any(ls[key]["applied"] for key in KEYS), "離開主選單留有覆蓋")
        result[locale] = {"samples":len(shots),"source_events":source_counts,"changes":changes,
                          "cursor_native_pixels":cursor_counts,"inputs_sha256":sha((gui/"gui.inputs.json").read_bytes()),
                          "final_step":g["state"]["steps"],"final_memory_sha256":g["state"]["memory_sha256"]}
    return {"status":"PASS_SPEC055_NORMAL_GUI_AND_NATIVE_STATE","binary_sha256":inputs["binary"],
            "go_tests":len(passed),"skip":0,"reproduced_files":len(products),"locales":result,
            "script_sha256":sha(Path(__file__).read_bytes()),"bake_check_sha256":sha((atlas/"bake-check.json").read_bytes()),
            "limitations":["Only five measured main menu rows; no full language switching or HD completion.",
                            "Existing saves are compared unchanged; no save format or RNG rule change is claimed.",
                            "Japanese and Korean drafts still require native-language review."]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("reports","build","atlas","repeat","output"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    require(Path("/.dockerenv").is_file(), "請在Docker內驗證")
    result=check(a.reports,a.build,a.atlas,a.repeat)
    new_output(a.output).write_bytes(canonical(result)+b"\n")
    print(result["status"],result["go_tests"],sum(r["samples"] for r in result["locales"].values()))


if __name__ == "__main__":main()
