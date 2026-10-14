"""目標186 R51 DRAFT：組裝31種小圖像的唯讀RAM／游標研究工具；不安裝HD。"""
from pathlib import Path
import argparse,hashlib,json,os,shutil
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--r49-root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];root=args.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0
assert root.is_relative_to('/out') and root.parent.stat().st_uid==os.getuid()

assert not root.exists();root.mkdir();sources=root/'sources';sources.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r49=args.r49_root.resolve()
assert sha(r49/'small-public-r1/build.json')=='324278b998dcfad66e4551d622a75a4287adfd6d4d5cc8d06155f6afd104f47d'
for name,want in {
 'build_hd_terrain_ram_lifecycle_probe.py':'facb6b45a16d94f83d64f0b03e56b507d1806ec012945e53e82d852d74760640',
 'check_hd_terrain_ram_lifecycle.py':'270e7fc079566c28aed984549780add00467e9fd39b0e949e7220f9b3bb16771',
}.items():assert sha(repo/'tools'/name)==want
build=json.loads((r49/'small-public-r1/build.json').read_bytes());rows=[]
for f in build['sources']:
 r=dict(f,opaque=f['opaque_pixels'],length=f['encoded_length']);rows.append(r)
 raw=r49/'decoded-public-r3/pixels'/f'{f["research_id"]:04d}.idx';assert sha(raw)==f['indexed_sha256']
 shutil.copyfile(raw,sources/f'building-{f["ordinal"]:03d}.pixels')
