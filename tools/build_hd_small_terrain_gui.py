"""規格068：沿正式五語GUI核對八種小尺寸來源與正常懸停。"""
import argparse,ast,hashlib,json,os,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for n in ['base','formal','original','output']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists()
build=read(a.formal/'formal-build-r1.json');binding=build['source_bindings']['source_sha256']
assert len(build['go_sources'])==53 and len(binding)==36 and all(sha(repo/n)==h for n,h in binding.items())
assert all(sha(a.formal/'formal-runtime-r1'/n)==h for n,h in build['go_sources'].items())
base=a.base/'formal-gui-r1';parent=read(base/'gui/check.json');assert parent['result']=='PASS_WORLD_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI' and len(parent['checks'])==96
source=read(a.original/'source-review-r2.json');targets=[112,113,116,119,126,127,136,139]
proof=read(a.original/'oracle-r1/observed/draws.json');cursor=(a.original/'oracle-r1/observed'/(Path(proof['checkpoints'][0]['snapshot_prefix']).name+'.cursor')).read_bytes()
assert hashlib.sha256(cursor).hexdigest()=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
opaque=[(k%16,k//16) for k,v in enumerate(cursor) if v!=255];assert len(opaque)==82
positions={}
for n in targets:
 samples=[]
 for i in range(65):
  cells={int(k) for k,c in read(a.original/'model-r1'/f'point-{i:03d}.terrain-model.json').items() if c['ordinal']==n and int(k)%320<240 and 16<=int(k)//320<134}
  if cells:samples.append(cells)
 assert samples,n
 cells=set.intersection(*samples);assert cells,n
 candidates={(k%320-dx,k//320-dy) for k in cells for dx,dy in opaque if 0<=k%320-dx<240 and 16<=k//320-dy<134}
 positions[n]=max(candidates,key=lambda xy:(sum((xy[1]+dy)*320+xy[0]+dx in cells for dx,dy in opaque),-xy[1],-xy[0]))
out.mkdir();module=out/'runtime-gui';shutil.copytree(a.formal/'formal-runtime-r1',module)
for name in ['adapter.go','terrain079_probe_helpers.go']:shutil.copyfile(base/'runtime-gui'/name,module/name)
path=module/'terrain079_probe_helpers.go';s=path.read_text();old='for n, data := range map[string][]byte';assert s.count(old)==1
s=s.replace(old,'''smallCells:=map[int]map[string]any{}
 if group:=p.h.smallTerrain;group!=nil {for i,c:=range group.visible {if c.owned {smallCells[i]=map[string]any{"ordinal":int(c.ordinal),"local":int(c.k),"native":c.native}}}}
 for n, data := range map[string][]byte''',1)
old='"batch_cells": batchCells,';assert s.count(old)==1
s=s.replace(old,old+' "small_cells":smallCells,"small_terrain":p.h.smallTerrain.receipt(f),',1);path.write_text(s)
subprocess.run(['gofmt','-w',str(path),str(module/'adapter.go')],check=True,timeout=30)
bundle=out/'gui-bundle';shutil.copytree(a.formal/'formal-bundle-r1',bundle,symlinks=True)
subprocess.run(['go','build','-trimpath','-o',str(bundle/'bin/colonization-window'),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
script=(base/'probe-gui.py').read_text().replace('/out/formal-gui-r1',str(out))
old='def terrain_batch_mask(hd):';assert script.count(old)==1
script=script.replace(old,'''def small_terrain_mask(hd):
    group=hd.get("small_terrain") or {}
    if not group:return Image.new("1",(1280,800))
    need(group.get("formal") is True and group.get("prototype") is False,"不是正式8x8來源")
    raw=base64.b64decode(group["mask"],validate=True)
    need(len(raw)==8000 and sum(v.bit_count() for v in raw)==group["painted"]==group["valid"]<=group["owned"],"8x8遮罩或alpha不齊")
    need(group["generated_painted"]+group["preserved_native_zero"]==group["painted"],"8x8原版零值保留數不同")
    im=Image.new("1",(320,200));im.putdata([bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)])
    return im.resize((1280,800),Image.Resampling.NEAREST)
def terrain_batch_mask(hd):''',1)
old='return ImageChops.logical_or(formal_terrain079_mask(hd),terrain_batch_mask(hd))';assert script.count(old)==1
script=script.replace(old,'return ImageChops.logical_or(ImageChops.logical_or(formal_terrain079_mask(hd),terrain_batch_mask(hd)),small_terrain_mask(hd))',1)
old='scene.startswith("terrain-batch-")';assert script.count(old)==1
script=script.replace(old,old+' or scene.startswith("small-terrain-")',1)
old='            switch_round("terrain-batch-restored",locales=["zh-Hant"])\n';assert script.count(old)==1
hover='''            switch_round("small-terrain-en",locales=["en"])
            small_hovers=[]
            for ordinal,xy in __POSITIONS__:
                wait(lambda state:live(state).get("hd",{}).get("small_terrain",{}).get("by_ordinal",{}).get(str(ordinal),0)>0,"8x8來源尚未恢復")
                for sample_phase,position in [("hover",xy),("away",[224,176]),("return",xy)]:
                    x,y=position;before=status()["step"];move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"8x8正常懸停未完成")
                    if sample_phase=="away":
                        wait(lambda state:live(state).get("hd",{}).get("small_terrain",{}).get("by_ordinal",{}).get(str(ordinal),0)>0,"8x8移開後尚未恢復")
                    label="small-terrain-%03d-%s"%(ordinal,sample_phase)
                    proof=terrain_snapshot(label,locale="en")
                    group=proof["frame"]["native_live"].get("hd",{}).get("small_terrain") or {}
                    need(group.get("formal") and not group.get("prototype"),"8x8正式層未生效")
                    if sample_phase=="away":need(group.get("by_ordinal",{}).get(str(ordinal),0)>0,"8x8移開後沒有HD")
                    small_hovers.append({"ordinal":ordinal,"phase":sample_phase,"snapshot":label,"step":proof["state"]["step"],"group":group})
            switch_round("small-terrain-restored",locales=["zh-Hant"])
'''.replace('__POSITIONS__',repr(sorted(positions.items())))
script=script.replace(old,old+hover,1)
script=script.replace('len(checks)==96','len(checks)==100').replace('result["formal_assets"]=58','result["formal_assets"]=66').replace('PASS_WORLD_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI','PASS_SMALL_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI').replace('58種正式素材，96組五語GUI、36份來源懸停與九個邊界／恢復','66種正式素材，100組五語GUI、60份來源懸停與九個邊界／恢復')
old='        result["formal_assets"]=66';assert script.count(old)==1
script=script.replace(old,old+'\n        result["formal_small_terrain_sources"]=8\n        result["small_terrain_hovers"]=small_hovers\n        need(len(small_hovers)==24,"8x8懸停數不同")',1)
world_sets={ast.get_source_segment(script,node) for node in ast.walk(ast.parse(script)) if isinstance(node,ast.Set) and any(isinstance(item,ast.Constant) and item.value=='world' for item in node.elts)}
assert world_sets
for segment in world_sets:script=script.replace(segment,segment.replace('"world"','"world","small-terrain-en","small-terrain-restored"',1))
lines=script.splitlines()
for i,line in enumerate(lines):
 if line.strip().startswith('if graphics == "original" or not ('):lines[i]=line[:-2]+' or hd.get("small_terrain",{}).get("painted")):'
 if line.strip().startswith('if c["graphics"] != "hd" or not ('):lines[i]=line[:-2]+' or c["native_live"].get("hd",{}).get("small_terrain",{}).get("painted")):'
script='\n'.join(lines)+'\n';compile(script,'small_terrain_formal_gui','exec');(out/'probe-gui.py').write_text(script)
run=(base/'run-gui.sh').read_text().replace('/out/formal-gui-r1',str(out));(out/'run-gui.sh').write_text(run)
result={'result':'PASS_SMALL_TERRAIN_FORMAL_READ_ONLY_GUI_BUILD','go_sources':len(list(module.glob('*.go'))),'source_bindings':binding,'source_build_sha256':sha(a.formal/'formal-build-r1.json'),'binary_sha256':sha(bundle/'bin/colonization-window'),'gui_script_sha256':sha(out/'probe-gui.py'),'hover_positions':positions,'production_connected':True}
assert result['go_sources']==54
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(result['result'],len(positions),flush=True)

