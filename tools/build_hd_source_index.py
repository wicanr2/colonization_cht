"""R49 DRAFT：從本機解碼收據建立不含原版像素的來源索引。"""
import argparse,hashlib,json,os
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
for name in ['catalog','manifest','assets','output']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--entry-report',type=Path,help='可選：R49正常路徑全SS唯讀入口收據')
parser.add_argument('--cold-start-entry-report',type=Path,help='可選：規格069由步數0起的全SS入口收據，不授予HD信用')
parser.add_argument('--background-source-report',type=Path,help='可選：規格069主選單背景／底紋逐寫模型，不授予HD信用')
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
parser.add_argument('--menu-ready-report',type=Path,help='規格069主選單兩來源的READY審查')
parser.add_argument('--menu-conformed-report',type=Path,help='規格069正式兩來源及66種素材繼承審查')
parser.add_argument('--world-wood-ready-report',type=Path,help='規格069世界木紋READY審查')
parser.add_argument('--world-wood-conformed-report',type=Path,help='規格069世界木紋正式驗收及68種素材繼承審查')
parser.add_argument('--parch-ready-report',type=Path,help='規格069紙質底紋READY審查')
parser.add_argument('--parch-conformed-report',type=Path,help='規格069紙質底紋正式驗收及69種素材繼承審查')
parser.add_argument('--new-game-ready-report',type=Path,help='規格069新遊戲兩背景READY審查')
parser.add_argument('--new-game-conformed-report',type=Path,help='規格069新遊戲正式驗收及70種素材繼承審查')
parser.add_argument('--custom-world-ready-report',type=Path,help='規格069自訂地圖READY審查')
parser.add_argument('--custom-world-conformed-report',type=Path,help='規格069自訂地圖正式驗收及72種素材繼承審查')
parser.add_argument('--unit-report',type=Path,help='規格070正常單位圖鑑的獨立逐寫檢查收據，不授予HD信用')
parser.add_argument('--unit-build',type=Path,help='與unit-report一起使用的131候選來源綁定')
parser.add_argument('--ship-ready-report',type=Path,help='規格070五艘船的單幀PNG READY審查')
parser.add_argument('--ship-conformed-report',type=Path,help='規格070正常百科五船正式驗收及73張素材繼承審查')
parser.add_argument('--vehicle-ready-report',type=Path,help='規格070三種車輛／火炮單幀PNG READY審查')
parser.add_argument('--vehicle-conformed-report',type=Path,help='規格070三種車輛／火炮正式驗收及78張素材繼承審查')
parser.add_argument('--colonist-ready-report',type=Path,help='規格070同頁22幀殖民者READY審查')
parser.add_argument('--colonist-conformed-report',type=Path,help='規格070同頁22幀正式驗收及81張素材繼承審查')
parser.add_argument('--unit19-ready-report',type=Path,help='規格070其餘19幀單位READY審查')
parser.add_argument('--unit19-conformed-report',type=Path,help='規格070正常14頁19幀驗收及103張素材繼承審查')
parser.add_argument('--inherited-index',type=Path,help='可選：經雜湊固定的上一版來源清冊；只供新增規格069兩背景，保留既有驗收')
parser.add_argument('--inherited-manifest',type=Path,help='與inherited-index配對的上一版完整素材清冊')
parser.add_argument('--scene-background-ready-report',type=Path,help='規格069兩背景READY審查')
parser.add_argument('--scene-background-conformed-report',type=Path,help='規格069兩背景正式驗收與122張舊素材繼承審查')
parser.add_argument('--report-background-ready-report',type=Path,help='規格069八報告READY審查')
parser.add_argument('--report-background-conformed-report',type=Path,help='規格069八報告正式驗收與124張舊原稿繼承審查')
parser.add_argument('--room-score-ready-report',type=Path,help='規格069國會室內與計分背景READY審查r2')
parser.add_argument('--room-score-conformed-report',type=Path,help='規格069兩背景限定驗收及132張舊原稿繼承審查')
parser.add_argument('--published-surface-ready-report',type=Path,help='規格069 R79已發布顯示來源READY審查')
parser.add_argument('--published-surface-conformed-report',type=Path,help='規格069 R79正常讀檔背景限定驗收，素材不增加')
parser.add_argument('--published-text-ready-report',type=Path,help='規格069 R80已發布字底與游標READY審查')
parser.add_argument('--published-text-conformed-report',type=Path,help='規格069 R80正常字底與游標限定驗收，原素材保持')
parser.add_argument('--published-texture-ready-report',type=Path,help='規格069 R81既有三底紋發布來源READY審查')
parser.add_argument('--published-texture-conformed-report',type=Path,help='規格069 R81既有底紋限定驗收，原素材與其他來源保持')
parser.add_argument('--opening-ready-report',type=Path,help='規格069 R82開場PIK READY審查')
parser.add_argument('--opening-conformed-report',type=Path,help='規格069 R82開場PIK限定驗收及134張舊原稿繼承審查')
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
  original=asset['original_source'];file=original['file'];file_sha=original['sha256'];encoded=original.get('encoded_sha256');ordinal=original['ordinal']
 else:raise ValueError('未支援的正式來源紀錄：'+name)
 if file.endswith('.PIK'):
  assert encoded is None and original.get('indexed_sha256')
  matches=[f for f in frames if f['file']==file and f['file_sha256']==file_sha and f['indexed_sha256']==original['indexed_sha256'] and f['ordinal']==ordinal]
 else:
  assert encoded
  matches=[f for f in frames if f['file']==file and f['file_sha256']==file_sha and f.get('encoded_sha256')==encoded and (ordinal is None or f['ordinal']==ordinal)]
 assert len(matches)==1,(name,matches)
 f=matches[0];f['formal_assets'].append(name)
 bindings.append({'asset':name,'asset_sha256':asset['sha256'],'source_research_id':f['research_id'],'source_file':file,'source_ordinal':f['ordinal'],'source_encoded_sha256':f.get('encoded_sha256'),'spec':asset.get('spec',manifest['spec']),'claim':'matches verified formal manifest; conformance scope remains in cited spec'})
 if file.endswith('.PIK'):bindings[-1]['source_indexed_sha256']=f['indexed_sha256']
