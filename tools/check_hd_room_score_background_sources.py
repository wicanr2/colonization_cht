"""規格069 R78 DRAFT：核對國會室內、計分木紋與繼承十種背景的原版來源、字底及標準游標；只做唯讀研究，不安裝HD。"""
from pathlib import Path
import json,hashlib,collections,argparse,os,sys
parser=argparse.ArgumentParser(description=__doc__)
for name in ['probe','points','decoded','game','output']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--scope',choices=['reports-and-room-score','room-score-only','inherited-scenes'],default='reports-and-room-score',help='限定需要正例的正常路徑；完整十二來源均重建，不外推未出現來源')
a=parser.parse_args();scope=a.scope
assert Path('/.dockerenv').exists() and os.getuid()!=0
fingerprints={'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3', 'COLONY.PIK': 'faaa637d528641a5f098eb4b1975696de182bd2d586b5f089d5a0d51320f5465', 'EUROPE.PIK': '05386fef6140252040508bdc56ca0eaeb5d7563f55bb9046f714ba09d74af118', 'REPORT1.PIK': '8050c481b9bd8eecd8011d44acafa3e700377dacb28321475fc25e51349ce91b', 'REPORT2.PIK': 'c0434e666b5dfb6d751ba67a6cf34e384365c527645e02f08eddabf5c2757d25', 'REPORT3.PIK': '01372be38f137144bf5a6b796154d01893473b0684a06f703af4840eff410a1b', 'REPORT4.PIK': 'dbdcd1d98c8eddd1a979a4d60e4e03721de2ecc79444dd9b08db80c8d2fe0bd1', 'REPORT5.PIK': 'f621afd662a05bbcc5cfe0c9ce99cd758d3142f89ce9b7c62267843fb87a1797', 'REPORT6.PIK': 'c6d59ac693f16f611e86b5884c666082525d5e73e5e63db7f8089b8aa6f903aa', 'REPORT7.PIK': 'b3fc6b0d11b87b7ed056c08ee04ed757369b54cc19dbfda29d87ffdafaedf542', 'REPORT8.PIK': 'f09699044156d9aeef55bfe9e5607e872d47eb68ad9fb930d40a3a4988b34fa6', 'CCBKGD.PIK':'d2c11061faf65c2c51fee36177eee79f0e2cdc9f67efa17d465dbea5e0e1ceca','WOODPANL.PIK':'0858856ad5b5dd0b6ab8e7a8f815fa602a9cf0237d8d323cd2b5ca141b32bc69'}
for name,want in fingerprints.items():
 f=a.game/name
 if not f.is_file():print('SKIP: missing legal original '+name);sys.exit(77)
 assert hashlib.sha256(f.read_bytes()).hexdigest()==want,('original fingerprint',name)
