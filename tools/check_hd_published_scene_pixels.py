"""規格069 R79：核對正常五語讀檔GUI的已發布背景、原版前景、游標與X11實拍。"""
from pathlib import Path
from PIL import Image
import argparse,base64,hashlib,json,os
parser=argparse.ArgumentParser(description=__doc__)
for name in ['gui','model','probe','output']:parser.add_argument('--'+name,type=Path,required=True)
a=parser.parse_args()
assert Path('/.dockerenv').exists() and os.getuid()!=0
assert not a.output.exists() and a.output.parent.stat().st_uid==os.getuid()
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
cap=read(a.gui/'capture.json');model=read(a.model/'check.json')
assert cap['result']=='PASS_PUBLISHED_SCENE_FORMAL_FIVE_LANGUAGE_GUI' and len(cap['samples'])==32
assert model['scope']=='published-load' and model['native_state_points_equal_control']==32
points=model['published_surface']['points'];assert len(points)==32
art_path=Path('/repo/graphics/woodpanl-000.png')
assert sha(art_path)=='20a9e807bb330501e83565704a039134e4344a7550208c8813533ceb422d19d2'
# Use the renderer's integer centre mapping explicitly.
source=Image.open(art_path).convert('RGBA');art=Image.new('RGBA',(1280,800))
sp=source.load();ap=art.load()
for y in range(800):
 sy=(2*y+1)*source.height//1600
 for x in range(1280):ap[x,y]=sp[(2*x+1)*source.width//2560,sy]
artbytes=art.tobytes();counts={'hd_source_rgba':0,'native_foreground_rgba':0,'original_mode_rgba':0,'opaque_cursor_rgba':0,'x11_rgba':0}
rows=[]
coverage=set()
for i,(sample,point) in enumerate(zip(cap['samples'],points)):
 st=sample['state'];stem='point-%03d'%i
 assert sample['label']==point['label'] and st['step']==point['step']
 memory=(a.probe/'control'/(stem+'.memory')).read_bytes()
 idx=(a.probe/'control'/(stem+'.idx')).read_bytes();pal=(a.probe/'control'/(stem+'.palette')).read_bytes()
 assert hashlib.sha256(memory).hexdigest()==st['memory_sha256']
 assert hashlib.sha256(idx).hexdigest()==st['indexed_sha256']
 assert hashlib.sha256(pal).hexdigest()==st['palette_sha256']
 assert memory[0xa0000:0xa0000+64000]==idx
 native=Image.frombytes('P',(320,200),idx);native.putpalette([v<<2|v>>4 for v in pal])
 native=native.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST).tobytes()
 shown=Image.open(sample['image']).convert('RGBA');assert shown.size==(1280,800)
 pixels=shown.tobytes();x11=Image.open(sample['x11']).convert('RGBA').crop((0,48,1280,848)).tobytes()
 assert x11==pixels,('X11 crop',sample['label']);counts['x11_rgba']+=1280*800
 safe=set()
 for item in sample['native_live'].get('items') or []:
  rect=item['safe'];lo,hi=rect['Min'],rect['Max']
  assert 0<=lo['X']<hi['X']<=320 and 0<=lo['Y']<hi['Y']<=200
  safe.update(y*320+x for y in range(lo['Y'],hi['Y']) for x in range(lo['X'],hi['X']))
 mask=bytes(64000);cells={}
 if sample['graphics']=='hd':
  group=sample['native_live']['hd']['published_scene_picture']
  assert group['formal'] and group['surface']=='published-vga' and group['painted']>0
  mask=(a.model/(stem+'-published-1551-mask.bin')).read_bytes()
  packed=base64.b64decode(group['sources']['1551']['mask'])
  assert len(packed)==8000 and mask==bytes((packed[k>>3]>>(k&7))&1 for k in range(64000))
  assert group['painted']==sum(mask)==group['sources']['1551']['painted']
  assert all(v['painted']==0 for k,v in group['sources'].items() if k!='1551')
  cells=read(a.model/(stem+'.published.json'))
  coverage.add((sample['scene_label'],sample['locale'],sample['graphics']))
 elif sample['scene_label']:
  coverage.add((sample['scene_label'],sample['locale'],sample['graphics']))
 local=0
 for pos,hd in enumerate(mask):
  if pos in safe:continue
  expected_pos=pos
  category='original_mode_rgba' if sample['graphics']=='original' else 'native_foreground_rgba'
  expected=native
  if hd:
   cell=cells[str(pos)];assert cell[0]==1551 and cell[3]=='background' and cell[2]==idx[pos]
   expected_pos=cell[1];expected=artbytes;category='hd_source_rgba';local+=16
  for dy in range(4):
   at=((pos//320*4+dy)*1280+pos%320*4)*4
   source_at=((expected_pos//320*4+dy)*1280+expected_pos%320*4)*4
   assert pixels[at:at+16]==expected[source_at:source_at+16],(sample['label'],pos,dy,category)
   counts[category]+=4
 mouse=st['dos_mouse'];mx,my=mouse['x'],mouse['y'];cursor=memory[0x1cd74:0x1ce74]
 assert hashlib.sha256(cursor).hexdigest()=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 for k,v in enumerate(cursor):
  if v==255:continue
  x,y=mx+k%16,my+k//16
  if not(0<=x<320 and 0<=y<200):continue
  for dy in range(4):
   at=((y*4+dy)*1280+x*4)*4
   assert pixels[at:at+16]==native[at:at+16],('native cursor',sample['label'],k)
   counts['opaque_cursor_rgba']+=4
 rows.append({'label':sample['label'],'step':st['step'],'source_cells':sum(mask),'verified_hd_rgba':local,'excluded_text_cells':len(safe)})
required={(view,locale,graphics) for view in ['load-menu','load-slot'] for locale in ['en','zh-Hant','zh-Hans','ja','ko'] for graphics in ['original','hd']}
assert required<=coverage
result={'result':'PASS_PUBLISHED_SCENE_FORMAL_GUI_PIXELS','samples':len(rows),'hd_samples':sum(s['graphics']=='hd' for s in cap['samples']),'original_samples':sum(s['graphics']=='original' for s in cap['samples']),'counts':counts,'points':rows,'capture_sha256':sha(a.gui/'capture.json'),'model_sha256':sha(a.model/'check.json'),'asset_sha256':sha(art_path),'tool_sha256':sha(Path(__file__)),'all_five_languages_both_views_and_modes':True,'scope':'Published load menu/list backgrounds; original foreground and cursor preserved; no animation credit'}
a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result['result'],result['samples'],counts)