# R82 只增加兩個原始PIK的13張生成圖，其他來源及歷史驗收保持。
if a.opening_ready_report or a.opening_conformed_report:
 assert a.opening_ready_report and a.opening_conformed_report and a.inherited_index and a.inherited_manifest
 assert not a.published_texture_ready_report and not a.published_texture_conformed_report
 ready=json.loads(a.opening_ready_report.read_bytes());review=json.loads(a.opening_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());old_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert ready['state']=='READY' and review['result']=='PASS_OPENING_CONFORMANCE_REVIEW' and review['spec_state']=='CONFORMED'
 assert review['ready_sha256']==sha(a.opening_ready_report) and review['manifest_sha256']==sha(a.manifest)
 assert review['inherited_manifest_sha256']==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert review['inherited_source_index_sha256']==sha(a.inherited_index)
 assert len(old_manifest['assets'])==134 and len(manifest['assets'])==len(bindings)==147
 assert all(manifest['assets'][k]==v and sha(a.assets/k)==v['sha256'] for k,v in old_manifest['assets'].items())
 assert review['go_named_passed']>=88 and not review['go_failed'] and not review['go_skipped']
 assert review['native_points']==192 and review['native_full_rgba_pixels']==22528000
 assert review['gui_samples']==6 and review['gui_hd_samples']==3 and review['gui_original_samples']==3
 assert review['formal_source_points']>0 and review['opening_border_rgba_pixels']>0 and review['opening_map_rgba_pixels']>0
 assert review['three_replays_gui_audio_state_save_equal'] is True and review['complete_hd'] is False
 assert review['cursor_source_restore_verified'] is True and review['inherited_native32_passed'] is True
 assert review['package_graphics_files']==148 and review['original_inputs_unchanged'] is True
 assert prior['source_receipt_sha256']==sha(a.catalog) and len(prior['frames'])==1552 and prior['files']==d['files']
 assert bindings[:134]==prior['formal_bindings'] and {b['source_research_id'] for b in bindings[134:]}=={1092,1179}
 before={f['research_id']:f for f in prior['frames']}
 for frame in frames:
  old=before[frame['research_id']]
  assert {k:frame[k] for k in allowed if k in frame}=={k:old[k] for k in allowed if k in old}
 merged=json.loads(a.inherited_index.read_bytes());new={f['research_id']:f for f in frames};ids={1092,1179}
 for row in merged['frames']:
  if row['research_id'] not in ids:continue
  assert not row['formal_assets']
  row['formal_assets']=new[row['research_id']]['formal_assets']
  row['runtime_source_evidence']='confirmed complete original decode, uint32 map locals, exact RAM copy provenance, full opening canvas/VGA/index equality, canonical palette and normal exit; unknown foreground remains original'
  row['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.opening_conformed_report),'scope':'canonical-palette opening PIK border and panoramic map; raw per-object PNG geometry and verified source restoration inside mouse rectangle; SS foreground animation and intermediate fades unverified'}
 merged['formal_manifest_sha256']=sha(a.manifest);merged['formal_bindings']=bindings
 merged['opening_background_conformance']={'ready_sha256':sha(a.opening_ready_report),'review_sha256':sha(a.opening_conformed_report),'sources':sorted(ids),'new_raw_pngs':13,'formal_assets':147,'gui_samples':6,'claim':'two PIK sources only; unknown foreground, animation, fades and full HD remain incomplete'}
 assert all(f==before[f['research_id']] for f in merged['frames'] if f['research_id'] not in ids)
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_OPENING_PIK_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

# R81 只補三種既有底紋的發布生命週期，保留全部原始來源及歷史驗收。
if a.published_texture_ready_report or a.published_texture_conformed_report:
 assert a.published_texture_ready_report and a.published_texture_conformed_report and a.inherited_index and a.inherited_manifest
 assert not a.published_text_ready_report and not a.published_text_conformed_report
 ready=json.loads(a.published_texture_ready_report.read_bytes());review=json.loads(a.published_texture_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());old_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert ready['result']=='READY_PUBLISHED_TEXTURE_DISPLAY_ONLY' and ready['state']=='READY'
 assert review['result']=='PASS_PUBLISHED_TEXTURE_CONFORMANCE_REVIEW' and review['spec_state']=='CONFORMED'
 assert review['ready_sha256']==sha(a.published_texture_ready_report)
 assert review['manifest_sha256']==sha(a.manifest)==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert review['inherited_source_index_sha256']==sha(a.inherited_index)
 assert old_manifest==manifest and len(manifest['assets'])==134 and len(bindings)==134
 assert review['go_named_passed']==63 and not review['go_failed'] and not review['go_skipped']
 assert review['native_points']==32 and review['native_inputs']==31 and review['native_end']==80600000 and review['native_full_rgba_pixels']==32768000
 assert review['gui_samples']==9 and review['gui_hd_samples']==4 and review['gui_original_samples']==5 and review['formal_source_points']==9
 assert review['formal_inputs']==24 and review['formal_end']==63600000
 assert review['texture_rgba_pixels']>0 and review['verified_texture_underlay_cells']>0
 assert review['three_replays_gui_audio_state_save_equal'] is True and review['complete_hd'] is False
 assert review['positive_publication_sources']==[1265,1552] and review['unobserved_publication_sources']==[1287]
 assert prior['source_receipt_sha256']==sha(a.catalog) and len(prior['frames'])==1552 and prior['files']==d['files']
 assert prior['formal_bindings']==bindings and prior['coverage_limits']['complete_hd'] is False
 before={f['research_id']:f for f in prior['frames']}
 for frame in frames:
  old=before[frame['research_id']]
  assert {k:frame[k] for k in allowed if k in frame}=={k:old[k] for k in allowed if k in old}
  assert frame['formal_assets']==old['formal_assets']
 merged=json.loads(a.inherited_index.read_bytes());ids={1265,1552}
 targets=[f for f in merged['frames'] if f['research_id'] in ids];assert len(targets)==2
 for row in targets:
  row['published_texture_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','review_sha256':sha(a.published_texture_conformed_report),'scope':'verified per-cell texture VGA publication and standard cursor reverse pairs; WOODTILE popup backgrounds and glyph underlays in representative normal TC load path; unobserved paths retain prior scope; full HD incomplete'}
 merged['published_texture_conformance']={'ready_sha256':sha(a.published_texture_ready_report),'review_sha256':sha(a.published_texture_conformed_report),'sources':sorted(ids),'gui_samples':9,'formal_source_points':9,'formal_assets':134,'claim':'existing texture publication lifecycle and normal popup wood underlays only; no new art or full-HD credit'}
 assert all(f==before[f['research_id']] for f in merged['frames'] if f['research_id'] not in ids)
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_PUBLISHED_TEXTURE_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

# R80 只補已發布字底與標準游標的生命週期；不擴張全量HD信用。
if a.published_text_ready_report or a.published_text_conformed_report:
 assert a.published_text_ready_report and a.published_text_conformed_report and a.inherited_index and a.inherited_manifest
 assert not a.published_surface_ready_report and not a.published_surface_conformed_report
 ready=json.loads(a.published_text_ready_report.read_bytes());review=json.loads(a.published_text_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());old_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert ready['result']=='READY_PUBLISHED_TEXT_CURSOR_DISPLAY_ONLY' and ready['spec_state']=='READY'
 assert review['result']=='PASS_PUBLISHED_TEXT_CURSOR_CONFORMANCE_REVIEW' and review['spec_state']=='CONFORMED'
 assert review['ready_sha256']==sha(a.published_text_ready_report)
 assert review['manifest_sha256']==sha(a.manifest)==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert review['inherited_source_index_sha256']==sha(a.inherited_index)
 assert old_manifest==manifest and len(manifest['assets'])==134 and len(bindings)==134
 assert review['go_named_passed']==251 and not review['go_failed'] and not review['go_skipped']
 assert review['native_points']==32 and review['native_inputs']==31 and review['native_end']==72800000
 assert review['gui_samples']==32 and review['gui_hd_samples']==18 and review['gui_original_samples']==14
 assert review['formal_source_points']==32 and review['formal_inputs']==31 and review['formal_end']==80600000
 assert review['hd_cursor_rgba_pixels']==23616 and review['verified_hd_underlay_cells']>0
 assert review['four_replays_gui_audio_state_save_equal'] is True and review['unknown_popup_underlays_original'] is True
 assert prior['source_receipt_sha256']==sha(a.catalog) and len(prior['frames'])==1552 and prior['files']==d['files']
 assert prior['formal_bindings']==bindings and prior['coverage_limits']['complete_hd'] is False
 before={f['research_id']:f for f in prior['frames']}
 for frame in frames:
  old=before[frame['research_id']]
  assert {k:frame[k] for k in allowed if k in frame}=={k:old[k] for k in allowed if k in old}
  assert frame['formal_assets']==old['formal_assets']
 merged=json.loads(a.inherited_index.read_bytes())
 targets=[f for f in merged['frames'] if f['research_id']==1551 or f['file']=='CURSOR.SS' and f['ordinal']==0]
 assert len(targets)==2
 for row in targets:
  row['published_text_cursor_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','review_sha256':sha(a.published_text_conformed_report),'scope':'normal published scene glyph underlays, transparent cursor ownership and opaque reverse pairs, standard HD cursor over text; unknown popup underlays stay Original, full HD incomplete'}
 merged['published_text_cursor_conformance']={'ready_sha256':sha(a.published_text_ready_report),'review_sha256':sha(a.published_text_conformed_report),'sources':[f['research_id'] for f in targets],'gui_samples':32,'formal_source_points':32,'formal_assets':134,'claim':'verified glyph underlays and standard cursor only; previous raw PNGs and conformance scopes unchanged; full HD incomplete'}
 ids={f['research_id'] for f in targets}
 assert all(f==before[f['research_id']] for f in merged['frames'] if f['research_id'] not in ids)
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_PUBLISHED_TEXT_CURSOR_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

# R79 只增加已驗顯示生命週期，134張原稿與既有來源事實保持。
if a.published_surface_ready_report or a.published_surface_conformed_report:
 assert a.published_surface_ready_report and a.published_surface_conformed_report and a.inherited_index and a.inherited_manifest
 assert not a.room_score_ready_report and not a.room_score_conformed_report
 ready=json.loads(a.published_surface_ready_report.read_bytes());review=json.loads(a.published_surface_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());old_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert ready['result']=='READY_PUBLISHED_SCENE_DISPLAY_ONLY'
 assert review['result']=='PASS_PUBLISHED_SCENE_CONFORMANCE_REVIEW' and review['spec_state']=='CONFORMED'
 assert review['ready_sha256']==sha(a.published_surface_ready_report)
 assert review['manifest_sha256']==sha(a.manifest)==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert review['inherited_source_index_sha256']==sha(a.inherited_index)
 assert old_manifest==manifest and len(manifest['assets'])==134
 assert review['gui_samples']==32 and review['formal_source_points']==32 and review['native_points']==27
 assert review['go_named_passed']==215 and not review['go_failed'] and not review['go_skipped']
 assert review['four_replays_gui_audio_state_save_equal'] is True and review['original_inputs_unchanged'] is True
 assert prior['source_receipt_sha256']==sha(a.catalog) and len(prior['frames'])==1552 and prior['files']==d['files']
 assert prior['formal_bindings']==bindings and prior['coverage_limits']['complete_hd'] is False
 before={f['research_id']:f for f in prior['frames']}
 for frame in frames:
  previous=before[frame['research_id']]
  assert {k:frame[k] for k in allowed if k in frame}=={k:previous[k] for k in allowed if k in previous}
  assert frame['formal_assets']==previous['formal_assets']
 merged=json.loads(a.inherited_index.read_bytes())
 row=next(f for f in merged['frames'] if f['research_id']==1551)
 row['runtime_source_evidence'] += '; additionally confirmed exact main-to-VGA publication in recorded normal load views; post-publication main writes do not revoke displayed background owners'
 row['published_surface_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','review_sha256':sha(a.published_surface_conformed_report),'scope':'normal load list and success-message backgrounds, five languages, Original/HD and EN/TC cursor hover/return; cursor and foreground preserved as original, text underlay HD pending'}
 merged['published_surface_conformance']={'ready_sha256':sha(a.published_surface_ready_report),'review_sha256':sha(a.published_surface_conformed_report),'source':1551,'gui_samples':32,'formal_source_points':32,'formal_assets':134,'claim':'published source background only; inherited134 PNGs and previous conformance scopes unchanged; full HD incomplete'}
 assert all(f==before[f['research_id']] for f in merged['frames'] if f['research_id']!=1551)
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_PUBLISHED_SURFACE_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

# R78 僅增補國會室內與計分木紋兩個來源；載入選單HD仍未完成。
if a.room_score_ready_report or a.room_score_conformed_report:
 assert a.room_score_ready_report and a.room_score_conformed_report and a.inherited_index and a.inherited_manifest
 assert not any([a.report_background_ready_report,a.report_background_conformed_report,a.scene_background_ready_report,a.scene_background_conformed_report])
 ready=json.loads(a.room_score_ready_report.read_bytes());current=json.loads(a.room_score_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());prior_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert ready['result']=='READY_ROOM_SCORE_BACKGROUND_DISPLAY_ONLY' and ready['spec_state']=='READY' and ready['ready_revision']==2
 assert current['result']=='PASS_ROOM_SCORE_BACKGROUND_CONFORMANCE_REVIEW' and current['spec_state']=='CONFORMED'
 assert current['sources']==[120,1551] and current['formal_assets']==134 and current['graphics_files']==135
 assert current['manifest_sha256']==sha(a.manifest) and current['ready_review_sha256']==sha(a.room_score_ready_report)
 assert current['inherited_source_index_sha256']==sha(a.inherited_index)
 assert current['inherited_manifest_sha256']==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert prior['source_receipt_sha256']==sha(a.catalog) and prior['schema']==1 and prior['kind']=='DRAFT-native-source-index-not-complete-player-coverage'
 assert prior['coverage_limits']['complete_hd'] is False and prior['coverage_limits']['contains_original_pixels'] is False
 new_assets={'ccbkgd-000.png','woodpanl-000.png'}
 assert set(prior_manifest['assets'])==set(manifest['assets'])-new_assets==set(current['unchanged_inherited_assets'])
 assert len(prior_manifest['assets'])==len(prior['formal_bindings'])==132
 assert all(manifest['assets'][name]==record and record['sha256']==current['unchanged_inherited_assets'][name] for name,record in prior_manifest['assets'].items())
 before={row['research_id']:row for row in prior['frames']}
 assert len(before)==len(frames)==1552 and prior['files']==d['files'] and prior['summary']==d['summary']
 assert prior['declared_encoding_alias_groups']==d['declared_encoding_alias_groups']
 for row in frames:
  old=before[row['research_id']]
  assert {k:old[k] for k in allowed if k in old}=={k:row[k] for k in allowed if k in row}
  if row['research_id'] not in [120,1551]:assert old['formal_assets']==row['formal_assets']
 assert {row['asset']:row for row in bindings if row['asset'] not in new_assets}=={row['asset']:row for row in prior['formal_bindings']}
 assert current['native_points']==27 and current['native_inputs']==42 and current['native_end']==192600000 and current['native_rgba_pixels']==27648000
 assert current['formal_source_points']==27 and current['gui_samples']==37 and current['gui_hd_samples']==18 and current['gui_original_samples']==19
 assert current['go_passed_unique_cases']==196 and current['startup_cases']==5 and current['package_rejected_cases']==407
 assert current['formal_actual_inputs']==34 and current['formal_end']==100200000 and current['load_menu_hd_complete'] is False
 assert current['gui_room_foreground_rgba_pixels']==433008
 merged=json.loads(a.inherited_index.read_bytes())
 for rid,name in [(120,'ccbkgd-000.png'),(1551,'woodpanl-000.png')]:
  row=next(row for row in merged['frames'] if row['research_id']==rid);fresh=next(row for row in frames if row['research_id']==rid)
  assert not row['formal_assets'] and fresh['formal_assets']==[name]
  row['formal_assets']=[name]
  row['runtime_source_evidence']='confirmed complete PIK decode at explicit verified canvas bases, exact source-used palette RGB and original copy/glyph/cursor ownership; only native surfaces that pass the inherited guard'
  row['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.room_score_conformed_report),'scope':'normal F3 congress-room background and F10 score background, five languages, original/HD and EN/TC standard cursor hover/return; load-menu/slot stay Original on native guard failure; actors, animation and other paths unverified'}
 merged['formal_manifest_sha256']=sha(a.manifest);merged['formal_bindings']=bindings
 merged['coverage_limits']['formal_asset_bindings']=len(bindings)
 merged['coverage_limits']['additional_ready_source_contracts']=sum(row.get('source_contract_reference',{}).get('state')=='READY' and not row.get('source_contract_reference',{}).get('formal_connected') for row in merged['frames'])
 merged['room_score_background_conformance']={'ready_review_sha256':sha(a.room_score_ready_report),'review_sha256':sha(a.room_score_conformed_report),'sources':[120,1551],'formal_assets':134,'gui_samples':37,'native_source_points':27,'inherited_source_index_sha256':sha(a.inherited_index),'load_menu_hd_complete':False,'claim':'two normal backgrounds only; all132 inherited raw PNGs/records and conformance scopes preserved; stage load-menu native guard failure stays Original, full HD incomplete'}
 assert all(row==before[row['research_id']] for row in merged['frames'] if row['research_id'] not in [120,1551])
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_ROOM_SCORE_SOURCE_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

# R77 只增補八個已驗報告來源，保留 R76 的完整索引快照。
if a.report_background_ready_report or a.report_background_conformed_report:
 assert a.report_background_ready_report and a.report_background_conformed_report and a.inherited_index and a.inherited_manifest
 assert not a.scene_background_ready_report and not a.scene_background_conformed_report
 ready=json.loads(a.report_background_ready_report.read_bytes());current=json.loads(a.report_background_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());prior_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert ready['result']=='READY_REPORT_BACKGROUND_DISPLAY_ONLY' and ready['spec_state']=='READY'
 assert current['result']=='PASS_REPORT_BACKGROUND_CONFORMANCE_REVIEW' and current['spec_state']=='CONFORMED'
 assert current['sources']==list(range(1442,1450)) and current['formal_assets']==132 and current['graphics_files']==133
 assert current['manifest_sha256']==sha(a.manifest) and current['ready_review_sha256']==sha(a.report_background_ready_report)
 assert current['inherited_source_index_sha256']==sha(a.inherited_index)
 assert current['inherited_manifest_sha256']==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert prior['source_receipt_sha256']==sha(a.catalog) and prior['kind']=='DRAFT-native-source-index-not-complete-player-coverage' and prior['schema']==1
 assert prior['coverage_limits']['complete_hd'] is False and prior['coverage_limits']['contains_original_pixels'] is False
 new_assets={'report%d-000.png'%n for n in range(1,9)}
 assert set(prior_manifest['assets'])==set(manifest['assets'])-new_assets==set(current['unchanged_inherited_assets'])
 assert len(prior_manifest['assets'])==len(prior['formal_bindings'])==124
 assert all(manifest['assets'][name]==record and record['sha256']==current['unchanged_inherited_assets'][name] for name,record in prior_manifest['assets'].items())
 before={row['research_id']:row for row in prior['frames']}
 assert len(before)==len(frames)==1552 and prior['files']==d['files'] and prior['summary']==d['summary']
 assert prior['declared_encoding_alias_groups']==d['declared_encoding_alias_groups']
 for row in frames:
  old=before[row['research_id']]
  assert {k:old[k] for k in allowed if k in old}=={k:row[k] for k in allowed if k in row}
  if row['research_id'] not in range(1442,1450):assert old['formal_assets']==row['formal_assets']
 old_bindings={row['asset']:row for row in prior['formal_bindings']}
 assert {row['asset']:row for row in bindings if row['asset'] not in new_assets}==old_bindings
 assert current['native_points']==27 and current['native_inputs']==42 and current['native_end']==192600000 and current['native_rgba_pixels']==27648000
 assert current['formal_source_points']==99 and current['gui_samples']==149 and current['gui_hd_samples']==82 and current['gui_original_samples']==67
 assert current['go_passed_unique_cases']==163 and current['startup_cases']==5 and current['package_rejected_cases']==401
 assert current['formal_actual_inputs']==74 and current['formal_end']==262000000
 merged=json.loads(a.inherited_index.read_bytes())
 for rid in range(1442,1450):
  name='report%d-000.png'%(rid-1441);row=next(row for row in merged['frames'] if row['research_id']==rid)
  fresh=next(row for row in frames if row['research_id']==rid);assert not row['formal_assets'] and fresh['formal_assets']==[name]
  row['formal_assets']=[name]
  row['runtime_source_evidence']='confirmed complete direct-main PIK decode at dosgolem linear RAM 0x2CAE0, exact source-used palette RGB, glyph underlays and standard cursor reverse-pair; only settled native surfaces'
  row['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.report_background_conformed_report),'scope':'normal eight report backgrounds, five languages, original/HD, report pages, EN/TC standard-cursor hover/return; REPORT9, other backgrounds, actors and animation unverified'}
 merged['formal_manifest_sha256']=sha(a.manifest);merged['formal_bindings']=bindings
 merged['coverage_limits']['formal_asset_bindings']=len(bindings)
 merged['coverage_limits']['additional_ready_source_contracts']=sum(row.get('source_contract_reference',{}).get('state')=='READY' and not row.get('source_contract_reference',{}).get('formal_connected') for row in merged['frames'])
 merged['report_background_conformance']={'ready_review_sha256':sha(a.report_background_ready_report),'review_sha256':sha(a.report_background_conformed_report),'sources':list(range(1442,1450)),'formal_assets':132,'gui_samples':149,'native_source_points':99,'inherited_source_index_sha256':sha(a.inherited_index),'claim':'eight normal report backgrounds only; all 124 inherited PNGs, records and conformance scopes unchanged; full player-visible denominator unknown and full HD incomplete'}
 assert all(row==before[row['research_id']] for row in merged['frames'] if row['research_id'] not in range(1442,1450))
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_REPORT_SOURCE_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

# 只增補經本輪審查的兩列；上一版已完成項及原始事實逐項原樣繼承。
if any([a.inherited_index,a.inherited_manifest,a.scene_background_ready_report,a.scene_background_conformed_report]):
 assert all([a.inherited_index,a.inherited_manifest,a.scene_background_ready_report,a.scene_background_conformed_report])
 current_ready=json.loads(a.scene_background_ready_report.read_bytes())
 current=json.loads(a.scene_background_conformed_report.read_bytes())
 prior=json.loads(a.inherited_index.read_bytes());prior_manifest=json.loads(a.inherited_manifest.read_bytes())
 assert current_ready['result']=='READY_SCENE_BACKGROUND_DISPLAY_ONLY'
 assert current['result']=='PASS_SCENE_BACKGROUND_CONFORMANCE_REVIEW' and current['spec_state']=='CONFORMED'
 assert current['sources']==[308,824] and current['formal_assets']==124 and current['graphics_files']==125
 assert current['manifest_sha256']==sha(a.manifest) and current['ready_review_sha256']==sha(a.scene_background_ready_report)
 assert current['inherited_source_index_sha256']==sha(a.inherited_index)
 assert current['inherited_manifest_sha256']==sha(a.inherited_manifest)==prior['formal_manifest_sha256']
 assert prior['source_receipt_sha256']==sha(a.catalog) and prior['kind']=='DRAFT-native-source-index-not-complete-player-coverage'
 assert prior['schema']==1 and prior['coverage_limits']['complete_hd'] is False and prior['coverage_limits']['contains_original_pixels'] is False
 new_assets={'colony-000.png','europe-000.png'}
 assert set(prior_manifest['assets'])==set(manifest['assets'])-new_assets==set(current['unchanged_inherited_assets'])
 assert len(prior_manifest['assets'])==len(prior['formal_bindings'])==122
 assert all(manifest['assets'][name]==record and record['sha256']==current['unchanged_inherited_assets'][name] for name,record in prior_manifest['assets'].items())
 before={row['research_id']:row for row in prior['frames']}
 assert len(before)==len(frames)==1552 and prior['files']==d['files'] and prior['summary']==d['summary']
 assert prior['declared_encoding_alias_groups']==d['declared_encoding_alias_groups']
 for row in frames:
  old=before[row['research_id']]
  assert {k:old[k] for k in allowed if k in old}=={k:row[k] for k in allowed if k in row}
  if row['research_id'] not in [308,824]:assert old['formal_assets']==row['formal_assets']
 old_bindings={row['asset']:row for row in prior['formal_bindings']}
 assert {row['asset']:row for row in bindings if row['asset'] not in new_assets}==old_bindings
 assert current['native_points']==19 and current['native_rgba_pixels']==19456000
 assert current['formal_source_points']==67 and current['gui_samples']==107 and current['gui_hd_samples']==60 and current['gui_original_samples']==47
 assert current['go_passed_unique_cases']==31 and current['startup_cases']==5 and current['package_rejected_cases']==377
 merged=json.loads(a.inherited_index.read_bytes())
 for rid,name in [(308,'colony-000.png'),(824,'europe-000.png')]:
  row=next(row for row in merged['frames'] if row['research_id']==rid)
  fresh=next(row for row in frames if row['research_id']==rid)
  assert not row['formal_assets'] and fresh['formal_assets']==[name]
  row['formal_assets']=[name]
  row['runtime_source_evidence']='confirmed complete PIK decode, exact source-used palette RGB, 0C9F/0CBA RAM provenance, glyph underlays and standard cursor reverse-pair; only settled visible native surfaces'
  row['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.scene_background_conformed_report),'scope':'normal colony partial backdrop and Europe harbor, five languages, recruit/purchase/train open/close and verified standard-cursor hover/return; other scenes, program-drawn graphics and animation unverified'}
 merged['formal_manifest_sha256']=sha(a.manifest);merged['formal_bindings']=bindings
 merged['coverage_limits']['formal_asset_bindings']=len(bindings)
 merged['coverage_limits']['additional_ready_source_contracts']=sum(row.get('source_contract_reference',{}).get('state')=='READY' and not row.get('source_contract_reference',{}).get('formal_connected') for row in merged['frames'])
 merged['scene_background_conformance']={'ready_review_sha256':sha(a.scene_background_ready_report),'review_sha256':sha(a.scene_background_conformed_report),'sources':[308,824],'formal_assets':124,'gui_samples':107,'native_source_points':67,'inherited_source_index_sha256':sha(a.inherited_index),'claim':'two verified normal backgrounds only; all 122 prior raw PNGs, records and delimited conformance states preserved; full player-visible graphics denominator remains unknown and full HD remains incomplete'}
 assert all(row==before[row['research_id']] for row in merged['frames'] if row['research_id'] not in [308,824])
 out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
 print('PASS_INHERITED_SCENE_SOURCE_INDEX',len(frames),len(bindings),sha(out),flush=True)
 raise SystemExit(0)

ready=[f for f in frames if f['file']=='PHYS0.SS' and f['ordinal']==79 and f.get('encoded_sha256')=='a8a861754068c86a9c150442f7b07f1fbd297d82b8e5dcb2e3ee108bde4dc84c']
assert len(ready)==1
ready[0]['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/062-hd-sea-draw-lifecycle.md','section':'2026-10-15 R58正式驗收與限定CONFORMED','formal_connected':bool(ready[0]['formal_assets'])}
unit19_review=None
unit19_assets=set()
assert bool(a.unit19_ready_report)==bool(a.unit19_conformed_report)
if a.unit19_conformed_report:
 assert a.colonist_conformed_report and a.unit_report and a.unit_build
 unit19_ready=json.loads(a.unit19_ready_report.read_bytes());unit19_review=json.loads(a.unit19_conformed_report.read_bytes())
 assert unit19_ready['result']=='PASS_UNIT19_READY_REVIEW' and unit19_ready['spec_state']=='READY'
 assert unit19_review['result']=='PASS_UNIT19_FORMAL_CONFORMANCE_REVIEW' and unit19_review['spec_state']=='CONFORMED'
 assert unit19_review['sources']==[65,73,74,75,76,77,101,102,103,104,105,109,110,111,112,125,126,128,129]
 assert unit19_review['formal_assets']==122 and unit19_review['graphics_files']==123
 assert unit19_review['manifest_sha256']==sha(a.manifest) and unit19_review['ready_review_sha256']==sha(a.unit19_ready_report)
 assert unit19_review['inherited_colonist_conformance_sha256']==sha(a.colonist_conformed_report)
 unit19_assets={'icons-%03d.png'%n for n in unit19_review['sources']}
 assert set(unit19_review['unchanged_inherited_assets'])==set(manifest['assets'])-unit19_assets
 assert len(unit19_review['unchanged_inherited_assets'])==103
 assert all(manifest['assets'][n]['sha256']==h for n,h in unit19_review['unchanged_inherited_assets'].items())
 assert unit19_review['native_points']==61 and unit19_review['native_inputs']==137 and unit19_review['native_rgba_pixels']==53248000
 assert unit19_review['unit_gui_samples']==178 and unit19_review['gui_hd_samples']==108
 assert unit19_review['startup_cases']==4 and unit19_review['package_rejected_cases']==371
 assert unit19_review['go_passed_unique_cases']==457 and unit19_review['go_resource_cases']==131 and unit19_review['go_small_resource_rejections']==321
colonist_review=None
colonist_assets=set()
assert bool(a.colonist_ready_report)==bool(a.colonist_conformed_report)
if a.colonist_conformed_report:
 assert a.vehicle_conformed_report and a.unit_report and a.unit_build
 colonist_ready=json.loads(a.colonist_ready_report.read_bytes());colonist_review=json.loads(a.colonist_conformed_report.read_bytes())
 assert colonist_ready['result']=='PASS_COLONIST_22_READY_REVIEW' and colonist_ready['spec_state']=='READY'
 assert colonist_review['result']=='PASS_COLONIST_22_FORMAL_CONFORMANCE_REVIEW' and colonist_review['spec_state']=='CONFORMED'
 assert colonist_review['sources']==[58,60,66,81,82,83,84,85,86,87,88,89,90,91,92,93,95,96,97,98,106,107]
 assert colonist_review['formal_assets']==103 and colonist_review['graphics_files']==104
 assert colonist_review['manifest_sha256']==(unit19_review['inherited_manifest_sha256'] if unit19_review else sha(a.manifest)) and colonist_review['ready_review_sha256']==sha(a.colonist_ready_report)
 assert colonist_review['inherited_vehicle_conformance_sha256']==sha(a.vehicle_conformed_report)
 colonist_assets={'icons-%03d.png'%n for n in colonist_review['sources']}
 assert set(colonist_review['unchanged_inherited_assets'])==set(manifest['assets'])-colonist_assets-unit19_assets
 assert len(colonist_review['unchanged_inherited_assets'])==81
 assert all(manifest['assets'][n]['sha256']==h for n,h in colonist_review['unchanged_inherited_assets'].items())
 assert colonist_review['native_points']==54 and colonist_review['native_inputs']==81 and colonist_review['native_rgba_pixels']==46080000
 assert colonist_review['unit_gui_samples']==54 and colonist_review['gui_hd_samples']==49
 assert colonist_review['startup_cases']==4 and colonist_review['package_rejected_cases']==314
vehicle_review=None
vehicle_assets=set()
assert bool(a.vehicle_ready_report)==bool(a.vehicle_conformed_report)
if a.vehicle_conformed_report:
 assert a.ship_conformed_report and a.unit_report and a.unit_build
 vehicle_assets={'icons-%03d.png'%n for n in [8,9,16]}
 vehicle_ready=json.loads(a.vehicle_ready_report.read_bytes())
 assert vehicle_ready['result']=='PASS_THREE_STANDALONE_VEHICLE_READY_REVIEW' and vehicle_ready['spec_state']=='READY'
 vehicle_review=json.loads(a.vehicle_conformed_report.read_bytes())
 assert vehicle_review['result']=='PASS_THREE_STANDALONE_VEHICLE_FORMAL_CONFORMANCE_REVIEW' and vehicle_review['spec_state']=='CONFORMED'
 assert vehicle_review['sources']==[8,9,16] and vehicle_review['formal_assets']==81 and vehicle_review['graphics_files']==82
 assert vehicle_review['manifest_sha256']==(colonist_review['inherited_manifest_sha256'] if colonist_review else sha(a.manifest)) and vehicle_review['ready_review_sha256']==sha(a.vehicle_ready_report)
 assert vehicle_review['inherited_ship_conformance_sha256']==sha(a.ship_conformed_report)
 assert set(vehicle_review['unchanged_inherited_assets'])==set(manifest['assets'])-vehicle_assets-colonist_assets-unit19_assets
 assert len(vehicle_review['unchanged_inherited_assets'])==78
 assert all(manifest['assets'][n]['sha256']==h for n,h in vehicle_review['unchanged_inherited_assets'].items())
 assert vehicle_review['native_points']==18 and vehicle_review['native_inputs']==86 and vehicle_review['native_rgba_pixels']==9216000
 assert vehicle_review['unit_gui_samples']==60 and vehicle_review['gui_hd_samples']==45
 assert vehicle_review['startup_cases']==4 and vehicle_review['package_rejected_cases']==248
ship_review=None
ship_assets=set()
assert bool(a.ship_ready_report)==bool(a.ship_conformed_report)
if a.ship_conformed_report:
 assert a.custom_world_conformed_report and a.unit_report and a.unit_build
 ship_assets={'icons-%03d.png'%n for n in [6,7,14,15,127]}
 ship_ready=json.loads(a.ship_ready_report.read_bytes())
 assert ship_ready['result']=='PASS_FIVE_STANDALONE_SHIP_READY_REVIEW' and ship_ready['spec_state']=='READY'
 ship_review=json.loads(a.ship_conformed_report.read_bytes())
 assert ship_review['result']=='PASS_FIVE_STANDALONE_SHIP_FORMAL_CONFORMANCE_REVIEW' and ship_review['spec_state']=='CONFORMED'
 assert ship_review['sources']==[6,7,14,15,127] and ship_review['formal_assets']==78 and ship_review['graphics_files']==79
 assert ship_review['manifest_sha256']==(vehicle_review['inherited_manifest_sha256'] if vehicle_review else sha(a.manifest)) and ship_review['ready_review_sha256']==sha(a.ship_ready_report)
 assert ship_review['inherited_custom_world_conformance_sha256']==sha(a.custom_world_conformed_report)
 assert set(ship_review['unchanged_inherited_assets'])==set(manifest['assets'])-ship_assets-vehicle_assets-colonist_assets-unit19_assets
 assert len(ship_review['unchanged_inherited_assets'])==73
 assert all(manifest['assets'][n]['sha256']==h for n,h in ship_review['unchanged_inherited_assets'].items())
 assert ship_review['native_points']==24 and ship_review['native_inputs']==109 and ship_review['native_rgba_pixels']==15360000
 assert ship_review['ship_gui_samples']==100 and ship_review['gui_hd_samples']==75
 assert ship_review['replay_end']==335800000 and ship_review['replay_inputs']==264
 assert ship_review['startup_cases']==6 and ship_review['package_rejected_cases']==238
custom_review=None
custom_assets={'customiz-000.png'}
assert bool(a.custom_world_ready_report)==bool(a.custom_world_conformed_report)
if a.custom_world_conformed_report:
 assert a.new_game_conformed_report
 custom_ready=json.loads(a.custom_world_ready_report.read_bytes())
 assert custom_ready['result']=='PASS_CUSTOM_WORLD_READY_REVIEW' and custom_ready['spec_state']=='READY'
 custom_review=json.loads(a.custom_world_conformed_report.read_bytes())
 assert custom_review['result']=='PASS_CUSTOM_WORLD_FORMAL_CONFORMANCE_REVIEW' and custom_review['spec_state']=='CONFORMED'
 assert custom_review['formal_assets']==73 and custom_review['manifest_sha256']==(ship_review['inherited_manifest_sha256'] if ship_review else sha(a.manifest))
 assert custom_review['ready_review_sha256']==sha(a.custom_world_ready_report)
 assert custom_review['inherited_new_game_conformance_sha256']==sha(a.new_game_conformed_report)
 assert set(custom_review['unchanged_inherited_assets'])==set(manifest['assets'])-custom_assets-ship_assets-vehicle_assets-colonist_assets-unit19_assets
 assert len(custom_review['unchanged_inherited_assets'])==72
 assert all(manifest['assets'][n]['sha256']==h for n,h in custom_review['unchanged_inherited_assets'].items())
new_game_review=None
new_game_assets={'difficul-000.png','nations-000.png'}
assert bool(a.new_game_ready_report)==bool(a.new_game_conformed_report)
if a.new_game_conformed_report:
 assert a.parch_conformed_report
 new_game_ready=json.loads(a.new_game_ready_report.read_bytes())
 assert new_game_ready['result']=='PASS_NEW_GAME_READY_REVIEW' and new_game_ready['spec_state']=='READY'
 new_game_review=json.loads(a.new_game_conformed_report.read_bytes())
 assert new_game_review['result']=='PASS_NEW_GAME_FORMAL_CONFORMANCE_REVIEW' and new_game_review['spec_state']=='CONFORMED'
 assert new_game_review['formal_assets']==72 and new_game_review['manifest_sha256']==(custom_review['inherited_manifest_sha256'] if custom_review else sha(a.manifest))
 assert new_game_review['ready_review_sha256']==sha(a.new_game_ready_report)
 assert new_game_review['inherited_parch_conformance_sha256']==sha(a.parch_conformed_report)
 assert set(new_game_review['unchanged_inherited_assets'])==set(manifest['assets'])-new_game_assets-custom_assets-ship_assets-vehicle_assets-colonist_assets-unit19_assets
 assert len(new_game_review['unchanged_inherited_assets'])==70
 assert all(manifest['assets'][n]['sha256']==h for n,h in new_game_review['unchanged_inherited_assets'].items())
parch_review=None
assert bool(a.parch_ready_report)==bool(a.parch_conformed_report)
if a.parch_conformed_report:
 assert a.world_wood_conformed_report
 parch_ready=json.loads(a.parch_ready_report.read_bytes())
 assert parch_ready['result']=='PASS_PARCH_READY_REVIEW' and parch_ready['spec_state']=='READY'
 parch_review=json.loads(a.parch_conformed_report.read_bytes())
 assert parch_review['result']=='PASS_PARCH_FORMAL_CONFORMANCE_REVIEW' and parch_review['spec_state']=='CONFORMED'
 assert parch_review['formal_assets']==70 and parch_review['manifest_sha256']==(new_game_review['inherited_manifest_sha256'] if new_game_review else sha(a.manifest))
 assert parch_review['ready_review_sha256']==sha(a.parch_ready_report)
 assert parch_review['inherited_world_wood_conformance_sha256']==sha(a.world_wood_conformed_report)
 assert set(parch_review['unchanged_inherited_assets'])==set(manifest['assets'])-{'parch-000.png'}-new_game_assets-custom_assets-ship_assets-vehicle_assets-colonist_assets-unit19_assets
 assert len(parch_review['unchanged_inherited_assets'])==69
 assert all(manifest['assets'][n]['sha256']==h for n,h in parch_review['unchanged_inherited_assets'].items())
wood_review=None
assert bool(a.world_wood_ready_report)==bool(a.world_wood_conformed_report)
if a.world_wood_conformed_report:
 assert a.menu_conformed_report
 wood_ready=json.loads(a.world_wood_ready_report.read_bytes())
 assert wood_ready['result']=='PASS_WORLD_WOOD_READY_REVIEW' and wood_ready['spec_state']=='READY'
 wood_review=json.loads(a.world_wood_conformed_report.read_bytes())
 assert wood_review['result']=='PASS_WORLD_WOOD_FORMAL_CONFORMANCE_REVIEW' and wood_review['spec_state']=='CONFORMED'
 assert wood_review['formal_assets']==69 and wood_review['manifest_sha256']==(parch_review['inherited_manifest_sha256'] if parch_review else sha(a.manifest))
 assert wood_review['ready_review_sha256']==sha(a.world_wood_ready_report)
 assert wood_review['inherited_menu_conformance_sha256']==sha(a.menu_conformed_report)
 assert set(wood_review['unchanged_inherited_assets'])==set(manifest['assets'])-{'woodtile-000.png','parch-000.png'}-new_game_assets-custom_assets-ship_assets-vehicle_assets-colonist_assets-unit19_assets
 assert len(wood_review['unchanged_inherited_assets'])==68
 assert all(manifest['assets'][n]['sha256']==h for n,h in wood_review['unchanged_inherited_assets'].items())
menu_review=None
if a.menu_conformed_report:
 assert a.menu_ready_report and a.small_terrain_conformed_report
 menu_ready=json.loads(a.menu_ready_report.read_bytes());assert menu_ready['result']=='PASS_MENU_BACKGROUND_READY_REVIEW' and menu_ready['spec_state']=='READY'
 menu_review=json.loads(a.menu_conformed_report.read_bytes())
 assert menu_review['result']=='PASS_MENU_FORMAL_CONFORMANCE_REVIEW' and menu_review['spec_state']=='CONFORMED'
 assert menu_review['formal_assets']==68 and menu_review['manifest_sha256']==(wood_review['inherited_manifest_sha256'] if wood_review else sha(a.manifest))
 assert menu_review['ready_review_sha256']==sha(a.menu_ready_report)
 assert len(menu_review['unchanged_inherited_assets'])==66
 assert all(manifest['assets'][n]['sha256']==h for n,h in menu_review['unchanged_inherited_assets'].items())
small_review=None
if a.small_terrain_ready_report:
 small_review=json.loads(a.small_terrain_ready_report.read_bytes())
 assert small_review['result']=='PASS_SMALL_TERRAIN_READY_REVIEW' and small_review['spec_state']=='READY'
 assert small_review['native_source_report_sha256']==sha(a.small_terrain_report)
if a.small_terrain_conformed_report:
 assert small_review is not None and a.terrain_batch_conformed_report
 small_review=json.loads(a.small_terrain_conformed_report.read_bytes())
 assert small_review['result']=='PASS_SMALL_TERRAIN_FORMAL_CONFORMANCE_REVIEW' and small_review['spec_state']=='CONFORMED'
 assert small_review['formal_assets']==66
 assert small_review['manifest_sha256']==(menu_review['inherited_manifest_sha256'] if menu_review else sha(a.manifest))
 if menu_review:assert menu_review['inherited_small_terrain_conformance_sha256']==sha(a.small_terrain_conformed_report)
 assert small_review['ready_review_sha256']==sha(a.small_terrain_ready_report)
 assert len(small_review['unchanged_inherited_assets'])==58
 assert all(manifest['assets'][n]['sha256']==h for n,h in small_review['unchanged_inherited_assets'].items())
expected_assets=122 if unit19_review else 103 if colonist_review else 81 if vehicle_review else 78 if ship_review else 73 if custom_review else 72 if new_game_review else 70 if parch_review else 69 if wood_review else 68 if menu_review else 66 if a.small_terrain_conformed_report else 58 if a.terrain_batch_conformed_report else 46
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
if a.cold_start_entry_report:
 cold=json.loads(a.cold_start_entry_report.read_bytes())
 assert cold['result']=='PASS_READONLY_COLD_START_SS_ENTRY_CATALOG' and cold['original_state_and_saves_equal']
 assert (cold['calls'],cold['unique_match_calls'],cold['ambiguous_match_calls'],cold['unmapped_calls'])==(2022,1948,74,0)
 assert cold['checkpoints']==49 and cold['dos_inputs']==53
 assert cold['input_hashes']=={f['file']:f['sha256'] for f in d['files'] if f['format']=='SS'}
 by_id={f['research_id']:f for f in frames}
 for group in cold['groups'].values():
  for n in group['candidate_research_ids']:
   f=by_id[n];assert f['encoded_sha256']==group['source_hash']
   assert any(s['file']==f['file'] and s['ordinal']==f['ordinal'] and s['size']==f['size'] for s in group['sources'])
   f['cold_start_entry_sample']={'calls':group['calls'],'candidate_research_ids':group['candidate_research_ids'],'rectangles':group['rectangles'],'claim':'entry only from step 0; no visibility, animation or HD credit'}
 public['cold_start_entry_evidence']={'report_sha256':sha(a.cold_start_entry_report),'source_sha256':cold['source_sha256'],'binary_sha256':cold['binary_sha256'],'calls':2022,'additional_calls_before_50000000':17,'checkpoints':49,'dos_inputs':53,'production_connected':False}
if a.background_source_report:
 assert a.cold_start_entry_report
 background=json.loads(a.background_source_report.read_bytes())
 assert background['result']=='PASS_BACKGROUND_SOURCE_WRITES_AND_FOUR_TEXTURE_MODELS' and not background['production_connected']
 assert background['checkpoints']==4 and background['dos_inputs']==7 and background['pik_native_write_count']==64000
 for row in background['texture_sources']:
  f=by_id[row['source_id']];assert f['file']==row['file'] and f['indexed_sha256']==row['indexed_sha256']
  f['background_texture_native_sample']={'state':'DRAFT','spec':'docs/spec/069-hd-menu-background-and-textures.md','source_writes':row['writes'],'visible_native_cells':[p['visible'].get(str(row['source_id']),0) for p in background['points']],'report_sha256':sha(a.background_source_report),'formal_connected':False}
 pik=by_id[1181];assert pik['file']=='OPENMENU.PIK' and pik['indexed_sha256']==background['pik_decoded_sha256']
 pik['background_native_decode_sample']={'state':'DRAFT','spec':'docs/spec/069-hd-menu-background-and-textures.md','writes':64000,'report_sha256':sha(a.background_source_report),'claim':'exact decoded stage pixels only; VGA and presentation lifecycle unverified','formal_connected':False}
 public['background_source_evidence']={'report_sha256':sha(a.background_source_report),'texture_sources':3,'native_menu_points':4,'source_events':background['events'],'pik_decode_writes':64000,'production_connected':False}
if menu_review:
 for ident,name in [(1181,'openmenu-000.png'),(1265,'opentile-000.png')]:
  f=next(f for f in frames if f['research_id']==ident)
  assert f['formal_assets']==[name]
  f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.menu_conformed_report),'scope':'settled main menu; exact visible bitmap recognition for PIK, source ownership and text underlays for OPENTILE'}
 public['menu_graphics_conformance']={'ready_review_sha256':sha(a.menu_ready_report),'review_sha256':sha(a.menu_conformed_report),'sources':[1181,1265],'formal_assets':68,'claim':'two settled-main-menu sources only; full visible denominator remains unknown'}
if wood_review:
 f=next(f for f in frames if f['research_id']==1552)
 assert f['file']=='WOODTILE.SS' and f['formal_assets']==['woodtile-000.png']
 f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.world_wood_conformed_report),'scope':'verified RAM-copy source ownership and text underlays; palette indices 128..138; recorded normal GUI samples only'}
 public['world_wood_conformance']={'ready_review_sha256':sha(a.world_wood_ready_report),'review_sha256':sha(a.world_wood_conformed_report),'sources':[1552],'formal_assets':69,'claim':'inherited R67 wood source only; later PARCH conformance is recorded separately; animation and full HD remain incomplete' if parch_review else 'one wood source only; PARCH, animation and full HD remain incomplete'}
