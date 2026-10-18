#!/usr/bin/env python3
"""規格069 R83：由原PNG與獨立發布來源核對船隻八幀RGBA。"""
import argparse,base64,collections,hashlib,json,os,struct
from pathlib import Path
from PIL import Image
from check_hd_opening_pixels import mapped
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('assets','model','formal','decoded','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--gui',action='store_true');a=p.parse_args()
 assert Path('/.dockerenv').is_file() and os.getuid()!=0
 assert a.output.resolve().is_relative_to('/out')and not a.output.exists()and a.output.parent.stat().st_uid==os.getuid()
 manifest=read(a.assets/'manifest.json');pics={1:Image.new('RGBA',(1280,800)),2:Image.new('RGBA',(3840,528))};ships={};selected={}
 for name,item in manifest['assets'].items():
  f=item.get('original_source',{}).get('file')
  if f not in ['OPENBORD.PIK','OPENING.PIK','OPENSHIP.SS']:continue
  path=a.assets/name;assert path.is_file()and not path.is_symlink()and sha(path)==item['sha256']
  im=Image.open(path).convert('RGBA');assert list(im.size)==item['size'];selected[name]=item['sha256']
  if f=='OPENSHIP.SS':
   ordinal=item['original_source']['ordinal'];dst=Image.new('RGBA',(188,100))if ordinal==0 else ships[0].copy()
  else:dst=pics[1 if f=='OPENBORD.PIK'else 2]
  for r,b in zip(item['native_display_rects'],item['generated_display_rects']):
   x0,y0,x1,y1=r;piece=mapped(im,b,((x1-x0)*4,(y1-y0)*4))
   if f=='OPENSHIP.SS'or name in ['openbord-000.png','opening-000.png']:dst.paste(piece,(x0*4,y0*4))
   else:dst.alpha_composite(piece,(x0*4,y0*4))
  if f=='OPENSHIP.SS':ships[ordinal]=dst
 assert len(selected)==21 and set(ships)==set(range(8))
 assert all(im.getchannel('A').getextrema()==(255,255)for im in pics.values())
 pics={k:im.tobytes()for k,im in pics.items()};ships={k:im.tobytes()for k,im in ships.items()}
 nativePIC={1:(a.decoded/'1092.idx').read_bytes(),2:(a.decoded/'1179.idx').read_bytes()}
 nativeSS={1250+i:(a.decoded/('%04d.idx'%(1250+i))).read_bytes()for i in range(8)}
 states={r['step']:r for r in read(a.model/'check.json')['points']};owners={r['step']:r for r in read(a.model/'actors.json')['points']}
 if a.gui:samples=read(a.formal/'capture.json')['samples']
 else:samples=[{'label':f.stem,'image':str(f),'graphics':'hd','state':{'step':int(f.stem[6:])}}for f in sorted(a.formal.glob('point-*.png'))]
 totals=collections.Counter();results=[];frames=set()
 for sample in samples:
  step=sample['state']['step'];state=states[step];o=owners[step];actual=Image.open(sample['image']).convert('RGBA');assert actual.size==(1280,800)
  if a.gui:
   for k in ['memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags']:assert sample['state'][k]==state[k],(sample['label'],k)
   x11=Image.open(sample['x11']).convert('RGBA').crop((0,48,1280,848));assert x11.tobytes()==actual.tobytes();totals['x11_rgba']+=1280*800
   if sample['scene_label']!='opening':
    assert sample.get('native_live',{}).get('hd',{}).get('opening_picture',{}).get('painted',0)==0
    results.append({'label':sample['label'],'step':step,'scope':'exit state and X11; other scene pixels inherit their own checks'});continue
   assert not sample.get('native_live',{}).get('items')
  stem='point-%08d'%step;idx=(a.model/(stem+'.idx')).read_bytes();pal=(a.model/(stem+'.palette')).read_bytes();mem=(a.model/(stem+'.memory')).read_bytes()
  assert hashlib.sha256(mem).hexdigest()==state['memory_sha256']and hashlib.sha256(idx).hexdigest()==state['indexed_sha256']
  original=Image.frombytes('P',(320,200),idx);original.putpalette([v<<2|v>>4 for v in pal]);expected=bytearray(original.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST).tobytes())
  pic=list(struct.iter_unpack('<BIB',(a.model/o['published_pic_file']).read_bytes()));actor=list(struct.iter_unpack('<HHBBBIB',(a.model/o['published_actor_file']).read_bytes()))
  assert len(pic)==len(actor)==64000
  enabled=sample['graphics']=='hd'and state['mode']==19 and o['live_code']and mem[0xa0000:0xafa00]==idx and hashlib.sha256(pal).hexdigest()=='b53fcec3d9bbe9af2e1d07566cd74d079dedce14f792788c7471f9e2ef0c6a54'and mem[0xafc00:0xaff00]==pal
  masks=[bytearray(8000),bytearray(8000)];counts=collections.Counter();seen=set()
  for pos,(kind,local,value)in enumerate(pic):
   ident,sslocal,ssvalue,pad,underKind,underLocal,underValue=actor[pos]
   if kind:assert kind in nativePIC and local<len(nativePIC[kind])and nativePIC[kind][local]==value==idx[pos]
   if ident:
    assert ident in nativeSS and sslocal<1175 and nativeSS[ident][sslocal]==ssvalue==idx[pos]and ssvalue!=253
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
     ordinal=ident-1250;ssx,ssy=sslocal%47*4,sslocal//47*4
     for dx in range(4):
      src=((ssy+dy)*188+ssx+dx)*4;at=dest+dx*4;alpha=ships[ordinal][src+3]
      for channel in range(3):expected[at+channel]=(ships[ordinal][src+channel]*alpha+expected[at+channel]*(255-alpha)+127)//255
   if ident:counts['ship_rgba']+=16;seen.add(ident-1250);masks[1][pos>>3]|=1<<(pos&7)
   else:counts['border_rgba'if kind==1 else'map_rgba']+=16;masks[0][pos>>3]|=1<<(pos&7)
  assert actual.tobytes()==expected,(sample['label'],'complete RGBA differs')
  if a.gui and enabled:
   receipt=sample['native_live']['hd']['opening_picture'];assert base64.b64decode(receipt['picture_mask'])==masks[0]and base64.b64decode(receipt['sprite_mask'])==masks[1]
  frames.update(seen);totals.update(counts);totals['full_rgba']+=1280*800
  results.append({'label':sample['label'],'step':step,'counts':dict(counts),'frames':sorted(seen),'main_vga_equal':o['full_main_vga_equal']})
 report={'result':'PASS_OPENING_SHIP_INDEPENDENT_RGBA','samples':len(samples),'verified_frames':sorted(frames),'totals':dict(totals),'assets':selected,'results':results,'scope':'canonical palette, exact published original provenance, raw PNG integer geometry; unknown sources stay original'}
 a.output.mkdir();(a.output/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(report['result'],report['samples'],report['verified_frames'],report['totals'],flush=True)
if __name__=='__main__':main()
