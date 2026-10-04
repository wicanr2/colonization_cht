#!/usr/bin/env python3
"""Docker 內限定驗收正常存讀檔標題、槽位清單及關框恢復。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal178_ship import ORIGINALS, equal_image, png_for, sha
from check_goal181_rename import field_active, need

INPUT_SHA = '5f22c2ecd4eb57e91a0048fd93c060876602e92d041bfead3f844bb5314b3943'
SEED_SHA = 'd3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
MEMORY_SHA = '6e446d715610ba27c698ec5e22f5e4bdcc0c0b11fce4b1ad50ea1336b1e7b578'
LAYOUT_SHA = '51569e36d08cc591a0537b644a3329fed860238e097ed4de846a37f902aa0497'
PROBE_SHA = '44a3c0e11f8fd58c4b62310f0cade6a72d7767402d6719feeba4c7465aab3ecb'
PROFILE = 'Discoverer Walter Raleigh of the English, Spring 1496'
SLOT_ID = 'STRING:save-slot+list'
SHOTS = {'load-slots': 36465000, 'load-highlight': 42075000,
         'loaded-notice': 48675000, 'loaded-world': 54945000,
         'game-menu': 61875000, 'save-slots': 68970000,
         'save-highlight': 74580000, 'save-success': 81510000,
         'save-dismissed': 88110000}
FIELDS = [
    ('GAME.TXT:0x00000826', 'Select Game To Load', [64, 66, 135, 74],
     32044927, 174228, 'GAME.TXT:@LOADGAME'),
    (SLOT_ID, ' '.join(['(EMPTY)'] * 3 + [PROFILE] + ['(EMPTY)'] * 6),
     [68, 74, 254, 136], 32059763, 174586, None),
    ('GAME.TXT:0x0000078E', 'Select Save Slot', [65, 64, 121, 73],
     63672368, 175146, 'GAME.TXT:@SAVEGAME'),
    (SLOT_ID, ' '.join(['(EMPTY)'] * 3 + [PROFILE] + ['(EMPTY)'] * 4),
     [69, 74, 255, 138], 63684592, 175504, None),
]


def verify(game, root, provenance, layout):
    for name, expected in ORIGINALS.items():
        need(sha(game / name) == expected, '原版指紋不同：' + name)
    need(sha(root / 'gui-colony.inputs.json') == INPUT_SHA, 'GUI 輸入不同')
    inputs = json.loads((root / 'gui-colony.inputs.json').read_text())
    need(not inputs.get('rejected') and inputs['end'] == 88600000, 'GUI 輸入被拒絕或終點不同')
    names = ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas', 'baseline-v55')
    loaded = {name: load(root / name) for name in names}
    control = loaded['replay-control'][0]
    need(control['control'] and control['state']['steps'] == inputs['end'], '缺原文控制終點')
    need(control['state']['memory_sha256'] == MEMORY_SHA, '原版終點與凍結收據不同')
    for name, value in loaded.items():
        if name != 'replay-control':
            same_state(value, loaded['replay-control'], name + '原版完整狀態不同')
        for key in ('state', 'input_hashes', 'opened'):
            need(value[0][key] == control[key], name + '：' + key + '不同')
        need(hashlib.sha256(value[1]['memory']).hexdigest() == MEMORY_SHA, 'RAM 指紋不同')
    for name, expected in control['input_hashes'].items():
        need(sha(game / name) == expected, '輸入指紋不同：' + name)
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (root / 'gui-colony.shots').read_text().splitlines()))
    need(shots == SHOTS, '正常 GUI 取樣點不同')
    indices = {name: {c['step']: c for c in loaded[name][0]['checkpoints'] if c['label'] != 'final'}
               for name in names if name != 'gui-colony'}
    need(all(set(cs) == set(shots.values()) for cs in indices.values()), '共同取樣點缺失')

    def frame(name, step):
        return Image.open(png_for(root, name, indices[name][step])).convert('RGB')

    for shot, step in shots.items():
        equal_image(root / f'gui-colony.{shot}.png',
                    png_for(root, 'replay-zh', indices['replay-zh'][step]))
        for name in indices:
            need(all(indices[name][step][k] == indices['replay-control'][step][k]
                     for k in ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256')),
                 '原版取樣狀態不同：' + name)
        need(ImageChops.difference(frame('neg-noatlas', step),
                                  frame('replay-control', step)).getbbox() is None,
             '缺圖集未完整回原文：' + shot)
        fresh, old = frame('replay-zh', step), frame('baseline-v55', step)
        ranges = ([FIELDS[0][2], FIELDS[1][2]] if shot.startswith('load-') else
                  [FIELDS[3][2]] if shot.startswith('save-') and shot in ('save-slots', 'save-highlight') else [])
        for safe in ranges:
            box = tuple(v * 4 for v in safe)
            need(ImageChops.difference(fresh.crop(box), old.crop(box)).getbbox() is not None,
                 '核准欄位未顯示新增中文：' + shot)
            fresh.paste(old.crop(box), box)
        need(ImageChops.difference(fresh, old).getbbox() is None, '核准欄位外或關框後不同：' + shot)
    zh = loaded['replay-zh'][0]
    sources = [e for e in zh['events'] if e.get('stage') == 'source' and
               e.get('candidate_id') in {f[0] for f in FIELDS}]
    need(len(sources) == len(FIELDS), '槽位或標題来源數量不同')
    verified = []
    for cid, shown, safe, step, address, source_id in FIELDS:
        hits = [e for e in sources if e['candidate_id'] == cid and e.get('shown') == shown]
        need(len(hits) == 1, '來源不唯一：' + cid)
        e = hits[0]
        need(e.get('safe') == safe and e.get('font_px') == 21 and e.get('step') == step and
             e.get('source_linear') == address and e.get('entry_ip') == '0D21:00C6', 'READY 欄位定位不同')
        if cid == SLOT_ID:
            expected = ['(EMPTY)'] * 3 + [PROFILE] + ['(EMPTY)'] * (6 if safe == FIELDS[1][2] else 4)
            need(e.get('items') == expected, '槽位列數或描述不同')
        f = {'candidate_id': cid, 'shown': shown, 'safe': safe}
        if source_id:
            f['source_ids'] = [source_id]
        verified.append(f)
    for shot in ('load-slots', 'load-highlight', 'save-slots', 'save-highlight'):
        step = shots[shot]
        title = FIELDS[0][0] if shot.startswith('load-') else FIELDS[2][0]
        need(field_active(zh, SLOT_ID, step) and field_active(zh, title, step), '槽位或標題未啟用')
    for shot in ('loaded-notice', 'loaded-world', 'game-menu', 'save-success', 'save-dismissed'):
        need(not any(field_active(zh, cid, shots[shot]) for cid in {f[0] for f in FIELDS}),
             '關框後仍啟用：' + shot)
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save', 'baseline-v55-save'):
        saves = sorted((root / folder).glob('*.SAV'))
        need([p.name for p in saves] == ['COLONY00.SAV', 'COLONY03.SAV'], '存檔檔名不同')
        for p in saves:
            need(p.stat().st_size == 24343 and sha(p) == SEED_SHA, '正常新舊存檔位元組不同')
    proof_path = provenance / 'source-query.log.matches.json'
    proof = json.loads(proof_path.read_text())
    need(sha(provenance / 'probe.go') == PROBE_SHA and sha(provenance / 'inputs.json') == INPUT_SHA,
         '來源探針或輸入不同')
    need(proof['inputs_sha256'] == INPUT_SHA and proof['final_step'] == inputs['end'] and
         proof['memory_sha256'] == MEMORY_SHA, '來源未綁定新正常 GUI 原版終點')
    state = json.loads((provenance / 'source-query.log.state.json').read_text())
    need(state['step'] == inputs['end'] and state['memory_sha256'] == MEMORY_SHA, '來源終點不同')
    need(len(proof['matches']) == 2, '兩個原版標題查詢未齊')
    for m, header, step, offset, position, read_step in zip(
            proof['matches'], ('@LOADGAME', '@SAVEGAME'), (31975372, 63586256),
            (173808, 174726), (2048, 1536), (31969125, 63567730)):
        need(m['header'] == m['key'] == header and m['step'] == step and m['key_ram'] == offset and
             m['header_ram'] == 149980 and m['cx'] == 1 and m['code_bytes'] == 'f3a6' and
             m['original_cs_ip'] == '0E2D:0832' and m['return_cs'] == 0x9320 and m['return_ip'] == 0xD7,
             '原版標題查詢定位不同')
        f, rd = m['file_op'], m['read_op']
        need(f['Name'] == rd['Name'] == 'GAME.TXT' and f['Step'] == rd['Step'] == read_step and
             f['Op'] == 'read' and f['Fn'] == 63 and not f['Failed'] and f['Pos'] == position and
             f['Len'] == rd['Want'] == rd['Got'] == 512 and rd['Seg'] == 0x1C6A and rd['Off'] == 0xE962,
             '原版標題檔案讀取不同')
    first = proof['slot_reads'][0]
    need(first['shown'] == '(EMPTY)' and first['linear'] == 124814 and first['step'] == 31985970 and
         first['cs_ip'] == '0E2D:07F9' and first['code'] == 'f2aef7d18b7e068bc7a80174', '空槽原版讀取不同')
    need(any(x['shown'] == PROFILE and x['linear'] == 174634 and x['step'] == 32003891 and
             x['cs_ip'] == '0E2D:1149' for x in proof['slot_reads']), '描述原版讀取缺失')
    raw = (game / 'VICEROY.EXE').read_bytes()
    fragment = raw[129660:129699]
    need(raw.count(b'(EMPTY)\0') == 1 and raw[129678:129686] == b'(EMPTY)\0' and
         loaded['replay-control'][1]['memory'][124796:124835] == fragment, '空槽片段與原版 RAM 不同')
    for name in ('COLONY00.SAV', 'COLONY03.SAV'):
        need(sha(provenance / 'scratch' / name) == SEED_SHA, '來源存檔不同')
    need(sha(layout) == LAYOUT_SHA, '正式圖集排版回歸不同')
    measured = json.loads(layout.read_text())
    need(measured['result'] == 'PASS' and [x['rows'] for x in measured['lists']] == [10, 8] and
         all(x['selected_px'] == 21 and x['cases'] == 160 and x['wide_ascii_name_fallback_px'] == 0
             for x in measured['lists']), '字級與超寬回退未驗證')
    return {'result': 'PASS', 'grade': 'confirmed', 'inputs_sha256': INPUT_SHA,
            'final_step': inputs['end'], 'final_memory_sha256': MEMORY_SHA,
            'verified_fields': verified, 'gui_images_exact': 9, 'original_checkpoints_equal': 9,
            'new_fields_only': True, 'closed_screens_exact': 5,
            'layout_sha256': LAYOUT_SHA, 'evidence_sha256': sha(proof_path),
            'scope': '僅正常讀 COLONY03、存空列 COLONY00、兩標題與 10／8 列槽位；未知列數、描述及錯誤提示仍待驗'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'reports', 'provenance', 'layout'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game / name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版，不宣稱槽位驗收通過')
        return 77
    try:
        result = verify(a.game, a.reports, a.provenance, a.layout)
    except (ValueError, OSError, AssertionError, KeyError, TypeError, IndexError) as e:
        print('FAIL：' + str(e))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
