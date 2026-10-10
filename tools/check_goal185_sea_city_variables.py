#!/usr/bin/env python3
"""四個既有城市槽位的資料契約；不把未抽樣畫面算成正常命中。"""
import argparse
import json
from pathlib import Path

from check_goal185_remaining import pixels, read, sha
from check_goal185_tutorial_cargo import SEA_CITY_BINARY, source_audit

CONTRACT_SHA = 'd60e38cf7f33d5f9c3f58a2b0f7fe16bdcba526b8a0b5481d96d83fcaa059e61'
IDS = {'GAME.TXT:0x00001447', 'GAME.TXT:@FULL:0x00001482',
       'GAME.TXT:@INDIANFOREST2:0x00004F7B', 'GAME.TXT:@TOONEAR:0x00006A24'}


def check(game, reports, repo):
    audit = source_audit(repo, reports)
    assert audit.name in ['sea-city-variable-connection-audit', 'trade-fields-connection-audit',
                          'issue56-source-connection-audit']
    for filename, digest in {
        'sea-city-variable-contracts.json': CONTRACT_SHA,
        'sea_formal_catalog_test.go': '8b08fd047ad74d60a6dd19bcf0666723d09dcaa2076ec7e2213ab21c9a554d83',
        'sea_city_contracts_test.go': 'f4ccf20c083bd856e0dee42191ec6f7c9f4154d12db80b8b6ea02bcb412447ee',
    }.items():
        assert sha(audit / filename) == digest, filename
    tests = [json.loads(s) for s in (audit / 'source-test-results.jsonl').read_text().splitlines()]
    assert {'TestSeaCityVariableContracts', 'TestAdditionalCitySlotIsolation'} <= {
        e.get('Test') for e in tests if e['Action'] == 'pass'}
    values = read(audit / 'sea-city-variable-contracts.json')
    assert len(values) == 16 and {v['id'] for v in values} == IDS
    assert {v['name'] for v in values} == {'Jamestown', 'New Amsterdam', 'Quebec', 'My Colony'}
    assert all(v['zh'] and '錯誤術語' not in v['zh'] for v in values)
    regressions = []
    for fresh_name, accepted_name, gui_name, count in [
        ('sea-city-tutorial-regression', 'orders-compact-tutorial-regression', 'tutorial6-current-formal-gui', 13),
        ('sea-city-build-regression', 'orders-compact-build-regression', 'build-transaction-formal-gui', 31),
        ('sea-city-compact-regression', 'orders-compact-formal-zh', 'orders-compact-formal-gui', 15),
    ]:
        fresh, accepted, gui = reports / fresh_name, reports / accepted_name, reports / gui_name
        assert sha(Path(read(fresh / 'command.json')[0])) == SEA_CITY_BINARY
        assert read(fresh / 'run.json')['state'] == read(accepted / 'run.json')['state']
        for filename in ['run.memory', 'raw.wav']:
            assert (fresh / filename).read_bytes() == (accepted / filename).read_bytes()
        assert {p.name: sha(p) for p in (fresh / 'save').glob('*.SAV')} == {
            p.name: sha(p) for p in (accepted / 'save').glob('*.SAV')}
        shots = (gui / 'gui.shots').read_text().splitlines()
        assert len(shots) == count
        for line in shots:
            _, step = line.split()
            for ext in ['idx', 'pal']:
                filename = 'run.cp-' + step + '.' + ext
                assert (fresh / filename).read_bytes() == (accepted / filename).read_bytes()
            filename = 'run.cp-' + step + '.png'
            assert pixels(fresh / filename) == pixels(accepted / filename)
        regressions.append({'session': gui_name, 'samples': count, 'unchanged': True})
    run = read(reports / 'sea-city-tutorial-regression/run.json')
    fields = [e for e in run['events'] if e.get('stage') == 'source'
              and e.get('candidate_id') == 'GAME.TXT:@TUTORIAL6']
    assert len(fields) == 1 and fields[0]['safe'] == [52, 113, 271, 157]
    return {'result': 'PASS', 'status': 'PASS_SEA_CITY_DATA_CONTRACTS',
            'binary_sha256': SEA_CITY_BINARY, 'city_data_cases': 16,
            'new_templates_normal_hits': 0, 'regressions': regressions,
            'verified_fields': fields, 'inputs_sha256': sha(reports / 'tutorial6-current-formal-gui/gui.inputs.json'),
            'final_step': run['state']['steps'], 'final_memory_sha256': run['state']['memory_sha256'],
            'limitations': ['四個新增城市槽位只完成資料回呼，尚無各自正常GUI，不新增shown。',
                           '本列普查只保留實際回歸的教學6欄位；不宣稱完整#55完成。']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    originals = read(a.repo / 'docs/text-census-baseline.json')['originals']
    if not all((a.game / name).is_file() for name in originals):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    for name, digest in originals.items():
        assert sha(a.game / name) == digest, name
    result = check(a.game, a.reports, a.repo)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
