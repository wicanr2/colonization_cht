"""規格067：以隔離原型或READY正式組裝，驗十二來源的正常五語GUI及懸停。"""
import argparse,ast,hashlib,json,os,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for n in ['reference','prototype','candidates','native','output']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--formal',action='store_true',help='以READY正式組裝與標準素材入口驗證')
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and not out.exists() and out.parent.stat().st_uid==os.getuid()
build_path=a.prototype/('formal-build-r1.json' if a.formal else 'build.json');build=read(build_path)
sources=build['go_sources'] if a.formal else build['generated_go_sha256']
runtime=a.prototype/('formal-runtime-r1' if a.formal else 'runtime')
assert len(sources)==50 and (a.formal or not build['production_connected'])
assert all(sha(runtime/n)==digest for n,digest in sources.items())
binding=build['source_bindings']['source_sha256'] if a.formal else build['source_bindings']
assert len(binding)==(33 if a.formal else 30) and all(sha(repo/n)==digest for n,digest in binding.items())
gui=a.reference/'gui-build-r1';old=read(gui/'gui-r1/check.json');assert old['result']=='PASS_CURSOR_FORMAL_FIVE_LANGUAGE_GUI' and len(old['checks'])==92
native=read(a.native/'check.json');assert native['result']=='PASS_TERRAIN_BATCH_PROTOTYPE_NATIVE_29'
positions={}
cursor=(a.native/'point-000.cursor').read_bytes();assert len(cursor)==256 and hashlib.sha256(cursor).hexdigest()=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
opaque=[(k%16,k//16) for k,v in enumerate(cursor) if v!=255];assert len(opaque)==82
for n in read(a.candidates)['sources']:
 ordinal=n['ordinal'];samples=[]
 for point in native['points']:
  cells={int(k) for k,c in point['terrain_batch_cells'].items() if c['ordinal']==ordinal and int(k)%320<240 and 16<=int(k)//320<134}
  if cells:samples.append(cells)
 assert samples,ordinal
 cells=set.intersection(*samples)
 assert cells,ordinal
 candidates={(k%320-dx,k//320-dy) for k in cells for dx,dy in opaque if 0<=k%320-dx<240 and 16<=k//320-dy<134}
 position=max(candidates,key=lambda xy:(sum((xy[1]+dy)*320+xy[0]+dx in cells for dx,dy in opaque),-xy[1],-xy[0]))
 assert any((position[1]+dy)*320+position[0]+dx in cells for dx,dy in opaque)
 positions[ordinal]=list(position)
out.mkdir();module=out/'runtime-gui';shutil.copytree(runtime,module)
for name in ['adapter.go','terrain079_probe_helpers.go']:shutil.copyfile(gui/'runtime-gui-r1'/name,module/name)
helper=module/'terrain079_probe_helpers.go';s=helper.read_text()
old='for n, data := range map[string][]byte';assert s.count(old)==1
s=s.replace(old,'''batchCells:=map[int]map[string]any{}
 if batch:=p.h.terrainBatch;batch!=nil {for i,c:=range batch.visible {if c.owned {batchCells[i]=map[string]any{"ordinal":int(c.ordinal),"local":int(c.k),"native":c.native}}}}
 for n, data := range map[string][]byte''',1)
old='"cells": cells,';assert s.count(old)==1;s=s.replace(old,'"cells": cells,"batch_cells":batchCells,"terrain_batch":p.h.terrainBatch.receipt(f),',1);helper.write_text(s)
subprocess.run(['gofmt','-w',str(module/'adapter.go'),str(helper)],check=True,timeout=30)
bundle=out/'gui-bundle';shutil.copytree(a.prototype/'formal-bundle-r1' if a.formal else a.reference/'bundle-r3',bundle,symlinks=True)
subprocess.run(['go','build','-trimpath','-o',str(bundle/'bin/colonization-window'),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
script=(gui/'probe-gui-r1.py').read_text();old_prefix='/out/gui-build-r1/gui-bundle-r1';assert old_prefix in script
script=script.replace(old_prefix,str(bundle))
old='def terrain079_mask(hd):';assert script.count(old)==1
new='''def terrain_batch_mask(hd):
    group=hd.get("terrain_batch") or {}
    if not group:return Image.new("1",(1280,800))
    need(group.get("prototype") is True and group.get("formal") is False,"不是十二來源原型")
    raw=base64.b64decode(group["mask"],validate=True)
    need(len(raw)==8000 and sum(v.bit_count() for v in raw)==group["painted"]==group["valid"]<=group["owned"],"批次來源遮罩或alpha不齊")
    im=Image.new("1",(320,200));im.putdata([bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)])
    return im.resize((1280,800),Image.Resampling.NEAREST)
def terrain079_mask(hd):
    return ImageChops.logical_or(formal_terrain079_mask(hd),terrain_batch_mask(hd))
def formal_terrain079_mask(hd):'''
script=script.replace(old,new,1)
for old,new in [
 ('def switch_round(scene):','def switch_round(scene,locales=None):'),
 ('locales = ["en"] if scene == "hd-quit-confirmation" else ["zh-Hans", "ja", "ko", "en", "zh-Hant"]','locales = locales or (["en"] if scene == "hd-quit-confirmation" else ["zh-Hans", "ja", "ko", "en", "zh-Hant"])'),
 ('or scene in terrain_scenes else ["hd", "original"]','or scene in terrain_scenes or scene.startswith("terrain-batch-") else ["hd", "original"]'),
 ('    command += ["--hd-terrain079-probe-root",str(terrain_root)]','    command += ["--hd-terrain079-probe-root",str(terrain_root),"--hd-terrain-batch-prototype",'+repr(str(a.candidates.parent/'candidates'))+']'),
 ('PASS_CURSOR_FORMAL_FIVE_LANGUAGE_GUI','PASS_TWELVE_TERRAIN_PROTOTYPE_FIVE_LANGUAGE_GUI'),
 ('need(len(checks)==92,"地形必要GUI範圍不同")','need(len(checks)==96,"地形必要GUI範圍不同")'),
 ('46種正式素材的92組五語GUI與九個正常邊界／恢復；完整原版重播及全量HD另驗。','46種正式素材加十二來源DRAFT原型，96組五語GUI、36份來源懸停與九個邊界／恢復；完整原版重播及全量HD另驗。'),
]:
 assert script.count(old)==1,(old,script.count(old));script=script.replace(old,new,1)
old='            switch_round("terrain079-start")\n';assert script.count(old)==1
hover='''            switch_round("terrain-batch-en",locales=["en"])
            batch_hovers=[]
            for ordinal,xy in __POSITIONS__:
                wait(lambda state:live(state).get("hd",{}).get("terrain_batch",{}).get("by_ordinal",{}).get(str(ordinal),0)>0,"來源尚被原版後畫遮擋")
                before_group=live(status()).get("hd",{}).get("terrain_batch",{})
                before_restores=before_group.get("owned_cursor_restores_by_ordinal",{}).get(str(ordinal),0)
                for sample_phase,position in [("hover",xy),("away",[224,176]),("return",xy)]:
                    x,y=position;before=status()["step"];move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"批次正常懸停未完成")
                    if sample_phase=="away":
                        wait(lambda state:live(state).get("hd",{}).get("terrain_batch",{}).get("by_ordinal",{}).get(str(ordinal),0)>0,"來源在原版後畫撤除後尚未恢復")
                    label="terrain-batch-%03d-%s"%(ordinal,sample_phase)
                    proof=terrain_snapshot(label,locale="en")
                    group=proof["frame"]["native_live"].get("hd",{}).get("terrain_batch") or {}
                    need(group.get("prototype") and not group.get("formal"),"批次原型沒有生效")
                    if sample_phase=="away":
                        need(group.get("by_ordinal",{}).get(str(ordinal),0)>0,"移開後來源沒有恢復HD")
                    batch_hovers.append({"ordinal":ordinal,"phase":sample_phase,"snapshot":label,"step":proof["state"]["step"],"ram_cursor_restores_before":before_restores,"ram_cursor_restores_observed":group.get("owned_cursor_restores_by_ordinal",{}).get(str(ordinal),0)-before_restores,"group":group})
            switch_round("terrain-batch-restored",locales=["zh-Hant"])
'''.replace('__POSITIONS__',repr(sorted(positions.items())))
script=script.replace(old,old+hover,1)
old='            marker.write_text(json.dumps({"label":label,"buttons":0,"min_step":before+200000,"require_hd":bool(locale) if require_hd is None else require_hd,"ordinal":79,"locale":locale}))'
assert script.count(old)==1
script=script.replace(old,'            pending=marker.with_suffix(".pending")\n'+old.replace('marker.write_text','pending.write_text')+'\n            pending.replace(marker)',1)
old='        result["formal_assets"]=46';assert script.count(old)==1
script=script.replace(old,old+'\n        result["prototype_terrain_sources"]=12\n        result["production_connected"]=False\n        result["terrain_batch_hovers"]=batch_hovers\n        need(len(checks)==96 and len(batch_hovers)==36,"批次GUI範圍不齊")',1)
# 新增兩個取樣標籤仍是世界畫面，沿所有既有世界判準，避免漏列地圖城名等欄位。
world_sets={ast.get_source_segment(script,node) for node in ast.walk(ast.parse(script)) if isinstance(node,ast.Set) and any(isinstance(item,ast.Constant) and item.value=='world' for item in node.elts)}
assert world_sets
for segment in world_sets:
 assert '"world"' in segment
 script=script.replace(segment,segment.replace('"world"','"world","terrain-batch-en","terrain-batch-restored"',1))
lines=script.splitlines()
for i,line in enumerate(lines):
 if line.strip().startswith('if graphics == "original" or not ('):lines[i]=line[:-2]+' or hd.get("terrain_batch",{}).get("painted")):'
 if line.strip().startswith('if c["graphics"] != "hd" or not ('):lines[i]=line[:-2]+' or c["native_live"].get("hd",{}).get("terrain_batch",{}).get("painted")):'
script='\n'.join(lines)+'\n';compile(script,'terrain_batch_gui','exec');(out/'probe-gui.py').write_text(script)
if a.formal:
 script=script.replace(',"--hd-terrain-batch-prototype",'+repr(str(a.candidates.parent/'candidates')),'')
 assert '--hd-terrain-batch-prototype' not in script
 script=script.replace('group.get("prototype") is True and group.get("formal") is False','group.get("prototype") is False and group.get("formal") is True')
 script=script.replace('group.get("prototype") and not group.get("formal")','not group.get("prototype") and group.get("formal")')
 script=script.replace('PASS_TWELVE_TERRAIN_PROTOTYPE_FIVE_LANGUAGE_GUI','PASS_WORLD_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI')
 script=script.replace('result["formal_assets"]=46','result["formal_assets"]=58').replace('result["prototype_terrain_sources"]=12','result["formal_terrain_sources"]=12').replace('result["production_connected"]=False','result["production_connected"]=True')
 script=script.replace('46種正式素材加十二來源DRAFT原型','58種正式素材').replace('十二來源原型','十二來源正式層').replace('批次原型沒有生效','批次正式層沒有生效')
 compile(script,'world_terrain_formal_gui','exec');(out/'probe-gui.py').write_text(script)
run=(gui/'run-gui-r1.sh').read_text().replace('/out/gui-build-r1/gui-bundle-r1',str(bundle)).replace('/out/gui-build-r1/probe-gui-r1.py',str(out/'probe-gui.py')).replace('/out/gui-build-r1/gui-r1',str(out/'gui')).replace('/out/gui-build-r1/cursor-prototype-gui-xvfb-r1.log',str(out/'xvfb.log'))
(out/'run-gui.sh').write_text(run)
result={'result':'PASS_WORLD_TERRAIN_FORMAL_READ_ONLY_GUI_BUILD' if a.formal else 'PASS_TERRAIN_BATCH_READ_ONLY_GUI_PROTOTYPE_BUILD','go_sources':len(list(module.glob('*.go'))),'source_bindings':binding,'source_assembly_sha256':sha(build_path),'gui_binary_sha256':sha(bundle/'bin/colonization-window'),'gui_python_sha256':sha(out/'probe-gui.py'),'hover_positions':positions,'production_connected':a.formal}
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(result['result'],len(positions),flush=True)
