#!/usr/bin/env python3
"""目標173（Issue #45）：全可達文字普查；原版缺失回 SKIP 77。

分母
- TXT：訊息型檔案一個段落一列，清單型檔案（NAMES、LABELS、MENU、COLONY、MAPMENU、TRIBE）一行一列。
  段落鍵是行首第一個詞為 `@鍵` 或 `@@鍵`（鍵為大寫英數與底線；`@@VICEROY` 的鍵記為 `@VICEROY`，與 `@VICEROY` 不同）；
  `@width=`、`@x=`、`@y=`、`@default=`、`@smallfont`、`@options`、`@checkbox`（含 `@@` 形式）是版面指令，
  `@;` 是註解；其餘 `@` 開頭而含英文字母的行（國王接見的 `@^`、`@"`）是內容。
  每個段落以 `text/census-map.tsv` 恰好一條樣式分類（畫面、機制、可達性、理由）。機制 none 的段落不計入分母。
- 靜態文字圖像：`text/static-overlay.zh-Hant.tsv` 各列。
- 執行期字串：收據裡印出、但歸屬不到任何 TXT 行的字串，以文字 SHA-256 前 12 碼為鍵；字串層已套用者自動列入，
  其餘由對照表 `file=EXE` 的列（pattern 比對雜湊）人工分類，未分類者列為待歸類，不計入分母。
  人工分類的理由以「已顯示」開頭者（例如由另一層繪製）記為已顯示，證據等級「人工歸類」。

證據（只取收據自己記錄的，不做事後配對）
- 以鍵套用：`frames[].lines[]` 的 applied 列、`events` 的 active 事件，鍵為 `檔案:@段落`、`檔案:0x位移` 或靜態圖 id。
- 以文字套用：字串層 active 事件的 `shown`；對話框引擎經字串層翻譯的逐行清單（`STRING:line`）active 不帶文字，
  引擎一次只處理一段，取同鍵最近一次 source 事件的 `shown`。
- 海上狀態欄只記整層套用：以其詞典 `sea-status.zh-Hant.tsv` 的來源位移推定（強推論）。
- 未套用：對話框層 fallback 事件的 `shown`，以及 `string_misses`、`sea_misses`、`dialog_misses`。
  某一層未套用不等於畫面上是英文：同一份收據中若有以文字套用的字串包含它，視為已由其他層顯示。

歸屬（顯示文字 → TXT 列）只用兩種精確方法：
1. 正規化空白後與某一行完全相同（容許結尾冒號差異），或與某段落各行以空白相接的全文相同。
2. 含 `%變數` 的行或段落全文把變數換成萬用後整句相符；字面英文字母至少 6 個。

狀態：shown（已顯示中文）、pending（機制已有待接；reach 另分 normal／conditional）、
new-mechanism（機制為 input，或執行期字串的分類理由以「需新機制」開頭）、unreachable（附理由）。
可提交輸出只含鍵、雜湊與數量；含英文原文的明細只寫到 workplace。
"""

import argparse
import csv
import glob
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


FILES = ["GAME.TXT", "PEDIA.TXT", "NAMES.TXT", "LABELS.TXT", "MENU.TXT", "COLONY.TXT", "MAPEDIT.TXT", "MAPMENU.TXT",
         "WOODCUT.TXT", "OPENING.TXT", "CLOSING.TXT", "TRIBE.TXT", "DEBUG.TXT"]
