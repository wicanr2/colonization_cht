#!/usr/bin/env python3
"""核對目標181正常建城、選建貨車、GAME選單另存的三側原版狀態；不宣稱存檔訊息中文完成。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from check_goal134_window import load, same_state
from check_goal172_window import cp


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    a = p.parse_args()
    if not (a.game / 'OPENING.EXE').is_file():
        print('SKIP：缺合法原版，不宣稱正常存檔通過')
        return 77
    b = a.reports
    gui, zh, control, negative = [load(b / name) for name in
                                  ('gui-colony', 'replay-zh', 'replay-control', 'neg-noatlas')]
    same_state(zh, control, '正常存檔中英原版狀態不同')
    for observed, name in ((gui, '正常GUI'), (negative, '缺圖集負例')):
        need(observed[0]['state'] == control[0]['state'] and observed[1] == control[1] and
             observed[0]['input_hashes'] == control[0]['input_hashes'] and
             observed[0]['opened'] == control[0]['opened'], name + '原版狀態、輸入或完整RAM不同')
    for name, expected in gui[0]['input_hashes'].items():
        need(digest(a.game / name) == expected, '原版指紋不同：' + name)
    inputs = (b / 'gui-colony.inputs.json').read_bytes()
    need(not json.loads(inputs).get('rejected'), '正常GUI有被拒絕輸入')
    shots = dict((name, int(step)) for name, step in
                 (line.split() for line in (b / 'gui-colony.shots').read_text().splitlines()))
    need({'wagon-buy-response', 'game-menu', 'save-slots', 'save-name', 'colony-saved'} <= shots.keys(),
         '沒有完整正常存檔GUI路徑')
    for step in shots.values():
        expected = cp(control[0], step)
        for observed in (zh, negative):
            now = cp(observed[0], step)
            need(all(now[k] == expected[k] for k in
                     ('step', 'memory_sha256', 'raw_sha256', 'palette_sha256')), '存檔路徑原版取樣點不同')
    seed = 'cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e'
    saved = 'c27b44665f1a229ca5257ac8f23b2f63dc025d5814aa5172742ffcd69939e647'
    for folder in ('scratch', 'replay-zh-save', 'replay-control-save', 'neg-noatlas-save'):
        need(digest(b / folder / 'COLONY00.SAV') == seed, '正常初始存檔被覆寫')
        need(digest(b / folder / 'COLONY01.SAV') == saved and
             (b / folder / 'COLONY01.SAV').stat().st_size == 24343, '三側新殖民地存檔位元組不同')
    step = shots['save-name']
    # 本項驗正常另存，沒有驗收成功訊息的中文覆蓋。整張GUI必須與同模式重播相同；
    # 控制模式的狀態欄語言不同，不能把訊息框右側的狀態欄一起要求中英像素相同。
    g = Image.open(b / 'gui-colony.save-name.png').convert('RGB')
    now = Image.open(b / f'replay-zh.cp-{step}.png').convert('RGB')
    need(ImageChops.difference(g, now).getbbox() is None, '正常GUI存檔成功畫面與中文重播不同')
    print(json.dumps({'result': 'PASS', 'inputs_sha256': hashlib.sha256(inputs).hexdigest(),
                      'original_checkpoints': len(set(shots.values())),
                      'final_step': control[0]['state']['steps'],
                      'final_memory_sha256': control[0]['state']['memory_sha256'],
                      'normal_save_name': 'COLONY01.SAV', 'normal_save_sha256': saved,
                      'initial_save_sha256': seed,
                      'limits': '正常另存、三側原版狀態及GUI整張同模式重播；成功訊息仍英文、狀態欄遮擋待驗，未提高其中文完成數'},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
