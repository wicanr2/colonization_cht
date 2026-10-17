"""規格070：以原始PNG、原版索引及獨立來源模型重算五船RGBA。"""
import argparse,json,hashlib,os,base64
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda f:json.loads(f.read_bytes())
PROFILES={
 'ships':{'ordinals':[6,7,14,15,127],'baseline':'baseline-ships-r5','ram':'ships-ram-r1','gui':'standalone-ships-gui-r1','native_prefix':'pedia-ship-','gui_prefix':'ship-','native_result':'PASS_FIVE_SHIP_RUNTIME_NATIVE_24','point_key':'ship_points','point_count':24,'positive_points':15,'inputs':109,'end':227400000,'model_result':'PASS_FIVE_SHIP_RAM_RESEARCH_NATIVE_MODEL','image_key':'ships','rgba_result':'PASS_FIVE_SHIP_INDEPENDENT_NATIVE_RGBA','gui_result':'PASS_FIVE_SHIP_FORMAL_GUI_RGBA'},
 'vehicles':{'ordinals':[8,9,16],'baseline':'baseline-vehicles-r1','ram':'vehicles-ram-r1','gui':'r73-vehicles-gui-r3','native_prefix':'pedia-vehicle-','gui_prefix':'vehicle-','native_result':'PASS_THREE_VEHICLE_RUNTIME_NATIVE_18','point_key':'vehicle_points','point_count':18,'positive_points':9,'inputs':86,'end':175200000,'model_result':'PASS_THREE_VEHICLE_RAM_RESEARCH_NATIVE_MODEL','image_key':'vehicles','rgba_result':'PASS_THREE_VEHICLE_INDEPENDENT_NATIVE_RGBA','gui_result':'PASS_THREE_VEHICLE_FORMAL_GUI_RGBA'}
}
def sample_rgba(meta,art,x,y):
 a,b,c,d=meta['sample_rect'];x0,y0,x1,y1=meta['native_content_rect']
 if not (x0*4<=x<x1*4 and y0*4<=y<y1*4):return (0,0,0,0)
 return art.getpixel((a+(2*(x-x0*4)+1)*(c-a)//((x1-x0)*8),b+(2*(y-y0*4)+1)*(d-b)//((y1-y0)*8)))
def check(root,assets,runtime,profile='ships'):
 cfg=PROFILES[profile]
 manifest=read(assets/'manifest.json')
 assert sha((assets/'manifest.json').read_bytes())=='c2947ac671891c191addb9a0f5ae6a5f0055f9ac0cab94071103420d3e67abd7'
 cap=read(root/cfg['baseline']/'capture.json')
 model=read(root/cfg['ram']/'model-r1/check.json')
 result=read(runtime/'check.json')
 assert result['result']==cfg['native_result'] and result[cfg['point_key']]==cfg['positive_points']
 assert result['dos_inputs']==cfg['inputs'] and result['end']==cfg['end']
 assert set(map(int,result['negative_cases']))==set(cfg['ordinals'])
 assert all(len(v)==20 for v in result['negative_cases'].values())
 assert model['result']==cfg['model_result'] and len(model['points'])==cfg['point_count']
 frames={}
 for ordinal in cfg['ordinals']:
  name='icons-%03d.png'%ordinal;f=manifest['assets'][name];raw=(assets/name).read_bytes()
  assert sha(raw)==f['sha256'] and f['original_source']['ordinal']==ordinal
  art=Image.open(assets/name).convert('RGBA');assert list(art.size)==f['size']
  assert list(art.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox())==f['sample_rect']
  assert 0<=f['native_content_rect'][0]<f['native_content_rect'][2]<=f['native_size'][0] and 0<=f['native_content_rect'][1]<f['native_content_rect'][3]<=f['native_size'][1]
  frames[ordinal]=(f,art)
 checks=[];all_rgba=painted=0
 for i,(sample,point) in enumerate(zip(cap['samples'],model['points'])):
  if not sample['label'].startswith(cfg['native_prefix']):continue
  ordinal=int(sample['label'].split('-')[2]);f,art=frames[ordinal];w,h=f['native_size']
  prefix=root/cfg['ram']/'observed-r1'/('point-%03d'%i)
  indexed=prefix.with_suffix('.idx').read_bytes();palette=prefix.with_suffix('.palette').read_bytes()
  assert sha(indexed)==sample['state']['indexed_sha256'] and sha(palette)==sample['state']['palette_sha256']
  native=Image.frombytes('P',(320,200),indexed);native.putpalette([v<<2|v>>4 for v in palette])
  native=native.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST)
  assert Image.open(runtime/('point-%03d-original.png'%i)).convert('RGBA').tobytes()==native.tobytes()
  expected=native.copy();owners=read(root/cfg['ram']/'model-r1'/point['main_owners_file'])
  state=read(runtime/('point-%03d.json'%i))
  assert {k:{'ordinal':v['Ordinal'],'local':v['Local'],'native':v['Native']} for k,v in state['cells'].items()}=={k:{a:v[a] for a in ['ordinal','local','native']} for k,v in owners.items()}
  a,b,c,d=f['sample_rect'];ink_cells=alpha_pixels=0
  for key,cell in owners.items():
   assert cell['ordinal']==ordinal
   pos=int(key);sx,sy=cell['local']%w*4,cell['local']//w*4;ink=False
   for yy in range(4):
    for xx in range(4):
     rgba=sample_rgba(f,art,sx+xx,sy+yy)
     alpha=rgba[3];ink=ink or alpha!=0;alpha_pixels+=alpha!=0
     x,y=pos%320*4+xx,pos//320*4+yy;dst=expected.getpixel((x,y))
     premult=[(v*257*alpha//255)>>8 for v in rgba[:3]]
     color=tuple((v*257+old*(255-alpha)*257//255)>>8 for v,old in zip(premult,dst[:3]))
     expected.putpixel((x,y),color+(255,))
   ink_cells+=ink
  cursor=prefix.with_suffix('.cursor').read_bytes();mouse=sample['state']['dos_mouse']
  assert sha(cursor)=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
  for k,v in enumerate(cursor):
   if v==255:continue
   x,y=mouse['x']+k%16,mouse['y']+k//16
   if 0<=x<320 and 0<=y<200:
    expected.paste(native.crop((x*4,y*4,x*4+4,y*4+4)),(x*4,y*4))
  actual=Image.open(runtime/('point-%03d-%s.png'%(i,cfg['image_key']))).convert('RGBA')
  assert actual.size==expected.size and actual.tobytes()==expected.tobytes(),('RGBA mismatch',i,ordinal)
  go_source=state['small']['sources'][str(ordinal)]
  assert go_source['painted']==ink_cells and go_source['alpha_pixels']==alpha_pixels
  checks.append({'point':i,'ordinal':ordinal,'painted_source_cells':ink_cells,'sampled_alpha_pixels':alpha_pixels,
                 'all_rgba_pixels_equal':1280*800,'original_cursor_preserved':True,'outside_source_unchanged':True})
  all_rgba+=1280*800;painted+=ink_cells
 assert len(checks)==cfg['positive_points'] and all_rgba==cfg['positive_points']*1280*800
 return {'result':cfg['rgba_result'],'production_connected':True,'samples':checks,
         'whole_rgba_pixels_compared':all_rgba,'painted_native_source_cells':painted,
         'original_png_and_alpha_retained':True,'scope':str(cfg['positive_points'])+' fixed native snapshots; original alpha and final original cursor; no full HD claim'}
def check_gui(root,assets,profile='ships'):
 cfg=PROFILES[profile]
 gui=root/cfg['gui']
 cap=read(gui/'capture.json');base=read(root/cfg['baseline']/'capture.json');model=read(root/cfg['ram']/'model-r1/check.json')
 manifest=read(assets/'manifest.json')
 assert sha((assets/'manifest.json').read_bytes())=='c2947ac671891c191addb9a0f5ae6a5f0055f9ac0cab94071103420d3e67abd7'
 owners={}
 for i,(s,m) in enumerate(zip(base['samples'],model['points'])):
  if s['label'].startswith(cfg['native_prefix']):
   ordinal=int(s['label'].split('-')[2])
   cells=read(root/cfg['ram']/'model-r1'/m['main_owners_file'])
   if ordinal in owners:assert owners[ordinal]==cells
   owners[ordinal]=cells
 arts={o:(manifest['assets']['icons-%03d.png'%o],Image.open(assets/('icons-%03d.png'%o)).convert('RGBA')) for o in owners}
 for o,(meta,art) in arts.items():
  assert sha((assets/('icons-%03d.png'%o)).read_bytes())==meta['sha256']
  assert list(art.size)==meta['size'] and list(art.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox())==meta['sample_rect']
 cursor=(root/cfg['ram']/'observed-r1/point-009.cursor').read_bytes()
 assert sha(cursor)=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 curart=Image.open(assets/'cursor-000.png').convert('RGBA')
 assert sha((assets/'cursor-000.png').read_bytes())=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
 def blend(image,xy,rgba):
  alpha=rgba[3];old=image.getpixel(xy)
  pre=[(v*257*alpha//255)>>8 for v in rgba[:3]]
  color=tuple((v*257+d*(255-alpha)*257//255)>>8 for v,d in zip(pre,old[:3]))
  image.putpixel(xy,color+(255,))
 def native(s):
  st=s['state'];idx=Path(st['indexed_path']).read_bytes();pal=Path(st['palette_path']).read_bytes()
  assert sha(idx)==st['indexed_sha256'] and sha(pal)==st['palette_sha256']
  colors=[v<<2|v>>4 for v in pal]
  image=Image.frombytes('P',(320,200),idx);image.putpalette(colors)
  return image.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST),idx,colors
 def cursorbox(s):
  mouse=s['state']['dos_mouse'];return (mouse['x']*4,mouse['y']*4,(mouse['x']+16)*4,(mouse['y']+16)*4)
 rows=[s for s in cap['samples'] if s['label'].startswith(cfg['gui_prefix'])]
 assert len(rows)==len(cfg['ordinals'])*20
 originals={(int(s['label'].split('-')[1]),s['locale']):s for s in rows if s['graphics']=='original'}
 checks=[];roi_pixels=outside_pixels=cursor_pixels=0
 for s in rows:
  ordinal=int(s['label'].split('-')[1]);meta,art=arts[ordinal];w,h=meta['native_size']
  cells=owners[ordinal];expected,idx,pal=native(s)
  actual=Image.open(s['state']['presentation_path']).convert('RGBA')
  assert sha(actual.tobytes())==s['state']['presentation_rgba_sha256']
  assert actual.tobytes()==Image.open(gui/(s['label']+'.x11.png')).convert('RGBA').crop((0,48,1280,848)).tobytes()
  mouse=s['state']['dos_mouse'];opaque={}
  for k,v in enumerate(cursor):
   if v!=255:
    x,y=mouse['x']+k%16,mouse['y']+k//16
    if 0<=x<320 and 0<=y<200:opaque[y*320+x]=(k,v)
  if s['graphics']=='hd':
   live=s['native_live']['hd'];small=live['small'];source=small['sources'][str(ordinal)]
   assert source['valid']==source['owned']==len(cells) and source['art_available']
   source_mask=base64.b64decode(source['mask'])
   expected_mask=bytearray(8000);painted=alpha_pixels=0
   a,b,c,d=meta['sample_rect']
   for key,cell in cells.items():
    pos=int(key);local=cell['local'];sx,sy=local%w*4,local//w*4;active=False
    assert pos in opaque or idx[pos]==cell['native'],('original source changed',s['label'],pos)
    for yy in range(4):
     for xx in range(4):
      rgba=sample_rgba(meta,art,sx+xx,sy+yy)
      active|=rgba[3]!=0;alpha_pixels+=rgba[3]!=0
      blend(expected,(pos%320*4+xx,pos//320*4+yy),rgba)
    expected_mask[pos>>3]|=1<<(pos&7)
    if active:painted+=1
   assert bytes(expected_mask)==source_mask and source['painted']==painted and source['alpha_pixels']==alpha_pixels,(s['label'],bytes(expected_mask)==source_mask,source['painted'],painted,source['alpha_pixels'],alpha_pixels)
   count=0
   for pos,(k,v) in opaque.items():
    rgb=tuple(pal[3*v:3*v+3])+(255,)
    for dy in range(4):
     for dx in range(4):
      x,y=pos%320*4+dx,pos//320*4+dy;expected.putpixel((x,y),rgb)
      sx,sy=k%16*4+dx,k//16*4+dy
      rgba=curart.getpixel((106+(2*sx+1)*615//80,188+(2*sy+1)*859//112)) if sx<40 and sy<56 else (0,0,0,0)
      blend(expected,(x,y),rgba);count+=1
   cursor_pixels+=count
  # All source rectangle pixels include flags and transparent background.
  anchors={(int(k)%320-v['local']%w,int(k)//320-v['local']//w) for k,v in cells.items()}
  assert len(anchors)==1
  x0,y0=next(iter(anchors));roi=(x0*4,y0*4,(x0+w)*4,(y0+h)*4)
  assert expected.crop(roi).tobytes()==actual.crop(roi).tobytes(),('source ROI RGBA',s['label'])
  roi_pixels+=(roi[2]-roi[0])*(roi[3]-roi[1])
  for pos in opaque:
   box=(pos%320*4,pos//320*4,pos%320*4+4,pos//320*4+4)
   assert expected.crop(box).tobytes()==actual.crop(box).tobytes(),('cursor RGBA',s['label'],pos)
  excluded=Image.new('L',(1280,800),0);draw=ImageDraw.Draw(excluded)
  for box in [roi,cursorbox(s),cursorbox(originals[(ordinal,s['locale'])])]:
   draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
  orig=originals[(ordinal,s['locale'])];orig_native,orig_idx,orig_pal=native(orig)
  # Palette animation changes only unused colors; normalize only actual cursor boxes.
  diff=ImageChops.difference(native(s)[0],orig_native).convert('RGB')
  assert ImageChops.multiply(diff,ImageChops.invert(excluded).convert('RGB')).getbbox() is None,('native outside changes',s['label'])
  original_image=Image.open(orig['state']['presentation_path']).convert('RGBA')
  diff=ImageChops.difference(actual,original_image).convert('RGB')
  assert ImageChops.multiply(diff,ImageChops.invert(excluded).convert('RGB')).getbbox() is None,('outside ship/cursors changed',s['label'])
  outside=(1280*800)-excluded.histogram()[255];outside_pixels+=outside
  checks.append({'label':s['label'],'ordinal':ordinal,'language':s['locale'],'graphics':s['graphics'],'source_rgba_pixels':(roi[2]-roi[0])*(roi[3]-roi[1]),'cursor_rgba_pixels':len(opaque)*16,'preserved_other_rgba_pixels':outside,'actual_dos_mouse':mouse,'actual_x11_equal':True})
  assert s['graphics']=='original' or s['native_live']['hd']['cursor']['painted']==len(opaque)
 r={'result':cfg['gui_result'],'samples':checks,'source_rgba_pixels':roi_pixels,'cursor_hd_rgba_pixels':cursor_pixels,'preserved_other_rgba_pixels':outside_pixels,'formal_hd_samples':len(cfg['ordinals'])*15,'original_samples':len(cfg['ordinals'])*5,'original_png_alpha_retained':True,'production_connected':True,'capture_sha256':sha((gui/'capture.json').read_bytes()),'manifest_sha256':sha((assets/'manifest.json').read_bytes()),'scope':'ship source rectangles, original flags, alpha gaps and actual standard cursor; all other pixels preserved outside source and both actual cursor boxes','checker_sha256':sha(Path(__file__).read_bytes())}
 return r
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--profile',choices=sorted(PROFILES),default='ships',help='五船R72或三種車輛／火炮R73的固定原版收據')
 parser.add_argument('--gui',action='store_true',help='核對固定收據的正式五語GUI的來源、原alpha、旗標、實際游標與區外保留')
 for name in ['root','assets','output']:parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--runtime-output',type=Path,help='非GUI模式必填，指定Go原版路徑測試輸出')
 a=parser.parse_args()
 assert Path('/.dockerenv').is_file() and os.getuid()!=0 and not a.output.exists() and a.output.parent.stat().st_uid==os.getuid()
 assert a.gui or a.runtime_output is not None
 report=check_gui(a.root,a.assets,a.profile) if a.gui else check(a.root,a.assets,a.runtime_output,a.profile);report['checker_sha256']=sha(Path(__file__).read_bytes())
 report['receipts_sha256']={str(f):sha(f.read_bytes()) for f in ([a.assets/'manifest.json',a.root/PROFILES[a.profile]['ram']/'model-r1/check.json']+([] if a.gui else [a.runtime_output/'check.json']))}
 a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(report['result'],len(report['samples']),report.get('whole_rgba_pixels_compared',report.get('source_rgba_pixels')),flush=True)
if __name__=='__main__':main()
