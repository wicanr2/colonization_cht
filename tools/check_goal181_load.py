#!/usr/bin/env python3
"""容器內驗證正常讀檔成功欄位：來源、中文安全區、三側狀態及原檔保留。"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops
from check_goal134_window import load, same_state
from check_goal172_window import cp


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--lookup-reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，不宣稱讀檔欄位通過")
        return 77
    b = a.reports
    gui, zh, ctl, neg = [load(b / n) for n in
                         ("gui-colony", "replay-zh", "replay-control", "neg-noatlas")]
    same_state(zh, ctl, "讀檔中文與原文完整狀態不同")
    for obs, name in ((gui, "正常GUI"), (neg, "缺圖集")):
        need(obs[0]["state"] == ctl[0]["state"] and obs[1] == ctl[1] and
             obs[0]["input_hashes"] == ctl[0]["input_hashes"] and
             obs[0]["opened"] == ctl[0]["opened"], name + "完整原版狀態不同")
    for name, expected in gui[0]["input_hashes"].items():
        need(digest(a.game / name) == expected, "原版指紋不同：" + name)
    raw_inputs = (b / "gui-colony.inputs.json").read_bytes()
    inputs = json.loads(raw_inputs)
    need(not inputs.get("rejected") and inputs["end"] == gui[0]["state"]["steps"], "輸入未綁定終點")
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (b / "gui-colony.shots").read_text().splitlines()))
    need({"load-slots", "loaded-notice", "loaded-world"} <= shots.keys(), "正常讀檔路徑不完整")
    for step in shots.values():
        expected = cp(ctl[0], step)
        for obs in (zh, neg):
            now = cp(obs[0], step)
            need(all(now[k] == expected[k] for k in
                     ("step", "memory_sha256", "raw_sha256", "palette_sha256")), "原版取樣點不同")
    key = "GAME.TXT:0x00000854"
    sources = [e for e in zh[0]["events"] if e.get("candidate_id") == key and e.get("stage") == "source"]
    need(len(sources) == 1, "讀檔正文來源不唯一")
    e = sources[0]
    need(e.get("safe") == [66, 94, 237, 106] and e.get("font_px") == 30 and
         e.get("entry_ip") == "0D21:00C6" and e.get("source_linear") == 174216,
         "讀檔欄位與READY量測不同")
    notice = shots["loaded-notice"]
    for obs, wanted in ((zh, True), (neg, False)):
        lines = cp(obs[0], notice)["lines"]
        applied = any(x.get("candidate_id") == key and x.get("applied") for x in lines)
        need(applied == wanted, "讀檔欄位未啟用或缺圖集未回退")
    need(not any(x.get("candidate_id") == key and x.get("applied") for x in
                 cp(zh[0], shots["loaded-world"])["lines"]), "關閉提示後仍有讀檔覆蓋")
    rect = (264, 376, 948, 424)
    def frame(obs):
        return Image.open(cp(obs[0], notice)["png"]).convert("RGB")
    zi, ci, ni = frame(zh), frame(ctl), frame(neg)
    diff = ImageChops.difference(zi, ci)
    box = diff.getbbox()
    need(box is not None and box[0] >= rect[0] and box[1] >= rect[1] and
         box[2] <= rect[2] and box[3] <= rect[3], "中文差異超出安全區或沒有中文")
    need(ImageChops.difference(ni, ci).getbbox() is None, "缺圖集未完整回原文")
    gi = Image.open(b / "gui-colony.loaded-notice.png").convert("RGB")
    need(ImageChops.difference(gi.crop(rect), zi.crop(rect)).getbbox() is None, "正常GUI與中文重播不同")
    seed = "f683eb9132406e1dc7de5c90372f933b724b71b78a327551a305ba19d9a7d991"
    for folder in ("scratch", "replay-zh-save", "replay-control-save", "neg-noatlas-save"):
        need(digest(b / folder / "COLONY02.SAV") == seed, "讀檔改寫了初始存檔")
        need(len(list((b / folder).glob("COLONY*.SAV"))) == 1, "讀檔產生未預期存檔")
    lookup = json.loads((a.lookup_reports / "trace.json.matches.json").read_text())
    need(lookup["inputs_sha256"] == hashlib.sha256(raw_inputs).hexdigest() and
         lookup["final_step"] == inputs["end"] and
         lookup["memory_sha256"] == gui[0]["state"]["memory_sha256"], "來源觀測器未綁定同輸入／完整終點")
    matches = lookup["matches"]
    need(len(matches) == 1, "LOADGOOD查詢來源不唯一")
    m = matches[0]
    need(m["key"] == m["header"] == "@LOADGOOD" and
         m["original_cs_ip"] == "0E2D:0832" and m["code_bytes"] == "f3a6" and m["cx"] == 1 and
         m["return_cs"] == 0x9320 and m["return_ip"] == 0xD7 and
         m["read_op"]["Name"] == "GAME.TXT" and
         m["read_op"]["Seg"] == 0x1C6A and m["read_op"]["Off"] == 0xE962 and
         m["file_op"]["Pos"] == 2048 and m["file_op"]["Len"] == 512,
         "LOADGOOD原始查詢／檔案位移不同")
    original = (a.game / "GAME.TXT").read_bytes()
    marker = b"@LOADGOOD\r\n"
    need(original.count(marker) == 1 and
         digest(a.game / "GAME.TXT") == "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a" and
         hashlib.sha256(original[0x854:0x854 + 29]).hexdigest() ==
         "9c7e7034756620ffc8d6b3a3e7675e61cf78e4d5a3062341857986af099ec14c",
         "LOADGOOD原始段落或正文片段不同")
    need(m["header_ram"] == 149980 and m["key_ram"] == 174438 and
         m["step"] < e["step"] < notice and
         m["file_op"]["Op"] == "read" and not m["file_op"]["Failed"] and
         m["file_op"]["Step"] == m["read_op"]["Step"] < m["step"] and
         m["file_op"]["Pos"] <= original.index(marker) < m["file_op"]["Pos"] + m["file_op"]["Len"] and
         m["read_op"]["Got"] == 512,
         "LOADGOOD查詢未與原始DOS讀取及GUI印字時序綁定")
    print(json.dumps({"result": "PASS", "scope": "正常第三欄讀檔成功提示及關閉；其他訊息未驗",
                      "candidate_id": key, "safe": list(rect), "font_px": 30,
                      "original_checkpoints": len(set(shots.values())),
                      "inputs_sha256": hashlib.sha256(raw_inputs).hexdigest(),
                      "final_step": inputs["end"],
                      "final_memory_sha256": gui[0]["state"]["memory_sha256"],
                      "verified_fields": [{"candidate_id": key, "shown": e["shown"], "safe": e["safe"]}],
                      "grade": "confirmed",
                      "observed_template_source_aliases": {key: "GAME.TXT:@LOADGOOD"},
                      "lookup_gui_inputs_sha256": lookup["inputs_sha256"],
                      "lookup_original_step": lookup["final_step"],
                      "lookup_original_memory_sha256": lookup["memory_sha256"],
                      "evidence_sha256": digest(a.lookup_reports / "trace.json.matches.json"),
                      "limit": "只驗正常第三欄讀檔成功與提示關閉，不外推其他檔名格式或存讀檔訊息"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
