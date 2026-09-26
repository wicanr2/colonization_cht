#!/usr/bin/env python3
"""規格033 動態文字資料模型的獨立參考實作：把探針記錄的原版印字事件歸類到唯一來源鍵。

不依賴 Go 前端；只讀 tools/probe_goal141_captions.go 產生的 JSON（prints 內含 Raw／Text、改色 bbox 與色號）。
輸出類別：
- glyph-run：逐字事件列（字元與 0 交錯、每字一次事件、同基址），以整列字元序列 SHA 定鍵；
  開場字幕、整頁長文（介紹頁、help）與選單列都屬此類。
- template：連續讀取的單行字串，以模板＋詞典鍵定鍵，變數原值不翻。
"""

import base64
import csv
import hashlib
import io
import re
from pathlib import Path

CAPTIONS = {  # 規格026／029：十張字幕顯示字串 SHA-256（英格蘭 Explorer 展開）
    "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6": "GAME.TXT:0x000153CC",
    "0cfc5ab07ea787de0d84826366302ef1810044e8e34094a67b557daeda9fc937": "GAME.TXT:0x0001542B",
    "bbbbdd6e1a3539314ea015d7764af6ed6451f5a4534c169bba1f882ce560d767": "GAME.TXT:0x00015482",
    "c6e372958c2d98a8b53e59d58dac57d7de1eeaab01e145b71c40b9fcf6e373d5": "GAME.TXT:0x000154CB",
    "ee8b6569c2bba4b57ce2133fd1f0ac9fe52f62db4f5621ce73fa40898f1a78d5": "GAME.TXT:0x00015522",
    "b8cb47fdb1c13aa34a0fce30e333a1232d7991ded6a9daedd8b210cf24cc27c2": "GAME.TXT:0x0001555D",
    "53f1e7991791074f9e5a1f54f9a40abc9b4b1957ff168e01d502f2f52b21eda6": "GAME.TXT:0x00015597",
    "0d3ec9226fae1b8b33356f299e2726dc109db51904c5409d1c71b7a3360abf13": "GAME.TXT:0x000155F5",
    "65e7fb3ace0f3a3b37f53d6410ee6de05bacab86a2ead7e37e81608fd4bbca5a": "GAME.TXT:0x0001563F",
    "cff475dbcfaf09ea9edf40efa8a40350da7eba8e0f0f0983175eef16e479480e": "GAME.TXT:0x00015695",
}
PAGES = {"4181fdd58a74d0031037027762468fbf8cbe28565ff097f4726a0fa73a37936b": "GAME.TXT:@TUTORIAL1"}
MENU = "GAMEVIEWORDERSREPORTSTRADECOLONIZOPEDIA"
BAR, PANEL = (0, 0, 320, 8), (240, 48, 320, 200)
TEMPLATES = [  # (模板代號, 正規式, 各群組的詞典角色；None 表示變數原值)
    ("gold", r"^(Gold:)(\d+)\$  (Tax:) (\d+)%$", ("label", None, "label", None)),
    ("locat", r"^(Locat:) \((\d+), (\d+)\)$", ("label", None, None)),
    ("moves", r"^(Moves:) (\S+)$", ("label", None)),
    ("title", r"^(\S+) (.+) (Inbound From) (.+)$", ("nation", "unit", "label", "port")),
    ("season", r"^(\S+) (\d+)$", ("season", None)),
    ("unit", r"^(\S+\.) (.+)$", ("nation_abbrev", "unit")),
    ("terrain", r"^\((.+)\)$", ("terrain",)),
    ("goods", r"^(\d+) (.+)$", (None, "goods")),
    ("order", r"^(.+)$", ("order",)),
    ("cargo", r"^(.+)$", ("cargo",)),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inside(box, rect):
    return rect[0] <= box[0] and rect[1] <= box[1] and box[2] <= rect[2] and box[3] <= rect[3]


def load_dictionary(path):
    rows = list(csv.DictReader(io.StringIO(Path(path).read_text(encoding="utf-8")), delimiter="\t"))
    return {(r["role"], r["source_text"]): r["candidate_id"] for r in rows}


def events(report):
    """把探針 prints 轉成事件：(開始步數, 基址, 原始位元組, 可見字串, 半開 bbox, 色號集合)。"""
    out = []
    for p in report["prints"]:
        if p.get("Raw"):
            raw = base64.b64decode(p["Raw"])
            interleaved = len(raw) >= 2 and all(b == 0 for b in raw[1::2])
            text = (raw[0::2] if interleaved else raw).rstrip(b"\0").decode("latin1")
        else:  # 目標143 以前的收據只記偶數位讀取；交錯讀取時即為完整字元序列。
            chars = base64.b64decode(p["Text"] or "")
            interleaved = p["Reads"] == 2 * len(chars)
            text = chars.rstrip(b"\0").decode("latin1")
        box = (p["MinX"], p["MinY"], p["MaxX"] + 1, p["MaxY"] + 1) if p["Writes"] else None
        out.append({"step": p["Start"], "base": p["Base"], "text": text, "interleaved": interleaved,
                    "box": box, "writes": p["Writes"], "colors": set(p["Colors"])})
    return out


def classify(report, dictionary):
    """回傳 (已歸類事件清單, 未知事件清單)。每筆已歸類事件只有一個鍵集合。"""
    known, unknown = [], []
    # 逐字事件的空白沒有改色，仍屬整列字串的一部分；連續字串則只看有改色者。
    evs = [e for e in events(report) if e["writes"] or e["interleaved"]]
    i = 0
    while i < len(evs):
        e = evs[i]
        # 逐字事件列：同基址、每字交錯讀取，時間相鄰者合併。
        if e["interleaved"] and len(e["text"]) == 1:
            run = [e]
            while i + len(run) < len(evs):
                n = evs[i + len(run)]
                if not (n["interleaved"] and len(n["text"]) == 1 and n["base"] == e["base"] and
                        n["step"] - run[-1]["step"] < 60000):
                    break
                run.append(n)
            text = "".join(r["text"] for r in run)
            key = CAPTIONS.get(sha(text.encode("latin1"))) or PAGES.get(sha(text.encode("latin1")))
            if key is None and text == MENU and all(r["box"] is None or inside(r["box"], BAR) for r in run):
                key = "MENU.TXT:~GAME..~COLONIZOPEDIA"
            box = next((r["box"] for r in run if r["box"]), None)
            if box is not None:  # 全為空白的逐字事件不計
                (known if key else unknown).append({"class": "glyph-run", "step": e["step"], "text": text,
                                                    "keys": [key] if key else [], "box": box})
            i += len(run)
            continue
        i += 1
        if e["interleaved"]:
            unknown.append({"class": "unclassified", "step": e["step"], "text": e["text"][:40], "keys": [], "box": e["box"]})
            continue
        t = e["text"].rstrip(" ")
        region = "bar" if inside(e["box"], BAR) else "panel" if inside(e["box"], PANEL) else None
        hit = None
        if region:
            for name, pattern, roles in TEMPLATES:
                m = re.match(pattern, t)
                if not m:
                    continue
                keys = [dictionary.get((role, g)) for role, g in zip(roles, m.groups()) if role]
                if all(keys):
                    hit = {"class": "template", "template": name, "step": e["step"], "text": t,
                           "keys": keys, "box": e["box"], "region": region}
                    break
        if hit:
            known.append(hit)
        else:
            unknown.append({"class": "template" if region else "unclassified", "step": e["step"], "text": t,
                            "keys": [], "box": e["box"]})
    return known, unknown
