from pathlib import Path
from PIL import Image
import json,hashlib,base64,collections,argparse,os
parser=argparse.ArgumentParser(description='規格069：獨立核對世界木紋GUI像素、來源及文字底色')
for name in ['fixture','model','original','asset','output']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--expected-samples',type=int,default=43)
a=parser.parse_args()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and 1<=a.expected_samples<=100
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
fixture=read(a.fixture);model=a.model
raw=a.asset;assert sha(raw)=='8580efcf85a45fa879938b5b73e8d54c58853dd9297e8ecd1f10801e637bb5d9'
im=Image.open(raw).convert('RGBA');assert im.size==(1448,1086)
art=[im.getpixel(((2*x+1)*1448//256,(2*y+1)*1086//192)) for y in range(96) for x in range(128)]
assert all(c[3]==255 for c in art)
results=[];full_palettes=set();positive=collections.Counter();guarded=0
for s in fixture['samples']:
 if s['graphics']!='hd':continue
 i=s['point'];base=a.original;canvas=(base/f'point-{i:03d}.canvas').read_bytes();native=(base/f'point-{i:03d}.idx').read_bytes();pal=(base/f'point-{i:03d}.palette').read_bytes()
 live=s.get('native_live') or read(Path(s['proof']))['frame']['native_live']
 if 'world_texture' not in live['hd']:
  assert live['hd']['reason']=='unverified-cursor-or-native-surface'
  shown=Image.open(s['image']).convert('RGBA');pixels=shown.load();cur=s['state']['dos_mouse'];count=0
  unsafe=set()
  if s['locale']!='en':
   for item in live['items']:
    area=item['safe'];unsafe.update(y*320+x for y in range(area['Min']['Y'],area['Max']['Y']) for x in range(area['Min']['X'],area['Max']['X']))
  for k,v in enumerate(native):
   x,y=k%320,k//320
   if k in unsafe or (cur['x']<=x<cur['x']+16 and cur['y']<=y<cur['y']+16):continue
   want=tuple((z<<2)|(z>>4) for z in pal[v*3:v*3+3])+(255,)
   for dy in range(4):
    for dx in range(4):assert pixels[x*4+dx,y*4+dy]==want;count+=1
  results.append({'sample':s['label'],'point':i,'wood_cells':0,'wood_rgba_pixels':0,'guard_fallback_rgba_pixels':count,'text_background_cells':0,'guard_fallback':True});guarded+=1
  continue
 hd=live['hd']['world_texture']
 owners={int(k):v for k,v in read(model/f'point-{i:03d}.texture-owners.json').items() if v['source_id']==1552}
 under={int(k):v for k,v in read(model/f'point-{i:03d}.texture-underlays.json').items() if v['source_id']==1552}
 footprint=b''.join(bytes([k])+pal[k*3:k*3+3] for k in range(128,139))
 supported=hashlib.sha256(footprint).hexdigest()=='84794389fcc2d6ee1bc645822433a74736551ccd1c8d0ed73507235ac42e3896'
 assert supported==hd['palette_supported']
 def mask(name):
  raw=base64.b64decode(hd[name]);assert len(raw)==8000
  return {k for k in range(64000) if raw[k>>3]&(1<<(k&7))}
 actual=mask('mask');assert actual==(set(owners) if supported else set()),s['label']
 assert len(actual)==hd['painted']
 bg=mask('background_mask');assert len(bg)==hd['background_repaints']
 assert bg<=set(owners)|set(under)
 if s['locale']=='en':assert not bg
 unsafe=set()
 if s['locale']!='en':
  for item in live['items']:
   r=item['safe'];unsafe.update(y*320+x for y in range(r['Min']['Y'],r['Max']['Y']) for x in range(r['Min']['X'],r['Max']['X']))
 assert bg<=unsafe,(s['label'],'background outside existing text fields')
 cur=s['state']['dos_mouse'];cx,cy=cur['x'],cur['y'];shown=Image.open(s['image']).convert('RGBA');pixels=shown.load();count=0
 for k in actual:
  x,y=k%320,k//320;c=owners[k];assert canvas[k]==c['native']
  if k in unsafe or (cx<=x<cx+16 and cy<=y<cy+16):continue
  for dy in range(4):
   for dx in range(4):
    want=art[(c['local']//32*4+dy)*128+c['local']%32*4+dx]
    assert pixels[x*4+dx,y*4+dy]==want,(s['label'],x,y,dx,dy,pixels[x*4+dx,y*4+dy],want)
    count+=1
 if actual:full_palettes.add(hashlib.sha256(pal).hexdigest());positive[s['locale']]+=1
 results.append({'sample':s['label'],'point':i,'wood_cells':len(actual),'wood_rgba_pixels':count,'text_background_cells':len(bg),'palette_supported':supported,'original_canvas_sha256':hashlib.sha256(canvas).hexdigest()})
assert len(results)==a.expected_samples and set(positive)=={'en','zh-Hant','zh-Hans','ja','ko'}
out={'result':'PASS_WORLD_WOOD_43_INDEPENDENT_GUI_RGBA_SAMPLES','samples':results,'rgba_pixels':sum(x['wood_rgba_pixels'] for x in results),'positive_languages':dict(positive),'full_palette_hashes':sorted(full_palettes),'candidate_sha256':sha(raw),'fixture_sha256':sha(a.fixture),'model_sha256':sha(model/'check.json'),'checker_sha256':sha(Path(__file__)),'production_connected':all((x.get('native_live') or read(Path(x['proof']))['frame']['native_live']).get('hd',{}).get('world_texture',{}).get('formal',False) for x in fixture['samples'] if x['graphics']=='hd' and (x.get('native_live') or read(Path(x['proof']))['frame']['native_live']).get('hd',{}).get('world_texture'))}
f=a.output;assert not f.exists();f.write_text(json.dumps(out,indent=2)+'\n');print(out['result'],out['rgba_pixels'],out['positive_languages'],flush=True)
