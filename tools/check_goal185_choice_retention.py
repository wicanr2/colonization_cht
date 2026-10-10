#!/usr/bin/env python3
"""Docker內核對高海正文／選項保留、正常取消與三側同狀態。"""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageChops

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def pixels(p):
    with Image.open(p) as im:return im.convert('RGBA').tobytes()

def main():
    p=argparse.ArgumentParser();p.add_argument('--reports',type=Path,required=True);p.add_argument('--game',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not(a.game/'VICEROY.EXE').is_file():print('SKIP: 缺少原版');return 77
    assert sha(a.game/'VICEROY.EXE')=='a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3'
    root=a.reports;source=root/'sailhome-formal-gui-v3';gui=load(source/'gui.json');receipt=load(source/'gui.inputs.json')
    binary=root/'sailhome-retention/formal-v2/colonization-window';assert sha(Path(load(source/'session.json')['binary']))==sha(binary)
    modes={m:root/f'retention-final-{m}' for m in ['zh','control','missing','baseline']}
    runs={m:load(path/'run.json') for m,path in modes.items()};assert all(r['state']==gui['state'] for r in runs.values())
    for m,path in modes.items():
        assert sha(path/'run.memory')==gui['state']['memory_sha256'] and sha(path/'raw.wav')==sha(source/'raw.wav')
        cmd=load(path/'command.json');assert Path(cmd[cmd.index('--replay-inputs')+1]).read_bytes()==(source/'gui.inputs.json').read_bytes()
        for s in (source/'save').glob('COLONY*.SAV'):assert sha(s)==sha(path/'save'/s.name)
    shots=[s.split() for s in (source/'gui.shots').read_text().splitlines()];cps={m:{x['label']:x for x in r['checkpoints']} for m,r in runs.items()};by_name={n:s for n,s in shots}
    for name,step in shots:
        label=f'cp-{step}'
        for f in ['memory_sha256','raw_sha256','palette_sha256']:assert len({cps[m][label][f] for m in modes})==1
        assert pixels(source/f'gui.{name}.png')==pixels(modes['zh']/f'run.{label}.png')
        assert pixels(modes['control']/f'run.{label}.png')==pixels(modes['missing']/f'run.{label}.png')
        with Image.open(modes['zh']/f'run.{label}.png') as x,Image.open(modes['baseline']/f'run.{label}.png') as y:
            box=ImageChops.difference(x.convert('RGB'),y.convert('RGB')).getbbox()
            if box:assert box[0]>=268 and box[1]>=444 and box[2]<=1024 and box[3]<=540,(name,box)
    body='GAME.TXT:@SAILHOME:0x00001B6F';safe=(268,444,1024,540);bodies=[]
    for name in ['east-2','hover-yes','hover-no','hover-yes-again']:
        with Image.open(source/f'gui.{name}.png') as im:bodies.append(im.convert('RGB').crop(safe).tobytes())
    assert len(set(bodies))==1
    events=gui['events'];expired=next(e['step'] for e in events if e.get('candidate_id')==body and e.get('stage')=='expired')
    assert expired>int(by_name['hover-yes-again']) and not any(e.get('candidate_id')==body and e.get('reason')=='superseded-by-new-dialog' for e in events)
    assert pixels(source/'gui.cancelled-world.png')==pixels(modes['baseline']/f'run.cp-{by_name["cancelled-world"]}.png')
    result={'result':'PASS_NORMAL_CHOICE_BODY_RETENTION','scope':'SAILHOME高海正文、兩選項、三次懸停與正常取消；不外推其他正文組','gui_shots':len(shots),'end':receipt['end'],'binary_sha256':sha(binary),'inputs_sha256':sha(source/'gui.inputs.json'),'state_sha256':gui['state']['memory_sha256'],'body_expired_after_cancel':expired,'source_original':sha(a.game/'VICEROY.EXE')}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (AssertionError,KeyError,FileNotFoundError) as e:print(f'FAIL: {e}',file=sys.stderr);sys.exit(1)
