#!/usr/bin/env python3
"""六類百科與正常河流欄位抽驗；未命中與真接線缺口分開回報。"""
import argparse
import hashlib
import json
from pathlib import Path

from check_goal185_remaining import EXPECTED, pixels, read, sha

INPUT = '2ca098d3c10a765526278f96718a096468bab8b2614f035ba570c8da2cd34481'
BINARY = 'ed5444ea648d551cf8d512d282c1a9b970b6737dd9d5596f048c1869f4d7ad8c'
PEDIA = {'PEDIA.TXT:@CARGO10','PEDIA.TXT:@UNIT20','PEDIA.TXT:@TERRAIN24','PEDIA.TXT:@JOB14','PEDIA.TXT:@BUILDING3','PEDIA.TXT:@FATHER0','PEDIA.TXT:@TERRAIN23'}


def check(game, reports):
    for name, value in EXPECTED.items():
        assert sha(game/name) == value
    gui = reports/'remaining-representatives-v2-gui'
    assert sha(gui/'gui.inputs.json') == INPUT
    assert sha(Path(read(gui/'session.json')['binary'])) == BINARY
    original = read(gui/'gui.json')
    peers = {mode: reports/('representatives-v2-'+mode) for mode in ('zh','control','missing')}
    data = {mode: read(root/'run.json') for mode, root in peers.items()}
    for mode, root in peers.items():
        assert data[mode]['state'] == original['state']
        assert (root/'run.memory').read_bytes() == (gui/'gui.memory').read_bytes()
        assert (root/'raw.wav').read_bytes() == (gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes'] == original['input_hashes']
        assert {p.name: sha(p) for p in (root/'save').glob('COLONY*.SAV')} == {p.name: sha(p) for p in (gui/'save').glob('COLONY*.SAV')}
        command = read(root/'command.json')
        assert sha(Path(command[0])) == BINARY
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
    shots = [line.split() for line in (gui/'gui.shots').read_text().splitlines()]
    assert len(shots) == len({name for name, step in shots}) == 31
    captures = {r['name']: r for r in map(json.loads, (gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {mode: {r['label']: r for r in record['checkpoints']} for mode, record in data.items()}
    for name, step in shots:
        actual = pixels(gui/f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        stem = 'run.cp-'+step
        assert actual == pixels(peers['zh']/(stem+'.png'))
        assert pixels(peers['control']/(stem+'.png')) == pixels(peers['missing']/(stem+'.png'))
        for mode, root in peers.items():
            for key in ('memory_sha256','raw_sha256','palette_sha256'):
                assert cps[mode]['cp-'+step][key] == cps['control']['cp-'+step][key]
            for suffix in ('idx','pal'):
                assert (root/(stem+'.'+suffix)).read_bytes() == (peers['control']/(stem+'.'+suffix)).read_bytes()
    active = {r['candidate_id'] for r in data['zh']['events'] if r.get('stage') == 'active'}
    assert PEDIA <= active
    # 正常檢視大河欄位：事件與實際安全區皆須顯示，不能只由百科正文推定。
    river_source = [e for e in data['zh']['events'] if e.get('stage') == 'source' and e.get('shown') == '(Major River)']
    assert len(river_source) == 1
    river = river_source[0]
    assert river['candidate_id'] == 'STRING:template:paren-term' and river['safe'] == [242, 88, 291, 96]
    assert river['font_px'] == 22 and river['source_linear'] == 175514 and river['entry_ip'] == '0D21:00C6'
    assert river['zh'] == '（大河）'
    assert any(e.get('stage') == 'active' and e.get('candidate_id') == river['candidate_id'] and e.get('shown') == river['shown'] for e in data['zh']['events'])
    from PIL import Image, ImageChops
    river_step = dict(shots)['river-selected']
    river_area = (968, 352, 1164, 384)
    zh_image = Image.open(peers['zh']/('run.cp-'+river_step+'.png')).convert('RGB')
    en_image = Image.open(peers['control']/('run.cp-'+river_step+'.png')).convert('RGB')
    assert ImageChops.difference(zh_image, en_image).crop(river_area).getbbox()
    for category in ('cargo','unit','terrain','skill','building','father'):
        name = 'pedia-article-'+category
        step = dict(shots)[name]
        assert pixels(gui/f'gui.{name}.png') != pixels(peers['control']/f'run.cp-{step}.png')
    misses = data['zh'].get('string_misses', {})
    view_gaps = {key: value for key, value in misses.items() if key.startswith('no-template\tLocat:') or key.endswith('\tIroquois Land')}
    assert view_gaps, '凍結的尚存欄位缺口收據被更換'
    return {'status':'PASS_PEDIA_REPRESENTATIVES_WITH_VIEW_GAPS','scope':'六類百科及河流頁正常抽樣；View座標與原住民領土仍缺接線，不代表#55完成',
            'samples':len(shots),'input_sha256':INPUT,'binary_sha256':BINARY,'original_state':original['state'],
            'pedia_template_ids':sorted(PEDIA),'view_connection_gaps':view_gaps,
            'verified_river_field':{'candidate_id':river['candidate_id'],'shown':river['shown'],'safe':river['safe']}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True)
    p.add_argument('--reports',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if any(not (a.game/name).is_file() for name in EXPECTED):
        print('SKIP：缺合法原版輸入');return 77
    result=check(a.game,a.reports)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['status'],result['samples']);return 0


if __name__=='__main__':
    raise SystemExit(main())
