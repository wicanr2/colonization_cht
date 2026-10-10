#!/usr/bin/env python3
"""正常VIEW懸停、取消、重開及Move Pieces關閉後無殘字。"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_voyage import SOURCES

BINARY = 'f8d65786000bbaecd037fbdf17050bb19ed7d1f9cd5e31d5f0e69450f87ff687'
BASELINE = '70462b912fee1c1277c34c5200df7299d00991ab852a769ac8c673b2f140c79a'
INPUT = '98294d85323cd4aac191121ac93d09f00de5fb5b675ba0c26a0ce6d3141668dd'
CHECKER = 'd93101ea070ba541b2f8c4160e2d6580c3bb4b310e45c3570a6b4a8d92bb717c'
MENU = '5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702'


def check(game, reports):
    for name, digest in dict(EXPECTED, **SOURCES, **{'MENU.TXT': MENU}).items():
        assert sha(game / name) == digest, name
    gui = reports / 'menu-survival-formal-gui'
    assert sha(gui / 'gui.inputs.json') == INPUT
    assert sha(Path(read(gui / 'session.json')['binary'])) == BINARY
    private = reports / 'check_menu_survival_new.py'
    assert sha(private) == CHECKER
    with tempfile.TemporaryDirectory(prefix='colonization-menu-survival-') as tmp:
        output = Path(tmp) / 'proof.json'
        run = subprocess.run([sys.executable, str(private), '--reports', str(reports),
                              '--gui', 'menu-survival-formal-gui', '--prefix', 'menu-survival-formal',
                              '--output', str(output)], capture_output=True, text=True, timeout=90)
        assert run.returncode == 0, run.stderr[-1500:]
        proof = read(output)
    assert proof['result'] == 'PASS_NEW_MENU_SURVIVAL' and proof['samples'] == 17
    assert {row['name'] for row in proof['changes']} == {'move-mode-selected'}
    for mode in ['zh', 'control', 'missing', 'baseline']:
        path = reports / ('menu-survival-formal-' + mode)
        command = read(path / 'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        for name, digest in read(path / 'run.json')['input_hashes'].items():
            assert sha(game / name) == digest, name
    regressions = []
    for session, fresh_name, prior_name, count in [
        ('remaining-representatives-v2-gui', 'menu-survival-formal-pedia-regression', 'menu-survival-pedia-current-baseline', 31),
        ('view-fields-formal-gui', 'menu-survival-formal-view-regression', 'view-fields-formal-zh', 10),
    ]:
        fresh, prior = reports / fresh_name, reports / prior_name
        assert sha(Path(read(fresh / 'command.json')[0])) == BINARY
        assert read(fresh / 'run.json')['state'] == read(prior / 'run.json')['state']
        for name in ['run.memory', 'raw.wav']:
            assert (fresh / name).read_bytes() == (prior / name).read_bytes()
        shots = [line.split() for line in (reports / session / 'gui.shots').read_text().splitlines()]
        assert len(shots) == count
        for name, step in shots:
            stem = 'run.cp-' + step
            assert pixels(fresh / (stem + '.png')) == pixels(prior / (stem + '.png')), (session, name)
            for suffix in ['idx', 'pal']:
                assert (fresh / (stem + '.' + suffix)).read_bytes() == (prior / (stem + '.' + suffix)).read_bytes()
        regressions.append({'session': session, 'samples': count, 'unchanged': True})
    source = proof['source']
    fields = []
    for event in source:
        field = {'candidate_id': event['candidate_id'], 'shown': event['shown'], 'safe': event['safe']}
        if field not in fields:
            fields.append(field)
    return {'result': 'PASS', 'status': 'PASS_MENU_SURVIVAL_FORMAL', 'samples': 17,
            'changes': proof['changes'], 'regressions': regressions,
            'binary_sha256': BINARY, 'inputs_sha256': INPUT, 'original_state': proof['original_state'],
            'final_step': proof['original_state']['steps'],
            'final_memory_sha256': proof['original_state']['memory_sha256'],
            'verified_fields': fields,
            'scope': '正常VIEW懸停、Escape、重開與點選關閉；原版不變，只清除已關閉選單的殘字。'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if not all((a.game / name).is_file() for name in dict(EXPECTED, **SOURCES, **{'MENU.TXT': MENU})):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(a.game, a.reports)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
