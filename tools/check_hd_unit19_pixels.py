"""規格070 R75：獨立重算19幀單位的正常百科RGBA。"""
import argparse,base64,json,hashlib,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from check_hd_colonist_pixels import native,opaque_cursor,frame,paint,restore_cursor
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
MANIFEST='c2947ac671891c191addb9a0f5ae6a5f0055f9ac0cab94071103420d3e67abd7'
MODEL='05c9fbd9841b5b67d56128239ebdcd8c315f65365ec0612c6aff14e47bc0a0cd'
TARGETS={65,73,74,75,76,77,101,102,103,104,105,109,110,111,112,125,126,128,129}

def fixed(root,assets):
 assert sha((assets/'manifest.json').read_bytes())==MANIFEST
 manifest=read(assets/'manifest.json');assert len(manifest['assets'])==122
 model_file=root/'units19-ram-r1/model-r1/check.json';assert sha(model_file.read_bytes())==MODEL
 model=read(model_file);assert model['result']=='PASS_UNIT19_RAM_RESEARCH_NATIVE_MODEL' and len(model['points'])==61 and model['source_calls']==19
 base=read(root/'baseline-unit19-r1/capture.json');assert len(base['samples'])==61
 cursor=(root/'units19-ram-r1/observed-r1/point-008.cursor').read_bytes()
 assert sha(cursor)=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 return manifest,model,base,cursor

def cells_for(root,point):
 return read(root/'units19-ram-r1/model-r1'/point['main_owners_file'])

def check_native(root,assets,runtime):
 manifest,model,base,cursor=fixed(root,assets);proof=read(runtime/'check.json')
 assert proof['result']=='PASS_UNIT19_RUNTIME_NATIVE_61' and len(proof['points'])==61 and proof['dos_inputs']==137 and proof['unit_points']==52
 assert set(map(int,proof['negative_cases']))==TARGETS and all(len(x)==20 for x in proof['negative_cases'].values())
 frames={n:frame(assets,manifest,n) for n in TARGETS};checks=[]
 for i,(point,sample) in enumerate(zip(model['points'],base['samples'])):
  cells=cells_for(root,point)
  if not cells:continue
  expected,indexed,colors=native(sample['state']);opaque=opaque_cursor(cursor,sample['state'])
  counts=paint(expected,cells,frames,indexed,opaque);restore_cursor(expected,opaque,colors)
  actual=Image.open(runtime/('point-%03d-units19.png'%i)).convert('RGBA')
  assert expected.tobytes()==actual.tobytes(),('native-RGBA',i)
  checks.append({'point':i,'label':sample['label'],'source_frames':sorted(counts),'whole_rgba_equal':True})
 assert len(checks)==52
 return {'result':'PASS_UNIT19_INDEPENDENT_NATIVE_RGBA','samples':checks,'whole_rgba_pixels_compared':53248000,'native_negative_cases':380,'production_connected':True}

