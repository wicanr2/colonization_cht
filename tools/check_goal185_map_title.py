#!/usr/bin/env python3
"""地圖載入居中標題：七張正常GUI／四側、取消及自訂六圖回歸。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY='a1d43865238a63e4658aee2d5bd37daa64b655c0619b7d0e4930c74109969567'
BASELINE='30464b5293d97a92ecd528f318a5be2eb52169fa7b791505161aafdbc0805a15'
INPUT='fb4cc37ef9f2bf7accf8234c4e9708b8d13e69ba0bed67bd74c558a5d2720181'
CID='GAME.TXT:0x000002C8'

def check(game,reports):
    for name,digest in EXPECTED.items():assert sha(game/name)==digest
    gui=reports/'map-title-formal-gui';assert sha(gui/'gui.inputs.json')==INPUT
    assert sha(Path(read(gui/'session.json')['binary']))==BINARY
    original=read(gui/'gui.json')
    peers={m:reports/('map-title-formal-'+m) for m in ['zh','control','missing','baseline']}
    data={m:read(p/'run.json') for m,p in peers.items()}
    for mode,p in peers.items():
        assert data[mode]['state']==original['state']
        assert(p/'run.memory').read_bytes()==(gui/'gui.memory').read_bytes()
        assert(p/'raw.wav').read_bytes()==(gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes']==original['input_hashes']
        assert{f.name:sha(f) for f in(p/'save').glob('*.SAV')}=={f.name:sha(f) for f in(gui/'save').glob('*.SAV')}
        command=read(p/'command.json');assert sha(Path(command[0]))==(BASELINE if mode=='baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert('--control'in command)==(mode=='control') and ('--missing'in command)==(mode=='missing')
    shots=[l.split() for l in(gui/'gui.shots').read_text().splitlines()];assert len(shots)==7
    captures={r['name']:r for r in map(json.loads,(gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps={m:{c['label']:c for c in d['checkpoints']} for m,d in data.items()}
    changes=[]
    for name,step in shots:
        stem='run.cp-'+step;actual=pixels(gui/('gui.'+name+'.png'))
        assert actual==pixels(peers['zh']/(stem+'.png'))
        assert hashlib.sha256(actual).hexdigest()==captures[name]['capture_rgba_sha256'] and captures[name]['frame_step']==int(step)
        assert pixels(peers['control']/(stem+'.png'))==pixels(peers['missing']/(stem+'.png'))
        for key in ['memory_sha256','raw_sha256','palette_sha256']:assert len({cps[m]['cp-'+step][key] for m in peers})==1
        for ext in ['idx','pal']:assert len({(p/(stem+'.'+ext)).read_bytes() for p in peers.values()})==1
        a=Image.open(peers['baseline']/(stem+'.png')).convert('RGB');b=Image.open(peers['zh']/(stem+'.png')).convert('RGB')
        diff=ImageChops.difference(a,b);outside=diff.copy()
        if name=='map-load-prompt':outside.paste((0,0,0),(424,348,856,400))
        assert not outside.getbbox() and bool(diff.getbbox())==(name=='map-load-prompt'),(name,diff.getbbox())
        if diff.getbbox():changes.append({'name':name,'difference':diff.getbbox()})
    source=[e for e in data['zh']['events'] if e.get('stage')=='source' and e.get('candidate_id')==CID];assert len(source)==1
    e=source[0];assert e['entry_ip']=='0D21:00C6' and e['shown']=='Select Map File to Load' and e['source_linear']==174110 and e['safe']==[106,87,214,100] and e['font_px']==30
    fresh=reports/'map-title-custom-regression';old=reports/'custom-settings-formal-zh';oldgui=reports/'custom-settings-formal-gui'
    assert read(fresh/'run.json')['state']==read(old/'run.json')['state']==read(oldgui/'gui.json')['state']
    assert(fresh/'run.memory').read_bytes()==(old/'run.memory').read_bytes()
    assert(fresh/'raw.wav').read_bytes()==(old/'raw.wav').read_bytes()
    assert{f.name:sha(f) for f in(fresh/'save').glob('*.SAV')}=={f.name:sha(f) for f in(old/'save').glob('*.SAV')}
    command=read(fresh/'command.json');assert sha(Path(command[0]))==BINARY
    assert Path(command[command.index('--replay-inputs')+1]).samefile(oldgui/'gui.inputs.json')
    regression=[l.split() for l in(oldgui/'gui.shots').read_text().splitlines()];assert len(regression)==6
    for name,step in regression:
        stem='run.cp-'+step;assert pixels(fresh/(stem+'.png'))==pixels(old/(stem+'.png'))==pixels(oldgui/('gui.'+name+'.png'))
        for ext in ['idx','pal']:assert(fresh/(stem+'.'+ext)).read_bytes()==(old/(stem+'.'+ext)).read_bytes()
    return {'result':'PASS','status':'PASS_MAP_TITLE_FORMAL','samples':len(shots),'changes':changes,'source':source,'regression_samples':len(regression),'inputs_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],'final_step':original['state']['steps'],'final_memory_sha256':original['state']['memory_sha256'],'verified_fields':[{'candidate_id':CID,'shown':e['shown'],'safe':e['safe']}],'scope':'只驗唯一0x2C8居中標題、檔名原樣、正常取消与重入；其他^列不外推。'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not all((a.game/name).is_file() for name in EXPECTED):print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
