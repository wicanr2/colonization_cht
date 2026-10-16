"""R49 DRAFT：從本機解碼收據建立不含原版像素的來源索引。"""
import argparse,hashlib,json,os
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
for name in ['catalog','manifest','assets','output']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--entry-report',type=Path,help='可選：R49正常路徑全SS唯讀入口收據')
parser.add_argument('--small-report',type=Path,help='可選：R49的31種小圖像逐寫審查收據')
parser.add_argument('--small-build',type=Path,help='與small-report一起使用的小圖像來源綁定')
parser.add_argument('--small-ram-root',type=Path,help='可選：R51小圖像RAM／游標研究根目錄')
parser.add_argument('--cursor-report',type=Path,help='可選：R59一般游標來源與定位收據')
parser.add_argument('--cursor-ready-report',type=Path,help='與cursor-report一起使用的R60 READY審查收據')
parser.add_argument('--cursor-conformed-report',type=Path,help='正式游標來源必附的R61限定CONFORMED審查收據')
parser.add_argument('--terrain-batch-report',type=Path,help='可選：規格067的R62十三來源正常GUI逐寫審查，不授予HD信用')
parser.add_argument('--terrain-batch-ready-report',type=Path,help='規格067 READY候選及合成契約審查')
parser.add_argument('--terrain-batch-conformed-report',type=Path,help='正式十二來源的完整驗收與既有素材繼承審查')
parser.add_argument('--small-terrain-report',type=Path,help='規格068十五個AX槽位的原版來源審查')
parser.add_argument('--small-terrain-ready-report',type=Path,help='規格068八個8×8來源的READY審查')
parser.add_argument('--small-terrain-conformed-report',type=Path,help='規格068正式八來源的完整驗收與58種素材繼承審查')
a=parser.parse_args();out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.parent.stat().st_uid==os.getuid() and not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(a.catalog.read_bytes());manifest=json.loads(a.manifest.read_bytes())
assert not d['summary']['failed_files'] and d['summary']['ss_files']==206 and d['summary']['pik_files']==35
assert d['summary']['ss_frame_records']==1517 and len(d['frames'])==1552
allowed=['research_id','file','file_sha256','ordinal','size','header_part1_offset','data_part3_offset','encoded_length','other_header_fields','decode_status','encoded_sha256','indexed_sha256','opaque_pixels','transparency_index','header_part0_hex','pixel_part1_offset','pixel_bytes','part1_trailing_bytes','embedded_palette']
frames=[{k:f[k] for k in allowed if k in f} for f in d['frames']]
for f in frames:
 f['runtime_source_evidence']='not_assessed_by_this_inventory'
 f['animation_evidence']='not_assessed_by_this_inventory'
 f['formal_assets']=[]
bindings=[]
for name,asset in manifest['assets'].items():
 assert sha(a.assets/name)==asset['sha256'] and (a.assets/name).stat().st_size==asset['bytes']
 if 'original_binding' in asset:
  original=asset['original_binding'];source_files=[n for n in original if n.endswith('.SS')]
  assert len(source_files)==1;file=source_files[0];file_sha=original[file];encoded=original['encoded_frame_sha256'];ordinal=None
 elif 'original_source' in asset:
  original=asset['original_source'];file=original['file'];file_sha=original['sha256'];encoded=original['encoded_sha256'];ordinal=original['ordinal']
 else:raise ValueError('未支援的正式來源紀錄：'+name)
 matches=[f for f in frames if f['file']==file and f['file_sha256']==file_sha and f.get('encoded_sha256')==encoded and (ordinal is None or f['ordinal']==ordinal)]
 assert len(matches)==1,(name,matches)
 f=matches[0];f['formal_assets'].append(name)
 bindings.append({'asset':name,'asset_sha256':asset['sha256'],'source_research_id':f['research_id'],'source_file':file,'source_ordinal':f['ordinal'],'source_encoded_sha256':f['encoded_sha256'],'spec':asset.get('spec',manifest['spec']),'claim':'matches verified formal manifest; conformance scope remains in cited spec'})
ready=[f for f in frames if f['file']=='PHYS0.SS' and f['ordinal']==79 and f.get('encoded_sha256')=='a8a861754068c86a9c150442f7b07f1fbd297d82b8e5dcb2e3ee108bde4dc84c']
assert len(ready)==1
ready[0]['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/062-hd-sea-draw-lifecycle.md','section':'2026-10-15 R58正式驗收與限定CONFORMED','formal_connected':bool(ready[0]['formal_assets'])}
small_review=None
if a.small_terrain_ready_report:
 small_review=json.loads(a.small_terrain_ready_report.read_bytes())
 assert small_review['result']=='PASS_SMALL_TERRAIN_READY_REVIEW' and small_review['spec_state']=='READY'
 assert small_review['native_source_report_sha256']==sha(a.small_terrain_report)
