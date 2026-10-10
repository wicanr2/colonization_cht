#!/usr/bin/env python3
"""人口三人的貨車建造、資金不足與存檔正常 GUI 抽驗。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import ImageChops, Image
from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_tutorial_cargo import ISSUE56_BINARY, source_audit

INPUT_SHA = '9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979'
FIELDS = [
    ('build-choice', 'GAME.TXT:@TUTORIAL16',
     '21100d0a521b163c42238e50fd63287f04301c60d1b0af889fcb4dc5dfbd37de', [8, 13, 227, 72], 26),
    ('wagon-buy', 'GAME.TXT:@BUYME1:0x00002F09',
     'ac17c47c4af5d2f378c9de52964aaae352cad3c05c300d22aa1b1ec76561a83e', [80, 114, 220, 147], 30),
    ('saved', 'GAME.TXT:0x000007B9',
     '1a6612502eab83abee076ff0c09ed49f8c96ee0185fc214ddb49341ecf392402', [65, 82, 254, 115], 30),
]


def check(game, reports, repo):
    for name, value in EXPECTED.items():
        assert sha(game / name) == value, name
    source_audit(repo, reports)
    gui = reports / 'issue56-wagon-sample-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT_SHA
    assert sha(Path(read(gui / 'session.json')['binary'])) == ISSUE56_BINARY
    sides = {mode: reports / ('issue56-wagon-sample-' + mode)
             for mode in ['zh', 'control', 'missing']}
    data = {mode: read(path / 'run.json') for mode, path in sides.items()}
    original = read(gui / 'gui.json')
    assert all(d['state'] == original['state'] for d in data.values())
    assert original['state']['steps'] == read(gui / 'gui.inputs.json')['end'] == 173200000
    for mode, path in sides.items():
        assert sha(Path(read(path / 'command.json')[0])) == ISSUE56_BINARY
        assert data[mode]['opened'] == data['zh']['opened']
        assert data[mode]['input_hashes'] == data['zh']['input_hashes']
        assert sha(path / 'run.memory') == sha(gui / 'gui.memory')
        assert sha(path / 'raw.wav') == sha(gui / 'raw.wav')
    save_hashes = [{p.name: sha(p) for p in (directory / 'save').glob('*.SAV')}
                   for directory in [gui] + list(sides.values())]
    assert all(values == save_hashes[0] for values in save_hashes)
    assert set(save_hashes[0]) == {'COLONY00.SAV', 'COLONY09.SAV'}
    shots = dict(line.split() for line in (gui / 'gui.shots').read_text().splitlines())
    assert len(shots) == 15
    points = {mode: {p['step']: p for p in d['checkpoints']} for mode, d in data.items()}
    for name, step_string in shots.items():
        step = int(step_string)
        stem = 'run.cp-' + step_string
        assert pixels(gui / ('gui.' + name + '.png')) == pixels(sides['zh'] / (stem + '.png')), name
        assert pixels(sides['control'] / (stem + '.png')) == pixels(sides['missing'] / (stem + '.png')), name
        for key in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({p[step][key] for p in points.values()}) == 1, (name, key)
        for suffix in ['idx', 'pal']:
            assert len({sha(p / (stem + '.' + suffix)) for p in sides.values()}) == 1
    verified = []
    for name, candidate, shown_sha, safe, size in FIELDS:
        step = int(shots[name])
        events = [e for e in data['zh']['events'] if e.get('stage') == 'source'
                  and e.get('candidate_id') == candidate and e['step'] <= step
                  and hashlib.sha256(e['shown'].encode()).hexdigest() == shown_sha
                  and e['safe'] == safe and e['font_px'] == size]
        assert events and any(r.get('applied') and r['candidate_id'] == candidate
                              for r in points['zh'][step]['lines']), name
        rect = tuple(value * 4 for value in safe)
        stem = 'run.cp-' + str(step) + '.png'
        with Image.open(sides['zh'] / stem) as zh, Image.open(sides['control'] / stem) as control:
            assert ImageChops.difference(zh.convert('RGB').crop(rect), control.convert('RGB').crop(rect)).getbbox(), name
        verified.append(events[0])
    return {'result': 'PASS', 'status': 'PASS_WAGON_SAMPLE', 'samples': len(shots),
            'binary_sha256': ISSUE56_BINARY, 'inputs_sha256': INPUT_SHA,
            'final_step': original['state']['steps'],
            'final_memory_sha256': original['state']['memory_sha256'],
            'save_sha256': save_hashes[0],
            'verified_fields': [e for e in verified if e['candidate_id'] != 'GAME.TXT:@BUYME1:0x00002F09'],
            'observed_ui_fields': verified,
            'limitations': ['只抽驗既有存檔的貨車選擇、資金不足與正常存檔。',
                           'BUY正文同文模板不證明原始查詢來源，本列不增加BUY來源普查信用。',
                           '不將未觸發的貨車上限或晚期城市條件列為正常 GUI 通過。']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path('/repo'))
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if not all((a.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(a.game, a.reports, a.repo)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
