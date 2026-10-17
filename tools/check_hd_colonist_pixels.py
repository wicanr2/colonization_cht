"""規格070 R74：獨立重算22幀殖民者與同頁繼承圖像的RGBA。"""
import argparse,base64,json,hashlib,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from check_hd_ship_pixels import sample_rgba
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
MANIFEST='c2947ac671891c191addb9a0f5ae6a5f0055f9ac0cab94071103420d3e67abd7'
MODEL='b6da3cef172296ce2abbd900413743d6287678a0cb3def046341112f6c2ba2ea'
TARGETS={58,60,66,81,82,83,84,85,86,87,88,89,90,91,92,93,95,96,97,98,106,107}

def blend(im,xy,rgba):
 a=rgba[3];old=im.getpixel(xy);pre=[(v*257*a//255)>>8 for v in rgba[:3]]
 im.putpixel(xy,tuple((v*257+d*(255-a)*257//255)>>8 for v,d in zip(pre,old[:3]))+(255,))

def native(st):
 idx=Path(st['indexed_path']).read_bytes();pal=Path(st['palette_path']).read_bytes()
 assert sha(idx)==st['indexed_sha256'] and sha(pal)==st['palette_sha256']
 colors=[v<<2|v>>4 for v in pal];im=Image.frombytes('P',(320,200),idx);im.putpalette(colors)
 return im.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST),idx,colors

def opaque_cursor(cursor,st):
 mouse=st['dos_mouse'];out={}
 for k,v in enumerate(cursor):
  x,y=mouse['x']+k%16,mouse['y']+k//16
  if v!=255 and 0<=x<320 and 0<=y<200:out[y*320+x]=(k,v)
 return out

def frame(assets,manifest,n):
 name='person-100.png' if n==100 else 'icons-%03d.png'%n
 meta=dict(manifest['assets'][name]);raw=(assets/name).read_bytes();assert sha(raw)==meta['sha256']
 art=Image.open(assets/name).convert('RGBA');assert list(art.size)==meta['size']
 if n==100:meta.update(sample_rect=[0,0,*meta['size']],native_content_rect=[0,0,6,16])
 else:assert list(art.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox())==meta['sample_rect']
 return meta,art

def paint(im,cells,frames,indexed,opaque):
 counts={}
 for key,cell in cells.items():
  pos=int(key);n=cell['ordinal'];meta,art=frames[n];w=meta['native_size'][0];local=cell['local']
  assert pos in opaque or indexed[pos]==cell['native'],('native-source-changed',pos,n)
  active=False;ink=0
  for yy in range(4):
   for xx in range(4):
    rgba=sample_rgba(meta,art,local%w*4+xx,local//w*4+yy)
    active|=rgba[3]>0;ink+=rgba[3]>0
    blend(im,(pos%320*4+xx,pos//320*4+yy),rgba)
  c=counts.setdefault(n,{'owned':0,'painted':0,'alpha':0});c['owned']+=1;c['painted']+=active;c['alpha']+=ink
 return counts

def restore_cursor(im,opaque,colors,curart=None):
 for pos,(k,v) in opaque.items():
  rgb=tuple(colors[3*v:3*v+3])+(255,)
  for dy in range(4):
   for dx in range(4):
    xy=(pos%320*4+dx,pos//320*4+dy);im.putpixel(xy,rgb)
    if curart is not None:
     x,y=k%16*4+dx,k//16*4+dy
     rgba=curart.getpixel((106+(2*x+1)*615//80,188+(2*y+1)*859//112)) if x<40 and y<56 else (0,0,0,0)
     blend(im,xy,rgba)

def fixed(root,assets):
 manifest=read(assets/'manifest.json');assert sha((assets/'manifest.json').read_bytes())==MANIFEST
 model=root/'colonists-ram-r1/model-r1/check.json';assert sha(model.read_bytes())==MODEL
 report=read(model);assert report['result']=='PASS_COLONIST_22_RAM_RESEARCH_NATIVE_MODEL'
 base=read(root/'baseline-colonists-r1/capture.json');assert len(base['samples'])==len(report['points'])==54
 cursor=(root/'colonists-ram-r1/observed-r1/point-008.cursor').read_bytes()
 assert sha(cursor)=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 return manifest,report,base,cursor

def check_native(root,assets,runtime):
 manifest,model,base,cursor=fixed(root,assets);frames={n:frame(assets,manifest,n) for n in TARGETS}
 go=read(runtime/'check.json');assert go['result']=='PASS_COLONIST_22_RUNTIME_NATIVE_54' and go['colonist_points']==45 and go['dos_inputs']==81 and go['end']==156200000
 assert set(map(int,go['negative_cases']))==TARGETS and all(len(v)==20 for v in go['negative_cases'].values())
 checks=[]
 for i,(sample,point) in enumerate(zip(base['samples'],model['points'])):
  cells=read(root/'colonists-ram-r1/model-r1'/point['main_owners_file'])
  if not cells:continue
  original,indexed,colors=native(sample['state']);expected=original.copy();opaque=opaque_cursor(cursor,sample['state'])
  counts=paint(expected,cells,frames,indexed,opaque);restore_cursor(expected,opaque,colors)
  assert Image.open(runtime/('point-%03d-original.png'%i)).convert('RGBA').tobytes()==original.tobytes()
  actual=Image.open(runtime/('point-%03d-colonists.png'%i)).convert('RGBA');assert expected.tobytes()==actual.tobytes(),('native-RGBA',i)
  state=read(runtime/('point-%03d.json'%i))
  assert {k:{'ordinal':v['Ordinal'],'local':v['Local'],'native':v['Native']} for k,v in state['cells'].items()}=={k:{f:v[f] for f in ['ordinal','local','native']} for k,v in cells.items()}
  for n,c in counts.items():
   got=state['small']['sources'][str(n)];assert got['painted']==c['painted'] and got['alpha_pixels']==c['alpha']
  checks.append({'point':i,'rgba_pixels':1024000,'sources':counts})
 assert len(checks)==45
 return {'result':'PASS_COLONIST_22_INDEPENDENT_NATIVE_RGBA','samples':checks,'whole_rgba_pixels_compared':len(checks)*1024000,'production_connected':True,'native_negative_cases':440}

def check_gui(root,assets):
 manifest,model,base,cursor=fixed(root,assets)
 # R71已驗來源在同一百科頁的完整幾何。每幀當前數量等於其全部不透明點。
 evidence=read(root/'icons-pedia-check-r3.json');assert sha((root/'icons-pedia-check-r3.json').read_bytes())=='f47871e4eb52f5ddd74ff2fc977a53f86d8b5df164b3c9e22e7db84b9aba8eaf'
 oldcap=read(root/'baseline-pedia-r4/capture.json');i=next(i for i,s in enumerate(oldcap['samples']) if s['label']=='pedia-unit-05')
 points=evidence['checkpoints'][i];calls=read(root/'icons-pedia-observer-r2/draws.json')['calls']
 cells={};groups={}
 source_root=Path('/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels')
 for ident,count in points['by_research_id'].items():
  ident=int(ident);n=ident-827;f=next(f for f in evidence['source_observations'] if f['research_id']==ident)
  assert count==f['opaque_pixels']
  call=next(c for c in reversed(calls) if c['research_id']==ident and c['return_step']<=oldcap['samples'][i]['state']['step'])
  raw=(source_root/('%04d.idx'%ident)).read_bytes();assert sha(raw)==f['indexed_sha256']
  w,h=f['size'];x,y,_,_=call['rect'];groups[n]=(x*4,y*4,(x+w)*4,(y+h)*4)
  for local,v in enumerate(raw):
   if v!=253:cells[str((y+local//w)*320+x+local%w)]={'ordinal':n,'local':local,'native':v}
 assert len(cells)==1573 and set(groups)==TARGETS|{59,94,100}
 selected={k:v for k,v in cells.items() if v['ordinal'] in TARGETS}
 for point in model['points']:
  current=read(root/'colonists-ram-r1/model-r1'/point['main_owners_file'])
  if current:assert {k:{f:v[f] for f in ['ordinal','local','native']} for k,v in current.items()}==selected
 frames={n:frame(assets,manifest,n) for n in groups};curart=Image.open(assets/'cursor-000.png').convert('RGBA')
 assert sha((assets/'cursor-000.png').read_bytes())=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
 cap=read(root/'r74-colonists-gui-r1/capture.json');rows=[s for s in cap['samples'] if s['label'].startswith('colonists-')]
 assert len(rows)==54;originals={s['locale']:s for s in rows if s['graphics']=='original'};assert set(originals)=={'en','zh-Hant','zh-Hans','ja','ko'}
 checks=[];source_pixels=cursor_pixels=outside_pixels=0
 def box(s):
  m=s['state']['dos_mouse'];return (m['x']*4,m['y']*4,(m['x']+16)*4,(m['y']+16)*4)
 for s in rows:
  expected,indexed,colors=native(s['state']);actual=Image.open(s['image']).convert('RGBA');opaque=opaque_cursor(cursor,s['state'])
  assert sha(actual.tobytes())==s['state']['presentation_rgba_sha256']
  assert actual.tobytes()==Image.open(s['x11']).convert('RGBA').crop((0,48,1280,848)).tobytes()
  if s['graphics']=='hd':
   counts=paint(expected,cells,frames,indexed,opaque);restore_cursor(expected,opaque,colors,curart)
   hd=s['native_live']['hd']
   for n,c in counts.items():
    got=hd['person'] if n==100 else hd['small']['sources'][str(n)]
    mask=bytearray(8000)
    for key,cell in cells.items():
     if cell['ordinal']==n:pos=int(key);mask[pos>>3]|=1<<(pos&7)
    assert base64.b64decode(got['mask'])==bytes(mask)
    assert got['owned']==got['valid']==c['owned'] and got['painted']==c['painted']
    if n!=100:assert got['alpha_pixels']==c['alpha']
   assert all(v.get('painted',0)==0 for k,v in hd.items() if isinstance(v,dict) and k not in ['person','small','cursor'])
   assert hd['cursor']['painted']==len(opaque)
  for roi in groups.values():
   assert expected.crop(roi).tobytes()==actual.crop(roi).tobytes(),('GUI-source-RGBA',s['label'],roi)
   source_pixels+=(roi[2]-roi[0])*(roi[3]-roi[1])
  for pos in opaque:
   roi=(pos%320*4,pos//320*4,pos%320*4+4,pos//320*4+4)
   assert expected.crop(roi).tobytes()==actual.crop(roi).tobytes(),('GUI-cursor-RGBA',s['label'],pos)
  if s['graphics']=='hd':cursor_pixels+=len(opaque)*16
  excluded=Image.new('L',(1280,800),0);d=ImageDraw.Draw(excluded);original=originals[s['locale']]
  for roi in list(groups.values())+[box(s),box(original)]:d.rectangle((roi[0],roi[1],roi[2]-1,roi[3]-1),fill=255)
  opposite=ImageChops.invert(excluded).convert('RGB');orig_native,_,_=native(original['state'])
  assert ImageChops.multiply(ImageChops.difference(native(s['state'])[0],orig_native).convert('RGB'),opposite).getbbox() is None
  original_im=Image.open(original['image']).convert('RGBA')
  assert ImageChops.multiply(ImageChops.difference(actual,original_im).convert('RGB'),opposite).getbbox() is None,('GUI-outside',s['label'])
  outside_pixels+=1024000-excluded.histogram()[255]
  checks.append({'label':s['label'],'locale':s['locale'],'graphics':s['graphics'],'source_frames':25,'actual_x11_equal':True})
 return {'result':'PASS_COLONIST_22_FORMAL_GUI_RGBA','samples':checks,'formal_hd_samples':49,'original_samples':5,'source_rgba_pixels':source_pixels,'cursor_hd_rgba_pixels':cursor_pixels,'preserved_other_rgba_pixels':outside_pixels,'inherited_frames':[59,94,100],'production_connected':True}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['root','assets','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--runtime-output',type=Path);p.add_argument('--gui',action='store_true');a=p.parse_args()
 assert Path('/.dockerenv').is_file() and os.getuid()!=0 and not a.output.exists() and a.output.parent.stat().st_uid==os.getuid()
 result=check_gui(a.root,a.assets) if a.gui else check_native(a.root,a.assets,a.runtime_output)
 result['checker_sha256']=sha(Path(__file__).read_bytes());result['manifest_sha256']=MANIFEST;result['model_sha256']=MODEL
 result['scope']='固定正常殖民者百科與標準游標；原PNG及alpha保持；不授予世界移動、戰鬥、動畫或全量HD信用。'
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(result['result'],sha(a.output.read_bytes()),flush=True)
if __name__=='__main__':main()
