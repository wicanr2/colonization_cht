#!/usr/bin/env python3
"""Docker內驗收正常抵港教學、Enter關閉及畫布指紋同步。"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops
from check_goal134_window import load,same_state
from check_goal178_ship import ORIGINALS,sha,png_for
from check_goal181_purchase import verify as verify_flow
from check_goal181_rename import need
EVIDENCE_SHA='5c236781c08f1cbffcbe43dc0f58a6e12a2c59588b6a1b8f46ca1680e7904af4'

def verify(game,root,evidence):
 batch=json.loads((evidence/'batch.json').read_text())
 need(set(batch['save_manifest'])=={'COLONY03.SAV','COLONY09.SAV'},'原版存檔清冊不同')
 result=verify_flow(game,root,evidence,evidence_sha=EVIDENCE_SHA,field_count=1,shot_count=14,require_purchase_layout=False,expected_save_manifest=batch['save_manifest'],scope='僅正常Jamestown抵港教學、Enter關閉及正常後續船隻選單；不外推其他教學或裝貨結果')
 field=batch['fields'][0];e=field['source'];m=field['measurement']
 need(e['candidate_id']=='GAME.TXT:@TUTORIAL12' and field['shots']==['dock-arrival-tutorial'],'教學來源或取樣不同')
 need(e['source_linear']==175180 and e['safe']==[50,73,269,187] and e['font_px']==m['actual_px']==30 and m['cap_h']==9,'教學字級或安全區不同')
 need(m['candidate_sizes'][0]['rows']==5 and '%STRING0' not in m['zh'] and '{ESC}' in m['zh'] and '{G}' in m['zh'],'完整正文或強調不同')
 layout=json.loads((evidence/'layout.json').read_text());need(layout['result']=='PASS' and len(layout['cases'])==5 and all(c['px']==30 for c in layout['cases']),'名稱字模量測不齊')
 need(sha(root/'gui-colony.capture-attempts.jsonl')==sha(evidence/'sync-receipts.jsonl'),'正常GUI同步收據不同')
 receipts=[json.loads(l) for l in (evidence/'sync-receipts.jsonl').read_text().splitlines()]
 accepted=[x for x in receipts if x['aligned']]
 need(len(accepted)==14 and {x['name']:x['frame_step'] for x in accepted}==batch['shots'],'指紋綁定取樣不齊')
 for row in accepted:
  with Image.open(root/f"gui-colony.{row['name']}.png") as im:
   digest=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
   need(row['stable'] and row['canvas_size']==row['capture_size']==list(im.size)==[1280,800] and digest==row['canvas_rgba_sha256']==row['capture_rgba_sha256'],'真GUI指紋未與畫布對齊')
 baseline=load(root/'baseline-v118');zh=load(root/'replay-zh');control=load(root/'replay-control');same_state(baseline,control,'舊正式改變原版')
 need(all(baseline[0][k]==control[0][k] for k in ('state','input_hashes','opened')),'舊正式完整終點不同')
 indices={tag:{c['step']:c for c in d[0]['checkpoints'] if c['label']!='final'} for tag,d in [('baseline-v118',baseline),('replay-zh',zh),('replay-control',control)]}
 need(set(indices['baseline-v118'])==set(batch['shots'].values()),'舊正式取樣缺失')
 changed=[]
 for name,step in batch['shots'].items():
  need(all(indices['baseline-v118'][step][k]==indices['replay-control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256')),'舊正式原版取樣不同')
  before=Image.open(png_for(root,'baseline-v118',indices['baseline-v118'][step])).convert('RGB');after=Image.open(png_for(root,'replay-zh',indices['replay-zh'][step])).convert('RGB')
  if ImageChops.difference(before,after).getbbox():changed.append(name)
  for rect in batch['new_areas'].get(name,[]):
   box=tuple(v*4 for v in rect);need(ImageChops.difference(before.crop(box),after.crop(box)).getbbox() is not None,'教學沒有顯示');after.paste(before.crop(box),box)
  need(ImageChops.difference(before,after).getbbox() is None,'教學安全區外改變或關閉殘留')
 need(changed==['dock-arrival-tutorial'],'教學生命週期不同')
 need({p.name:sha(p) for p in (root/'baseline-v118-save').glob('*.SAV')}==batch['save_manifest'],'舊正式輸出存檔不同')
 result.update(original_final_sides=6,baseline_images_equal_outside_fields=14,gui_canvas_hashes_equal=14,save_manifest=batch['save_manifest'])
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('game','reports','evidence'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args()
 if any(not(a.game/n).is_file() for n in ORIGINALS):print('SKIP：缺合法原版，不宣稱抵港教學驗收通過');return 77
 try:result=verify(a.game,a.reports,a.evidence)
 except (ValueError,OSError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
 print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