if parch_review:
 f=next(f for f in frames if f['research_id']==1287)
 assert f['file']=='PARCH.SS' and f['formal_assets']==['parch-000.png']
 f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.parch_conformed_report),'scope':'verified RAM-copy source ownership and text underlays; palette indices 98,99,100,106,107; recorded normal GUI samples only'}
 public['parch_conformance']={'ready_review_sha256':sha(a.parch_ready_report),'review_sha256':sha(a.parch_conformed_report),'sources':[1287],'formal_assets':70,'claim':'one paper texture source only; other images, special cursors, animation and full HD remain incomplete'}
if new_game_review:
 for ident,name in [(819,'difficul-000.png'),(1073,'nations-000.png')]:
  f=next(f for f in frames if f['research_id']==ident)
  assert f['formal_assets']==[name]
  f['runtime_source_evidence']='confirmed complete PIK decode and settled canvas/palette/foreground signatures within recorded normal paths; no VGA round-trip ownership'
  f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.new_game_conformed_report),'scope':'five difficulty and four nation settled states; exact native foreground and selection outlines preserved; animation unverified'}
 public['new_game_backgrounds_conformance']={'ready_review_sha256':sha(a.new_game_ready_report),'review_sha256':sha(a.new_game_conformed_report),'sources':[819,1073],'formal_assets':72,'claim':'two settled new-game backgrounds only; other images, program-drawn graphics, animation and full HD remain incomplete'}