if a.small_terrain_conformed_report:
 assert small_review is not None and a.terrain_batch_conformed_report
 small_review=json.loads(a.small_terrain_conformed_report.read_bytes())
 assert small_review['result']=='PASS_SMALL_TERRAIN_FORMAL_CONFORMANCE_REVIEW' and small_review['spec_state']=='CONFORMED'
 assert small_review['formal_assets']==66 and small_review['manifest_sha256']==sha(a.manifest)
 assert small_review['ready_review_sha256']==sha(a.small_terrain_ready_report)
 assert len(small_review['unchanged_inherited_assets'])==58
 assert all(manifest['assets'][n]['sha256']==h for n,h in small_review['unchanged_inherited_assets'].items())
expected_assets=66 if a.small_terrain_conformed_report else 58 if a.terrain_batch_conformed_report else 46
assert len(bindings)==expected_assets and sum(bool(f['formal_assets']) for f in frames)==expected_assets
batch_review=None
if a.terrain_batch_ready_report:
 batch_review=json.loads(a.terrain_batch_ready_report.read_bytes())
 assert batch_review['result']=='PASS_WORLD_TERRAIN_READY_REVIEW' and batch_review['spec_state']=='READY'
 assert batch_review['native_source_report_sha256']==sha(a.terrain_batch_report)
if a.terrain_batch_conformed_report:
 assert batch_review is not None
 batch_review=json.loads(a.terrain_batch_conformed_report.read_bytes())
 assert batch_review['result']=='PASS_WORLD_TERRAIN_FORMAL_CONFORMANCE_REVIEW' and batch_review['spec_state']=='CONFORMED'
 assert batch_review['formal_assets']==58
 if a.small_terrain_conformed_report:
  assert small_review['inherited_manifest_sha256']==batch_review['manifest_sha256']
  assert small_review['inherited_terrain_batch_conformance_sha256']==sha(a.terrain_batch_conformed_report)
 else:assert batch_review['manifest_sha256']==sha(a.manifest)
 assert batch_review['ready_review_sha256']==sha(a.terrain_batch_ready_report)
 assert len(batch_review['unchanged_inherited_assets'])==46
 assert all(manifest['assets'][name]['sha256']==digest for name,digest in batch_review['unchanged_inherited_assets'].items())
entry_evidence=None
if a.entry_report:
 entry=json.loads(a.entry_report.read_bytes())
 assert entry['result']=='PASS_READONLY_FULL_SS_ENTRY_CATALOG' and entry['original_state_and_saves_equal'] is True
 assert entry['checkpoints']==49 and entry['dos_inputs']==53 and entry['calls']==2005
 assert entry['matched_calls']==2005 and entry['unique_match_calls']==1931 and entry['ambiguous_match_calls']==74 and entry['unmapped_calls']==0
 assert entry['input_hashes']=={f['file']:f['sha256'] for f in d['files'] if f['format']=='SS'}
 by_id={f['research_id']:f for f in frames}
 for group in entry['groups'].values():
  ids=group['candidate_research_ids'];assert ids and len(ids)==len(set(ids))
  for source_id in ids:
   f=by_id[source_id];assert f['encoded_sha256']==group['source_hash']
   assert any(s['file']==f['file'] and s['ordinal']==f['ordinal'] and s['size']==f['size'] for s in group['sources'])
   f['runtime_source_evidence']='entry_match_only' if len(ids)==1 else 'entry_alias_candidates_only'
   f['normal_entry_sample']={'calls':group['calls'],'candidate_research_ids':ids,'source_far':group['source_far'],'record_far':group['record_far'],'ax':group['ax'],'rectangles':group['rectangles'],'claim':'0D46:000A entry only; writes, visibility and animation not granted'}
 entry_evidence={'report_sha256':sha(a.entry_report),'source_sha256':entry['source_sha256'],'binary_sha256':entry['binary_sha256'],'checkpoints':49,'dos_inputs':53,'calls':2005,'unique_match_calls':1931,'ambiguous_match_calls':74,'unmapped_calls':0,'observer_state_and_saves_equal':True,'claim':entry['claim']}
