#!/usr/bin/env python3
"""Docker 內驗正常另存檔、SAVEGOOD 中文提示與正常關閉。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal178_ship import ORIGINALS, equal_image, png_for, sha
from check_goal181_rename import field_active, need

INPUT_SHA = '4fa9a6d33dfc54ed7c17ebb11de0bafbf541e4f6a0e713cb0d877e4c2f511d0f'
SEED_SHA = 'd3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
SAVE_SHA = '1dfece16afb982dfa6ed73b19b53e9f7784c3d6179793fb121ee6e1a6ca7dc69'
LAYOUT_SHA = 'c95347164caec255d6755b60d16b72dd6d51212ce5d38661deb8b4ef05dfc82b'
CASES_SHA = '6b3112c0c8544420cc08a58f36dddf8ec9f445628d9e471d6117643d3671807a'
PROBE_SHA = '1ea111025230eed1e0658c9c9ad62e1a921e960e9c20bafdf2eb703ff4085a8a'
CID = 'GAME.TXT:0x000007B9'
SHOWN = 'Discoverer Walter Raleigh of the English (Spring 1496) saved as COLONY00.SAV.'
SAFE = [65, 82, 254, 115]
SHOTS = {'load-slots': 36465000, 'loaded-notice': 43065000,
         'loaded-world': 49335000, 'game-menu': 56265000,
         'save-slots': 63360000, 'save-success': 70290000,
         'save-dismissed': 76890000}


def verify(game, root, provenance, layout, cases):
    for name, expected in ORIGINALS.items():
        need(sha(game / name) == expected, '原版指紋不同：' + name)
    need(sha(root / 'gui-colony.inputs.json') == INPUT_SHA, 'GUI 輸入不同')
    inputs = json.loads((root / 'gui-colony.inputs.json').read_text())
    need(not inputs.get('rejected') and inputs['end'] == 77200000, '輸入被拒絕或終點不同')
    loaded = {name: load(root / name) for name in
              ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas')}
    control = loaded['replay-control'][0]
    need(control['control'] and control['state']['steps'] == 77200000, '缺原文控制終點')
    for name, value in loaded.items():
        if name != 'replay-control':
            same_state(value, loaded['replay-control'], name + '完整原版不同')
        for key in ('state', 'input_hashes', 'opened'):
            need(value[0][key] == control[key], name + '：' + key + '不同')
        need(hashlib.sha256(value[1]['memory']).hexdigest() ==
             value[0]['state']['memory_sha256'], 'RAM 指紋不同')
    for name, expected in control['input_hashes'].items():
        need(sha(game / name) == expected, '輸入指紋不同：' + name)
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (root / 'gui-colony.shots').read_text().splitlines()))
    need(shots == SHOTS, '正常操作取樣點不同')
    indices = {name: {c['step']: c for c in loaded[name][0]['checkpoints'] if c['label'] != 'final'}
               for name in ('replay-zh', 'replay-control', 'neg-noatlas')}
    need(all(set(cs) == set(shots.values()) for cs in indices.values()), '共同原版取樣點缺失')

    def frame(name, step):
        return Image.open(png_for(root, name, indices[name][step])).convert('RGB')

    for shot, step in shots.items():
        equal_image(root / f'gui-colony.{shot}.png',
                    png_for(root, 'replay-zh', indices['replay-zh'][step]))
        for name in ('replay-zh', 'neg-noatlas'):
            need(all(indices[name][step][k] == indices['replay-control'][step][k]
                     for k in ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256')),
                 '原版取樣狀態不同')
        need(ImageChops.difference(frame('neg-noatlas', step),
                                  frame('replay-control', step)).getbbox() is None,
             '缺圖集未完整回原文：' + shot)
    zh = loaded['replay-zh'][0]
    sources = [e for e in zh['events'] if e.get('stage') == 'source' and e.get('candidate_id') == CID]
    need(len(sources) == 1, '存檔提示來源不唯一')
    source = sources[0]
    need(source.get('shown') == SHOWN and source.get('safe') == SAFE
         and source.get('font_px') == 30 and source.get('source_linear') == 175134
         and source.get('entry_ip') == '0D21:00C6' and source.get('step') == 64948187,
         '欄位與 READY 定位不同')
    box = tuple(v * 4 for v in SAFE)
    step = shots['save-success']
    need(field_active(zh, CID, step), '正常存檔提示未啟用')
    original, translated = frame('replay-control', step), frame('replay-zh', step)
    need(ImageChops.difference(translated.crop(box), original.crop(box)).getbbox() is not None,
         '提示未顯示中文')
    translated.paste(original.crop(box), box)
    border = tuple((SAFE[i] + (-2 if i < 2 else 2)) * 4 for i in range(4))
    need(ImageChops.difference(translated.crop(border), original.crop(border)).getbbox() is None,
         '中文超出核准安全區')
    restored_diffs = []
    for shot in ('loaded-world', 'save-dismissed'):
        step = shots[shot]
        need(not field_active(zh, CID, step), '存檔提示仍啟用')
        restored_diffs.append(ImageChops.difference(frame('replay-zh', step).crop(box),
                                                    frame('replay-control', step).crop(box)))
    # 安全矩形右緣包含既有中文狀態欄；關框後須恢復開框前的相同差異。
    need(ImageChops.difference(*restored_diffs).getbbox() is None, '提示區未恢復原有中文狀態欄')
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save'):
        saves = sorted((root / folder).glob('*.SAV'))
        need([p.name for p in saves] == ['COLONY00.SAV', 'COLONY03.SAV'], '存檔檔名不同')
        need(sha(saves[0]) == SAVE_SHA and saves[0].stat().st_size == 24343, '新存檔不同')
        need(sha(saves[1]) == SEED_SHA, '原始存檔被修改')
        need(saves[0].read_bytes() == (root / 'scratch/COLONY00.SAV').read_bytes(), '新存檔位元組不同')
    proof_path = provenance / 'source-query.log.matches.json'
    proof = json.loads(proof_path.read_text())
    need(proof['inputs_sha256'] == INPUT_SHA and sha(provenance / 'inputs.json') == INPUT_SHA
         and proof['final_step'] == control['state']['steps']
         and proof['memory_sha256'] == control['state']['memory_sha256'], '來源未綁定正常 GUI 終點')
    state = json.loads((provenance / 'source-query.log.state.json').read_text())
    need(state['step'] == control['state']['steps']
         and state['memory_sha256'] == control['state']['memory_sha256'], '來源終點 RAM 雜湊不同')
    need(sha(provenance / 'probe.go') == PROBE_SHA, '來源探針程式不同')
    need(len(proof['matches']) == 1, '存檔提示查詢不唯一')
    m = proof['matches'][0]
    need(m['header'] == m['key'] == '@SAVEGOOD' and m['step'] == 64895084 and m['cx'] == 1
         and m['original_cs_ip'] == '0E2D:0832' and m['code_bytes'] == 'f3a6'
         and m['header_ram'] == 149980 and m['key_ram'] == 175356
         and m['return_cs'] == 0x9320 and m['return_ip'] == 0xD7, '原始查詢定位不同')
    raw = (game / 'GAME.TXT').read_bytes()
    need(raw.count(b'@SAVEGOOD\r\n') == 1 and raw.index(b'@SAVEGOOD\r\n') == 1954
         and hashlib.sha256(raw[1977:2004]).hexdigest() ==
         '68950b5338b58ed3b14b56bcc94333d8794be024547b7be88d4323e44ed64284', '原始段落不同')
    f, read = m['file_op'], m['read_op']
    need(f['Name'] == read['Name'] == 'GAME.TXT' and f['Step'] == read['Step'] == 64873669
         and f['Op'] == 'read' and f['Fn'] == 63 and f['Handle'] == read['Handle'] == 6
         and f['Pos'] == 1536 and f['Len'] == read['Want'] == read['Got'] == 512 and not f['Failed']
         and read['Seg'] == 0x1C6A and read['Off'] == 0xE962, '來源檔案讀取定位不同')
    creates = [x for x in proof['save_file_ops'] if x['Op'] == 'create']
    need(len(creates) == 1 and creates[0]['Name'] == 'COLONY00.SAV'
         and creates[0]['Step'] == 64761371 and creates[0]['Fn'] == 60
         and not creates[0]['Failed'], '正常建立新檔不同')
    need(any(x['Op'] == 'open' and x['Name'] == 'COLONY00.SAV'
             and x['Step'] == 64761411 and x['Fn'] == 61 and not x['Failed']
             for x in proof['save_file_ops']), '正常開啟新檔不同')
    need(all(x['Name'] == 'COLONY00.SAV' and x['N'] > 0 for x in proof['writes'])
         and sum(x['N'] for x in proof['writes']) == 24343, 'DOS 寫入檔名／長度不同')
    for name, expected in (('COLONY03.SAV', SEED_SHA), ('COLONY00.SAV', SAVE_SHA)):
        need(sha(provenance / 'scratch' / name) == expected, '來源重播存檔不同')
    path = layout / 'save-measurement.json'
    need(sha(path) == LAYOUT_SHA, 'READY 量測指紋不同')
    measurement = json.loads(path.read_text())
    need(measurement['key'] == CID and measurement['shown'] == SHOWN
         and measurement['original_cap_h'] == 9 and measurement['pitch'] == 10
         and measurement['actual']['selected_px'] == 30 and measurement['actual']['fits']
         and not measurement['overflow']['fits'] and measurement['overflow']['selected_px'] == 0,
         '字高／字級或超界回退不同')
    rect = measurement['safe']
    need([rect['Min']['X'], rect['Min']['Y'], rect['Max']['X'], rect['Max']['Y']] == SAFE,
         '量測安全矩形不同')
    ink = measurement['actual']['ink']
    need(0 <= ink['Min']['X'] < ink['Max']['X'] <= 756
         and 0 <= ink['Min']['Y'] < ink['Max']['Y'] <= 132, '墨跡超界')
    need([c['candidate_px'] for c in measurement['candidates']] == list(range(30, 19, -1))
         and measurement['candidates'][0]['cjk_ink_height'] == 28, '候選字級未量測')
    need(sha(cases) == CASES_SHA, '描述／檔名排版回歸不同')
    return {'result': 'PASS', 'grade': 'confirmed', 'inputs_sha256': INPUT_SHA,
            'final_step': control['state']['steps'], 'final_memory_sha256': control['state']['memory_sha256'],
            'verified_fields': [{'candidate_id': CID, 'shown': SHOWN, 'safe': SAFE,
                                 'source_ids': ['GAME.TXT:@SAVEGOOD']}],
            'gui_images_exact': 7, 'original_checkpoints_equal': 7,
            'layout_sha256': LAYOUT_SHA, 'matcher_layout_sha256': CASES_SHA,
            'evidence_sha256': sha(proof_path), 'save_sha256': SAVE_SHA,
            'scope': '僅正常讀 COLONY03、另存空列 COLONY00、SAVEGOOD 提示及關閉；其他存檔錯誤仍待驗'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'reports', 'provenance', 'layout', 'cases'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game / name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版，不宣稱存檔提示驗收通過')
        return 77
    try:
        result = verify(a.game, a.reports, a.provenance, a.layout, a.cases)
    except (ValueError, OSError, AssertionError, KeyError, TypeError) as e:
        print('FAIL：' + str(e))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
