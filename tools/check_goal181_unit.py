#!/usr/bin/env python3
"""Docker內驗收正常單位面板士兵標題及當次三列選項。"""
import argparse,json
from pathlib import Path
from PIL import Image,ImageChops
from check_goal134_window import load,same_state
from check_goal178_ship import ORIGINALS,sha,png_for
from check_goal181_purchase import verify as verify_flow
from check_goal181_rename import need

EVIDENCE_SHA='956e79529691fa8ccdb2eec656f7018b44c6725605a97a787aa8f3835b67cf03'

def verify(game,root,evidence):
 result=verify_flow(game,root,evidence,evidence_sha=EVIDENCE_SHA,field_count=2,shot_count=11,require_purchase_layout=False,scope='僅正常COLONY03選任士兵、右下單位面板的士兵標題與當次三列、Escape關閉及返回世界；其他名稱只有合成排版，不外推其餘兩列')
 batch=json.loads((evidence/'batch.json').read_text());layout=json.loads((evidence/'layout.json').read_text())
 need(layout['result']=='PASS' and len(layout['cases'])==22 and layout['longest_ink_px']==289 and layout['original_cap_h']==8 and layout['overflow_px']==0,'22個名稱排版不齊')
 for f in batch['fields']:
  need(f['source']['font_px']==30 and f['measurement']['cap_h']==8,'欄位字級不同')
  if f['source']['candidate_id'].endswith('+list'):need(f['measurement']['pitch']==12 and len(f['measurement']['items'])==3,'當次三列不同')
 baseline=load(root/'baseline-v74');zh=load(root/'replay-zh');control=load(root/'replay-control')
 same_state(baseline,control,'舊正式改變原版');need(all(baseline[0][k]==control[0][k] for k in ('state','input_hashes','opened')),'舊正式完整終點不同')
 indices={tag:{cp['step']:cp for cp in doc[0]['checkpoints'] if cp['label']!='final'} for tag,doc in [('baseline-v74',baseline),('replay-zh',zh),('replay-control',control)]}
 need(set(indices['baseline-v74'])==set(batch['shots'].values()),'舊正式取樣缺失')
 changed=[]
 for name,step in batch['shots'].items():
  need(all(indices['baseline-v74'][step][k]==indices['replay-control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256')),'舊正式原版取樣不同')
  before=Image.open(png_for(root,'baseline-v74',indices['baseline-v74'][step])).convert('RGB');after=Image.open(png_for(root,'replay-zh',indices['replay-zh'][step])).convert('RGB')
  if ImageChops.difference(before,after).getbbox():changed.append(name)
  portrait=tuple(v*4 for v in batch['portrait']);need(ImageChops.difference(before.crop(portrait),after.crop(portrait)).getbbox() is None,'單位圖示改變')
  for rect in batch['new_areas'].get(name,[]):
   box=tuple(v*4 for v in rect);need(ImageChops.difference(before.crop(box),after.crop(box)).getbbox() is not None,'新欄未顯示');after.paste(before.crop(box),box)
  need(ImageChops.difference(before,after).getbbox() is None,'核准文字區外改變')
 need(changed==list(batch['new_areas']),'新覆蓋生命週期不同')
 saves=sorted((root/'baseline-v74-save').glob('*.SAV'));need([p.name for p in saves]==['COLONY03.SAV'] and sha(saves[0])==batch['seed_sha256'],'舊正式修改存檔')
 result.update(original_final_sides=6,baseline_images_equal_outside_fields=11,portrait_unchanged=True)
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('game','reports','evidence'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args()
 if any(not(a.game/name).is_file() for name in ORIGINALS):print('SKIP：缺合法原版，不宣稱單位選項驗收通過');return 77
 try:result=verify(a.game,a.reports,a.evidence)
 except (ValueError,OSError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
 print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0

if __name__=='__main__':raise SystemExit(main())
