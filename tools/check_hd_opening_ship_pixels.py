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


def fish_art_cache(assets,manifest,pictures):
 """由原PNG、清冊世界矩形與逐點alpha獨立重建完整魚形，保留原圖bytes。"""
 definitions={};cache={};selected={}
 for name,item in manifest['assets'].items():
  source=item.get('original_source',{})
  if source.get('file')not in ['OPENMON1.SS','OPENMON2.SS']:continue
  ident=(1182 if source['file']=='OPENMON1.SS'else 1197)+source['ordinal']
  path=assets/name;assert path.is_file()and not path.is_symlink()and sha(path)==item['sha256']
  raw=Image.open(path).convert('RGBA');assert list(raw.size)==item['size']
  assert len(item['native_display_rects'])==len(item['generated_display_rects'])==1
  world=item['native_display_rects'][0];crop=item['generated_display_rects'][0]
  assert list(raw.getchannel('A').point(lambda v:255 if v>=32 else 0).getbbox())==crop
  ax,ay=item['native_source_anchor'];w,h=item['native_size']
  assert world==[min(584,ax),min(24,ay),max(633,ax+w),max(55,ay+h)]
  assert 584<=world[0]<world[2]<=640 and 16<=world[1]<world[3]<=55
  definitions[ident]=item;selected[name]=item['sha256']
 if not definitions:return {},{},{}
 assert set(definitions)==set(range(1182,1203))
 oldmeta=manifest['assets']['opening-fish-top-000.png']
 old=Image.open(assets/'opening-fish-top-000.png').convert('RGBA')
 assert oldmeta['native_display_rects']==[[584,24,633,55]]
 oldpiece=mapped(old,oldmeta['generated_display_rects'][0],(196,124))
 mask=Image.new('L',(224,156),0);mask.paste(oldpiece.getchannel('A'),(0,32))
 path=assets/'opening-fish-clear-000.png';meta=manifest['assets'][path.name]
 assert path.is_file()and not path.is_symlink()and sha(path)==meta['sha256']=='96d98080dec2b7f0cdac9fea3e42a0ca093dc7ca6dee90f0c16f4a783ad62ada'
 clean=Image.open(path).convert('RGBA');assert clean.size==(1503,1047)and clean.getchannel('A').getextrema()==(255,255)
 selected[path.name]=meta['sha256'];clean=mapped(clean,[0,0,1503,1047],(224,156))
 base=Image.frombytes('RGBA',(3840,528),pictures[2]).crop((2336,64,2560,220))
 base.paste(clean,(0,0),mask.point(lambda v:255 if v else 0))
 for ident,item in definitions.items():
  source=item['original_source'];name=source['file'].lower().replace('.ss','')+'-%03d.png'%source['ordinal']
  raw=Image.open(assets/name).convert('RGBA');x0,y0,x1,y1=item['native_display_rects'][0]
  piece=mapped(raw,item['generated_display_rects'][0],((x1-x0)*4,(y1-y0)*4))
  layer=Image.new('RGBA',(224,156));layer.paste(piece,((x0-584)*4,(y0-16)*4))
  dst=bytearray(base.tobytes());src=layer.tobytes()
  for at in range(0,len(dst),4):
   alpha=src[at+3]
   for c in range(3):dst[at+c]=(src[at+c]*alpha+dst[at+c]*(255-alpha)+127)//255
  cache[ident]=bytes(dst)
 return cache,definitions,selected

