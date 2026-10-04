#!/usr/bin/env python3
"""Docker內驗收第一貿易路線的正常海陸GUI、原版狀態與存檔。"""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image,ImageChops
from check_goal134_window import load,same_state
from check_goal178_ship import png_for
EVIDENCE_SHA='ae74120db1d7534117e003d80f72978b9df57282fe976c110a0a408912512cf4'
ROOTS={'sea': 'trade-port-role-sea-gui-v176', 'land': 'trade-port-role-land-gui-v177', 'build': 'trade-port-role-build-v175', 'native': 'trade-native-source-v161', 'scope': 'trade-title-scope-verify-v165', 'same_name': 'trade-same-name-verify-v167', 'verify': 'trade-port-role-formal-v178', 'role': 'trade-port-role-verify-v174'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(game,root,out,side):
 assert root.resolve()==(out.parent/ROOTS[side]).resolve(),'GUI root does not match side'
 assert sha(out/'batch.json')==EVIDENCE_SHA,'reviewed manifest differs'
 batch=json.loads((out/'batch.json').read_text())
 assert batch['schema']==1 and batch['roots']==ROOTS
 b=out.parent;build=b/ROOTS['build']
 for name,digest in batch['original_files'].items():assert sha(game/name)==digest,('original version differs',name)
 for key,files in batch['artifact_hashes'].items():
  for rel,digest in files.items():
   p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
   assert sha(b/ROOTS[key]/p)==digest,('receipt differs',key,rel)
 integrity=json.loads((out/'gui-integrity.json').read_text())
 assert json.loads((b/ROOTS['role']/'role-summary.json').read_text())['result']=='PASS_PRIVATE_INDEXED_PORT_ROLE'
 source=json.loads((b/'trade-native-source-v161/source-summary.json').read_text());assert source['result']=='PASS_REPLAY_SOURCE_AND_LAYOUT'
 summaries={};scopes={}
 new_ids={'STRING:template:route-editor-title','STRING:dictionary:route-land','GAME.TXT:@CARGOLOAD:0x0000862B','GAME.TXT:@CARGOUNLOAD:0x0000866E'}
 for side,version,count in [(side,176 if side=='sea' else 177,21 if side=='sea' else 19)]:
  root=b/f'trade-port-role-{side}-gui-v{version}';control=load(root/'control')
  docs={tag:load(root/tag) for tag in ['gui-colony','zh','observer','noatlas','v152']}
  for tag,d in docs.items():same_state(d,control,side+tag+' changed original state')
  assert sha(root/'gui-colony.inputs.json')==integrity[side]['inputs_sha256'] and docs['zh'][0]['state']['steps']==integrity[side]['end']
  shots={n:int(s) for n,s in [x.split() for x in (root/'gui-colony.shots').read_text().splitlines()]};assert len(shots)==count
  cps={tag:{c['step']:c for c in d[0]['checkpoints'] if c['label']!='final'} for tag,d in dict(docs,**{'control':control}).items() if tag!='gui-colony'}
  for tag,rows in cps.items():
   assert set(rows)==set(shots.values()),(side,tag)
   for step,row in rows.items():assert all(row[k]==cps['control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256')),(side,tag,step)
  receipts=[json.loads(l) for l in (root/'gui-colony.capture-attempts.jsonl').read_text().splitlines()]
  for tag in docs.keys()|{'control'}:
   folder=root/('scratch' if tag=='gui-colony' else tag+'-save')
   assert {p.name:sha(p) for p in folder.glob('*.SAV')}==integrity[side]['saves'],(side,tag,'save changed')
  assert set(integrity[side]['saves'])=={'COLONY00.SAV','COLONY03.SAV'}
  assert integrity[side]['saves']['COLONY03.SAV']=='d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
  editor_names={'sea':{'same-name-editor','same-name-load-options','same-name-load-furs','same-name-unload-options','same-name-port-options','same-name-london-selected'},'land':{'land-editor','land-destination-options','land-deleted-destination'}}[side]
  changed=[];areas_by_name={}
  for name,step in shots.items():
   images={tag:Image.open(png_for(root,tag,rows[step])).convert('RGB') for tag,rows in cps.items()}
   z=images['zh'];gui=Image.open(root/f'gui-colony.{name}.png').convert('RGB')
   rs=[x for x in receipts if x['name']==name and x['aligned']];assert len(rs)==1 and rs[0]['frame_step']==step and rs[0]['stable']
   assert hashlib.sha256(gui.convert('RGBA').tobytes()).hexdigest()==rs[0]['canvas_rgba_sha256']==rs[0]['capture_rgba_sha256']
   assert ImageChops.difference(z,gui).getbbox() is None,(side,name,'GUI mismatch')
   assert ImageChops.difference(z,images['observer']).getbbox() is None,(side,name,'observer changed display')
   areas=[]
   if name in editor_names:
    areas.append([127,4,193,11])
    if side=='land':areas.append([54,32,71,39])
   if name in {'same-name-load-options','same-name-unload-options'}:areas.append([100,27,219,44])
   if name=='same-name-port-options':areas.append([76,90,171,126])
   events=docs['zh'][0]['events']
   source_safes={tuple(e['safe']) for e in events if e.get('stage')=='source' and e.get('step',0)<=step and 'safe' in e and (e['candidate_id'] in new_ids or (e['candidate_id']=='STRING:line+list' and e['safe']==[76,90,171,126]))}
   assert all(tuple(safe) in source_safes for safe in areas),(side,name,'unbound scoped area')
   if ImageChops.difference(z,images['v152']).getbbox():changed.append(name)
   masked=z.copy()
   for safe in areas:
    box=tuple(v*4 for v in safe)
    assert ImageChops.difference(images['noatlas'].crop(box),images['control'].crop(box)).getbbox() is None,(side,name,'missing atlas fallback')
    masked.paste(images['v152'].crop(box),box)
   assert ImageChops.difference(masked,images['v152']).getbbox() is None,(side,name,'changed outside scope',ImageChops.difference(masked,images['v152']).getbbox())
   if side=='sea' and name in editor_names-{'same-name-load-options','same-name-unload-options'}:
    box=(216,96,480,124)
    assert ImageChops.difference(z.crop(box),images['control'].crop(box)).getbbox() is None,(name,'player name changed')
   if areas:areas_by_name[name]=areas
  assert set(changed)==editor_names,(side,'unexpected changed shots',changed)
  titles=[e for e in events if e.get('stage')=='source' and e['candidate_id']=='STRING:template:route-editor-title']
  assert titles and all(e['safe']==[127,4,193,11] and e['shown']=='EDIT TRADE ROUTE 1' and e['font_px']==22 for e in titles)
  if side=='land':
   land=[e for e in events if e.get('stage')=='source' and e['candidate_id']=='STRING:dictionary:route-land']
   assert land and all(e['safe']==[54,32,71,39] and e['font_px']==22 and e['shown']=='Land' and e['zh']=='陸上' for e in land)
  summaries[side]=dict(integrity[side],full_original_sides=6,all_GUI_equal_replay=True,all_checkpoint_original_states_equal=True,changed_shots=changed)
  scopes[side]=areas_by_name
 paragraphs={}
 for line in (out/'sea-observer-measure/paragraphs.jsonl').read_text().splitlines():
  row=json.loads(line);paragraphs.setdefault(row['shown'],row)
 assert len(paragraphs)==2
 for row in paragraphs.values():assert row['actual_px']==22 and row['cap_h']==5 and row['overflow_px']==0 and row['safe']=={'Min':{'X':100,'Y':27},'Max':{'X':219,'Y':44}}
 assert (build/'tests.log').read_text().count('--- PASS:')==113 and '--- SKIP:' not in (build/'tests.log').read_text()
 assert (build/'stable-build/adapter.go').read_bytes()==(build/'adapter.go').read_bytes() and (build/'stable-build/strings.go').read_bytes()==(build/'strings.go').read_bytes()
 old=json.loads((b/'cargo-messages-formal-build-v152/font/string-atlas.json').read_text());new=json.loads((build/'font/string-atlas.json').read_text());assert old['sizes']==new['sizes'] and old['charset_sha256']==new['charset_sha256']

 profiles=[
  ('EDIT TRADE ROUTE 1',[127,4,193,11],'LABELS.TXT:@ROUTE:0x00000AF9'),
  ('Route Name:',[9,24,51,32],'LABELS.TXT:@ROUTE:0x00000B0B'),
  ('Route Type:',[9,32,49,40],'LABELS.TXT:@ROUTE:0x00000B18'),
  ('Sea' if side=='sea' else 'Land',[54,32,67,39] if side=='sea' else [54,32,71,39],'LABELS.TXT:@ROUTE:0x00000B25' if side=='sea' else 'LABELS.TXT:@ROUTE:0x00000B2A'),
  ('Destination',[20,48,59,56],'LABELS.TXT:@ROUTE:0x00000B30'),
  ('Unload Cargo',[124,48,169,56],'LABELS.TXT:@ROUTE:0x00000B3D'),
  ('Load Cargo',[207,48,246,56],'LABELS.TXT:@ROUTE:0x00000B4B'),
 ]
 if side=='sea':profiles.extend([
  ('Select a cargo to load at Jamestown.',[100,27,219,44],'GAME.TXT:@CARGOLOAD:0x0000862B'),
  ('Select a cargo to unload at Jamestown.',[100,27,219,44],'GAME.TXT:@CARGOUNLOAD:0x0000866E'),
 ])
 profiles.append(('London (England) Jamestown (Delete Destination)' if side=='sea' else 'Jamestown (Delete Destination)',[76,90,171,126] if side=='sea' else [76,96,171,120],'LABELS.TXT:@ROUTE:0x00000B57'))
 verified=[]
 events=docs['zh'][0]['events']
 for text,safe,cid in profiles:
  rows=[e for e in events if e.get('stage')=='source' and e.get('shown','').strip()==text and e.get('safe')==safe]
  assert rows,('missing reviewed source field',text,safe)
  e=rows[0]
  assert e['entry_ip']=='0D21:00C6' and e['font_px']==(30 if cid.endswith('0x00000B57') else 22)
  assert any(a.get('stage')=='active' and a['candidate_id']==e['candidate_id'] and a.get('step',0)>=e['step'] for a in events),('no active field',text)
  if cid.startswith('LABELS.'):
   assert cid in source['raw_pool_reads'] and source['raw_pool_reads'][cid]
  verified.append({'candidate_id':e['candidate_id'],'shown':e['shown'],'safe':safe,'source_ids':[cid.rsplit(':',1)[0] if cid.startswith('GAME.TXT:@CARGO') else cid]})
 result={'result':'PASS','grade':'confirmed','verified_fields':verified,'inputs_sha256':integrity[side]['inputs_sha256'],'final_step':integrity[side]['end'],'final_memory_sha256':integrity[side]['memory_sha256'],'field_count':len(verified),'original_final_sides':6,'normal_GUI':integrity[side]['normal_GUI'],'scope':batch['scope'],'side':side,'evidence_sha256':EVIDENCE_SHA,'all_saves':integrity[side]['saves']}
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['game','reports','evidence']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--side',choices=['sea','land'],required=True);a=p.parse_args()
 required=['OPENING.EXE','VICEROY.EXE','MENU.TXT','GAME.TXT','LABELS.TXT','NAMES.TXT']
 if any(not(a.game/n).is_file() for n in required):print('SKIP：缺合法原版，未驗收貿易路線');return 77
 try:result=verify(a.game,a.reports,a.evidence,a.side)
 except (OSError,ValueError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
 print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
