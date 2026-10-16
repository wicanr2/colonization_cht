"""規格068 DRAFT：從已驗正式來源組裝可丟棄8×8原型，不修改正式入口。"""
import argparse,hashlib,json,os,shutil,subprocess
from collections import Counter
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for name in ['reference','original','candidates','source-report','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists()
build=read(a.reference/'formal-build-r1.json');bindings=build['source_bindings']['source_sha256']
assert len(bindings)==33 and len(build['go_sources'])==50
used=['hd_world_terrain_runtime.go','hd_world_terrain_runtime_test.go']
assert all(sha(repo/'tools'/n)==build['go_sources'][n] for n in used)
proof=read(a.source_report);assert proof['result']=='PASS_SMALL_TERRAIN_15_SOURCES_AND_65_ORIGINAL_MODELS' and proof['original_state_and_saves_equal']
arts=read(a.candidates)['sources'];targets=[112,113,116,119,126,127,136,139];assert [x['ordinal'] for x in arts]==targets
rows={n:proof['sources'][str(n)] for n in targets};assert all(r['size']==[8,8] and r['visible_native_cells']>0 for r in rows.values())
assert sha(a.original/'inputs.json')=='6783faef06b074fa738bc33276ac186f89479954b75e6d5a142868fbdacb113f'
assert sha(a.original/'points.json')=='11233aafe611c91ab1bb3425676e03e7bb30b8a25d62fab3ec1bd6ec6617dfb5'
copies=read(a.original/'model-r1/terrain-batch-ram-copies.json');counts=Counter(x['kind'] for x in copies if x['cell']['ordinal'] in targets)
assert counts=={'save':697,'restore':474} and sum(x['cell']['ordinal'] in targets for x in read(a.original/'model-r1/cursor-pairs.json'))==56
out.mkdir();runtime=out/'runtime';runtime.mkdir()
for n,h in build['go_sources'].items():
 source=a.reference/'formal-runtime-r1'/n;assert sha(source)==h;shutil.copyfile(source,runtime/n)
for n in ['go.mod','go.sum','go.work','go.work.sum','language-catalogs.json','observation-sources.json']:shutil.copyfile(a.reference/'formal-runtime-r1'/n,runtime/n)
s=(repo/'tools/hd_world_terrain_runtime.go').read_text().replace('hdTerrainBatch','hdSmallTerrain').replace('HDTerrainBatch','HDSmallTerrain')
s=s.replace('// 規格067 READY：十二世界來源；共用原版觀測，只合成顯示。','// 規格068 DRAFT：八個8×8來源的隔離原型。')
s=s.replace('"bytes"','"bytes"\n "flag"',1)
s=s.replace('type hdSmallTerrainDefinition struct {','var hdSmallTerrainDirectory=flag.String("hd-small-terrain-prototype","","規格068候選目錄")\n\ntype hdSmallTerrainDefinition struct {',1)
for old,new in [
 ('[256]byte','[64]byte'),('[256]uint16','[64]uint16'),
 ('image.Rect(0, 0, 64, 64)','image.Rect(0, 0, 32, 32)'),('y < 64','y < 32'),('x < 64','x < 32'),
 ('d.width/128','d.width/64'),('d.height/128','d.height/64'),('len(p.frames) != 12','len(p.frames) != 8'),
 ('x+16 > 320','x+8 > 320'),('y+16 > 200','y+8 > 200'),('record[4] != 16 || record[5] != 16','record[4] != 8 || record[5] != 8'),
 ('k < 256','k < 64'),('k/16','k/8'),('k%16','k%8'),('x >= 16 || y < 0 || y >= 16','x >= 8 || y < 0 || y >= 8'),
 ('k := y*16 + x','k := y*8 + x'),('int(c.k)%16','int(c.k)%8'),('int(c.k)/16','int(c.k)/8'),
 ('"formal": true, "prototype": false','"formal": false, "prototype": true'),
]:assert old in s,(old,'source-shape-changed');s=s.replace(old,new)
s=s.replace('owned, valid, painted := 0, 0, 0','owned, valid, painted := 0, 0, 0\n preservedZero:=0',1)
old='frame := p.frames[int(c.ordinal)]';assert s.count(old)==1
s=s.replace(old,'''if c.native==0 {
 x,y:=i%320*4,i/320*4
 color0:=color.RGBA{(f.palette[0]<<2)|(f.palette[0]>>4),(f.palette[1]<<2)|(f.palette[1]>>4),(f.palette[2]<<2)|(f.palette[2]>>4),255}
 draw.Draw(out,image.Rect(x,y,x+4,y+4),image.NewUniform(color0),image.Point{},draw.Src)
 painted++;preservedZero++;by[int(c.ordinal)]++;mask[i>>3]|=1<<uint(i&7)
 continue
 }
 frame := p.frames[int(c.ordinal)]''',1)
s=s.replace('"painted": painted,','"painted": painted, "generated_painted":painted-preservedZero,"preserved_native_zero":preservedZero,',1)
(runtime/'hd_small_terrain_prototype.go').write_text(s)
defs=['package main','var hdSmallTerrainDefinitions=[]hdSmallTerrainDefinition{']
for art in arts:
 n=art['ordinal'];r=rows[n];assert sha(a.candidates.parent/art['file'])==art['sha256']
 defs.append('{%d,%d,%d,%d,%d,%s,%s,%s,%s},'%(n,r['encoded_length'],r['opaque_cells'],*art['size'],*[json.dumps(x) for x in [r['encoded_sha256'],r['sorted_local_offset_value_sha256'],Path(art['file']).name,art['sha256']]]))
defs.append('}');(runtime/'hd_small_terrain_sources.go').write_text('\n'.join(defs)+'\n')
s=(repo/'tools/hd_world_terrain_runtime_test.go').read_text().replace('hdTerrainBatch','hdSmallTerrain').replace('HDTerrainBatch','HDSmallTerrain').replace('h.terrainBatch','h.smallTerrain').replace('terrain_batch','small_terrain').replace('TEST_TERRAIN_BATCH','TEST_SMALL_TERRAIN')
s=s.replace('TestHDWorldTerrainNative29','TestHDSmallTerrainPrototypeNative65').replace('TestHDWorldTerrainAssetNegatives','TestHDSmallTerrainPrototypeAssetNegatives')
s=s.replace('// 規格067 READY：正式十二來源與獨立原版收據的同狀態驗證。','// 規格068 DRAFT：隔離八來源與65點原版收據。')
for old,new in [
 ('gui-oracle-inputs.json','inputs.json'),('gui-oracle-points.json','points.json'),('gui-oracle-r1/control','oracle-r1/control'),
 ('63b8cc52610760adf4a63e4d8351a262d6c4007db45e3939f24ce94de1f20cfb','6783faef06b074fa738bc33276ac186f89479954b75e6d5a142868fbdacb113f'),
 ('len(points) != 29','len(points) != 65'),('len(replay.Inputs) != 109','len(replay.Inputs) != 143'),('218130001','251625001'),
 ('at != 29','at != 65'),('p.accepted != 80','p.accepted != 57'),('p.bufferSaves != 3325','p.bufferSaves != 697'),('p.bufferRestores != 2471','p.bufferRestores != 474'),('len(p.pairs) != 220','len(p.pairs) != 56'),
 ('len(entries) != 12','len(entries) != 8'),('len(finishes) != 12','len(finishes) != 8'),('len(ownership) != 12','len(ownership) != 8'),('len(negatives) != 108','len(negatives) != 72'),
 ('p.y+k/16','p.y+k/8'),('p.x+k%16','p.x+k%8'),('len(cases) != 40','len(cases) != 28'),('len(positive.frames) != 12','len(positive.frames) != 8'),
 ('PASS_WORLD_TERRAIN_FORMAL_NATIVE_29','PASS_SMALL_TERRAIN_PROTOTYPE_NATIVE_65'),('PASS_TERRAIN_BATCH_40_LOADER_NEGATIVES_AND_POSITIVE_RECHECK','PASS_SMALL_TERRAIN_28_LOADER_NEGATIVES_AND_POSITIVE_RECHECK'),('"production_connected": true','"production_connected": false'),
]:assert old in s,(old,'test-shape-changed');s=s.replace(old,new)
old='h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))';assert s.count(old)==1
s=s.replace(old,'''previous:=*hdSmallTerrainDirectory
 *hdSmallTerrainDirectory=os.Getenv("TEST_SMALL_TERRAIN_CANDIDATES")
 defer func(){*hdSmallTerrainDirectory=previous}()
 h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))''',1)
old='os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_SMALL_TERRAIN_ASSET_OUTPUT")';assert s.count(old)==1
s=s.replace(old,'os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_SMALL_TERRAIN_CANDIDATES"), os.Getenv("TEST_SMALL_TERRAIN_ASSET_OUTPUT")',1)
s=s.replace('if opaque < 0 || transparent < 0 {','if opaque < 0 {',1)
anchor='\tvar result []string\n\tfor _, test := range tests {'
assert s.count(anchor)==2
at=s.index(anchor,s.index('func hdSmallTerrainFinishNegatives('))
s=s[:at]+''' if transparent<0 {
 tests[2].name="outside-write"
 tests[2].change=func(n *hdSmallTerrainRuntime){n.outside=true}
 }
'''+s[at:]
(runtime/'hd_small_terrain_prototype_test.go').write_text(s)
def patch(name,old,new):
 path=runtime/name;s=path.read_text();assert s.count(old)==1,(name,old);path.write_text(s.replace(old,new,1))
patch('hd_runtime.go','type hdRuntime struct {','type hdRuntime struct {\n smallTerrain *hdSmallTerrainRuntime')
patch('hd_runtime.go','h.terrainBatch, err = loadHDTerrainBatchRuntime(h, game, directory)','if *hdSmallTerrainDirectory!="" {h.smallTerrain,err=loadHDSmallTerrainRuntime(h,game,*hdSmallTerrainDirectory);if err!=nil{return nil,err}}\n h.terrainBatch, err = loadHDTerrainBatchRuntime(h, game, directory)')
patch('hd_runtime.go','h.terrainBatch.beforeInstruction()','h.terrainBatch.beforeInstruction()\n h.smallTerrain.beforeInstruction()')
patch('hd_runtime.go','receipt["terrain_batch"] = h.terrainBatch.paint(out, f)','receipt["terrain_batch"] = h.terrainBatch.paint(out, f)\n }\n if h.smallTerrain!=nil {receipt["small_terrain"]=h.smallTerrain.paint(out,f)')
patch('hd_runtime.go','if h != nil && h.small != nil {','if h!=nil && h.smallTerrain!=nil {base=fmt.Sprintf("%s/small-terrain/%d",base,h.smallTerrain.revision)}\n if h != nil && h.small != nil {')
patch('hd_sea_runtime.go','h.terrainBatch.memoryWrite(a, old, value)','h.terrainBatch.memoryWrite(a, old, value)\n }\n if h.smallTerrain!=nil {h.smallTerrain.memoryWrite(a,old,value)')
subprocess.run(['gofmt','-w',*[str(runtime/n) for n in ['hd_runtime.go','hd_sea_runtime.go','hd_small_terrain_prototype.go','hd_small_terrain_sources.go','hd_small_terrain_prototype_test.go']]],check=True,timeout=30)
subprocess.run(['go','build','-trimpath','-o',str(out/'colonization-window-prototype'),'.'],cwd=runtime,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=runtime,check=True,timeout=120)
result={'result':'PASS_SMALL_TERRAIN_ISOLATED_PROTOTYPE_BUILD','source_bindings':bindings,'baseline_bindings_only':True,'baseline_graphics_directory':str(a.reference/'formal-bundle-r1/graphics'),'current_assembly_inputs':{n:sha(repo/'tools'/n) for n in used},'generated_go_sha256':{p.name:sha(p) for p in runtime.glob('*.go')},'candidate_index_sha256':sha(a.candidates),'native_source_report_sha256':sha(a.source_report),'prototype_builder_sha256':sha(Path(__file__)),'production_connected':False}
assert len(result['generated_go_sha256'])==53
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(result['result'],53,flush=True)

