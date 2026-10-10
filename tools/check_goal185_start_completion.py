#!/usr/bin/env python3
"""#61收尾審查：全部來源接線、已接受抽樣、正常存讀與回退。"""
import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_goal185_remaining import read, sha
from check_goal185_woodcut_sample import check as check_woodcut
from check_goal185_tutorial_cities import check as check_tutorial_cities
from check_goal185_tutorial_cargo import check as check_tutorial_cargo
from text_census_history import BASELINE_SHA, METADATA_SHA

CONNECTION_SHA = '3fc1c56f7983aa1bf43c65bdccf85cceca688ff10b16cfc4c6e0e4eb773ea2b1'
SECTIONS_SHA = '072931935c0702b24275272127e38529168bbc3cefa9b77242a801a3e7bb1694'
SECTIONS = {'PICKNATION': 5, 'DIFFICULTY': 6, 'CLAND': 4, 'CCONT': 4, 'CTEMP': 4, 'CCLIM': 4}
ACCEPTED = ['tutorial-help', 'tutorial-dialogs', 'colony-strings', 'nation-cards-rest',
            'third-card', 'england-intro', 'other-intros', 'build-captions']
CURRENT = ['goal185-newgame-save', 'goal185-newgame-reload', 'goal185-save-error',
           'goal185-load-error', 'goal185-load-invalid', 'goal185-load-obsolete',
           'goal185-load-map-size', 'save-load-slot-lists', 'start-custom-three-fields',
           'start-custom-eight-values', 'start-map-load-centered-title', 'woodcut-three-retained-samples',
           'tutorial-cargo-city']


