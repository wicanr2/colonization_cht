#!/usr/bin/env python3
"""Docker 內驗正常城市改名提示、輸入標籤、編輯與取消。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal178_ship import ORIGINALS, equal_image, png_for, sha

INPUT_SHA = '3857d61dc51181fa36874b2729fc4a197ef94279bf26241efdb807f15f282cf1'
SEED_SHA = 'd3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
FIELDS = {
    'body': ('GAME.TXT:0x00000F5C', 'What shall we rename this colony?', [61, 86, 219, 98], 30, 175166),
    'label': ('STRING:input-label', 'Name: Jamestown_', [61, 102, 89, 113], 29, 175436),
}
SHOTS = {'load-slots': 36465000, 'loaded-notice': 43065000, 'loaded-world': 49335000,
         'city-reloaded': 55935000, 'rename-prompt': 62865000, 'rename-edited': 69300000,
         'rename-retyped': 75570000, 'rename-cancelled': 81675000, 'world-restored': 88770000}
LAYOUT_SHA = {
    'body': '3c6a049c882eda8d0768afa0b61237b56bea045fb0c428863985be9b3c1bd6d3',
    'label': 'b6a8734d1b0fa0a43c5835f6aee9292da31278afc2689dbe284b66cbd624c428',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def field_active(report, cid, step):
    """兩欄都由通用對話框印字，但 input-label 的鍵使用 STRING 前綴。"""
    active = False
    for event in report['events']:
        if event.get('candidate_id') != cid or event['step'] > step:
            continue
        if event.get('stage') == 'active':
            active = True
        elif event.get('stage') == 'expired':
            active = False
    return active


def verify(game, root, provenance, layout):
    for name, expected in ORIGINALS.items():
        need(sha(game / name) == expected, '原版指紋不同：' + name)
    need(sha(root / 'gui-colony.inputs.json') == INPUT_SHA, 'GUI 輸入不同')
    inputs = json.loads((root / 'gui-colony.inputs.json').read_text())
    need(not inputs.get('rejected') and inputs['end'] == 89000000, '輸入被拒絕或終點不同')
    loaded = {name: load(root / name) for name in ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas')}
    control = loaded['replay-control'][0]
    need(control['control'] and control['state']['steps'] == 89000000, '缺原文控制終點')
    for name, value in loaded.items():
        if name != 'replay-control':
            same_state(value, loaded['replay-control'], name + '完整原版不同')
        for key in ('state', 'input_hashes', 'opened'):
            need(value[0][key] == control[key], name + '：' + key + '不同')
        need(hashlib.sha256(value[1]['memory']).hexdigest() == value[0]['state']['memory_sha256'], 'RAM 指紋不同')
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
        equal_image(root / f'gui-colony.{shot}.png', png_for(root, 'replay-zh', indices['replay-zh'][step]))
        for name in ('replay-zh', 'neg-noatlas'):
            need(all(indices[name][step][k] == indices['replay-control'][step][k]
                     for k in ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256')), '原版取樣狀態不同')
        need(ImageChops.difference(frame('neg-noatlas', step), frame('replay-control', step)).getbbox() is None,
             '缺圖集未完整回原文：' + shot)
    zh = loaded['replay-zh'][0]
    fields, measurements = [], {}
    for role, (cid, shown, safe, size, source_linear) in FIELDS.items():
        sources = [e for e in zh['events'] if e.get('stage') == 'source' and e.get('candidate_id') == cid]
        need(len(sources) == 1, '改名欄位來源不唯一：' + role)
        source = sources[0]
        need(source.get('shown') == shown and source.get('safe') == safe and source.get('font_px') == size
             and source.get('source_linear') == source_linear and source.get('entry_ip') == '0D21:00C6',
             '欄位與 READY 定位不同：' + role)
        path = layout / (role + '-measurement.json')
        need(sha(path) == LAYOUT_SHA[role], 'READY 量測指紋不同：' + role)
        m = json.loads(path.read_text())
        need(m['original_cap_h'] == 8 and m['pitch'] == 12 and m['actual']['selected_px'] == size
             and m['actual']['fits'] and not m['overflow']['fits'] and m['overflow']['selected_px'] == 0,
             '字高／字級或超界回退不同：' + role)
        rect = m['safe']
        need([rect['Min']['X'], rect['Min']['Y'], rect['Max']['X'], rect['Max']['Y']] == safe,
             '量測安全矩形不同')
        ink = m['actual']['ink']
        need(0 <= ink['Min']['X'] < ink['Max']['X'] <= (safe[2] - safe[0]) * 4
             and 0 <= ink['Min']['Y'] < ink['Max']['Y'] <= (safe[3] - safe[1]) * 4, '墨跡超界')
        need([c['candidate_px'] for c in m['candidates']] == list(range(30, 19, -1)), '候選字級未量測')
        if role == 'label':
            need(not m['candidates'][0]['fits'] and m['candidates'][1]['fits'], '標籤未按實際欄寬縮字')
        box = tuple(v * 4 for v in safe)
        for shot in ('rename-prompt', 'rename-edited', 'rename-retyped'):
            step = shots[shot]
            need(field_active(zh, cid, step),
                 '改名編輯時欄位未啟用：' + role)
            need(ImageChops.difference(frame('replay-zh', step).crop(box),
                                      frame('replay-control', step).crop(box)).getbbox() is not None,
                 '欄位未顯示中文：' + role)
            border = tuple((safe[i] + (-2 if i < 2 else 2)) * 4 for i in range(4))
            original, translated = frame('replay-control', step), frame('replay-zh', step)
            translated.paste(original.crop(box), box)
            need(ImageChops.difference(translated.crop(border), original.crop(border)).getbbox() is None,
                 '中文超出核准安全區：' + role)
        for shot in ('rename-cancelled', 'world-restored'):
            step = shots[shot]
            need(not field_active(zh, cid, step),
                 '取消後仍啟用改名欄位')
            need(ImageChops.difference(frame('replay-zh', step).crop(box),
                                      frame('replay-control', step).crop(box)).getbbox() is None, '取消後殘字')
        field = {'candidate_id': cid, 'shown': shown, 'safe': safe}
        if role == 'body':
            field['source_ids'] = ['GAME.TXT:@RENAMECOLONY']
        fields.append(field)
        measurements[role] = sha(path)
    name_box = tuple(v * 4 for v in (90, 102, 156, 114))
    for shot in ('rename-prompt', 'rename-edited', 'rename-retyped'):
        step = shots[shot]
        need(ImageChops.difference(frame('replay-zh', step).crop(name_box),
                                  frame('replay-control', step).crop(name_box)).getbbox() is None,
             '玩家姓名被中文覆蓋')
    need(ImageChops.difference(frame('replay-control', shots['rename-prompt']).crop(name_box),
                              frame('replay-control', shots['rename-edited']).crop(name_box)).getbbox() is not None,
         '正常 Backspace 未編輯姓名')
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save'):
        saves = sorted((root / folder).glob('*.SAV'))
        need([p.name for p in saves] == ['COLONY03.SAV'] and sha(saves[0]) == SEED_SHA, '原始存檔被修改')
    proof_path = provenance / 'source-query.log.matches.json'
    proof = json.loads(proof_path.read_text())
    need(proof['inputs_sha256'] == INPUT_SHA and sha(provenance / 'inputs.json') == INPUT_SHA
         and proof['final_step'] == control['state']['steps']
         and proof['memory_sha256'] == control['state']['memory_sha256'], '來源未綁定正常 GUI 終點')
    state = json.loads((provenance / 'source-query.log.state.json').read_text())
    need(state['step'] == control['state']['steps'] and state['memory_sha256'] == control['state']['memory_sha256'],
         '來源探針完整 RAM 雜湊不同')
    need(sha(provenance / 'probe.go') == sha(Path(__file__).with_name('probe_goal181_buy_sources.go')),
         '來源探針程式不同')
    need(len(proof['matches']) == 1, '改名查詢不唯一')
    m = proof['matches'][0]
    need(m['header'] == m['key'] == '@RENAMECOLONY' and m['step'] == 57470473 and m['cx'] == 1
         and m['original_cs_ip'] == '0E2D:0832' and m['code_bytes'] == 'f3a6'
         and m['header_ram'] == 149980 and m['key_ram'] == 175388
         and m['return_cs'] == 0x9320 and m['return_ip'] == 0xD7, '原始查詢定位不同')
    raw = (game / 'GAME.TXT').read_bytes()
    need(raw.count(b'@RENAMECOLONY\r\n') == 1 and raw.index(b'@RENAMECOLONY\r\n') == 3917
         and hashlib.sha256(raw[3917:3978]).hexdigest() ==
         'da21c1451e15435126a4ab5c6eb15a1413b92a08531fbb09cd0deb3fbd19158c', '原始兩行段落不同')
    f, read = m['file_op'], m['read_op']
    need(f['Name'] == read['Name'] == 'GAME.TXT' and f['Step'] == read['Step'] == 57451427
         and f['Op'] == 'read' and f['Fn'] == 63 and f['Handle'] == read['Handle'] == 6
         and f['Pos'] == 3584 and f['Len'] == read['Want'] == read['Got'] == 512 and not f['Failed']
         and read['Seg'] == 0x1C6A and read['Off'] == 0xE962, '來源檔案讀取定位不同')
    return {'result': 'PASS', 'grade': 'confirmed', 'inputs_sha256': INPUT_SHA,
            'final_step': control['state']['steps'], 'final_memory_sha256': control['state']['memory_sha256'],
            'verified_fields': fields, 'gui_images_exact': 9, 'original_checkpoints_equal': 9,
            'layout_sha256': measurements, 'evidence_sha256': sha(proof_path),
            'scope': '僅本次正常改名兩欄、英文姓名編輯與取消；未驗接受改名或其他輸入長度'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'reports', 'provenance', 'layout'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game / name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版，不宣稱改名驗收通過')
        return 77
    try:
        result = verify(a.game, a.reports, a.provenance, a.layout)
    except (ValueError, OSError, AssertionError, KeyError, TypeError) as e:
        print('FAIL：' + str(e))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
