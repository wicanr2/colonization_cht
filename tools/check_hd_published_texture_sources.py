"""規格069 R81：獨立核對三種底紋的主畫布、已發布VGA、字底及標準游標來源。"""
from pathlib import Path
import json,hashlib,collections,argparse,os,sys
parser=argparse.ArgumentParser(description=__doc__)
for name in ['probe','points','decoded','game','output']:parser.add_argument('--'+name,type=Path,required=True)
a=parser.parse_args();scope='published-load';published_surface=published_cursor=True
assert Path('/.dockerenv').exists() and os.getuid()!=0
assert hashlib.sha256((a.decoded.parent/'catalog.json').read_bytes()).hexdigest()=='e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d'
catalog=json.loads((a.decoded.parent/'catalog.json').read_bytes())
frames={f['research_id']:f for f in catalog['frames']}
fingerprints={frames[rid]['file']:frames[rid]['file_sha256'] for rid in [1265,1287,1552]}
fingerprints['VICEROY.EXE']='a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3'
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
native_fields=['steps','memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags','cycles','dos_input_count']
assert len(draw['checkpoints'])==len(control['checkpoints'])
assert all(all(a[k]==b[k] for k in native_fields) for a,b in zip(draw['checkpoints'],control['checkpoints']))
assert (obs/'final.memory').read_bytes()==(ctrl/'final.memory').read_bytes()
assert 1<=len(points)==len(draw['checkpoints'])<=100
assert [(p['step'],p['dos_input_count']) for p in points]==sorted(set((p['step'],p['dos_input_count']) for p in points))
assert draw['input_sha256']==control['input_sha256']
base=0x2cae0;stage=0x3c500
rawroot=a.decoded
raw={rid:(rawroot/('%04d.idx'%rid)).read_bytes() for rid in [1265,1287,1552]}
native_sha={rid:frames[rid]['indexed_sha256'] for rid in raw}
assert all(sha(raw[rid])==native_sha[rid] and len(raw[rid])==768 for rid in raw)
palettes={1265:'243ca37172f22fbfb4182d6d495ad129b9a524f093d67f0d1c5e6d215434ee5f',1552:'84794389fcc2d6ee1bc645822433a74736551ccd1c8d0ed73507235ac42e3896',1287:'7ad1391ceb732163dec0f70b714bd2efd13a53c01e878d90bbb899354ecb22c3'}
def palette_sha(rid,pal):
 return sha(pal) if rid==1265 else sha(bytes(v for k in sorted(set(raw[rid])) for v in [k,*pal[k*3:k*3+3]]))
codes={0xca:'f3a503f3790c81ee00808cd981c10008',0x9c:'f3a5a403f3790c81ee00808cd981c100',0x9e:'a403f3790c81ee00808cd981c100088e'}
glyph='26882547feca740afecd75dfacb504eb'
cursor='f3a48ac82bf92bf103f303fafecc75f0'
owners={};values={};pending={};copies=collections.Counter();losses=collections.Counter();sites=collections.Counter();decodes=collections.Counter();same=0;restores=0;paints=0;results=[];pi=0
calls=sorted(j['calls'],key=lambda c:c['return_step']);call_next=0;write_counts={rid:collections.Counter() for rid in raw}
assert len(calls)==3 and {c['source_id'] for c in calls}==set(raw)
writers={0x181:'268807035ef042fecc7402ebe7ebd03b',0x1b4:'268807035ef042fecc7403ebe790ebcc',0x1d2:'268807035ef042ebb5905a5b035efe79'}
cursor_source_sha='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
completed=collections.Counter()
cursor_rows={}
if published_cursor:
 assert read(a.probe/'build.json').get('cursor_publication_live_memory') is True
 for line in (obs/'cursor-publication.jsonl').open():
  row=json.loads(line);assert len(row)==8 and row[0] not in cursor_rows and len(bytes.fromhex(row[3]))==256
  cursor_rows[row[0]]=row
