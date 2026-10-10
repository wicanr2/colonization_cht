#!/usr/bin/env python3
"""來源限定兩行職業標題：九張正式GUI／四側與取消驗收。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY='4cf2b7d30672794cdfc3e2c924f391a632b2e09f96397bfc59d8e8c4353a87f1'
INPUT='d8a6c631501d8221ac7042b4a22d18ec8a4be131d304ed45e4c00672181d905d'
BASELINE='54a1cf49e822558100bc503f11e37adf49e85dc447d91100addcc7fd9ad3a30f'
CID='STRING:profession-title'

def check(game,reports):
 for name,digest in EXPECTED.items():assert sha(game/name)==digest
 gui=reports/'profession-formal-gui';assert sha(gui/'gui.inputs.json')==INPUT
 assert sha(Path(read(gui/'session.json')['binary']))==BINARY
 original=read(gui/'gui.json');peers={m:reports/('profession-formal-'+m) for m in ['zh','control','missing','baseline']}
 data={m:read(p/'run.json') for m,p in peers.items()}
 for mode,path in peers.items():
  assert data[mode]['state']==original['state']
  assert (path/'run.memory').read_bytes()==(gui/'gui.memory').read_bytes()
  assert (path/'raw.wav').read_bytes()==(gui/'raw.wav').read_bytes()
  assert data[mode]['input_hashes']==original['input_hashes']
  assert {p.name:sha(p) for p in (path/'save').glob('*.SAV')}=={p.name:sha(p) for p in(gui/'save').glob('*.SAV')}
  command=read(path/'command.json');assert sha(Path(command[0]))==(BASELINE if mode=='baseline' else BINARY)
  assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
  assert ('--control' in command)==(mode=='control');assert ('--missing' in command)==(mode=='missing')
 shots=[l.split() for l in (gui/'gui.shots').read_text().splitlines()];assert len(shots)==9
 captures={r['name']:r for r in map(json.loads,(gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
 cps={m:{c['label']:c for c in r['checkpoints']} for m,r in data.items()}
 changes=[]
 for name,step in shots:
  stem='run.cp-'+step;actual=pixels(gui/('gui.'+name+'.png'))
  assert hashlib.sha256(actual).hexdigest()==captures[name]['capture_rgba_sha256']
  assert captures[name]['frame_step']==int(step) and actual==pixels(peers['zh']/(stem+'.png'))
  assert pixels(peers['control']/(stem+'.png'))==pixels(peers['missing']/(stem+'.png'))
  for mode,path in peers.items():
   for key in ['memory_sha256','raw_sha256','palette_sha256']:assert cps[mode]['cp-'+step][key]==cps['control']['cp-'+step][key]
   for ext in ['idx','pal']:assert (path/(stem+'.'+ext)).read_bytes()==(peers['control']/(stem+'.'+ext)).read_bytes()
  a=Image.open(peers['zh']/(stem+'.png')).convert('RGB');b=Image.open(peers['baseline']/(stem+'.png')).convert('RGB')
  diff=ImageChops.difference(a,b);outside=diff.copy()
  if name=='garrison-double-select':outside.paste((0,0,0),(260,64,1016,132))
  assert not outside.getbbox() and bool(diff.getbbox())==(name=='garrison-double-select'),name
  if diff.getbbox():changes.append({'name':name,'difference':list(diff.getbbox())})
 events=[e for e in data['zh']['events'] if e.get('stage')=='source' and e.get('candidate_id')==CID]
 assert len(events)==1 and events[0]['font_px']==22 and events[0]['safe']==[65,16,254,33]
 assert events[0]['shown']=='Select a Profession for Veteran Soldiers(Statesman):'
 assert any(e.get('stage')=='active' and e.get('candidate_id')==CID for e in data['zh']['events'])
 return {'result':'PASS','status':'PASS_PROFESSION_TITLE_FORMAL','samples':9,'changes':changes,
         'inputs_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],
         'final_step':original['state']['steps'],'final_memory_sha256':original['state']['memory_sha256'],
         'verified_fields':[{'candidate_id':CID,'shown':events[0]['shown'],'safe':events[0]['safe']}],
         'scope':'只驗此兩行標題、原選項不變及正常取消；其他折行／單位組合不外推。'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
 a=p.parse_args()
 if any(not(a.game/n).is_file() for n in EXPECTED):print('SKIP：缺合法原版輸入');return 77
 result=check(a.game,a.reports)
 if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
