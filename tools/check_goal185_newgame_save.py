#!/usr/bin/env python3
"""Docker 內核對正常新局手動存檔、三側重播與新行程讀回。"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def pixels(p):
    with Image.open(p) as im: return im.size, hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reports',type=Path,required=True)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    originals={'OPENING.EXE':'3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39','VICEROY.EXE':'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3'}
    if any(not(a.game/n).is_file() for n in originals): print('SKIP: 缺少原版輸入');return 77
    for n,h in originals.items(): assert sha(a.game/n)==h
    root=a.reports;source=root/'newgame-save-20261008';receipt=load(source/'gui.inputs.json');gui=load(source/'gui.json')
    assert load(source/'session.json')['initial_saves']==[]
    assert sha(Path(load(source/'session.json')['binary']))=='f4042b3db4b808e8d768502b5a6b521dcfbf1e104b3e6cd59f60f3ee4fafa3e6'
    runs={m:root/f'save-{m}-20261008' for m in ['zh','control','missing']}
    shots=[x.split() for x in (source/'gui.shots').read_text().splitlines()]
    assert len(shots)>=15 and (source/'save/COLONY00.SAV').is_file()
    for mode,path in runs.items():
        run=load(path/'run.json');cmd=load(path/'command.json')
        assert run['state']==gui['state'] and run['state']['steps']==receipt['end']
        assert sha(path/'run.memory')==gui['state']['memory_sha256']
        assert ('--control' in cmd)==(mode=='control') and ('--missing' in cmd)==(mode=='missing')
        assert Path(cmd[cmd.index('--replay-inputs')+1]).read_bytes()==(source/'gui.inputs.json').read_bytes()
        assert sha(path/'raw.wav')==sha(source/'raw.wav')
        for save in (source/'save').glob('COLONY*.SAV'): assert sha(path/'save'/save.name)==sha(save)
    cps={m:{x['label']:x for x in load(p/'run.json')['checkpoints']} for m,p in runs.items()}
    for name,step in shots:
        label=f'cp-{step}'
        for field in ['memory_sha256','raw_sha256','palette_sha256']: assert len({cps[m][label][field] for m in runs})==1
        assert pixels(source/f'gui.{name}.png')==pixels(runs['zh']/f'run.{label}.png')
        assert pixels(runs['missing']/f'run.{label}.png')==pixels(runs['control']/f'run.{label}.png')
    reload=root/'reload-newgame-20261008';control=root/'reload-control-20261008'
    assert load(reload/'gui.json')['state']==load(control/'run.json')['state']
    assert sha(reload/'raw.wav')==sha(control/'raw.wav')
    for save in (source/'save').glob('COLONY*.SAV'):
        assert sha(save)==sha(reload/'save'/save.name)==sha(control/'save'/save.name)
    cmd=load(control/'command.json');assert Path(cmd[cmd.index('--replay-inputs')+1]).read_bytes()==(reload/'gui.inputs.json').read_bytes()
    output={'result':'PASS_NORMAL_NEWGAME_SAVE_RELOAD','scope':'英國發現者新局、正常向西移動、GAME手動存檔、關窗重啟讀回','gui_shots':len(shots),'end':receipt['end'],'binary_sha256':sha(Path(cmd[0])),'inputs_sha256':sha(source/'gui.inputs.json'),'save_sha256':sha(source/'save/COLONY00.SAV'),'reload_inputs_sha256':sha(reload/'gui.inputs.json'),'reload_memory_sha256':load(reload/'gui.json')['state']['memory_sha256'],'originals':originals}
    a.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print(json.dumps(output,ensure_ascii=False));return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (AssertionError,KeyError,FileNotFoundError) as exc: print(f'FAIL: {exc}',file=sys.stderr);sys.exit(1)
