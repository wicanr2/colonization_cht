#!/usr/bin/env python3
"""將目標185既有驗收接到矩陣，只回報已核對的欄位。"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import read, sha

PROFILES = {
    'newgame-save': ('check_goal185_newgame_save.py', 'newgame-save-20261008', 'save-zh-20261008', ['GAME.TXT:0x000007B9']),
    'newgame-reload': ('check_goal185_newgame_save.py', 'reload-newgame-20261008', 'reload-newgame-20261008', ['GAME.TXT:0x00000854']),
    'choice-retention': ('check_goal185_choice_retention.py', 'sailhome-formal-gui-v3', 'retention-final-zh', ['GAME.TXT:@SAILHOME:0x00001B6F', 'GAME.TXT:@SAILHOME:0x00001B6F#2+list']),
    'reports': ('check_goal185_remaining.py', 'closure-report-gui', 'closure-report-formal-zh', ['STRING:colony']),
    'save-error': ('check_goal185_save_failure.py', 'save-error-formal-gui', 'save-error-formal-zh', ['GAME.TXT:0x000007F0']),
    'load-error': ('check_goal185_load_failures.py', 'load-family-error-gui', 'load-family-error-zh', ['GAME.TXT:0x00000971']),
    'load-invalid': ('check_goal185_load_failures.py', 'load-family-invalid-gui', 'load-family-invalid-zh', ['GAME.TXT:0x0000088B']),
    'load-obsolete': ('check_goal185_load_failures.py', 'load-family-obsolete-gui', 'load-family-obsolete-zh', ['GAME.TXT:0x000008C7']),
    'load-map-size': ('check_goal185_load_failures.py', 'load-family-map-size-gui', 'load-family-map-size-zh', ['GAME.TXT:@LOADSIZE:0x00000904']),
    'representatives': ('check_goal185_representatives.py', 'remaining-representatives-v2-gui', 'representatives-v2-zh', [
        'PEDIA.TXT:@CARGO10', 'PEDIA.TXT:@UNIT20', 'PEDIA.TXT:@TERRAIN24',
        'PEDIA.TXT:@JOB14', 'PEDIA.TXT:@BUILDING3', 'PEDIA.TXT:@FATHER0', 'STRING:template:paren-term']),
    'view': ('check_goal185_view_fields.py', 'view-fields-formal-gui', 'view-fields-formal-zh', ['STRING:view-location', 'STRING:view-tribe-land']),
}
ORIGINALS = {
    'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
    'GAME.TXT': '67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a',
    'PEDIA.TXT': 'cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1',
    'NAMES.TXT': '4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061',
}


def check(game, reports, profile):
    if any(not (game / name).is_file() for name in ORIGINALS):
        return None
    for name, digest in ORIGINALS.items():
        assert sha(game / name) == digest, name
    checker, gui_name, zh_name, ids = PROFILES[profile]
    delegated = Path(__file__).parent / checker
    with tempfile.TemporaryDirectory(prefix='colonization-goal185-check-') as tmp:
        output = Path(tmp) / 'proof.json'
        command = [sys.executable, str(delegated), '--game', str(game), '--reports', str(reports), '--output', str(output)]
        if profile == 'reports':
            command += ['--profile', 'reports']
        run = subprocess.run(command, capture_output=True, text=True)
        if run.returncode == 77:
            return None
        if run.returncode != 0:
            raise ValueError(run.stderr[-1600:] or run.stdout[-1600:])
        proof = read(output)
        assert str(proof.get('result', proof.get('status', ''))).startswith('PASS')
    gui = reports / gui_name
    source = reports / zh_name
    report_name = 'gui' if profile == 'newgame-reload' else 'run'
    record = read(source / (report_name + '.json'))
    original = read(gui / 'gui.json')
    assert sha(gui / 'gui.memory') == original['state']['memory_sha256']
    assert record['state'] == original['state']
    assert (source / (report_name + '.memory')).read_bytes() == (gui / 'gui.memory').read_bytes()
    if profile == 'newgame-reload':
        control = reports / 'reload-control-20261008'
        assert (control / 'run.memory').read_bytes() == (gui / 'gui.memory').read_bytes()
    events = record['events']
    active = {e.get('candidate_id') for e in events if e.get('stage') == 'active'}
    fields = {}
    for e in events:
        cid = e.get('candidate_id')
        if e.get('stage') != 'source' or cid not in ids:
            continue
        safe = e.get('safe')
        if not safe or not e.get('shown'):
            continue
        if profile == 'reports' and safe not in ([1, 43, 66, 51], [24, 26, 89, 34]):
            continue
        if profile == 'representatives' and cid == 'STRING:template:paren-term':
            if e['shown'] != '(Major River)' or safe != [242, 88, 291, 96]:
                continue
            assert proof['verified_river_field'] == {'candidate_id': cid, 'shown': e['shown'], 'safe': safe}
        assert cid in active
        field = {'candidate_id': cid, 'shown': e['shown'], 'safe': safe}
        if profile == 'choice-retention' and cid.endswith('+list'):
            assert len(e.get('items', [])) == 2
            field['source_ids'] = ['GAME.TXT:@SAILHOME']
        fields[cid, e['shown'], tuple(safe)] = field
    assert fields and set(ids) == {f['candidate_id'] for f in fields.values()}, profile
    return {
        'result': 'PASS', 'status': 'PASS_GOAL185_REGISTERED_FIELDS', 'profile': profile,
        'inputs_sha256': sha(gui / 'gui.inputs.json'),
        'final_step': original['state']['steps'],
        'final_memory_sha256': original['state']['memory_sha256'],
        'verified_fields': list(fields.values()),
        'delegated_checker_sha256': sha(delegated),
        'delegated_proof_sha256': hashlib.sha256(json.dumps(proof, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        'scope': '只採既有檢查器已核對的欄位；同文TERRAIN23及其他伴隨事件不提高來源完成數。',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--profile', choices=PROFILES, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    result = check(a.game, a.reports, a.profile)
    if result is None:
        print('SKIP：缺合法原版輸入')
        return 77
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