def check(game, reports, repo):
    assert sha(repo / 'docs/text-census-baseline.tsv') == BASELINE_SHA
    assert sha(repo / 'docs/text-census-baseline.json') == METADATA_SHA
    meta = read(repo / 'docs/text-census-baseline.json')
    for name, digest in meta['originals'].items():
        assert sha(game / name) == digest, name
    # 模板載入不證明文字變數接線。正常7／15驗收與6的城市來源角色
    # 必須另有證據，不能沿舊21模板計數再次給出完整Issue的PASS。
    tutorial_cities = check_tutorial_cities(game, reports)
    tutorial_cargo = check_tutorial_cargo(game, reports, repo)
    source_pairs = [('adapter.go', 'live_menu.go'), ('dialog.go', 'dialog_overlay.go'),
                    ('strings.go', 'string_overlay.go')]
    candidates = [reports / 'start-current-connection-audit', reports / 'menu-survival-connection-audit',
                  reports / 'port-family-connection-audit', reports / 'build-transaction-connection-audit',
                  reports / 'reprint-frame-connection-audit',
                  reports / 'unit-caption-city-connection-audit', reports / 'orders-compact-connection-audit',
                  reports / 'sea-city-variable-connection-audit', reports / 'trade-fields-connection-audit',
                  reports / 'issue56-source-connection-audit']
    matching = [directory for directory in candidates
                if (directory / 'start-connection-audit.json').is_file()
                and (directory / 'start-sections-audit.json').is_file()
                and sha(directory / 'start-connection-audit.json') == CONNECTION_SHA
                and sha(directory / 'start-sections-audit.json') == SECTIONS_SHA
                and all((directory / local).read_bytes() == (repo / 'tools' / source).read_bytes()
                        for local, source in source_pairs)]
    assert matching, '缺與目前正式來源相同的完整開局接線審查'
    audit = matching[0]
    connected = read(audit / 'start-connection-audit.json')
    assert connected['tutorial_count'] == 21 and all(connected['tutorial_ids'].values())
    assert connected['woodcut_count'] == len(connected['woodcut_titles']) == 17
    sections = read(audit / 'start-sections-audit.json')
    assert sections['line_count'] == 27 and set(sections['sections']) == set(SECTIONS)
    draft = list(csv.DictReader((repo / 'text/draft.zh-Hant.tsv').open(), delimiter='\t'))
    for section, count in SECTIONS.items():
        expected = {r['candidate_id']: r for r in draft if r['source_file'] == 'GAME.TXT'
                    and r['notes'].split(';', 1)[0] == '@' + section}
        rows = sections['sections'][section]
        assert len(rows) == count and {r['id'] for r in rows} == set(expected)
        for row in rows:
            original = expected[row['id']]
            assert row['zh'] == original['zh_hant'].strip()
            assert row['source_sha256'] == original['source_sha256']
            assert row['source_bytes_sha256'] == original['source_bytes_sha256']
    adapter = (repo / 'tools/live_menu.go').read_text()
    assert 'dlg.cat.addCorpus(helpBytes' in adapter and 'dlg.cat.addDraft(draftBytes' in adapter
    assert 'loadStringCatalog(' in adapter
    matrix = read(repo / 'tools/verification-matrix.json')
    ids = {r['id'] for r in matrix['rows']}
    assert set(ACCEPTED + CURRENT) <= ids
    assert set(ACCEPTED) <= set(meta['historical_row_ids'])
    assert '歷史矩陣報表原文封存' in (repo / 'WORKLOG.md').read_text()
    checks = ['check_goal185_newgame_save.py', 'check_goal185_save_failure.py',
              'check_goal185_load_failures.py', 'check_goal185_custom_settings.py',
              'check_goal185_start_settings.py', 'check_goal185_map_title.py']
    verified = []
    with tempfile.TemporaryDirectory(prefix='colonization-start-completion-') as tmp:
        for i, filename in enumerate(checks):
            output = Path(tmp) / f'{i}.json'
            run = subprocess.run([sys.executable, str(repo / 'tools' / filename), '--game', str(game),
                                  '--reports', str(reports), '--output', str(output)],
                                 capture_output=True, text=True, timeout=150)
            assert run.returncode == 0, (filename, run.stderr[-1500:], run.stdout[-300:])
            proof = read(output)
            assert str(proof.get('status', proof.get('result', ''))).startswith('PASS'), filename
            verified.append(filename)
    woodcut = check_woodcut(game, repo / 'workplace/reports/goal181-colony-rest')
    # 地圖載入檢查器已逐圖核對同一路徑的AMERICA正文與選項、原文回退。
    # 本審查只新增這兩個已可見欄位的普查登錄，不擴大其他伴隨事件。
    map_gui = read(reports / 'map-title-formal-gui/gui.json')
    map_run = read(reports / 'map-title-formal-zh/run.json')
    america_ids = {'GAME.TXT:@AMERICA:0x00000231', 'GAME.TXT:0x000002A0+list'}
    america = [e for e in map_run['events'] if e.get('stage') == 'source'
               and e.get('candidate_id') in america_ids]
    assert {e['candidate_id'] for e in america} == america_ids
    active = {e.get('candidate_id') for e in map_run['events'] if e.get('stage') == 'active'}
    assert america_ids <= active
    fields = []
    for event in america:
        safe = [80, 70, 239, 104] if event['candidate_id'].startswith('GAME.TXT:@AMERICA:') else [85, 106, 171, 130]
        assert event['safe'] == safe and event['font_px'] == 30 and event['entry_ip'] == '0D21:00C6'
        if event['candidate_id'].endswith('+list'):
            assert event['items'] == ['Original Americas', 'Map Editor']
        field = {'candidate_id': event['candidate_id'], 'shown': event['shown'], 'safe': safe}
        if field not in fields:
            fields.append(field)
    assert len(fields) == 2 and map_run['state'] == map_gui['state']
    census = {r['id']: r for r in csv.DictReader((repo / 'docs/text-census.tsv').open(), delimiter='\t')}
    for key in ['GAME.TXT:@SAVEGAME', 'GAME.TXT:@SAVEGOOD', 'GAME.TXT:@LOADGAME', 'GAME.TXT:@LOADGOOD',
                'GAME.TXT:@SAVEERROR', 'GAME.TXT:@LOADERROR', 'GAME.TXT:@LOADNOT', 'GAME.TXT:@LOADOLD',
                'GAME.TXT:@LOADSIZE', 'GAME.TXT:@MAPTOLOAD', 'WOODCUT.TXT:@WOODCUT',
                'GAME.TXT:@TUTORIAL6', 'GAME.TXT:@TUTORIAL7', 'GAME.TXT:@TUTORIAL15']:
        assert census[key]['status'] == 'shown', key
    return {'result': 'PASS', 'status': 'PASS_ISSUE61_COMPLETION_AUDIT', 'issue': 61,
            'requirements': {'six_startup_sections_connected': 27, 'tutorial_templates_connected': 21,
                             'tutorial_city_variables': tutorial_cities['status'],
                             'tutorial_cargo_city_variables': tutorial_cargo['status'],
                             'all_tutorial_variables_audited': tutorial_cargo['tutorial_variables_connected'],
                             'woodcut_titles_connected': 17, 'normal_save_load_and_failures': verified,
                             'accepted_startup_and_tutorial_samples_retained': ACCEPTED,
                             'woodcut_representative_titles': woodcut['titles'], 'matrix_and_census_updated': True},
            'census_sha256': sha(repo / 'docs/text-census.tsv'),
            'verified_fields': fields,
            'inputs_sha256': sha(reports / 'map-title-formal-gui/gui.inputs.json'),
            'final_step': map_gui['state']['steps'],
            'final_memory_sha256': map_gui['state']['memory_sha256'],
            'limitations': ['六項開局原始段落未聲稱逐段正常命中，實際卡片與設定改選另有驗收。',
                           '教學與版畫採使用者已確認的代表性抽樣；其餘局勢未抽樣保留，不提高原始來源命中數。',
                           '本審查不包含新版封包、發行、人耳音訊或macOS真機驗收。']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    meta = read(a.repo / 'docs/text-census-baseline.json')
    if not all((a.game / name).is_file() for name in meta['originals']):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(a.game, a.reports, a.repo)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