catalog={'kind':'DRAFT-small-image-source-bindings','original_file':'ICONS.SS','original_sha256':build['original_sha256'],'r49_build_sha256':sha(r49/'small-public-r1/build.json'),'sources':rows}
(sources/'source-catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
entry_src=r49/'entry-public-r1/lifecycle-r1/observed/draws.json';assert sha(entry_src)=='1b61c32909db439c3fdeb379a6b7b07ffa4a0f980c56c53e3dd3c2d76ab484cf';(sources/'lifecycle-r1/observed').mkdir(parents=True)
entry=sources/'lifecycle-r1/observed/draws.json';shutil.copyfile(entry_src,entry)
tool=repo/'tools/build_hd_terrain_ram_lifecycle_probe.py';s=tool.read_text()
s=s.replace("repo=Path(__file__).resolve().parents[1]","repo=Path('/repo')")
s=s.replace('4a89951c8a884eb5147d15c7b2a2fd1021f6079183ae5a10a493237c417c2b0e',sha(sources/'source-catalog.json'))
s=s.replace('ordinals={6,9,17,66,71,74,77,78,79,80,96,147,150}','ordinals='+repr({f['ordinal'] for f in rows}))
s=s.replace("r['file']=='PHYS0.SS'","r['file']=='ICONS.SS'")
s=s.replace(" and all(r['size']==[16,16] for r in rows)","")
old="'{%d,16,16,%d,%d,%s,%s,nil},'%(row['ordinal'],row['opaque'],row['length'],json.dumps(row['encoded_sha256']),json.dumps(row['indexed_sha256']))"
new="'{%d,%d,%d,%d,%d,%s,%s,nil},'%(row['ordinal'],*row['size'],row['opaque'],row['length'],json.dumps(row['encoded_sha256']),json.dumps(row['indexed_sha256']))"
assert old in s;s=s.replace(old,new)
s=s.replace('"PHYS0.SS": "deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16"','"ICONS.SS": "'+build['original_sha256']+'"')
s=s.replace("s=base.read_text()","s=base.read_text()\ns=s.replace('candidate := &buildingSources[i]', 'candidate := &buildingSources[i]\\n if int(record[4])!=candidate.Width || int(record[5])!=candidate.Height {continue}')")
s=s.replace("'DRAFT-terrain-raw-lifecycle-collector'","'DRAFT-small-images-raw-RAM-lifecycle-collector'")
(root/'build-small-ram.py').write_text(s)
tool=repo/'tools/check_hd_terrain_ram_lifecycle.py';s=tool.read_text()
s=s.replace('ORDINALS={6,9,17,66,71,74,77,78,79,80,96,147,150}','ORDINALS='+repr({f['ordinal'] for f in rows}))
s=s.replace('4a89951c8a884eb5147d15c7b2a2fd1021f6079183ae5a10a493237c417c2b0e',sha(sources/'source-catalog.json'))
s=s.replace("r['file']=='PHYS0.SS'","r['file']=='ICONS.SS'")
s=s.replace("len(pixels[n])==256","len(pixels[n])==r['size'][0]*r['size'][1]")
s=s.replace('3d9d7b70a3f6046c0d54ce32aa94189b367cd7f031ea4b8f7c7163bd52bc094f',sha(entry))
s=s.replace("len(before)==len(after)==256","len(before)==len(after)==w*h")
s=s.replace('y+k//16','y+k//c[\'record_words\'][4]').replace('x+k%16','x+k%c[\'record_words\'][4]')
s=s.replace("if cell['ordinal']==79:","if cell['ordinal'] in ORDINALS:")
s=s.replace('terrain079-ram-copies.json','small-ram-copies.json').replace('PASS_TERRAIN_RAM_RESEARCH_NATIVE_MODEL','PASS_SMALL_IMAGE_RAM_RESEARCH_NATIVE_MODEL')
s=s.replace('TERRAIN.SS及8×8別名未建立來源契約。','限31種小圖像；其他圖像、未知游標、動畫與正式HD未驗。')
(root/'check-small-ram.py').write_text(s)
meta={'kind':'DRAFT-small-image-raw-RAM-research-adaptation','sources':31,'native_entry_sha256':sha(entry),'source_catalog_sha256':sha(sources/'source-catalog.json'),'reference_tools':{p.name:sha(p) for p in [repo/'tools/build_hd_terrain_ram_lifecycle_probe.py',repo/'tools/check_hd_terrain_ram_lifecycle.py']},'changes':['31 fixed original ICONS.SS ordinals and actual widths/heights','dimension guard before complete encoding hash','same original collectors and accepted cursor/main-RAM semantics','all 31 source RAM examples retained'],'production_connected':False}
(root/'prepare.json').write_text(json.dumps(meta,indent=2)+'\n')
print('PASS_SMALL_IMAGE_RAM_RESEARCH_PREPARED',len(rows),meta['source_catalog_sha256'],flush=True)

from pathlib import Path
import json,os
assert root.stat().st_uid==os.getuid()
s=(repo/'tools/test_hd_terrain_ram_lifecycle.py').read_text()
start=s.index('root.mkdir()')
tail=s[start:]
tail=tail.replace("dest/'point-042.terrain-model.json'","dest/target_name")
tail=tail.replace("d['ram_saves_verified']==5886 and d['ram_restorations_accepted']==4370","d['ram_saves_verified']==547 and d['ram_restorations_accepted']==422")
tail=tail.replace("Path(__file__).resolve().with_name('check_hd_terrain_ram_lifecycle.py')","Path(__file__).resolve().with_name('check-small-ram.py')")
tail=tail.replace('PASS_TERRAIN_RAM_12_NEGATIVES_AND_POSITIVE_RECHECK','PASS_SMALL_IMAGE_RAM_12_NEGATIVES_AND_POSITIVE_RECHECK')
tail=tail.replace('第079幀來源','小圖像來源')
tail=tail.replace("(saved['event']['old']+1)&255","(old_saved['event']['old']+1)&255")
tail=tail.replace("source=saved if side=='save' else target;index=source['event_index'];insert=field.startswith('insert-')", "source=(old_saved if field=='old' else saved) if side=='save' else target;index=source['event_index'];insert=field.startswith('insert-')")
header='''from pathlib import Path
import copy,hashlib,importlib.util,json,os
out=Path('/out');root=out/'negatives-r3';assert not root.exists() and root.parent.stat().st_uid==os.getuid()==1000
observed=out/'lifecycle-r1/observed';control=out/'lifecycle-r1/control';sources=out/'sources';baseline=out/'model-r1'
copies=json.loads((baseline/'small-ram-copies.json').read_bytes())
from check_hd_building_nine_lifecycle import event_stream
save_indices={c['event_index'] for c in copies if c['kind']=='save'}
ram_seen=set();known_save_indices=set()
for i,e in enumerate(event_stream(observed/'writes.json')):
 if e['kind']=='ram-write':
  if i in save_indices and e['linear'] in ram_seen:known_save_indices.add(i)
  ram_seen.add(e['linear'])
old_saved=next(c for c in copies if c['kind']=='save' and c['event_index'] in known_save_indices)
proof=json.loads((baseline/'check.json').read_bytes());selected=None
for point in proof['points']:
 name=point['main_owners_file'];owners=json.loads((baseline/name).read_bytes())
 for c in copies:
  if c['kind']=='restore' and c['event']['step']<=point['step']:
   position=str(c['destination']-0x2cae0)
   if owners.get(position)==c['cell']:
    selected=(c,position,name);break
 if selected:break
assert selected is not None
target,position,target_name=selected
saved=next(x for x in reversed(copies) if x['kind']=='save' and x['destination']==target['source'] and x['event_index']<target['event_index'] and x['cell']==target['cell'])
spec=importlib.util.spec_from_file_location('small_ram_checker',Path('/out/check-small-ram.py'))
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
read0,event0=checker.read,checker.event_stream
print('TARGET_SMALL_IMAGE_RAM_RESTORE',target['cell']['ordinal'],target['event']['step'],target_name,position,flush=True)
'''
(root/'test-small-ram.py').write_text(header+tail)
print('PASS_SMALL_IMAGE_RAM_NEGATIVES_PREPARED',flush=True)