if custom_review:
 f=next(f for f in frames if f['research_id']==311)
 assert f['file']=='CUSTOMIZ.PIK' and f['formal_assets']==['customiz-000.png']
 f['runtime_source_evidence']='confirmed complete PIK decode, full palette and 81 native glyph/border geometry pairs with exact source equality outside protected foreground; no VGA ownership'
 f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/069-hd-menu-background-and-textures.md','formal_connected':True,'review_sha256':sha(a.custom_world_conformed_report),'scope':'twelve custom-world cards, 81 selection geometries, original glyphs and selection outlines preserved; other graphics and animation unverified'}
 public['custom_world_conformance']={'ready_review_sha256':sha(a.custom_world_ready_report),'review_sha256':sha(a.custom_world_conformed_report),'sources':[311],'formal_assets':73,'claim':'one twelve-card custom-world background only; other images, program-drawn graphics, animation and full HD remain incomplete'}
if a.unit_report or a.unit_build:
 assert a.unit_report and a.unit_build
 unit=json.loads(a.unit_report.read_bytes());unit_build=json.loads(a.unit_build.read_bytes())
 assert unit['result']=='PASS_UNIT_SOURCE_WRITES_NATIVE_GUI_POINTS' and not unit['production_connected']
 assert unit['candidate_sources']==unit_build['source_count']==131 and unit['hit_sources']==80
 assert len(unit['checkpoints'])==35 and unit['dos_inputs']==353 and unit['source_calls']==196 and unit['raw_events']==5048144
 assert unit['end']['steps']==601800000 and unit['verified_transferred_pixels']==0
 assert unit_build['source_receipt_sha256']==sha(a.catalog)
 assert sha(a.unit_build) in unit['receipts_sha256'].values()
 assert unit['checker_sha256']==sha(Path(__file__).parent/'check_hd_unit_lifecycle.py')
 rows=unit['source_observations'];assert len(rows)==unit['hit_sources'] and sum(r['calls'] for r in rows)==unit['source_calls']
 for row in rows:
  f=next(f for f in frames if f['research_id']==row['research_id'])
  assert f['file']=='ICONS.SS' and f['ordinal']==row['ordinal']
  assert all(f[k]==row[k] for k in ['encoded_sha256','indexed_sha256','size','opaque_pixels'])
  assert row['descriptors']==[[200,320,0,0x2cae]] and len(row['write_sha256'])==1
  f['unit_pedia_native_sample']={'state':'DRAFT','spec':'docs/spec/070-hd-unit-small-images.md','report_sha256':sha(a.unit_report),
    'calls':row['calls'],'source_far':row['source_far'],'record_far':row['record_far'],'sorted_local_offset_value_sha256':row['write_sha256'][0],
    'first_entry_step':row['first_entry_step'],'claim':'confirmed recorded pedia source and native writes only; no new formal HD, world movement, combat or animation credit'}
 public['unit_pedia_native_evidence']={'report_sha256':sha(a.unit_report),'build_sha256':sha(a.unit_build),'sources':80,
   'source_calls':196,'checkpoints':35,'dos_inputs':353,'raw_events':5048144,'end_step':601800000,'production_connected':False,
   'claim':'23 distinct normal unit-pedia entries plus one wrap to first; unknown writes revoke, including 239 same-value losses; no stage transfer credit'}
