"""規格064 DRAFT：沿木棚正常GUI收據組裝獨立原版來源／背景寫入探針。"""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
for name in ["gui","output","reference"]:parser.add_argument("--"+name,type=Path,required=True)
a=parser.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo/"workplace")
assert out.parent.stat().st_uid==os.getuid() and not out.exists()
gui=json.loads((a.gui/"check.json").read_bytes());inputs=a.gui/"gui.inputs.json"
assert gui["result"]=="PASS_SHELTER_PROTOTYPE_FIVE_LANGUAGE_GUI" and len(gui["checks"])==322
assert gui["gui_inputs_sha256"]==sha(inputs.read_bytes())
labels=["shelter-hover-roof","shelter-away-roof","shelter-return-roof","shelter-hover-post","shelter-away-post","shelter-return-post","shelter-drag-held","shelter-drag-moved","shelter-drag-returned","shelter-drag-released"]
points=[json.loads((a.gui/"shelter"/label/"check.json").read_bytes())["state"] for label in labels]
points.sort(key=lambda p:(p["step"],p["dos_input_count"]))
assert len({(p["step"],p["dos_input_count"]) for p in points})==10
out.mkdir();raw=(json.dumps(points,indent=2)+"\n").encode();(out/"points.json").write_bytes(raw)
base=repo/"tools/probe_hd_building_batch.go"
assert sha(base.read_bytes())=="5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6"
s=base.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
one("type buildingObserver struct {","type buildingObserver struct {\n backingTracked map[uint32]bool\n cursorInitialized bool")
one("func (b *buildingObserver) beforeStep() {",'''func (b *buildingObserver) beforeStep() {
 if b!=nil && !b.cursorInitialized && b.m.Steps>=49999999 {
  b.cursorInitialized=true
  b.events=append(b.events,map[string]any{"kind":"cursor-init","step":b.m.Steps,"linear":uint32(0x1cd74),"bytes":append([]byte(nil),b.m.Mem[0x1cd74:0x1ce74]...)})
 }''')
one("flag.Parse()",'''flag.Parse()
 if buildingSources[2].Ordinal!=24 {panic("固定第024幀綁定不同")}
 buildingSources=[]buildingSource{buildingSources[2]}''')
one('panic("觀測畫布不同")',"""cs,ip:=b.m.CPU.OpAddr()
  if addr>=0x1cd74 && addr<0x1ce74 {
   if len(b.events)>=1000000 {panic("游標來源證據超限")}
   b.events=append(b.events,map[string]any{"kind":"cursor-write","step":b.m.Steps,"linear":addr,"old":old,"value":value,"site":fmt.Sprintf("%04X:%04X",cs,ip),"code16":fmt.Sprintf("%x",b.read(cs,ip,16))})
   return
  }
  source:=-1;delta:=int(addr)-(int(b.m.CPU.Seg[golem.ES])*16+int(b.m.CPU.R[golem.DI]))
  copySite:=(cs==0xcba||cs==0xc9f)&&ip==0xca&&bytes.Equal(b.read(cs,ip,16),[]byte{0xf3,0xa5,3,0xf3,0x79,0xc,0x81,0xee,0,0x80,0x8c,0xd9,0x81,0xc1,0,8})
  selected:=false
  if copySite&&delta>=0&&delta<2 {
   source=int(b.m.CPU.Seg[golem.DS])*16+int(b.m.CPU.R[golem.SI])+delta
   ss,si,known:=buildingSurface(uint32(source))
   selected=known&&b.tracked[ss][si]
  }
  if b.backingTracked[addr]||selected {
   if len(b.events)>=1000000 {panic("木棚背景證據超限")}
   b.backingTracked[addr]=true
   b.events=append(b.events,map[string]any{"kind":"ram-write","step":b.m.Steps,"linear":addr,"old":old,"value":value,"site":fmt.Sprintf("%04X:%04X",cs,ip),"code16":fmt.Sprintf("%x",b.read(cs,ip,16)),"registers":b.m.CPU.R,"segments":b.m.CPU.Seg,"source_candidate":source})
  }
  return""")
one('"after_cell": b.owners[s][i]','"after_cell": b.owners[s][i], "registers": b.m.CPU.R, "segments": b.m.CPU.Seg')
one('copySites: map[string]uint64{}}','copySites: map[string]uint64{},backingTracked:map[uint32]bool{}}')
one('for _, base := range []uint32{buildingMain, buildingStage} {\n\t\t\tm.WatchWrite(base, base+63999,','for _, base := range []uint32{0} {\n\t\t\tm.WatchWrite(base, uint32(len(m.Mem)-1),')
one('wantInput = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"','wantInput = "'+sha(inputs.read_bytes())+'"')
one('"821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901"','"'+sha(raw)+'"')
one("if len(points) != 49 {","if len(points) != 10 {")
one("end = 134600000","end = "+str(max(p["step"] for p in points)))
s=s.replace("49點","10點").replace("readonly-colony-building-batch-normal-input-research","readonly-building-024-gui-cursor-background-research")
s=s.replace("Ten exact decoded sources; no production HD, animation, cursor or RAM restoration claim.","Single frame 024; no production HD, animation, cursor or RAM restoration claim.")
(out/"main.go").write_text(s)
for name in ["go.mod","go.sum","go.work"]:shutil.copyfile(a.reference/name,out/name)
subprocess.run(["gofmt","-w","main.go"],cwd=out,check=True,timeout=30)
subprocess.run(["go","build","-trimpath","-o","shelter-probe","."],cwd=out,check=True,timeout=120)
subprocess.run(["go","vet","."],cwd=out,check=True,timeout=60)
meta={"kind":"DRAFT-readonly-shelter-GUI-source-research","input_sha256":sha(inputs.read_bytes()),"points_sha256":sha(raw),"source_sha256":sha((out/"main.go").read_bytes()),"binary_sha256":sha((out/"shelter-probe").read_bytes()),"source_base_sha256":sha(base.read_bytes())}
(out/"build.json").write_text(json.dumps(meta,indent=2)+"\n")
print("PASS_SHELTER_GUI_LIFECYCLE_PROBE_BUILD",meta["binary_sha256"],flush=True)
