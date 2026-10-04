#!/usr/bin/env python3
"""核對目標181正常建城後的資金不足BUY正文、原始查詢來源與建造面板。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal169_window import string_spans
from check_goal172_window import cp, dialog_spans


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--lookup-reports', type=Path, help='來源映射收據目錄；必須與reports完全相同')
    args = parser.parse_args()
    if not (args.game / 'OPENING.EXE').is_file():
        print('SKIP：缺合法原版，不宣稱BUY驗收通過')
        return 77
    root = args.reports
    gui, zh, control, negative = [load(root / name) for name in
                                  ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas')]
    same_state(zh, control, '中英完整原版狀態不同')
    for observed, name in ((gui, '正常GUI'), (negative, '缺圖集負例')):
        need(observed[0]['state'] == control[0]['state'] and observed[1] == control[1] and
             observed[0]['input_hashes'] == control[0]['input_hashes'] and
             observed[0]['opened'] == control[0]['opened'], name + '原版狀態、輸入或完整記憶體不同')
    for name, want in gui[0]['input_hashes'].items():
        need(hashlib.sha256((args.game / name).read_bytes()).hexdigest() == want, '原版輸入版本不符：' + name)
    inputs = (root / 'gui-colony.inputs.json').read_bytes()
    need(not json.loads(inputs).get('rejected'), '正常GUI有被拒絕輸入')
    shots = [(name, int(step)) for name, step in
             (line.split() for line in (root / 'gui-colony.shots').read_text().splitlines())]
    for _, step in shots:
        original = cp(control[0], step)
        for item in (zh, negative):
            now = cp(item[0], step)
            for key in ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256'):
                need(now[key] == original[key], f'{step}：原版{key}不同')
    key = 'GAME.TXT:@BUYME1:0x00002F09'
    sources = [e for e in zh[0]['events'] if e.get('candidate_id') == key and e.get('stage') == 'source']
    need(len(sources) == 1, 'BUY正文來源不唯一')
    source = sources[0]
    need(source['entry_ip'] == '0D21:00C6' and source['source_linear'] == 174976 and
         source['font_px'] == 30 and source['safe'] == [80, 119, 228, 142], 'BUY正文原始定位或字級不符')
    # 事件中的鍵是同文模板，不單獨證明原始段落。正常資金不足查詢實際為BUYME0。
    if args.lookup_reports:
        need(args.lookup_reports.resolve() == root.resolve(), '來源收據未綁定相同GUI目錄')
    proof_path = root / 'buy-source.log.matches.json'
    proof = json.loads(proof_path.read_text())
    need(proof['inputs_sha256'] == hashlib.sha256(inputs).hexdigest() and
         proof['final_step'] == control[0]['state']['steps'] and
         proof['memory_sha256'] == control[0]['state']['memory_sha256'], 'BUY來源觀測輸入或原版終點不同')
    need(len(proof['matches']) == 1, 'BUY來源匹配不唯一')
    match = proof['matches'][0]
    need(match['header'] == match['key'] == '@BUYME0' and match['cx'] == 1 and
         match['original_cs_ip'] == '0E2D:0832' and match['code_bytes'] == 'f3a6' and
         match['header_ram'] == 0x249DC and match['key_ram'] == 0x2AC5E and
         match['return_cs'] == 0x9B94 and match['return_ip'] == 0xD7 and
         match['step'] == 247889018, 'BUY原始標記／比較指令或定位不同')
    original = (args.game / 'GAME.TXT').read_bytes()
    marker = b'@BUYME0\r\n'
    need(original.count(marker) == 1 and original.index(marker) == 0x2E93 and
         hashlib.sha256(original[0x2EA8:0x2EA8+60]).hexdigest() ==
         '4d7b50c35be4f0b6c0f947e02da53f73aa4e3cdfcfd6c15bf755c4cb58660250', 'BUYME0原始標記或正文片段不同')
    read, file_op = match['read_op'], match['file_op']
    need(file_op['Name'] == read['Name'] == 'GAME.TXT' and
         file_op['Step'] == read['Step'] == 247878189 and file_op['Op'] == 'read' and
         file_op['Pos'] == 11776 and file_op['Len'] == read['Got'] == 512 and
         not file_op['Failed'] and read['Seg'] == 0x1C6A and read['Off'] == 0xE962 and
         file_op['Pos'] <= original.index(marker) < file_op['Pos'] + file_op['Len'],
         'BUY標記未與原始DOS讀取位置對應')
    step = dict(shots)['buy-response']
    need(any(cid == key and start <= step < end for shown, cid, start, end, safe in dialog_spans(zh[0])),
         'BUY正文在GUI取樣點未啟用')
    need(not any(e.get('candidate_id') == key and e.get('stage') == 'active' for e in negative[0]['events']),
         '缺圖集時BUY正文仍啟用')
    need(negative[0]['dialog_reason'] == 'font-mask-unavailable', '缺圖集回退原因不符')
    safe = tuple(v * 4 for v in source['safe'])
    g = Image.open(root / 'gui-colony.buy-response.png').convert('RGB')
    z, c, n = [Image.open(root / f'{name}.cp-{step}.png').convert('RGB') for name in
               ('replay-zh', 'replay-control', 'neg-noatlas')]
    need(ImageChops.difference(g.crop(safe), z.crop(safe)).getbbox() is None, 'BUY正常GUI與中文重播不同')
    need(ImageChops.difference(z.crop(safe), c.crop(safe)).getbbox() is not None, 'BUY正文未產生中文像素')
    need(ImageChops.difference(n.crop(safe), c.crop(safe)).getbbox() is None, '缺圖集時BUY正文未回原文')
    panel_step = dict(shots)['production-panel']
    fields = {}
    for shown, candidate_id, start, end, field in string_spans(zh[0]):
        if shown not in ('Docks', 'BUY', 'CHANGE') or not start <= panel_step < end:
            continue
        box = tuple(v * 4 for v in field)
        g = Image.open(root / 'gui-colony.production-panel.png').convert('RGB').crop(box)
        z, c = [Image.open(root / f'{name}.cp-{panel_step}.png').convert('RGB').crop(box)
                for name in ('replay-zh', 'replay-control')]
        need(ImageChops.difference(g, z).getbbox() is None, '建造面板GUI與重播不同')
        need(ImageChops.difference(z, c).getbbox() is not None, '建造面板欄位未產生中文像素')
        fields[shown] = field
    need(set(fields) == {'Docks', 'BUY', 'CHANGE'}, '建造面板三欄未全部驗到')
    measurements = json.loads((root / 'buy-layout-measurements.json').read_text())
    actual, stress, overflow = measurements
    need(actual['case'] == 'observed' and actual['selected_px'] == 30 and actual['fits'], '實際BUY譯文排版不符')
    need(stress['fits'] and 20 <= stress['selected_px'] <= 30, '長數值壓力排版未通過')
    need(not overflow['fits'] and overflow['selected_px'] == 0, '超界未回退')
    print(json.dumps({'result': 'PASS', 'inputs_sha256': hashlib.sha256(inputs).hexdigest(),
                      'final_state_sha256': zh[0]['state']['memory_sha256'],
                      'original_checkpoints': len(set(step for name, step in shots)),
                      'body_key': key, 'body_safe': source['safe'], 'font_px': source['font_px'],
                      'panel_fields': fields, 'layout': measurements,
                      'grade': 'confirmed',
                      'observed_template_source_aliases': {key: 'GAME.TXT:@BUYME0'},
                      'lookup_gui_inputs_sha256': proof['inputs_sha256'],
                      'lookup_original_step': proof['final_step'],
                      'lookup_original_memory_sha256': proof['memory_sha256'],
                      'evidence_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                      'original_marker': '@BUYME0', 'original_marker_file_offset': 0x2E93,
                      'original_body_file_offset': 0x2EA8,
                      'limit': '僅本次正常資金不足碼頭BUYME0正文；未驗全文搬運或可支付BUYME1選項',
                      'limits': '僅資金不足碼頭正文；購買選項、其他建物、武裝、多人口與捲動待驗'},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
