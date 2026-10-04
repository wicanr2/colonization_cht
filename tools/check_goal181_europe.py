#!/usr/bin/env python3
"""Docker內驗收正常歐洲港口取消操作、教學及F2至F10的已量測欄位。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal178_ship import ORIGINALS, equal_image, png_for, sha
from check_goal181_rename import need

EVIDENCE_SHA = '3fab1dec078a4a22f0c83dbc462c3362a9792eeed9e58742c04159be803ad2af'


def visible_fields(report, shots):
    """把來源物件保留至停用；只採正常GUI取樣時仍啟用的文字。"""
    pending, recent, active, spans = {}, {}, {}, []
    for e in report['events']:
        cid, stage = e.get('candidate_id', ''), e.get('stage')
        if stage == 'source' and 'font_px' in e and 'safe' in e:
            pending[cid, e['shown']] = e
            recent[cid] = e
        elif stage == 'active':
            source = pending.get((cid, e.get('shown'))) if e.get('shown') else recent.get(cid)
            if source:
                key = cid, source['shown'], tuple(source['safe'])
                active[key] = source, e['step']
        elif stage in ('expired', 'suspended'):
            for key in list(active):
                if key[0] == cid and (not e.get('shown') or key[1] == e['shown']):
                    source, start = active.pop(key)
                    spans.append((source, start, e['step']))
    spans += [(source, start, 1 << 62) for source, start in active.values()]
    out = {}
    for source, start, end in spans:
        if source['step'] < 50000000:
            continue
        names = [name for name, step in shots.items() if start <= step < end]
        if names:
            key = source['candidate_id'], source['shown'], tuple(source['safe'])
            if key not in out:
                out[key] = {'source': source, 'shots': []}
            out[key]['shots'] += [name for name in names if name not in out[key]['shots']]
    return list(out.values())


def verify(game, root, evidence):
    for name, expected in ORIGINALS.items():
        need(sha(game / name) == expected, '原版指紋不同：' + name)
    batch_path = evidence / 'batch.json'
    need(sha(batch_path) == EVIDENCE_SHA, '欄位及量測清冊不同')
    batch = json.loads(batch_path.read_text())
    need(batch['result'] == 'PASS' and batch['field_count'] == len(batch['fields']), '清冊未通過')
    for relative, expected in batch['evidence_hashes'].items():
        need(sha(evidence / relative) == expected, '量測或來源證據不同：' + relative)
    need(sha(root / 'gui-colony.inputs.json') == batch['inputs_sha256'], '正常GUI輸入不同')
    inputs = json.loads((root / 'gui-colony.inputs.json').read_text())
    need(not inputs.get('rejected') and inputs['end'] == batch['end'], '输入拒絕或終點不同')
    names = ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas', 'baseline-v66')
    loaded = {name: load(root / name) for name in names}
    control = loaded['replay-control'][0]
    need(control['control'] and control['state']['steps'] == batch['end'] and
         control['state']['memory_sha256'] == batch['memory_sha256'], '原版終點不同')
    for name, value in loaded.items():
        if name != 'replay-control':
            same_state(value, loaded['replay-control'], name + '完整原版不同')
        need(all(value[0][key] == control[key] for key in ('state', 'input_hashes', 'opened')),
             name + '原版狀態或讀檔不同')
        need(hashlib.sha256(value[1]['memory']).hexdigest() == batch['memory_sha256'], 'RAM不同')
    for name, expected in control['input_hashes'].items():
        need(sha(game / name) == expected, '實際輸入檔不同：' + name)
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (root / 'gui-colony.shots').read_text().splitlines()))
    need(shots == batch['shots'] and len(shots) == 26, '正常GUI取樣不同')
    indices = {name: {c['step']: c for c in loaded[name][0]['checkpoints'] if c['label'] != 'final'}
               for name in names if name != 'gui-colony'}
    need(all(set(cs) == set(shots.values()) for cs in indices.values()), '共同取樣缺失')
    observer = load(evidence / 'observer' / 'observer')
    same_state(observer, loaded['replay-control'], '量測觀測改變原版')
    need(observer[0]['state'] == control['state'] and observer[0]['opened'] == control['opened'],
         '量測觀測終點或讀檔不同')
    observed = {c['step']: c for c in observer[0]['checkpoints'] if c['label'] != 'final'}

    frame_cache = {}

    def frame(name, step):
        key = name, step
        if key not in frame_cache:
            frame_cache[key] = Image.open(png_for(root, name, indices[name][step])).convert('RGB')
        return frame_cache[key]

    changed = []
    for shot, step in shots.items():
        equal_image(root / f'gui-colony.{shot}.png', png_for(root, 'replay-zh', indices['replay-zh'][step]))
        equal_image(evidence / 'observer' / f'observer.cp-{step}.png',
                    png_for(root, 'replay-zh', indices['replay-zh'][step]))
        for name in indices:
            need(all(indices[name][step][key] == indices['replay-control'][step][key]
                     for key in ('memory_sha256', 'raw_sha256', 'palette_sha256')),
                 '原版取樣不同：' + name + '/' + shot)
        need(all(observed[step][key] == indices['replay-control'][step][key]
                 for key in ('memory_sha256', 'raw_sha256', 'palette_sha256')), '觀測取樣不同')
        need(ImageChops.difference(frame('neg-noatlas', step), frame('replay-control', step)).getbbox() is None,
             '缺圖集未完整回原文：' + shot)
        fresh, old = frame('replay-zh', step).copy(), frame('baseline-v66', step)
        ranges = batch['new_areas'].get(shot, [])
        if ImageChops.difference(fresh, old).getbbox():
            changed.append(shot)
        for safe in ranges:
            box = tuple(v * 4 for v in safe)
            need(ImageChops.difference(fresh.crop(box), old.crop(box)).getbbox() is not None,
                 '新欄位未顯示：' + shot)
            fresh.paste(old.crop(box), box)
        need(ImageChops.difference(fresh, old).getbbox() is None, '核准區外有新增差異：' + shot)
    need(changed == list(batch['new_areas']), '新欄位畫面範圍不同')
    shown = visible_fields(loaded['replay-zh'][0], shots)
    gui_fields = visible_fields(loaded['gui-colony'][0], shots)
    verified = []
    for field in batch['fields']:
        source = field['source']
        for pool in (shown, gui_fields):
            matches = [f for f in pool if all(f['source'].get(key) == source.get(key) for key in
                       ('candidate_id', 'shown', 'safe', 'font_px', 'source_linear', 'step', 'entry_ip', 'items', 'zh'))]
            need(len(matches) == 1 and set(field['shots']) <= set(matches[0]['shots']), '欄位未在正常GUI啟用')
        need(source['entry_ip'] == '0D21:00C6', '原始印字入口不同')
        measure = field['measurement']
        need(measure['actual_px'] == source['font_px'] and measure['overflow_px'] == 0 and
             measure['cap_h'] > 0 and any(c['candidate_px'] == source['font_px'] and c['fits']
                                         for c in measure['candidate_sizes']), '字級或超界回退不同')
        ink, safe = measure['actual_ink'], source['safe']
        need(0 <= ink['Min']['X'] < ink['Max']['X'] <= (safe[2] - safe[0]) * 4 and
             0 <= ink['Min']['Y'] < ink['Max']['Y'] <= (safe[3] - safe[1]) * 4, '中文墨跡超出安全區')
        for shot in field['shots']:
            step = shots[shot]
            box = tuple(v * 4 for v in safe)
            need(ImageChops.difference(frame('replay-zh', step).crop(box),
                                      frame('replay-control', step).crop(box)).getbbox() is not None,
                 '已驗欄位沒有中文畫面差異')
        f = {key: source[key] for key in ('candidate_id', 'shown', 'safe')}
        verified.append(f)
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save', 'baseline-v66-save'):
        saves = sorted((root / folder).glob('*.SAV'))
        need([p.name for p in saves] == ['COLONY03.SAV'] and sha(saves[0]) == batch['seed_sha256'],
             '正常取消路徑修改存檔')
    proof = json.loads((evidence / 'source/source-query.log.matches.json').read_text())
    need(proof['inputs_sha256'] == batch['inputs_sha256'] and proof['final_step'] == batch['end'] and
         proof['memory_sha256'] == batch['memory_sha256'], '來源未綁定正常GUI原版終點')
    need(len(proof['matches']) == 4, '四項原版查詢未齊')
    for m in proof['matches']:
        need(m['header'] == m['key'] and m['header'] in batch['headers'] and m['cx'] == 1 and
             m['code_bytes'] == 'f3a6' and m['original_cs_ip'] == '0E2D:0832', '原版查詢定位不同')
        f, rd = m['file_op'], m['read_op']
        need(f['Name'] == rd['Name'] == 'GAME.TXT' and not f['Failed'] and f['Op'] == 'read' and
             f['Step'] == rd['Step'] and f['Len'] == rd['Want'] == rd['Got'] == 512,
             '原版來源讀取不同')
    return {'result': 'PASS', 'grade': 'confirmed', 'inputs_sha256': batch['inputs_sha256'],
            'final_step': batch['end'], 'final_memory_sha256': batch['memory_sha256'],
            'verified_fields': verified, 'gui_images_exact': 26, 'original_checkpoints_equal': 26,
            'new_fields_only': True, 'unchanged_screens': 23, 'field_count': len(verified),
            'evidence_sha256': EVIDENCE_SHA,
            'scope': '僅正常港口取消、教學及本初始局勢F2至F10已量測欄位；三個城市名仍原文，未驗購入成功或其他局勢'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'reports', 'evidence'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game / name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版，不宣稱港口及報表驗收通過')
        return 77
    try:
        result = verify(a.game, a.reports, a.evidence)
    except (ValueError, OSError, AssertionError, KeyError, TypeError, IndexError) as e:
        print('FAIL：' + str(e))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
