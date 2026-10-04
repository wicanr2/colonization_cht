#!/usr/bin/env python3
"""在Docker驗收正常歐洲砲台購入確認與接受後的三個中文欄位。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal178_ship import ORIGINALS, equal_image, png_for, sha
from check_goal181_europe import visible_fields
from check_goal181_rename import need

EVIDENCE_SHA = '7abe110f339b307ab58974efcdea20b5c02ccff99b6e720d2a19331edadb56c5'


PURCHASE_SCOPE = '僅正常Artillery500購入確認、Enter接受及返回世界；不外推其他單位、取消、稅率或其他局勢'


def verify(game, root, evidence, *, evidence_sha=EVIDENCE_SHA, field_count=3, shot_count=9,
           require_purchase_layout=True, scope=PURCHASE_SCOPE, expected_save_manifest=None):
    for name, expected in ORIGINALS.items():
        need(sha(game / name) == expected, '原版指紋不同：' + name)
    need(sha(evidence / 'batch.json') == evidence_sha, '凍結欄位清冊不同')
    batch = json.loads((evidence / 'batch.json').read_text())
    need(batch['result'] == 'PASS' and batch['field_count'] == len(batch['fields']) == field_count, '欄位不齊')
    for path, expected in batch['evidence_hashes'].items():
        need(sha(evidence / path) == expected, '來源或量測不同：' + path)
    need(sha(root / 'gui-colony.inputs.json') == batch['inputs_sha256'], '正常GUI輸入不同')
    inputs = json.loads((root / 'gui-colony.inputs.json').read_text())
    need(not inputs.get('rejected') and inputs['end'] == batch['end'], '輸入拒絕或終點不同')
    tags = ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas')
    loaded = {tag: load(root / tag) for tag in tags}
    control = loaded['replay-control'][0]
    need(control['control'] and control['state']['steps'] == batch['end'] and
         control['state']['memory_sha256'] == batch['memory_sha256'], '原版控制終點不同')
    for tag, value in loaded.items():
        if tag != 'replay-control':
            same_state(value, loaded['replay-control'], tag + '完整原版不同')
        need(all(value[0][key] == control[key] for key in ('state', 'input_hashes', 'opened')),
             tag + '原版狀態或讀檔不同')
        need(hashlib.sha256(value[1]['memory']).hexdigest() == batch['memory_sha256'], '完整RAM不同')
    for name, expected in control['input_hashes'].items():
        need(sha(game / name) == expected, '原始檔不同：' + name)
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (root / 'gui-colony.shots').read_text().splitlines()))
    need(shots == batch['shots'] and len(shots) == shot_count, 'GUI取樣不同')
    indices = {tag: {cp['step']: cp for cp in loaded[tag][0]['checkpoints'] if cp['label'] != 'final'}
               for tag in tags if tag != 'gui-colony'}
    need(all(set(cps) == set(shots.values()) for cps in indices.values()), '重播取樣缺失')
    observer = load(evidence / 'observer/observer')
    same_state(observer, loaded['replay-control'], '量測副本改變原版')
    need(all(observer[0][key] == control[key] for key in ('state', 'input_hashes', 'opened')),
         '量測原版終點不同')
    observed = {cp['step']: cp for cp in observer[0]['checkpoints'] if cp['label'] != 'final'}
    need(set(observed) == set(shots.values()), '量測共同取樣缺失')
    cache = {}

    def frame(tag, step):
        key = tag, step
        if key not in cache:
            cache[key] = Image.open(png_for(root, tag, indices[tag][step])).convert('RGB')
        return cache[key]

    for name, step in shots.items():
        equal_image(root / f'gui-colony.{name}.png', png_for(root, 'replay-zh', indices['replay-zh'][step]))
        equal_image(evidence / f'observer/observer.cp-{step}.png',
                    png_for(root, 'replay-zh', indices['replay-zh'][step]))
        for tag in indices:
            need(all(indices[tag][step][key] == indices['replay-control'][step][key]
                     for key in ('memory_sha256', 'raw_sha256', 'palette_sha256')), '原版共同取樣不同')
        need(all(observed[step][key] == indices['replay-control'][step][key]
                 for key in ('memory_sha256', 'raw_sha256', 'palette_sha256')), '量測共同取樣不同')
        need(ImageChops.difference(frame('neg-noatlas', step), frame('replay-control', step)).getbbox() is None,
             '缺圖集未完整回原文：' + name)
    pools = (visible_fields(loaded['replay-zh'][0], shots), visible_fields(loaded['gui-colony'][0], shots))
    verified = []
    for field in batch['fields']:
        source = field['source']
        for pool in pools:
            matches = [f for f in pool if all(f['source'].get(key) == source.get(key) for key in
                       ('candidate_id', 'shown', 'safe', 'font_px', 'source_linear', 'step', 'entry_ip', 'items', 'zh'))]
            need(len(matches) == 1 and set(field['shots']) <= set(matches[0]['shots']), '欄位未在正常GUI啟用')
        need(source['entry_ip'] == '0D21:00C6', '原版印字入口不同')
        measure = field['measurement']
        need(measure['actual_px'] == source['font_px'] and measure['cap_h'] > 0 and
             measure['overflow_px'] == 0 and any(c['candidate_px'] == source['font_px'] and c['fits']
                                                for c in measure['candidate_sizes']), '字級或超界回退不同')
        ink, safe = measure['actual_ink'], source['safe']
        need(0 <= ink['Min']['X'] < ink['Max']['X'] <= (safe[2] - safe[0]) * 4 and
             0 <= ink['Min']['Y'] < ink['Max']['Y'] <= (safe[3] - safe[1]) * 4, '墨跡越界')
        for name in field['shots']:
            step = shots[name]
            box = tuple(v * 4 for v in safe)
            need(ImageChops.difference(frame('replay-zh', step).crop(box),
                                      frame('replay-control', step).crop(box)).getbbox() is not None,
                 '欄位沒有中文畫面差異')
        verified.append({key: source[key] for key in ('candidate_id', 'shown', 'safe')})
    expected_saves = ({'COLONY03.SAV': batch['seed_sha256']} if expected_save_manifest is None
                      else expected_save_manifest)
    need(isinstance(expected_saves, dict) and expected_saves.get('COLONY03.SAV') == batch['seed_sha256'] and
         all(Path(name).name == name and name.endswith('.SAV') and isinstance(digest, str) and
             len(digest) == 64 for name, digest in expected_saves.items()), '存檔清冊不合法')
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save'):
        saves = sorted((root / folder).glob('*.SAV'))
        need({p.name: sha(p) for p in saves} == expected_saves, '原版輸出存檔不同')
    for folder in ('observer/scratch', 'source/scratch'):
        saves = sorted((evidence / folder).glob('*.SAV'))
        need({p.name: sha(p) for p in saves} == expected_saves, '觀測輸出存檔不同')
    proof = json.loads((evidence / 'source/source-query.log.matches.json').read_text())
    need(proof['inputs_sha256'] == batch['inputs_sha256'] and proof['final_step'] == batch['end'] and
         proof['memory_sha256'] == batch['memory_sha256'], '來源未綁定正常GUI終點')
    need([m['key'] for m in proof['matches']] == batch['headers'], '原版查詢不齊')
    for match in proof['matches']:
        need(match['header'] == match['key'] and match['cx'] == 1 and match['code_bytes'] == 'f3a6' and
             match['original_cs_ip'] == '0E2D:0832', '原版查詢定位不同')
        op, read = match['file_op'], match['read_op']
        need(op['Name'] == read['Name'] == 'GAME.TXT' and not op['Failed'] and op['Op'] == 'read' and
             op['Step'] == read['Step'] and op['Len'] == read['Want'] == read['Got'] == 512, '原版讀取不同')
    if require_purchase_layout:
        layout = json.loads((evidence / 'layout.json').read_text())
        need(layout['result'] == 'PASS' and layout['case_count'] == len(layout['cases']) == 24 and
             layout['unknown_rejected'] and layout['numeric_overflow_rejected'] and
             all(case['font_px'] == 30 for case in layout['cases']), '單位或數值排版未通過')
    return {'result': 'PASS', 'grade': 'confirmed', 'inputs_sha256': batch['inputs_sha256'],
            'final_step': batch['end'], 'final_memory_sha256': batch['memory_sha256'],
            'verified_fields': verified, 'gui_images_exact': shot_count, 'original_checkpoints_equal': shot_count,
            'original_final_sides': 5, 'gui_original_checkpoint_scope': '完整終點；取樣GUI畫面與重播全等',
            'field_count': field_count, 'evidence_sha256': evidence_sha, 'scope': scope}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'reports', 'evidence'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if any(not (args.game / name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版，不宣稱購入驗收通過')
        return 77
    try:
        result = verify(args.game, args.reports, args.evidence)
    except (ValueError, OSError, AssertionError, KeyError, TypeError, IndexError) as error:
        print('FAIL：' + str(error))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
