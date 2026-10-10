#!/usr/bin/env python3
"""單列母港：九正常GUI／四側、懸停／取消與兩列24圖回歸。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageChops
from check_goal185_remaining import EXPECTED,pixels,read,sha

BINARY='70462b912fee1c1277c34c5200df7299d00991ab852a769ac8c673b2f140c79a'
BASELINE='89e63cae4628d85ecf6febef5a386614837c5ef327772f26a485eeed8dc50fd5'
INPUT='787b2ebcea066a62a729d9f8a3285ea83d4b580ab2700e2e81506e25010d21d2'
def check(game,reports):
    for name,digest in EXPECTED.items():assert sha(game/name)==digest
    gui=reports/'one-port-formal-gui';assert sha(gui/'gui.inputs.json')==INPUT
    assert sha(Path(read(gui/'session.json')['binary']))==BINARY
    original=read(gui/'gui.json');peers={m:reports/('one-port-formal-'+m) for m in ['zh','control','missing','baseline']};data={m:read(p/'run.json') for m,p in peers.items()}
    for mode,p in peers.items():
        assert data[mode]['state']==original['state']
        assert(p/'run.memory').read_bytes()==(gui/'gui.memory').read_bytes()
        assert(p/'raw.wav').read_bytes()==(gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes']==original['input_hashes']
        assert{f.name:sha(f) for f in(p/'save').glob('*.SAV')}=={f.name:sha(f) for f in(gui/'save').glob('*.SAV')}
        command=read(p/'command.json');assert sha(Path(command[0]))==(BASELINE if mode=='baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert('--control'in command)==(mode=='control') and ('--missing'in command)==(mode=='missing')
    shots=[l.split() for l in(gui/'gui.shots').read_text().splitlines()];assert len(shots)==9
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
        diff=ImageChops.difference(Image.open(peers['baseline']/(stem+'.png')).convert('RGB'),Image.open(peers['zh']/(stem+'.png')).convert('RGB'));outside=diff.copy()
        changed=name in ['one-port-menu','one-port-hover','one-port-reopen']
        if changed:outside.paste((0,0,0),(304,408,628,456))
        assert not outside.getbbox() and bool(diff.getbbox())==changed,(name,diff.getbbox())
        if diff.getbbox():changes.append({'name':name,'difference':diff.getbbox()})
    source=[e for e in data['zh']['events'] if e.get('stage')=='source' and e.get('shown')=='London (England)']
    assert len(source)>=2 and all(e['candidate_id']=='STRING:voyage-ports' and e['safe']==[76,102,157,114] and e['font_px']==30 and e['source_linear']==175470 for e in source)
    regressions=[]
    for fresh_name,old_name,gui_name in [('one-port-coast-formal-regression','coast-formal-zh','coast-formal-gui'),('one-port-voyage-formal-regression','voyage-formal-zh','voyage-formal-gui')]:
        fresh,old,oldgui=reports/fresh_name,reports/old_name,reports/gui_name
        assert read(fresh/'run.json')['state']==read(old/'run.json')['state']==read(oldgui/'gui.json')['state']
        assert(fresh/'run.memory').read_bytes()==(old/'run.memory').read_bytes()
        assert(fresh/'raw.wav').read_bytes()==(old/'raw.wav').read_bytes()
        assert{f.name:sha(f) for f in(fresh/'save').glob('*.SAV')}=={f.name:sha(f) for f in(old/'save').glob('*.SAV')}
        command=read(fresh/'command.json');assert sha(Path(command[0]))==BINARY
        assert Path(command[command.index('--replay-inputs')+1]).samefile(oldgui/'gui.inputs.json')
        rows=[l.split() for l in(oldgui/'gui.shots').read_text().splitlines()]
        for name,step in rows:
            stem='run.cp-'+step;assert pixels(fresh/(stem+'.png'))==pixels(old/(stem+'.png'))==pixels(oldgui/('gui.'+name+'.png'))
            for ext in ['idx','pal']:assert(fresh/(stem+'.'+ext)).read_bytes()==(old/(stem+'.'+ext)).read_bytes()
        regressions.append({'gui':gui_name,'samples':len(rows)})
    return {'result':'PASS','status':'PASS_ONE_PORT_FORMAL','samples':len(shots),'changes':changes,'source':source,'regressions':regressions,'inputs_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],'final_step':original['state']['steps'],'final_memory_sha256':original['state']['memory_sha256'],'verified_fields':[{'candidate_id':'STRING:voyage-ports','shown':'London (England)','safe':[76,102,157,114]}],'scope':'單列母港來源角色、正常英國單列与兩列回歸；其他國家實際命中、多城市或其他行數不外推。'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not all((a.game/name).is_file() for name in EXPECTED):print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
