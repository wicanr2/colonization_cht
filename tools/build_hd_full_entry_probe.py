"""R49 DRAFT：產生全SS來源的唯讀入口探針；不安裝HD或授予生命週期信用。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
for name in ["catalog", "base-probe", "output"]:
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--start-step", type=int, default=50000000,
                    help="唯讀入口觀測起點；0含冷啟動，預設保持R49範圍")
a = parser.parse_args()
assert 0 <= a.start_step <= 50000000
out = a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert out.is_relative_to("/out") and out.parent.stat().st_uid == os.getuid()
assert not out.exists()
assert digest(a.base_probe) == "5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6"
d = json.loads(a.catalog.read_bytes())
assert not d["summary"]["failed_files"] and d["summary"]["ss_files"] == 206
assert d["summary"]["ss_frame_records"] == 1517 and d["summary"]["pik_files"] == 35
inputs = {f["file"]: f["sha256"] for f in d["files"] if f["format"] == "SS"}
sources = [f for f in d["frames"] if f["file"] in inputs and
           f["decode_status"] == "decoded" and f["opaque_pixels"] > 0 and f["encoded_length"] > 0]
assert len(inputs) == 206 and len(sources) == 1429
for f in sources:
    assert digest(a.catalog.parent / "pixels" / f'{f["research_id"]:04d}.idx') == f["indexed_sha256"]
go = a.base_probe.read_text()
start = go.index("var buildingSources = []buildingSource{")
end = go.index("\n}\n", start) + 2
rows = ["var buildingSources = []buildingSource{"]
for f in sources:
    rows.append("\t{%d,%d,%d,%d,%d,%s,%s,nil}," % (
        f["research_id"], *f["size"], f["opaque_pixels"], f["encoded_length"],
        json.dumps(f["encoded_sha256"]), json.dumps(f["indexed_sha256"])))
rows.append("}")
go = go[:start] + "\n".join(rows) + go[end:]
go = go.replace('`json:"ordinal"`', '`json:"unique_research_id"`', 1)
go = go.replace("type buildingCall struct {", "type buildingCall struct {\n" +
                '\tCandidates []int `json:"candidate_research_ids"`\n', 1)
start = go.index("func (b *buildingObserver) beforeStep()")
end = go.index("\nfunc ", start + 1)
body = '''func (b *buildingObserver) beforeStep() {
 if b==nil || b.m.Steps<50000000{return};m:=b.m
 if m.CPU.Seg[golem.CS]!=0xd46 || m.CPU.IP!=0xa{return}
 if len(b.calls)>=20000{panic("catalog call limit")}
 if !bytes.Equal(b.read(0xd46,0xa,12),[]byte{0xc8,0x28,0,0,0x52,0x53,0x50,0x57,0x56,0x8b,0x47,2}){panic("catalog entry mismatch")}
 stack:=buildingWords(b.read(m.CPU.Seg[golem.SS],m.CPU.R[golem.SP],10))
 off:=uint16((m.CPU.R[golem.AX]&0x7fff)*12+stack[3]+0x36)
 record:=buildingWords(b.read(stack[4],off,12)); descriptor:=buildingWords(b.read(m.CPU.Seg[golem.DS],m.CPU.R[golem.BX],8))
 x,y:=int(int16(m.CPU.R[golem.DX])),int(int16(stack[2]))
 matches:=[]int{};digest:="";hashes:=map[int]string{}
 for _,source:=range buildingSources{
  if int(record[4])!=source.Width || int(record[5])!=source.Height{continue}
  hash,found:=hashes[source.Length]
  if !found{hash=buildingHash(b.read(record[1],record[0],source.Length));hashes[source.Length]=hash}
  if hash==source.Encoded{matches=append(matches,source.Ordinal);digest=hash}
 }
 c:=&buildingCall{Ordinal:-1,Candidates:matches,Entry:m.Steps,Registers:m.CPU.R,Segments:m.CPU.Seg,Stack:stack,Descriptor:descriptor,RecordFar:fmt.Sprintf("%04X:%04X",stack[4],off),Record:record,SourceFar:fmt.Sprintf("%04X:%04X",record[1],record[0]),SourceSHA:digest,Canvas:uint32(descriptor[3])*16+uint32(descriptor[2]),Rect:[4]int{x,y,x+int(record[4]),y+int(record[5])},EntryCode:fmt.Sprintf("%x",b.read(0xd46,0xa,12)),Mismatch:"entry only; lifecycle unverified"}
 if len(matches)==1{c.Ordinal=matches[0]}
 b.calls=append(b.calls,c)
}
'''
go = go[:start] + body + go[end:]
start = go.index("func (b *buildingObserver) write(")
end = go.index("\nfunc ", start + 1)
go = go[:start] + "func (b *buildingObserver) write(addr uint32, old, value byte) {}\n" + go[end:]
watch = '''\t\tfor _, base := range []uint32{buildingMain, buildingStage} {
\t\t\tm.WatchWrite(base, base+63999, func(_ *golem.Machine, a uint32, o, v byte) { observer.write(a, o, v) })
\t\t}'''
assert go.count(watch) == 1
go = go.replace(watch, "")
needle = '\tseedBytes, inputBytes := buildingRead(*seed), buildingRead(*inputs)'
checks = ['\tfor name, want := range map[string]string{']
checks.extend("\t\t%s:%s," % (json.dumps(n), json.dumps(h)) for n, h in sorted(inputs.items()))
checks.extend(['\t} {', '\t\tpath:=filepath.Join(*root,name)',
               '\t\tif _,err:=os.Stat(path);os.IsNotExist(err){fmt.Fprintln(os.Stderr,"SKIP: missing legal original "+name);os.Exit(77)}',
               '\t\tif buildingHash(buildingRead(path))!=want{panic("SS fingerprint mismatch: "+name)}', '\t}'])
assert go.count(needle) == 1
go = go.replace(needle, "\n".join(checks) + "\n" + needle)
go = go.replace('"building-%03d.pixels"', '"%04d.idx"')
go = go.replace("Ten exact decoded sources; no production HD, animation, cursor or RAM restoration claim.",
                "All nonempty decoded SS source candidates at 0D46:000A after 50000000 steps; alias sets preserved. Entry matching only, no drawing lifecycle, PIK, animation, HD, cursor or RAM restoration claim.")
go = go.replace("readonly-colony-building-batch-normal-input-research", "readonly-full-ss-entry-catalog-normal-input-research")
go = go.replace("// 規格064 DRAFT：十種城內建築的唯讀正常路徑探針。", "// 目標186 R49 DRAFT：全SS的唯讀正常路徑入口探針。")
if a.start_step != 50000000:
    assert go.count('b.m.Steps<50000000') == 1
    go = go.replace('b.m.Steps<50000000', 'b.m.Steps<' + str(a.start_step))
    go = go.replace('after 50000000 steps', 'after ' + str(a.start_step) + ' steps')
out.mkdir()
(out / "entry-catalog.go").write_text(go)
proof = {"kind": "DRAFT-readonly-all-SS-source-entry-catalog", "inputs": inputs,
         "catalog_sha256": digest(a.catalog), "generator_sha256": digest(Path(__file__)),
         "base_probe_sha256": digest(a.base_probe), "sources": sources,
         "limitations": ["Research IDs are catalog row keys, not original AX values or production keys.",
                         "Alias candidate sets remain unresolved; no first-match identity.",
                         "Only 0D46:000A after step " + str(a.start_step) + "; no PIK or whole-game coverage claim.",
                         "No write observer, no ownership, no HD installation."]}
(out / "source-catalog.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n")
print("PASS_FULL_SS_ENTRY_PROBE_PREPARED", len(sources), digest(out / "entry-catalog.go"), flush=True)
