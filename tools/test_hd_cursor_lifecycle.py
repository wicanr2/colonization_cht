"""以原版游標收據的失真樣本檢查拒絕條件，不修改原始收據。"""
from pathlib import Path
import argparse,copy,hashlib,json,os,shutil,subprocess,sys

p=argparse.ArgumentParser(description=__doc__)
for name in ['root','catalog','game','inputs','points','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();assert Path('/.dockerenv').is_file() and os.getuid()!=0 and a.output.is_relative_to('/out') and not a.output.exists()
for name in ['VICEROY.EXE','CURSOR.SS']:
 if not (a.game/name).is_file():print('SKIP：缺少合法原版 '+name);sys.exit(77)
a.output.mkdir();fixture=a.output/'fixture';shutil.copytree(a.root/'lifecycle-r1',fixture)
read=lambda p:json.loads(p.read_bytes());write=lambda p,d:p.write_text(json.dumps(d)+'\n')
checker=Path(__file__).with_name('check_hd_cursor_lifecycle.py')
common=['python3',str(checker),'--observed',str(fixture/'observed'),'--control',str(fixture/'control'),'--catalog',str(a.catalog),'--game',str(a.game),'--inputs',str(a.inputs),'--points',str(a.points)]
def run(name,expect):
 result=subprocess.run(common+['--output',str(a.output/(name+'.json'))],capture_output=True,text=True,timeout=15)
 (a.output/(name+'.log')).write_text(result.stdout+result.stderr)
 assert (result.returncode==0)==expect,(name,result.stdout,result.stderr)
 if not expect:assert 'AssertionError' in result.stderr and 'TypeError' not in result.stderr,(name,result.stderr)
 return {'name':name,'rejected':not expect,'log_sha256':hashlib.sha256((a.output/(name+'.log')).read_bytes()).hexdigest()}
run('baseline',True)
obs=fixture/'observed';draw=obs/'draws.json';events=obs/'writes.json';control=fixture/'control/draws.json'
rows=read(events);source=next(i for i,e in enumerate(rows) if e['kind']=='asset_draw');copied=next(i for i,e in enumerate(rows) if e['kind']=='cursor_ram' and e['call']==1)
cases=[
 ('encoded-source',draw,lambda d:d['calls'][0].__setitem__('source_encoded_sha256','0'*64)),
 ('record-address',draw,lambda d:d['calls'][0].__setitem__('record_far','4F0B:0043')),
 ('temporary-canvas',draw,lambda d:d['calls'][0].__setitem__('canvas_linear',d['calls'][0]['canvas_linear']+1)),
 ('source-old-value',events,lambda d:d[source].__setitem__('old',254)),
 ('source-write-value',events,lambda d:d[source].__setitem__('value',d[source]['value']^1)),
 ('missing-source-write',events,lambda d:d.pop(source)),
 ('extra-source-write',events,lambda d:d.append(copy.deepcopy(d[source]))),
 ('copy-source-segment',events,lambda d:d[copied]['segments'].__setitem__(3,d[copied]['segments'][3]+1)),
 ('copy-destination-register',events,lambda d:d[copied]['registers'].__setitem__(7,d[copied]['registers'][7]+1)),
 ('unverified-copy-site',events,lambda d:d[copied].__setitem__('site','0CBA:00CA')),
 ('missing-copy-write',events,lambda d:d.pop(copied)),
 ('control-register',control,lambda d:d['end']['registers'].__setitem__(0,d['end']['registers'][0]^1)),
 ('cursor-source-bytes',obs/'point-000.cursor',lambda d:bytes([d[0]^1])+d[1:]),
 ('pixel-outside-cursor',obs/'point-000.idx',lambda d:bytes([d[0]^1])+d[1:]),
]
results=[]
for name,path,mutate in cases:
 original=path.read_bytes()
 try:
  if path.suffix=='.json':data=json.loads(original);mutate(data);write(path,data)
  else:path.write_bytes(mutate(original))
  results.append(run(name,False))
 finally:path.write_bytes(original)
run('restored',True)
assert len(results)==14 and all(r['rejected'] for r in results)
report={'result':'PASS_STANDARD_CURSOR_FOURTEEN_EVIDENCE_NEGATIVES','cases':results,'checker_sha256':hashlib.sha256(checker.read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'restored_baseline_passed':True,'original_receipts_unchanged':all((fixture/'observed'/p.name).read_bytes()==p.read_bytes() for p in (a.root/'lifecycle-r1/observed').iterdir() if p.is_file()),'production_hd':False}
assert report['original_receipts_unchanged'];(a.output/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(report['result'],flush=True)
