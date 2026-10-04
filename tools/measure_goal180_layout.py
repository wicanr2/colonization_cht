#!/usr/bin/env python3
"""Docker 內以正式排版函式量測目標180候選；不變更正式程式或原版。"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from build_help_bilingual import FIELDS, read_tsv, unescape_text


def diagnostics(path, prefix):
    return [json.loads(line[len(prefix):]) for line in path.read_text().splitlines()
            if line.startswith(prefix)]


def normalized(text):
    return re.sub(r"\s+", " ", re.sub(r"[{}^]", "", text).replace("%%", "%")).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--assembly", type=Path, required=True)
    p.add_argument("--with-building", action="store_true", help="加入已完成的建築診斷與22個先決條件欄位")
    p.add_argument("--with-coast", action="store_true", help="加入正常地形重播的海岸／河流欄位")
    p.add_argument("--with-bullet", action="store_true", help="加入三篇教育建築的DRAFT分段候選欄位")
    a = p.parse_args()
    if a.assembly.stat().st_uid != os.getuid():
        raise ValueError("量測組裝目錄擁有者不符")
    root = a.reports
    rows = read_tsv(root / "layout-prototype/pedia-bilingual.tsv", FIELDS)
    cases = []
    comparisons = {}
    categories = ("job", "father", "building-v2") if a.with_building else ("job", "father")
    for category in categories:
        control = json.loads((root / category / "replay-control.json").read_text())
        probe = json.loads((root / category / "geometry-body.json").read_text())
        original = {x["label"]: x for x in control["checkpoints"]}
        common = [x for x in probe["checkpoints"] if x["label"].startswith("cp-")]
        if not common or any(any(x[k] != original[x["label"]][k] for k in
                              ("step", "memory_sha256", "raw_sha256", "palette_sha256")) for x in common):
            raise ValueError(category + " 診斷共同取樣點原版狀態不同")
        comparisons[category] = len(common)
        misses = json.loads((root / category / "replay-zh.json").read_text())["dialog_misses"]
        geometry = {d["shown_sha256"]: d for d in diagnostics(root / category / "geometry-body.log", "PEDIA_BODY_DIAGNOSTIC ")}
        for row in rows:
            if not row["message_id"].startswith("PEDIA.TXT:@" + category.split("-")[0].upper()):
                continue
            source = normalized(unescape_text(row["source_en"]))
            found = [key.split("\t", 1)[1] for key in misses if "\t" in key and key.split("\t", 1)[1] == source]
            if not found:
                continue
            d = geometry[hashlib.sha256(found[0].encode()).hexdigest()]
            cases.append(dict(d, kind="body", key=row["message_id"],
                              zh=row["zh_hant"].replace("%%", "%").replace(r"\t", "\t")))
    if len(cases) != (12 if a.with_building else 7):
        raise ValueError("缺漏正文量測未齊")
    for d in json.loads((root / "draft-string-measurements.json").read_text()):
        cases.append(dict(d, kind="string", key=d["shown"], zh=d["candidate_zh"]))
    seen = set()
    for d in diagnostics(root / "terrain/header-geometry.log", "STRING_DIAGNOSTIC "):
        if d["shown"] in seen or d["shown"] not in ("Savannah", "(Boreal Forest: Terrain Type)"):
            continue
        seen.add(d["shown"])
        zh = "熱帶草原" if d["shown"] == "Savannah" else "（北方森林：地形類型）"
        cases.append(dict(d, kind="string", key=d["shown"], zh=zh))
    if a.with_building:
        lookup = json.loads((root / "layout-prototype/lookup-cases.txt.json").read_text())
        seen = set()
        for d in diagnostics(root / "building-v2/geometry-body.log", "STRING_DIAGNOSTIC "):
            text = d["shown"]
            if not text.startswith("Prerequisite: ") or text in seen:
                continue
            seen.add(text)
            if lookup[text]["reason"]:
                raise ValueError("先決條件查譯失敗")
            cases.append(dict(d, kind="string", key=text, zh=lookup[text]["zh"]))
        if len(seen) != 22:
            raise ValueError("22個先決條件欄位量測未齊")
    if a.with_coast:
        target = root / "terrain-fixed"
        probe = json.loads((target / "coast-geometry.json").read_text())
        control = json.loads((target / "replay-control.json").read_text())
        original = {x["label"]: x for x in control["checkpoints"]}
        common = [x for x in probe["checkpoints"] if x["label"].startswith("cp-")]
        if not common or any(any(x[k] != original[x["label"]][k] for k in
                              ("step", "memory_sha256", "raw_sha256", "palette_sha256")) for x in common):
            raise ValueError("海岸欄位診斷原版取樣點不同")
        comparisons["coast"] = len(common)
        fields = [d for d in diagnostics(target / "coast-geometry.log", "STRING_DIAGNOSTIC ")
                  if d["shown"].strip() == "Coast/River: +1"]
        if len(fields) != 2 or fields[0]["safe"] != fields[1]["safe"]:
            raise ValueError("兩次海岸欄位幾何未齊")
        cases.append(dict(fields[0], kind="string", key="Coast/River: +1", zh="海岸／河流：+1"))
    if a.with_bullet:
        target = root / "building-v2"
        probe = json.loads((target / "bullet-prototype.json").read_text())
        control = json.loads((target / "replay-control.json").read_text())
        original = {x["label"]: x for x in control["checkpoints"]}
        common = [x for x in probe["checkpoints"] if x["label"].startswith("cp-")]
        if len(common) != 81 or probe["state"] != control["state"] or any(
                any(x[k] != original[x["label"]][k] for k in
                    ("step", "memory_sha256", "raw_sha256", "palette_sha256")) for x in common):
            raise ValueError("項目符號候選原版狀態不同")
        comparisons["bullet-prototype"] = len(common)
        geometry = {d["shown_sha256"]: d for d in diagnostics(target / "bullet-prototype.log", "PEDIA_BODY_DIAGNOSTIC ")}
        for key in ("PEDIA.TXT:@BUILDING12", "PEDIA.TXT:@BUILDING13", "PEDIA.TXT:@BUILDING14"):
            entries = [e for e in probe["events"] if e.get("candidate_id") == key and e.get("stage") == "source"]
            if len(entries) != 1:
                raise ValueError("三篇條列正文事件不完整")
            e = entries[0]
            row = next(r for r in rows if r["message_id"] == key)
            if normalized(unescape_text(row["source_en"]).replace("•", "")) != e["shown"]:
                raise ValueError("條列正文未按原始來源匹配")
            d = geometry[hashlib.sha256(e["shown"].encode()).hexdigest()]
            cases.append(dict(d, kind="body", key=key, zh=row["zh_hant"]))
    label = "measurement-building" if a.with_building else "measurement"
    if a.with_coast:
        label += "-coast"
    if a.with_bullet:
        label += "-bullet"
    case_path = root / ("layout-prototype/" + label + "-cases.json")
    case_path.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n")
    helper = a.assembly / "layout_measurement_test.go"
    if helper.exists():
        raise ValueError("量測掛鉤已存在")
    helper.write_text(r'''package main
import ("testing"; "os"; "encoding/json"; "image"; "fmt")
func TestGoal180CandidateLayout(t *testing.T) {
  root := os.Getenv("GOAL180_REPORTS")
  readFonts := func(name string) map[int]*dialogFont {
    raw,e := os.ReadFile(root+"/layout-prototype/"+name+"-atlas/"+name+"-atlas.json"); if e!=nil { t.Fatal(e) }
    var h struct { Font string `json:"font_sha256"`; Bind map[string]string `json:"bindings"` }
    if e=json.Unmarshal(raw,&h);e!=nil { t.Fatal(e) }
    f,why:=loadAtlasFonts(raw,h.Font,h.Bind,30,12); if why!="" { t.Fatal(why) };return f
  }
  dlg:=&dialogCatalog{fonts:readFonts("dialog")}; str:=&stringCatalog{fonts:readFonts("string")}
  raw,e:=os.ReadFile(os.Getenv("GOAL180_CASES"));if e!=nil {t.Fatal(e)}
  var cases []map[string]json.RawMessage;if e=json.Unmarshal(raw,&cases);e!=nil {t.Fatal(e)}
  result:=[]map[string]any{}
  for _,c:=range cases {
    text:=func(k string) string {var s string;json.Unmarshal(c[k],&s);return s}
    number:=func(k string) int {var n int;json.Unmarshal(c[k],&n);return n}
    rect:=func(k string) image.Rectangle {var q [4]int;json.Unmarshal(c[k],&q);return image.Rect(q[0],q[1],q[2],q[3])}
    safe:=rect("safe"); var n *image.Alpha;size:=0
    if text("kind")=="body" {_,n,_,size=dlg.centeredMasks(text("zh"),safe.Dx()*4,safe.Dy()*4,number("pitch")*4,false)
    } else {_,n,_,size=str.stringMasks("",text("zh"),rect("ink"),safe,number("cap_height"),safe.Dx()*4,0)}
    var ink image.Rectangle
    if n!=nil {for y:=0;y<n.Rect.Dy();y++ {for x:=0;x<n.Rect.Dx();x++ {if n.AlphaAt(x,y).A!=0 {ink=ink.Union(image.Rect(x,y,x+1,y+1))}}}}
    result=append(result,map[string]any{"key":text("key"),"kind":text("kind"),"selected_px":size,"mask_ink":[4]int{ink.Min.X,ink.Min.Y,ink.Max.X,ink.Max.Y},"safe":[4]int{safe.Min.X,safe.Min.Y,safe.Max.X,safe.Max.Y},"cap_height":number("cap_height"),"pitch":number("pitch"),"fits":n!=nil && ink.In(n.Rect)})
  }
  out,_:=json.MarshalIndent(result,""," ");if e=os.WriteFile(os.Getenv("GOAL180_MEASUREMENTS"),out,0644);e!=nil {t.Fatal(e)}
  fmt.Printf("候選欄位 %d；實際函式量測完成\n",len(result))
}
''')
    env = dict(os.environ, GOAL180_REPORTS=str(root), GOAL180_CASES=str(case_path),
               GOAL180_MEASUREMENTS=str(root / ("layout-prototype/" + label + "s.json")))
    try:
        subprocess.run(["go", "test", "-run", "^TestGoal180CandidateLayout$", "-count=1", "-v", "."], cwd=a.assembly, env=env, check=True)
    finally:
        helper.unlink()
    (root / ("layout-prototype/" + label + "-state.json")).write_text(json.dumps({
        "共同原版取樣點": comparisons, "範圍": "候選排版量測；不取代正常中文GUI驗收",
        "工具_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
