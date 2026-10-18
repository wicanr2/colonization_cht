"""規格069 R77：由生成原PNG與獨立原版來源重算背景RGBA。"""
from pathlib import Path
from PIL import Image
import argparse,json,hashlib,os
from check_hd_colonist_pixels import native,opaque_cursor,restore_cursor
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
MANIFEST='e3ff9d59ae66aa2bfe643d8c208c49367de97888704173b66d6230df2fc2b636'
SOURCE_MODEL='86b56026abf760940e54f1bab89d54bdeba0bd03e90aab50b41e52ec8616781d'
CAPTURE='b4ce2bd7919cd5f693052293151f52a5a42135474ee22b847d6364452453d053'
CURSOR='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
def center_sample(art,rect,size):
 # 依規格用整數選像素中心，避免浮點最近鄰在剛好整數的取樣點向下偏一列。
 x0,y0,x1,y1=rect;w,h=size;src=art.tobytes();stride=art.width*4
 xs=[x0+(2*x+1)*(x1-x0)//(2*w) for x in range(w)]
 rows=[]
 for y in range(h):
  sy=y0+(2*y+1)*(y1-y0)//(2*h)
  rows.append(b''.join(src[sy*stride+x*4:sy*stride+x*4+4] for x in xs))
 return Image.frombytes('RGBA',(w,h),b''.join(rows))
def assets(directory):
 assert sha((directory/'manifest.json').read_bytes())==MANIFEST
 manifest=read(directory/'manifest.json');assert len(manifest['assets'])==132
 frames={}
 for rid,name in [(308,'colony-000.png'),(824,'europe-000.png'),*[(1441+n,'report%d-000.png'%n) for n in range(1,9)]]:
  meta=manifest['assets'][name];raw=(directory/name).read_bytes();assert sha(raw)==meta['sha256']
  art=Image.open(directory/name).convert('RGBA');assert list(art.size)==meta['size'] and art.getchannel('A').getextrema()==(255,255)
  target=Image.new('RGBA',tuple(meta['target_size']));covered=Image.new('L',tuple(meta['native_size']),0)
  for nr,ar in zip(meta['native_display_rects'],meta['generated_display_rects']):
   assert max(covered.crop(nr).getdata())==0
   x0,y0,x1,y1=nr;target.paste(center_sample(art,ar,((x1-x0)*4,(y1-y0)*4)),(x0*4,y0*4));covered.paste(1,nr)
  assert min(covered.getdata())==1
  frames[rid]=target
 return frames
def check_native(root,directory,runtime):
 frames=assets(directory);model_path=root/'report-source-model-r3/check.json';capture_path=root/'r77-report-baseline-gui-r1/capture.json'
 assert sha(model_path.read_bytes())==SOURCE_MODEL and sha(capture_path.read_bytes())==CAPTURE
 model=read(model_path);cap=read(capture_path);proof=read(runtime/'check.json')
 assert model['result']=='PASS_REPORT_BACKGROUND_SOURCE_MODEL' and len(model['points'])==len(cap['samples'])==27
 assert proof['result']=='PASS_REPORT_NATIVE27_SOURCE_PIXELS_AND_STATE' and proof['checkpoints']==27 and proof['dos_inputs']==42
 rows=[];source_pixels=0
 for i,(point,sample) in enumerate(zip(model['points'],cap['samples'])):
  expected,indexed,colors=native(sample['state'])
  presented=Image.open(sample['image']).convert('RGBA')
  # Open/cancel可能保留前一顯示幀；來源矩形仍須與原版索引／DAC逐點相同。
  mem=(root/'report-source-probe-r2/observed'/('point-%03d.memory'%i)).read_bytes();cursor=mem[0x1cd74:0x1ce74]
  assert sha(cursor)==CURSOR
  opaque=opaque_cursor(cursor,sample['state'])
  owners=read(root/'report-source-model-r3'/('point-%03d.owners.json'%i))
  count={rid:0 for rid in frames}
  for key,cell in owners.items():
   rid,local,current,kind=cell
   if kind!='background' or not point['cursor_valid'] or not point['sources'][str(rid)]['palette_supported']:continue
   pos=int(key);assert pos in opaque or indexed[pos]==current
   x,y=pos%320*4,pos//320*4;sx,sy=local%320*4,local//320*4
   assert expected.crop((x,y,x+4,y+4)).tobytes()==presented.crop((x,y,x+4,y+4)).tobytes(),('original-background-source-region',i,pos)
   expected.paste(frames[rid].crop((sx,sy,sx+4,sy+4)),(x,y));count[rid]+=1
  restore_cursor(expected,opaque,colors)
  actual=Image.open(runtime/('point-%03d.png'%i)).convert('RGBA')
  assert expected.tobytes()==actual.tobytes(),('independent-source-RGBA',i)
  for rid in frames:assert count[rid]==point['sources'][str(rid)]['painted']
  source_pixels+=sum(16 for key,c in owners.items() if c[3]=='background' and int(key) not in opaque and point['cursor_valid'] and point['sources'][str(c[0])]['palette_supported'])
  rows.append({'point':i,'label':sample['label'],'source_cells':count,'whole_rgba_equal':True})
 return {'result':'PASS_REPORT_INDEPENDENT_NATIVE_RGBA','samples':rows,'source_rgba_cells_compared':source_pixels,'whole_rgba_pixels_compared':27*1280*800,'production_connected':True,'manifest_sha256':MANIFEST,'source_model_sha256':SOURCE_MODEL}
def translated_rectangles(sample):
 out=[]
 for item in sample['native_live'].get('items',[]):
  box=item.get('safe')
  if not box:continue
  a,b=box['Min'],box['Max'];rect=(a['X'],a['Y'],b['X'],b['Y'])
  assert 0<=rect[0]<rect[2]<=320 and 0<=rect[1]<rect[3]<=200
  out.append(rect)
 return out
def check_gui(root,directory,gui,model_root,source_probe):
 import base64
 from PIL import ImageDraw,ImageChops
 frames=assets(directory);cap=read(gui/'capture.json');model=read(model_root/'check.json')
 assert cap['result']=='PASS_REPORT_FORMAL_FIVE_LANGUAGE_GUI' and len(cap['samples'])==149
 assert model['result']=='PASS_REPORT_BACKGROUND_SOURCE_MODEL' and model['native_state_points_equal_control']==99
 by_label={p['label']:(i,p) for i,p in enumerate(model['points'])};assert len(by_label)==99
 curart_path=directory/'cursor-000.png';assert sha(curart_path.read_bytes())=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
 curart=Image.open(curart_path).convert('RGBA')
 cursor=(source_probe/'observed/point-000.memory').read_bytes()[0x1cd74:0x1ce74]
 assert sha(cursor)==CURSOR
 source_pixels=cursor_pixels=original_pixels=repaint_bits=0;rows=[];positives=set();repaint_locales=set();hovered=set();hd_count=0;original_count=0
 decoded=Path('/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels')
 original_sources={rid:(decoded/('%04d.idx'%rid)).read_bytes() for rid in [308,824,*range(1442,1450)]}
 for sample in cap['samples']:
  st=sample['state'];actual=Image.open(sample['image']).convert('RGBA');x11=Image.open(sample['x11']).convert('RGBA').crop((0,48,1280,848))
  assert sha(actual.tobytes())==st['presentation_rgba_sha256'] and actual.tobytes()==x11.tobytes(),('actual-X11',sample['label'])
  baseline,indexed,colors=native(st);opaque=opaque_cursor(cursor,st);safes=translated_rectangles(sample) if sample['locale']!='en' else []
  if sample['graphics']=='original':
   excluded=Image.new('L',(1280,800),0);d=ImageDraw.Draw(excluded)
   for x0,y0,x1,y1 in safes:d.rectangle((x0*4,y0*4,x1*4-1,y1*4-1),fill=255)
   keep=ImageChops.invert(excluded).convert('RGB')
   assert ImageChops.multiply(ImageChops.difference(actual,baseline).convert('RGB'),keep).getbbox() is None,('original-native-outside-translated-fields',sample['label'])
   original_pixels+=1024000-excluded.histogram()[255];original_count+=1
   rows.append({'label':sample['label'],'locale':sample['locale'],'graphics':'original','actual_x11_equal':True,'unchanged_native_outside_translated_fields':True})
   continue
  i,point=by_label[sample['label']]
  assert point['step']==st['step'] and point['dos_input_count']==st['dos_input_count'] and point['cursor_valid']
  owners=read(model_root/('point-%03d.owners.json'%i));group=sample['native_live']['hd']['scene_picture']
  assert group['formal'] and not group['blocked']
  sources={rid:{} for rid in frames}
  for key,c in owners.items():sources[c[0]][int(key)]=c
  checked={}
  for rid,cells in sources.items():
   expected_mask=bytearray(8000);n=0
   for pos,(ident,local,current,kind) in cells.items():
    if kind!='background':continue
    expected_mask[pos>>3]|=1<<(pos&7)
    if pos in opaque:continue
    assert indexed[pos]==current
    nx,ny=pos%320,pos//320
    if any(x0<=nx<x1 and y0<=ny<y1 for x0,y0,x1,y1 in safes):continue
    x,y=nx*4,ny*4;sx,sy=local%320*4,local//320*4
    assert actual.crop((x,y,x+4,y+4)).tobytes()==frames[rid].crop((sx,sy,sx+4,sy+4)).tobytes(),('GUI-background-source-RGBA',sample['label'],rid,pos)
    n+=16
   got=group['sources'][str(rid)];want=point['sources'][str(rid)]
   assert base64.b64decode(got['mask'])==bytes(expected_mask)
   assert got['owned_background']==got['valid_background']==got['painted']==want['painted']
   assert got['glyph_underlays']==want['glyph_underlays']
   checked[rid]=n;source_pixels+=n
   if n:positives.add((rid,sample['locale']))
  returned=base64.b64decode(group['background_mask']);assert len(returned)==8000
  active=0
  for pos in range(64000):
   if not returned[pos>>3]&(1<<(pos&7)):continue
   c=owners.get(str(pos));assert c is not None and c[0] in original_sources and 0<=c[1]<len(original_sources[c[0]])
   # 只接受獨立模型保有的背景或其字底；所有未知前景已撤銷。
   assert c[3] in ['background','glyph'] and point['sources'][str(c[0])]['palette_supported']
   active+=1
  assert group['background_repaints']>=active
  if active:repaint_locales.add(sample['locale'])
  repaint_bits+=active
  cursor_expected=baseline.copy();restore_cursor(cursor_expected,opaque,colors,curart)
  for pos in opaque:
   x,y=pos%320*4,pos//320*4
   assert actual.crop((x,y,x+4,y+4)).tobytes()==cursor_expected.crop((x,y,x+4,y+4)).tobytes(),('GUI-HD-cursor-RGBA',sample['label'],pos)
  cursor_pixels+=len(opaque)*16
  if '-hover-' in sample['label']:
   wanted=1441+sample['asset_ordinal']
   mouse=st['dos_mouse'];overlap=[pos for pos,c in sources[wanted].items() if c[3]=='background' and mouse['x']<=pos%320<mouse['x']+16 and mouse['y']<=pos//320<mouse['y']+16]
   assert overlap,('hover missed actual background',sample['label']);hovered.add((wanted,sample['locale']))
  hd_count+=1
  rows.append({'label':sample['label'],'locale':sample['locale'],'graphics':'hd','actual_x11_equal':True,'source_rgba_pixels':checked,'verified_background_repaint_cells':active})
 languages={'en','zh-Hant','zh-Hans','ja','ko'}
 assert hd_count==82 and original_count==67 and positives=={(rid,loc) for rid in range(1442,1450) for loc in languages}
 assert hovered=={(rid,loc) for rid in range(1442,1450) for loc in ['en','zh-Hant']}
 assert {'zh-Hant','zh-Hans','ja','ko'}<=repaint_locales
 return {'result':'PASS_REPORT_FORMAL_GUI_SOURCE_CURSOR_AND_ORIGINAL_RGBA','samples':rows,'hd_samples':hd_count,'original_samples':original_count,'source_rgba_pixels':source_pixels,'cursor_hd_rgba_pixels':cursor_pixels,'original_mode_preserved_native_rgba_pixels':original_pixels,'verified_background_repaint_cells':repaint_bits,'independent_native_points':99,'all_five_languages_both_sources_and_hovers':True,'manifest_sha256':MANIFEST,'gui_capture_sha256':sha((gui/'capture.json').read_bytes()),'source_model_sha256':sha((model_root/'check.json').read_bytes()),'scope':'Source background RGBA excludes translated field rectangles and opaque cursor; those cursor pixels are checked separately. Original-mode preservation excludes only declared translated fields. Full 27-point English native RGBA is separately exact. No animation or full-HD claim.','production_connected':True}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['root','assets','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--native',type=Path)
 p.add_argument('--gui-root',type=Path)
 p.add_argument('--source-model',type=Path)
 p.add_argument('--source-probe',type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists() and os.getuid()!=0
 assert a.output.parent.stat().st_uid==os.getuid() and not a.output.exists()
 assert (a.native is not None)!=(a.gui_root is not None)
 if a.gui_root is not None:
  assert a.source_model is not None and a.source_probe is not None
  result=check_gui(a.root,a.assets,a.gui_root,a.source_model,a.source_probe)
 else:result=check_native(a.root,a.assets,a.native)
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(result['result'],result.get('whole_rgba_pixels_compared',result.get('source_rgba_pixels')),flush=True)
if __name__=='__main__':main()
