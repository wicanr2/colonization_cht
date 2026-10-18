"""規格069 R79：核對正常五語讀檔GUI的已發布背景、原版前景、游標與X11實拍。"""
from pathlib import Path
from PIL import Image
import argparse,base64,hashlib,json,os
parser=argparse.ArgumentParser(description=__doc__)
for name in ['gui','model','probe','output']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--text-cursor',action='store_true',help='規格069 R80：另驗已發布字底與HD游標；省略時保留R79原版游標驗收')
parser.add_argument('--texture-model',type=Path,help='規格069 R81：九項代表性GUI的三底紋獨立來源模型；須搭配text-cursor')
a=parser.parse_args()
assert not a.texture_model or a.text_cursor
expected_samples=9 if a.texture_model else 32
assert Path('/.dockerenv').exists() and os.getuid()!=0
assert not a.output.exists() and a.output.parent.stat().st_uid==os.getuid()
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
cap=read(a.gui/'capture.json');model=read(a.model/'check.json')
assert cap['result']==('PASS_PUBLISHED_TEXTURE_FORMAL_REPRESENTATIVE_GUI' if a.texture_model else 'PASS_PUBLISHED_TEXT_CURSOR_FORMAL_FIVE_LANGUAGE_GUI' if a.text_cursor else 'PASS_PUBLISHED_SCENE_FORMAL_FIVE_LANGUAGE_GUI') and len(cap['samples'])==expected_samples
assert model['scope']=='published-load' and model['native_state_points_equal_control']==expected_samples
points=model['published_surface']['points'];assert len(points)==expected_samples
art_path=Path('/repo/graphics/woodpanl-000.png')
assert sha(art_path)=='20a9e807bb330501e83565704a039134e4344a7550208c8813533ceb422d19d2'
# Use the renderer's integer centre mapping explicitly.
source=Image.open(art_path).convert('RGBA');art=Image.new('RGBA',(1280,800))
sp=source.load();ap=art.load()
for y in range(800):
 sy=(2*y+1)*source.height//1600
 for x in range(1280):ap[x,y]=sp[(2*x+1)*source.width//2560,sy]
texture_art={};texture_underlays=0;texture_rgba=0
if a.texture_model:
 texture_model=read(a.texture_model/'check.json')
 assert texture_model['result']=='PASS_PUBLISHED_TEXTURE_SOURCE_MODEL_RESEARCH' and texture_model['native_state_points_equal_control']==expected_samples
 for rid,name,want in [(1265,'opentile-000.png','cb2a8af8077d1e6fd0082d753e7cc0251192df0705ebe34496f1954f5cdc4547'),(1287,'parch-000.png','4ef702ede0e2d0a46ea94b54fdca602f01071a36a16a83dd57918b8fab15847e'),(1552,'woodtile-000.png','8580efcf85a45fa879938b5b73e8d54c58853dd9297e8ecd1f10801e637bb5d9')]:
  path=Path('/repo/graphics')/name;assert sha(path)==want
  raw=Image.open(path).convert('RGBA');assert raw.size==(1448,1086)
  canonical=Image.new('RGBA',(128,96))
  for y in range(96):
   for x in range(128):canonical.putpixel((x,y),raw.getpixel(((2*x+1)*1448//256,(2*y+1)*1086//192)))
  texture_art[rid]=canonical.tobytes()
cursor_art=None
if a.text_cursor:
 cursor_path=Path('/repo/graphics/cursor-000.png')
 assert sha(cursor_path)=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
 cursor_image=Image.open(cursor_path).convert('RGBA')
 assert cursor_image.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()==(106,188,721,1047)
 cursor_art=[[cursor_image.getpixel((106+(2*x+1)*615//80,188+(2*y+1)*859//112)) for x in range(40)] for y in range(56)]
 assert model['published_cursor']['sidecar_rows']>0 and model['published_cursor']['pending_peak']<=256
underlay_cells=0;native_cursor_underlay_cells=0;hd_cursor_pixels=0
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
 mouse=st['dos_mouse'];mx,my=mouse['x'],mouse['y'];cursor=memory[0x1cd74:0x1ce74]
 opaque={ (my+k//16)*320+mx+k%16 for k,v in enumerate(cursor) if v!=255 and 0<=mx+k%16<320 and 0<=my+k//16<200 }
 mask=bytes(64000);cells={}
 if sample['graphics']=='hd':
  hd_record=sample['native_live']['hd']
  published=bool(hd_record.get('published_scene_picture'))
  group=hd_record.get('published_scene_picture') or hd_record.get('scene_picture')
  assert group['formal'] and (a.text_cursor or group['surface']=='published-vga')
  assert group['sources']['1551']['painted']>0
  mask=(a.model/(stem+('-published-1551-mask.bin' if published else '-source-1551-mask.bin'))).read_bytes()
  packed=base64.b64decode(group['sources']['1551']['mask'])
  assert len(packed)==8000 and mask==bytes((packed[k>>3]>>(k&7))&1 for k in range(64000))
  assert sum(mask)==group['sources']['1551']['painted']
  if published:assert group['painted']==sum(mask)
  assert all(v['painted']==0 for k,v in group['sources'].items() if k!='1551')
  cells=read(a.model/(stem+('.published.json' if published else '.owners.json')))
  if a.text_cursor:
   backmask=base64.b64decode(group.get('background_mask',''),validate=True)
   assert len(backmask)==8000
   before_cells=read(a.model/(stem+('.published.json' if published else '.owners.json')))
   for pos in range(64000):
    if backmask[pos>>3]>>(pos&7)&1:
     assert pos in safe and str(pos) in before_cells
     c=before_cells[str(pos)];assert c[0]==1551 and c[2]==(idx[pos] if published else memory[0x2cae0+pos])
     underlay_cells+=1
   native_mask=base64.b64decode(hd_record['native_cursor_text_background_mask'],validate=True);assert len(native_mask)==8000
   for pos in range(64000):
    if native_mask[pos>>3]>>(pos&7)&1:
     assert pos in safe and mx<=pos%320<mx+16 and my<=pos//320<my+16 and cursor[(pos//320-my)*16+pos%320-mx]==255
     native_cursor_underlay_cells+=1
  coverage.add((sample['scene_label'],sample['locale'],sample['graphics']))
 elif sample['scene_label']:
  coverage.add((sample['scene_label'],sample['locale'],sample['graphics']))
 texture_cells={};texture_masks={}
 if a.texture_model and sample['graphics']=='hd':
  texture_cells=read(a.texture_model/(stem+'.published.json'))
  for rid,key in [(1265,'published_texture'),(1287,'published_parch'),(1552,'published_world_texture')]:
   texture=hd_record[key];assert texture['formal'] and not texture['prototype']
   tm=(a.texture_model/(stem+'-published-%d-mask.bin'%rid)).read_bytes();packed=base64.b64decode(texture['mask'])
   assert len(packed)==8000 and tm==bytes((packed[k>>3]>>(k&7))&1 for k in range(64000))
   assert texture['painted']==sum(tm)
   texture_masks[rid]=tm
   back=base64.b64decode(texture['background_mask']);assert len(back)==8000
   for pos in range(64000):
    if back[pos>>3]>>(pos&7)&1:
     c=texture_cells[str(pos)];assert pos in safe and c[0]==rid and c[2]==idx[pos]
     texture_underlays+=1
 local=0
 for pos,hd in enumerate(mask):
  if pos in safe or (a.text_cursor and pos in opaque):continue
  expected_pos=pos
  category='original_mode_rgba' if sample['graphics']=='original' else 'native_foreground_rgba'
  expected=native;source_width=320;is_texture=False
  if hd:
   cell=cells[str(pos)];assert cell[0]==1551 and cell[3]=='background' and cell[2]==idx[pos]
   expected_pos=cell[1];expected=artbytes;category='hd_source_rgba';local+=16
  for rid,tm in texture_masks.items():
   if tm[pos]:
    assert not hd and not is_texture
    c=texture_cells[str(pos)];assert c[0]==rid and c[3]=='background' and c[2]==idx[pos]
    expected_pos=c[1];expected=texture_art[rid];source_width=32;is_texture=True;category='hd_source_rgba';local+=16
  for dy in range(4):
   at=((pos//320*4+dy)*1280+pos%320*4)*4
   source_at=((expected_pos//source_width*4+dy)*source_width*4+expected_pos%source_width*4)*4
   assert pixels[at:at+16]==expected[source_at:source_at+16],(sample['label'],pos,dy,category)
   counts[category]+=4
   if is_texture:texture_rgba+=4
 mouse=st['dos_mouse'];mx,my=mouse['x'],mouse['y'];cursor=memory[0x1cd74:0x1ce74]
 assert hashlib.sha256(cursor).hexdigest()=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 for k,v in enumerate(cursor):
  if v==255:continue
  x,y=mx+k%16,my+k//16
  if not(0<=x<320 and 0<=y<200):continue
  for dy in range(4):
   at=((y*4+dy)*1280+x*4)*4
   for dx in range(4):
    offset=at+dx*4;expected=tuple(native[offset:offset+3])
    if a.text_cursor and sample['graphics']=='hd':
     proof=sample['native_live']['hd']['cursor'];assert proof['formal'] and proof['painted']==proof['source_cells']==82
     rgba=cursor_art[k//16*4+dy][k%16*4+dx];alpha=rgba[3]
     premult=[(v*257*alpha//255)>>8 for v in rgba[:3]]
     expected=tuple((v*257+old*(255-alpha)*257//255)>>8 for v,old in zip(premult,expected))
     hd_cursor_pixels+=1
    assert tuple(pixels[offset:offset+3])==expected,('cursor',sample['label'],k,dx,dy)
    counts['opaque_cursor_rgba']+=1
 rows.append({'label':sample['label'],'step':st['step'],'source_cells':sum(mask),'verified_hd_rgba':local,'excluded_text_cells':len(safe)})
required={(view,locale,graphics) for view in ['load-menu','load-slot'] for locale in ['en','zh-Hant','zh-Hans','ja','ko'] for graphics in ['original','hd']} if not a.texture_model else {('load-slot','zh-Hant',g) for g in ['original','hd']}
assert required<=coverage
result={'result':'PASS_PUBLISHED_TEXT_CURSOR_FORMAL_GUI_PIXELS' if a.text_cursor else 'PASS_PUBLISHED_SCENE_FORMAL_GUI_PIXELS','samples':len(rows),'hd_samples':sum(s['graphics']=='hd' for s in cap['samples']),'original_samples':sum(s['graphics']=='original' for s in cap['samples']),'counts':counts,'points':rows,'capture_sha256':sha(a.gui/'capture.json'),'model_sha256':sha(a.model/'check.json'),'asset_sha256':sha(art_path),'tool_sha256':sha(Path(__file__)),'all_five_languages_both_views_and_modes':not bool(a.texture_model),'scope':'Published load menu/list backgrounds; original foreground and cursor preserved; no animation credit'}
if a.text_cursor:
 assert hd_cursor_pixels==sum(s['graphics']=='hd' for s in cap['samples'])*82*16 and underlay_cells>0
 result['hd_cursor_rgba_pixels']=hd_cursor_pixels;result['verified_hd_underlay_cells']=underlay_cells;result['verified_native_cursor_underlay_cells']=native_cursor_underlay_cells
 result['scope']='Published scene backgrounds and verified glyph underlays with standard HD cursor. Text layout checked separately; unknown popup underlays stay Original.'
 for view in (['load-slot'] if a.texture_model else ['load-menu','load-slot']):
  for locale in (['zh-Hant'] if a.texture_model else ['en','zh-Hant','zh-Hans','ja','ko']):
   pair=[s for s in cap['samples'] if s['scene_label']==view and s['locale']==locale and '-hover-' not in s['label'] and '-returned-' not in s['label']]
   assert len(pair)==2 and {s['graphics'] for s in pair}=={'original','hd'}
   fields=lambda sample:[{k:item.get(k) for k in ['kind','id','text','source','safe','font_px']} for item in sample['native_live'].get('items') or []]
   assert fields(pair[0])==fields(pair[1]),(view,locale,'text layout changed with graphics mode')
 result['five_language_text_layouts_unchanged_between_modes']=not bool(a.texture_model)
 if a.texture_model:
  assert texture_rgba>0 and texture_underlays>0
  result.update(result='PASS_PUBLISHED_TEXTURE_FORMAL_GUI_PIXELS',texture_rgba_pixels=texture_rgba,verified_texture_underlay_cells=texture_underlays,representative_text_layouts_unchanged_between_modes=True,texture_model_sha256=sha(a.texture_model/'check.json'),scope='Published popup wood and glyph underlays, inherited scene background and HD cursor; nine representative normal GUI samples; other languages inherit R80, full HD incomplete')
a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result['result'],result['samples'],counts)