if ship_review:
 for ordinal in ship_review['sources']:
  f=next(f for f in frames if f['file']=='ICONS.SS' and f['ordinal']==ordinal)
  assert f['formal_assets']==['icons-%03d.png'%ordinal] and 'unit_pedia_native_sample' in f
  f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/070-hd-unit-small-images.md','formal_connected':True,'review_sha256':sha(a.ship_conformed_report),'scope':'normal unit-pedia, original per-frame PNG RGBA and standard cursor only; native flags and 26 whole transparent source cells retained; world movement, combat and animation unverified'}
 public['ship_pedia_conformance']={'ready_review_sha256':sha(a.ship_ready_report),'review_sha256':sha(a.ship_conformed_report),'sources':ship_review['sources'],'formal_assets':78,'ship_gui_samples':100,'claim':'five standalone ship sprites within recorded normal pedia only; other sources, program-drawn graphics, animation and full HD remain incomplete'}
if vehicle_review:
 for ordinal in vehicle_review['sources']:
  f=next(f for f in frames if f['file']=='ICONS.SS' and f['ordinal']==ordinal)
  assert f['formal_assets']==['icons-%03d.png'%ordinal] and 'unit_pedia_native_sample' in f
  f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/070-hd-unit-small-images.md','formal_connected':True,'review_sha256':sha(a.vehicle_conformed_report),'scope':'normal unit-pedia Wagon Train, Artillery and Treasure; per-frame native content rectangle, raw PNG alpha, native flags and standard cursor; world movement, combat and animation unverified'}
 public['vehicle_pedia_conformance']={'ready_review_sha256':sha(a.vehicle_ready_report),'review_sha256':sha(a.vehicle_conformed_report),'sources':vehicle_review['sources'],'formal_assets':81,'unit_gui_samples':60,'claim':'three standalone vehicle/artillery sprites in recorded normal pedia only; other sources, program-drawn graphics, animation and full HD remain incomplete'}
