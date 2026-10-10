#!/usr/bin/env python3
"""建造兩欄生命週期：14正常GUI／四側及碼頭、職業、地圖回歸。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY='89e63cae4628d85ecf6febef5a386614837c5ef327772f26a485eeed8dc50fd5'
BASELINE='a1d43865238a63e4658aee2d5bd37daa64b655c0619b7d0e4930c74109969567'
INPUT='4580f33158a01847d3a563162e0386c51b3684b37f09aeb44c249a18ae050258'
TITLE=(296,180,616,216)
WAGON=(940,524,1112,552)

def same_state(fresh,original):
    d,g=read(fresh/'run.json'),read(original/'gui.json')
    assert d['state']==g['state']
    assert(fresh/'run.memory').read_bytes()==(original/'gui.memory').read_bytes()
    assert(fresh/'raw.wav').read_bytes()==(original/'raw.wav').read_bytes()
    assert d['input_hashes']==g['input_hashes']
    assert{f.name:sha(f) for f in(fresh/'save').glob('*.SAV')}=={f.name:sha(f) for f in(original/'save').glob('*.SAV')}
    return d

def compare_rectangles(before,after,areas,name):
    diff=ImageChops.difference(Image.open(before).convert('RGB'),Image.open(after).convert('RGB'))
    outside=diff.copy()
    for area in areas:
        assert diff.crop(area).getbbox(),(name,area)
        outside.paste((0,0,0),area)
    assert not outside.getbbox() and bool(diff.getbbox())==bool(areas),(name,diff.getbbox())
    return diff.getbbox()

def check(game,reports):
    for name,digest in EXPECTED.items():assert sha(game/name)==digest
    gui=reports/'build-lifecycle-formal-gui';assert sha(gui/'gui.inputs.json')==INPUT
    assert sha(Path(read(gui/'session.json')['binary']))==BINARY
    peers={m:reports/('build-lifecycle-formal-'+m) for m in ['zh','control','missing','baseline']}
    data={m:same_state(p,gui) for m,p in peers.items()}
    for mode,p in peers.items():
        command=read(p/'command.json');assert sha(Path(command[0]))==(BASELINE if mode=='baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert('--control'in command)==(mode=='control') and ('--missing'in command)==(mode=='missing')
    shots=[l.split() for l in(gui/'gui.shots').read_text().splitlines()];assert len(shots)==14
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
        areas=[]
        if name in ['build-panel','build-list','build-next','build-second','build-first-return','build-last','build-list-cancel']:areas.append(WAGON)
        if name in ['build-next','build-second','build-first-return','build-last']:areas.append(TITLE)
        diff=compare_rectangles(peers['baseline']/(stem+'.png'),peers['zh']/(stem+'.png'),areas,name)
        if diff:changes.append({'name':name,'difference':diff})
    source=data['zh']['events']
    wagon=[e for e in source if e.get('stage')=='source' and e.get('shown')=='Wagon Train'];assert len(wagon)==2
    assert all(e['candidate_id']=='STRING:dictionary' and e['safe']==[235,131,278,138] and e['font_px']==22 and e['entry_ip']=='0D21:00C6' for e in wagon)
    title=[e for e in source if e.get('stage')=='source' and e.get('shown')=='Select An Item To Build'];assert len(title)==1
    assert title[0]['candidate_id']=='STRING:line' and title[0]['safe']==[74,45,154,54] and title[0]['font_px']==21 and title[0]['source_linear']==175132
    assert not any(e.get('candidate_id')=='STRING:line' and e.get('reason')=='superseded-by-new-dialog' for e in source)
    assert not any(e.get('shown')=='Wagon Train' and e.get('reason')=='canvas-changed-before-screen' for e in source)
    regressions=[]
    for fresh_name,gui_name in [('build-lifecycle-docks-regression','build-docks-probe-gui'),('build-lifecycle-profession-regression','profession-family-formal-gui'),('build-lifecycle-map-regression','map-title-formal-gui')]:
        fresh,oldgui=reports/fresh_name,reports/gui_name
        same_state(fresh,oldgui)
        command=read(fresh/'command.json');assert sha(Path(command[0]))==BINARY
        assert Path(command[command.index('--replay-inputs')+1]).samefile(oldgui/'gui.inputs.json')
        rows=[l.split() for l in(oldgui/'gui.shots').read_text().splitlines()]
        for name,step in rows:
            areas=[]
            if gui_name=='build-docks-probe-gui':
                if name in ['build-panel','build-list']:areas.append(WAGON)
                if name=='docks-list-next':areas.append(TITLE)
            compare_rectangles(oldgui/('gui.'+name+'.png'),fresh/('run.cp-'+step+'.png'),areas,gui_name+'/'+name)
        regressions.append({'gui':gui_name,'samples':len(rows)})
    original=read(gui/'gui.json')
    return {'result':'PASS','status':'PASS_BUILD_LIFECYCLE_FORMAL','samples':len(shots),'changes':changes,'source':wagon+title,'regressions':regressions,'inputs_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],'final_step':original['state']['steps'],'final_memory_sha256':original['state']['memory_sha256'],'verified_fields':[{'candidate_id':e['candidate_id'],'shown':e['shown'],'safe':e['safe']} for e in [wagon[0],title[0]]],'scope':'貨車面板底邊与同一完整建造清單多次導航；其他建造名／列數、真正長清單捲動不外推。'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not all((a.game/name).is_file() for name in EXPECTED):print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
