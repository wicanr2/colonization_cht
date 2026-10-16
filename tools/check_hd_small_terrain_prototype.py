"""規格068：獨立核對八來源、65點原版模型與原PNG合成。"""
import argparse,base64,hashlib,json,os
from collections import Counter
from pathlib import Path
from PIL import Image

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def need(value,message):
 if not value:raise ValueError(message)

TARGETS={112,113,116,119,126,127,136,139}

def check(native,candidates,model,report,out,formal=False):
 d=read(native/'check.json');source=read(report);arts=read(candidates)
 need(d['result']==('PASS_SMALL_TERRAIN_FORMAL_NATIVE_65' if formal else 'PASS_SMALL_TERRAIN_PROTOTYPE_NATIVE_65') and d['original_state_and_saves_equal'] and d['production_connected'] is formal,'同狀態重播未通過')
 need(len(d['points'])==65 and d['accepted_calls']==57 and d['dos_inputs']==143 and d['end']==251625001 and len(d['negatives'])==72,'原型範圍不同')
 need(d['ram_saves']==697 and d['ram_restores']==474 and d['owned_cursor_restores']==56,'RAM或游標配對數不同')
 frames={};coverage={};verified=Counter();visible_points=Counter();missing=Counter();outside_verified=0
 for row in arts['sources']:
  n=row['ordinal'];path=candidates.parent/row['file'];need(sha(path)==row['sha256'],'候選指紋不同')
  with Image.open(path) as im:
   im=im.convert('RGBA');w,h=im.size;need([w,h]==row['size'],'候選尺寸不同')
   frames[n]=[im.getpixel(((2*x+1)*w//64,(2*y+1)*h//64)) for y in range(32) for x in range(32)]
 need(set(frames)==TARGETS,'候選來源不齊')
 calls=Counter(c['ordinal'] for c in d['calls']);need(calls==Counter({int(n):r['draw_calls'] for n,r in source['sources'].items() if int(n) in TARGETS}),'逐來源呼叫數不同')
 for call in d['calls']:
  row=source['sources'][str(call['ordinal'])]
  need(call['source_sha256']==row['encoded_sha256'] and call['writes_sha256']==row['sorted_local_offset_value_sha256'] and call['record_far']==row['record_far'] and call['source_far']==row['source_far'],'原生來源定位或逐寫不同')
 pairs=[p for p in read(model/'cursor-pairs.json') if p['cell']['ordinal'] in frames]
 need(len(pairs)==len(d['cursor_pairs'])==56,'游標正向配對不齊')
 for actual,expected in zip(d['cursor_pairs'],pairs):
  need((actual['ordinal'],actual['step'],actual['linear'],actual['local'],actual['native'],actual['source_cursor_index'])==(expected['cell']['ordinal'],expected['step'],0x2cae0+expected['offset'],expected['cell']['local'],expected['cell']['native'],expected['cursor']),'游標反向配對不同')
 for index,point in enumerate(d['points']):
  oracle={int(k):v for k,v in read(model/f'point-{index:03d}.terrain-model.json').items() if v['ordinal'] in frames}
  cells={int(k):v for k,v in point['small_terrain_cells'].items()};need(cells=={k:{'ordinal':v['ordinal'],'local':v['local'],'native':v['native']} for k,v in oracle.items()},'原型來源身分不同')
  with Image.open(native/f'point-{index:03d}.png') as im:actual=im.convert('RGBA')
  with Image.open(native/f'point-{index:03d}.baseline.png') as im:baseline=im.convert('RGBA')
  need(actual.size==baseline.size==(1280,800),'畫布尺寸不同')
  expected=baseline.copy();painted=Counter();valid=Counter();mask=bytearray(8000);preserved_zero=0
  palette=(native/f'point-{index:03d}.palette').read_bytes()
  cursor=(native/f'point-{index:03d}.cursor').read_bytes();mouse=point['dos_mouse'];cursor_cells=set()
  for k,v in enumerate(cursor):
   x,y=mouse['x']+k%16,mouse['y']+k//16
   if v!=255 and 0<=x<320 and 0<=y<200:cursor_cells.add(y*320+x)
  for pos,cell in cells.items():
   n,k=cell['ordinal'],cell['local'];sx,sy=k%8*4,k//8*4;art=frames[n];valid[n]+=1
   active=cell['native']==0 or any(art[(sy+dy)*32+sx+dx][3]>0 for dy in range(4) for dx in range(4))
   if not active:missing[n]+=1;continue
   painted[n]+=1;mask[pos>>3]|=1<<(pos&7)
   preserved_zero+=cell['native']==0
   if pos in cursor_cells:continue
   for dy in range(4):
    for dx in range(4):
     xy=(pos%320*4+dx,pos//320*4+dy);r,g,b,a=art[(sy+dy)*32+sx+dx];dst=baseline.getpixel(xy)
     premult=[(c*257*a//255)>>8 for c in [r,g,b]]
     color=tuple((c*257+v*(255-a)*257//255)>>8 for c,v in zip(premult,dst[:3]))+(255,)
     if cell['native']==0:color=tuple((c<<2)|(c>>4) for c in palette[:3])+(255,)
     expected.putpixel(xy,color);verified[n]+=1
  record=point.get('small_terrain')
  need(record is not None and record['prototype'] is (not formal) and record['formal'] is formal,'不是預期的八來源顯示層')
  need(record['preserved_native_zero']==preserved_zero and record['generated_painted']+preserved_zero==record['painted'],'原版索引0保留數不同')
  need(record['valid']==sum(valid.values()) and record['painted']==sum(painted.values()),'有效與實繪來源數不同')
  need({int(k):v for k,v in record['by_ordinal'].items()}==dict(painted),'逐來源實繪數不同')
  need(base64.b64decode(record['mask'],validate=True)==bytes(mask),'實繪遮罩不同')
  need(actual.tobytes()==expected.tobytes(),'原alpha、遮擋或來源範圍外像素不同：'+str(index))
  visible_points.update(painted.keys());outside_verified+=1280*800-sum(painted.values())*16
 result={'result':'PASS_SMALL_TERRAIN_PROTOTYPE_NATIVE_MODEL_AND_RGBA','production_connected':False,'checkpoints':65,'native_negatives':72,'source_calls':57,'ram_saves':697,'ram_restores':474,'owned_cursor_restores':56,'verified_rgba_pixels':sum(verified.values()),'verified_rgba_by_ordinal':dict(verified),'visible_points_by_ordinal':dict(visible_points),'missing_alpha_cell_occurrences':dict(missing),'source_outside_pixels_verified':outside_verified,'original_state_and_saves_equal':True,'native_check_sha256':sha(native/'check.json'),'candidate_index_sha256':sha(candidates),'checker_sha256':sha(Path(__file__)),'full_hd_complete':False}
 if formal:result.update(result='PASS_SMALL_TERRAIN_FORMAL_NATIVE_MODEL_AND_RGBA',production_connected=True)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['native','candidates','model','source-report','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--formal',action='store_true')
 a=p.parse_args();out=a.output.resolve();need(Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists(),'需新的非root本機輸出')
 result=check(a.native,a.candidates,a.model,a.source_report,out,a.formal);print(result['result'],result['verified_rgba_pixels'],flush=True)
if __name__=='__main__':main()
