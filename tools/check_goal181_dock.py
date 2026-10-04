#!/usr/bin/env python3
"""Docker內驗收已取證的歐洲碼頭清單與輕帆船裝載標題。"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from check_goal134_window import load,same_state
from check_goal178_ship import png_for

EVIDENCE_SHA='9a17519fd79e2df51263ea271c5276d229a49e74791ba4f37d1a4e22eae0a051'
ROOTS={'purchase':'europe-purchase-formal-gui-v202','dock':'europe-dock-formal-gui-v203','build':'europe-dock-formal-build-v201','verify':'europe-dock-formal-verify-v204','ready':'europe-dock-profiles-v200','baseline':'trade-grid-build-v187'}
MISSIONARY_EVIDENCE_SHA='f78d6fd6c608e89aba8101a5f7cb17dd0eaddaca536956d668ca64d030efd4b3'
MISSIONARY_ROOTS={'gui':'europe-missionary-formal-gui-v213','build':'europe-missionary-formal-build-v212','verify':'europe-missionary-formal-verify-v214','ready':'europe-missionary-prototype-verify-v211','baseline':'europe-dock-formal-build-v201'}
FRONT_EVIDENCE_SHA='4b65c62b9c8c1840d79ae197605590d13e485dcdba01270717e9aa2536e3b5df'
FRONT_ROOTS={'gui':'europe-dock-seven-formal-gui-v224','build':'europe-dock-seven-formal-build-v223','verify':'europe-dock-seven-formal-verify-v225','ready':'europe-dock-seven-prototype-verify-v222','baseline':'europe-missionary-formal-build-v212'}
ARM='GAME.TXT:@ARMOPTIONS:0x000098AC'
ARM_SOURCE='GAME.TXT:@ARMOPTIONS'
LABEL='LABELS.TXT:@MISC:0x00000205'
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cp(d):return {x['step']:x for x in d[0]['checkpoints'] if x['label']!='final'}
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sav(p):return {f.name:SHA(f) for f in p.glob('*.SAV')}
def rect(r):return [r['Min']['X'],r['Min']['Y'],r['Max']['X'],r['Max']['Y']]
def active_fields(events):
 latest={};active=set()
 for e in events:
  cid=e.get('candidate_id')
  if e.get('stage')=='source':latest[cid]=e
  if e.get('stage')=='active' and cid in latest:
   s=latest[cid]
   if e.get('shown',s['shown'])==s['shown']:active.add((cid,s['shown'],tuple(s['safe'])))
 return active
def inside(diff,areas):
 for safe in areas:
  x0,y0,x1,y1=[v*4 for v in safe];ImageDraw.Draw(diff).rectangle((x0,y0,x1-1,y1-1),fill=(0,0,0))
 assert diff.getbbox() is None,'中文安全區外改變'

def check(b,o,side):
 g=b/ROOTS[side];build=b/ROOTS['build'];proof=json.loads((o/'gui-integrity.json').read_text())[side]
 docs={tag:load(o/(side+'-'+tag)) for tag in ['zh','control','observer','baseline','noatlas']};gui=load(g/'gui-colony');control=docs['control'];shots=proof['shots']
 assert len(shots)==(16 if side=='purchase' else 29) and SHA(g/'gui-colony.inputs.json')==proof['inputs_sha256']
 assert gui[0]['state']['steps']==proof['end'] and gui[0]['state']['memory_sha256']==proof['memory_sha256']
 assert dict((n,int(s)) for n,s in [x.split() for x in (g/'gui-colony.shots').read_text().splitlines()])==shots
 for tag,d in dict(docs,gui=gui).items():
  if tag!='control':same_state(d,control,side+tag+' 原版狀態改變')
  assert sav(g/'scratch' if tag=='gui' else o/(side+'-'+tag+'-save'))==proof['saves'],tag+' 存檔改變'
  if tag!='gui':
   for ext in ['json','memory']:assert SHA(g/(tag+'.'+ext))==SHA(o/(side+'-'+tag+'.'+ext)),'矩陣收據連結不同'
 assert proof['saves']['COLONY03.SAV']=='d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
 cps={tag:cp(d) for tag,d in docs.items()}
 for tag,rows in cps.items():
  assert set(rows)==set(shots.values()),tag+' 取樣不足'
  for step,c in rows.items():assert all(c[k]==cps['control'][step][k] for k in ['memory_sha256','raw_sha256','palette_sha256']),tag+' 原始畫面不同'
 events=docs['zh'][0]['events'];active=active_fields(events);source=[e for e in events if e.get('stage')=='source' and str(e.get('candidate_id','')).startswith(ARM+'#')]
 runs=lines(o/('sea-'+side+'-observer-measure/runs.jsonl'));measures=lines(o/('sea-'+side+'-observer-measure/lines.jsonl'))
 layouts=json.loads((b/ROOTS['ready']/'profiles-layout.json').read_text());profiles={x['shown']:x for x in layouts};assert len(profiles)==6
 for e in source:
  raw=[x for x in runs if x['start']==e['step'] and x['base']==e['source_linear'] and x['shown']==e['shown']];assert len(raw)==1
  r=raw[0];assert e['entry_ip']=='0D21:00C6' and e['items']==[x['shown'] for x in r['lines']]
  assert (r['normal_c'],r['accent_c'],r['shadow_c'])==(68,149,47)
  assert all(l['cap_h']==8 and l['box']['Min']['X']==82 for l in r['lines'])
  assert e['shown'] in profiles and e['font_px']==30 and e['safe']==rect(profiles[e['shown']]['safe'])
  mm=[x for x in measures if x['start']==e['step'] and x['base']==e['source_linear'] and x['shown']==e['shown']];assert len(mm)==1
  m=mm[0];assert m['actual_px']==30 and m['cap_h']==8 and m['pitch']==12 and m['overflow_px']==0 and rect(m['safe'])==e['safe']
  assert [x['candidate_px'] for x in m['candidate_sizes']]==list(range(30,19,-1)) and rect(m['actual_ink'])==rect(profiles[e['shown']]['ink'])
  assert (e['candidate_id'],e['shown'],tuple(e['safe'])) in active,'清單未啟用'
 assert source and len({e['shown'] for e in source})==(1 if side=='purchase' else 6)
 lookups=json.loads((o/(side+'-source/source-query.log.matches.json')).read_text())
 assert lookups['final_step']==proof['end'] and lookups['memory_sha256']==proof['memory_sha256'] and lookups['inputs_sha256']==proof['inputs_sha256']
 assert sav(o/(side+'-source/scratch'))==proof['saves']
 matches=[x for x in lookups['matches'] if x['header']==x['key']=='@ARMOPTIONS'];assert len(matches)==(1 if side=='purchase' else 9)
 assert all(x['code_bytes']=='f3a6' and x['original_cs_ip']=='0E2D:0832' and x['file_op']['Name']=='GAME.TXT' and x['file_op']['Pos']<=39071<x['file_op']['Pos']+x['file_op']['Len'] for x in matches)
 captures=lines(g/'gui-colony.capture-attempts.jsonl');changed=[];fields=[];seen=set();areas={}
 for name,step in shots.items():
  ims={tag:Image.open(png_for(o,side+'-'+tag,rows[step])).convert('RGB') for tag,rows in cps.items()};normal=Image.open(g/f'gui-colony.{name}.png').convert('RGB');z=ims['zh']
  cap=[x for x in captures if x['name']==name and x['aligned']];assert len(cap)==1
  c=cap[0];assert c['stable'] and c['frame_step']==step and c['canvas_size']==c['capture_size']==list(normal.size)==[1280,800]
  assert hashlib.sha256(normal.convert('RGBA').tobytes()).hexdigest()==c['canvas_rgba_sha256']==c['capture_rgba_sha256']
  assert ImageChops.difference(z,normal).getbbox() is None and ImageChops.difference(z,ims['observer']).getbbox() is None,name+' GUI或觀測畫面不同'
  allowed=[]
  if name.endswith('-options') or name=='dock-options':
   es=[e for e in source if e['step']<=step];assert es; e=es[-1];assert step-e['step']<10000000;allowed=[e['safe']]
   box=tuple(v*4 for v in e['safe']);assert ImageChops.difference(z,ims['control']).crop(box).getbbox() is not None
   assert ImageChops.difference(ims['noatlas'],ims['control']).crop(box).getbbox() is None
   if e['shown'] not in seen:fields.append({'candidate_id':e['candidate_id'],'shown':e['shown'],'safe':e['safe'],'source_ids':[ARM_SOURCE]});seen.add(e['shown'])
  if side=='purchase' and name=='caravel-purchased':
   allowed=[[153,119,214,127]];box=tuple(v*4 for v in allowed[0]);assert ImageChops.difference(z,ims['control']).crop(box).getbbox() is not None
   assert ImageChops.difference(ims['noatlas'],ims['control']).crop(box).getbbox() is None,'缺圖集仍殘留舊港口中文'
  diff=ImageChops.difference(z,ims['baseline'])
  if diff.getbbox() is not None:changed.append(name)
  inside(diff,allowed);areas[name]=allowed
 if side=='purchase':
  assert changed==['dock-options','caravel-purchased']
  headers=[e for e in events if e.get('stage')=='source' and e.get('candidate_id')=='STRING:template:cargo-loading-header' and e.get('shown')=='Loading:  Caravel'];assert len(headers)==1
  e=headers[0];assert e['zh']=='裝載中：輕帆船' and e['safe']==[153,119,214,127] and e['font_px']==22 and e['entry_ip']=='0D21:00C6'
  assert (e['candidate_id'],e['shown'],tuple(e['safe'])) in active,'港口標題未啟用'
  assert any(x.get('stage')=='expired' and x.get('reason')=='superseded' and x.get('shown')=='No Ships In Port' for x in events)
  ms=lines(o/'sea-purchase-observer-measure/strings.jsonl');mm=[x for x in ms if x['shown']==e['shown'] and x['start']==e['step'] and x['base']==e['source_linear']];assert len(mm)==1;m=mm[0]
  assert m['actual_px']==22 and m['cap_h']==5 and m['overflow_px']==0 and rect(m['face'])==[154,120,213,126] and rect(m['safe'])==e['safe']
  assert [x['candidate_px'] for x in m['candidate_sizes']]==list(range(22,14,-1)) and rect(m['actual_ink'])==[5,4,170,25]
  q=json.loads((o/'purchase-concat/source-query.log.matches.json').read_text());assert (q['inputs_sha256'],q['final_step'],q['memory_sha256'])==(proof['inputs_sha256'],proof['end'],proof['memory_sha256']) and sav(o/'purchase-concat/scratch')==proof['saves']
  raw=lines(o/'purchase-concat/source-query.log.concat.jsonl');parts=[x for x in raw if x.get('original_cs_ip')=='0E2D:11CF' and x.get('destination_parameter_linear')==175678]
  assert [(x['source_parameter_linear'],x['source_now'],x['destination_now']) for x in parts]==[(317818,'Loading',''),(316238,'Caravel','Loading:  ')]
  assert all(x['code_bytes'][16:52]=='f2aef7d12bf98cc08ed88e460887fe8b4606' for x in parts)
  first=[x for x in lines(o/'purchase-concat/source-query.log.cargo.jsonl') if x['shown']=='Loading:  Caravel'];assert len(first)==1;f=first[0]
  assert f['entry_cs_ip']==e['entry_ip'] and f['source_linear']==e['source_linear'] and f['step']==e['step']
  snapshot=Path(f['snapshot']);snapshot=snapshot if snapshot.is_absolute() else o/'purchase-concat'/snapshot;mem=snapshot.read_bytes();readz=lambda a:mem[a:a+128].split(b'\0',1)[0]
  assert readz(175510)==readz(175678)==b'Loading:  Caravel' and readz(317818)==b'Loading' and readz(316238)==b'Caravel'
  fields.append({'candidate_id':e['candidate_id'],'shown':e['shown'],'safe':e['safe'],'source_ids':[LABEL]})
 else:assert changed==[n for n in shots if n.endswith('-options')]
 negative=docs['noatlas'][0]['events'];assert not any(e.get('stage')=='source' and (str(e.get('candidate_id','')).startswith(ARM+'#') or e.get('shown')=='Loading:  Caravel' and e.get('candidate_id')=='STRING:template:cargo-loading-header') for e in negative)
 assert (build/'tests.log').read_text().count('--- PASS:')==123 and '--- SKIP:' not in (build/'tests.log').read_text()
 assert (build/'build-entry-tests.log').read_text().count('--- PASS:')==113 and '--- SKIP:' not in (build/'build-entry-tests.log').read_text()
 for n in ['dialog.go','strings.go','adapter.go']:assert (build/n).read_bytes()==(build/'stable-build'/n).read_bytes()
 return {'result':'PASS','grade':'confirmed','side':side,'field_count':len(fields),'verified_fields':fields,'normal_GUI':len(shots),'original_final_sides':6,'inputs_sha256':proof['inputs_sha256'],'all_saves':proof['saves'],'changed_shots':changed,'areas':areas,'final_step':proof['end'],'final_memory_sha256':proof['memory_sha256'],'evidence_sha256':EVIDENCE_SHA,'scope':'僅六種完整碼頭清單與固定Caravel歐洲裝載標題；未驗傳教士取消、移到碼頭最前面或其他船型'}

def verify(game,root,out,side,freeze_required=True):
 b=out.parent;assert root.resolve()==(b/ROOTS[side]).resolve(),'GUI來源不同'
 if freeze_required:
  assert SHA(out/'batch.json')==EVIDENCE_SHA,'reviewed manifest differs'
  batch=json.loads((out/'batch.json').read_text());assert batch['schema']==1 and batch['roots']==ROOTS
  for name,digest in batch['original_files'].items():assert SHA(game/name)==digest,('original version differs',name)
  for key,files in batch['artifact_hashes'].items():
   for rel,digest in files.items():
    p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
    assert SHA(b/ROOTS[key]/p)==digest,('receipt differs',key,rel)
 assert json.loads((b/ROOTS['ready']/'ready-evidence.json').read_text())['status']=='READY_LIMITED_EVIDENCE_REVIEW'
 return check(b,out,side)

def verify_missionary(game,root,out,freeze_required=True,side='missionary'):
 assert side in ['missionary','front'];front=side=='front'
 b=out.parent;roots=FRONT_ROOTS if front else MISSIONARY_ROOTS;g=b/roots['gui'];build=b/roots['build']
 evidence=FRONT_EVIDENCE_SHA if front else MISSIONARY_EVIDENCE_SHA
 needle='Move to front of dock.' if front else 'Cancel Missionary Status.'
 names=['rear-dock-options','old-rear-options'] if front else ['missionary-on-options','missionary-off-options']
 safe=[81,66,236,150] if front else [81,90,205,126];profile_count=1 if front else 2
 assert root.resolve()==g.resolve(),'GUI來源不同'
 if freeze_required:
  assert SHA(out/'batch.json')==evidence,'reviewed manifest differs'
  batch=json.loads((out/'batch.json').read_text());assert batch['schema']==1 and batch['roots']==roots
  for name,digest in batch['original_files'].items():assert SHA(game/name)==digest,('original version differs',name)
  for key,files in batch['artifact_hashes'].items():
   for rel,digest in files.items():
    p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
    assert SHA(b/roots[key]/p)==digest,('receipt differs',key,rel)
 assert json.loads((b/roots['ready']/'ready-evidence.json').read_text())['status']==('READY_ONE_SEVEN_DOCK_FIELD' if front else 'READY_TWO_MISSIONARY_FIELDS')
 proof=json.loads((out/'gui-integrity.json').read_text());shots=proof['shots'];assert len(shots)==19
 assert proof['root']==g.name and SHA(g/'gui-colony.inputs.json')==proof['inputs_sha256']
 assert dict((n,int(s)) for n,s in [x.split() for x in (g/'gui-colony.shots').read_text().splitlines()])==shots
 docs={tag:load(out/tag) for tag in ['zh','control','observer','baseline','noatlas']};gui=load(g/'gui-colony');control=docs['control']
 assert gui[0]['state']['steps']==proof['end'] and gui[0]['state']['memory_sha256']==proof['memory_sha256']
 for tag,d in dict(docs,gui=gui).items():
  if tag!='control':same_state(d,control,tag+' 原版狀態改變')
  assert sav(g/'scratch' if tag=='gui' else out/(tag+'-save'))==proof['saves'],tag+' 存檔改變'
  if tag!='gui':
   for ext in ['json','memory']:assert SHA(g/(tag+'.'+ext))==SHA(out/(tag+'.'+ext)),'矩陣收據連結不同'
 assert proof['saves']['COLONY03.SAV']=='d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
 cps={tag:cp(d) for tag,d in docs.items()}
 for tag,rows in cps.items():
  assert set(rows)==set(shots.values()),tag+' 取樣不足'
  for step,c in rows.items():assert all(c[k]==cps['control'][step][k] for k in ['memory_sha256','raw_sha256','palette_sha256']),tag+' 原始畫面不同'
 events=docs['zh'][0]['events'];active=active_fields(events)
 source=[e for e in events if e.get('stage')=='source' and str(e.get('candidate_id','')).startswith(ARM+'#') and needle in e.get('shown','')]
 layouts=json.loads((build/('seven-layout.json' if front else 'missionary-layout.json')).read_text());profiles={x['shown']:x for x in layouts};assert len(profiles)==profile_count
 runs=lines(out/'sea-observer-measure/runs.jsonl');measures=lines(out/'sea-observer-measure/lines.jsonl')
 for e in source:
  raw=[x for x in runs if x['start']==e['step'] and x['base']==e['source_linear'] and x['shown']==e['shown']];assert len(raw)==1
  r=raw[0];assert e['entry_ip']=='0D21:00C6' and e['items']==[x['shown'] for x in r['lines']]
  assert (r['normal_c'],r['accent_c'],r['shadow_c'])==(68,149,47)
  assert [l['box']['Min']['Y'] for l in r['lines']]==(list(range(67,140,12)) if front else [91,103,115]) and all(l['cap_h']==8 and l['box']['Min']['X']==82 for l in r['lines'])
  assert e['shown'] in profiles and e['font_px']==30 and e['safe']==rect(profiles[e['shown']]['safe'])==safe
  mm=[x for x in measures if x['start']==e['step'] and x['base']==e['source_linear'] and x['shown']==e['shown']];assert len(mm)==1;m=mm[0]
  assert m['actual_px']==30 and m['cap_h']==8 and m['pitch']==12 and m['overflow_px']==0 and rect(m['safe'])==e['safe']
  assert [x['candidate_px'] for x in m['candidate_sizes']]==list(range(30,19,-1)) and rect(m['actual_ink'])==rect(profiles[e['shown']]['actual_ink'])
  assert (e['candidate_id'],e['shown'],tuple(e['safe'])) in active,'清單未啟用'
 assert source and set(e['shown'] for e in source)==set(profiles)
 queries=json.loads((out/'source/source-query.log.matches.json').read_text())
 assert (queries['final_step'],queries['memory_sha256'],queries['inputs_sha256'])==(proof['end'],proof['memory_sha256'],proof['inputs_sha256']) and sav(out/'source/scratch')==proof['saves']
 matches=[x for x in queries['matches'] if x['header']==x['key']=='@ARMOPTIONS'];assert len(matches)==(3 if front else 4)
 assert all(x['code_bytes']=='f3a6' and x['original_cs_ip']=='0E2D:0832' and x['file_op']['Name']=='GAME.TXT' and x['file_op']['Pos']<=39071<x['file_op']['Pos']+x['file_op']['Len'] for x in matches)
 captures=lines(g/'gui-colony.capture-attempts.jsonl');changed=[];fields=[];seen=set();areas={}
 for name,step in shots.items():
  ims={tag:Image.open(png_for(out,tag,rows[step])).convert('RGB') for tag,rows in cps.items()};normal=Image.open(g/f'gui-colony.{name}.png').convert('RGB');z=ims['zh']
  caps=[x for x in captures if x['name']==name and x['aligned']];assert len(caps)==1;c=caps[0]
  assert c['stable'] and c['frame_step']==step and c['canvas_size']==c['capture_size']==list(normal.size)==[1280,800]
  assert hashlib.sha256(normal.convert('RGBA').tobytes()).hexdigest()==c['canvas_rgba_sha256']==c['capture_rgba_sha256']
  assert ImageChops.difference(z,normal).getbbox() is None and ImageChops.difference(z,ims['observer']).getbbox() is None,name+' GUI或觀測畫面不同'
  allowed=[]
  if name in names:
   es=[e for e in source if e['step']<=step];assert es;e=es[-1];assert step-e['step']<10000000;allowed=[e['safe']]
   box=tuple(v*4 for v in e['safe']);assert ImageChops.difference(z,ims['control']).crop(box).getbbox() is not None
   assert ImageChops.difference(ims['noatlas'],ims['control']).crop(box).getbbox() is None,'缺圖集未回原文'
   if e['shown'] not in seen:fields.append({'candidate_id':e['candidate_id'],'shown':e['shown'],'safe':e['safe'],'source_ids':[ARM_SOURCE]});seen.add(e['shown'])
  diff=ImageChops.difference(z,ims['baseline'])
  if diff.getbbox() is not None:changed.append(name)
  inside(diff,allowed);areas[name]=allowed
 assert changed==names and len(fields)==profile_count
 restored_name='moved-first-options' if front else 'restored-colonist-options'
 restored=[r for r in runs if r['start']<=shots[restored_name] and len(r['lines'])==6 and r['lines'][0]['shown']==("Don't get on next ship." if front else 'Board next ship.')]
 assert restored and shots[restored_name]-restored[-1]['start']<10000000
 assert restored[-1]['lines'][-2]['shown']=='Bless as Missionaries.' and restored[-1]['lines'][-1]['shown']=='No changes.'
 if front:assert shots[names[0]]<shots['move-front-result']<shots[restored_name]<shots[names[1]]
 assert not any(e.get('stage')=='source' and needle in e.get('shown','') for e in docs['noatlas'][0]['events'])
 for log,count in [('tests.log',125 if front else 124),('build-entry-tests.log',113)]:
  s=(build/log).read_text();assert s.count('--- PASS:')==count and '--- SKIP:' not in s
 for n in ['dialog.go','strings.go','adapter.go']:assert (build/n).read_bytes()==(build/'stable-build'/n).read_bytes()
 assert (build/'font/string-atlas.json').read_bytes()==(b/roots['baseline']/'font/string-atlas.json').read_bytes()
 scope='僅一種已觀測七列碼頭清單與正常移到最前面後兩清單；未驗Board七列或單位標題' if front else '僅兩種已觀測傳教士三列清單與正常取消後復原；未驗移到碼頭最前面或單位標題'
 return {'result':'PASS','grade':'confirmed','side':side,'field_count':profile_count,'verified_fields':fields,'normal_GUI':19,'original_final_sides':6,'inputs_sha256':proof['inputs_sha256'],'all_saves':proof['saves'],'changed_shots':changed,'areas':areas,'final_step':proof['end'],'final_memory_sha256':proof['memory_sha256'],'evidence_sha256':evidence,'scope':scope}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['game','reports','evidence']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--side',choices=['purchase','dock','missionary','front'],required=True);a=p.parse_args()
 if any(not(a.game/n).is_file() for n in ['OPENING.EXE','VICEROY.EXE','MENU.TXT','GAME.TXT','LABELS.TXT','NAMES.TXT','COLONY.TXT']):print('SKIP：缺合法原版，未驗收碼頭清單');return 77
 try:r=verify_missionary(a.game,a.reports,a.evidence,side=a.side) if a.side in ['missionary','front'] else verify(a.game,a.reports,a.evidence,a.side)
 except (OSError,ValueError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
 print(json.dumps(r,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
