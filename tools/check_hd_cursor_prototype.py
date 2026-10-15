"""規格066 DRAFT：依原PNG獨立重算49份游標元件RGBA，沒有正常GUI信用。"""
from pathlib import Path
import argparse,base64,hashlib,json
from PIL import Image

p=argparse.ArgumentParser(description=__doc__)
for name in ['components','asset','native','receipts','output']:p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--formal',action='store_true',help='驗正式游標元件；省略時驗R60原型')
a=p.parse_args();assert Path('/.dockerenv').is_file() and not a.output.exists()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=read(a.components/'check.json');assert report['result']==('PASS_FORMAL_CURSOR_49_ORIGINAL_FRAME_COMPONENTS' if a.formal else 'PASS_DRAFT_CURSOR_49_ORIGINAL_FRAME_COMPONENTS') and not report['normal_gui_claim']
assert sha(a.asset)=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
with Image.open(a.asset) as im:art=im.convert('RGBA')
bbox=art.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();assert bbox==(106,188,721,1047)
ox,oy,ex,ey=bbox;sample=[[art.getpixel((ox+(2*x+1)*(ex-ox)//80,oy+(2*y+1)*(ey-oy)//112)) for x in range(40)] for y in range(56)]
points=read(a.receipts/'lifecycle-public-r29-r1/observed/gui-points.json');summaries=[]
assert len(report['points'])==len(points)==49
for i,(row,point) in enumerate(zip(report['points'],points)):
 assert row['point']==i and row['step']==point['step'] and row['memory_sha256']==point['memory_sha256']==sha(a.native/f'point-{i:03d}.memory')
 native=(a.native/f'point-{i:03d}.idx').read_bytes();palette=(a.native/f'point-{i:03d}.palette').read_bytes();cursor=(a.native/f'point-{i:03d}.cursor').read_bytes()
 assert sha(a.native/f'point-{i:03d}.idx')==point['indexed_sha256'] and sha(a.native/f'point-{i:03d}.palette')==point['palette_sha256']
 assert hashlib.sha256(cursor).hexdigest()=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 source=Image.frombytes('P',(320,200),native);source.putpalette([v<<2|v>>4 for v in palette]);source=source.convert('RGBA').resize((1280,800),Image.Resampling.NEAREST)
 with Image.open(a.components/f'point-{i:03d}.before.png') as im:before=im.convert('RGBA')
 with Image.open(a.components/f'point-{i:03d}.after.png') as im:after=im.convert('RGBA')
 assert before.tobytes()==source.tobytes()
 expected=before.copy();mx,my=row['mouse']['X'],row['mouse']['Y'];cells=set();pixels=0;underlay=0
 for k,v in enumerate(cursor):
  if v==255:continue
  x,y=mx+k%16,my+k//16
  if not(0<=x<320 and 0<=y<200):continue
  cells.add(y*320+x)
  for dy in range(4):
   for dx in range(4):
    sx,sy=k%16*4+dx,k//16*4+dy;rgba=sample[sy][sx];alpha=rgba[3];dst=before.getpixel((x*4+dx,y*4+dy))
    premult=[(c*257*alpha//255)>>8 for c in rgba[:3]]
    color=tuple((c*257+old*(255-alpha)*257//255)>>8 for c,old in zip(premult,dst[:3]))+(255,)
    expected.putpixel((x*4+dx,y*4+dy),color);pixels+=1;underlay+=alpha<128
 assert after.tobytes()==expected.tobytes(),i
 mask=base64.b64decode(row['mask'],validate=True);assert len(mask)==8000 and sum(v.bit_count() for v in mask)==len(cells)==row['painted']==row['source_cells']==82
 assert all(mask[k>>3]&(1<<(k&7)) for k in cells) and pixels==1312 and underlay==128
 summaries.append({'point':i,'verified_rgba_pixels':pixels,'under_alpha128_subpixels':underlay,'source_cells':len(cells),'outside_unchanged':True})
result={'result':'PASS_FORMAL_CURSOR_49_COMPONENT_RGBA' if a.formal else 'PASS_DRAFT_CURSOR_49_COMPONENT_RGBA','points':summaries,'verified_rgba_pixels':sum(x['verified_rgba_pixels'] for x in summaries),'normal_gui_claim':False,'production_connected':a.formal,'asset_sha256':sha(a.asset),'component_check_sha256':sha(a.components/'check.json'),'checker_sha256':sha(Path(__file__))}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['result'],result['verified_rgba_pixels'],flush=True)
