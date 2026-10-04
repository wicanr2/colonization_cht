#!/usr/bin/env python3
"""Docker內驗收正常港口船隻標題、當次三列及關閉。"""
import argparse,json
from pathlib import Path
from PIL import Image,ImageChops
from check_goal134_window import load,same_state
from check_goal178_ship import ORIGINALS,sha,png_for
from check_goal181_purchase import verify as verify_flow
from check_goal181_rename import need
EVIDENCE_SHA='55dd04e6ca91b737a7793cfe03b39caab2ca3cb1a0fb0afe133368d21049221e'

def verify(game,root,evidence):
    batch=json.loads((evidence/'batch.json').read_text())
    need(set(batch['save_manifest'])=={'COLONY03.SAV','COLONY09.SAV'},'原版存檔清冊不同')
    result=verify_flow(game,root,evidence,evidence_sha=EVIDENCE_SHA,field_count=2,shot_count=14,require_purchase_layout=False,expected_save_manifest=batch['save_manifest'],scope='僅正常港口Caravel標題、原始第3／4／6列及Escape關閉；教學、其餘三列與其他船隻局勢未採用')
    sources={f['source']['candidate_id']:f for f in batch['fields']}
    need(set(sources)=={'GAME.TXT:@COLONYUNIT:0x00009A33','GAME.TXT:@SHIPOPTIONS:0x00009AC0#6+list'},'船隻來源鍵不同')
    for f in sources.values():need(f['shots']==['ship-options-after-tutorial'] and f['measurement']['actual_px']==30 and f['measurement']['cap_h']==8,'正常取樣或字級不同')
    need(sources['GAME.TXT:@COLONYUNIT:0x00009A33']['source']['safe']==[77,76,265,88] and sources['GAME.TXT:@SHIPOPTIONS:0x00009AC0#6+list']['source']['safe']==[81,90,218,126],'核准安全區不同')
    layout=json.loads((evidence/'layout.json').read_text());need(layout['result']=='PASS' and len(layout['cases'])==23,'名稱量測不齊')
    baseline=load(root/'baseline-v105');zh=load(root/'replay-zh');control=load(root/'replay-control');same_state(baseline,control,'舊正式改變原版')
    need(all(baseline[0][k]==control[0][k] for k in ('state','input_hashes','opened')),'舊正式完整終點不同')
    indices={tag:{c['step']:c for c in d[0]['checkpoints'] if c['label']!='final'} for tag,d in [('baseline-v105',baseline),('replay-zh',zh),('replay-control',control)]}
    need(set(indices['baseline-v105'])==set(batch['shots'].values()),'舊正式取樣缺失')
    changed=[]
    for name,step in batch['shots'].items():
        need(all(indices['baseline-v105'][step][k]==indices['replay-control'][step][k] for k in ('memory_sha256','raw_sha256','palette_sha256')),'舊正式原版取樣不同')
        before=Image.open(png_for(root,'baseline-v105',indices['baseline-v105'][step])).convert('RGB');after=Image.open(png_for(root,'replay-zh',indices['replay-zh'][step])).convert('RGB')
        if ImageChops.difference(before,after).getbbox():changed.append(name)
        portrait=tuple(v*4 for v in batch['portrait']);need(ImageChops.difference(before.crop(portrait),after.crop(portrait)).getbbox() is None,'船隻圖示改變')
        for rect in batch['new_areas'].get(name,[]):
            box=tuple(v*4 for v in rect);need(ImageChops.difference(before.crop(box),after.crop(box)).getbbox() is not None,'新欄未顯示');after.paste(before.crop(box),box)
        need(ImageChops.difference(before,after).getbbox() is None,'核准兩欄區外改變')
    need(changed==['ship-options-after-tutorial'],'覆蓋生命週期不同')
    saves=sorted((root/'baseline-v105-save').glob('*.SAV'));need({p.name:sha(p) for p in saves}==batch['save_manifest'],'舊正式輸出存檔不同')
    result.update(original_final_sides=6,baseline_images_equal_outside_fields=14,portrait_unchanged=True,save_manifest=batch['save_manifest'])
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('game','reports','evidence'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    if any(not(a.game/n).is_file() for n in ORIGINALS):print('SKIP：缺合法原版，不宣稱船隻驗收通過');return 77
    try:result=verify(a.game,a.reports,a.evidence)
    except (ValueError,OSError,AssertionError,KeyError,TypeError,IndexError) as e:print('FAIL：'+str(e));return 1
    print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