public={'schema':1,'kind':'DRAFT-native-source-index-not-complete-player-coverage','source_receipt_sha256':sha(a.catalog),'decoder':d['tools'],'formal_manifest_sha256':sha(a.manifest),'summary':d['summary'],'coverage_limits':{'player_visible_graphics_denominator':'unknown','formal_asset_bindings':len(bindings),'additional_ready_source_contracts':sum(f.get('source_contract_reference',{}).get('state')=='READY' and not f.get('source_contract_reference',{}).get('formal_connected') for f in frames),'complete_hd':False,'contains_original_pixels':False,'other_formats_and_program_drawn_graphics':'not_assessed'},'files':d['files'],'frames':frames,'declared_encoding_alias_groups':d['declared_encoding_alias_groups'],'formal_bindings':bindings,'limitations':['檔案解碼、索引指紋與幾何事實，不授予未驗來源的正式HD或動畫信用。','來源列包含空尺寸、零不透明像素與編碼別名；不可因尚未命中就排除。','正式素材只按現行清冊連結，完整驗收範圍以所連規格為準。','其他格式及程式直接繪圖尚未分類，玩家可見圖像的完整分母仍未知。','原版像素、色盤與預覽只留本機，本索引不含原始素材位元組。']}
if entry_evidence:public['normal_entry_evidence']=entry_evidence
assert bool(a.small_report)==bool(a.small_build)
if a.small_report:
 assert entry_evidence is not None
 small=json.loads(a.small_report.read_bytes());build=json.loads(a.small_build.read_bytes())
 assert small['result']=='PASS_SMALL_IMAGE_SOURCE_WRITES_49_NATIVE_POINTS' and small['production_connected'] is False
 assert small['sources']==31 and small['source_calls']==420 and small['raw_events']==131722 and len(small['checkpoints'])==49
 assert build['source_receipt_sha256']==sha(a.catalog) and build['entry_report_sha256']==sha(a.entry_report)
 assert build['source_count']==31 and len(build['sources'])==31 and build['production_connected'] is False
 for source in build['sources']:
  f=by_id[source['research_id']]
  assert f['file']==source['file']=='ICONS.SS' and f['file_sha256']==source['file_sha256']==build['original_sha256']
  assert f['indexed_sha256']==source['indexed_sha256'] and f['encoded_sha256']==source['encoded_sha256']
  f['small_image_draw_sample']={'calls':f['normal_entry_sample']['calls'],'state':'verified writes on 49 normal points; not HD conformance','report_sha256':sha(a.small_report),'unknown_writes':'revoke including same value','cursor_restoration_verified':False,'ram_restoration_verified':False}
 public['small_image_write_evidence']={'report_sha256':sha(a.small_report),'build_sha256':sha(a.small_build),'source_sha256':build['source_sha256'],'binary_sha256':build['binary_sha256'],'sources':31,'calls':420,'raw_events':131722,'negative_scope':'separate true-receipt tests','production_connected':False}
if a.small_ram_root:
 assert a.small_report and a.small_build
 root=a.small_ram_root;report_path=root/'model-r1/check.json';report=json.loads(report_path.read_bytes())
 assert report['result']=='PASS_SMALL_IMAGE_RAM_RESEARCH_NATIVE_MODEL' and report['production_connected'] is False
 assert report['source_calls']==420 and report['raw_events']==180696 and len(report['points'])==49
 assert report['ram_saves_verified']==547 and report['ram_restorations_accepted']==422 and report['verified_cursor_restores']==260
 catalog_path=root/'sources/source-catalog.json';catalog=json.loads(catalog_path.read_bytes())
 assert catalog['r49_build_sha256']==sha(a.small_build) and len(catalog['sources'])==31
 copies=json.loads((root/'model-r1/small-ram-copies.json').read_bytes())
 counts={}
 for copy in copies:
  assert copy['kind'] in ['save','restore'];ordinal=copy['cell']['ordinal']
  count=counts.setdefault(ordinal,{'ram_saves':0,'ram_restores':0,'cursor_restores':0})
  count['ram_saves' if copy['kind']=='save' else 'ram_restores']+=1
 assert sum(c['ram_saves'] for c in counts.values())==547 and sum(c['ram_restores'] for c in counts.values())==422
 for ordinal,value in report['cursor_restores_by_ordinal'].items():
  counts.setdefault(int(ordinal),{'ram_saves':0,'ram_restores':0,'cursor_restores':0})['cursor_restores']=value
 for ordinal,count in counts.items():
  source=next(s for s in catalog['sources'] if s['ordinal']==ordinal)
  f=by_id[source['research_id']]
  assert f['file']=='ICONS.SS' and f['ordinal']==ordinal and f['indexed_sha256']==source['indexed_sha256'] and f['encoded_sha256']==source['encoded_sha256']
  f['small_image_restore_sample']=dict(count,report_sha256=sha(report_path),state='verified native samples; not production HD or animation',cursor_bitmap_sha256='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03')
 public['small_image_restore_evidence']={'report_sha256':sha(report_path),'source_catalog_sha256':sha(catalog_path),'source_calls':420,'raw_events':180696,'ram_saves':547,'ram_restores':422,'cursor_restores':260,'by_original_ordinal':counts,'production_connected':False,'claim':'RAM positive examples only ordinal 005; cursor positive examples 005 and 062; other frames not granted restoration coverage'}
