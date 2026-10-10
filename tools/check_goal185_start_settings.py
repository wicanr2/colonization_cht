#!/usr/bin/env python3
"""正常點選自訂頁四種設定的兩端縮圖，十圖／三側與實際值核對。"""
import argparse
import hashlib
import json
from pathlib import Path
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY='30464b5293d97a92ecd528f318a5be2eb52169fa7b791505161aafdbc0805a15'
INPUT='7f630eab2d50347801742eb92a836f08d6b8f8591d45bd959d7ece2dc99f334c'
WORDS={'Small':'小','Large':'大','Archipelago':'群島','Continents':'大陸','Cool':'涼冷','Warm':'溫暖','Arid':'乾燥','Wet':'潮濕'}

def check(game,reports):
    for name,digest in EXPECTED.items():assert sha(game/name)==digest
    gui=reports/'start-settings-arrows-gui'
    assert sha(gui/'gui.inputs.json')==INPUT
    assert sha(Path(read(gui/'session.json')['binary']))==BINARY
    original=read(gui/'gui.json')
    peers={m:reports/('start-settings-arrows-'+m) for m in ['zh','control','missing']}
    data={m:read(p/'run.json') for m,p in peers.items()}
    for mode,p in peers.items():
        assert data[mode]['state']==original['state']
        assert(p/'run.memory').read_bytes()==(gui/'gui.memory').read_bytes()
        assert(p/'raw.wav').read_bytes()==(gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes']==original['input_hashes']
        assert{f.name:sha(f) for f in(p/'save').glob('*.SAV')}=={f.name:sha(f) for f in(gui/'save').glob('*.SAV')}
        command=read(p/'command.json');assert sha(Path(command[0]))==BINARY
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert('--control'in command)==(mode=='control') and ('--missing'in command)==(mode=='missing')
    shots=[l.split() for l in(gui/'gui.shots').read_text().splitlines()];assert len(shots)==10
    captures={r['name']:r for r in map(json.loads,(gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps={m:{c['label']:c for c in d['checkpoints']} for m,d in data.items()}
    for name,step in shots:
        stem='run.cp-'+step;actual=pixels(gui/('gui.'+name+'.png'))
        assert actual==pixels(peers['zh']/(stem+'.png')) and actual!=pixels(peers['control']/(stem+'.png'))
        assert hashlib.sha256(actual).hexdigest()==captures[name]['capture_rgba_sha256'] and captures[name]['frame_step']==int(step)
        assert pixels(peers['control']/(stem+'.png'))==pixels(peers['missing']/(stem+'.png'))
        for key in ['memory_sha256','raw_sha256','palette_sha256']:assert len({cps[m]['cp-'+step][key] for m in peers})==1
        for ext in ['idx','pal']:assert len({(p/(stem+'.'+ext)).read_bytes() for p in peers.values()})==1
    source=[e for e in data['zh']['events'] if e.get('stage')=='source' and e.get('shown') in WORDS]
    assert {e['shown'] for e in source}==set(WORDS)
    active={(e.get('candidate_id'),e.get('shown')) for e in data['zh']['events'] if e.get('stage')=='active'}
    fields=[]
    for word,zh in WORDS.items():
        rows=[e for e in source if e['shown']==word]
        assert all(e['candidate_id']=='STRING:dictionary' and e['entry_ip']=='0D21:00C6' and e['source_linear']==173978 and e['zh']==zh and e['font_px'] in [21,22] for e in rows)
        assert ('STRING:dictionary',word) in active
        for e in rows:
            f={'candidate_id':e['candidate_id'],'shown':word,'safe':e['safe']}
            if f not in fields:fields.append(f)
    return {'result':'PASS','status':'PASS_START_SETTINGS_VALUES','samples':len(shots),'source':source,'inputs_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],'final_step':original['state']['steps'],'final_memory_sha256':original['state']['memory_sha256'],'verified_fields':fields,'scope':'四種設定卡八個實際值；不以同文反推其他原始段落或宣稱六項開局範圍全部完成。'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not all((a.game/name).is_file() for name in EXPECTED):print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