cursor_pairs={};cursor_publications=collections.Counter();cursor_pairs_peak=0;cursor_rows_used=0
published={};publication_sites=collections.Counter();publication_losses=collections.Counter();published_points=[]
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
 if published_surface:
  assert mem[0xa0000:0xa0000+64000]==idx,('raw VGA/indexed mismatch',p['label'])
  groups_vga={}
  valid={}
  vga_palettes={rid:palette_sha(rid,pal)==palettes[rid] for rid in raw}
  for at,c in published.items():
   assert c[2]==idx[at],('published/indexed mismatch',p['label'],at)
   assert raw[c[0]][c[1]]==c[2] or c[3]=='glyph'
   if not c[3]=='glyph' and not(mx<=at%320<mx+16 and my<=at//320<my+16 and (not published_cursor or source[(at//320-my)*16+at%320-mx]!=255)):
    if vga_palettes[c[0]]:valid[at]=c
  for rid in raw:
   mask=bytes(1 if at in valid and valid[at][0]==rid else 0 for at in range(64000))
   (r/(stem+'-published-%d-mask.bin'%rid)).write_bytes(mask)
   groups_vga[rid]={'owned':sum(c[0]==rid for c in published.values()),'painted':sum(mask),'mask_sha256':sha(mask)}
  (r/(stem+'.published.json')).write_text(json.dumps(published,separators=(',',':'))+'\n')
  published_points.append({'label':p['label'],'step':p['step'],'sources':groups_vga,'main_indexed_differences':sum(x!=y for x,y in zip(cv,idx))})
 groups={}
 for rid in raw:
  owned={a-base:c for a,c in owners.items() if base<=a<base+64000 and c[0]==rid}
  mismatches=[at for at,c in owned.items() if cv[at]!=c[2]]
  assert not mismatches,(p['label'],rid,mismatches[:6])
  background={at:c for at,c in owned.items() if c[3]=='background'}
  foreground={at:c for at,c in owned.items() if c[3]=='glyph'}
  assert all(raw[rid][c[1]]==c[2] for c in background.values())
  used=sorted(set(raw[rid]));projection=palette_sha(rid,pal)
  paint=background if projection==palettes[rid] and cursor_ok else {}
  groups[rid]={'palette_supported':projection==palettes[rid],'projection_sha256':projection,'owned_background':len(background),'glyph_underlays':len(foreground),'painted':len(paint),'source_mask_sha256':sha(bytes(1 if at in paint else 0 for at in range(64000)))}
  (r/(stem+'-source-%d-mask.bin'%rid)).write_bytes(bytes(1 if at in paint else 0 for at in range(64000)))
 out={'label':p['label'],'step':p['step'],'dos_input_count':p['dos_input_count'],'cursor_valid':cursor_ok,'cursor_reasons':sorted(set(why)),'sources':groups}
 (r/(stem+'.owners.json')).write_text(json.dumps({at-base:c for at,c in owners.items() if base<=at<base+64000},separators=(',',':'))+'\n')
 results.append(out)
 print('POINT',p['label'],{rid:groups_vga[rid]['painted'] for rid in raw},cursor_ok,flush=True)
for event_number,line in enumerate((obs/'background-writes.jsonl').open()):
 row=json.loads(line);step,a,o,v,cs,ip,ds,si,es,di,ax,cx,flags,code=row
 while pi<len(points) and points[pi]['step']<=step:capture(pi);pi+=1
 while call_next<len(calls) and calls[call_next]['return_step']<=step:
  c=calls[call_next];rid=c['source_id']
  assert c['entry']['entry_code12']=='c828000052535057568b4702' and c['entry']['record_words'][4:6]==[32,24] and c['entry']['registers'][0]==1
  assert c['entry']['ds_bx_words'][:2]==[24,32] and c['return_cs_ip']=='121D:1554'
  assert write_counts[rid]==collections.Counter({k:1 for k in range(768)})
  assert (obs/('texture-%d.after'%rid)).read_bytes()==raw[rid] and c['source_pixels_sha256']==native_sha[rid]
  for k,v0 in enumerate(raw[rid]):owners[c['base']+k]=(rid,k,v0,'background')
  completed[rid]+=1;call_next+=1
 for c in calls:
  if c['entry_step']<=step<c['return_step'] and c['base']<=a<c['base']+768:
   rid=c['source_id'];local=a-c['base']
   assert cs==0xd46 and writers.get(ip)==code and v==raw[rid][local]
   write_counts[rid][local]+=1
 if a>=0xa0000:
  if published_surface and 0xa0000<=a<0xa0000+64000:
   at=a-0xa0000;oldcell=published.pop(at,None)
   pair=cursor_pairs.pop(at,None)
   delta=a-(es*16+di);src=ds*16+si+delta
   row_cursor=cursor_rows.get(event_number)
   if row_cursor is not None:
    cursor_rows_used+=1
    _,cursor_step,cursor_a,source_hex,back,composed,source_value,main_value=row_cursor
    assert (cursor_step,cursor_a)==(step,a) and source_value==v
    source_bytes=bytes.fromhex(source_hex);k=si&255
    known_cursor=(cs==0xb68 and ip==0x51c and ds==0xa000 and es==0xa000 and code==cursor and delta==0 and 0xfa00<=si<0xfc00 and sha(source_bytes)==cursor_source_sha)
    if known_cursor and si>=0xfb00 and back==o and composed==v and v==(back if source_bytes[k]==255 else source_bytes[k]):
     if source_bytes[k]==255 and o==v and oldcell is not None and oldcell[2]==v:
      published[at]=oldcell;cursor_publications['transparent-paint']+=1
     elif source_bytes[k]!=255 and oldcell is not None and oldcell[2]==o:
      cursor_pairs[at]=(o,v,k,oldcell);cursor_publications['opaque-save']+=1
    elif known_cursor and si<0xfb00 and back==v:
     if source_bytes[k]==255 and composed==o==v and oldcell is not None and oldcell[2]==v:
      published[at]=oldcell;cursor_publications['transparent-restore']+=1
     elif pair is not None and pair[:3]==(v,o,k) and composed==o and source_bytes[k]==o:
      published[at]=pair[3];cursor_publications['opaque-restore']+=1
    cursor_pairs_peak=max(cursor_pairs_peak,len(cursor_pairs))
    assert len(cursor_pairs)<=256,'cursor publication pair bound'
   if cs==0xe21 and ip==0x91 and code=='f3a503f3790c81ee00808cd981c10008' and es==0xa000 and 0<=delta<2 and si+delta<65536 and di+delta<64000 and src==base+at:
    got=owners.get(src)
    if got is not None and got[2]==v:
     published[at]=got;publication_sites['%04X:%04X'%(cs,ip)]+=1
   if oldcell is not None and at not in published:publication_losses['%04X:%04X'%(cs,ip)]+=1
  continue
 prior=owners.get(a);cell=None
 if cs==0xcba and ip in codes and code==codes[ip] and not flags&0x400:
  delta=a-(es*16+di);src=ds*16+si+delta
  width=1 if ip==0x9e else 2
  if 0<=delta<width and si+delta<65536 and di+delta<65536 and 0<=src<0xa0000:
   got=owners.get(src)
   if got is not None and got[2]==v and got[3]=='background':
    cell=got;copies['%04X:%04X:%s'%(cs,ip,'main' if base<=a<base+64000 else 'stage' if stage<=a<stage+64000 else 'backing')]+=1
 elif base<=a<base+64000 and cs==0xd21 and ip==0x12c and code==glyph and prior is not None and prior[2]==o:
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
assert call_next==len(calls)
required=[1265,1552]
assert all(any(p['sources'][rid]['painted']>0 for p in published_points) for rid in required)
out={'result':'PASS_PUBLISHED_TEXTURE_SOURCE_MODEL_RESEARCH','complete_decodes':dict(completed),'texture_sources':calls,'address_space':'dosgolem real-mode CS:IP and 20-bit linear RAM; no IDA EA','points':results,'copies':dict(copies),'loss_sites':dict(losses),'same_value_revocations':same,'cursor_paints':paints,'cursor_reverse_pair_restores':restores,'decode_writes':{rid:sum(c.values()) for rid,c in write_counts.items()},'cursor_source_sha256':cursor_source_sha,'remaining_backing_owners':sum(not(base<=a<base+64000 or stage<=a<stage+64000) for a in owners),'production_connected':False,'native_state_points_equal_control':len(points)}
if published_cursor:
 assert cursor_rows_used==len(cursor_rows)
 out['published_cursor']={'operations':dict(cursor_publications),'pending_peak':cursor_pairs_peak,'pending_remaining':len(cursor_pairs),'sidecar_rows':len(cursor_rows),'sidecar_sha256':sha((obs/'cursor-publication.jsonl').read_bytes()),'production_connected':False}
out['scope']=scope;out['required_sources']=required
if published_surface:
 out['published_surface']={'points':published_points,'copy_sites':dict(publication_sites),'revocations':dict(publication_losses),'production_connected':False}
 assert any('scene-load-slot' in p['label'] and p['sources'][1552]['painted']>0 for p in published_points)
out['receipt_sha256']={str(f):sha(f.read_bytes()) for f in [Path(__file__),a_points,obs.parent/'build.json',obs/'draws.json',ctrl/'draws.json',obs/'background.json',obs/'background-writes.jsonl',obs/'final.memory',ctrl/'final.memory',*([obs/'cursor-publication.jsonl'] if published_cursor else [])]}
(r/'check.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS_PUBLISHED_TEXTURE_SOURCE_MODEL_RESEARCH',len(results),dict(copies),dict(decodes),restores,flush=True)
