#!/usr/bin/env python3
"""View兩欄來源限定正式GUI；不把名稱容量投影當正常命中。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

INPUT='316463c110d48bade77afd42399b999d8fe824500e953303e390de0ea160ebcf'
BINARY='11fe199fe13106f145cdb3c4aab2c22018a7a49007d507c425d0cc257aeee9f6'
BASELINE='ed5444ea648d551cf8d512d282c1a9b970b6737dd9d5596f048c1869f4d7ad8c'


def check(game,reports):
    for name,value in EXPECTED.items():
        assert sha(game/name)==value
    gui=reports/'view-fields-formal-gui'
    assert sha(gui/'gui.inputs.json')==INPUT
    assert sha(Path(read(gui/'session.json')['binary']))==BINARY
    original=read(gui/'gui.json')
    peers={mode:reports/('view-fields-formal-'+mode) for mode in ('zh','control','missing','baseline')}
    data={mode:read(root/'run.json') for mode,root in peers.items()}
    for mode,root in peers.items():
        assert data[mode]['state']==original['state']
        assert (root/'run.memory').read_bytes()==(gui/'gui.memory').read_bytes()
        assert (root/'raw.wav').read_bytes()==(gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes']==original['input_hashes']
        assert {p.name:sha(p) for p in (root/'save').glob('COLONY*.SAV')}=={p.name:sha(p) for p in (gui/'save').glob('COLONY*.SAV')}
        command=read(root/'command.json')
        assert sha(Path(command[0]))==(BASELINE if mode=='baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert ('--control' in command)==(mode=='control')
        assert ('--missing' in command)==(mode=='missing')
    shots=[line.split() for line in (gui/'gui.shots').read_text().splitlines()]
    assert len(shots)==len({name for name,step in shots})==10
    captures={r['name']:r for r in map(json.loads,(gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cp={mode:{r['label']:r for r in value['checkpoints']} for mode,value in data.items()}
    changed=[]
    for name,step in shots:
        actual=pixels(gui/f'gui.{name}.png');stem='run.cp-'+step
        assert hashlib.sha256(actual).hexdigest()==captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step']==int(step)
        assert actual==pixels(peers['zh']/(stem+'.png'))
        assert pixels(peers['missing']/(stem+'.png'))==pixels(peers['control']/(stem+'.png'))
        for mode,root in peers.items():
            for key in ('memory_sha256','raw_sha256','palette_sha256'):
                assert cp[mode]['cp-'+step][key]==cp['control']['cp-'+step][key]
            for suffix in ('idx','pal'):
                assert (root/(stem+'.'+suffix)).read_bytes()==(peers['control']/(stem+'.'+suffix)).read_bytes()
        with Image.open(gui/f'gui.{name}.png') as im:a=im.convert('RGB')
        with Image.open(peers['baseline']/(stem+'.png')) as im:b=im.convert('RGB')
        diff=ImageChops.difference(a,b).getbbox()
        if name in ('view-first','view-river','view-after-pedia'):
            regions=[(964,268,1212,300)]
            if name!='view-first':regions.append((964,296,1160,328))
            assert diff,name
            restored=a.copy()
            for region in regions:restored.paste(b.crop(region),region[:2])
            assert restored.tobytes()==b.tobytes(),name
            changed.append({'name':name,'regions':regions,'difference':diff})
        else:
            assert diff is None,(name,diff)
    events=[r for r in data['zh']['events'] if r.get('stage')=='source' and r.get('candidate_id','').startswith('STRING:view-')]
    assert len(events)==7 and all(r['font_px']==22 for r in events)
    assert {r['candidate_id'] for r in events}=={'STRING:view-location','STRING:view-tribe-land'}
    assert not any(key.startswith('no-template\tLocat:') or key.endswith('\tIroquois Land') for key in data['zh'].get('string_misses',{}))
    return {'status':'PASS_VIEW_FIELDS_FORMAL','scope':'two verified whole-message View fields, opaque trailing numeric value preserved',
            'input_sha256':INPUT,'binary_sha256':BINARY,'samples':len(shots),'changes':changed,'original_state':original['state']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if any(not (a.game/name).is_file() for name in EXPECTED):
        print('SKIP：缺合法原版輸入');return 77
    result=check(a.game,a.reports)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['status'],result['samples']);return 0


if __name__=='__main__':raise SystemExit(main())
