"""規格067：從真實GUI的65份快照建立獨立原版觀測／控制收據。"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for n in ['gui','output']:p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--run',action='store_true',help='同批組裝並執行原版觀測／控制，不安裝HD')
p.add_argument('--formal',action='store_true',help='綁定正式十二來源GUI；原版執行仍不安裝HD')
p.add_argument('--diagnostic',action='store_true',help='只診斷未通過GUI的已保存快照，不授予GUI完成信用')
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=a.gui/'gui.inputs.json'
if a.diagnostic:
 assert not (a.gui/'check.json').exists() and inputs.is_file()
else:
 gui=read(a.gui/'check.json');assert gui['result']==('PASS_WORLD_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI' if a.formal else 'PASS_TWELVE_TERRAIN_PROTOTYPE_FIVE_LANGUAGE_GUI') and len(gui['checks'])==96 and len(gui['terrain_batch_hovers'])==36 and gui['production_connected'] is a.formal
 assert sha(inputs)==gui['gui_inputs_sha256']
rows=[]
for directory in (a.gui/'terrain079').iterdir():
 if not directory.is_dir():continue
 path=directory/'check.json';d=read(path);state=d['state'];assert state['dos_mouse']['buttons']==0
 # 此欄沿第079來源；十二來源及整批GUI的正式狀態另由formal參數與收據驗證。
 assert d['formal'] is True
 if directory.name not in {'terrain079-saved-world','terrain079-quit-original'}:assert d['terrain079']['painted']>0
 rows.append((state['step'],state['dos_input_count'],directory.name,state,sha(path)))
point_count=len(rows);assert (0<point_count<65 if a.diagnostic else point_count==65);rows.sort();assert len({r[:2] for r in rows})==point_count
full=read(inputs);end,count=rows[-1][:2];prefix=full['inputs'][:count]
assert len(prefix)==count and all(e['step']<=end for e in prefix) and (len(full['inputs'])==count or full['inputs'][count]['step']>=end)
out.mkdir();input_path=out/'inputs.json';point_path=out/'points.json';input_path.write_text(json.dumps({'inputs':prefix,'end':end},indent=2)+'\n');point_path.write_text(json.dumps([r[3] for r in rows],indent=2)+'\n')
fixture={'kind':'unchanged-actual-GUI-input-prefix','diagnostic_only':a.diagnostic,'gui_check_sha256':None if a.diagnostic else sha(a.gui/'check.json'),'actual_inputs_sha256':sha(inputs),'prefix_sha256':sha(input_path),'points_sha256':sha(point_path),'end':end,'dos_inputs':count,'point_count':point_count,'points':[{'label':r[2],'step':r[0],'count':r[1],'receipt_sha256':r[4]} for r in rows],'production_connected':False}
fixture['production_connected']=a.formal
(out/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
script=(repo/'tools/build_hd_terrain_ram_lifecycle_probe.py').read_text().replace('repo=Path(__file__).resolve().parents[1]','repo=Path("/repo")')
anchor='s=base.read_text()';assert script.count(anchor)==1
addition='''
fixture=json.loads(Path(__file__).with_name('fixture.json').read_bytes())
assert sha(a.inputs.read_bytes())==fixture['prefix_sha256'] and sha(a.points.read_bytes())==fixture['points_sha256']
s=s.replace('3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca',fixture['prefix_sha256'])
s=s.replace('821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901',fixture['points_sha256'])
s=s.replace('len(points) != 49','len(points) != '+str(fixture['point_count'])).replace('end = 134600000','end = '+str(fixture['end']))
'''
script=script.replace(anchor,anchor+addition,1)
for old,new in [
 ("assert sha(a.points.read_bytes())=='821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901'","assert sha(a.points.read_bytes())==fixture['points_sha256']"),
 ("assert sha(a.inputs.read_bytes())=='3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca'","assert sha(a.inputs.read_bytes())==fixture['prefix_sha256']"),
]:assert script.count(old)==1;script=script.replace(old,new,1)
compile(script,'terrain_batch_raw_collector','exec');builder=out/'build-collector.py';builder.write_text(script)
if a.run:
 module=out/'oracle';sources=repo/'workplace/reports/goal186-display-hd/hd-terrain-source-catalog-r46'
 subprocess.run(['python3',str(builder),'--sources',str(sources),'--inputs',str(input_path),'--points',str(point_path),'--output',str(module),'--reference',str(repo/'workplace/reports/goal186-display-hd/hd-building-nine-formal-r43/runtime-r1')],check=True,timeout=240)
 seed=repo/'workplace/reports/goal186-display-hd/hd-building032-draw-boundary-20261012/lifecycle-r29-r1/gui/save/COLONY09.SAV'
 common=[str(module/'terrain-probe'),'--root','/game','--seed',str(seed),'--inputs',str(input_path),'--sources',str(sources),'--lifecycle-points',str(point_path)]
 for name,extra in [('observed',[]),('control',['--control'])]:
  with (module/(name+'.log')).open('wb') as log:subprocess.run(common+['--out',str(module/name)]+extra,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
  print('PASS_TERRAIN_BATCH_GUI_ORIGINAL_RAW_RUN',name,flush=True)
 assert (module/'observed/final.memory').read_bytes()==(module/'control/final.memory').read_bytes()
 names={p.name for p in (module/'observed/saves').glob('*.SAV')}
 assert names=={p.name for p in (module/'control/saves').glob('*.SAV')} and 'COLONY09.SAV' in names
 if not a.diagnostic:assert 'COLONY00.SAV' in names
 for name in names:assert (module/'observed/saves'/name).read_bytes()==(module/'control/saves'/name).read_bytes()
print('PASS_TERRAIN_BATCH_ACTUAL_GUI_DIAGNOSTIC_FIXTURE' if a.diagnostic else 'PASS_TERRAIN_BATCH_ACTUAL_GUI_FIXTURE',point_count,count,end,flush=True)
