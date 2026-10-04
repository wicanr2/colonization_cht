#!/usr/bin/env python3
"""Docker內驗收第一路線城市欄；收據與原版版本綁定。"""
from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageChops
sys.path.insert(0,'/repo/tools')
from check_goal134_window import load,same_state
from check_goal178_ship import png_for
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(b,out,side):
 version=188 if side=='sea' else 189;count=21 if side=='sea' else 19
 gui=b/f'trade-grid-{side}-gui-v{version}';build=b/'trade-grid-build-v187';control=load(gui/'control');old=load(gui/'v175')
 docs={tag:load(gui/tag) for tag in ['zh','observer','noatlas','gui-colony','v175']}
 integrity=json.loads((out/'gui-integrity.json').read_text())[side]
 assert sha(gui/'gui-colony.inputs.json')==integrity['inputs_sha256'] and docs['gui-colony'][0]['state']['steps']==integrity['end']
 shots=dict((n,int(s)) for n,s in [x.split() for x in (gui/'gui-colony.shots').read_text().splitlines()]);assert len(shots)==count
 cps={tag:{c['step']:c for c in d[0]['checkpoints'] if c['label']!='final'} for tag,d in dict(docs,control=control).items() if tag!='gui-colony'}
 for tag,d in docs.items():same_state(d,control,side+tag+' changed original state')
 for tag,rows in cps.items():
  assert set(rows)==set(shots.values())
  for step,cp in rows.items():assert all(cp[k]==cps['control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256'))
 for tag in docs.keys()|{'control'}:
  folder=gui/('scratch' if tag=='gui-colony' else tag+'-save');assert {p.name:sha(p) for p in folder.glob('*.SAV')}==integrity['saves']
 assert integrity['saves']['COLONY03.SAV']=='d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
 budget={'1.  Jamestown':[10,68,114,76],'2.  Jamestown':[9,88,114,96]};events=docs['zh'][0]['events'];fields=[]
 for text,area in budget.items():
  rows=[e for e in events if e.get('candidate_id')=='STRING:route-grid-colony' and e.get('shown')==text and e.get('stage')=='source'];assert rows
  safes={tuple(e['safe']) for e in rows};assert len(safes)==1;safe=next(iter(safes));assert safe[:2]==tuple(area[:2]) and safe[2]<=area[2] and safe[3]==area[3]
  assert all(e['font_px']==22 and e['entry_ip']=='0D21:00C6' and e['zh']==text[:4]+'詹姆斯敦（Jamestown）' for e in rows)
  assert any(e.get('stage')=='active' and e.get('candidate_id')=='STRING:route-grid-colony' and e.get('shown')==text for e in events)
  fields.append({'candidate_id':'STRING:route-grid-colony','shown':text,'safe':list(safe),'source_ids':['COLONY.TXT:@ENGLISH:0x0000011B']})
 names={'sea':{'same-name-editor','same-name-load-options','same-name-load-furs','same-name-unload-options','same-name-port-options','same-name-london-selected'},'land':{'land-editor','land-destination-options','land-deleted-destination'}}[side]
 receipts=[json.loads(x) for x in (gui/'gui-colony.capture-attempts.jsonl').read_text().splitlines()];changed=[];areas={}
 for name,step in shots.items():
  images={tag:Image.open(png_for(gui,tag,cps[tag][step])).convert('RGB') for tag in cps};z=images['zh'];normal=Image.open(gui/f'gui-colony.{name}.png').convert('RGB')
  rs=[x for x in receipts if x['name']==name and x['aligned']];assert len(rs)==1 and rs[0]['frame_step']==step and rs[0]['stable']
  assert hashlib.sha256(normal.convert('RGBA').tobytes()).hexdigest()==rs[0]['canvas_rgba_sha256']==rs[0]['capture_rgba_sha256']
  assert ImageChops.difference(z,normal).getbbox() is None and ImageChops.difference(z,images['observer']).getbbox() is None
  diff=ImageChops.difference(z,images['v175']);allowed=[]
  if name in names:
   allowed=[budget['1.  Jamestown']]
   if name not in {'same-name-london-selected','land-deleted-destination'}:allowed.append(budget['2.  Jamestown'])
  if name in {'same-name-london-selected','land-deleted-destination'}:assert diff.crop(tuple(x*4 for x in budget['2.  Jamestown'])).getbbox() is None,(side,name,'stale city')
  if diff.getbbox() is not None:
   changed.append(name)
   for a in allowed:diff.paste((0,0,0),tuple(x*4 for x in a))
   assert diff.getbbox() is None,(side,name,'outside city fields')
  for a in allowed:assert ImageChops.difference(images['noatlas'],images['control']).crop(tuple(x*4 for x in a)).getbbox() is None,(side,name,'noatlas')
  if name in {'same-name-editor','land-editor'}:
   for a in budget.values():assert ImageChops.difference(z,images['v175']).crop(tuple(x*4 for x in a)).getbbox() is not None
  areas[name]=allowed
 measures=[json.loads(x) for x in (out/(side+'-observer-measure/strings.jsonl')).read_text().splitlines()]
 for text in budget:
  rows=[x for x in measures if x['shown']==text];assert rows
  assert all(x['actual_px']==22 and x['cap_h']==5 and x['overflow_px']==0 and x['zh']==text[:4]+'詹姆斯敦（Jamestown）' for x in rows)
 assert (build/'tests.log').read_text().count('--- PASS:')==119 and '--- SKIP:' not in (build/'tests.log').read_text()
 assert (build/'stable-build/adapter.go').read_bytes()==(build/'adapter.go').read_bytes() and (build/'stable-build/strings.go').read_bytes()==(build/'strings.go').read_bytes()
 assert sha(build/'font/string-atlas.json')==sha(b/'trade-port-role-build-v175/font/string-atlas.json')
 capacity=json.loads((out/'catalog-layout.json').read_text());assert capacity['result']=='PASS_CATALOG_FONT_PROJECTION' and capacity['catalog_names']==172 and len(capacity['cases'])==688 and capacity['overflow_fallback_all_four_profiles']
 assert capacity['atlas_sha256']==sha(build/'font/string-atlas.json') and capacity['original_colony_sha256']=='2996f8a9d53a7f7a93e4a238bfd2ba727c4cf5cdabc334c4059c6860c9e4ae36'
 return {'result':'PASS','grade':'confirmed','verified_fields':fields,'field_count':2,'side':side,'normal_GUI':count,'original_final_sides':6,'inputs_sha256':integrity['inputs_sha256'],'all_saves':integrity['saves'],'changed_shots':changed,'areas':areas,'scope':'第一路線前兩列預設Jamestown；未知母港原文，改印／刪除不得殘留；不含其他編號及自動跑商'}

