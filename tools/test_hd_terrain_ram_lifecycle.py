"""R47 DRAFT：由原始正向RAM事件做單項變異，不製造正向遊戲狀態。"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os
p=argparse.ArgumentParser(description=__doc__)
for name in ['evidence-root','sources','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();out=a.evidence_root.resolve();root=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and root.is_relative_to('/out') and root.parent.stat().st_uid==os.getuid() and not root.exists()
observed=out/'ram-oracle-r1/observed';control=out/'ram-oracle-r1/control'
sources=a.sources.resolve()
baseline=out/'ram-model-r2'
copies=json.loads((baseline/'terrain079-ram-copies.json').read_bytes())
owners=json.loads((baseline/'point-042.terrain-model.json').read_bytes())
target=next(x for x in reversed(copies) if x['kind']=='restore' and x['event']['step']<=110600000 and str(x['destination']-0x2cae0) in owners)
saved=next(x for x in reversed(copies) if x['kind']=='save' and x['destination']==target['source'] and x['event_index']<target['event_index'])
position=str(target['destination']-0x2cae0);assert owners[position]['ordinal']==79
spec=importlib.util.spec_from_file_location('terrain_ram_checker',Path(__file__).resolve().with_name('check_hd_terrain_ram_lifecycle.py'))
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
read0,event0=checker.read,checker.event_stream
root.mkdir()
cases=[
 ('save-unknown-code','save','code16','00'*16),
 ('save-unaccepted-site','save','site','0C9F:00CA'),
 ('save-wrong-source','save','ds',0x2000),
 ('save-wrong-old','save','old',(saved['event']['old']+1)&255),
 ('restore-unknown-code','restore','code16','00'*16),
 ('restore-unaccepted-site','restore','site','0C9F:00CA'),
 ('restore-wrong-source','restore','ds',0x2000),
 ('restore-wrong-destination','restore','di',target['event']['registers'][7]-2),
 ('restore-wrapped-source','restore','si',65535),
 ('restore-stale-value','restore','value',(target['event']['value']+1)&255),
 ('ram-unknown-same-write','save','insert-ram',None),
 ('main-unknown-same-write','restore','insert-main',None),
]
results=[]
for name,side,field,value in cases:
 source=saved if side=='save' else target;index=source['event_index'];insert=field.startswith('insert-')
 def stream(path):
  for i,e in enumerate(event0(path)):
   if i!=index:
    yield e;continue
   e=copy.deepcopy(e)
   if insert:
    yield e
    extra=copy.deepcopy(e);extra['old']=extra['value'];extra['code16']='00'*16;extra['site']='FFFF:0000'
    yield extra
   else:
    if field in ['ds']:e['segments'][3]=value
    elif field=='di':e['registers'][7]=value
    elif field=='si':e['registers'][6]=value
    else:e[field]=value
    yield e
 def read(path):
  d=read0(path)
  if insert and path==observed/'draws.json':
   d=copy.deepcopy(d);d['raw_event_count']+=1
   for p in d['checkpoints']:
    if p['event_count']>index:p['event_count']+=1
  return d
 checker.event_stream,checker.read=stream,read
 dest=root/name;dest.mkdir()
 try:
  result=checker.check(observed,control,sources,dest)
  remaining=json.loads((dest/'point-042.terrain-model.json').read_bytes())
  assert position not in remaining,'變異事件仍授予第079幀來源：'+name
  results.append({'case':name,'result':'PASS_SOURCE_REVOKED','event_index':index,'position':int(position),'ram_restores':result['ram_restorations_accepted']})
 except ValueError as error:
  results.append({'case':name,'result':'PASS_INVALID_EVIDENCE_REJECTED','event_index':index,'reason':str(error)})
 finally:
  checker.event_stream,checker.read=event0,read0
 print('PASS_TERRAIN_RAM_NEGATIVE',name,results[-1]['result'],flush=True)
positive=root/'positive-after-negatives';positive.mkdir()
d=checker.check(observed,control,sources,positive)
assert d['ram_saves_verified']==5886 and d['ram_restorations_accepted']==4370
for index in range(49):
 name=f'point-{index:03d}.terrain-model.json'
 assert (positive/name).read_bytes()==(baseline/name).read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'result':'PASS_TERRAIN_RAM_12_NEGATIVES_AND_POSITIVE_RECHECK','cases':results,'positive_after_negatives':True,'all_49_positive_models_equal':True,'target_restore':target,'target_save':saved,'checker_sha256':sha(Path(__file__).resolve().with_name('check_hd_terrain_ram_lifecycle.py')),'test_sha256':sha(Path(__file__)),'production_connected':False}
(root/'check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(report['result'],flush=True)
