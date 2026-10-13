"""規格063 DRAFT：沿人物視窗收據組裝唯讀原版背景追蹤探針。"""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
for name in ["gui","output","reference"]:
 parser.add_argument("--"+name,type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];out=args.output.resolve()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo/"workplace")
assert out.parent.stat().st_uid==os.getuid() and not out.exists()
gui=json.loads((args.gui/"check.json").read_bytes())
inputs=args.gui/"gui.inputs.json"
assert gui["result"]=="PASS_PERSON_PROTOTYPE_FIVE_LANGUAGE_GUI" and len(gui["checks"])==252
assert gui["gui_inputs_sha256"]==sha(inputs.read_bytes())
labels=["person-hover-main","person-away-main","person-return-main","person-hover-garrison","person-away-garrison","person-return-garrison","person-drag-held","person-drag-moved","person-drag-returned","person-drag-released"]
points=[json.loads((args.gui/"person"/label/"check.json").read_bytes())["state"] for label in labels]
points.sort(key=lambda p:(p["step"],p["dos_input_count"]))
assert len({(p["step"],p["dos_input_count"]) for p in points})==10
out.mkdir()
raw=(json.dumps(points,indent=2)+"\n").encode();(out/"points.json").write_bytes(raw)
source=repo/"tools/probe_hd_person_draws.go"
assert sha(source.read_bytes())=="bba9120a9012d6a6a9b3286576e17839e8515f3afff1f56d99265d00dd446e52"
s=source.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a))
 s=s.replace(a,b,1)
one("type personObserver struct {","type personObserver struct {\n backingTracked map[uint32]bool")
one('panic("觀測畫布不同")',"""cs,ip:=b.m.CPU.OpAddr()
  source:=-1; delta:=int(addr)-(int(b.m.CPU.Seg[golem.ES])*16+int(b.m.CPU.R[golem.DI]))
  copySite:=(cs==0xcba||cs==0xc9f)&&ip==0xca&&bytes.Equal(b.read(cs,ip,16),[]byte{0xf3,0xa5,3,0xf3,0x79,0xc,0x81,0xee,0,0x80,0x8c,0xd9,0x81,0xc1,0,8})
  selected:=false
  if copySite&&delta>=0&&delta<2 {
   source=int(b.m.CPU.Seg[golem.DS])*16+int(b.m.CPU.R[golem.SI])+delta
   ss,si,known:=personSurface(uint32(source))
   selected=known&&b.tracked[ss][si]
  }
  if b.backingTracked[addr]||selected {
   if len(b.events)>=1000000 {panic("人物背景證據超限")}
   b.backingTracked[addr]=true
   b.events=append(b.events,map[string]any{"kind":"ram-write","step":b.m.Steps,"linear":addr,"old":old,"value":value,"site":fmt.Sprintf("%04X:%04X",cs,ip),"code16":fmt.Sprintf("%x",b.read(cs,ip,16)),"registers":b.m.CPU.R,"segments":b.m.CPU.Seg,"source_candidate":source})
  }
  return""")
one('"after_cell": b.owners[s][i]', '"after_cell": b.owners[s][i], "registers": b.m.CPU.R, "segments": b.m.CPU.Seg')
one('if len(b.events) >= 100000 {','if len(b.events) >= 1000000 {')
one('copySites: map[string]uint64{}}','copySites: map[string]uint64{},backingTracked:map[uint32]bool{}}')
one('for _, base := range []uint32{personMain, personStage} {\n\t\t\tm.WatchWrite(base, base+63999,','for _, base := range []uint32{0} {\n\t\t\tm.WatchWrite(base, uint32(len(m.Mem)-1),')
one('wantInput = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"','wantInput = "'+sha(inputs.read_bytes())+'"')
one('"821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901"','"'+sha(raw)+'"')
one('if len(points) != 49 {','if len(points) != 10 {')
one('end = 134600000','end = '+str(max(p["step"] for p in points)))
s=s.replace("49點","10點").replace("readonly-person-100-normal-input-research","readonly-person-100-gui-cursor-background-research")
(out/"main.go").write_text(s)
for name in ["go.mod","go.sum","go.work"]:
 p=args.reference/name;assert p.is_file();shutil.copyfile(p,out/name)
subprocess.run(["gofmt","-w","main.go"],cwd=out,check=True,timeout=30)
subprocess.run(["go","build","-trimpath","-o","person-probe","."],cwd=out,check=True,timeout=120)
subprocess.run(["go","vet","."],cwd=out,check=True,timeout=60)
(out/"build.json").write_text(json.dumps({"kind":"DRAFT-readonly-person-GUI-source-research","input_sha256":sha(inputs.read_bytes()),"points_sha256":sha(raw),"source_sha256":sha((out/"main.go").read_bytes()),"binary_sha256":sha((out/"person-probe").read_bytes()),"source_base_sha256":sha(source.read_bytes())},indent=2)+"\n")
print("PASS_PERSON_GUI_LIFECYCLE_PROBE_BUILD",sha((out/"person-probe").read_bytes()),flush=True)
