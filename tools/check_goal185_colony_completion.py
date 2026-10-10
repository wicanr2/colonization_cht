#!/usr/bin/env python3
"""#56完整來源接線與代表性正常路徑收尾；資料契約不增加畫面命中。"""
import argparse
from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace

from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_trade_fields import check as trade_check
from check_goal185_tutorial_cargo import (ISSUE56_BINARY, TRADE_FIELDS_BINARY,
    sample_set, source_audit, without_approved_city_extension)
from text_census import Census, tsv
from verification_matrix import run_row

SCOPE = {'殖民地', '歐洲港口', '報告', '國會與建國之父', '貿易路線'}
AUDIT_HASHES = {
    'issue56-source-audit.json': 'c291ca785d2320b3d1d6f4133d3ff87c0927758ccfe2b2a7fcaca4cb3a4bae76',
    'issue56-variable-consumers.json': '510b0032f0954e47880929ebf677f30f1a2ad45c631f4f691fb2a0c7b79c7c30',
    'issue56-constant-consumers.json': 'a0d880b7bb1b0bf7e0bbcfac4439ea5851a20b4d6a8803ac1ccb32a45a9bb5c3',
    'issue56_source_audit_test.go': 'f8349c03a27adfe7a16bae510286e07983eb33053132e01b077c89d651ffa4ec',
}
RETAINED = {
    'colony-buy-insufficient', 'colony-buy-payable', 'colony-jobs-and-fathers',
    'colony-profession-equipment', 'colony-abandon-cancel',
    'colony-soldier-unit-options', 'colony-fortified-unit-options',
    'europe-cancel-and-report-fields', 'europe-artillery-purchase', 'goal185-reports',
}


def regression(reports, name, accepted_name, gui_name, count):
    current, accepted = reports / ('issue56-' + name + '-regression'), reports / accepted_name
    assert sha(Path(read(current / 'command.json')[0])) == ISSUE56_BINARY
    assert read(current / 'run.json')['state'] == read(accepted / 'run.json')['state']
    for filename in ['run.memory', 'raw.wav']:
        assert (current / filename).read_bytes() == (accepted / filename).read_bytes(), (name, filename)
    assert {p.name: sha(p) for p in (current / 'save').glob('*.SAV')} == {
        p.name: sha(p) for p in (accepted / 'save').glob('*.SAV')}
    shots = [line.split() for line in (reports / gui_name / 'gui.shots').read_text().splitlines()]
    assert len(shots) == count
    for _, step in shots:
        for extension in ['idx', 'pal']:
            filename = 'run.cp-' + step + '.' + extension
            assert (current / filename).read_bytes() == (accepted / filename).read_bytes(), (name, filename)
        filename = 'run.cp-' + step + '.png'
        assert pixels(current / filename) == pixels(accepted / filename), (name, filename)
    return {'name': name, 'samples': count, 'unchanged': True}


