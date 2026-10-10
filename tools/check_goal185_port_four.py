#!/usr/bin/env python3
"""帶貨船隻四列正式GUI、完整來源、同狀態及三側回退。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY='8e27f92bc4a73ded8289f19e664e62b5eae1185b21bad3866c33c7e7a94af015'
BASELINE='2f0fbafd16e677e12774e8bdc11d093e8f2e46f5fb6aa2b99d3f67afcb051dcd'
INPUT='f6233915b1bbc44c53642967de145b86dd81d1a3e3f7c16912cf2af6f58b1ecb'
SEED={'COLONY00.SAV':'c9655cc23ed5eaa1dff004161d99dd57c339c58f49e2635a49e71127f0ec3cd7',
      'COLONY03.SAV':'d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77',
      'COLONY09.SAV':'8a70bc0e3ce8b3110a4c9e1eec438ca930bd784eb375c488e18b9a78b521d7d8'}
ID='GAME.TXT:@EUROPESHIPOPTIONS:0x00009B3D#4+list'
MENU={'cargo-four-options','hover-0','hover-1','hover-2','hover-3'}


def check(game,reports):
    for name,digest in EXPECTED.items():assert sha(game/name)==digest
    raw=(game/'GAME.TXT').read_bytes()[0x9B3D:0x9B3D+75]
    assert hashlib.sha256(raw).hexdigest()=='9f32942301758e884038362e26a03eebf1bbd02076aedc5d5b07983875e1d370'
    expected=raw.decode('cp437').strip().split('\r\n');assert len(expected)==4
    gui=reports/'port-four-formal-gui';assert sha(gui/'gui.inputs.json')==INPUT
    assert sha(Path(read(gui/'session.json')['binary']))==BINARY
    original=read(gui/'gui.json')
    peers={m:reports/('port-four-formal-'+m) for m in ('zh','control','missing','baseline')}
    data={m:read(p/'run.json') for m,p in peers.items()}
    for mode,p in peers.items():
        assert data[mode]['state']==original['state']
        assert (p/'run.memory').read_bytes()==(gui/'gui.memory').read_bytes()
        assert (p/'raw.wav').read_bytes()==(gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes']==original['input_hashes']
        assert {f.name:sha(f) for f in(p/'save').glob('*.SAV')}==SEED
        cmd=read(p/'command.json');assert sha(Path(cmd[0]))==(BASELINE if mode=='baseline' else BINARY)
        assert Path(cmd[cmd.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert ('--control' in cmd)==(mode=='control');assert ('--missing' in cmd)==(mode=='missing')
    assert {f.name:sha(f) for f in(gui/'save').glob('*.SAV')}==SEED
    shots=[s.split() for s in(gui/'gui.shots').read_text().splitlines()];assert len(shots)==len({n for n,s in shots})==13
    captures={r['name']:r for r in map(json.loads,(gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps={m:{c['label']:c for c in r['checkpoints']} for m,r in data.items()};changes=[]
    for name,step in shots:
        stem='run.cp-'+step;actual=pixels(gui/f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest()==captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step']==int(step)
        assert actual==pixels(peers['zh']/(stem+'.png'))
        assert pixels(peers['control']/(stem+'.png'))==pixels(peers['missing']/(stem+'.png'))
        for m,p in peers.items():
            for key in ('memory_sha256','raw_sha256','palette_sha256'):assert cps[m]['cp-'+step][key]==cps['control']['cp-'+step][key]
            for ext in ('idx','pal'):assert(p/(stem+'.'+ext)).read_bytes()==(peers['control']/(stem+'.'+ext)).read_bytes()
        with Image.open(peers['zh']/(stem+'.png')) as im:a=im.convert('RGB')
        with Image.open(peers['baseline']/(stem+'.png')) as im:b=im.convert('RGB')
        diff=ImageChops.difference(a,b);outside=diff.copy()
        if name in MENU:outside.paste((0,0,0),(216,272,1060,528))
        assert not outside.getbbox(),(name,outside.getbbox());assert bool(diff.getbbox())==(name in MENU),name
        if name in MENU:changes.append({'name':name,'difference':list(diff.getbbox()),'approved_regions':[[54,68,265,132]]})
    sources=[e for e in data['zh']['events'] if e.get('stage')=='source' and e.get('candidate_id')==ID]
    assert len(sources)==1 and sources[0]['font_px']==30 and sources[0]['safe']==[81,84,207,132] and sources[0]['items']==expected
    assert any(e.get('stage')=='active' and e.get('candidate_id')==ID for e in data['zh']['events'])
    assert not any(' '.join(expected) in k for k in data['zh'].get('dialog_misses',{}))
    return {'result':'PASS','status':'PASS_PORT_FOUR_FORMAL','samples':13,'changes':changes,
            'inputs_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],
            'final_step':original['state']['steps'],'final_memory_sha256':original['state']['memory_sha256'],
            'verified_fields':[{'candidate_id':ID,'shown':sources[0]['shown'],'safe':sources[0]['safe'],
                                'source_ids':['GAME.TXT:@EUROPESHIPOPTIONS']}],
            'scope':'完整四列已逐行顯示；三列回歸另核，不外推其他船型。'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if any(not(a.game/n).is_file() for n in EXPECTED):print('SKIP：缺合法原版輸入');return 77
    r=check(a.game,a.reports)
    if a.output:a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(r,ensure_ascii=False,sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