LIST_FILES = {"NAMES.TXT", "LABELS.TXT", "MENU.TXT", "COLONY.TXT", "MAPMENU.TXT", "TRIBE.TXT"}
DIRECTIVE = re.compile(r"@@?(width|x|y|default)=|@@?(smallfont|options|checkbox)\b|@;")
KEY = re.compile(r"@(@?[A-Z0-9_]+)$")
MECHANISMS = {"dialog", "pedia", "tutorial", "menu", "string", "caption", "input", "nation", "none"}
REACH = {"normal", "conditional", "unreachable"}
STATUSES = ("shown", "pending", "new-mechanism", "unreachable")
LABELS = {"shown": "已顯示中文", "pending": "機制已有待接", "new-mechanism": "需新機制", "unreachable": "無法正常觸發"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tsv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def display(s):
    """TXT 原文 → 畫面文字：去掉強調 {} 與熱鍵 ~ 標記。"""
    return norm(s.replace("{", "").replace("}", "").replace("~", ""))


def loose_end(s):
    return s.rstrip(" ,.:;")


def text_hash(text):
    return sha(norm(text).encode("utf-8"))[:12]


DATA_TAIL = re.compile(r",[\s\d,.\-+]*$")


def units(data):
    """顯示行：(位移, 長度, 文字)。排除空行、`;` 註解與 `@` 行；「名稱,數值…」資料行只取名稱。

    與 text_inventory.units 的差別：資料尾巴必須含數字，否則以逗號結尾的一般句子會被截斷。
    """
    out, pos = [], 0
    for raw in data.split(b"\n"):
        start, line = pos, raw.rstrip(b"\r")
        pos += len(raw) + 1
        s = line.decode("cp437").strip()
        if not s or s.startswith((";", "@")):
            continue
        if ";" in s and not re.search(r"[A-Za-z]", s[:s.index(";")]):
            continue
        tail = DATA_TAIL.search(s)
        if "," in s and tail and re.search(r"\d", tail.group(0)):
            s = s[:s.index(",")].strip()
        if re.search(r"[A-Za-z]", s):
            out.append((start, len(line), s))
    return out


def parse(name, data):
    """回傳 (段落 [(鍵, 起點, 終點)], 顯示行 [(位移, 長度, 文字)])。第一個段落鍵之前的內容歸入鍵 ''。"""
    secs, key, start, pos, extra = [], "", 0, 0, []
    for raw in data.split(b"\n"):
        line = raw.rstrip(b"\r").decode("cp437")
        if line.startswith("@"):
            tok = line.split()[0] if line.split() else line
            m = KEY.match(tok)
            if not DIRECTIVE.match(tok) and m:
                secs.append((key, start, pos))
                key, start = m.group(1), pos
            elif not DIRECTIVE.match(tok) and re.search(r"[A-Za-z]", line):
                extra.append((pos, len(line), line[1:]))
        pos += len(raw) + 1
    secs.append((key, start, len(data)))
    lines = sorted(units(data) + extra)
    return [s for s in secs if s[1] < s[2]], [(o, n, display(t.lstrip("^_"))) for o, n, t in lines]


def pattern_of(text):
    """含 %變數 且字面字母至少 6 個時回傳整句正規式，否則 None。"""
    parts = re.split(r"%[A-Z0-9]+", text)
    if len(parts) < 2 or len(re.findall(r"[A-Za-z]", "".join(parts))) < 6:
        return None
    return re.compile(".+?".join(re.escape(p) for p in parts))


def new_row(rid, kind, m, start, end, lines, text):
    return {"id": rid, "kind": kind, "screen": m["screen"], "mechanism": m["mechanism"], "reach": m["reach"],
            "reason": m["reason"], "start": start, "end": end, "lines": lines, "text": text,
            "shown": set(), "evidence": "", "reached": set()}


class Census:
    def __init__(self, game, map_rows):
        self.rows, self.hashes, self.exact, self.patterns, self.by_id = [], {}, defaultdict(set), [], {}
        used = Counter()
        for name in FILES:
            data = (game / name).read_bytes()
            self.hashes[name] = sha(data)
            secs, us = parse(name, data)
            for key, s0, s1 in secs:
                inside = [u for u in us if s0 <= u[0] < s1]
                if key == "" and not inside:  # 檔頭註解
                    continue
                hits = [m for m in map_rows if m["file"] == name and re.fullmatch(m["pattern"], key)]
                if len(hits) != 1:
                    raise ValueError(f"{name}:@{key} 被 {len(hits)} 條對照樣式命中（必須恰好 1 條）")
                used[(name, hits[0]["pattern"])] += 1
                if not inside:  # 沒有顯示行（結束標記、純數字資料）
                    continue
                for g in ([[u] for u in inside] if name in LIST_FILES else [inside]):
                    rid = f"{name}:@{key}" + (f":0x{g[0][0]:08X}" if name in LIST_FILES else "")
                    row = new_row(rid, "txt", hits[0], g[0][0], g[-1][0] + g[-1][1], len(g), " / ".join(u[2] for u in g))
                    row.update(file=name, section=key, sec=(s0, s1))
                    self.rows.append(row)
                    # 段落內任意連續幾行以空白相接（含單行與全文）
                    for i in range(len(g)):
                        for j in range(i + 1, len(g) + 1):
                            t = " ".join(u[2] for u in g[i:j])
                            self.exact[loose_end(t)].add(id(row))
                            rx = pattern_of(loose_end(t))
                            if rx:
                                self.patterns.append((rx, row))
                    self.by_id[id(row)] = row
        self.unused = [(m["file"], m["pattern"]) for m in map_rows
                       if m["file"] != "EXE" and (m["file"], m["pattern"]) not in used]

    def at(self, name, off):
        """涵蓋位移的行；位移落在段落鍵或段落內空白處時取該段落第一列。"""
        cand = [r for r in self.rows if r["file"] == name and r["start"] <= off < r["end"]]
        cand = cand or [r for r in self.rows if r["file"] == name and r["sec"][0] <= off < r["sec"][1]]
        return min(cand, key=lambda r: r["start"]) if cand else None

    def by_key(self, cid):
        m = re.match(r"([A-Z0-9]+\.TXT):(.*)", cid)
        if not m:
            return []
        name, rest = m.groups()
        k, o = re.match(r"@(@?[A-Z0-9_]+)", rest), re.search(r"0x([0-9A-Fa-f]+)", rest)
        if o and (name in LIST_FILES or not k):
            r = self.at(name, int(o.group(1), 16))
            return [r] if r else []
        return [r for r in self.rows if r["file"] == name and r["section"] == k.group(1)] if k else []

    def by_text(self, text):
        """精確歸屬：唯一一列時回傳該列；對到多列（通用片段）或對不到回空，另回傳是否不明確。"""
        t = loose_end(norm(text))
        ids = self.exact.get(t) or {id(r) for rx, r in self.patterns if rx.fullmatch(t)}
        if len(ids) == 1:
            return [self.by_id[next(iter(ids))]], False
        return [], len(ids) > 1


def observations(path):
    """一份收據 → (以鍵套用, 以文字套用, 未套用文字, 海上層是否套用)。"""
    d = json.loads(path.read_text())
    keys, applied, missed, sea = set(), set(), Counter(), False
    for fr in d.get("frames", []):
        for line in fr.get("lines", []):
            if str(line.get("applied")) == "True":
                keys.add(line["candidate_id"])
    last_source = {}
    for e in d.get("events", []):
        cid = e.get("candidate_id", "")
        if e.get("stage") == "source" and e.get("shown"):
            last_source[cid] = e["shown"]
        if e.get("stage") == "active":
            if cid.startswith("STRING"):
                # 字串層的 active 自帶 shown；對話框引擎經字串層翻譯的逐行清單（STRING:line）不帶，
                # 引擎一次只處理一段，取同鍵最近一次 source 的文字。
                text = e.get("shown") or last_source.get(cid)
                if text:
                    applied.add(norm(text))
            else:
                keys.add(cid)
        elif e.get("stage") == "fallback" and e.get("shown"):
            missed[norm(e["shown"])] += 1
    sea = any(k.startswith("sea:") for k in keys)
    for field in ("string_misses", "sea_misses", "dialog_misses"):
        for k, n in (d.get(field) or {}).items():
            if k.startswith("owned-by-field\t"):  # 該欄位由另一層（旗卡、選項）負責
                continue
            missed[norm(k.split("\t", 1)[-1])] += n
    missed = Counter({t: n for t, n in missed.items() if len(re.findall(r"[A-Za-z]", t)) >= 2})
    return keys, applied, missed, sea


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--text", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--matrix", type=Path, required=True)
    p.add_argument("--extra", nargs="*", default=[], help="驗證矩陣以外的新前端重播收據（相對 --reports 的樣式）")
    p.add_argument("--map", type=Path, required=True)
    p.add_argument("--census", type=Path, required=True, help="可提交的清冊 TSV（只含鍵）")
    p.add_argument("--report", type=Path, required=True, help="可提交的報表 Markdown")
    p.add_argument("--detail", type=Path, required=True, help="含原文的明細 JSON（workplace）")
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未產生普查")
        return 77
    map_rows = tsv(a.map)
    for m in map_rows:
        if m["mechanism"] not in MECHANISMS or m["reach"] not in REACH:
            raise ValueError(f"對照列不合法：{m}")
        if m["reach"] == "unreachable" and not m["reason"].strip():
            raise ValueError(f"unreachable 必須附理由：{m['file']} {m['pattern']}")
    c = Census(a.game, map_rows)
    exe_map = [m for m in map_rows if m["file"] == "EXE"]
    static_map = {"screen": "開場字幕", "mechanism": "static", "reach": "normal", "reason": "規格034 靜態覆蓋"}
    statics = {s["candidate_id"]: new_row(s["candidate_id"], "static", static_map, 0, 0, 1, s["source_text"])
               for s in tsv(a.text / "static-overlay.zh-Hant.tsv")}

    matrix = json.loads(a.matrix.read_text(encoding="utf-8"))
    recs = [(row["id"], Path(q)) for row in matrix["rows"] for z in row["zh"]
            for q in sorted(glob.glob(str(a.reports / row["dir"] / (z + ".json"))))]
    recs += [(Path(q).parent.name, Path(q)) for pat in a.extra for q in sorted(glob.glob(str(a.reports / pat)))]

    runtime = defaultdict(lambda: {"shown": set(), "reached": set(), "missed": 0})
    sea_rids, ambiguous = set(), Counter()
    for rid, path in recs:
        keys, applied, missed, sea = observations(path)
        if sea:
            sea_rids.add(rid)
        for cid in keys:
            if cid in statics:
                statics[cid]["shown"].add(rid)
                statics[cid]["evidence"] = "confirmed"
            for r in c.by_key(cid):
                r["shown"].add(rid)
                r["evidence"] = "confirmed"
        for t in applied:
            hit, amb = c.by_text(t)
            for r in hit:
                r["shown"].add(rid)
                r["evidence"] = "confirmed"
            if not hit and not amb:
                runtime[t]["shown"].add(rid)
        for t, n in missed.items():
            if any(t in s for s in applied):  # 同一收據已由其他層以文字顯示
                continue
            hit, amb = c.by_text(t)
            for r in hit:
                r["reached"].add(rid)
            if amb:
                ambiguous[t] += n
            elif not hit:
                runtime[t]["reached"].add(rid)
                runtime[t]["missed"] += n
    if sea_rids:
        for s in tsv(a.text / "sea-status.zh-Hant.tsv"):
            r = c.at(s["source_file"], int(s["byte_offset"], 16))
            if r is not None and not r["shown"]:
                r["shown"] |= sea_rids
                r["evidence"] = "強推論"

    exe_rows, unclassified = [], []
    for t, v in sorted(runtime.items()):
        h = text_hash(t)
        hits = [m for m in exe_map if re.fullmatch(m["pattern"], h)]
        if v["shown"] and not hits:
            hits = [{"screen": "（執行期字串）", "mechanism": "string", "reach": "normal", "reason": "字串層已套用"}]
        if len(hits) != 1:
            unclassified.append({"hash": h, "text": t, **{k: sorted(x) if isinstance(x, set) else x for k, x in v.items()}})
            continue
        r = new_row("EXE:" + h, "exe", hits[0], 0, 0, 1, t)
        r["shown"], r["reached"] = v["shown"], v["reached"]
        r["evidence"] = "confirmed" if v["shown"] else ""
        exe_rows.append(r)

    for r in exe_rows:  # 人工歸類為已由其他層顯示者（理由須寫明是哪一層）
        if not r["shown"] and r["reason"].startswith("已顯示"):
            r["shown"], r["evidence"] = {"人工歸類"}, "人工歸類"

    def status(r):
        if r["shown"]:
            return "shown"
        if r["reach"] == "unreachable":
            return "unreachable"
        if r["mechanism"] == "input" or (r["kind"] == "exe" and r["reason"].startswith("需新機制")):
            return "new-mechanism"
        return "pending"

    rows = [r for r in c.rows if r["mechanism"] != "none"] + list(statics.values()) + exe_rows
    hidden = [r for r in c.rows if r["mechanism"] == "none"]
    for r in rows:
        r["status"] = status(r)

    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(["id", "kind", "screen", "mechanism", "reach", "status", "evidence", "lines", "receipts", "reached_unapplied"])
    for r in sorted(rows, key=lambda r: r["id"]):
        w.writerow([r["id"], r["kind"], r["screen"], r["mechanism"], r["reach"], r["status"], r["evidence"], r["lines"],
                    ",".join(sorted(r["shown"])), ",".join(sorted(r["reached"] - r["shown"]))])
    a.census.write_text(buf.getvalue(), encoding="utf-8")

    total = Counter(r["status"] for r in rows)
    pend = Counter(r["reach"] for r in rows if r["status"] == "pending")
    gap = [r for r in rows if r["status"] != "shown" and r["reached"]]
    by = defaultdict(Counter)
    for r in rows:
        by[r["screen"]][r["status"]] += 1
    md = ["# 全可達文字普查", "",
          "由 `tools/text_census.py` 依 `text/census-map.tsv` 與重播收據產生；不要手改。逐列清冊在 `docs/text-census.tsv`（只含鍵）。", "",
          "- 原版輸入：" + "、".join(f"`{n}` `{c.hashes[n][:12]}…`" for n in FILES),
          f"- 收據：驗證矩陣 {len(matrix['rows'])} 列的中文重播與新前端重播，共 {len(recs)} 份",
          f"- 分母 {len(rows)} 列：TXT {sum(r['kind'] == 'txt' for r in rows)}、靜態圖 {len(statics)}、執行期字串 {len(exe_rows)}；"
          f"不顯示在遊戲畫面的段落 {len(hidden)} 列不計入",
          f"- {LABELS['shown']} {total['shown']}（其中海上層強推論 {sum(r['evidence'] == '強推論' for r in rows)}）、"
          f"{LABELS['pending']} {total['pending']}（正常路徑 {pend['normal']}、特定局勢 {pend['conditional']}）、"
          f"{LABELS['new-mechanism']} {total['new-mechanism']}、{LABELS['unreachable']} {total['unreachable']}",
          f"- 收據中已到達但仍是英文：{len(gap)} 列；歸屬不到 TXT、尚未分類的執行期字串：{len(unclassified)} 種；"
          f"對到多列而不歸屬的通用片段：{len(ambiguous)} 種", "",
          "| 畫面 | " + " | ".join(LABELS[s] for s in STATUSES) + " |", "|---|" + "---:|" * len(STATUSES)]
    md += [f"| {s} | " + " | ".join(str(by[s][x]) for x in STATUSES) + " |" for s in sorted(by)]
    md += ["", "## 已到達但仍是英文", ""]
    md += [f"- `{r['id']}`（{r['screen']}，{r['mechanism']}）" for r in sorted(gap, key=lambda r: r["id"])] or ["- 無"]
    md += ["", "## 無法正常觸發的理由", ""]
    reasons = Counter((r["id"].split(":")[0], r["reason"]) for r in rows if r["status"] == "unreachable")
    md += [f"- {f}：{why}（{n} 列）" for (f, why), n in sorted(reasons.items())] or ["- 無"]
    if unclassified:
        md += ["", "## 待歸類的執行期字串（雜湊）", ""] + [f"- `{u['hash']}`" for u in unclassified]
    if c.unused:
        md += ["", "## 未使用的對照樣式", ""] + [f"- {f} `{pt}`" for f, pt in c.unused]
    a.report.write_text("\n".join(md) + "\n", encoding="utf-8")

    def clean(r):
        return {k: (sorted(v) if isinstance(v, set) else v) for k, v in r.items() if k != "sec"}
    a.detail.write_text(json.dumps({"rows": [clean(r) for r in rows], "hidden": [clean(r) for r in hidden],
                                    "unclassified": unclassified, "ambiguous": dict(ambiguous)}, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"rows": len(rows), "status": dict(total), "pending_reach": dict(pend), "hidden": len(hidden),
                      "reached_gap": len(gap), "exe": len(exe_rows), "unclassified": len(unclassified),
                      "unused_patterns": len(c.unused), "census_sha256": sha(a.census.read_bytes()),
                      "report_sha256": sha(a.report.read_bytes())}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
