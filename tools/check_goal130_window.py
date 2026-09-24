#!/usr/bin/env python3
"""獨立驗證首張字幕的真視窗中／英文同輸入與精確 A 版像素。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


KEY = 'GAME.TXT:0x000153CC'
PRE_SHA = 'd8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab'
AFTER_SHA = 'b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772'
PALETTE_SHA = '92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b'
SAFE = (48, 108, 1228, 168)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def color(palette, index):
    p = palette[index * 3:index * 3 + 3]
    return tuple((v << 2) | (v >> 4) for v in p)


def check_pair(root, end, expect_caption):
    suffix = '120m' if end == 120000000 else str(end)
    live, control = (json.loads((root / f'{variant}-{suffix}.json').read_text())
                     for variant in ('live', 'control'))
    need(live['state'] == control['state'] and live['opened'] == control['opened'] and
         live['input_hashes'] == control['input_hashes'], f'{end}：原版狀態或開檔不同')
    need(live['state']['steps'] == end and len(live['frames']) == len(control['frames']),
         f'{end}：重播終點或畫格數不同')
    for extension in ('memory', 'final.idx', 'final.pal'):
        need((root / f'live-{suffix}.{extension}').read_bytes() ==
             (root / f'control-{suffix}.{extension}').read_bytes(),
             f'{end}：原版 {extension} 不同')
    indexed = (root / f'control-{suffix}.final.idx').read_bytes()
    palette = (root / f'control-{suffix}.final.pal').read_bytes()
    a, b = (Image.open(root / f'{variant}-{suffix}.final.png').convert('RGB')
            for variant in ('live', 'control'))
    need(a.size == b.size == (1280, 800), f'{end}：視窗尺寸不同')
    records = [next((line for line in frame['lines'] if line['candidate_id'] == KEY), None)
               for frame in live['frames']]
    need(all(record is not None for record in records), f'{end}：缺字幕逐幀紀錄')
    if not expect_caption:
        expired = [event['step'] for event in live['events']
                   if event.get('candidate_id') == KEY and event.get('stage') == 'expired']
        need(records[-1]['applied'] is False and
             (not expired or not any(record['applied'] for frame, record in
                                     zip(live['frames'], records) if frame['step'] >= expired[-1])) and
             ImageChops.difference(a, b).getbbox() is None,
             f'{end}：離頁或穩定後字幕殘留')
        return {'end': end, 'caption_at_end': False, 'state_sha256': live['state']['memory_sha256']}
    need(records[-1]['applied'] and records[-1]['reason'] == 'applied' and
         live['checkpoints'][-1]['lines'][-1]['applied'] is True and
         sum(record['applied'] for record in records) > 0,
         f'{end}：字幕未於正式視窗顯示')
    waiting = [record for record in records if record['reason'] == 'waiting-screen']
    need(len(waiting) == 7 and not any(record['applied'] for record in waiting),
         f'{end}：真 VGA 同步前未保留英文')
    events = [e for e in live['events'] if e.get('candidate_id') == KEY]
    need(len(events) == 2 and events[0]['stage'] == 'source' and
         events[0]['entry_ip'] == '0D21:00C6' and events[0]['source_linear'] == 0x2a560 and
         events[1]['stage'] == 'active' and events[1]['read_count'] == 122 and
         events[1]['changed_pixels'] == 1040 and events[1]['bbox'] == [16, 30, 303, 39],
         f'{end}：缺當次印字／畫布證據')
    need(sha(indexed) == AFTER_SHA and sha(palette) == PALETTE_SHA,
         f'{end}：正式原版影像或色盤錯誤')
    without = a.copy()
    without.paste(b.crop(SAFE), SAFE)
    need(ImageChops.difference(without, b).getbbox() is None and
         ImageChops.difference(a, b).getbbox() is not None,
         f'{end}：安全區外改像素或未顯示中文')
    return {'end': end, 'caption_at_end': True, 'state_sha256': live['state']['memory_sha256'],
            'live': a, 'control': b, 'indexed': indexed, 'palette': palette}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--preprint', type=Path, required=True)
    p.add_argument('--mask', type=Path, required=True)
    p.add_argument('--legacy', type=Path, required=True,
                   help='既有真視窗完整玩家路徑收據；核對原十七欄逐幀結果')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not args.preprint.is_file() or not args.mask.is_file() or not args.legacy.is_file():
        print('SKIP：缺合法原版印前畫布、本機字模或既有真視窗收據')
        return 77
    before = args.preprint.read_bytes()
    need(len(before) == 64000 and sha(before) == PRE_SHA, '印前原版畫布不符')
    mask = json.loads(args.mask.read_text())
    alpha = base64.b64decode(mask['alpha'], validate=True)
    need(mask['candidate_id'] == KEY and mask['font_size'] == 38 and
         (mask['width'], mask['height']) == (430, 35) and len(alpha) == 430*35,
         'A 版字模綁定或形狀錯誤')
    out = [check_pair(args.reports, 82000000, True),
           check_pair(args.reports, 86000000, False),
           check_pair(args.reports, 120000000, False)]
    legacy = json.loads(args.legacy.read_text())
    current = json.loads((args.reports / 'live-120m.json').read_text())
    need(len(legacy['frames']) >= len(current['frames']) and
         all(old['step'] == new['step'] and old['lines'] == new['lines'][:-1]
             for old, new in zip(legacy['frames'], current['frames'])) and
         legacy['events'] == [event for event in current['events']
                              if event.get('candidate_id') != KEY],
         '既有十七欄逐幀結果或事件退步')
    missing = json.loads((args.reports / 'missing-font-82000000.json').read_text())
    control = json.loads((args.reports / 'control-82000000.json').read_text())
    need(missing['state'] == control['state'] and missing['opened'] == control['opened'] and
         missing['checkpoints'][-1]['lines'][-1]['reason'] == 'font-mask-unavailable' and
         missing['checkpoints'][-1]['lines'][-1]['applied'] is False and
         (args.reports / 'missing-font-82000000.final.png').read_bytes() ==
         (args.reports / 'control-82000000.final.png').read_bytes(),
         '缺字模未完整回退原文或原版狀態不同')
    for variant in ('blank', 'duplicate'):
        candidate = json.loads((args.reports / f'catalog-{variant}-82000000.json').read_text())
        need(candidate['state'] == control['state'] and
             candidate['checkpoints'][-1]['lines'][-1]['reason'] ==
             'missing-or-invalid-translation' and
             candidate['checkpoints'][-1]['lines'][-1]['applied'] is False and
             (args.reports / f'catalog-{variant}-82000000.final.png').read_bytes() ==
             (args.reports / 'control-82000000.final.png').read_bytes(),
             f'{variant} 語料未完整回退原文')
    final = json.loads((args.reports / 'final-82000000.json').read_text())
    prior = json.loads((args.reports / 'live-82000000.json').read_text())
    need(final['state'] == prior['state'] and
         (args.reports / 'final-82000000.final.png').read_bytes() ==
         (args.reports / 'live-82000000.final.png').read_bytes(),
         '最後編譯版改變已驗 A 字幕')
    cursor = json.loads((args.reports / 'cursor-82000000.json').read_text())
    cursor_control = json.loads((args.reports / 'cursor-control-82000000.json').read_text())
    need(cursor['state'] == cursor_control['state'] and
         cursor['opened'] == cursor_control['opened'] and
         cursor['checkpoints'][-1]['lines'][-1]['reason'] ==
         'cursor-or-button-over-caption' and
         cursor['checkpoints'][-1]['lines'][-1]['applied'] is False and
         (args.reports / 'cursor-82000000.final.png').read_bytes() ==
         (args.reports / 'cursor-control-82000000.final.png').read_bytes(),
         '游標遮擋時未完整回退原文')
    shown = out[0]
    indexed, palette = shown['indexed'], shown['palette']
    expected = shown['control'].copy()
    for y in range(27, 42):
        for x in range(12, 307):
            i = y*320+x
            if before[i] != indexed[i]:
                expected.paste(color(palette, before[i]), (x*4, y*4, x*4+4, y*4+4))
    ink = Image.frombytes('L', (430, 35), alpha)
    need(ink.getbbox() == (0, 0, 430, 35), '字模可見墨跡框錯誤')
    expected.paste(color(palette, 47), (427, 124), ink)
    expected.paste(color(palette, 14), (423, 120), ink)
    # PIL 與 Go image/draw 的 16-bit Alpha 捨入可差 1–2 個色階；
    # 只接受真正抗鋸齒邊緣，實心墨跡、空白及安全區外必須逐像素相同。
    difference = ImageChops.difference(expected, shown['live'])
    edge_pixels = 0
    if box := difference.getbbox():
        for y in range(box[1], box[3]):
            for x in range(box[0], box[2]):
                delta = difference.getpixel((x, y))
                if not any(delta):
                    continue
                fg = ink.getpixel((x-423, y-120)) if 423 <= x < 853 and 120 <= y < 155 else 0
                shadow = ink.getpixel((x-427, y-124)) if 427 <= x < 857 and 124 <= y < 159 else 0
                need(max(delta) <= 2 and (0 < fg < 255 or 0 < shadow < 255),
                     f'非抗鋸齒捨入差異：{x},{y} {delta}')
                edge_pixels += 1
    summary = {'scope': 'fixed original English BUILD1, recorded Ebitengine inputs',
               'font_size_px': 38, 'ink_size': [430, 35], 'safe_scaled': SAFE,
               'cross_library_alpha_rounding_max': 2, 'edge_rounding_pixels': edge_pixels,
               'legacy_frames_preserved': len(current['frames']),
               'waiting_english_frames': 7, 'missing_font_original_fallback': True,
               'blank_and_duplicate_catalog_fallback': True,
               'cursor_original_fallback': True, 'final_build_same_as_reviewed': True,
               'pairs': [{k: v for k, v in row.items() if k not in
                          ('live', 'control', 'indexed', 'palette')} for row in out]}
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print('PASS：首張字幕 A 版安全區與字模；跨繪圖庫抗鋸齒捨入≤2；原版同狀態、離頁回退')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