r=a.output.resolve();assert not r.exists() and r.is_relative_to('/out') and r.parent.stat().st_uid==os.getuid();r.mkdir()
obs=a.probe/'observed';ctrl=a.probe/'control'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes())
a_points=a.points
points=read(a_points);j=read(obs/'background.json');draw=read(obs/'draws.json');control=read(ctrl/'draws.json')
native_fields=['steps','memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags','dos_input_count']
assert len(draw['checkpoints'])==len(control['checkpoints'])
assert all(all(a[k]==b[k] for k in native_fields) for a,b in zip(draw['checkpoints'],control['checkpoints']))
assert (obs/'final.memory').read_bytes()==(ctrl/'final.memory').read_bytes()
assert 1<=len(points)==len(draw['checkpoints'])<=100
assert [(p['step'],p['dos_input_count']) for p in points]==sorted(set((p['step'],p['dos_input_count']) for p in points))
assert draw['input_sha256']==control['input_sha256']
base=0x2cae0;stage=0x3c500
rawroot=a.decoded
raw={rid:(rawroot/("%04d.idx"%rid)).read_bytes() for rid in [308,824,120,1551,*range(1442,1450)]}
offsets={rid:(40960 if rid==308 else 0) for rid in raw}
buffer_bases={rid:(stage if rid in [308,824,120,1551] else base) for rid in raw}
names={'COLONY.PIK': 308, 'EUROPE.PIK': 824, 'REPORT1.PIK': 1442, 'REPORT2.PIK': 1443, 'REPORT3.PIK': 1444, 'REPORT4.PIK': 1445, 'REPORT5.PIK': 1446, 'REPORT6.PIK': 1447, 'REPORT7.PIK': 1448, 'REPORT8.PIK': 1449,'CCBKGD.PIK':120,'WOODPANL.PIK':1551}
palettes={1442: 'f8688191241b421bab77aeaa210179fc819ffe6fa8b048393078a68edd09b82a', 1443: '0fe40f34b6bdea6bda66d3a9cd523af3f1ea089c5445ff479ffd6aacfcb7f14c', 1444: '3da023b72cc2aab2b891a09bd47568cc85806bcb901568da55e45c1d85018886', 1445: 'bf9c51eca3aa24e46dead805cc4f70f2b506fa9cdfa94b53770d824ffe02dfea', 1446: '7e1601fcbcb0a1cf15d3d0b51047c5f11908b9c8730d9d80af6fd20399a7770c', 1447: '6c5f9d3001e21cbf19895411e10d49c0be793ee8f0f17e415cfb5f5def88dffa', 1448: '20f25bf344e47c51c4f3d8e5bb6caf8208414c21c824fa5c21597538f7d4d6ca', 1449: '4a839ea8a8ef2c53b7c06e33f97e08c0d9698c1b0f0f1c1ce0c4532c69d5638a', 308: '2e90f048458e720d90c72d1356cefcffbaaebf1df97c635c44b886283a59770c', 824: '1ff4b3ba491e13699cef305d9ccfef1a578e8c41b91930fa79320953d6d7c4b3'}
native_sha={308: '70c390b5178ce8cfc37afb9199d5e25cd1859c2b7adcca36df7d149d0efa20f4', 824: 'ec4a1200b087deb467d110d0559d27f8605d5e0a8a1dddf7f3b77919479a2d3d', 1442: '799ff084b96283d89568b2f1c5037f862cc5d95fabc4c6010f47e7c2d2e3952d', 1443: '1637889ddf2d9d53b9043e82d97b97c80f80bec760ad38be5db3700f0c573683', 1444: '9cce85d587b80c69a57afd4b6d3c265426f21bf4169de162807004634372d4d9', 1445: 'cc358aea0d90e957f9cd4226a3bf02137290408d4ab8a0713089eb098e01d317', 1446: '9d7541308a0cf38e69c8eb1784ba3332d7d3b35efa33831985e7f797f57d3a52', 1447: 'b3f81ce856a2ca53d9023c70ac84cacd5d8e043acbeae00d3766eca10a395d61', 1448: '43c76c42f2a99b76908c7f39d8c9f7ca908b75bd59451b40e0a394945c921f25', 1449: 'b948334de619d2bc566dd3fe9fe39b9c76846fe3676b5bb984a6f44310f63d94'}
palettes.update({120: '4f7b7364fd534feeb06d5ac3e5fe758bc5ead07281dd073fd4825daeef607a53', 1551: 'd57afdd6d792e1e29b9710fc122c4e3db7c94082def0c955688438215cee17f2'})
native_sha.update({120:'a0c9cfe6854a9eaa36a78020f87677e8bfe4660e1c12f23b3fd674ec6fd084e3',1551:'f31602f9a239a4f83fd6e27e644384009d628517185aeb80bb248479e67d0e71'})
assert all(sha(raw[rid])==want for rid,want in native_sha.items())
codes={0xca:'f3a503f3790c81ee00808cd981c10008',0x9c:'f3a5a403f3790c81ee00808cd981c100',0x9e:'a403f3790c81ee00808cd981c100088e'}
glyph='26882547feca740afecd75dfacb504eb'
cursor='f3a48ac82bf92bf103f303fafecc75f0'
owners={};values={};pending={};copies=collections.Counter();losses=collections.Counter();sites=collections.Counter();decodes=collections.Counter();same=0;restores=0;paints=0;phase=0;current=None;results=[];pi=0
reads=[v for v in j['reads'] if v['Name'].upper().endswith('.PIK')]
cursor_source_sha='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
transactions={};completed=collections.Counter()
def capture(i):
 global cursor_source_sha
 p=points[i];stem='point-%03d'%i;mem=(obs/(stem+'.memory')).read_bytes();cv=(obs/(stem+'.canvas')).read_bytes();idx=(obs/(stem+'.idx')).read_bytes();pal=(obs/(stem+'.palette')).read_bytes()
 assert sha(mem)==p['memory_sha256'] and sha(idx)==p['indexed_sha256'] and sha(pal)==p['palette_sha256']
 source=mem[0x1cd74:0x1ce74];sourcehash=sha(source)
 for suffix in ['.memory','.idx','.canvas','.stage','.palette']:assert (obs/(stem+suffix)).read_bytes()==(ctrl/(stem+suffix)).read_bytes(),(p['label'],suffix)
 mouse=points[i]['dos_mouse'];mx,my=mouse['x'],mouse['y'];tail=mem[0xafa00:0xafc00]
 cursor_ok=sourcehash==cursor_source_sha;why=[]
 if not cursor_ok:why.append('source')
 for k,v in enumerate(source):
  if tail[256+k]!=(tail[k] if v==255 else v):cursor_ok=False;why.append('composition')
  x,y=mx+k%16,my+k//16
  if 0<=x<320 and 0<=y<200:
   at=y*320+x
   if cv[at]!=tail[k] or idx[at]!=tail[256+k]:cursor_ok=False;why.append('cursor-surface')
 for at,v in enumerate(idx):
  if not(mx<=at%320<mx+16 and my<=at//320<my+16) and cv[at]!=v:cursor_ok=False;why.append('outside-cursor')
 groups={}
 for rid in raw:
  owned={a-base:c for a,c in owners.items() if base<=a<base+64000 and c[0]==rid}
  mismatches=[at for at,c in owned.items() if cv[at]!=c[2]]
  assert not mismatches,(p['label'],rid,mismatches[:6])
  background={at:c for at,c in owned.items() if c[3]=='background'}
  foreground={at:c for at,c in owned.items() if c[3]=='glyph'}
  assert all(raw[rid][c[1]]==c[2] for c in background.values())
  used=sorted(set(raw[rid]));projection=sha(bytes(v for i in used for v in [i,*pal[i*3:i*3+3]]))
  paint=background if projection==palettes[rid] and cursor_ok else {}
  groups[rid]={'palette_supported':projection==palettes[rid],'projection_sha256':projection,'owned_background':len(background),'glyph_underlays':len(foreground),'painted':len(paint),'source_mask_sha256':sha(bytes(1 if at in paint else 0 for at in range(64000)))}
  (r/(stem+'-source-%d-mask.bin'%rid)).write_bytes(bytes(1 if at in paint else 0 for at in range(64000)))
 out={'label':p['label'],'step':p['step'],'dos_input_count':p['dos_input_count'],'cursor_valid':cursor_ok,'cursor_reasons':sorted(set(why)),'sources':groups}
 (r/(stem+'.owners.json')).write_text(json.dumps({at-base:c for at,c in owners.items() if base<=at<base+64000},separators=(',',':'))+'\n')
 results.append(out)
 print('POINT',p['label'],{rid:out['sources'][rid] for rid in [120,1551]},cursor_ok,flush=True)
for line in (obs/'background-writes.jsonl').open():
 row=json.loads(line);step,a,o,v,cs,ip,ds,si,es,di,ax,cx,flags,code=row
 while pi<len(points) and points[pi]['step']<=step:capture(pi);pi+=1
 while phase<len(reads) and reads[phase]['Step']<=step:current=reads[phase]['Name'].upper();phase+=1
 if a>=0xa0000:continue
 prior=owners.get(a);cell=None
 known=(cs==0x11b5 and ip in [0x4ee,0x54a] and code=={0x4ee:'a4ebed33c94a7509adb210d1ed8be8d1',0x54a:'aae2faeb8fac0ac074323c0174058ac8'}[ip])
 rid=names.get(current)
 if rid==1551:buffer_bases[rid]=base if base<=a<base+64000 else stage
 if known and rid and buffer_bases[rid]+offsets[rid]<=a<buffer_bases[rid]+offsets[rid]+len(raw[rid]):
  local=a-buffer_bases[rid]-offsets[rid];assert raw[rid][local]==v
  if local==0:
   assert rid not in transactions,('incomplete decode',rid)
   transactions[rid]=bytearray()
  assert rid in transactions and len(transactions[rid])==local,('decode order',rid,local)
  transactions[rid].append(v)
  if local==len(raw[rid])-1:
   assert sha(transactions.pop(rid))==native_sha[rid];completed[rid]+=1
  cell=(rid,local,v,'background');decodes[rid]+=1
 elif cs in [0xc9f,0xcba] and ip in codes and code==codes[ip]:
  delta=a-(es*16+di);src=ds*16+si+delta
  width=1 if ip==0x9e else 2
  if 0<=delta<width and si+delta<65536 and di+delta<65536 and 0<=src<0xa0000:
   got=owners.get(src)
   if got is not None and got[2]==v:
    cell=got;copies['%04X:%04X:%s'%(cs,ip,'main' if base<=a<base+64000 else 'stage' if stage<=a<stage+64000 else 'backing')]+=1
 elif cs==0xd21 and ip==0x12c and code==glyph and prior is not None and prior[2]==o:
  cell=(prior[0],prior[1],v,'glyph')
 if base<=a<base+64000 and cs==0xb68 and ip==0x51c and ds==0xa000 and es==0x2cae and code==cursor:
  delta=a-(es*16+di);src=si+delta
  if delta==0 and 0xfa00<=src<0xfc00:
   k=src&255
   if src>=0xfb00:
    pending[a]=(o,v,prior,k);owners.pop(a,None);values[a]=v;paints+=1;continue
   previous=pending.pop(a,None)
   if previous is not None and previous[3]==k and o==previous[1] and v==previous[0]:
    if previous[2] is None:owners.pop(a,None)
    else:owners[a]=previous[2]
    values[a]=v;restores+=1;continue
 if base<=a<base+64000:pending.clear()
 if prior is not None and cell is None:
  losses['%04X:%04X'%(cs,ip)]+=1;same+=o==v
 if cell is None:owners.pop(a,None)
 else:owners[a]=cell
 values[a]=v;sites['%04X:%04X:%s'%(cs,ip,code)]+=1
while pi<len(points):capture(pi);pi+=1
assert not transactions
required=[308,824] if scope=='inherited-scenes' else [120,1551] if scope=='room-score-only' else [120,1551,*range(1442,1450)]
assert all(completed[rid]>0 and any(p['sources'][rid]['painted']>0 for p in results) for rid in required),'each required source needs actual painted native evidence'
if scope=='inherited-scenes':assert completed[120]==0 and all(completed[rid]==0 for rid in range(1442,1450))
out={'result':'PASS_ROOM_SCORE_BACKGROUND_SOURCE_MODEL_RESEARCH','complete_decodes':dict(completed),'address_space':'dosgolem real-mode CS:IP and 20-bit linear RAM; no IDA EA','points':results,'copies':dict(copies),'loss_sites':dict(losses),'same_value_revocations':same,'cursor_paints':paints,'cursor_reverse_pair_restores':restores,'decode_writes':dict(decodes),'cursor_source_sha256':cursor_source_sha,'remaining_backing_owners':sum(not(base<=a<base+64000 or stage<=a<stage+64000) for a in owners),'production_connected':False,'native_state_points_equal_control':len(points)}
out['scope']=scope;out['required_sources']=required
out['receipt_sha256']={str(f):sha(f.read_bytes()) for f in [Path(__file__),a_points,obs.parent/'build.json',obs/'draws.json',ctrl/'draws.json',obs/'background.json',obs/'background-writes.jsonl',obs/'final.memory',ctrl/'final.memory']}
(r/'check.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS_ROOM_SCORE_BACKGROUND_SOURCE_MODEL_RESEARCH',len(results),dict(copies),dict(decodes),restores,flush=True)
