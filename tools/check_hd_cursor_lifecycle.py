"""R59唯讀游標收據：原始來源、逐寫、RAM複製及正常49點定位。"""
from pathlib import Path
from collections import Counter
import argparse,base64,hashlib,json,struct,sys

p=argparse.ArgumentParser(description=__doc__)
for name in ['observed','control','catalog','game','inputs','points','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();read=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
assert Path('/.dockerenv').is_file() and not a.output.exists()
for name in ['VICEROY.EXE','CURSOR.SS']:
 if not (a.game/name).is_file():print('SKIP：缺少合法原版 '+name);sys.exit(77)
obs,ctl=read(a.observed/'draws.json'),read(a.control/'draws.json')
points=read(a.points);inputs=read(a.inputs)['inputs'];catalog=read(a.catalog)
assert sha(a.inputs.read_bytes())==obs['input_sha256']==ctl['input_sha256']=='3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca'
assert sha(a.points.read_bytes())=='821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901'
source=next(x for x in catalog['frames'] if x['file']=='CURSOR.SS' and x['ordinal']==0)
raw=(a.catalog.parent/'pixels/0309.idx').read_bytes();assert len(raw)==289 and sha(raw)==source['indexed_sha256']
cursor_archive=(a.game/'CURSOR.SS').read_bytes();exe=(a.game/'VICEROY.EXE').read_bytes()
assert sha(cursor_archive)==source['file_sha256']=='3ff5a4b70f08780f845b1e973d7dce3ff34868bb73279174210fce76332fffcb'
assert sha(exe)=='a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3'
assert len(obs['checkpoints'])==len(ctl['checkpoints'])==len(points)==49 and obs['dos_inputs']==ctl['dos_inputs']==53 and obs['end']==ctl['end']
for left,right,point in zip(obs['checkpoints'],ctl['checkpoints'],points):
 assert all(left[k]==right[k] for k in right)
 assert left['steps']==point['step'] and all(left[k]==point[k] for k in ['memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags','dos_input_count'])
 for suffix in ['idx','canvas','stage','palette','cursor']:assert (a.observed/(left['snapshot_prefix']+'.'+suffix)).read_bytes()==(a.control/(right['snapshot_prefix']+'.'+suffix)).read_bytes()
assert (a.observed/'final.memory').read_bytes()==(a.control/'final.memory').read_bytes()
saves=lambda root:{str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
assert saves(a.observed/'saves')==saves(a.control/'saves')
converted=bytes(255 if x==253 else x for x in raw)
cursor=bytes(converted[y*17+x] for y in range(16) for x in range(16))
assert sha(cursor)=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
offset=exe.find(cursor);assert offset==122996 and exe.find(cursor,offset+1)<0
header=struct.unpack_from('<H',exe,8)[0]*16
assert header==9216 and offset-header+0x1100==0x1cd74
events=read(a.observed/'writes.json');calls=obs['calls'];assert len(calls)==2
load=[e for e in events if e['kind']=='cursor_ram' and e['site']=='9FDE:0002'];assert len(load)==256 and len({e['step'] for e in load})==1
assert [e['linear'] for e in load]==list(range(0x1cd74,0x1ce74)) and bytes(e['value'] for e in load)==cursor
source_summaries=[]
for n,c in enumerate(calls,1):
 assert c['source_encoded_sha256']==source['encoded_sha256']=='d77899f35c0e5f40780af7fddd6918c58ff86005de5ea4ecfbde34f5989e7dde'
 assert c['record_far']=='4F0B:0042' and c['source_far']=='4F10:000A' and c['record_words']==[10,20240,5,23,17,17]
 assert c['entry_code12']=='c828000052535057568b4702' and c['registers'][0]==1 and c['ds_bx_words']==[17,17,59216,7274]
 assert c['canvas_linear']==0x2adf0 and c['rect']==[0,0,17,17] and c['return_cs_ip']=='0C6E:0051'
 assert c['return_registers'][4]==c['registers'][4]+10 and 0<c['return_step']-c['entry_step']<100000
 before=base64.b64decode(c['private_before_roi'],validate=True);after=base64.b64decode(c['private_after_roi'],validate=True)
 assert before==bytes([255])*289 and after==converted
 writes=[e for e in events if e['kind']=='asset_draw' and e['call']==n]
 expected={c['canvas_linear']+k:v for k,v in enumerate(raw) if v!=253}
 assert len(writes)==len(expected)==84 and len({e['linear'] for e in writes})==84
 assert {e['linear']:e['value'] for e in writes}==expected
 assert all(e['old']==255 and c['entry_step']<=e['step']<c['return_step'] and e['site'] in {'0D46:0181','0D46:01B4','0D46:01D2'} for e in writes)
 copies=[e for e in events if e['kind']=='cursor_ram' and e['call']==n]
 assert len(copies)==256 and [e['linear'] for e in copies]==list(range(0x1cd74,0x1ce74))
 for e in copies:
  assert e['site']=='0C9F:00CA' and e['code64'].startswith('f3a503f3790c81ee00808cd981c100088ed9') and e['step']>c['return_step']
  es,cs,ss,ds=e['segments'];ax,cx,dx,bx,sp,bp,si,di=e['registers']
  delta=e['linear']-(es*16+di);k=e['linear']-0x1cd74;local=(k//16)*17+k%16
  assert 0<=delta<cx*2<=16 and ds*16+si+delta==c['canvas_linear']+local
  assert base64.b64decode(e['ds_si32'],validate=True)[delta]==converted[local]==e['value']==cursor[k]
 source_summaries.append({'entry_step':c['entry_step'],'return_step':c['return_step'],'source_writes':84,'ram_copy_writes':256,'copy_first_step':copies[0]['step'],'copy_last_step':copies[-1]['step']})
positions=[]
for i,point in enumerate(points):
 moves=[e for e in inputs[:point['dos_input_count']] if e['kind']=='move'];assert moves;mouse=moves[-1]
 x,y=mouse['x'],mouse['y'];name='point-%03d'%i
 native=(a.observed/(name+'.idx')).read_bytes();canvas=(a.observed/(name+'.canvas')).read_bytes();expected=bytearray(canvas)
 assert (a.observed/(name+'.cursor')).read_bytes()==cursor
 for k,v in enumerate(cursor):
  xx,yy=x+k%16,y+k//16
  if v!=255 and 0<=xx<320 and 0<=yy<200:expected[yy*320+xx]=v
 assert native==expected,(i,x,y)
 positions.append({'point':i,'step':point['step'],'mouse':[x,y],'source_hotspot':[0,0],'opaque_pixels':sum(v!=255 for v in cursor)})
report={'result':'PASS_STANDARD_CURSOR_ORIGINAL_SOURCE_RAM_AND_49_POSITIONS','inference':'confirmed within the fixed original version and 53-input normal path','file_sha256':{'VICEROY.EXE':sha(exe),'CURSOR.SS':sha(cursor_archive)},'source_indexed_sha256':sha(raw),'cursor_sha256':sha(cursor),'exe_constant_file_offset':offset,'exe_mz_header_bytes':header,'exe_load_linear':0x1100,'initial_load_step':load[0]['step'],'source_calls':source_summaries,'positions':positions,'original_state_and_saves_equal':True,'raw_events':len(events),'raw_event_counts':dict(Counter(e['kind'] for e in events)),'receipts_sha256':{str(p):sha(p.read_bytes()) for p in [a.observed/'draws.json',a.observed/'writes.json',a.control/'draws.json',a.catalog,a.inputs,a.points]},'limitations':['Not production HD; no new cursor artwork.','Edge clipping, hidden cursor and other cursor sources not established by these 49 points.','Legacy collector fields unique_writes, sorted_local_offset_value_sha256, transparent_background_unchanged and outside_rectangle_unchanged were not populated; this checker derives its own assertions from raw writes and ROI bytes.']}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['result'],sha(a.output.read_bytes()),flush=True)
