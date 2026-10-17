"""規格062 R47 DRAFT：唯讀蒐集地形逐寫、游標來源及RAM暫存，不安裝HD。"""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for name in ['sources','inputs','points','reference','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();repo=Path('/repo');out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0
assert out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
catalog=a.sources/'source-catalog.json';assert sha(catalog.read_bytes())=='b1185d86b627175f647a0d11a06a0a4a339299ade30e329f15fa2dfc108b5d68'
data=json.loads(catalog.read_bytes());ordinals={128, 129, 65, 73, 74, 75, 76, 77, 101, 102, 103, 104, 105, 109, 110, 111, 112, 125, 126}
rows=[r for r in data['sources'] if r['file']=='ICONS.SS' and r['ordinal'] in ordinals]
assert len(rows)==len(ordinals)
base=repo/'tools/probe_hd_building_batch.go';assert sha(base.read_bytes())=='5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6'
s=base.read_text()
s=s.replace('candidate := &buildingSources[i]','candidate := &buildingSources[i]\n if int(record[4])!=candidate.Width || int(record[5])!=candidate.Height || int(m.CPU.R[golem.AX]&0x7fff)!=candidate.Ordinal+1 {continue}')
fixture_points=json.loads(a.points.read_bytes());fixture_input_sha=sha(a.inputs.read_bytes());fixture_point_sha=sha(a.points.read_bytes())
assert len(fixture_points)==61
fixture_end=fixture_points[-1]['step']
for old,new in [
 ('821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901',fixture_point_sha),
 ('3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca',fixture_input_sha),
 ('9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979',fixture_input_sha),
 ('len(points) != 49','len(points) != 61'),
 ('end := uint64(75900000)','end := uint64('+str(fixture_end)+')'),
 ('end = 134600000','end = '+str(fixture_end)),
 ('case "enter", "escape", "backspace":','case "enter", "escape", "backspace", "up", "down", "left", "right":'),
 ('"Backspace"}[e.Kind]','"Backspace", "up":"Up", "down":"Down", "left":"Left", "right":"Right"}[e.Kind]')]:
 assert old in s,old
 s=s.replace(old,new)

def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
start=s.index('var buildingSources = []buildingSource{');end=s.index('\n}\n',start)+2
source_rows=['var buildingSources = []buildingSource{']
for row in rows:source_rows.append('{%d,%d,%d,%d,%d,%s,%s,nil},'%(row['ordinal'],*row['size'],row['opaque'],row['length'],json.dumps(row['encoded_sha256']),json.dumps(row['indexed_sha256'])))
s=s[:start]+'\n'.join(source_rows)+'\n}'+s[end:]
one('"BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4"','"ICONS.SS": "a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716"')
# 保留原版49點與來源前後完整矩形。觀測軌跡不替轉送建立正式身分。
one('if b.tracked[s][i] {','''if s==0 && cs==0xcba && ip==0xca {
  delta:=int(addr)-(int(b.m.CPU.Seg[golem.ES])*16+int(b.m.CPU.R[golem.DI]))
  src:=int(b.m.CPU.Seg[golem.DS])*16+int(b.m.CPU.R[golem.SI])+delta
  ss,si,known:=buildingSurface(uint32(src))
  if delta>=0 && delta<2 && known && b.tracked[ss][si] {b.tracked[s][i]=true}
 }
 if b.tracked[s][i] || (s==0 && cs==0xb68 && ip==0x51c) {''')
one('"after_cell": b.owners[s][i]','"after_cell": b.owners[s][i], "registers":b.m.CPU.R, "segments":b.m.CPU.Seg')
one('".palette": m.DAC[:]}','".palette": m.DAC[:], ".cursor":m.Mem[0x1cd74:0x1ce74]}')
one('import (','import (\n "bufio"')
s,n=re.subn(r'events\s+\[\]map\[string\]any','eventCount int\n eventLog *bufio.Writer\n eventFile *os.File',s);assert n==1
s,n=re.subn(r'b\.events\s*=\s*append\(b\.events,\s*(map\[string\]any\{[^\n]+\})\)',r'b.event(\1)',s);assert n==2
s=s.replace('len(b.events)','b.eventCount').replace('len(observer.events)','observer.eventCount').replace('>= 1000000','>= 8000000')
s,n=re.subn(r'(observer = &buildingObserver\{[^\n]+\})',r'\1\n observer.openEvents(filepath.Join(*out,"writes.json"))\n defer observer.closeEvents()',s);assert n==1
one('buildingJSON(filepath.Join(*out, "writes.json"), observer.events)','observer.closeEvents()\n result["raw_event_count"]=observer.eventCount')
s+='''
func (b *buildingObserver) openEvents(path string) {
 var err error;b.eventFile,err=os.Create(path);buildingNeed(err)
 b.eventLog=bufio.NewWriterSize(b.eventFile,65536);_,err=b.eventLog.WriteString("[\\n");buildingNeed(err)
}
func (b *buildingObserver) event(value map[string]any) {
 if b.eventCount>=8000000 {panic("地形事件超過8M有界上限")}
 if b.eventCount>0 {_,err:=b.eventLog.WriteString(",\\n");buildingNeed(err)}
 raw,err:=json.Marshal(value);buildingNeed(err);_,err=b.eventLog.Write(raw);buildingNeed(err);b.eventCount++
}
func (b *buildingObserver) closeEvents() {
 if b.eventLog==nil{return};_,err:=b.eventLog.WriteString("\\n]\\n");buildingNeed(err)
 buildingNeed(b.eventLog.Flush());buildingNeed(b.eventFile.Close());b.eventLog=nil
}
'''
# 既有49點、53筆正常輸入的指紋守門沿原始探針，不接受任意座標注入。
assert sha(a.points.read_bytes())==fixture_point_sha
assert sha(a.inputs.read_bytes())==fixture_input_sha

one('type buildingObserver struct {','type buildingObserver struct {\n cursorInit bool')
one('func (b *buildingObserver) beforeStep() {','''func (b *buildingObserver) beforeStep() {
 if b!=nil && !b.cursorInit && b.m.Steps>=49999999 {
  b.event(map[string]any{"kind":"cursor-init","step":b.m.Steps,"linear":0x1cd74,"bytes":b.m.Mem[0x1cd74:0x1ce74]});b.cursorInit=true
 }''')
one('for _, base := range []uint32{buildingMain, buildingStage} {','''m.WatchWrite(0x1cd74,0x1ce73,func(_ *golem.Machine,a uint32,old,value byte){
 if m.Steps<50000000{return};cs,ip:=m.CPU.OpAddr();pc:=int(cs)*16+int(ip)
 observer.event(map[string]any{"kind":"cursor-write","step":m.Steps,"linear":a,"old":old,"value":value,"site":fmt.Sprintf("%04X:%04X",cs,ip),"code16":fmt.Sprintf("%x",m.Mem[pc:pc+16])})
 })
 for _, base := range []uint32{buildingMain, buildingStage} {''')


one('type buildingObserver struct {','type buildingObserver struct {\n ramTracked map[uint32]bool')
one('if delta>=0 && delta<2 && known && b.tracked[ss][si] {b.tracked[s][i]=true}',
    'if delta>=0 && delta<2 && ((known && b.tracked[ss][si]) || b.ramTracked[uint32(src)]) {b.tracked[s][i]=true}')
one('for _, base := range []uint32{buildingMain, buildingStage} {',r'''
 m.WatchWrite(0,0x9ffff,func(_ *golem.Machine,a uint32,old,value byte){
  if m.Steps<50000000 || (a>=buildingMain && a<buildingMain+64000) || (a>=buildingStage && a<buildingStage+64000) {return}
  cs,ip:=m.CPU.OpAddr();pc:=int(cs)*16+int(ip)
  delta:=int(a)-(int(m.CPU.Seg[golem.ES])*16+int(m.CPU.R[golem.DI]))
  src:=int(m.CPU.Seg[golem.DS])*16+int(m.CPU.R[golem.SI])+delta
  surface,pos,known:=buildingSurface(uint32(src))
  traced:=observer.ramTracked[a]
  if cs==0xcba && ip==0xca && delta>=0 && delta<2 && ((known && observer.tracked[surface][pos]) || observer.ramTracked[uint32(src)]) {traced=true}
  if !traced{return}
  if observer.ramTracked==nil{observer.ramTracked=map[uint32]bool{}}
  observer.ramTracked[a]=true
  observer.event(map[string]any{"kind":"ram-write","step":m.Steps,"linear":a,"old":old,"value":value,"registers":m.CPU.R,"segments":m.CPU.Seg,"site":fmt.Sprintf("%04X:%04X",cs,ip),"code16":fmt.Sprintf("%x",m.Mem[pc:pc+16])})
 })
 for _, base := range []uint32{buildingMain, buildingStage} {
''')
one('".cursor":m.Mem[0x1cd74:0x1ce74]}','".cursor":m.Mem[0x1cd74:0x1ce74], ".memory":m.Mem}')

out.mkdir();(out/'main.go').write_text(s)
for name in ['go.mod','go.sum','go.work']:shutil.copyfile(a.reference/name,out/name)
subprocess.run(['gofmt','-w','main.go'],cwd=out,check=True,timeout=15)
subprocess.run(['go','build','-trimpath','-o','terrain-probe','.'],cwd=out,check=True,timeout=120)
subprocess.run(['go','vet','.'],cwd=out,check=True,timeout=60)
meta={'kind':'DRAFT-unit19-raw-RAM-lifecycle-collector','ordinals':sorted(ordinals),'source_catalog_sha256':sha(catalog.read_bytes()),'source_base_sha256':sha(base.read_bytes()),'generated_source_sha256':sha((out/'main.go').read_bytes()),'binary_sha256':sha((out/'terrain-probe').read_bytes()),'production_connected':False,'event_limit':8000000,'claim':'raw original calls and writes only; no HD, cursor restoration or RAM source identity'}
(out/'build.json').write_text(json.dumps(meta,indent=2)+'\n');print('PASS_TERRAIN_RAW_COLLECTOR_BUILD',flush=True)
