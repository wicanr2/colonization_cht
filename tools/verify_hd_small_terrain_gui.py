"""規格068：從100組正式GUI重生89點原版收據，獨立核對八來源與24份懸停。"""
import argparse,base64,hashlib,json,os,subprocess
from collections import Counter
from pathlib import Path
import hd_small_terrain_source_model as support
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def oracle(a,out):
 gui=read(a.gui/'check.json');need(gui['result']=='PASS_SMALL_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI' and len(gui['checks'])==100 and len(gui['small_terrain_hovers'])==24 and len(gui['terrain_batch_hovers'])==36 and gui['production_connected'],'正式GUI未完成')
 inputs=a.gui/'gui.inputs.json';need(sha(inputs)==gui['gui_inputs_sha256'],'實際輸入不同');rows=[]
 for directory in (a.gui/'terrain079').iterdir():
  if not directory.is_dir():continue
  d=read(directory/'check.json');state=d['state'];need(state['dos_mouse']['buttons']==0,'快照未放開滑鼠');rows.append((state['step'],state['dos_input_count'],directory.name,state,sha(directory/'check.json')))
 rows.sort();need(len(rows)==89 and len({r[:2] for r in rows})==89,'快照數或唯一性不同')
 data=read(inputs);end,count=rows[-1][:2];prefix=data['inputs'][:count];need(len(prefix)==count and all(e['step']<=end for e in prefix) and (len(data['inputs'])==count or data['inputs'][count]['step']>=end),'前綴不同')
 (out/'inputs.json').write_text(json.dumps({'inputs':prefix,'end':end},indent=2)+'\n');(out/'points.json').write_text(json.dumps([r[3] for r in rows],indent=2)+'\n')
 fixture={'kind':'unchanged-actual-formal-GUI-prefix','gui_check_sha256':sha(a.gui/'check.json'),'actual_inputs_sha256':sha(inputs),'prefix_sha256':sha(out/'inputs.json'),'points_sha256':sha(out/'points.json'),'end':end,'dos_inputs':count,'point_count':89,'points':[{'label':r[2],'step':r[0],'count':r[1],'receipt_sha256':r[4]} for r in rows]}
 (out/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n');builder=out/'build-collector.py';support.raw_builder(builder)
 if a.run:
  repo=support.REPO;sources=repo/'workplace/reports/goal186-display-hd/hd-terrain-source-catalog-r46';module=out/'oracle'
  subprocess.run(['python3',str(builder),'--sources',str(sources),'--inputs',str(out/'inputs.json'),'--points',str(out/'points.json'),'--reference',str(repo/'workplace/reports/goal186-display-hd/hd-building-nine-formal-r43/runtime-r1'),'--output',str(module)],check=True,timeout=240)
  seed=repo/'workplace/reports/goal186-display-hd/hd-building032-draw-boundary-20261012/lifecycle-r29-r1/gui/save/COLONY09.SAV'
  cmd=[str(module/'terrain-probe'),'--root','/game','--seed',str(seed),'--inputs',str(out/'inputs.json'),'--sources',str(sources),'--lifecycle-points',str(out/'points.json')]
  for name,flags in [('observed',[]),('control',['--control'])]:
   with (module/(name+'.log')).open('wb') as log:subprocess.run(cmd+['--out',str(module/name)]+flags,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
   print('PASS_SMALL_TERRAIN_GUI_ORIGINAL_RUN',name,flush=True)
  need((module/'observed/final.memory').read_bytes()==(module/'control/final.memory').read_bytes(),'原版終點不同')
 print('PASS_SMALL_TERRAIN_ACTUAL_GUI_FIXTURE',89,count,end,flush=True)
def over(rgba,dst):
 a=rgba[3];premult=[(c*257*a//255)>>8 for c in rgba[:3]]
 return tuple((c*257+d*(255-a)*257//255)>>8 for c,d in zip(premult,dst[:3]))+(255,)
def check(a,out):
 from PIL import Image
 g=read(a.gui/'check.json');fixture=read(a.oracle/'fixture.json')
 need(g['result']=='PASS_SMALL_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI' and len(g['checks'])==100 and len(g['small_terrain_hovers'])==24,'正式GUI未完成')
 need(fixture['point_count']==89 and fixture['gui_check_sha256']==sha(a.gui/'check.json'),'原版前綴不同')
 model_path=out/'native-model.py';model=support.native_model(model_path);dest=out/'model';dest.mkdir()
 observed,control=a.oracle/'oracle/observed',a.oracle/'oracle/control';result=model.check(observed,control,support.REPO/'workplace/reports/goal186-display-hd/hd-terrain-source-catalog-r46',dest,expected_points=89,all_ram=True)
 proof=read(observed/'draws.json');frames={};verified=Counter();cursor_pixels=original_pixels=snapshots=zero_cells=0
 for row in read(a.candidates)['sources']:
  path=a.candidates.parent/row['file'];need(sha(path)==row['sha256'],'生成PNG不同')
  with Image.open(path) as im:
   im=im.convert('RGBA');w,h=im.size;frames[row['ordinal']]=[im.getpixel(((2*x+1)*w//64,(2*y+1)*h//64)) for y in range(32) for x in range(32)]
 need(set(frames)==support.TARGETS,'候選缺漏');cursor_path=support.REPO/'graphics/cursor-000.png';need(sha(cursor_path)=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4','一般游標不同')
 with Image.open(cursor_path) as im:cursor_art=im.convert('RGBA')
 pairs=read(dest/'cursor-pairs.json');counts_by_source=Counter()
 for i,row in enumerate(fixture['points']):
  directory=a.gui/'terrain079'/row['label'];d=read(directory/'check.json');state=d['state'];p=proof['checkpoints'][i]
  for key in ['memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags','cycles']:need(state[key]==p[key],'GUI與原版不同：'+row['label']+'/'+key)
  need(state['step']==p['steps'] and state['dos_input_count']==p['dos_input_count'],'GUI步數或輸入數不同')
  expected={int(k):{'ordinal':v['ordinal'],'local':v['local'],'native':v['native']} for k,v in read(dest/f'point-{i:03d}.terrain-model.json').items() if v['ordinal'] in frames};cells={int(k):v for k,v in d['small_cells'].items()};need(cells==expected,'8x8來源不同')
  counts=Counter(p['cell']['ordinal'] for p in pairs if p['step']<=row['step'] and p['cell']['ordinal'] in frames);need({str(k):v for k,v in counts.items()}==d['small_terrain']['owned_cursor_restores_by_ordinal'],'游標原版事件不同');counts_by_source=counts
  indexed=(directory/'indexed').read_bytes();canvas=(directory/'canvas').read_bytes();palette=(directory/'palette').read_bytes();cursor=(directory/'cursor-source').read_bytes()
  need(sha(directory/'memory')==p['memory_sha256'] and hashlib.sha256(indexed).hexdigest()==p['indexed_sha256'] and hashlib.sha256(palette).hexdigest()==p['palette_sha256'],'快照指紋不同')
  with Image.open(directory/'display.png') as im:actual=im.convert('RGBA')
  color=lambda v:tuple((c<<2)|(c>>4) for c in palette[v*3:v*3+3])+(255,)
  if row['label']=='terrain079-quit-original':
   native=Image.frombytes('P',(320,200),indexed);native.putpalette([(c<<2)|(c>>4) for c in palette]);native=native.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST);need(actual.tobytes()==native.tobytes(),'原版模式有HD');original_pixels+=1280*800
  if not row['label'].startswith('small-terrain-'):continue
  live=d['frame']['native_live'];group=(live.get('hd') or {}).get('small_terrain') or {};need(live['locale']=='en' and group.get('formal') and not group.get('prototype'),'英文來源未正式生效')
  mouse=state['dos_mouse'];cursor_cells={}
  for k,v in enumerate(cursor):
   x,y=mouse['x']+k%16,mouse['y']+k//16
   if v!=255 and 0<=x<320 and 0<=y<200:cursor_cells[y*320+x]=k
  mask=bytearray(8000);painted=Counter();zeros=0
  for pos,cell in cells.items():
   if canvas[pos]!=cell['native']:continue
   n,k=cell['ordinal'],cell['local'];art=frames[n];sx,sy=k%8*4,k//8*4
   need(cell['native']==0 or any(art[(sy+dy)*32+sx+dx][3]>0 for dy in range(4) for dx in range(4)),'彩色格缺alpha')
   painted[n]+=1;mask[pos>>3]|=1<<(pos&7);zeros+=cell['native']==0
   if pos in cursor_cells:continue
   for dy in range(4):
    for dx in range(4):
     xy=(pos%320*4+dx,pos//320*4+dy);expected=color(0) if cell['native']==0 else over(art[(sy+dy)*32+sx+dx],color(cell['native']));need(actual.getpixel(xy)==expected,'8x8合成不同：'+row['label']+'/'+str(n)+'/'+str(xy));verified[n]+=1
  need(base64.b64decode(group['mask'],validate=True)==bytes(mask) and group['painted']==group['valid']==sum(painted.values()),'8x8遮罩不同');need(group['preserved_native_zero']==zeros and group['generated_painted']+zeros==group['painted'],'零值保留不同')
  need({int(k):v for k,v in group['by_ordinal'].items()}==dict(painted),'逐來源實繪不同')
  for pos,k in cursor_cells.items():
   for dy in range(4):
    for dx in range(4):
     sx,sy=k%16*4+dx,k//16*4+dy;rgba=cursor_art.getpixel((106+(2*sx+1)*615//80,188+(2*sy+1)*859//112));xy=(pos%320*4+dx,pos//320*4+dy);need(actual.getpixel(xy)==over(rgba,color(indexed[pos])),'游標被8x8蓋住');cursor_pixels+=1
  snapshots+=1;zero_cells+=zeros
 need(snapshots==24 and set(verified)==support.TARGETS,'八來源懸停未完整')
 report={'result':'PASS_SMALL_TERRAIN_FORMAL_89_ORIGINAL_MODELS_AND_24_HOVER_RGBA','production_connected':True,'checkpoints':89,'gui_checks':100,'hover_snapshots':24,'verified_terrain_rgba_pixels':sum(verified.values()),'verified_terrain_rgba_by_ordinal':dict(verified),'verified_cursor_rgba_pixels':cursor_pixels,'verified_original_mode_pixels':original_pixels,'preserved_zero_cells':zero_cells,'cursor_restores_by_ordinal':dict(counts_by_source),'source_calls':result['source_calls'],'raw_events':result['raw_events'],'ram_saves':result['ram_saves_verified'],'ram_restores':result['ram_restorations_accepted'],'fixture_sha256':sha(a.oracle/'fixture.json'),'gui_check_sha256':sha(a.gui/'check.json'),'checker_sha256':sha(Path(__file__)),'model_checker_sha256':sha(model_path),'model_factory_sha256':sha(Path(support.__file__)),'base_model_sha256':sha(support.REPO/'tools/check_hd_terrain_ram_lifecycle.py'),'full_hd_complete':False}
 (out/'check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report['result'],report['verified_terrain_rgba_pixels'],flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['oracle','check'])
 for n in ['gui','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--run',action='store_true');p.add_argument('--oracle',type=Path);p.add_argument('--candidates',type=Path)
 a=p.parse_args();out=a.output.resolve();need(Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists(),'需新的非root輸出');out.mkdir()
 if a.action=='oracle':oracle(a,out)
 else:need(a.oracle and a.candidates,'缺審查輸入');check(a,out)
if __name__=='__main__':main()

