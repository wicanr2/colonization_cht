#!/usr/bin/env python3
"""規格069：由原PNG與獨立發布來源核對船隻、太陽、風與煙霧動畫RGBA。"""
import argparse,base64,collections,csv,hashlib,json,os,struct
from pathlib import Path
from PIL import Image
from check_hd_opening_pixels import mapped
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def fixed_static_text(expected,idx,pal,sample,bundle):
 """從原版靜態指紋、公開譯稿和已綁定Noto字模獨立重建，不遮掉文字區。"""
 stats=collections.Counter()
 for item in sample.get('native_live',{}).get('items')or []:
  assert item['kind']=='fixed'and item['id'].startswith('OPENCRD1.SS:role:'),('unhandled text layer',item['id'])
  locale=sample['locale'];assert locale!='en'
  root=bundle/'languages'/locale
  manifest=read(root/'manifest.json');assert manifest['locale']==locale
  rel='masks/static/'+item['id'].replace(':','-')+'.json';path=root/rel
  assert path.is_file()and not path.is_symlink()and sha(path)==manifest['files_sha256'][rel]
  mask=read(path);assert mask['candidate_id']==item['id']and mask['locale']==locale and mask['font_sha256']==manifest['font_sha256']
  assert mask['family']=='Noto Sans CJK '+{'zh-Hant':'TC','zh-Hans':'SC','ja':'JP','ko':'KR'}[locale]
  assert mask['face']==manifest['face']=={'zh-Hant':3,'zh-Hans':2,'ja':0,'ko':1}[locale]
  rows=list(csv.DictReader((root/'text/static-overlay.zh-Hant.tsv').open(),delimiter='\t'))
  row=next(v for v in rows if v['candidate_id']==item['id'])
  assert sha(root/'text/static-overlay.zh-Hant.tsv')==mask['catalog_sha256']
  text=row['zh_hant']
  if locale=='zh-Hant':public=next(v for v in csv.DictReader((Path(__file__).resolve().parent.parent/'text/static-overlay.zh-Hant.tsv').open(),delimiter='\t')if v['candidate_id']==item['id'])['zh_hant']
  else:public=next(v for v in csv.DictReader((Path(__file__).resolve().parent.parent/('text/game.'+locale+'.tsv')).open(),delimiter='\t')if v['catalog']=='static'and v['key']==item['id'])['text']
  assert item['text']==text==public and hashlib.sha256(text.encode()).hexdigest()==mask['translation_sha256']
  fp=list(map(int,row['fingerprint_rect'].split(',')));safe=list(map(int,row['text_band'].split(',')))
  rect=bytes(idx[y*320+x]for y in range(fp[1],fp[3])for x in range(fp[0],fp[2]))
  assert hashlib.sha256(rect).hexdigest()==row['fingerprint_sha256']
  assert safe==[item['safe']['Min']['X'],item['safe']['Min']['Y'],item['safe']['Max']['X'],item['safe']['Max']['Y']]
  x0,y0,x1,y1=safe;lum=lambda v:sum(pal[v*3:v*3+3]);inkset=set(map(int,row['ink_indices'].split(',')))if row['ink_indices']else None
  istext=lambda v:v in inkset if inkset is not None else lum(v)<122
  colors=collections.Counter(idx[y*320+x]for y in range(y0,y1)for x in range(x0,x1))
  ink=next(iter(inkset))if inkset is not None else min((v for v in colors if colors[v]>=10),key=lum)
  assert ink==mask['ink_index']
  color=tuple(v<<2|v>>4 for v in pal[ink*3:ink*3+3])+(255,)
  for y in range(y0,y1):
   for x in range(x0,x1):
    old=idx[y*320+x]
    if not istext(old):continue
    clean=old
    found=False
    for distance in range(1,x1-x0):
     for nx in [x-distance,x+distance]:
      if x0<=nx<x1 and not istext(idx[y*320+nx]):clean=idx[y*320+nx];found=True;break
     if found:break
    if clean==old:continue
    pixel=bytes(tuple(v<<2|v>>4 for v in pal[clean*3:clean*3+3])+(255,))
    for dy in range(4):
     at=((y*4+dy)*1280+x*4)*4;expected[at:at+16]=pixel*4
    stats['static_erased_native_cells']+=1
  width,height=mask['width'],mask['height'];x,y=mask['x'],mask['y'];alpha=base64.b64decode(mask['alpha'],validate=True)
  assert len(alpha)==width*height and mask['font_size']==item['font_px']and [x,y]==[item['position']['X'],item['position']['Y']]
  assert x0*4<=x and y0*4<=y and x+width<=x1*4 and y+height<=y1*4
  for pos,ma in enumerate(alpha):
   if not ma:continue
   at=((y+pos//width)*1280+x+pos%width)*4;ma*=257;inverse=(65535-ma)*257
   for channel in range(4):expected[at+channel]=((expected[at+channel]*inverse+color[channel]*257*ma)//65535)>>8
   stats['fixed_text_rgba']+=1
  stats['fixed_text_fields']+=1
 return stats

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('assets','model','formal','decoded','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--gui',action='store_true')
 p.add_argument('--language-bundle-root',type=Path,help='正式語言包根目錄；預設formal目錄，含languages/')
 p.add_argument('--model-overlay',type=Path,help='另一次獨立來源觀測目錄')
 p.add_argument('--overlay-steps',default='',help='只替換指定步數的模型，逗號分隔')
 a=p.parse_args()
 assert bool(a.model_overlay)==bool(a.overlay_steps)
 assert Path('/.dockerenv').is_file() and os.getuid()!=0
 assert a.output.resolve().is_relative_to('/out')and not a.output.exists()and a.output.parent.stat().st_uid==os.getuid()
 manifest=read(a.assets/'manifest.json');pics={1:Image.new('RGBA',(1280,800)),2:Image.new('RGBA',(3840,528))};ships={};dimensions={};selected={}
 for name,item in manifest['assets'].items():
  f=item.get('original_source',{}).get('file')
  if f not in ['OPENBORD.PIK','OPENING.PIK','OPENSHIP.SS','OPENSUN.SS','OPENWND1.SS','OPENWND2.SS']:continue
  path=a.assets/name;assert path.is_file()and not path.is_symlink()and sha(path)==item['sha256']
  im=Image.open(path).convert('RGBA');assert list(im.size)==item['size'];selected[name]=item['sha256']
  if f in ['OPENSHIP.SS','OPENSUN.SS','OPENWND1.SS','OPENWND2.SS']:
   ordinal=item['original_source']['ordinal'];ident={'OPENSHIP.SS':1250,'OPENSUN.SS':1258,'OPENWND1.SS':1266,'OPENWND2.SS':1276}[f]+ordinal;w,h=item['native_size'];dimensions[ident]=(w,h)
   dst=ships[1250].copy()if f=='OPENSHIP.SS'and ordinal>0 else Image.new('RGBA',(w*4,h*4))
  else:dst=pics[1 if f=='OPENBORD.PIK'else 2]
  for r,b in zip(item['native_display_rects'],item['generated_display_rects']):
   x0,y0,x1,y1=r;piece=mapped(im,b,((x1-x0)*4,(y1-y0)*4))
   if f in ['OPENSHIP.SS','OPENSUN.SS','OPENWND1.SS','OPENWND2.SS']or name in ['openbord-000.png','opening-000.png']:dst.paste(piece,(x0*4,y0*4))
   else:dst.alpha_composite(piece,(x0*4,y0*4))
  if f in ['OPENSHIP.SS','OPENSUN.SS','OPENWND1.SS','OPENWND2.SS']:ships[ident]=dst
 assert set(range(1250,1258)).issubset(ships)
 assert set(ships)in [set(range(1250,1258)),set(range(1250,1265)),set(range(1250,1265))|set(range(1266,1287))]
 assert len(selected)==14+len(ships)
 assert all(im.getchannel('A').getextrema()==(255,255)for im in pics.values())
 pics={k:im.tobytes()for k,im in pics.items()};ships={k:im.tobytes()for k,im in ships.items()}
 nativePIC={1:(a.decoded/'1092.idx').read_bytes(),2:(a.decoded/'1179.idx').read_bytes()}
 nativeSS={ident:(a.decoded/('%04d.idx'%ident)).read_bytes()for ident in ships}
 states={r['step']:r for r in read(a.model/'check.json')['points']};owners={r['step']:r for r in read(a.model/'actors.json')['points']}
 roots={step:a.model for step in states}
 if a.model_overlay:
  extra_states={v['step']:v for v in read(a.model_overlay/'check.json')['points']};extra_owners={v['step']:v for v in read(a.model_overlay/'actors.json')['points']}
  for step in map(int,a.overlay_steps.split(',')):
   states[step]=extra_states[step];owners[step]=extra_owners[step];roots[step]=a.model_overlay
 if a.gui:samples=read(a.formal/'capture.json')['samples']
 else:samples=[{'label':f.stem,'image':str(f),'graphics':'hd','state':{'step':int(f.stem[6:])}}for f in sorted(a.formal.glob('point-*.png'))]
 totals=collections.Counter();results=[];frames=set();sun_frames=set();wind_frames=set();smoke_frames=set()
 for sample in samples:
  step=sample['state']['step'];state=states[step];o=owners[step];model=roots[step];actual=Image.open(sample['image']).convert('RGBA');assert actual.size==(1280,800)
  if a.gui:
   for k in ['memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags']:assert sample['state'][k]==state[k],(sample['label'],k)
   x11=Image.open(sample['x11']).convert('RGBA').crop((0,48,1280,848));assert x11.tobytes()==actual.tobytes();totals['x11_rgba']+=1280*800
   if sample['scene_label']!='opening':
    assert sample.get('native_live',{}).get('hd',{}).get('opening_picture',{}).get('painted',0)==0
    results.append({'label':sample['label'],'step':step,'scope':'exit state and X11; other scene pixels inherit their own checks'});continue
  stem='point-%08d'%step;idx=(model/(stem+'.idx')).read_bytes();pal=(model/(stem+'.palette')).read_bytes();mem=(model/(stem+'.memory')).read_bytes()
  assert hashlib.sha256(mem).hexdigest()==state['memory_sha256']and hashlib.sha256(idx).hexdigest()==state['indexed_sha256']
  original=Image.frombytes('P',(320,200),idx);original.putpalette([v<<2|v>>4 for v in pal]);expected=bytearray(original.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST).tobytes())
  pic=list(struct.iter_unpack('<BIB',(model/o['published_pic_file']).read_bytes()));actor=list(struct.iter_unpack('<HHBBBIB',(model/o['published_actor_file']).read_bytes()))
  assert len(pic)==len(actor)==64000
  enabled=sample['graphics']=='hd'and state['mode']==19 and o['live_code']and mem[0xa0000:0xafa00]==idx and hashlib.sha256(pal).hexdigest()=='b53fcec3d9bbe9af2e1d07566cd74d079dedce14f792788c7471f9e2ef0c6a54'and mem[0xafc00:0xaff00]==pal
  masks=[bytearray(8000),bytearray(8000)];counts=collections.Counter();actor_counts=collections.Counter();seen=set();sun_seen=set();wind_seen=set();smoke_seen=set()
  for pos,(kind,local,value)in enumerate(pic):
   ident,sslocal,ssvalue,pad,underKind,underLocal,underValue=actor[pos]
   if ident not in nativeSS:ident=0
   if kind:assert kind in nativePIC and local<len(nativePIC[kind])and nativePIC[kind][local]==value==idx[pos]
   if ident:
    assert ident in nativeSS and sslocal<len(nativeSS[ident]) and nativeSS[ident][sslocal]==ssvalue==idx[pos]and ssvalue!=253
    if underKind:assert underKind in nativePIC and underLocal<len(nativePIC[underKind])and nativePIC[underKind][underLocal]==underValue
   if not enabled:counts['original_rgba']+=16;continue
   if ident:
    if not underKind:counts['original_rgba']+=16;continue
    kind,local=underKind,underLocal
   if not kind:counts['original_rgba']+=16;continue
   width=320 if kind==1 else 960;sx,sy=local%width*4,local//width*4;x,y=pos%320*4,pos//320*4
   for dy in range(4):
    dest,src=((y+dy)*1280+x)*4,((sy+dy)*width*4+sx)*4;expected[dest:dest+16]=pics[kind][src:src+16]
    if ident:
     w,h=dimensions[ident];ssx,ssy=sslocal%w*4,sslocal//w*4
     for dx in range(4):
      src=((ssy+dy)*w*4+ssx+dx)*4;at=dest+dx*4;alpha=ships[ident][src+3]
      for channel in range(3):expected[at+channel]=(ships[ident][src+channel]*alpha+expected[at+channel]*(255-alpha)+127)//255
   if ident:
    if 1250<=ident<1258:group,base,visible='ship_rgba',1250,seen
    elif 1258<=ident<1265:group,base,visible='sun_rgba',1258,sun_seen
    elif 1266<=ident<1276:group,base,visible='wind_rgba',1266,wind_seen
    elif 1276<=ident<1287:group,base,visible='smoke_rgba',1276,smoke_seen
    else:raise AssertionError(('unknown formal animation',ident))
    counts[group]+=16;actor_counts[ident]+=1
    visible.add(ident-base);masks[1][pos>>3]|=1<<(pos&7)
   else:counts['border_rgba'if kind==1 else'map_rgba']+=16;masks[0][pos>>3]|=1<<(pos&7)
  if a.gui and sample.get('native_live',{}).get('items'):
   before_text=bytes(expected)
   counts.update(fixed_static_text(expected,idx,pal,sample,a.language_bundle_root or a.formal))
   modified=[i//4 for i in range(0,len(expected),4)if before_text[i:i+4]!=expected[i:i+4]]
   for pixel in modified:
    native=(pixel//1280//4)*320+pixel%1280//4
    assert pic[native][0]==0 and actor[native][0]not in nativeSS,'HD under static text needs a separate source contract'
   assert counts['original_rgba']>=len(modified)
   counts['original_rgba']-=len(modified);counts['localized_text_rgba']+=len(modified)
  assert actual.tobytes()==expected,(sample['label'],'complete RGBA differs')
  if a.gui and enabled:
   receipt=sample['native_live']['hd']['opening_picture'];assert base64.b64decode(receipt['picture_mask'])==masks[0]and base64.b64decode(receipt['sprite_mask'])==masks[1]
   for field,first,count in [('frames',1250,8),('sun_frames',1258,7),('wind_frames',1266,10),('smoke_frames',1276,11)]:
    if first not in nativeSS:continue
    assert receipt[field]==[actor_counts[first+i]for i in range(count)],(sample['label'],field,'published frame counts differ')
  frames.update(seen);sun_frames.update(sun_seen);wind_frames.update(wind_seen);smoke_frames.update(smoke_seen);totals.update(counts);totals['full_rgba']+=1280*800
  results.append({'label':sample['label'],'step':step,'counts':dict(counts),'frames':sorted(seen),'sun_frames':sorted(sun_seen),'wind_frames':sorted(wind_seen),'smoke_frames':sorted(smoke_seen),'main_vga_equal':o['full_main_vga_equal']})
 report={'result':'PASS_OPENING_ANIMATION_INDEPENDENT_RGBA','samples':len(samples),'verified_frames':sorted(frames),'verified_sun_frames':sorted(sun_frames),'verified_wind_frames':sorted(wind_frames),'verified_smoke_frames':sorted(smoke_frames),'totals':dict(totals),'assets':selected,'results':results,'scope':'canonical palette, exact published original provenance, raw PNG integer geometry; unknown sources stay original'}
 a.output.mkdir();(a.output/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(report['result'],report['samples'],report['verified_frames'],report['verified_sun_frames'],report['verified_wind_frames'],report['verified_smoke_frames'],report['totals'],flush=True)
if __name__=='__main__':main()