if colonist_review:
 for ordinal in colonist_review['sources']:
  f=next(f for f in frames if f['file']=='ICONS.SS' and f['ordinal']==ordinal)
  assert f['formal_assets']==['icons-%03d.png'%ordinal] and 'unit_pedia_native_sample' in f
  f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/070-hd-unit-small-images.md','formal_connected':True,'review_sha256':sha(a.colonist_conformed_report),'scope':'normal Colonists pedia, 22 per-frame PNGs and content rectangles, native flags, original alpha and all22 standard-cursor hover/return; three inherited pedia images also checked; world movement, combat and animation unverified'}
 public['colonist_pedia_conformance']={'ready_review_sha256':sha(a.colonist_ready_report),'review_sha256':sha(a.colonist_conformed_report),'sources':colonist_review['sources'],'formal_assets':103,'unit_gui_samples':54,'resource_revalidation':{'scope':'R74 all 103 raw PNGs; complete positively loaded private fixture and exact restore per case','case_count':323,'six_test_families_completed_cases':329,'review_sha256':colonist_review['receipts_sha256']['r74-resource-complete-r6-check.json'],'legacy_fixture_erratum':'R72/R73 Go per-file fault credit withdrawn where the copied fixture omitted unrelated graphics or CUSTOMIZ.PIK. Current complete-fixture cases supersede those negatives; native, actual GUI and package evidence remain separate.'},'claim':'22 colonist frames in recorded normal pedia only; other sources, program-drawn graphics, animation and full HD remain incomplete'}
