"""規格070 DRAFT：核對五艘船的正常游標遮擋；不授予RAM還原或正式HD信用。"""
from pathlib import Path
import argparse,json,hashlib,os
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def validate(canvas,indexed,memory,cursor,x,y):
 assert len(canvas)==len(indexed)==64000 and len(cursor)==256 and len(memory)>=0xafc00
 assert sha(cursor)=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03','cursor-source'
 assert memory[0x1cd74:0x1ce74]==cursor,'cursor-memory'
 expected=bytearray(canvas);background=memory[0xafa00:0xafb00];composed=memory[0xafb00:0xafc00]
 opaque=set()
 for k,v in enumerate(cursor):
  assert composed[k]==(background[k] if v==255 else v),'cursor-composition'
  xx,yy=x+k%16,y+k//16
  if not (0<=xx<320 and 0<=yy<200):continue
  at=yy*320+xx
  assert background[k]==canvas[at],'cursor-background'
  assert composed[k]==indexed[at],'cursor-indexed'
  if v!=255:expected[at]=v;opaque.add(at)
 assert bytes(expected)==indexed,'outside-cursor'
 return opaque

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();p=args.root.resolve()
 assert Path('/.dockerenv').is_file() and os.getuid()!=0
 assert not args.output.exists() and args.output.parent.stat().st_uid==os.getuid()
 ram=p/'ships-ram-r1/observed-r1'
 assert sha((p/'baseline-ships-r5/gui.inputs.json').read_bytes())=='639574cafe140655c699c9cc9709208f668af08751bdab4895b875c8673353e1'
 cap=read(p/'baseline-ships-r5/capture.json');model=read(p/'ships-ram-r1/model-r1/check.json')
 assert sha((p/'ships-ram-r1/model-r1/check.json').read_bytes())=='0e66369e9cc74d7281e4ae8d8e10f5cd06eb3a7d999b36e863906252f88875cd'
 assert model['result']=='PASS_FIVE_SHIP_RAM_RESEARCH_NATIVE_MODEL' and len(model['points'])==len(cap['samples'])==24
 checks=[];groups={}
 for sample,point in zip(cap['samples'],model['points']):
  i=point['point'];prefix=ram/('point-%03d'%i)
  canvas=prefix.with_suffix('.canvas').read_bytes();indexed=prefix.with_suffix('.idx').read_bytes()
  memory=prefix.with_suffix('.memory').read_bytes();cursor=prefix.with_suffix('.cursor').read_bytes()
  assert sha(memory)==sample['state']['memory_sha256']
  assert memory[0x2cae0:0x2cae0+64000]==canvas and sha(indexed)==sample['state']['indexed_sha256']
  mouse=sample['state']['dos_mouse'];reason=''
  try:opaque=validate(canvas,indexed,memory,cursor,mouse['x'],mouse['y'])
  except AssertionError as error:reason=str(error);opaque=set()
  owners=read(p/'ships-ram-r1/model-r1'/point['main_owners_file'])
  assert all(canvas[int(k)]==v['native'] for k,v in owners.items())
  hidden=sum(int(k) in opaque for k in owners)
  if reason:assert sample['label'] in ['load-menu','load-slot'] and not owners
  checks.append({'point':i,'label':sample['label'],'owned':len(owners),'cursor_covered_source_cells':hidden,'source_unchanged':True,'cursor_surface_verified':not reason,'guard_reason':reason})
  if sample['label'].startswith('pedia-ship-'):
   assert not reason
   ordinal=int(sample['label'].split('-')[2]);groups.setdefault(ordinal,[]).append((sample['label'],owners,hidden))
 assert set(groups)=={6,7,14,15,127}
 for ordinal,items in groups.items():
  assert len(items)==3 and items[0][1]==items[1][1]==items[2][1]
  assert items[0][2]==items[2][2]==0 and items[1][2]>0
 assert not checks[-1]['owned']
 out={'result':'PASS_FIVE_SHIP_STANDARD_CURSOR_VISIBLE_SURFACES','checker_sha256':sha(Path(__file__).read_bytes()),'production_connected':False,'native_points':24,'verified_cursor_surface_points':22,'guarded_non_source_points':2,
      'checks':checks,'ship_sources':5,'native_ram_saves':0,'native_ram_restores':0,'cursor_source_restores':0,
      'cursor_contract':'docs/spec/066-hd-standard-cursor.md','claim':'full indexed surface equals unchanged main canvas plus verified original cursor; no VGA ownership or new RAM restoration claim',
      'receipts_sha256':{str(f):sha(f.read_bytes()) for f in [p/'baseline-ships-r5/capture.json',p/'ships-ram-r1/model-r1/check.json']}}
 (args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(out['result'],[(ordinal,items[1][2]) for ordinal,items in sorted(groups.items())],flush=True)

if __name__=='__main__':main()
