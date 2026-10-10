#!/usr/bin/env python3
"""短名與長名目的地：原版內框、34GUI四側與33圖回歸。"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import EXPECTED, read, sha
from check_goal185_voyage import SOURCES

BINARY='6ea4f982d2467421f42eeb00b2ea05060068bfe29d296e901187694fa7e0d394'
BASELINE='f8d65786000bbaecd037fbdf17050bb19ed7d1f9cd5e31d5f0e69450f87ff687'
CHECKER='85897e98dcdc39f2e5aea8308b8ad7e282751054155b3b6d9d31eeaf1190fbf5'
INPUTS={'short':'adc3167c26870fa0c1926eb5e5c7e0ee7edecd9a1d4f29b1a9ad6e811969f573',
        'long':'edbf6f163aacba5b5646385d2d3142967ce245dd4da506093e1f765d45226d4d'}


def check(game,reports,kind):
    for name,digest in dict(EXPECTED,**SOURCES).items():assert sha(game/name)==digest,name
    private=reports/'check_port_family_formal.py';assert sha(private)==CHECKER
    for profile in ['short','long']:
        gui=reports/('port-family-'+profile+'-formal-gui')
        assert sha(gui/'gui.inputs.json')==INPUTS[profile]
        assert sha(Path(read(gui/'session.json')['binary']))==BINARY
        for mode in ['zh','control','missing','baseline']:
            path=reports/('port-family-'+profile+'-formal-'+mode);command=read(path/'command.json')
            assert sha(Path(command[0]))==(BASELINE if mode=='baseline' else BINARY)
            assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
            assert ('--control' in command)==(mode=='control') and ('--missing' in command)==(mode=='missing')
            for name,digest in read(path/'run.json')['input_hashes'].items():assert sha(game/name)==digest,name
    with tempfile.TemporaryDirectory(prefix='colonization-port-family-') as tmp:
        output=Path(tmp)/'proof.json'
        run=subprocess.run([sys.executable,str(private),'--reports',str(reports),'--output',str(output)],capture_output=True,text=True,timeout=120)
        assert run.returncode==0,run.stderr[-1500:]
        proof=read(output)
    assert proof['result']=='PASS_PORT_FAMILY_FORMAL' and len(proof['cases'])==2
    assert sum(r['samples'] for r in proof['regressions'])==33
    case=next(r for r in proof['cases'] if r['kind']==kind);assert case['samples']==17
    record=read(reports/('port-family-'+kind+'-formal-zh/run.json'))
    # 改名屬玩家資料；普查只登錄已驗原版SAILPORT標題，不反推COLONY原始行已被遊戲讀取。
    titles=[e for e in record['events'] if e.get('stage')=='source' and e.get('candidate_id')=='GAME.TXT:0x00001CBB']
    assert titles and all(e['font_px']==30 and e['safe']==[66,82,176,94] and e['items']==['Select a port to sail to:'] for e in titles)
    return {'result':'PASS','status':'PASS_PORT_FAMILY_FORMAL','profile':kind,'samples':34,
            'cases':proof['cases'],'regressions':proof['regressions'],'inputs_sha256':INPUTS[kind],
            'binary_sha256':BINARY,'final_step':case['state']['steps'],'final_memory_sha256':case['state']['memory_sha256'],
            'verified_fields':[{'candidate_id':titles[0]['candidate_id'],'shown':titles[0]['shown'],'safe':titles[0]['safe']}],
            'scope':'34新正常GUI四側、短名與長名、實際懸停／取消／重開，33圖既有回歸；不把玩家改名反推為COLONY來源命中。'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True)
    p.add_argument('--kind',choices=['short','long'],default='short');p.add_argument('--output',type=Path);a=p.parse_args()
    if not all((a.game/name).is_file() for name in dict(EXPECTED,**SOURCES)):
        print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports,a.kind)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())