if unit19_review:
 for ordinal in unit19_review['sources']:
  f=next(f for f in frames if f['file']=='ICONS.SS' and f['ordinal']==ordinal)
  assert f['formal_assets']==['icons-%03d.png'%ordinal] and 'unit_pedia_native_sample' in f
  f['source_contract_reference']={'state':'CONFORMED','spec':'docs/spec/070-hd-unit-small-images.md','formal_connected':True,'review_sha256':sha(a.unit19_conformed_report),'scope':'19 remaining R71-observed unit frames in normal 14-page pedia, all19 standard-cursor hover/return, per-frame native content rectangles and raw alpha; world movement, combat and animation unverified'}
 public['unit19_pedia_conformance']={'ready_review_sha256':sha(a.unit19_ready_report),'review_sha256':sha(a.unit19_conformed_report),'sources':unit19_review['sources'],'formal_assets':122,'unit_gui_samples':178,'go_named_cases':457,'small_resource_rejection_types':321,'resource_cases':131,'resource_scope':'all new19 PNG triplets, all source/manifest faults and 20 inherited art representatives; other 249 catalog cases not rerun','claim':'19 unit frames in recorded normal pedia only; all 80 R71-observed small-image sources now connected in their verified scenes. Other sources, program-drawn graphics, world movement, combat, animation and full HD remain incomplete'}

public['coverage_limits']['additional_ready_source_contracts']=sum(f.get('source_contract_reference',{}).get('state')=='READY' and not f.get('source_contract_reference',{}).get('formal_connected') for f in frames)
out.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
print('PASS_METADATA_ONLY_FULL_SOURCE_INDEX',len(frames),len(bindings),sha(out),flush=True)
