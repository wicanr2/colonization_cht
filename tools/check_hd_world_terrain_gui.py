"""規格067：獨立核對65份GUI的原版來源與36份英文懸停alpha像素。"""
import argparse,base64,hashlib,json,os
from collections import Counter
from pathlib import Path
from PIL import Image
import check_hd_terrain_ram_lifecycle as model

read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
need=model.need
def over(rgba,dst):
 a=rgba[3];premult=[(c*257*a//255)>>8 for c in rgba[:3]]
 return tuple((c*257+d*(255-a)*257//255)>>8 for c,d in zip(premult,dst[:3]))+(255,)

def check(gui,oracle,candidates,out,formal=False):
 repo=Path(__file__).resolve().parents[1];g=read(gui/'check.json');fixture=read(oracle/'fixture.json')
 need(g['result']==('PASS_WORLD_TERRAIN_FORMAL_FIVE_LANGUAGE_GUI' if formal else 'PASS_TWELVE_TERRAIN_PROTOTYPE_FIVE_LANGUAGE_GUI') and len(g['checks'])==96 and len(g['terrain_batch_hovers'])==36 and g['production_connected'] is formal,'正常GUI未完成')
 need(fixture['point_count']==65 and not fixture['diagnostic_only'] and fixture['gui_check_sha256']==sha(gui/'check.json'),'原版前綴未綁成功GUI')
 observed,control=oracle/'oracle/observed',oracle/'oracle/control';dest=out/'model';dest.mkdir()
 result=model.check(observed,control,repo/'workplace/reports/goal186-display-hd/hd-terrain-source-catalog-r46',dest,expected_points=65,all_ram=True)
 proof=read(observed/'draws.json');frames={};verified=Counter();cursor_pixels=0;original_pixels=0;pixel_snapshots=0
 for row in read(candidates)['sources']:
  path=candidates.parent/row['file'];need(sha(path)==row['sha256'],'候選PNG不同')
  with Image.open(path) as im:
   im=im.convert('RGBA');w,h=im.size;frames[row['ordinal']]=[im.getpixel(((2*x+1)*w//128,(2*y+1)*h//128)) for y in range(64) for x in range(64)]
 cursor_path=repo/'graphics/cursor-000.png';need(sha(cursor_path)=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4','正式游標PNG不同')
 with Image.open(cursor_path) as im:cursor_art=im.convert('RGBA')
 pairs=read(dest/'cursor-pairs.json');counts_by_source=Counter()
 for i,row in enumerate(fixture['points']):
  directory=gui/'terrain079'/row['label'];d=read(directory/'check.json');state=d['state'];p=proof['checkpoints'][i]
  for key in ['memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags','cycles']:need(state[key]==p[key],'GUI與原版狀態不同：'+row['label']+'/'+key)
  need(state['step']==p['steps'] and state['dos_input_count']==p['dos_input_count'],'GUI步數或輸入數不同')
  expected={int(k):{'ordinal':v['ordinal'],'local':v['local'],'native':v['native']} for k,v in read(dest/f'point-{i:03d}.terrain-model.json').items() if v['ordinal'] in frames}
  cells={int(k):v for k,v in d['batch_cells'].items()};need(cells==expected,'GUI來源身分不同：'+row['label'])
  counts=Counter(p['cell']['ordinal'] for p in pairs if p['step']<=row['step'] and p['cell']['ordinal'] in frames)
  need({str(k):v for k,v in counts.items()}==d['terrain_batch']['owned_cursor_restores_by_ordinal'],'GUI與原版游標RAM配對計數不同')
  counts_by_source=counts
  indexed=(directory/'indexed').read_bytes();canvas=(directory/'canvas').read_bytes();palette=(directory/'palette').read_bytes();cursor=(directory/'cursor-source').read_bytes()
  need(sha(directory/'memory')==p['memory_sha256'] and hashlib.sha256(indexed).hexdigest()==p['indexed_sha256'] and hashlib.sha256(palette).hexdigest()==p['palette_sha256'],'實際快照指紋不同')
  with Image.open(directory/'display.png') as im:actual=im.convert('RGBA')
  need(actual.size==(1280,800),'顯示畫布不同')
  color=lambda v:tuple((c<<2)|(c>>4) for c in palette[v*3:v*3+3])+(255,)
  if row['label']=='terrain079-quit-original':
   native=Image.frombytes('P',(320,200),indexed);native.putpalette([(c<<2)|(c>>4) for c in palette]);native=native.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST)
   need(actual.tobytes()==native.tobytes(),'原版模式出現HD像素');original_pixels+=1280*800
  if not row['label'].startswith('terrain-batch-'):continue
  live=d['frame']['native_live'];hd=live.get('hd') or {};group=hd.get('terrain_batch') or {};need(live['locale']=='en' and group.get('prototype') is (not formal) and group.get('formal') is formal,'英文懸停沒有預期顯示層')
  mouse=state['dos_mouse'];cursor_cells={}
  for k,v in enumerate(cursor):
   x,y=mouse['x']+k%16,mouse['y']+k//16
   if v!=255 and 0<=x<320 and 0<=y<200:cursor_cells[y*320+x]=k
  mask=bytearray(8000);painted=Counter()
  for pos,cell in cells.items():
   if canvas[pos]!=cell['native']:continue
   n,k=cell['ordinal'],cell['local'];art=frames[n];sx,sy=k%16*4,k//16*4
   need(any(art[(sy+dy)*64+sx+dx][3]>0 for dy in range(4) for dx in range(4)),'來源格沒有生成alpha')
   painted[n]+=1;mask[pos>>3]|=1<<(pos&7)
   if pos in cursor_cells:continue
   for dy in range(4):
    for dx in range(4):
     xy=(pos%320*4+dx,pos//320*4+dy);expected=over(art[(sy+dy)*64+sx+dx],color(cell['native']))
     need(actual.getpixel(xy)==expected,'GUI地形alpha不同：'+row['label']+'/'+str(n)+'/'+str(xy));verified[n]+=1
  need(base64.b64decode(group['mask'],validate=True)==bytes(mask) and group['painted']==group['valid']==sum(painted.values()),'GUI來源遮罩不同')
  need({int(k):v for k,v in group['by_ordinal'].items()}==dict(painted),'GUI逐來源實繪數不同')
  for pos,k in cursor_cells.items():
   for dy in range(4):
    for dx in range(4):
     sx,sy=k%16*4+dx,k//16*4+dy;rgba=cursor_art.getpixel((106+(2*sx+1)*615//80,188+(2*sy+1)*859//112));xy=(pos%320*4+dx,pos//320*4+dy)
     need(actual.getpixel(xy)==over(rgba,color(indexed[pos])),'GUI游標被地形蓋住：'+row['label']);cursor_pixels+=1
  pixel_snapshots+=1
 need(pixel_snapshots==36 and set(verified)==set(frames),'十二來源懸停像素沒有完整驗證')
 report={'result':'PASS_TWELVE_TERRAIN_65_GUI_ORIGINAL_MODELS_AND_36_HOVER_RGBA','production_connected':False,'checkpoints':65,'gui_checks':96,'hover_snapshots':36,'verified_terrain_rgba_pixels':sum(verified.values()),'verified_terrain_rgba_by_ordinal':dict(verified),'verified_cursor_rgba_pixels':cursor_pixels,'verified_original_mode_pixels':original_pixels,'source_calls':result['source_calls'],'raw_events':result['raw_events'],'stage_main_transfers':result['verified_stage_main_transfers'],'ram_saves':result['ram_saves_verified'],'ram_restores':result['ram_restorations_accepted'],'cursor_restores':len(pairs),'cursor_restores_by_ordinal':dict(counts_by_source),'gui_check_sha256':sha(gui/'check.json'),'fixture_sha256':sha(oracle/'fixture.json'),'checker_sha256':sha(Path(__file__)),'model_checker_sha256':sha(Path(model.__file__)),'full_hd_complete':False}
 if formal:report.update(result='PASS_WORLD_TERRAIN_FORMAL_65_GUI_ORIGINAL_MODELS_AND_36_HOVER_RGBA',production_connected=True)
 (out/'check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['gui','oracle','candidates','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--formal',action='store_true')
 a=p.parse_args();out=a.output.resolve();need(Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists(),'需新非root輸出');out.mkdir()
 result=check(a.gui,a.oracle,a.candidates,out,a.formal);print(result['result'],result['verified_terrain_rgba_pixels'],flush=True)
if __name__=='__main__':main()