def check(game, reports, repo):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    audit = source_audit(repo, reports)
    assert audit.name == 'issue56-source-connection-audit'
    for name, digest in AUDIT_HASHES.items():
        assert sha(audit / name) == digest, name
    # 重新由原版段落建立分母，不能只核對手填的已接線數量。
    census = Census(game, tsv(repo / 'text/census-map.tsv'))
    rows = [r for r in census.rows if r['screen'] in SCOPE and r['mechanism'] != 'none']
    keys = ['id', 'file', 'section', 'start', 'end', 'text', 'screen', 'reach', 'mechanism']
    assert read(audit / 'source-rows.json') == {
        'originals': census.hashes, 'rows': [{k: r[k] for k in keys} for r in rows]}
    sources = read(audit / 'issue56-source-audit.json')
    counts = {'literal-resolver': 250, 'template-loaded': 37, 'route-land-consumer': 1}
    assert len(rows) == 288 and {r['id'] for r in rows} == {r['id'] for r in sources['rows']}
    assert sources['counts'] == counts
    assert Counter(r['status'] for r in sources['rows']) == counts
    variables, constants = [read(audit / name) for name in
        ['issue56-variable-consumers.json', 'issue56-constant-consumers.json']]
    assert len(variables) == len(constants) == 19
    assert all(v['zh'] and not v.get('reason') for v in variables + constants)
    tests = [json.loads(line) for line in (audit / 'test-results.jsonl').read_text().splitlines()]
    passed = {e['Test'] for e in tests if e['Action'] == 'pass' and 'Test' in e}
    assert not any(e['Action'] in ['fail', 'skip'] for e in tests)
    assert len(passed) == 180
    assert {'TestIssue56SourceAudit', 'TestIssue56VariableConsumerAudit',
            'TestIssue56ConstantConsumerAudit', 'TestAdditionalCitySlotIsolation'} <= passed
    # 只有核准的城市變數分支改動；其他正式執行檔來源保持既有驗收版本。
    previous = reports / 'trade-fields-formal'
    for source in audit.glob('*.go'):
        if source.name.endswith('_test.go'):
            continue
        old, new = (previous / source.name).read_text(), source.read_text()
        if source.name == 'dialog.go':
            old, new = [without_approved_city_extension(s) for s in [old, new]]
        assert old == new, source.name
    trade = trade_check(game, reports, repo)
    normal, data = sample_set(reports, 'issue56-formal-gui', 'issue56-formal',
                              ISSUE56_BINARY, TRADE_FIELDS_BINARY, {})
    assert normal['samples'] == 34 and not normal['changes']
    events = [e for e in data['zh']['events'] if e.get('stage') == 'source']
    for field in trade['verified_fields']:
        assert any(all(e.get(k) == field.get(k) for k in
                       ['candidate_id', 'shown', 'zh', 'font_px', 'safe']) for e in events)
    regressions = [regression(reports, *case) for case in [
        ('tutorial', 'trade-fields-tutorial-regression', 'tutorial6-current-formal-gui', 13),
        ('build', 'trade-fields-build-regression', 'build-transaction-formal-gui', 31),
        ('compact', 'trade-fields-compact-regression', 'orders-compact-formal-gui', 15),
        ('trade', 'trade-fields-formal-zh', 'trade-fields-formal-gui', 34),
    ]]
    config = read(repo / 'tools/verification-matrix.json')
    args = SimpleNamespace(repo=repo, reports=repo / 'workplace/reports', game=game)
    retained = [run_row(row, args) for row in config['rows'] if row['id'] in RETAINED]
    assert {r['id'] for r in retained} == RETAINED
    assert all(r['status'] == 'PASS' for r in retained), retained
    return {
        'result': 'PASS', 'status': 'PASS_COLONY_COMPLETION', 'issue': 56,
        'binary_sha256': ISSUE56_BINARY, 'go_tests': len(passed),
        'source_rows': len(rows), 'source_connections': counts,
        'variable_consumers': len(variables), 'constant_consumers': len(constants),
        'normal_gui': normal, 'regressions': regressions,
        'inputs_sha256': normal['inputs_sha256'],
        'final_step': normal['final_step'],
        'final_memory_sha256': normal['final_memory_sha256'],
        'retained_row_ids': sorted(RETAINED),
        'retained_checks': [{'id': r['id'], 'checker_sha256': r['checker_sha256']} for r in retained],
        'verified_fields': trade['verified_fields'],
        'limitations': [
            '依2026-10-04決定，以完整來源接線及代表性正常路徑收尾，未聲稱全部情境已顯示中文。',
            '五類普查291項含288實際TXT來源及3個歷史整段清單鍵；154 shown、137 pending保持。',
            '新增四個城市條件訊息僅資料契約READY，沒有各自正常GUI，不增加shown。',
            '15項建造全部可見；原版超過22項才換頁，換頁情境未抽樣。',
            '其他貿易編號、母港及自動跑商未抽樣；不由局部畫面外推其規則或版面。',
            '舊BUY、武裝、多人口、議會與港口報表收據重驗通過；沒有宣稱重錄這些GUI。',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(args.game, args.reports, args.repo)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
