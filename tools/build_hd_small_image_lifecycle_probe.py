"""目標186 R49 DRAFT：已命中小圖像的唯讀逐寫探針；不安裝HD。"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
for name in ["catalog", "entry-report", "reference", "output"]:
    parser.add_argument("--" + name, type=Path, required=True)
a = parser.parse_args()
out = a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert out.is_relative_to("/out") and out.parent.stat().st_uid == os.getuid() and not out.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
repo = Path(__file__).resolve().parents[1]
base = repo / "tools/probe_hd_building_batch.go"
assert sha(base) == "5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6"
d = json.loads(a.catalog.read_bytes())
entry = json.loads(a.entry_report.read_bytes())
assert entry["result"] == "PASS_READONLY_FULL_SS_ENTRY_CATALOG" and entry["original_state_and_saves_equal"]
assert entry["calls"] == 2005 and entry["checkpoints"] == 49 and entry["dos_inputs"] == 53
ids = {g["candidate_research_ids"][0] for g in entry["groups"].values()
       if len(g["candidate_research_ids"]) == 1 and g["sources"][0]["file"] == "ICONS.SS"}
sources = [f for f in d["frames"] if f["research_id"] in ids]
assert len(sources) == len(ids) == 31
original = next(f for f in d["files"] if f["file"] == "ICONS.SS")
assert entry["input_hashes"]["ICONS.SS"] == original["sha256"]
for f in sources:
    assert f["file"] == "ICONS.SS" and f["file_sha256"] == original["sha256"]
    assert sha(a.catalog.parent / "pixels" / f'{f["research_id"]:04d}.idx') == f["indexed_sha256"]
s = base.read_text()
start = s.index("var buildingSources = []buildingSource{")
end = s.index("\n}\n", start) + 2
rows = ["var buildingSources = []buildingSource{"]
for f in sources:
    rows.append("\t{%d,%d,%d,%d,%d,%s,%s,nil}," % (
        f["research_id"], *f["size"], f["opaque_pixels"], f["encoded_length"],
        json.dumps(f["encoded_sha256"]), json.dumps(f["indexed_sha256"])))
rows.append("}")
s = s[:start] + "\n".join(rows) + s[end:]


def one(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new, 1)


one('"BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",',
    '"ICONS.SS": ' + json.dumps(original["sha256"]) + ',')
one('candidate := &buildingSources[i]', 'candidate := &buildingSources[i]\n' +
    ' if int(record[4])!=candidate.Width || int(record[5])!=candidate.Height {continue}')
one('"building-%03d.pixels"', '"%04d.idx"')
one('`json:"ordinal"`', '`json:"research_id"`')
one('import (', 'import (\n "bufio"')
s, count = re.subn(r'events\s+\[\]map\[string\]any',
                  'eventCount int\n eventLog *bufio.Writer\n eventFile *os.File', s)
assert count == 1
s, count = re.subn(r'b\.events\s*=\s*append\(b\.events,\s*(map\[string\]any\{[^\n]+\})\)', r'b.event(\1)', s)
assert count == 2
s = s.replace('len(b.events)', 'b.eventCount').replace('len(observer.events)', 'observer.eventCount')
one('>= 1000000', '>= 8000000')
s, count = re.subn(r'(observer = &buildingObserver\{[^\n]+\})',
                  r'\1\n observer.openEvents(filepath.Join(*out,"writes.json"))\n defer observer.closeEvents()', s)
assert count == 1
one('buildingJSON(filepath.Join(*out, "writes.json"), observer.events)',
    'observer.closeEvents()\n result["raw_event_count"]=observer.eventCount')
s += '''
func (b *buildingObserver) openEvents(path string) {
 var err error;b.eventFile,err=os.Create(path);buildingNeed(err)
 b.eventLog=bufio.NewWriterSize(b.eventFile,65536);_,err=b.eventLog.WriteString("[\\n");buildingNeed(err)
}
func (b *buildingObserver) event(value map[string]any) {
 if b.eventCount>=8000000 {panic("小圖像原始事件超過8M有界上限")}
 if b.eventCount>0 {_,err:=b.eventLog.WriteString(",\\n");buildingNeed(err)}
 raw,err:=json.Marshal(value);buildingNeed(err);_,err=b.eventLog.Write(raw);buildingNeed(err);b.eventCount++
}
func (b *buildingObserver) closeEvents() {
 if b.eventLog==nil{return};_,err:=b.eventLog.WriteString("\\n]\\n");buildingNeed(err)
 buildingNeed(b.eventLog.Flush());buildingNeed(b.eventFile.Close());b.eventLog=nil
}
'''
s = s.replace("// 規格064 DRAFT：十種城內建築的唯讀正常路徑探針。",
              "// 目標186 R49 DRAFT：31種已命中小圖像的唯讀逐寫探針。")
s = s.replace("readonly-colony-building-batch-normal-input-research", "readonly-small-images-normal-input-write-research")
s = s.replace("Ten exact decoded sources; no production HD, animation, cursor or RAM restoration claim.",
              "31 fixed ICONS.SS sources; unknown writes revoke ownership including same values. No HD, animation, cursor or RAM restoration claim.")
out.mkdir()
(out / "main.go").write_text(s)
for name in ["go.mod", "go.sum", "go.work"]:
    shutil.copyfile(a.reference / name, out / name)
subprocess.run(["gofmt", "-w", "main.go"], cwd=out, check=True, timeout=30)
subprocess.run(["go", "build", "-trimpath", "-o", "small-probe", "."], cwd=out, check=True, timeout=120)
subprocess.run(["go", "vet", "."], cwd=out, check=True, timeout=60)
meta = {"kind": "DRAFT-small-image-native-write-collector", "source_count": 31,
        "source_receipt_sha256": sha(a.catalog), "entry_report_sha256": sha(a.entry_report),
        "generator_sha256": sha(Path(__file__)), "source_base_sha256": sha(base),
        "original_file": "ICONS.SS", "original_sha256": original["sha256"], "sources": sources,
        "source_sha256": sha(out / "main.go"), "binary_sha256": sha(out / "small-probe"),
        "event_storage": "streamed JSON array", "event_limit": 8000000,
        "production_connected": False, "ownership": "unknown writes revoke, including same value"}
(out / "build.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
print("PASS_SMALL_IMAGE_NATIVE_COLLECTOR_BUILD", meta["binary_sha256"], flush=True)
