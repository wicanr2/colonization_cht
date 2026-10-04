#!/usr/bin/env python3
"""Docker內驗收正常駐守後的三列單位選項。"""
import argparse,json
from pathlib import Path
from PIL import Image,ImageChops
from check_goal134_window import load,same_state
from check_goal178_ship import ORIGINALS,sha,png_for
from check_goal181_purchase import verify as verify_flow
from check_goal181_rename import need
EVIDENCE_SHA='7e64586d896e6ab881779a749c469efd459b41b7dd907bc07d624822c4af000f'

def verify(game,root,evidence):
    result=verify_flow(game,root,evidence,evidence_sha=EVIDENCE_SHA,field_count=1,shot_count=13,require_purchase_layout=False,scope='僅正常COLONY03士兵駐守後再開選項的清除命令／警戒或登船／不做更動三列及關閉；未驗第1列及其他單位局勢不外推')
    batch=json.loads((evidence/'batch.json').read_text());f=batch['fields'][0];m=f['measurement']
    need(f['source']['shown']=='Clear orders. Sentry / Board ship. No changes.' and f['source']['safe']==[81,90,181,126],'三列或安全區不同')
    need(m['actual_px']==30 and m['cap_h']==8 and m['pitch']==12 and m['items']==['清除命令。','警戒／登船。','不做更動。'],'逐欄量測不同')
    baseline=load(root/'baseline-v94');zh=load(root/'replay-zh');control=load(root/'replay-control')
    same_state(baseline,control,'舊正式改變原版');need(all(baseline[0][k]==control[0][k] for k in ('state','input_hashes','opened')),'舊正式完整終點不同')
    indices={tag:{cp['step']:cp for cp in d[0]['checkpoints'] if cp['label']!='final'} for tag,d in [('baseline-v94',baseline),('replay-zh',zh),('replay-control',control)]}
    need(set(indices['baseline-v94'])==set(batch['shots'].values()),'舊正式取樣缺失')
    changed=[]
    for name,step in batch['shots'].items():
        need(all(indices['baseline-v94'][step][k]==indices['replay-control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256')),'舊正式原版取樣不同')
        before=Image.open(png_for(root,'baseline-v94',indices['baseline-v94'][step])).convert('RGB');after=Image.open(png_for(root,'replay-zh',indices['replay-zh'][step])).convert('RGB')
        if ImageChops.difference(before,after).getbbox():changed.append(name)
        portrait=tuple(v*4 for v in batch['portrait']);need(ImageChops.difference(before.crop(portrait),after.crop(portrait)).getbbox() is None,'駐守單位圖示改變')
        for rect in batch['new_areas'].get(name,[]):
            box=tuple(v*4 for v in rect);need(ImageChops.difference(before.crop(box),after.crop(box)).getbbox() is not None,'新欄未顯示');after.paste(before.crop(box),box)
        need(ImageChops.difference(before,after).getbbox() is None,'核准清單區外改變')
    need(changed==['options-after-fortify'],'新覆蓋生命週期不同')
    saves=sorted((root/'baseline-v94-save').glob('*.SAV'));need([p.name for p in saves]==['COLONY03.SAV'] and sha(saves[0])==batch['seed_sha256'],'舊正式修改存檔')
    result.update(original_final_sides=6,baseline_images_equal_outside_fields=13,portrait_unchanged=True)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('game','reports','evidence'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    if any(not(a.game/n).is_file() for n in ORIGINALS):print('SKIP：缺合法原版，不宣稱駐守選項驗收通過');return 77
    try:result=verify(a.game,a.reports,a.evidence)
    except (ValueError,OSError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
    print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
