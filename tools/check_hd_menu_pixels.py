from pathlib import Path
from PIL import Image
import json,hashlib,base64
import argparse
parser=argparse.ArgumentParser(description='規格069：獨立核對主選單GUI像素與文字底色')
parser.add_argument('--root',type=Path,default=Path('/out'))
for name in ['fixture','original','model','assets','output']:parser.add_argument('--'+name,type=Path)
a=parser.parse_args()
p=a.root;read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
fixture_path=a.fixture or p/'menu-original-r1/fixture.json'
fixture=read(fixture_path);model=a.model or p/'menu-model-r1';original=a.original or fixture_path.parent/'observed'
decoded=Path('/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3')
rawpik=(decoded/'pixels/1181.idx').read_bytes()
def sample(path,size):
 im=Image.open(path).convert('RGBA');w,h=size
 return [im.getpixel(((2*x+1)*im.width//(2*w),(2*y+1)*im.height//(2*h))) for y in range(h) for x in range(w)]
assets=a.assets or Path('/repo/graphics')
assert sha(assets/'opentile-000.png')=='cb2a8af8077d1e6fd0082d753e7cc0251192df0705ebe34496f1954f5cdc4547'
assert sha(assets/'openmenu-000.png')=='2d688773ecc1bf1a1555d53d632f33fa571cf25a0ea930d38b5219b61ddc819f'
wood=sample(assets/'opentile-000.png',(128,96));art=sample(assets/'openmenu-000.png',(1280,800))
results=[]
for s in fixture['samples']:
 if s['graphics']!='hd':continue
 i=s['point'];canvas=(original/f'point-{i:03d}.canvas').read_bytes();native=(original/f'point-{i:03d}.idx').read_bytes();pal=(original/f'point-{i:03d}.palette').read_bytes()
 live=s.get('native_live') or read(Path(s['proof']))['frame']['native_live'];hd=live['hd']
 owners=read(model/f'point-{i:03d}.texture-owners.json');under=read(model/f'point-{i:03d}.texture-underlays.json')
 cur=s['state']['dos_mouse'];cx,cy=cur['x'],cur['y'];unsafe=set()
 if s['locale']!='en':
  for item in live['items']:
   r=item['safe'];unsafe.update(y*320+x for y in range(r['Min']['Y'],r['Max']['Y']) for x in range(r['Min']['X'],r['Max']['X']))
 picture=set(k for k in range(64000) if not(77<=k%320<243 and 91<=k//320<150))
 texture=set(map(int,owners));bg=base64.b64decode(hd['texture']['background_mask']);bgset={k for k in range(64000) if bg[k>>3]&(1<<(k&7))}
 assert len(bgset)==hd['texture']['background_repaints']
 assert all(str(k) in under or str(k) in owners for k in bgset)
 if s['locale']=='en':assert not bgset
 else:assert bgset==set(map(int,under)),(s['label'],'underlay missing')
 for key,want in [('picture',picture),('texture',texture)]:
  mask=base64.b64decode(hd[key]['mask']);actual={k for k in range(64000) if mask[k>>3]&(1<<(k&7))}
  assert actual==want,(s['label'],key,'independent mask mismatch')
 im=Image.open(s['image']).convert('RGBA');pixels=im.load();counts={'picture':0,'texture':0,'unchanged':0}
 for k in range(64000):
  x,y=k%320,k//320
  if k in unsafe or (cx<=x<cx+16 and cy<=y<cy+16):continue
  if k in picture:
   assert native[k]==rawpik[k],(s['label'],'original picture differs',k)
   group='picture'
  elif k in texture:
   cell=owners[str(k)];assert canvas[k]==cell['native'];group='texture'
  else:group='unchanged'
  v=native[k]*3;rgb=tuple((z<<2)|(z>>4) for z in pal[v:v+3])+(255,)
  for dy in range(4):
   for dx in range(4):
    if group=='picture':want=art[(y*4+dy)*1280+x*4+dx]
    elif group=='texture':want=wood[(cell['local']//32*4+dy)*128+cell['local']%32*4+dx]
    else:want=rgb
    assert pixels[x*4+dx,y*4+dy]==want,(s['label'],group,x*4+dx,y*4+dy,pixels[x*4+dx,y*4+dy],want)
    counts[group]+=1
 results.append({'sample':s['label'],'rgba_pixels':counts,'hd_text_underlay_cells':len(bgset),'excluded_text_cells':len(unsafe),'cursor_checked_by_existing_spec066_gui':True})
assert len(results)==8
out={'result':'PASS_MENU_EIGHT_INDEPENDENT_RGBA_AND_TEXT_UNDERLAY_SAMPLES','samples':results,'checker_sha256':sha(Path(__file__)),'fixture_sha256':sha(fixture_path),'model_sha256':sha(model/'check.json'),'formal_asset_sha256':{n:sha(assets/n) for n in ['opentile-000.png','openmenu-000.png']}}
output=a.output or p/'menu-pixels-formal-r1.json'
assert not output.exists()
output.write_text(json.dumps(out,indent=2)+'\n');print(out['result'],sum(sum(x['rgba_pixels'].values()) for x in results),flush=True)