assert bool(a.cursor_report)==bool(a.cursor_ready_report)
assert not a.cursor_conformed_report or a.cursor_report
if a.cursor_report:
 cursor=json.loads(a.cursor_report.read_bytes());review=json.loads(a.cursor_ready_report.read_bytes())
 assert cursor['result']=='PASS_STANDARD_CURSOR_ORIGINAL_SOURCE_RAM_AND_49_POSITIONS' and cursor['original_state_and_saves_equal'] is True
 assert len(cursor['source_calls'])==2 and len(cursor['positions'])==49 and cursor['cursor_sha256']=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03'
 assert review['result']=='PASS_STANDARD_CURSOR_READY_REVIEW' and review['spec_state']=='READY' and review['native_source_report_sha256']==sha(a.cursor_report)
 f=next(f for f in frames if f['file']=='CURSOR.SS' and f['ordinal']==0)
 assert f['research_id']==309 and f['file_sha256']==cursor['file_sha256']['CURSOR.SS'] and f['indexed_sha256']==cursor['source_indexed_sha256']
 f['runtime_source_evidence']='confirmed standard cursor source, RAM copy and input-origin placement within fixed normal paths'
 assert bool(f['formal_assets'])==bool(a.cursor_conformed_report)
 if a.cursor_conformed_report:
  conformed=json.loads(a.cursor_conformed_report.read_bytes())
  assert conformed['result']=='PASS_CURSOR_FORMAL_CONFORMANCE_REVIEW' and conformed['spec_state']=='CONFORMED'
  assert conformed['formal_assets']==46
  if conformed['manifest_sha256']!=sha(a.manifest):
   assert a.terrain_batch_conformed_report and batch_review['inherited_cursor_conformance_sha256']==sha(a.cursor_conformed_report)
   assert batch_review['inherited_manifest_sha256']==conformed['manifest_sha256']
   assert batch_review['unchanged_inherited_assets']['cursor-000.png']==manifest['assets']['cursor-000.png']['sha256']
 f['source_contract_reference']={'state':'CONFORMED' if a.cursor_conformed_report else 'READY','spec':'docs/spec/066-hd-standard-cursor.md','section':'2026-10-15 R61一般游標正式驗收與限定CONFORMED' if a.cursor_conformed_report else '2026-10-15 R60一般游標顯示契約READY','formal_connected':bool(f['formal_assets'])}
 if a.cursor_conformed_report:f['source_contract_reference']['conformance_review_sha256']=sha(a.cursor_conformed_report)
 f['standard_cursor_sample']={'native_source_report_sha256':sha(a.cursor_report),'ready_review_sha256':sha(a.cursor_ready_report),'source_calls':2,'native_positions':49,'runtime_bitmap_sha256':cursor['cursor_sha256'],'visible_opaque_cells':82,'input_origin':[0,0],'gui_snapshots':29,'edge_samples':9,'fully_clipped_edge_samples':1,'claim':'standard cursor only; other cursor sources and hidden states not granted coverage'}
 public['coverage_limits']['additional_ready_source_contracts']=sum(f.get('source_contract_reference',{}).get('state')=='READY' and not f.get('source_contract_reference',{}).get('formal_connected') for f in frames)
