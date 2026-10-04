#!/usr/bin/env python3
"""目標180：只驗context-v1實際打開的兩個F1森林頁面；不把八次嘗試算作八頁。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal134_window import load, same_state
from check_goal171_window import dialog_spans
from check_goal179_window import INPUT_SHA, SAVE_SHA, need, observed_strings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    a = p.parse_args()
    r = a.reports
    if not all((a.game / n).is_file() for n in INPUT_SHA) or not (r / 'scratch/COLONY00.SAV').is_file():
        print('SKIP：缺合法原版或正常存檔，未宣稱情境百科驗收完成')
        return 77
    for name, expected in INPUT_SHA.items():
        need(hashlib.sha256((a.game / name).read_bytes()).hexdigest() == expected, name + '原版指紋不同')
    need(hashlib.sha256((r / 'scratch/COLONY00.SAV').read_bytes()).hexdigest() == SAVE_SHA, '正常存檔指紋不同')
    gui, zh, control, neg = (load(r / n) for n in ('gui-pedia', 'replay-zh', 'replay-control', 'neg-noatlas'))
    same_state(zh, control, '中英完整原版狀態不同')
    for other in (gui, neg):
        need(other[0]['state'] == zh[0]['state'] and other[0]['opened'] == zh[0]['opened'] and
             other[0]['input_hashes'] == zh[0]['input_hashes'] and other[1] == zh[1], 'GUI或負例完整狀態不同')
    for n in ('OPENING.EXE', 'VICEROY.EXE'):
        need(zh[0]['input_hashes'].get(n) == INPUT_SHA[n], n + '收據指紋不同')
    raw = (r / 'gui-pedia.inputs.json').read_bytes()
    need(not json.loads(raw).get('rejected'), '真GUI有拒絕輸入')
    need(neg[0]['dialog_reason'] == 'font-mask-unavailable' and not dialog_spans(neg[0]), '缺圖集仍啟用正文')
    spans = [s for s in dialog_spans(zh[0]) if s[0].startswith('PEDIA.TXT:')]
    expected = {'context-f1-0': 'PEDIA.TXT:@TERRAIN12', 'context-f1-3': 'PEDIA.TXT:@TERRAIN23'}
    need({s[0] for s in spans} == set(expected.values()), '實際啟用正文鍵不同')
    cps, controls, negatives = ({c['label']: c for c in v[0]['checkpoints']} for v in (zh, control, neg))
    strings = observed_strings(zh[0])
    checked = set()
    shots = dict(line.split() for line in (r / 'gui-pedia.shots').read_text().splitlines())
    need(expected.keys() <= shots.keys(), '缺實際F1頁面的GUI取樣')
    for name, text_step in shots.items():
        step = int(text_step)
        label = 'cp-' + text_step
        need(label in cps and label in controls and label in negatives, '缺原版取樣點：' + name)
        for key in ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256'):
            need(cps[label][key] == controls[label][key] == negatives[label][key], '原版取樣點不同：' + name)
        if name not in expected:
            continue
        active = [(cid, safe) for cid, lo, hi, safe in spans if lo <= step < hi]
        need(len(active) == 1 and active[0][0] == expected[name], 'F1畫面沒有預期正文：' + name)
        fields = active + [(cid, safe) for text, cid, lo, hi, safe in strings if lo <= step < hi]
        images = [Image.open(r / f).convert('RGB') for f in
                  (f'gui-pedia.{name}.png', f'replay-zh.{label}.png', f'replay-control.{label}.png')]
        for cid, safe in fields:
            box = tuple(x * 4 for x in safe)
            g, z, c = (im.crop(box) for im in images)
            need(ImageChops.difference(g, z).getbbox() is None, name + '中文安全區與GUI不同：' + cid)
            need(ImageChops.difference(z, c).getbbox() is not None, name + '未顯示中文：' + cid)
        checked.update(text for text, cid, lo, hi, safe in strings if lo <= step < hi)
    print(json.dumps({'result': 'PASS', 'articles': expected, 'checkpoints': len(shots),
                      'string_fields': len(checked), 'inputs_sha256': hashlib.sha256(raw).hexdigest(),
                      'final_state_sha256': zh[0]['state']['memory_sha256'], 'input_fingerprints': INPUT_SHA,
                      'limit': '只驗兩頁；TERRAIN23模板歸屬仍強推論，沒有證實其他森林或雜項入口'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