def geometry(root,model,base):
 calls_path=root/'r75-icons-entry-observer-r1/draws.json'
 assert sha(calls_path.read_bytes())=='bd34b9ef697c6c02d00361eeb0a9007087341828e9cd9e5b53144eb4efd46bef'
 calls=read(calls_path)['calls'];source_root=Path('/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels')
 evidence_path=root/'icons-pedia-check-r3.json'
 assert sha(evidence_path.read_bytes())=='f47871e4eb52f5ddd74ff2fc977a53f86d8b5df164b3c9e22e7db84b9aba8eaf'
 evidence=read(evidence_path);layouts={}
 for i,s in enumerate(base['samples']):
  if not s['label'].startswith('pedia-unit19-') or not s['label'].endswith('-away'):continue
  index=int(s['label'].split('-')[2]);cells=cells_for(root,model['points'][i]);ordinals={c['ordinal'] for c in cells.values()};assert ordinals
  groups={}
  for n in ordinals:
   c=next(c for c in reversed(calls) if c.get('research_id')==827+n and c['return_step']<=s['state']['step'])
   x,y,right,bottom=c['rect'];groups[n]=(x*4,y*4,right*4,bottom*4)
  if index==1:
   n=9;ident=827+n;source=next(f for f in evidence['source_observations'] if f['research_id']==ident)
   c=next(c for c in reversed(calls) if c.get('research_id')==ident and c['return_step']<=s['state']['step'])
   assert c['selected'] and c['unique_writes']==c['write_count']==source['opaque_pixels']==67 and c['source_encoded_sha256']==source['encoded_sha256']
   raw=(source_root/('%04d.idx'%ident)).read_bytes();assert sha(raw)==source['indexed_sha256']
   w,h=source['size'];x,y,right,bottom=c['rect'];groups[n]=(x*4,y*4,right*4,bottom*4)
   for local,v in enumerate(raw):
    if v!=253:
     key=str((y+local//w)*320+x+local%w);assert key not in cells
     cells[key]={'ordinal':n,'local':local,'native':v}
  layouts[index]=(cells,groups)
 assert len(layouts)==14 and {n for cells,groups in layouts.values() for n in groups}==TARGETS|{9}
 return layouts

def check_gui(root,assets):
 manifest,model,base,cursor=fixed(root,assets);layouts=geometry(root,model,base)
 frames={n:frame(assets,manifest,n) for n in TARGETS|{9}}
 cursor_path=assets/'cursor-000.png';assert sha(cursor_path.read_bytes())=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
 curart=Image.open(cursor_path).convert('RGBA')
 cap=read(root/'r75-unit19-gui-r1/capture.json');assert cap['result']=='PASS_UNIT19_FORMAL_FIVE_LANGUAGE_GUI' and len(cap['samples'])==187
 rows=[s for s in cap['samples'] if s['label'].startswith('unit19-')];assert len(rows)==178
 originals={(s['pedia_index'],s['locale']):s for s in rows if s['graphics']=='original'}
 assert len(originals)==70 and {(i,loc) for i in layouts for loc in ['en','zh-Hant','zh-Hans','ja','ko']}==set(originals)
 source_pixels=cursor_pixels=outside_pixels=hd_samples=0;checks=[]
 def box(s):
  m=s['state']['dos_mouse'];return(m['x']*4,m['y']*4,(m['x']+16)*4,(m['y']+16)*4)
 for s in rows:
  cells,groups=layouts[s['pedia_index']]
  expected,indexed,colors=native(s['state']);actual=Image.open(s['image']).convert('RGBA');opaque=opaque_cursor(cursor,s['state'])
  assert sha(actual.tobytes())==s['state']['presentation_rgba_sha256']
  assert actual.tobytes()==Image.open(s['x11']).convert('RGBA').crop((0,48,1280,848)).tobytes()
  if s['graphics']=='hd':
   counts=paint(expected,cells,frames,indexed,opaque);restore_cursor(expected,opaque,colors,curart);hd=s['native_live']['hd']
   for n,c in counts.items():
    got=hd['small']['sources'][str(n)];mask=bytearray(8000)
    for key,cell in cells.items():
     if cell['ordinal']==n:pos=int(key);mask[pos>>3]|=1<<(pos&7)
    assert base64.b64decode(got['mask'])==bytes(mask)
    assert got['owned']==got['valid']==c['owned'] and got['painted']==c['painted'] and got['alpha_pixels']==c['alpha'],('source-count',s['label'],n,c,got)
   assert all(v.get('painted',0)==0 for k,v in hd.items() if isinstance(v,dict) and k not in ['small','cursor'])
   assert hd['cursor']['painted']==len(opaque)
   hd_samples+=1;cursor_pixels+=len(opaque)*16
  for roi in groups.values():
   assert expected.crop(roi).tobytes()==actual.crop(roi).tobytes(),('GUI-source-RGBA',s['label'],roi)
   source_pixels+=(roi[2]-roi[0])*(roi[3]-roi[1])
  for pos in opaque:
   roi=(pos%320*4,pos//320*4,pos%320*4+4,pos//320*4+4)
   assert expected.crop(roi).tobytes()==actual.crop(roi).tobytes(),('GUI-cursor-RGBA',s['label'],pos)
  original=originals[(s['pedia_index'],s['locale'])];excluded=Image.new('L',(1280,800),0);draw=ImageDraw.Draw(excluded)
  for roi in list(groups.values())+[box(s),box(original)]:draw.rectangle((roi[0],roi[1],roi[2]-1,roi[3]-1),fill=255)
  keep=ImageChops.invert(excluded).convert('RGB');original_native,_,_=native(original['state'])
  assert ImageChops.multiply(ImageChops.difference(native(s['state'])[0],original_native).convert('RGB'),keep).getbbox() is None
  assert ImageChops.multiply(ImageChops.difference(actual,Image.open(original['image']).convert('RGBA')).convert('RGB'),keep).getbbox() is None,('GUI-outside',s['label'])
  outside_pixels+=1024000-excluded.histogram()[255]
  checks.append({'label':s['label'],'pedia_index':s['pedia_index'],'locale':s['locale'],'graphics':s['graphics'],'actual_x11_equal':True})
 assert hd_samples==108
 return {'result':'PASS_UNIT19_FORMAL_GUI_RGBA','samples':checks,'formal_hd_samples':108,'original_samples':70,'source_rgba_pixels':source_pixels,'cursor_hd_rgba_pixels':cursor_pixels,'preserved_other_rgba_pixels':outside_pixels,'inherited_frames':[9],'production_connected':True}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ['root','assets','output']:parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--runtime-output',type=Path);parser.add_argument('--gui',action='store_true');args=parser.parse_args()
 assert Path('/.dockerenv').is_file() and os.getuid()!=0 and not args.output.exists() and args.output.parent.stat().st_uid==os.getuid()
 result=check_gui(args.root,args.assets) if args.gui else check_native(args.root,args.assets,args.runtime_output)
 result.update(checker_sha256=sha(Path(__file__).read_bytes()),manifest_sha256=MANIFEST,model_sha256=MODEL,scope='固定正常14頁百科及標準游標；原PNG與alpha保持；世界移動、戰鬥、動畫及全量HD仍未驗。')
 args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(result['result'],sha(args.output.read_bytes()),flush=True)
if __name__=='__main__':main()