EVIDENCE_SHA='a1c623fa4d4fd0fb2743dce01c8616fca8a9bd61f6509e0f5e8949b1438e5602'
ROOTS={'sea': 'trade-grid-sea-gui-v188', 'land': 'trade-grid-land-gui-v189', 'build': 'trade-grid-build-v187', 'native': 'trade-grid-source-v180', 'private': 'trade-grid-field-verify-v186', 'verify': 'trade-grid-formal-v190', 'baseline': 'trade-port-role-build-v175'}
def verify(game,root,out,side):
 b=out.parent
 assert root.resolve()==(b/ROOTS[side]).resolve(),'GUI root differs'
 assert sha(out/'batch.json')==EVIDENCE_SHA,'reviewed manifest differs'
 batch=json.loads((out/'batch.json').read_text());assert batch['schema']==1 and batch['roots']==ROOTS
 for name,digest in batch['original_files'].items():assert sha(game/name)==digest,('original version differs',name)
 for key,files in batch['artifact_hashes'].items():
  for rel,digest in files.items():
   p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
   assert sha(b/ROOTS[key]/p)==digest,('receipt differs',key,rel)
 assert json.loads((b/ROOTS['native']/'source-summary.json').read_text())['result']=='PASS_READONLY_GRID_SOURCE_AND_LAYOUT'
 assert json.loads((b/ROOTS['private']/'grid-summary.json').read_text())['result']=='PASS_PRIVATE_GRID_SCOPE_STATE_SAVE_AND_LAYOUT'
 result=check(b,out,side);state=json.loads((root/'control.json').read_text())['state'];result.update(final_step=state['steps'],final_memory_sha256=state['memory_sha256'],evidence_sha256=EVIDENCE_SHA);return result
def main():
 import argparse
 p=argparse.ArgumentParser(description='驗收第一貿易路線前兩列預設城市中文與正常GUI。')
 for name in ['game','reports','evidence']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--side',choices=['sea','land'],required=True);a=p.parse_args()
 if any(not(a.game/n).is_file() for n in ['OPENING.EXE','VICEROY.EXE','MENU.TXT','GAME.TXT','LABELS.TXT','NAMES.TXT','COLONY.TXT']):print('SKIP：缺合法原版，未驗收城市欄');return 77
 try:result=verify(a.game,a.reports,a.evidence,a.side)
 except (OSError,ValueError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
 print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
