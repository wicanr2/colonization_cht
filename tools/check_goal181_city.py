#!/usr/bin/env python3
"""目標181：正常讀入已驗殖民地存檔，核對進城三欄及要求的職業／議會欄位。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from check_goal134_window import load, same_state
from check_goal169_window import string_spans
from check_goal172_window import cp, dialog_spans


def need(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--require-jobs', action='store_true')
    p.add_argument('--require-more', action='store_true', help='驗證正常職業第二頁的裝備需求與停用列')
    p.add_argument('--require-fathers', action='store_true')
    p.add_argument('--require-buy', action='store_true')
    p.add_argument('--require-abandon', action='store_true', help='驗正常棄城正文、兩選項及取消結尾')
    p.add_argument('--lookup-reports', type=Path, help='來源映射；必須與reports相同且要求BUY或棄城')
    a = p.parse_args()
    if not (a.game / 'OPENING.EXE').is_file():
        print('SKIP：缺合法原版，不宣稱殖民地路徑驗收通過')
        return 77
    b = a.reports
    need(not a.lookup_reports or ((a.require_buy or a.require_abandon) and a.lookup_reports.resolve() == b.resolve()),
         '來源觀測未綁定相同收據')
    gui, zh, control, negative = [load(b / name) for name in
                                  ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas')]
    same_state(zh, control, '新存檔進城中英原版狀態不同')
    for observed, name in ((gui, '正常GUI'), (negative, '缺圖集負例')):
        need(observed[0]['state'] == control[0]['state'] and observed[1] == control[1] and
             observed[0]['input_hashes'] == control[0]['input_hashes'] and
             observed[0]['opened'] == control[0]['opened'], name + '原版終點、輸入或完整RAM不同')
    for name, expected in gui[0]['input_hashes'].items():
        need(hashlib.sha256((a.game / name).read_bytes()).hexdigest() == expected, '原版指紋不同：' + name)
    seed = 'c27b44665f1a229ca5257ac8f23b2f63dc025d5814aa5172742ffcd69939e647'
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save'):
        need(hashlib.sha256((b / folder / 'COLONY01.SAV').read_bytes()).hexdigest() == seed,
             '新正常存檔的檔名、位元組或雜湊不同')
    raw = (b / 'gui-colony.inputs.json').read_bytes()
    need(not json.loads(raw).get('rejected'), '正常GUI有被拒絕輸入')
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (b / 'gui-colony.shots').read_text().splitlines()))
    for step in shots.values():
        expected = cp(control[0], step)
        for observed in (zh, negative):
            now = cp(observed[0], step)
            need(all(now[k] == expected[k] for k in
                     ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256')), '原版取樣點不同')

    def compare(name, field):
        step = shots[name]
        box = tuple(v * 4 for v in field)
        g = Image.open(b / f'gui-colony.{name}.png').convert('RGB').crop(box)
        z, c = [Image.open(b / f'{prefix}.cp-{step}.png').convert('RGB').crop(box)
                for prefix in ('replay-zh', 'replay-control')]
        need(ImageChops.difference(g, z).getbbox() is None, name + '：GUI與中文重播安全區不同：' + str(field))
        need(ImageChops.difference(z, c).getbbox() is not None, name + '：安全區未顯示中文')
        return box

    verified_fields = []
    fields = {}
    step = shots['city-response']
    for shown, candidate_id, start, end, safe in string_spans(zh[0]):
        if not start <= step < end:
            continue
        if shown in ('Exit', 'No Ships In Port') or candidate_id == 'STRING:template:colony-title':
            compare('city-response', safe)
            verified_fields.append({'candidate_id': candidate_id, 'shown': shown, 'safe': safe})
            fields[shown] = safe
    need('Exit' in fields and 'No Ships In Port' in fields and len(fields) == 3, '正常進城三欄未全驗到')
    jobs = {}
    if a.require_jobs:
        step = shots['worker-jobs']
        for shown, key, start, end, safe in dialog_spans(zh[0]):
            if not start <= step < end:
                continue
            role = 'title' if 'Select a Profession' in shown else 'list' if 'Farmer =' in shown else None
            if role is None:
                continue
            box = compare('worker-jobs', safe)
            need(not any(cid == key and begin <= step < finish for _, cid, begin, finish, _ in
                         dialog_spans(negative[0])), '缺對話框圖集時工作選單仍啟用')
            n, c = [Image.open(b / f'{prefix}.cp-{step}.png').convert('RGB').crop(box)
                    for prefix in ('neg-noatlas', 'replay-control')]
            need(ImageChops.difference(n, c).getbbox() is None, '工作選單缺圖集未回原文')
            sources = [e for e in zh[0]['events'] if e.get('candidate_id') == key and
                       e.get('stage') == 'source' and e.get('safe') == safe]
            need(sources and all(e['entry_ip'] == '0D21:00C6' and e['font_px'] == 21 for e in sources),
                 '工作選單入口或逐欄字級不符既有規格')
            if role == 'list':
                need(len(sources[-1]['items']) == 17 and sources[-1]['items'][-1] == '(More)' and
                     'Lumberjack = 8/8 Lumber' in sources[-1]['items'] and
                     'Carpenter = 3 Hammers' in sources[-1]['items'], '正常工作清單項目或產量不同')
            jobs[role] = {'key': key, 'safe': safe, 'font_px': 21}
            verified_fields.append({'candidate_id': key, 'shown': shown, 'safe': safe})
        need(set(jobs) == {'title', 'list'}, '工作選單標題或17項清單未啟用')
    more = {}
    if a.require_more:
        step = shots['worker-more']
        expected_items = ['(More)', 'Colonist', 'Pioneer (100 Tools)', 'Soldier (50 Muskets)',
                          'Scout (50 Horses)', 'Dragoon (50 Muskets) (50 Horses)']
        expected = {
            'title': ('Select a Profession for Free Colonists(Fur Trapper):', [66, 69, 252, 78], 174814),
            'list': (' '.join(expected_items), [74, 79, 245, 128], 175172),
        }
        for shown, key, start, end, safe in dialog_spans(zh[0]):
            if not start <= step < end:
                continue
            role = next((role for role, field in expected.items() if field[0] == shown), None)
            if role is None:
                continue
            need(safe == expected[role][1], '職業第二頁安全區不同')
            box = compare('worker-more', safe)
            need(not any(cid == key and begin <= step < finish for _, cid, begin, finish, _ in
                         dialog_spans(negative[0])), '缺圖集時職業第二頁仍啟用')
            n, c = [Image.open(b / f'{prefix}.cp-{step}.png').convert('RGB').crop(box)
                    for prefix in ('neg-noatlas', 'replay-control')]
            need(ImageChops.difference(n, c).getbbox() is None, '職業第二頁缺圖集未回原文')
            sources = [e for e in zh[0]['events'] if e.get('candidate_id') == key and
                       e.get('stage') == 'source' and e.get('shown') == shown and e.get('safe') == safe and
                       e['step'] <= step]
            need(len(sources) == 1 and sources[0]['entry_ip'] == '0D21:00C6' and
                 sources[0]['font_px'] == 21 and sources[0]['source_linear'] == expected[role][2],
                 '職業第二頁入口、來源或欄位字級不同')
            if role == 'list':
                need(sources[0]['items'] == expected_items, '職業第二頁六項裝備需求不同')
                palette = control[1]['final.pal']
                colors = {index: tuple(round(v * 255 / 63) for v in palette[index * 3:index * 3 + 3])
                          for index in (8, 68)}
                for index in range(3, 6):
                    row_box = (74 * 4, (79 + index * 8) * 4, 245 * 4, (87 + index * 8) * 4)
                    for prefix in ('replay-zh', 'replay-control'):
                        pixels = set(Image.open(b / f'{prefix}.cp-{step}.png').convert('RGB').crop(row_box).getdata())
                        need(colors[8] in pixels and colors[68] not in pixels,
                             '士兵／斥候／龍騎兵未保留原版停用灰色：' + prefix)
            more[role] = {'key': key, 'safe': safe, 'font_px': 21}
            verified_fields.append({'candidate_id': key, 'shown': shown, 'safe': safe})
        need(set(more) == {'title', 'list'}, '職業第二頁標題或六項清單未顯示中文')
    fathers = {}
    if a.require_fathers:
        step = shots['end-turn-response']
        expected_items = ['Adam Smith (Trade Adviser)', 'Sieur De La Salle (Exploration Adviser)',
                          'Hernan Cortes (Military Adviser)', 'Pocahontas (Political Adviser)',
                          'Jean de Brebeuf (Religious Adviser)']
        for shown, key, start, end, safe in dialog_spans(zh[0]):
            if not start <= step < end:
                continue
            role = 'body' if key == 'GAME.TXT:@WHICHFREEDOM:0x00009532' else 'list' if 'Adam Smith (Trade Adviser)' in shown else None
            if role is None:
                continue
            box = compare('end-turn-response', safe)
            need(not any(cid == key and begin <= step < finish for _, cid, begin, finish, _ in
                         dialog_spans(negative[0])), '缺圖集時議會欄位仍啟用')
            n, c = [Image.open(b / f'{prefix}.cp-{step}.png').convert('RGB').crop(box)
                    for prefix in ('neg-noatlas', 'replay-control')]
            need(ImageChops.difference(n, c).getbbox() is None, '議會缺圖集未回原文')
            sources = [e for e in zh[0]['events'] if e.get('candidate_id') == key and
                       e.get('stage') == 'source' and e.get('safe') == safe]
            need(sources and all(e['entry_ip'] == '0D21:00C6' and e['font_px'] == 30 for e in sources),
                 '議會欄位入口或逐欄字級不同')
            need(safe == ([62, 46, 257, 90] if role == 'body' else [71, 92, 257, 152]),
                 '議會原版安全區不同')
            if role == 'list':
                need(sources[-1]['items'] == expected_items, '正常議會五項與已審選項不同')
            fathers[role] = {'key': key, 'safe': safe, 'font_px': 30}
            verified_fields.append({'candidate_id': key, 'shown': shown, 'safe': safe})
        need(set(fathers) == {'body', 'list'}, '議會正文或五項選擇未顯示中文')
    buy, source_proof, stock_titles = {}, {}, {}
    if a.require_buy:
        for shot, year in (('colony-stock', 1495), ('carpenter-stock', 1496)):
            at = shots[shot]
            expected = f'Jamestown.   Spring, {year}.  Gold: 1000$'
            titles = [(shown, cid, safe) for shown, cid, begin, finish, safe in string_spans(zh[0])
                      if begin <= at < finish and cid == 'STRING:template:colony-title' and shown == expected]
            need(len(titles) == 1, '正常年度殖民地標題未啟用：' + shot)
            shown, cid, safe = titles[0]
            need(safe == [89, 0, 231, 8], '正常年度標題安全區不同')
            compare(shot, safe)
            stock_titles[shot] = {'shown': shown, 'safe': safe}
            verified_fields.append({'candidate_id': cid, 'shown': shown, 'safe': safe})
        step = shots['payable-buy']
        body_key = 'GAME.TXT:@BUYME1:0x00002F09'
        list_key = body_key + '#2+list'
        for shown, key, start, end, safe in dialog_spans(zh[0]):
            if key not in (body_key, list_key) or not start <= step < end:
                continue
            role = 'body' if key == body_key else 'list'
            box = compare('payable-buy', safe)
            need(not any(cid == key and begin <= step < finish for _, cid, begin, finish, _ in
                         dialog_spans(negative[0])), '缺圖集時可支付BUY仍啟用')
            n, c = [Image.open(b / f'{prefix}.cp-{step}.png').convert('RGB').crop(box)
                    for prefix in ('neg-noatlas', 'replay-control')]
            need(ImageChops.difference(n, c).getbbox() is None, '可支付BUY缺圖集未回原文')
            sources = [e for e in zh[0]['events'] if e.get('candidate_id') == key and e.get('stage') == 'source']
            need(len(sources) == 1 and sources[0]['entry_ip'] == '0D21:00C6' and
                 sources[0]['font_px'] == 30 and sources[0]['safe'] == safe, '可支付BUY入口或逐欄字級不同')
            need(safe == ([80, 102, 220, 135] if role == 'body' else [85, 137, 140, 161]), '可支付BUY安全區不同')
            if role == 'body':
                need(shown == 'Cost to complete Wagon Train: 481$. Treasury: 1000$.' and
                     sources[0]['source_linear'] == 175114, '可支付BUY正文、價格或原始定位不同')
            else:
                need(sources[0]['items'] == ['Never mind.', 'Complete it.'] and
                     sources[0]['source_linear'] == 175472, '可支付BUY兩項選擇或原始定位不同')
            buy[role] = {'key': key, 'safe': safe, 'font_px': 30}
            verified_fields.append({'candidate_id': key, 'shown': shown, 'safe': safe})
        need(set(buy) == {'body', 'list'}, '可支付BUY正文或兩項選擇未顯示中文')
        proof_path = b / 'buy-source.log.matches.json'
        proof = json.loads(proof_path.read_bytes())
        need(proof['inputs_sha256'] == hashlib.sha256(raw).hexdigest() and
             proof['final_step'] == control[0]['state']['steps'] and
             proof['memory_sha256'] == control[0]['state']['memory_sha256'], '可支付BUY來源觀測輸入或完整終點不同')
        need(len(proof['matches']) == 1, '可支付BUY查詢不唯一')
        match = proof['matches'][0]
        need(match['header'] == match['key'] == '@BUYME1' and match['cx'] == 1 and
             match['original_cs_ip'] == '0E2D:0832' and match['code_bytes'] == 'f3a6' and
             match['header_ram'] == 149980 and match['key_ram'] == 175336 and
             match['return_cs'] == 0x97DC and match['return_ip'] == 0xD7 and
             match['step'] == 265986720, '可支付BUY原始查詢、指令或RAM參數不同')
        original = (a.game / 'GAME.TXT').read_bytes()
        marker = b'@BUYME1\r\n'
        need(original.count(marker) == 1 and original.index(marker) == 0x2EE8 and
             hashlib.sha256(original[0x2F09:0x2F09 + 89]).hexdigest() ==
             '1992fcfe57842da710b7f5163855308f5b1d043ea11b3648e08acdc1573bd984', '可支付BUY四行來源或原版標記不同')
        read, file_op = match['read_op'], match['file_op']
        need(file_op['Name'] == read['Name'] == 'GAME.TXT' and file_op['Step'] == read['Step'] == 265972187 and
             file_op['Op'] == 'read' and file_op['Pos'] == 11776 and file_op['Len'] == read['Got'] == 512 and
             not file_op['Failed'] and read['Seg'] == 0x1C6A and read['Off'] == 0xE962 and
             file_op['Pos'] <= original.index(marker) < file_op['Pos'] + file_op['Len'], '可支付BUY未與DOS讀取定位對應')
        source_proof = {'grade': 'confirmed', 'observed_template_source_aliases':
                        {body_key: 'GAME.TXT:@BUYME1', list_key: 'GAME.TXT:@BUYME1'},
                        'lookup_gui_inputs_sha256': proof['inputs_sha256'],
                        'lookup_original_step': proof['final_step'],
                        'lookup_original_memory_sha256': proof['memory_sha256'],
                        'evidence_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                        'limit': '僅本次可支付貨車的原版BUYME1查詢、讀取定位及已驗正文／兩選項；不宣稱逐位元組搬運已追完'}
    abandon = {}
    if a.require_abandon:
        at = shots['abandon-confirm']
        body_key = 'GAME.TXT:@ABANDON:0x00001994'
        list_key = 'GAME.TXT:@ABANDON2:0x00001A5B#2+list'
        for shown, key, start, end, safe in dialog_spans(zh[0]):
            if key not in (body_key, list_key) or not start <= at < end:
                continue
            role = 'body' if key == body_key else 'list'
            need(safe == ([65, 101, 254, 134] if role == 'body' else [70, 137, 193, 161]),
                 '棄城正文或兩選項安全區不同')
            box = compare('abandon-confirm', safe)
            need(not any(cid == key and begin <= at < finish for _, cid, begin, finish, _ in
                         dialog_spans(negative[0])), '缺圖集時棄城欄位仍啟用')
            n, c = [Image.open(b / f'{prefix}.cp-{at}.png').convert('RGB').crop(box)
                    for prefix in ('neg-noatlas', 'replay-control')]
            need(ImageChops.difference(n, c).getbbox() is None, '棄城缺圖集未完整回原文')
            sources = [e for e in zh[0]['events'] if e.get('candidate_id') == key and
                       e.get('stage') == 'source' and e.get('safe') == safe and e['step'] <= at]
            need(len(sources) == 1 and sources[0]['entry_ip'] == '0D21:00C6' and
                 sources[0]['font_px'] == 30, '棄城來源入口或欄位字級不同')
            if role == 'body':
                need(shown == 'Shall we indeed abandon our Jamestown colony, Your Excellency, forfeiting all of our hard work here?',
                     '棄城正文不是已取證的ABANDON；不得加1600年警告')
                need(sources[0]['source_linear'] == 174672, '棄城正文線性RAM來源不同')
            else:
                need(sources[0]['items'] == ["Yes, it is God's will.", 'Never! That would be folly.'],
                     '棄城兩項選擇不同')
            abandon[role] = {'key': key, 'safe': safe, 'font_px': 30, 'source_step': sources[0]['step']}
            verified_fields.append({'candidate_id': key, 'shown': shown, 'safe': safe})
        need(set(abandon) == {'body', 'list'}, '棄城正文或兩選項未顯示中文')
        after = shots['abandon-cancelled']
        need(not any(key in (body_key, list_key) and start <= after < end
                     for _, key, start, end, _ in dialog_spans(zh[0])), '取消後棄城覆蓋未撤銷')
        for shown, safe in fields.items():
            need(any(text == shown and begin <= after < finish and rectangle == safe
                     for text, _, begin, finish, rectangle in string_spans(zh[0])), '取消後殖民地欄位未恢復')
            compare('abandon-cancelled', safe)
        # 正常城市欄位之外，原棄城安全區必須完整回到原版像素。
        reference = Image.open(b / f'replay-control.cp-{after}.png').convert('RGB')
        for filename in ('gui-colony.abandon-cancelled.png', f'replay-zh.cp-{after}.png'):
            diff = ImageChops.difference(Image.open(b / filename).convert('RGB'), reference)
            draw = ImageDraw.Draw(diff)
            for safe in fields.values():
                x0, y0, x1, y1 = (v * 4 for v in safe)
                draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(0, 0, 0))
            for field in abandon.values():
                need(diff.crop(tuple(v * 4 for v in field['safe'])).getbbox() is None,
                     '取消後棄城區仍有非城市欄位差異：' + filename)
        proof_path = b / 'abandon-source.log.matches.json'
        proof = json.loads(proof_path.read_bytes())
        need(proof['inputs_sha256'] == hashlib.sha256(raw).hexdigest() and
             proof['final_step'] == control[0]['state']['steps'] and
             proof['memory_sha256'] == control[0]['state']['memory_sha256'], '棄城來源觀測輸入或完整終點不同')
        need(len(proof['matches']) == 1, '棄城來源查詢不唯一')
        match = proof['matches'][0]
        need(match['header'] == match['key'] == '@ABANDON' and match['cx'] == 1 and
             match['original_cs_ip'] == '0E2D:0832' and match['code_bytes'] == 'f3a6' and
             match['header_ram'] == 149980 and match['key_ram'] == 174894 and
             match['return_cs'] == 0x9320 and match['return_ip'] == 0xD7 and
             match['step'] < abandon['body']['source_step'] < at, '棄城原始查詢、定位或時序不同')
        original = (a.game / 'GAME.TXT').read_bytes()
        marker = b'@ABANDON\r\n'
        need(original.count(marker) == 1 and original.index(marker) == 6514 and
             hashlib.sha256(original[6548:6548 + 158]).hexdigest() ==
             'd9cf0aa7ce8612c94a9da8b0f4b02b74f6319cabb1cb0803bc304a421ae36f67', '棄城原始段落或兩選項片段不同')
        read, file_op = match['read_op'], match['file_op']
        need(file_op['Name'] == read['Name'] == 'GAME.TXT' and file_op['Step'] == read['Step'] and
             file_op['Step'] < match['step'] and file_op['Op'] == 'read' and
             file_op['Pos'] == 6144 and file_op['Len'] == read['Got'] == 512 and not file_op['Failed'] and
             read['Seg'] == 0x1C6A and read['Off'] == 0xE962 and
             file_op['Pos'] <= original.index(marker) < file_op['Pos'] + file_op['Len'], '棄城查詢未與原始DOS讀取定位對應')
        source_proof = {'grade': 'confirmed', 'observed_template_source_aliases':
                        {body_key: 'GAME.TXT:@ABANDON', list_key: 'GAME.TXT:@ABANDON'},
                        'lookup_gui_inputs_sha256': proof['inputs_sha256'],
                        'lookup_original_step': proof['final_step'],
                        'lookup_original_memory_sha256': proof['memory_sha256'],
                        'evidence_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                        'limit': '僅本次ABANDON查詢、來源片段、已驗正文／兩選項及正常取消；不宣稱ABANDON2或棄城結果已驗'}
    print(json.dumps({'result': 'PASS', 'inputs_sha256': hashlib.sha256(raw).hexdigest(),
                      'initial_save_sha256': seed, 'original_checkpoints': len(set(shots.values())),
                      'final_memory_sha256': control[0]['state']['memory_sha256'],
                      'final_step': control[0]['state']['steps'], 'verified_fields': verified_fields,
                      'city_fields': fields, 'jobs': jobs, 'more': more, 'fathers': fathers, 'buy': buy,
                      'abandon': abandon,
                      'stock_titles': stock_titles, **source_proof,
                      'limits': '僅本次要求的正常GUI欄位；未要求的職業頁、武裝操作與其他局勢仍待驗，不推定生產或價格公式'},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
