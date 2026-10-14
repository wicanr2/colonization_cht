"""規格064 R42 DRAFT：組裝九來源逐筆原版／游標觀測，不改正式入口。"""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for name in ["inputs","points","output","reference"]:p.add_argument("--"+name,type=Path,required=True)
p.add_argument("--end",type=int,help="可選正常輸入終點；不得早於檢查點或晚於輸入收據")
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo/"workplace")
assert out.parent.stat().st_uid==os.getuid() and not out.exists()
inputs=a.inputs.resolve();raw=a.points.read_bytes();points=json.loads(raw)
assert 1<=len(points)<=100
assert all(isinstance(q.get("step"),int) and isinstance(q.get("dos_input_count"),int) for q in points)
assert points==sorted(points,key=lambda q:(q["step"],q["dos_input_count"]))
base=repo/"tools/probe_hd_building_batch.go"
assert sha(base.read_bytes())=="5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6"
s=base.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
# Reuse the reviewed raw collector transformations, without running its GUI assumptions.
template=(repo/"tools/build_hd_building024_lifecycle_probe.py").read_text()
transforms=template.split("s=base.read_text()\n",1)[1].split('(out/"main.go").write_text(s)',1)[0]
transforms=transforms.replace('buildingSources=[]buildingSource{buildingSources[2]}',
 'selected:=[]buildingSource{}; for _,src:=range buildingSources {if src.Ordinal!=24 {selected=append(selected,src)}}; buildingSources=selected')
transforms=transforms.replace('"if len(points) != 10 {"','"if len(points) != '+str(len(points))+' {"')
exec(compile(transforms,str(repo/"tools/build_hd_building024_lifecycle_probe.py"),"exec"))
if a.end is not None:
 assert max(q["step"] for q in points)<=a.end<=json.loads(inputs.read_bytes())["end"]
 one("end = "+str(max(q["step"] for q in points)),"end = "+str(a.end))
one('if b.tracked[s][i] {','if b.tracked[s][i] || (s==0 && cs==0xb68 && ip==0x51c) {')
one('".palette": m.DAC[:]}','".palette": m.DAC[:], ".cursor":m.Mem[0x1cd74:0x1ce74], ".cursor-background":m.Mem[0xafa00:0xafb00], ".cursor-final":m.Mem[0xafb00:0xafc00]}')
s=s.replace('readonly-building-024-gui-cursor-background-research','readonly-nine-building-cursor-source-research')
s=s.replace("10點",str(len(points))+"點")
s=s.replace('Single frame 024; no production HD, animation, cursor or RAM restoration claim.',
            'Nine fixed sources; raw cursor evidence only, no production HD or unverified RAM restoration claim.')
# 首輪正常GUI的1848次來源，相對120次／387259事件約需6M筆；8M為有界餘量。
# 逐筆寫相同JSON陣列，避免在Go與後續檢查器保留整個事件表。
one('import (','import (\n "bufio"')
s,n=re.subn(r'events\s+\[\]map\[string\]any','eventCount int\n eventLog *bufio.Writer\n eventFile *os.File',s);assert n==1
s,n=re.subn(r'b\.events\s*=\s*append\(b\.events,\s*(map\[string\]any\{[^\n]+\})\)',r'b.event(\1)',s);assert n==5
s=s.replace('len(b.events)','b.eventCount').replace('len(observer.events)','observer.eventCount')
assert s.count('>= 1000000')+s.count('>=1000000')==3
s=s.replace('>= 1000000','>= 8000000').replace('>=1000000','>=8000000')
s,n=re.subn(r'(observer = &buildingObserver\{[^\n]+\})',r'\1\n observer.openEvents(filepath.Join(*out,"writes.json"))\n defer observer.closeEvents()',s);assert n==1
one('buildingJSON(filepath.Join(*out, "writes.json"), observer.events)','observer.closeEvents()\n result["raw_event_count"]=observer.eventCount')
s+='''
func (b *buildingObserver) openEvents(path string) {
 var err error;b.eventFile,err=os.Create(path);buildingNeed(err)
 b.eventLog=bufio.NewWriterSize(b.eventFile,65536);_,err=b.eventLog.WriteString("[\\n");buildingNeed(err)
}
func (b *buildingObserver) event(value map[string]any) {
 if b.eventCount>=8000000 {panic("九來源事件證據超過8M有界上限")}
 if b.eventCount>0 {_,err:=b.eventLog.WriteString(",\\n");buildingNeed(err)}
 raw,err:=json.Marshal(value);buildingNeed(err);_,err=b.eventLog.Write(raw);buildingNeed(err);b.eventCount++
}
func (b *buildingObserver) closeEvents() {
 if b.eventLog==nil{return};_,err:=b.eventLog.WriteString("\\n]\\n");buildingNeed(err)
 buildingNeed(b.eventLog.Flush());buildingNeed(b.eventFile.Close());b.eventLog=nil
}
'''
out.mkdir();(out/"points.json").write_bytes(raw);(out/"main.go").write_text(s)
for name in ["go.mod","go.sum","go.work"]:shutil.copyfile(a.reference/name,out/name)
subprocess.run(["gofmt","-w","main.go"],cwd=out,check=True,timeout=30)
subprocess.run(["go","build","-trimpath","-o","nine-probe","."],cwd=out,check=True,timeout=120)
subprocess.run(["go","vet","."],cwd=out,check=True,timeout=60)
meta={"kind":"DRAFT-nine-native-source-collector","ordinals":[16,21,27,35,39,42,43,44,45],
      "input_sha256":sha(inputs.read_bytes()),"points_sha256":sha(raw),"points":len(points),
      "source_sha256":sha((out/"main.go").read_bytes()),"binary_sha256":sha((out/"nine-probe").read_bytes()),
      "source_base_sha256":sha(base.read_bytes()),"collector_transform_sha256":sha(template.encode())}
meta.update({"event_storage":"streamed JSON array; no retained event table","event_limit":8000000})
(out/"build.json").write_text(json.dumps(meta,indent=2)+"\n")
print("PASS_NINE_NATIVE_COLLECTOR_BUILD",meta["binary_sha256"],flush=True)
