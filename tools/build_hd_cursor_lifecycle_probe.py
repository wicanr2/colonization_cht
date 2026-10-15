"""目標186 R59 DRAFT：唯讀追查一般游標來源至RAM，不安裝HD。"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess

p=argparse.ArgumentParser(description=__doc__)
for name in ['catalog','reference','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and not out.exists() and out.parent.stat().st_uid==os.getuid()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=repo/'tools/probe_hd_building_batch.go'
assert sha(base)=='5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6'
source=next(x for x in json.loads(a.catalog.read_bytes())['frames'] if x['file']=='CURSOR.SS' and x['ordinal']==0)
assert source['research_id']==309 and source['size']==[17,17] and source['opaque_pixels']==84 and source['encoded_length']==124
assert source['file_sha256']=='3ff5a4b70f08780f845b1e973d7dce3ff34868bb73279174210fce76332fffcb'
assert sha(a.catalog.parent/'pixels/0309.idx')==source['indexed_sha256']
s=base.read_text().replace('\n\t"sort"','')
start=s.index('var buildingSources = []buildingSource{');end=s.index('\n}\n',start)+2
s=s[:start]+('var buildingSources = []buildingSource{{0,17,17,84,124,%s,%s,nil}}'% (json.dumps(source['encoded_sha256']),json.dumps(source['indexed_sha256'])))+s[end:]
start=s.index('type buildingObserver struct {');end=s.index('func buildingState(',start)
s=s[:start]+r'''
type buildingObserver struct {
 m *golem.Machine
 calls []*buildingCall
 active *buildingCall
 events []map[string]any
 retCS,retIP,sp uint16
}
func (b *buildingObserver) read(seg,off uint16,n int) []byte {
 at:=uint32(seg)*16+uint32(off)
 if uint64(at)+uint64(n)>uint64(len(b.m.Mem)){panic("游標觀測讀取越界")}
 return b.m.Mem[at:at+uint32(n)]
}
func (b *buildingObserver) event(row map[string]any) {
 if len(b.events)>=100000{panic("游標觀測事件超過100K界限")};b.events=append(b.events,row)
}
func (b *buildingObserver) roi(c *buildingCall) []byte {
 var data []byte
 for y:=c.Rect[1];y<c.Rect[3];y++ {
  at:=c.Canvas+uint32(y*int(c.Descriptor[1])+c.Rect[0]);data=append(data,b.m.Mem[at:at+17]...)
 };return data
}
func (b *buildingObserver) beforeStep() {
 if b==nil{return};m:=b.m
 if b.active!=nil {
  if m.CPU.Seg[golem.CS]==b.retCS && m.CPU.IP==b.retIP && m.CPU.R[golem.SP]==b.sp+10 {
   c:=b.active;c.Return=m.Steps;c.ReturnRegisters=m.CPU.R;c.ReturnSegments=m.CPU.Seg;c.ReturnIP=m.CPU.IP;c.After=b.roi(c)
   b.event(map[string]any{"kind":"asset_return","step":m.Steps,"call":len(b.calls),"cursor_sha256":buildingHash(m.Mem[0x1cd74:0x1ce74]),"return_code64":fmt.Sprintf("%x",b.read(b.retCS,b.retIP,64))})
   b.active=nil
  } else if m.Steps-b.active.Entry>100000{panic("游標來源未在界限內返回")}
 }
 if m.CPU.Seg[golem.CS]!=0xd46 || m.CPU.IP!=0xa{return}
 ss,sp:=m.CPU.Seg[golem.SS],m.CPU.R[golem.SP];stack:=buildingWords(b.read(ss,sp,10))
 off:=uint16((m.CPU.R[golem.AX]&0x7fff)*12+stack[3]+0x36)
 record:=buildingWords(b.read(stack[4],off,12))
 if buildingHash(b.read(record[1],record[0],124))!=buildingSources[0].Encoded{return}
 if b.active!=nil || len(b.calls)>=64{panic("游標來源重入或呼叫超限")}
 descriptor:=buildingWords(b.read(m.CPU.Seg[golem.DS],m.CPU.R[golem.BX],8))
 x,y:=int(int16(m.CPU.R[golem.DX])),int(int16(stack[2]))
 if descriptor[0]!=17 || descriptor[1]!=17 || x!=0 || y!=0 || record[4]!=17 || record[5]!=17 || m.CPU.R[golem.AX]!=1 {panic("游標來源幾何未驗")}
 if !bytes.Equal(b.read(0xd46,0xa,12),[]byte{0xc8,0x28,0,0,0x52,0x53,0x50,0x57,0x56,0x8b,0x47,2}){panic("游標來源入口不同")}
 c:=&buildingCall{Ordinal:0,Entry:m.Steps,Registers:m.CPU.R,Segments:m.CPU.Seg,Stack:stack,Descriptor:descriptor,
 RecordFar:fmt.Sprintf("%04X:%04X",stack[4],off),Record:record,SourceFar:fmt.Sprintf("%04X:%04X",record[1],record[0]),SourceSHA:buildingSources[0].Encoded,
 ReturnSite:fmt.Sprintf("%04X:%04X",stack[1],stack[0]),Canvas:uint32(descriptor[3])*16+uint32(descriptor[2]),Rect:[4]int{x,y,x+17,y+17},
 EntryCode:fmt.Sprintf("%x",b.read(0xd46,0xa,12)),Selected:true,WriterSites:map[string]uint64{},WriterCode:map[string]string{}}
 c.Before=b.roi(c);b.calls=append(b.calls,c);b.active,b.sp,b.retCS,b.retIP=c,sp,stack[1],stack[0]
}
func (b *buildingObserver) write(addr uint32,old,value byte) {
 kind:=""
 if addr>=0x1cd74 && addr<0x1ce74{kind="cursor_ram"}
 if b.active!=nil && addr>=b.active.Canvas && addr<b.active.Canvas+289{kind="asset_draw"}
 if kind==""{return}
 c:=b.m.CPU;cs,ip:=c.OpAddr();site:=fmt.Sprintf("%04X:%04X",cs,ip)
 if kind=="asset_draw"{b.active.WriteCount++;b.active.WriterSites[site]++;b.active.WriterCode[site]=fmt.Sprintf("%x",b.read(cs,ip,16))}
 b.event(map[string]any{"kind":kind,"step":b.m.Steps,"call":len(b.calls),"linear":addr,"old":old,"value":value,"site":site,"code64":fmt.Sprintf("%x",b.read(cs,ip,64)),"registers":c.R,"segments":c.Seg,"ds_si32":append([]byte(nil),b.read(c.Seg[golem.DS],c.R[golem.SI],32)...),"es_di32":append([]byte(nil),b.read(c.Seg[golem.ES],c.R[golem.DI],32)...)})
}
''' +s[end:]
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
one('"BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4"','"CURSOR.SS": '+json.dumps(source['file_sha256']))
one('"building-%03d.pixels", source.Ordinal','"%04d.idx", 309')
one('observer = &buildingObserver{m: m, losses: map[string]uint64{}, copySites: map[string]uint64{}}','observer = &buildingObserver{m:m}')
start=s.index('\t\tfor _, base := range []uint32{buildingMain, buildingStage} {');end=s.index('\n\t}',start)
s=s[:start]+'\t\tm.WatchWrite(0,uint32(len(m.Mem)-1),func(_ *golem.Machine,a uint32,o,v byte){observer.write(a,o,v)})'+s[end:]
start=s.index('\t\tif observer != nil {\n\t\t\towners :=');end=s.index('\n\t}\n\tstep :=',start)
s=s[:start]+s[end:]
one('".palette": m.DAC[:]}','".palette": m.DAC[:],".cursor":m.Mem[0x1cd74:0x1ce74]}')
start=s.index('\n\t\tresult["ownership_loss_sites"]');end=s.index('\n\t}',start);s=s[:start]+s[end:]
s=s.replace('readonly-colony-building-batch-normal-input-research','readonly-standard-cursor-source-and-ram-research').replace('Ten exact decoded sources; no production HD, animation, cursor or RAM restoration claim.','DRAFT CURSOR.SS 000 source and RAM writes only; no HD or hotspot claim.')
out.mkdir();(out/'main.go').write_text(s)
for name in ['go.mod','go.sum','go.work']:shutil.copyfile(a.reference/name,out/name)
subprocess.run(['gofmt','-w','main.go'],cwd=out,check=True,timeout=20)
subprocess.run(['go','build','-trimpath','-o','cursor-probe','.'],cwd=out,check=True,timeout=120)
subprocess.run(['go','vet','.'],cwd=out,check=True,timeout=60)
meta={'kind':'DRAFT-read-only-standard-cursor-lifecycle','source':source,'source_base_sha256':sha(base),'generator_sha256':sha(Path(__file__)),'source_sha256':sha(out/'main.go'),'binary_sha256':sha(out/'cursor-probe'),'event_limit':100000,'production_connected':False}
(out/'build.json').write_text(json.dumps(meta,indent=2)+'\n');print('PASS_READ_ONLY_CURSOR_COLLECTOR_BUILD',flush=True)
