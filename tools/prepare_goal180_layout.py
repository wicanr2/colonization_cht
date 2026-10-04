#!/usr/bin/env python3
"""在 Docker 內建立可丟棄字級量測輸入；不是正式譯稿或 READY 授權。"""
import argparse
import csv
import io
import os
from pathlib import Path
import build_pedia_bilingual as pedia
from build_help_bilingual import read_tsv, render, FIELDS

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--game", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
if a.output.exists() or a.output.parent.stat().st_uid != os.getuid():
    raise ValueError("輸出已存在或父目錄擁有者不符")
existing = read_tsv(Path("/repo/text/pedia-bilingual.tsv"), FIELDS)
values = {r["message_id"]: r["zh_hant"] for r in existing}
pedia.KEYS = pedia.FATHER_KEYS + pedia.CARGO_KEYS + pedia.UNIT_KEYS + pedia.TERRAIN_KEYS + [f"JOB{i}" for i in range(28)] + pedia.BUILDING_KEYS
rows = pedia.source_rows(a.game)
if rows is None:
    raise SystemExit(77)
values["PEDIA.TXT:@JOB27"] = "^{印地安歸順者}\\n在原住民中傳教的傳教士，能說服部分印地安人相信基督教。這些歸順者擅長戶外活動與各種戶外職業；不過，他們不適合製造或加工工作。"
for r in rows:
    r["zh_hant"] = values[r["message_id"]]
    r["notes"] += "；目標180可丟棄版面量測，未進正式路徑"
templates = [
    ("pedia-unit-cargo", "Combat: {n1}   Moves: {n2}   (Cargo Holds: {n3})", "戰鬥：{n1}　行動：{n2}　（貨艙：{n3}）"),
    ("pedia-unit-veteran", "Combat: {n1}   (Veteran: {n2})   Moves: {n3}", "戰鬥：{n1}（老手：{n2}）　行動：{n3}"),
    ("pedia-unit-artillery", "Combat: {n1}   (Attack: +{n2} Damaged: -{n3})   Moves: {n4}", "戰鬥：{n1}（進攻：+{n2}，受損：-{n3}）　行動：{n4}"),
    ("pedia-unit-pair", "{w1} (and {w2})", "{w1}（含{w2}）"),
    ("pedia-artillery-pair", "Artillery (and {w1}", "砲台（含{w1}）"),
    ("pedia-boreal-subtitle", "(Boreal Forest: {w1})", "（北方森林：{w1}）"),
    ("pedia-coast-river", "Coast/River: +{n1}", "海岸／河流：+{n1}"),
    ("pedia-prerequisite", "Prerequisite: {w1}", "先決條件：{w1}"),
]
a.output.mkdir()
(a.output / "dialog-atlas").mkdir()
(a.output / "string-atlas").mkdir()
(a.output / "pedia-bilingual.tsv").write_text(render(rows))
source = Path("/repo/text/string-templates.zh-Hant.tsv").read_text()
out = io.StringIO()
w = csv.writer(out, delimiter="\t", lineterminator="\n")
for key, pattern, zh in templates:
    w.writerow([key, pattern, zh, "目標180正常GUI與原版欄位觀測；只供量測", "draft", "原版數值不變；未授權正式路徑"])
(a.output / "string-templates.zh-Hant.tsv").write_text(source + out.getvalue())
print("可丟棄輸入：164篇來源與8個候選字串模板；未修改正式譯稿")
