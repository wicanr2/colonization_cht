"""規格069 DRAFT：組裝冷啟動背景逐寫探針，原版及輸入唯讀。"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess
parser=argparse.ArgumentParser(description=__doc__)
for name in ["entry","reference","output"]:
    parser.add_argument("--"+name,type=Path,required=True)
parser.add_argument('--points',type=Path,help='可選：實際GUI檢查點；需同時提供inputs及end-step')
parser.add_argument('--inputs',type=Path,help='與points配對的實際DOS輸入')
parser.add_argument('--end-step',type=int,help='與points配對的有界原版終點')
parser.add_argument('--copy-closure',action='store_true',help='另記錄已驗RAM複製目的及後續撤銷寫入，最多300000個位址')
parser.add_argument('--copy-closure-c9f',action='store_true',help='搭配copy-closure，另觀測0C9F的同型複製入口；只記錄，不授予擁有權')
parser.add_argument('--memory-snapshots',action='store_true',help='每個實際GUI檢查點另存完整唯讀RAM，供游標與間接複製核對')
a=parser.parse_args()
assert not a.copy_closure_c9f or a.copy_closure
repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert out.is_relative_to("/out") and out.parent.stat().st_uid==os.getuid() and not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.entry/"entry-catalog.go")=="242751bcc3890494e414a8038e84419876af7506b5c2b2f83c9cbe80c87132ba"
out.mkdir()
ref=repo/"workplace/reports/goal186-display-hd/hd-building032-draw-boundary-20261012"
assert (a.points is None)==(a.inputs is None)==(a.end_step is None)
points=json.loads((a.points or ref/"lifecycle-public-r29-r1/observed/gui-points.json").read_bytes())
if a.points is None:points=points[:4]
end=a.end_step or 21000000
assert 1<=len(points)<=100 and 1<=end<=1200000000
assert [(x['step'],x['dos_input_count']) for x in points]==sorted(set((x['step'],x['dos_input_count']) for x in points))
assert all(0<=x['step']<=end for x in points)
(out/"points.json").write_text(json.dumps(points,indent=2)+"\n")
s=(a.entry/"entry-catalog.go").read_text()
s=s.replace('import (','import (\n "bufio"')
s=s.replace("821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901",sha(out/"points.json"))
s=s.replace("len(points) != 49","len(points) != "+str(len(points))).replace("end = 134600000","end = "+str(end))
if a.inputs:
    shutil.copyfile(a.inputs,out/'inputs.json')
    s=s.replace('3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca',sha(out/'inputs.json'))
s=s.replace("step := func() { observer.beforeStep();","step := func() { background.beforeStep(); observer.beforeStep();")
assert "background.beforeStep(); observer.beforeStep();" in s
needle="var checkpoints []map[string]any"
insert='''
 backgroundDOS=d
 if _,err:=os.Stat(filepath.Join(*root,"OPENMENU.PIK"));os.IsNotExist(err){fmt.Fprintln(os.Stderr,"SKIP: missing legal original OPENMENU.PIK");os.Exit(77)}
 if buildingHash(buildingRead(filepath.Join(*root,"OPENMENU.PIK")))!="f25c313c66a8f49bf79487fcecbcf76dafff2a81b713f2f3cb2e2d4349fd2004"{panic("OPENMENU version")}
 if observer!=nil {
  file,err:=os.Create(filepath.Join(*out,"background-writes.jsonl"));buildingNeed(err)
  raw:=buildingRead("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1181.idx")
  if buildingHash(raw)!="5325a3501b83df510cee60c134952130fdb9dfd4bdc00d9eb853fb7ae6021eff"{panic("PIK pixels differ")}
  background=&backgroundTrace{m:m,out:*out,file:file,log:bufio.NewWriterSize(file,1<<20),pik:raw}
  m.WatchWrite(0,0xaffff,func(_ *golem.Machine,a uint32,o,v byte){background.write(a,o,v)})
 }
'''
assert s.count(needle)==1;s=s.replace(needle,insert+needle)
s=s.replace('buildingJSON(filepath.Join(*out, "draws.json"), result)','background.close()\n buildingJSON(filepath.Join(*out, "draws.json"), result)')
TRACER=r'''
type backgroundTrace struct {
 m *golem.Machine
 out string
 file *os.File
 log *bufio.Writer
 events int
 active *buildingCall
 source *buildingSource
 before []byte
 calls []map[string]any
 pik []byte
 snapshots []map[string]any
 anchors []map[string]any
}
var background *backgroundTrace
func (b *backgroundTrace) beforeStep() {
 if b==nil{return}
 m:=b.m
 if m.Steps>=17800000 && m.Steps<=19800000 && m.Steps%100000==0 {
  row:=map[string]any{"step":m.Steps,"pik_full_ram_offset":bytes.Index(m.Mem,b.pik)}
  for name,base:=range map[string]uint32{"main":buildingMain,"stage":buildingStage} {
   raw:=m.Mem[base:base+64000];p:=fmt.Sprintf("background-%d.%s",m.Steps,name)
   buildingNeed(os.WriteFile(filepath.Join(b.out,p),raw,0644));row[name+"_file"]=p;row[name+"_sha256"]=buildingHash(raw)
  };b.snapshots=append(b.snapshots,row)
 }
 if b.active!=nil && m.CPU.Seg[golem.CS]==b.active.Stack[1] && m.CPU.IP==b.active.Stack[0] && m.CPU.R[golem.SP]==b.active.Registers[golem.SP]+10 {
  c:=b.active;n:=b.source.Width*b.source.Height;raw:=m.Mem[c.Canvas:c.Canvas+uint32(n)]
  if !bytes.Equal(raw,b.source.Raw){panic("background native source pixels differ")}
  buildingNeed(os.WriteFile(filepath.Join(b.out,fmt.Sprintf("texture-%d.before",b.source.Ordinal)),b.before,0644))
  buildingNeed(os.WriteFile(filepath.Join(b.out,fmt.Sprintf("texture-%d.after",b.source.Ordinal)),raw,0644))
  b.calls=append(b.calls,map[string]any{"source_id":b.source.Ordinal,"entry_step":c.Entry,"return_step":m.Steps,"base":c.Canvas,"size":[2]int{b.source.Width,b.source.Height},"return_cs_ip":fmt.Sprintf("%04X:%04X",c.Stack[1],c.Stack[0]),"source_pixels_sha256":buildingHash(raw),"entry":c})
  b.active=nil
 }
 if m.CPU.Seg[golem.CS]!=0xd46 || m.CPU.IP!=0xa{return}
 ss,sp:=m.CPU.Seg[golem.SS],m.CPU.R[golem.SP];at:=uint32(ss)*16+uint32(sp)
 stack:=buildingWords(m.Mem[at:at+10])
 off:=uint16((m.CPU.R[golem.AX]&0x7fff)*12+stack[3]+0x36)
 p:=uint32(stack[4])*16+uint32(off);record:=buildingWords(m.Mem[p:p+12])
 for i:=range buildingSources {
  f:=&buildingSources[i];if f.Ordinal!=1265 && f.Ordinal!=1287 && f.Ordinal!=1552{continue}
  src:=uint32(record[1])*16+uint32(record[0])
  if int(record[4])!=f.Width || int(record[5])!=f.Height || buildingHash(m.Mem[src:src+uint32(f.Length)])!=f.Encoded{continue}
  p=uint32(m.CPU.Seg[golem.DS])*16+uint32(m.CPU.R[golem.BX]);desc:=buildingWords(m.Mem[p:p+8])
  if b.active!=nil || desc[0]!=24 || desc[1]!=32 || m.CPU.R[golem.DX]!=0 || stack[2]!=0 || m.CPU.R[golem.AX]!=1{panic("background source shape unverified")}
  base:=uint32(desc[3])*16+uint32(desc[2])
  b.active=&buildingCall{Ordinal:f.Ordinal,Entry:m.Steps,Registers:m.CPU.R,Segments:m.CPU.Seg,Stack:stack,Descriptor:desc,Record:record,Canvas:base,EntryCode:fmt.Sprintf("%x",m.Mem[0xd46*16+0xa:0xd46*16+0xa+12])}
  b.source=f;b.before=append([]byte(nil),m.Mem[base:base+768]...);break
 }
}
func (b *backgroundTrace) write(a uint32,o,v byte) {
 if b==nil || b.m.Steps<14000000{return}
 yes:=(a>=buildingMain && a<buildingMain+64000)||(a>=buildingStage && a<buildingStage+64000)||(a>=0xa0000 && a<0xa0000+64000)
 for _,base:=range []uint32{404160,404960,181952} {yes=yes||(a>=base && a<base+768)}
 if !yes{return};if b.events>=6000000{panic("background event limit")}
 m:=b.m;cs,ip:=m.CPU.OpAddr();pc:=uint32(cs)*16+uint32(ip)
 if cs==0xc9f && ip==0xca && m.CPU.Seg[golem.DS]==0xa000 && m.CPU.R[golem.SI]==0 && m.CPU.R[golem.DI]==0 && a==uint32(m.CPU.Seg[golem.ES])*16 {
  raw:=m.Mem[0xa0000:0xa0000+64000];name:=fmt.Sprintf("pik-anchor-%d.vram",m.Steps)
  buildingNeed(os.WriteFile(filepath.Join(b.out,name),raw,0644))
  different:=0;for k,v:=range raw {if v!=b.pik[k]{different++}}
  b.anchors=append(b.anchors,map[string]any{"step":m.Steps,"registers":m.CPU.R,"segments":m.CPU.Seg,"ip":ip,"code16":fmt.Sprintf("%x",m.Mem[pc:pc+16]),"pixels_sha256":buildingHash(raw),"pixels_file":name,"different_pixels":different,"exact_pik":different==0})
 }
 fmt.Fprintf(b.log,"[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%q]\n",m.Steps,a,o,v,cs,ip,m.CPU.Seg[golem.DS],m.CPU.R[golem.SI],m.CPU.Seg[golem.ES],m.CPU.R[golem.DI],m.CPU.R[golem.AX],m.CPU.R[golem.CX],m.CPU.Flags,fmt.Sprintf("%x",m.Mem[pc:pc+16]))
 b.events++
}
func (b *backgroundTrace) close() {
 if b==nil{return};if b.active!=nil{panic("unfinished background source")}
 buildingNeed(b.log.Flush());buildingNeed(b.file.Close())
 buildingJSON(filepath.Join(b.out,"background.json"),map[string]any{"kind":"DRAFT-native-background-writes","events":b.events,"calls":b.calls,"snapshots":b.snapshots,"anchors":b.anchors,"opened":backgroundDOS.Opened,"reads":backgroundDOS.Reads,"address_space":"dosgolem real-mode CS:IP and 20-bit linear RAM; no IDA EA","production_connected":false})
}
var backgroundDOS *golem.DOS
'''
if a.copy_closure:
    TRACER=TRACER.replace('type backgroundTrace struct {','type backgroundTrace struct {\n copyAddresses map[uint32]bool',1)
    needle=' if !yes{return};if b.events>=6000000'
    assert TRACER.count(needle)==1
    TRACER=TRACER.replace(needle,''' // Observe copy destinations and all later invalidations, without assigning ownership.
 if cs,ip:=b.m.CPU.OpAddr();cs==0xcba && (ip==0x9c || ip==0x9e || ip==0xca) && a<0xa0000 {
  if b.copyAddresses==nil{b.copyAddresses=map[uint32]bool{}}
  b.copyAddresses[a]=true
  if len(b.copyAddresses)>300000{panic("copy observation address limit")}
 }
 yes=yes||b.copyAddresses[a]
'''+needle,1)
    if a.copy_closure_c9f:
        needle='cs==0xcba && (ip==0x9c || ip==0x9e || ip==0xca)'
        assert TRACER.count(needle)==1
        TRACER=TRACER.replace(needle,'(cs==0xcba || cs==0xc9f) && (ip==0x9c || ip==0x9e || ip==0xca)',1)
s+="\n"+TRACER
if a.memory_snapshots:
    needle='".palette": m.DAC[:]'
    assert s.count(needle)==1
    s=s.replace(needle,'".memory": m.Mem, '+needle,1)
(out/"main.go").write_text(s)
for name in ["go.mod","go.sum","go.work"]:shutil.copyfile(a.reference/name,out/name)
subprocess.run(["gofmt","-w","main.go"],cwd=out,check=True,timeout=20)
for cmd in [["go","build","-trimpath","-o","background-probe","."],["go","vet","."]]:
    subprocess.run(cmd,cwd=out,check=True,timeout=120)
meta={"kind":"DRAFT-readonly-background-source-collector","source_sha256":sha(out/"main.go"),"binary_sha256":sha(out/"background-probe"),"generator_sha256":sha(Path(__file__)),"entry_source_sha256":sha(a.entry/"entry-catalog.go"),"points_sha256":sha(out/"points.json"),"sources":3,"event_limit":6000000,"end":end,"production_connected":False}
if a.copy_closure:meta['copy_closure_address_limit']=300000
if a.copy_closure_c9f:meta['copy_closure_c9f']=True
if a.memory_snapshots:meta['complete_readonly_ram_per_checkpoint']=True
(out/"build.json").write_text(json.dumps(meta,indent=2)+"\n")
print("PASS_BACKGROUND_SOURCE_COLLECTOR_BUILD",meta["source_sha256"],flush=True)
