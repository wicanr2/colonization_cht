#!/usr/bin/env python3
"""Docker內驗收正常載貨、卸貨、下錨、清除命令的船隻選单。"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops
from check_goal134_window import load,same_state
from check_goal178_ship import ORIGINALS,sha,png_for
from check_goal181_purchase import verify as verify_flow
from check_goal181_rename import need
EVIDENCE_SHA='ce79d6c681c1469cf761d28810a3fb93634e19934ddabc0b36c0a17b63d51209'
PROFILES={
 'loaded-ship-options':(['Sentry.','Anchor in harbor ("Fortify").','Unload all cargo.','No changes.'],['警戒。','在港口下錨（「駐守」）。','卸下所有貨物。','不做更動。'],[81,84,218,132],[6,4,391,180]),
 'anchored-ship-options':(['Clear orders.','Sentry.','No changes.'],['清除命令。','警戒。','不做更動。'],[81,90,145,126],[6,4,160,132]),
}

def verify(game,root,evidence):
 batch=json.loads((evidence/'batch.json').read_text())
 need(set(batch['save_manifest'])=={'COLONY03.SAV','COLONY09.SAV'},'原版存檔清冊不同')
 result=verify_flow(game,root,evidence,evidence_sha=EVIDENCE_SHA,field_count=2,shot_count=23,require_purchase_layout=False,expected_save_manifest=batch['save_manifest'],scope='僅正常Jamestown港口Caravel載貨第3／4／5／6列、下錨第2／3／6列，以及卸貨／清除後恢復與Escape關閉；其他組合及移貨提示未採用')
 need({tuple(f['shots']) for f in batch['fields']}=={(n,) for n in PROFILES},'新增選單取樣不同')
 for field in batch['fields']:
  n=field['shots'][0];items,zh,safe,ink=PROFILES[n];e=field['source'];m=field['measurement']
  need(e['candidate_id']=='GAME.TXT:@SHIPOPTIONS:0x00009AC0#6+list' and e['items']==items and e['shown']==' '.join(items),'完整列或來源鍵不同')
  need(e['source_linear']==175408 and e['safe']==safe and e['font_px']==m['actual_px']==30 and m['cap_h']==8 and m['pitch']==12,'選單字級或安全區不同')
  need(m['items']==zh and [m['actual_ink'][a][c] for a,c in [('Min','X'),('Min','Y'),('Max','X'),('Max','Y')]]==ink,'譯文或墨跡不同')
  expected={'Min':{'X':safe[0],'Y':safe[1]},'Max':{'X':safe[2],'Y':safe[3]}}
  need(m['safe']==expected and m['base']==e['source_linear'] and m['start']==e['step'],'量測未綁定來源')
  queries=[x for x in json.loads((evidence/'source/source-query.log.matches.json').read_text())['matches'] if x['key']=='@SHIPOPTIONS' and x['step']<e['step']]
  need(queries and queries[-1]['file_op']['Pos']==39424 and queries[-1]==field['original_query'],'原版SHIP來源查詢不同')
 need(batch['new_areas']=={n:[v[2]] for n,v in PROFILES.items()},'核准區不同')
 need(sha(root/'gui-colony.capture-attempts.jsonl')==sha(evidence/'sync-receipts.jsonl'),'正常GUI同步收據不同')
 receipts=[json.loads(l) for l in (evidence/'sync-receipts.jsonl').read_text().splitlines()];accepted=[x for x in receipts if x['aligned']]
 need(len(accepted)==23 and {x['name']:x['frame_step'] for x in accepted}==batch['shots'],'GUI指紋取樣不齊')
 for row in accepted:
  with Image.open(root/f"gui-colony.{row['name']}.png") as im:
   digest=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
   need(row['stable'] and row['canvas_size']==row['capture_size']==list(im.size)==[1280,800] and digest==row['canvas_rgba_sha256']==row['capture_rgba_sha256'],'GUI未與畫布對齊')
 baseline=load(root/'baseline-v126');zh=load(root/'replay-zh');control=load(root/'replay-control');same_state(baseline,control,'v126改變原版')
 need(all(baseline[0][k]==control[0][k] for k in ('state','input_hashes','opened')),'v126完整原版不同')
 indices={tag:{c['step']:c for c in d[0]['checkpoints'] if c['label']!='final'} for tag,d in [('baseline-v126',baseline),('replay-zh',zh),('replay-control',control)]}
 need(set(indices['baseline-v126'])==set(batch['shots'].values()),'v126取樣缺失')
 changed=[]
 for n,step in batch['shots'].items():
  need(all(indices['baseline-v126'][step][k]==indices['replay-control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256')),'v126原版取樣不同')
  before=Image.open(png_for(root,'baseline-v126',indices['baseline-v126'][step])).convert('RGB');after=Image.open(png_for(root,'replay-zh',indices['replay-zh'][step])).convert('RGB')
  if ImageChops.difference(before,after).getbbox():changed.append(n)
  portrait=tuple(v*4 for v in ([54,68,73,88] if n=='loaded-ship-options' else [54,74,73,94]))
  need(ImageChops.difference(before.crop(portrait),after.crop(portrait)).getbbox() is None,'船隻圖示不同')
  for rect in batch['new_areas'].get(n,[]):
   box=tuple(v*4 for v in rect);need(ImageChops.difference(before.crop(box),after.crop(box)).getbbox() is not None,'新清單沒有顯示');after.paste(before.crop(box),box)
  need(ImageChops.difference(before,after).getbbox() is None,'安全區外改變或關框殘留')
 need(changed==list(PROFILES),'選單生命週期不同')
 need({p.name:sha(p) for p in (root/'baseline-v126-save').glob('*.SAV')}==batch['save_manifest'],'v126存檔不同')
 result.update(original_final_sides=6,baseline_images_equal_outside_fields=23,portrait_unchanged=True,gui_canvas_hashes_equal=23,save_manifest=batch['save_manifest'])
 return result


# 規格038 READY：僅驗已取證的毛皮／輕帆船與玩家同名城市。
MESSAGES_EVIDENCE_SHA = 'a497850bfb01f4b53f89009dbce7a078bb19de45700ff1e490075e51ac951716'
MESSAGE_FIELDS = {
 'cargo-loading-header': ('Loading: Caravel', '裝載中：輕帆船', [134,131,193,139], 22, ['LABELS.TXT:@MISC:0x00000205']),
 'cargo-loading-commodity': ('Loading Furs ', '裝載中毛皮', [137,0,182,8], 22, ['LABELS.TXT:@CMESSAGE:0x00000CE9']),
 'cargo-moved-unit': ('27 Furs moved to Caravel ', '27 毛皮已移動至輕帆船', [115,0,203,8], 22, ['LABELS.TXT:@CMESSAGE:0x00000C42']),
 'cargo-moved-city': ('27 Furs moved to Jamestown ', '27 毛皮已移動至詹姆斯敦（Jamestown）', [109,0,210,8], 20, ['LABELS.TXT:@CMESSAGE:0x00000C42']),
}

def verify_messages(game, root, evidence):
 batch=json.loads((evidence/'batch.json').read_text())
 need(sha(evidence/'batch.json')==MESSAGES_EVIDENCE_SHA,'貨物訊息審查清冊不同')
 for name,digest in batch['original_files'].items():
  need(sha(game/name)==digest,'貨物訊息原版版本不同：'+name)
 for rel,digest in batch['artifact_hashes'].items():
  need(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'收據路徑超出範圍')
  need(sha(evidence/rel)==digest,'貨物訊息收據不同：'+rel)
 need(batch['gui_inputs_sha256']==sha(root/'gui-colony.inputs.json'),'貨物訊息GUI輸入不同')
 need(batch['capture_receipts_sha256']==sha(root/'gui-colony.capture-attempts.jsonl'),'貨物訊息GUI同步收據不同')
 shots=dict((n,int(v)) for n,v in [l.split() for l in (root/'gui-colony.shots').read_text().splitlines()])
 need(shots==batch['shots'] and len(shots)==24,'貨物訊息正常GUI清冊不同')
 gui=load(root/'gui-colony');zh=load(root/'replay-zh');control=load(root/'replay-control')
 need(gui[0]['state']==zh[0]['state'] and gui[1]==zh[1],'貨物訊息新GUI完整原版不同')
 sides={name:load(root/name) for name in ['replay-zh','replay-control','neg-noatlas','replay-observer','baseline-v136']}
 need(zh[0]['state']['steps']==batch['final_step'] and zh[0]['state']['memory_sha256']==batch['final_memory_sha256'],'貨物訊息原版終點不同')
 for name,data in sides.items():
  if name!='replay-control':same_state(data,control,'貨物訊息完整原版不同：'+name)
  need({f.name:sha(f) for f in (root/(name+'-save')).glob('*.SAV')}==batch['save_manifest'],'貨物訊息存檔不同：'+name)
 need({f.name:sha(f) for f in (root/'scratch').glob('*.SAV')}==batch['save_manifest'],'GUI原版存檔不同')
 indices={tag:{c['label']:c for c in data[0]['checkpoints'] if c['label']!='final'} for tag,data in sides.items()}
 expected_cp={'cp-'+str(step) for step in shots.values()}
 need(all(set(v)==expected_cp for v in indices.values()),'貨物訊息共同原版取樣缺失')
 safe_boxes=[tuple(v*4 for v in values[2]) for values in MESSAGE_FIELDS.values()]
 changed=[];receipts=[json.loads(l) for l in (root/'gui-colony.capture-attempts.jsonl').read_text().splitlines()]
 for name,step in shots.items():
  label='cp-'+str(step);reference=indices['replay-zh'][label]
  for tag in sides:
   cp=indices[tag][label]
   need(all(cp[k]==reference[k] for k in ['step','memory_sha256','raw_sha256','palette_sha256']),'貨物訊息原版取樣不同：'+tag)
   need(sha(root/f'{tag}.{label}.idx')==cp['raw_sha256'] and sha(root/f'{tag}.{label}.pal')==cp['palette_sha256'],'原索引或色盤收據雜湊不同')
  live=Image.open(root/f'replay-zh.{label}.png').convert('RGB');capture=Image.open(root/f'gui-colony.{name}.png').convert('RGBA')
  accepted=[x for x in receipts if x['name']==name and x['aligned']]
  need(len(accepted)==1,'正常GUI沒有唯一對齊收據')
  receipt=accepted[0];digest=hashlib.sha256(capture.tobytes()).hexdigest()
  need(receipt['stable'] and receipt['frame_step']==step and receipt['canvas_size']==receipt['capture_size']==[1280,800] and digest==receipt['canvas_rgba_sha256']==receipt['capture_rgba_sha256'],'GUI畫布指紋不同')
  need(live.size==(1280,800) and live.tobytes()==capture.convert('RGB').tobytes(),'GUI與正式重播畫面不同')
  observed=Image.open(root/f'replay-observer.{label}.png').convert('RGB')
  need(live.tobytes()==observed.tobytes(),'唯讀觀測改變正式畫面')
  baseline=Image.open(root/f'baseline-v136.{label}.png').convert('RGB')
  if ImageChops.difference(live,baseline).getbbox():changed.append(name)
  restored=live.copy()
  for box in safe_boxes:restored.paste(baseline.crop(box),box)
  need(ImageChops.difference(restored,baseline).getbbox() is None,'貨物訊息安全區外改變或殘留')
 need(changed==batch['changed_shots'],'貨物訊息生命週期不同')
 fields=[]
 for key,(shown,translated,safe,size,source_ids) in MESSAGE_FIELDS.items():
  f=batch['fields'][key];event=f['source'];measurement=f['measurement'];cid='STRING:template:'+key
  need(event['candidate_id']==cid and event['shown']==shown and event['zh']==translated and event['safe']==safe and event['font_px']==size and event['entry_ip']=='0D21:00C6','貨物訊息來源欄位不同')
  need(event in zh[0]['events'] and any(e.get('candidate_id')==cid and e.get('shown')==shown and e.get('stage')=='active' for e in zh[0]['events']),'貨物訊息未在正式原版啟用')
  rect=measurement['safe'];expected={'Min':{'X':safe[0],'Y':safe[1]},'Max':{'X':safe[2],'Y':safe[3]}}
  need(measurement['shown']==shown and measurement['zh']==translated and rect==expected and measurement['cap_h']==5 and measurement['actual_px']==size and measurement['overflow_px']==0,'貨物訊息專屬量測不同')
  ink=measurement['actual_ink'];need(0<=ink['Min']['X']<ink['Max']['X']<=(safe[2]-safe[0])*4 and 0<=ink['Min']['Y']<ink['Max']['Y']<=(safe[3]-safe[1])*4,'中文墨跡超出原安全區')
  need(measurement['base']==event['source_linear'] and measurement['start']==event['step'] and [c['candidate_px'] for c in measurement['candidate_sizes']]==list(range(22,14,-1)),'字級量測未綁同次來源')
  box=tuple(v*4 for v in safe)
  need(f['shots'] and all(n in shots for n in f['shots']),'貨物訊息可見GUI缺失')
  for name in f['shots']:
   label='cp-'+str(shots[name]);a=Image.open(root/f'replay-zh.{label}.png').convert('RGB');old=Image.open(root/f'baseline-v136.{label}.png').convert('RGB')
   need(ImageChops.difference(a.crop(box),old.crop(box)).getbbox() is not None,'貨物訊息未呈現在正常GUI')
   missing=Image.open(root/f'neg-noatlas.{label}.png').convert('RGB');native=Image.open(root/f'replay-control.{label}.png').convert('RGB')
   need(missing.crop(box).tobytes()==native.crop(box).tobytes(),'缺字模貨物訊息未回原文')
  fields.append({'candidate_id':cid,'shown':shown,'safe':safe,'source_ids':source_ids})
 need(batch['fields']['cargo-loading-commodity']['shots']==['cargo-loading-preview'],'未驗按住裝貨畫面')
 # 同名玩家城市的正常輸入來自v143，不把文字相同當單位來源。
 city=load(evidence/'cityname');city_reference=load(evidence/'city-reference/zh')
 need(city[0]['state']==city_reference[0]['state'] and city[0]['opened']==city_reference[0]['opened'] and city[0]['input_hashes']==city_reference[0]['input_hashes'] and city[1]==city_reference[1],'正式同名城市原版回歸不同')
 city_shots=dict((n,int(v)) for n,v in [l.split() for l in (evidence/'city/shots').read_text().splitlines()])
 need(len(city_shots)==26,'同名城市正常GUI不齊')
 for step in city_shots.values():
  label='cp-'+str(step)
  for ext in ['idx','pal']:need((evidence/f'cityname.{label}.{ext}').read_bytes()==(evidence/f'city-reference/zh.{label}.{ext}').read_bytes(),'同名城市原索引／色盤不同')
  need(Image.open(evidence/f'cityname.{label}.png').convert('RGBA').tobytes()==Image.open(evidence/f'city-reference/zh.{label}.png').convert('RGBA').tobytes(),'同名城市畫面回歸不同')
 names={e.get('zh') for e in city[0]['events'] if e.get('stage')=='source' and e.get('shown')=='27 Furs moved to Caravel '}
 need({'27 毛皮已移動至輕帆船','27 毛皮已移動至Caravel'}<=names,'同名角色翻譯不分來源')
 need({f.name:sha(f) for f in (evidence/'cityname-save').glob('*.SAV')}==batch['city_save_manifest'],'同名城市存檔不同')
 copies=[json.loads(l) for l in (evidence/'source/source-query.log.concat.jsonl').read_text().splitlines()]
 params={(x['source_parameter_linear'],x['source_now']) for x in copies if x.get('original_cs_ip')=='0E2D:11CF' and x.get('stage')=='before-instruction'}
 need({(317818,'Loading'),(320325,'Loading'),(320171,'moved to'),(315996,'Furs'),(316238,'Caravel'),(140264,'Jamestown')}<=params,'原版組字角色來源缺失')
 source=json.loads((evidence/'source/source-query.log.state.json').read_text())
 need(source['step']==batch['final_step'] and source['memory_sha256']==batch['final_memory_sha256'],'組字來源原版RAM不同')
 need({f.name:sha(f) for f in (evidence/'source/scratch').glob('*.SAV')}==batch['save_manifest'],'組字來源存檔不同')
 return {'result':'PASS','grade':'confirmed','field_count':4,'verified_fields':fields,'inputs_sha256':batch['gui_inputs_sha256'],'final_step':batch['final_step'],'final_memory_sha256':batch['final_memory_sha256'],'original_final_sides':6,'original_checkpoints_equal':24,'gui_images_exact':24,'same_named_city_images_exact':26,'evidence_sha256':MESSAGES_EVIDENCE_SHA,'scope':'只驗Furs／Caravel來源池、四種貨物訊息、完整Loading按住提示與同名城市隔離；其他商品／船型未驗'}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('game','reports','evidence'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--cargo-messages',action='store_true')
 a=p.parse_args()
 required=set(ORIGINALS)|({"GAME.TXT","LABELS.TXT","NAMES.TXT"} if a.cargo_messages else set())
 if any(not(a.game/n).is_file() for n in required):print('SKIP：缺合法原版，不宣稱船隻載貨與下錨驗收通過');return 77
 try:result=(verify_messages if a.cargo_messages else verify)(a.game,a.reports,a.evidence)
 except (ValueError,OSError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
 print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
