"""規格067 DRAFT：在隔離副本組裝十二來源原型，不修改正式Go或原版資料。"""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for n in ['reference','candidates','source-report','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
report=read(a.source_report);assert sha(a.source_report)=='4774317a1df07bf762d1d08f483b7c87f202b3588baa363d60c62d2201d0eee8'
assert report['new_targets']==[6,9,17,66,71,74,77,78,80,96,147,150] and not report['production_connected']
build=read(a.reference/'build-r3.json');bindings=build['source_bindings']['source_sha256']
assert len(bindings)==30 and all(sha(repo/n)==digest for n,digest in bindings.items())
candidate_data=read(a.candidates);candidates={r['ordinal']:r for r in candidate_data['sources']};assert set(candidates)==set(report['new_targets'])
out.mkdir();runtime=out/'runtime';runtime.mkdir()
originals={}
for name,digest in build['go_sources'].items():
 source=a.reference/'runtime-r3'/name
 assert sha(source)==digest
 (runtime/name).write_bytes(source.read_bytes());originals[name]=digest
for name in ['go.mod','go.sum','go.work','go.work.sum','language-catalogs.json','observation-sources.json']:(runtime/name).write_bytes((a.reference/'runtime-r3'/name).read_bytes())
s=(repo/'tools/hd_terrain079_runtime.go').read_text().replace('hdTerrain079','hdTerrainBatch').replace('HDTerrain079','HDTerrainBatch')
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
one('// 規格062 R58 READY：世界079來源；沿既有海洋觀測回呼，只合成顯示。','// 規格067 DRAFT：十二來源可丟棄原型；未接正式程式。')
one('"bytes"','"bytes"\n "flag"')
start=s.index('const hdTerrainBatchEncoded');end=s.index('type hdTerrainBatchCell',start)
s=s[:start]+'''var hdTerrainBatchDirectory = flag.String("hd-terrain-batch-prototype", "", "規格067隔離候選目錄")
type hdTerrainBatchDefinition struct { ordinal,length,opaque,width,height int; encoded,writes,asset,assetSHA string }
type hdTerrainBatchFrame struct { hdTerrainBatchDefinition; art *image.RGBA }
'''+s[end:]
one('owned  bool','owned  bool\n ordinal uint16')
one('art                                                                            *image.RGBA','frames map[int]*hdTerrainBatchFrame\n current *hdTerrainBatchFrame\n before [256]byte\n acceptedBy map[int]uint64\n cursorRestoresBy map[int]uint64')
start=s.index('func loadHDTerrainBatchRuntime(');end=s.index('func (p *hdTerrainBatchRuntime) memoryWrite',start)
s=s[:start]+'''func loadHDTerrainBatchRuntime(h *hdRuntime, game, directory string) (*hdTerrainBatchRuntime,error) {
 if h==nil{return nil,fmt.Errorf("missing verified HD runtime")}
 raw,err:=hdReadFile(filepath.Join(game,"PHYS0.SS"),8<<20);if err!=nil{return nil,err}
 if hash(raw)!="deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16" {return nil,fmt.Errorf("terrain source mismatch")}
 p:=&hdTerrainBatchRuntime{h:h,frames:map[int]*hdTerrainBatchFrame{},acceptedBy:map[int]uint64{},cursorRestoresBy:map[int]uint64{},pending:map[int]hdTerrainBatchPair{},backing:map[uint32]hdTerrainBatchCell{}}
 for _,d:=range hdTerrainBatchDefinitions {
  raw,err=hdReadFile(filepath.Join(directory,d.asset),8<<20);if err!=nil{return nil,err}
  if hash(raw)!=d.assetSHA{return nil,fmt.Errorf("terrain candidate mismatch: %d",d.ordinal)}
  im,err:=png.Decode(bytes.NewReader(raw));if err!=nil{return nil,err}
  if im.Bounds()!=image.Rect(0,0,d.width,d.height) || d.width!=d.height {return nil,fmt.Errorf("terrain candidate shape mismatch")}
  f:=&hdTerrainBatchFrame{hdTerrainBatchDefinition:d,art:image.NewRGBA(image.Rect(0,0,64,64))}
  for y:=0;y<64;y++ {for x:=0;x<64;x++ {f.art.SetRGBA(x,y,color.RGBAModel.Convert(im.At((2*x+1)*d.width/128,(2*y+1)*d.height/128)).(color.RGBA))}}
  p.frames[d.ordinal]=f
 }
 if len(p.frames)!=12{return nil,fmt.Errorf("incomplete terrain group")};return p,nil
}

'''+s[end:]
one('if cs != 0xd46 || ip != 0xa || c.R[golem.AX] != 80 {','if cs != 0xd46 || ip != 0xa {')
one('pc := int(cs)*16 + int(ip)\n\tif !bytes.Equal(m.Mem[pc:pc+12]', 'frame,selected:=p.frames[int(c.R[golem.AX])-1]\n if !selected {return}\n pc := int(cs)*16 + int(ip)\n\tif !bytes.Equal(m.Mem[pc:pc+12]')
one('off := uint16(80*12 + uint32(stack[3]) + 0x36)','off := uint16(uint32(c.R[golem.AX])*12 + uint32(stack[3]) + 0x36)')
one('if int(record[0])+285 > 65536 || at+285 > len(m.Mem) || hash(m.Mem[at:at+285]) != hdTerrainBatchEncoded {','if int(record[0])+frame.length > 65536 || at+frame.length > len(m.Mem) || hash(m.Mem[at:at+frame.length]) != frame.encoded {')
one('p.active = true','p.current=frame\n for k:=0;k<256;k++ {p.before[k]=m.Mem[hdTerrainBatchStage+uint32((y+k/16)*320+x+k%16)]}\n p.active = true')
one('"ordinal": 79, "entry_step"','"ordinal": frame.ordinal, "entry_step"')
one('hash(m.Mem[at : at+285])','hash(m.Mem[at : at+frame.length])')
start=s.index('func (p *hdTerrainBatchRuntime) finish()');end=s.index('func (p *hdTerrainBatchRuntime) canvasWrite',start)
s=s[:start]+'''func (p *hdTerrainBatchRuntime) finish() {
 p.active=false;var encoded []byte;count:=0
 for k,v:=range p.writes {
  actual:=p.h.m.Mem[hdTerrainBatchStage+uint32((p.y+k/16)*320+p.x+k%16)]
  if p.counts[k]==0 {if actual!=p.before[k] {p.rejected++;return};continue}
  if p.counts[k]!=1 || actual!=v {p.rejected++;return}
  count++;encoded=binary.LittleEndian.AppendUint16(encoded,uint16(k));encoded=append(encoded,v)
 }
 if p.outside || p.current==nil || count!=p.current.opaque || hash(encoded)!=p.current.writes {p.rejected++;return}
 for k,v:=range p.writes {if p.counts[k]==1 {p.stage[(p.y+k/16)*320+p.x+k%16]=hdTerrainBatchCell{true,uint16(p.current.ordinal),byte(k),v}}}
 p.accepted++;p.acceptedBy[p.current.ordinal]++
 if p.trace {
  if len(p.calls)>=20000 {panic("terrain calls limit")}
  p.entry["return_step"]=p.h.m.Steps;p.entry["writes_sha256"]=hash(encoded);p.calls=append(p.calls,p.entry);p.entry=nil
 }
}
'''+s[end:]
one('"ordinal": 79, "step"','"ordinal": int(prior.cell.ordinal), "step"')
one('p.cursorRestores++','p.cursorRestores++\n if prior.cell.owned {p.cursorRestoresBy[int(prior.cell.ordinal)]++}')
start=s.index('func (p *hdTerrainBatchRuntime) paint(');end=s.index('func (p *hdTerrainBatchRuntime) receipt(',start)
s=s[:start]+'''func (p *hdTerrainBatchRuntime) paint(out *image.RGBA,f draftNativeFrame) map[string]any {
 if p==nil{return nil};owned,valid,painted:=0,0,0;mask:=make([]byte,8000);by:=map[int]int{};validBy:=map[int]int{}
 for i,c:=range p.visible {
  if !c.owned {continue};owned++;if f.canvas[i]!=c.native {continue};valid++;validBy[int(c.ordinal)]++
  frame:=p.frames[int(c.ordinal)];sx,sy:=int(c.k)%16*4,int(c.k)/16*4;active:=false
  for y:=0;y<4;y++ {for x:=0;x<4;x++ {if frame.art.RGBAAt(sx+x,sy+y).A>0 {active=true}}}
  if !active {continue};x,y:=i%320*4,i/320*4
  draw.Draw(out,image.Rect(x,y,x+4,y+4),frame.art,image.Pt(sx,sy),draw.Over)
  painted++;by[int(c.ordinal)]++;mask[i>>3]|=1<<uint(i&7)
 }
 return map[string]any{"formal":false,"prototype":true,"accepted":p.accepted,"accepted_by_ordinal":p.acceptedBy,"rejected":p.rejected,"owned":owned,"valid":valid,"painted":painted,"by_ordinal":by,"valid_by_ordinal":validBy,"transferred":p.transferred,"cursor_restore_points":p.cursorRestores,"owned_cursor_restores_by_ordinal":p.cursorRestoresBy,"buffer_saves":p.bufferSaves,"buffer_restores":p.bufferRestores,"mask":mask,"revision":p.revision}
}

'''+s[end:]
(runtime/'hd_terrain_batch_prototype.go').write_text(s)
defs=['package main','var hdTerrainBatchDefinitions=[]hdTerrainBatchDefinition{']
for n in report['new_targets']:
 r=report['sources'][str(n)];art=candidates[n];source=a.candidates.parent/art['file'];assert sha(source)==art['sha256']
 defs.append('{%d,%d,%d,%d,%d,%s,%s,%s,%s},'%(n,r['encoded_length'],r['opaque_cells'],*art['size'],*[json.dumps(v) for v in [r['encoded_sha256'],r['sorted_local_offset_value_sha256'],Path(art['file']).name,art['sha256']]]))
defs.append('}')
(runtime/'hd_terrain_batch_sources.go').write_text('\n'.join(defs)+'\n')
(runtime/'hd_world_terrain_prototype_test.go').write_bytes((repo/'tools/hd_world_terrain_prototype_test.go').read_bytes())
def patch(name,old,new):
 path=runtime/name;text=path.read_text();assert text.count(old)==1,(name,old);path.write_text(text.replace(old,new,1))
patch('hd_runtime.go','h.terrain079, err = loadHDTerrain079Runtime(h, game, directory)','if *hdTerrainBatchDirectory!="" {h.terrainBatch,err=loadHDTerrainBatchRuntime(h,game,*hdTerrainBatchDirectory);if err!=nil{return nil,err}}\n h.terrain079, err = loadHDTerrain079Runtime(h, game, directory)')
patch('hd_runtime.go','type hdRuntime struct {','type hdRuntime struct {\n terrainBatch *hdTerrainBatchRuntime')
patch('hd_runtime.go','h.terrain079.beforeInstruction()','h.terrain079.beforeInstruction()\n h.terrainBatch.beforeInstruction()')
patch('hd_runtime.go','receipt["terrain079"] = h.terrain079.paint(out, f)','receipt["terrain079"] = h.terrain079.paint(out, f)\n }\n if h.terrainBatch!=nil {receipt["terrain_batch"]=h.terrainBatch.paint(out,f)')
patch('hd_runtime.go','if h != nil && h.small != nil {','if h!=nil && h.terrainBatch!=nil {base=fmt.Sprintf("%s/terrain-batch/%d",base,h.terrainBatch.revision)}\n if h != nil && h.small != nil {')
patch('hd_sea_runtime.go','h.terrain079.memoryWrite(a, old, value)','h.terrain079.memoryWrite(a, old, value)\n }\n if h.terrainBatch!=nil {h.terrainBatch.memoryWrite(a,old,value)')
subprocess.run(['gofmt','-w',str(runtime/'hd_runtime.go'),str(runtime/'hd_sea_runtime.go'),str(runtime/'hd_terrain_batch_prototype.go'),str(runtime/'hd_terrain_batch_sources.go'),str(runtime/'hd_world_terrain_prototype_test.go')],check=True,timeout=30)
unchanged={n:sha(runtime/n)==digest for n,digest in originals.items()};assert all(v for n,v in unchanged.items() if n not in ['hd_runtime.go','hd_sea_runtime.go'])
result={'result':'PASS_TERRAIN_BATCH_ISOLATED_PROTOTYPE_ASSEMBLY','source_bindings':bindings,'formal_go_sources':originals,'unchanged_formal_sources':unchanged,'source_report_sha256':sha(a.source_report),'candidate_index_sha256':sha(a.candidates),'generated_go_sha256':{p.name:sha(p) for p in runtime.glob('*.go')},'production_connected':False}
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(result['result'],len(result['generated_go_sha256']),flush=True)
