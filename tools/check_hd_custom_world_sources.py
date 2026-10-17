#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,base64,collections,argparse,os
parser=argparse.ArgumentParser(description="規格069 R70：自訂地圖PIK、文字與81種選取獨立來源模型")
for name in ['root','decoded','generation','layout','output']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--base-contract',type=Path,help='同來源的89點／81組已驗契約；GUI抽樣只核對實際命中，不增加覆蓋分母')
parser.add_argument('--game',type=Path,default=Path('/game'),help='唯讀合法原版目錄')
parser.add_argument('--expected-samples',type=int,default=89)
args=parser.parse_args();assert Path('/.dockerenv').exists() and os.getuid()!=0 and 1<=args.expected_samples<=100
root=args.root;obs=root/'observed';read=lambda f:json.loads(f.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
assert args.output.resolve().is_relative_to('/out') and args.output.parent.stat().st_uid==os.getuid()
assert sha((args.decoded/'catalog.json').read_bytes())=='e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d'

fixture=read(root/'fixture.json');run=read(obs/'draws.json');control=read(root/'control/draws.json')
assert read(root/'check.json')['result'].startswith('PASS_') and len(fixture['samples'])==args.expected_samples
catalog=read(args.decoded/'catalog.json');frames={f['research_id']:f for f in catalog['frames'] if f['research_id'] in [311]}
raws={n:(args.decoded/'pixels'/('%04d.idx'%n)).read_bytes() for n in frames}
for n,f in frames.items():
 assert sha(raws[n])==f['indexed_sha256']
 if not (args.game/f['file']).is_file():print('SKIP: missing legal original '+f['file']);raise SystemExit(77)
 assert sha((args.game/f['file']).read_bytes())==f['file_sha256']
assert sha((root/'fixture.json').read_bytes())==read(root/'check.json')['fixture_sha256']
assert run['input_sha256']==control['input_sha256']==sha((root/'inputs.json').read_bytes())
assert run['end']==control['end'] and run['dos_inputs']==control['dos_inputs']
assert (obs/'final.memory').read_bytes()==(root/'control/final.memory').read_bytes()
assert len(run['checkpoints'])==len(control['checkpoints'])==fixture['points']
for x,y in zip(run['checkpoints'],control['checkpoints']):
 assert {k:v for k,v in x.items() if k!='event_count'}==y
 for suffix in ['idx','canvas','stage','palette']:
  assert (obs/(x['snapshot_prefix']+'.'+suffix)).read_bytes()==(root/'control'/(y['snapshot_prefix']+'.'+suffix)).read_bytes()
for sample in fixture['samples']:
 cp=run['checkpoints'][sample['point']]
 assert cp['steps']==sample['state']['step'] and cp['dos_input_count']==sample['state']['dos_input_count']
 assert cp['memory_sha256']==sample['state']['memory_sha256']
 assert sha((obs/(cp['snapshot_prefix']+'.idx')).read_bytes())==sample['state']['indexed_sha256']
 assert sha((obs/(cp['snapshot_prefix']+'.palette')).read_bytes())==sample['state']['palette_sha256']
glyph=bytearray(64000);border=bytearray(64000);pending={};mirror={};points=[];source_rects={311:{}}
stage=bytearray(64000);decode_counts=bytearray(64000);decoding=False;decode_start=0;decodes=[];decoded=set()
events=(json.loads(line) for line in (obs/'background-writes.jsonl').open());e=next(events,None);at=0;pair_count=0
out=args.output;assert not out.exists();out.mkdir()
def mask(bits):
 b=bytearray(8000)
 for k,v in enumerate(bits):
  if v:b[k>>3]|=1<<(k&7)
 return bytes(b)
for i,cp in enumerate(run['checkpoints']):
 while e is not None and e[0]<cp['steps']:
  step,a,old,v,cs,ip,ds,si,es,di,ax,cx,flags,code=e
  if a in mirror:assert mirror[a]==old,('old byte differs',e)
  mirror[a]=v
  if 0x3c500<=a<0x3c500+64000:
   k=a-0x3c500;known=(cs,ip,code) in [(0x11b5,0x4ee,'a4ebed33c94a7509adb210d1ed8be8d1'),(0x11b5,0x54a,'aae2faeb8fac0ac074323c0174058ac8')]
   stage[k]=v
   if k==0 and known:decode_counts=bytearray(64000);decoding=True;decode_start=step
   if decoding:
    if not known or decode_counts[k]:decoding=False
    else:
     decode_counts[k]=1
     if k==63999:
      decoding=False
      if all(decode_counts):
       for source_id,source in raws.items():
        if bytes(stage)==source:
         decoded.add(source_id);decodes.append({'source_id':source_id,'first_write_step':decode_start,'last_write_step':step,'native_writes':64000})
  if 0x2cae0<=a<0x2cae0+64000:
   k=a-0x2cae0;handled=False
   if (cs,ip,ds,es,code)==(0xb68,0x51c,0xa000,0x2cae,'f3a48ac82bf92bf103f303fafecc75f0'):
    delta=a-(es*16+di);src=si+delta
    if delta==0 and 0xfa00<=src<0xfc00:
     if src>=0xfb00:
      pending[k]=(old,v,src&255,glyph[k],border[k]);glyph[k]=border[k]=0;handled=True
     else:
      prior=pending.pop(k,None)
      if prior and old==prior[1] and v==prior[0] and src&255==prior[2]:
       glyph[k],border[k]=prior[3:5];pair_count+=1;handled=True
   if not handled:
    pending.clear()
    glyph[k]=int((cs,ip,code)==(0xd21,0x12c,'26882547feca740afecd75dfacb504eb'))
    border[k]=int((cs,ip,code) in [(0xcd3,0x64,'26880503fbe0f9075fc9ca0a0090558b'),(0xccc,0x6a,'26880547e0fa075fc9ca0a00c8060000')])
  at+=1;e=next(events,None)
 s=next(s for s in fixture['samples'] if s['point']==i);label=s['label']
 n=311 if label.startswith('custom-') and not label.startswith('custom-cancel') else 0
 canvas=(obs/(cp['snapshot_prefix']+'.canvas')).read_bytes();pal=(obs/(cp['snapshot_prefix']+'.palette')).read_bytes()
 g=mask(glyph);b=mask(border);eligible=bytearray(64000)
 if n:
  assert n in decoded,('picture not decoded before GUI point',label,n)
  eligible=bytearray(int(v==raws[n][k] and not glyph[k] and not border[k]) for k,v in enumerate(canvas))
  normalized=bytes(raws[n][k] if glyph[k] or border[k] else v for k,v in enumerate(canvas))
  assert normalized==raws[n],('non-foreground differs from source',label)
  assert sum(eligible)>50000,(label,'not a settled source picture')
  positions={k for k,v in enumerate(border) if v and canvas[k]!=raws[n][k]}
  components=[]
  while positions:
   found={positions.pop()};todo=list(found)
   while todo:
    k=todo.pop()
    for nxt in [k-320,k+320]+([k-1] if k%320 else [])+([k+1] if k%320<319 else []):
     if nxt in positions:positions.remove(nxt);found.add(nxt);todo.append(nxt)
   if len(found)>100:components.append(found)
  rect=[]
  for found in components:
   box=[min(k%320 for k in found),min(k//320 for k in found),max(k%320 for k in found)+1,max(k//320 for k in found)+1]
   assert box[2]-box[0]>60 and box[3]-box[1]>40,(label,box)
   key=((box[0]+box[2])//2//80,(box[1]+box[3])//2//65)
   assert key not in source_rects[n] or source_rects[n][key]==box,(key,box)
   source_rects[n][key]=box;rect.append(box)
  assert len(rect)==4,(label,rect)
  if label.startswith('custom-state-'):
   expected={(i,int(v)) for i,v in enumerate(label.rsplit('-',1)[1])}
   actual={((b[0]+b[2])//2//80,(b[1]+b[3])//2//65) for b in rect}
   assert actual==expected,('normal selection differs',label,actual,expected)
 else:rect=None
 row={'label':label,'point':i,'step':cp['steps'],'source_id':n,'canvas_sha256':sha(canvas),'palette_sha256':sha(pal),'glyph_mask_sha256':sha(g),'glyph_mask':base64.b64encode(g).decode(),'border_mask':base64.b64encode(b).decode(),'border_mask_sha256':sha(b),'glyph_cells':sum(glyph),'same_value_glyph_cells':sum(bool(glyph[k]) and canvas[k]==raws[n][k] for k in range(64000)) if n else 0,'selected_border':rect,'paint_mask':base64.b64encode(mask(eligible)).decode(),'paint_cells':sum(eligible)}
 (out/('point-%03d.json'%i)).write_text(json.dumps(row,indent=2)+'\n');points.append({k:v for k,v in row.items() if not k.endswith('_mask')})
assert len(source_rects[311])==12
generation=read(args.generation);layout=read(args.layout);contracts=[]
art_rects={int(k):v for k,v in layout['art_rects'].items()}
for n,name in [(311,'customiz')]:
 f=frames[n];scene={}
 band=layout['wood_band'][str(n)];assert band==[0,326,1586,354]
 assert all(band[2]<=b[0] or band[0]>=b[2] or band[3]<=b[1] or band[1]>=b[3] for b in art_rects[n])
 for row in points:
  if row['source_id']!=n:continue
  key=row['canvas_sha256']
  assert key not in scene or scene[key]==row['glyph_mask_sha256']
  scene[key]=row['glyph_mask_sha256']
 if not args.base_contract:assert len(scene)>=81,(n,len(scene))
 pairs={row['glyph_mask_sha256']:row['border_mask_sha256'] for row in points if row['source_id']==n}
 assert all(pairs[row['glyph_mask_sha256']]==row['border_mask_sha256'] for row in points if row['source_id']==n)
 if args.base_contract:
  base=read(args.base_contract);assert base['result']=='PASS_CUSTOM_WORLD_INDEPENDENT_FOREGROUND_AND_81_SCENE_MODELS'
  assert base['native_points']==89
  inherited=base['source_contracts'][0]
  assert inherited['source_id']==n and inherited['file_sha256']==f['file_sha256'] and inherited['native_sha256']==f['indexed_sha256']
  assert all(inherited['foreground_pairs'].get(k)==v for k,v in pairs.items())
  assert [source_rects[n][i] for i in sorted(source_rects[n])]==inherited['native_rects']
  assert len(inherited['foreground_pairs'])==81 and inherited['wood_band']==band
  pairs=inherited['foreground_pairs']
 else:assert len(pairs)==81,(n,len(pairs),'foreground geometries')
 pals={row['palette_sha256'] for row in points if row['source_id']==n};assert len(pals)==1
 contracts.append({'source_id':n,'file':f['file'],'file_sha256':f['file_sha256'],'native_sha256':f['indexed_sha256'],'asset':name+'-v1.png','asset_sha256':generation[name]['sha256'],'palette_sha256':pals.pop(),'scenes':scene,'foreground_pairs':pairs,'normalized_canvas_sha256':f['indexed_sha256'],'native_rects':[source_rects[n][i] for i in sorted(source_rects[n])],'art_rects':art_rects[n],'wood_band':layout['wood_band'][str(n)]})
result={'result':'PASS_CUSTOM_WORLD_INDEPENDENT_FOREGROUND_AND_81_SCENE_MODELS','source_contracts':contracts,'points':points,'native_points':len(points),'dos_inputs':run['dos_inputs'],'cursor_restore_pairs':pair_count,'events':at,'completed_picture_decodes':decodes,'source_fixture_sha256':sha((root/'fixture.json').read_bytes()),'script_sha256':sha(Path(__file__).read_bytes()),'base_contract_sha256':sha(args.base_contract.read_bytes()) if args.base_contract else None,'production_connected':False}
(out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
assert decoded=={311}
print(result['result'],[(c['source_id'],len(c['scenes']),c['native_rects']) for c in contracts],{'points':len(points),'glyph_cells':sorted({x['glyph_cells'] for x in points if x['source_id']}),'same_value_glyph_cells':sum(x['same_value_glyph_cells'] for x in points)},flush=True)
