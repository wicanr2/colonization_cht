"""規格066 DRAFT：原型GUI快照的原版游標定位、原alpha與來源外驗證。"""
from pathlib import Path
import argparse,base64,hashlib,json,sys
from PIL import Image

p=argparse.ArgumentParser(description=__doc__)
for name in ['gui','asset','output']:p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--formal',action='store_true',help='驗正式載入路徑；省略時驗R60原型')
a=p.parse_args();assert Path('/.dockerenv').is_file() and not a.output.exists()
if not (a.gui/'check.json').is_file():print('SKIP：缺少已完成的本機原版GUI收據');sys.exit(77)
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state_key='formal' if a.formal else 'prototype'
gui=read(a.gui/'check.json');assert gui['result']==('PASS_CURSOR_FORMAL_FIVE_LANGUAGE_GUI' if a.formal else 'PASS_DRAFT_CURSOR_FIVE_LANGUAGE_GUI') and len(gui['checks'])==92 and len(gui['cursor_edges'])==9
assert gui['gui_inputs_sha256']==sha(a.gui/'gui.inputs.json')
assert sha(a.asset)=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4'
with Image.open(a.asset) as im:art=im.convert('RGBA')
bbox=art.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();assert bbox==(106,188,721,1047)
sample=[[art.getpixel((106+(2*x+1)*615//80,188+(2*y+1)*859//112)) for x in range(40)] for y in range(56)]
# 既有來源外比較保留；游標改由下方原PNG獨立公式比較。
source=Path(__file__).with_name('check_hd_building_nine_display.py').read_text()
source=source.replace('["sea","person","shelter","nine","center"]','["sea","person","shelter","nine","center","small","terrain079","cursor"]')
source=source.replace('if key=="sea" else','if key in {"sea","terrain079","cursor"} else')
source=source.replace('if not source:continue','if not source or (key=="cursor" and not source.get("painted")):continue')
old='need(actual.crop(rect).tobytes()==original.crop(rect).tobytes(),"正常恢復畫面覆蓋不透明游標")';assert source.count(old)==1
source=source.replace(old,'pass # 原PNG透明合成另驗，不授予原版游標像素保持信用',1)
scope={'__name__':'cursor_prototype_outside_helpers'};exec(compile(source,'cursor_prototype_outside_helpers','exec'),scope)
rows=[]
for path in sorted((a.gui/'terrain079').iterdir()):
 if not path.is_dir():continue
 proof=read(path/'check.json');state=proof['state'];live=proof['frame']['native_live'];hd=live.get('hd') or {};c=hd.get('cursor') or {}
 indexed=(path/'indexed').read_bytes();canvas=(path/'canvas').read_bytes();palette=(path/'palette').read_bytes();cursor=(path/'cursor-source').read_bytes()
 assert sha(path/'memory')==state['memory_sha256'] and sha(path/'indexed')==state['indexed_sha256'] and sha(path/'palette')==state['palette_sha256']
 assert hashlib.sha256(cursor).hexdigest()=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 native=Image.frombytes('P',(320,200),indexed);native.putpalette([v<<2|v>>4 for v in palette]);native=native.convert('RGB').resize((1280,800),Image.Resampling.NEAREST)
 with Image.open(path/'display.png') as im:actual=im.convert('RGB')
 assert actual.size==(1280,800)
 mouse=state['dos_mouse'];mx,my=mouse['x'],mouse['y'];expected_indexed=bytearray(canvas);positions=[]
 for k,v in enumerate(cursor):
  if v==255:continue
  x,y=mx+k%16,my+k//16
  if 0<=x<320 and 0<=y<200:expected_indexed[y*320+x]=v;positions.append((k,x,y))
 native_origin_verified=indexed==expected_indexed
 source_proof_accepted=c.get(state_key) is True and c.get('source_sha256')=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03' and not c.get('reason')
 if source_proof_accepted:
  assert c['source_cells']==len(positions) and c['painted']==len(positions)
  raw=base64.b64decode(c['mask'],validate=True);assert len(raw)==8000 and sum(v.bit_count() for v in raw)==len(positions)
 generated=bool(c.get('painted'));pixels=0
 if generated:
  assert native_origin_verified and c.get(state_key) is True and c['source_sha256']=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
  mask=base64.b64decode(c['mask'],validate=True)
  assert len(mask)==8000 and sum(v.bit_count() for v in mask)==c['painted']==c['source_cells']==len(positions)
 for k,x,y in positions:
  if generated:assert mask[(y*320+x)>>3]&(1<<((y*320+x)&7))
  for dy in range(4):
   for dx in range(4):
    dst=native.getpixel((x*4+dx,y*4+dy));color=dst
    if generated:
     rgba=sample[k//16*4+dy][k%16*4+dx];alpha=rgba[3]
     premult=[(v*257*alpha//255)>>8 for v in rgba[:3]]
     color=tuple((v*257+old*(255-alpha)*257//255)>>8 for v,old in zip(premult,dst))
    assert actual.getpixel((x*4+dx,y*4+dy))==color,(path.name,k,dx,dy)
    pixels+=1
 outside=scope['image_check'](path,proof)
 rows.append({'label':path.name,'step':state['step'],'mouse':[mx,my],'visible_source_cells':len(positions),'actual_hd_cursor':generated,'native_origin_verified':native_origin_verified,'source_proof_accepted':source_proof_accepted,'fully_clipped':source_proof_accepted and not positions,'verified_cursor_rgba_pixels':pixels,'hd_reason':hd.get('reason'),'cursor_reject':hd.get('cursor_reject'),'outside_changed':outside['outside_changed']})
assert len(rows)==29
edges=[r for r in rows if r['label'].startswith('cursor-edge-')];assert len(edges)==9
edge_pass=all(r['native_origin_verified'] and r['source_proof_accepted'] and r['actual_hd_cursor']==bool(r['visible_source_cells']) for r in edges)
label=('PASS_CURSOR_FORMAL_GUI_RGBA_AND_EDGES' if a.formal else 'PASS_DRAFT_CURSOR_GUI_RGBA_AND_EDGES') if edge_pass else ('CURSOR_FORMAL_GUI_EDGE_GAP' if a.formal else 'DRAFT_CURSOR_GUI_EDGE_GAP')
result={'result':label,'snapshots':rows,'edge_samples':len(edges),'edge_hd_samples':sum(r['actual_hd_cursor'] for r in edges),'edge_fully_clipped_samples':sum(r['fully_clipped'] for r in edges),'verified_cursor_rgba_pixels':sum(r['verified_cursor_rgba_pixels'] for r in rows),'production_connected':a.formal,'normal_five_language_checks':92,'gui_sha256':sha(a.gui/'check.json'),'asset_sha256':sha(a.asset),'checker_sha256':sha(Path(__file__)),'limitations':['Original CPU/RAM/WAV/save replay is separate.','Other cursor sources and hidden states are not granted coverage.']}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['result'],len(rows),result['edge_hd_samples'],flush=True)