if a.terrain_batch_report:
 batch=json.loads(a.terrain_batch_report.read_bytes())
 assert batch['result']=='PASS_TERRAIN_BATCH_NATIVE_SOURCE_RAM_AND_29_GUI_POINTS' and batch['original_state_and_saves_equal'] is True
 assert batch['production_connected'] is False and batch['ready'] is False
 assert batch['new_targets']==[6,9,17,66,71,74,77,78,80,96,147,150] and len(batch['sources'])==13 and len(batch['points'])==29
 assert batch['source_calls']==101 and batch['raw_events']==194628 and batch['stage_main_transfers']==12823
 assert batch['ram_saves']==5886 and batch['ram_restores']==4370 and batch['cursor_restores']==10012 and batch['dos_inputs']==109
 for key,sample in batch['sources'].items():
  ordinal=int(key);assert sample['ordinal']==ordinal
  f=next(f for f in frames if f['file']=='PHYS0.SS' and f['ordinal']==ordinal)
  assert f['file_sha256']=='deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16'
  assert f['encoded_sha256']==sample['encoded_sha256'] and f['indexed_sha256']==sample['indexed_sha256'] and f['size']==sample['size']
  assert f['opaque_pixels']==sample['opaque_cells'] and sample['draw_calls']>0 and sample['stage_main_transfers']>0 and sample['vga_visible_pixels']>0
  f['terrain_batch_native_sample']=dict(sample,report_sha256=sha(a.terrain_batch_report),state='confirmed native source samples; no new HD or animation credit')
  if sample['new_target']:
   assert bool(f['formal_assets'])==bool(a.terrain_batch_conformed_report)
   f['runtime_source_evidence']='confirmed draw, stage transfer and enumerated native restore samples within fixed normal paths'
   f['source_contract_reference']={'state':batch_review['spec_state'] if batch_review else 'DRAFT','spec':'docs/spec/067-hd-world-terrain-batch.md','formal_connected':bool(f['formal_assets'])}
   if batch_review:f['source_contract_reference']['review_sha256']=sha(a.terrain_batch_conformed_report or a.terrain_batch_ready_report)
 public['terrain_batch_native_evidence']={'report_sha256':sha(a.terrain_batch_report),'sources':13,'new_targets':batch['new_targets'],'checkpoints':29,'dos_inputs':109,'input_sha256':batch['input_sha256'],'source_calls':101,'stage_main_transfers':12823,'ram_saves':5886,'ram_restores':4370,'cursor_restores':10012,'production_connected':False,'claim':'native source evidence only; positive counts remain per ordinal; zero examples do not grant restore coverage'}
if a.small_terrain_report:
 small=json.loads(a.small_terrain_report.read_bytes());targets={112,113,116,119,126,127,136,139}
 assert small['result']=='PASS_SMALL_TERRAIN_15_SOURCES_AND_65_ORIGINAL_MODELS' and small['original_state_and_saves_equal']
 assert len(small['sources'])==15 and small['checkpoints']==65 and small['dos_inputs']==143 and not small['production_connected']
 for key,sample in small['sources'].items():
  n=int(key);f=next(f for f in frames if f['file']=='PHYS0.SS' and f['ordinal']==n)
  assert f['file_sha256']=='deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16'
  assert f['encoded_sha256']==sample['encoded_sha256'] and f['indexed_sha256']==sample['indexed_sha256'] and f['size']==sample['size']
  assert f['opaque_pixels']==sample['opaque_cells'] and sample['ax']==n+1 and sample['draw_calls']>0
  f['small_terrain_native_sample']=dict(sample,report_sha256=sha(a.small_terrain_report),state='confirmed runtime AX slot and complete native source; shared encoding retained; visibility limited to sampled points')
  f['runtime_source_evidence']='confirmed runtime AX slot, exact source record, complete writes and native model within fixed normal paths'
  if n in targets:
   assert sample['size']==[8,8] and sample['visible_native_cells']>0
   assert bool(f['formal_assets'])==bool(a.small_terrain_conformed_report)
   f['source_contract_reference']={'state':small_review['spec_state'] if small_review else 'DRAFT','spec':'docs/spec/068-hd-small-world-terrain.md','formal_connected':bool(f['formal_assets'])}
   if small_review:f['source_contract_reference']['review_sha256']=sha(a.small_terrain_conformed_report or a.small_terrain_ready_report)
  else:assert sample['visible_native_cells']==0 and not f['formal_assets']
 public['small_terrain_native_evidence']={'report_sha256':sha(a.small_terrain_report),'sources':15,'targets':sorted(targets),'checkpoints':65,'dos_inputs':143,'production_connected':False,'claim':'native evidence only; zero visible samples do not imply unreachable sources; HD scope remains in spec068'}
public['coverage_limits']['additional_ready_source_contracts']=sum(f.get('source_contract_reference',{}).get('state')=='READY' and not f.get('source_contract_reference',{}).get('formal_connected') for f in frames)
out.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
print('PASS_METADATA_ONLY_FULL_SOURCE_INDEX',len(frames),len(bindings),sha(out),flush=True)