def published_fish_pose(idx,pic,actor,native_picture,native_ss,definitions,cache,verified):
 """完整原版物件的同狀態判定；不讀正式渲染器回報，也不以步數猜姿態。"""
 result={'present':False,'verified':False,'origin':None,'matches':[],'foreground':0}
 present=set()
 for pos,a in enumerate(actor):
  ident,local,value,_,kind,under,uv=a
  if ident not in definitions:continue
  result['present']=True;present.add(ident);d=definitions[ident];w,h=d['native_size'];ax,ay=d['native_source_anchor']
  if ident not in verified or not(kind==2 and 0<=local<w*h and under==(ay+local//w)*960+ax+local%w and native_picture[under]==uv):return result
  offset=(pos%320-ax-local%w,pos//320-ay-local//w)
  if result['origin']is not None and offset!=result['origin']:return result
  result['origin']=offset
 if not result['present']:return result
 dx,dy=result['origin']
 if not(0<=584+dx<640+dx<=320 and 0<=16+dy<55+dy<=200):return result
 foreground=set()
 for y in range(16,55):
  for x in range(584,640):
   pos=(y+dy)*320+x+dx;local=y*960+x;a=actor[pos];c=pic[pos]
   if a[0]:
    ident,sl,value,_,kind,under,uv=a
    if not(kind==2 and under==local and native_picture[local]==uv and ident in verified and ident in native_ss and 0<=sl<len(native_ss[ident])and native_ss[ident][sl]==idx[pos]):return result
    if ident not in definitions:foreground.add((x,y))
   elif not(c[0]==2 and c[1]==local and c[2]==idx[pos]==native_picture[local]):return result
 result['foreground']=len(foreground)
 for ident in sorted(present&verified):
  d=definitions[ident];ax,ay=d['native_source_anchor'];w,h=d['native_size'];matched=True
  for y in range(16,55):
   for x in range(584,640):
    if (x,y)in foreground:continue
    value=native_picture[y*960+x]
    if ax<=x<ax+w and ay<=y<ay+h:
     v=native_ss[ident][(y-ay)*w+x-ax]
     if v!=253:value=v
    if idx[(y+dy)*320+x+dx]!=value:matched=False;break
   if not matched:break
  if matched:result['matches'].append(ident)
 matches=result['matches']
 result['verified']=bool(matches)and all(cache[n]==cache[matches[0]]for n in matches)
 return result

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
  if name=='opening-fish-clear-000.png':continue
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
 fish_cache,fish_definitions,fish_selected=fish_art_cache(a.assets,manifest,pics);selected.update(fish_selected)
 dimensions.update({n:tuple(d['native_size'])for n,d in fish_definitions.items()})
 nativePIC={1:(a.decoded/'1092.idx').read_bytes(),2:(a.decoded/'1179.idx').read_bytes()}
 nativeSS={ident:(a.decoded/('%04d.idx'%ident)).read_bytes()for ident in set(ships)|set(fish_definitions)}
 states={r['step']:r for r in read(a.model/'check.json')['points']};owners={r['step']:r for r in read(a.model/'actors.json')['points']}
 roots={step:a.model for step in states}
 if a.model_overlay:
  extra_states={v['step']:v for v in read(a.model_overlay/'check.json')['points']};extra_owners={v['step']:v for v in read(a.model_overlay/'actors.json')['points']}
  for step in map(int,a.overlay_steps.split(',')):
   states[step]=extra_states[step];owners[step]=extra_owners[step];roots[step]=a.model_overlay
 if a.gui:samples=read(a.formal/'capture.json')['samples']
 else:samples=[{'label':f.stem,'image':str(f),'graphics':'hd','state':{'step':int(f.stem[6:])}}for f in sorted(a.formal.glob('point-*.png'))]
 totals=collections.Counter();results=[];frames=set();sun_frames=set();wind_frames=set();smoke_frames=set();fish_sources=set()
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
  source_calls=read(model/'actors.json')['calls']
  verified={v['source_id']for v in source_calls if v.get('verified')and v['return_step']<=step}
  fish_pose=published_fish_pose(idx,pic,actor,nativePIC[2],nativeSS,fish_definitions,fish_cache,verified)
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
   actor_fish=ident in fish_definitions
   if actor_fish and not underKind:counts['original_rgba']+=16;continue
   pk,pl=(underKind,underLocal)if ident and underKind else(kind,local)
   wx,wy=pl%960,pl//960
   if pk==2 and 584<=wx<640 and 16<=wy<55 and fish_pose['present']and (not ident or actor_fish):
    origin=fish_pose['origin']
    if not fish_pose['verified']or pos%320!=wx+origin[0]or pos//320!=wy+origin[1]:counts['original_rgba']+=16;continue
    data=fish_cache[fish_pose['matches'][0]]
    for sub in range(4):
     dest=((pos//320*4+sub)*1280+pos%320*4)*4;src=(((wy-16)*4+sub)*224+(wx-584)*4)*4
     expected[dest:dest+16]=data[src:src+16]
    counts['whole_fish_rgba']+=16
    if actor_fish:actor_counts[ident]+=1;masks[1][pos>>3]|=1<<(pos&7);counts['fish_rgba']+=16
    else:masks[0][pos>>3]|=1<<(pos&7);counts['map_rgba']+=16
    continue
   if actor_fish:counts['original_rgba']+=16;continue
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
   for field,first,count in [('frames',1250,8),('sun_frames',1258,7),('wind_frames',1266,10),('smoke_frames',1276,11),('fish_frames',1182,21)]:
    if first not in nativeSS:continue
    assert receipt[field]==[actor_counts[first+i]for i in range(count)],(sample['label'],field,'published frame counts differ')
  if enabled and fish_pose['verified']:fish_sources.update(n for n in fish_definitions if actor_counts[n])
  if a.gui and enabled and fish_definitions:
   receipt=sample['native_live']['hd']['opening_picture']['fish_object']
   assert receipt['present']==fish_pose['present']and receipt['verified']==fish_pose['verified'],(sample['label'],'fish source proof differs')
   if fish_pose['verified']:
    assert receipt['candidates']==fish_pose['matches']and [receipt['origin']['X'],receipt['origin']['Y']]==list(fish_pose['origin'])and receipt['foreground_cells']==fish_pose['foreground']
  frames.update(seen);sun_frames.update(sun_seen);wind_frames.update(wind_seen);smoke_frames.update(smoke_seen);totals.update(counts);totals['full_rgba']+=1280*800
  results.append({'label':sample['label'],'step':step,'counts':dict(counts),'frames':sorted(seen),'sun_frames':sorted(sun_seen),'wind_frames':sorted(wind_seen),'smoke_frames':sorted(smoke_seen),'fish_source_counts':{str(n):actor_counts[n]for n in fish_definitions if actor_counts[n]},'fish_pose':fish_pose,'main_vga_equal':o['full_main_vga_equal']})
 report={'result':'PASS_OPENING_ANIMATION_INDEPENDENT_RGBA','samples':len(samples),'verified_frames':sorted(frames),'verified_sun_frames':sorted(sun_frames),'verified_wind_frames':sorted(wind_frames),'verified_smoke_frames':sorted(smoke_frames),'verified_fish_sources':sorted(fish_sources),'totals':dict(totals),'assets':selected,'results':results,'scope':'canonical palette, exact published original provenance, raw PNG integer geometry; unknown sources stay original'}
 a.output.mkdir();(a.output/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(report['result'],report['samples'],report['verified_frames'],report['verified_sun_frames'],report['verified_wind_frames'],report['verified_smoke_frames'],report['totals'],flush=True)
if __name__=='__main__':main()
