#!/usr/bin/env python3
"""正常單位肖像標籤的來源角色、字級、同狀態及回退。"""
import argparse
import json
from pathlib import Path

from check_goal185_remaining import EXPECTED, pixels, read, sha
from check_goal185_tutorial_cargo import BINARY, current_source_binary, source_audit, sample_set

BASELINE = 'b4fe380e7ebe657eacdff8c0fad49b9740897daca941dadb15f83d4693a4041e'
GUI_BINARY = '6c3f916e3ab102bb78187fa4052de28722112bd3a4b200ad53ea41c147131a12'
FIELD = 'STRING:unit-selection-caption'
SAFE = [113, 94, 226, 106]


def check(game, reports, repo):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    audit = source_audit(repo, reports)
    assert sha(reports / 'unit-caption-candidate-review.json') == '77a21c0abe2f690f720ba6529631e15d8d644fcc4709621682f9f9b07fe2ca61'
    for filename, digest in {
        'unit_caption_test.go': '38324bceaca73a2e0457bf1ae2d8bf6cc15aec85f7037d64e7fd35816045b5fe',
        'unit-caption-layout.json': '1f089b7b40583e509bdf4d22f2710c1962c32fd3ef78f47d0886b304e45d02a4',
        'unit-caption-capacity.json': 'a4143fe48d5fc8a45c8d42bf4c8cdad30f6a1d636ade06c603b718cf320c1058',
    }.items():
        assert sha(audit / filename) == digest, filename
    tests = [json.loads(s) for s in (audit / 'unit-source-test-results.jsonl').read_text().splitlines()]
    assert not any(e['Action'] in ['fail', 'skip'] for e in tests)
    assert {'TestActualUnitCaptionSourcesAndLayout', 'TestUnitCaptionRoleAndGeometryGuards'} <= {
        e.get('Test') for e in tests if e['Action'] == 'pass'}
    expected = {name: SAFE for name in ['unit-selection-after-move-mode', 'caption-reopened', 'caption-hover-portrait']}
    result, data = sample_set(reports, 'unit-caption-formal-gui', 'unit-caption-current',
                              BINARY, BASELINE, expected, gui_binary=GUI_BINARY)
    assert result['samples'] == 11
    sources = [e for e in data['zh']['events'] if e.get('stage') == 'source' and e.get('candidate_id') == FIELD]
    assert len(sources) == 2
    assert all(e['safe'] == SAFE and e['font_px'] == 30 and e['entry_ip'] == '0D21:00C6' for e in sources)
    assert all(e['shown'] == 'English Pioneers (None)' for e in sources)
    # 同一正式來源重播既有士兵路徑；候選三側已核對的17張收據保留，
    # 此處再核對最新正式二進位的10張像素及完整原版狀態。
    fresh = reports / 'unit-caption-current-soldier'
    old = reports / 'unit-caption-soldier-zh'
    assert sha(Path(read(fresh / 'command.json')[0])) == BINARY
    assert read(fresh / 'run.json')['state'] == read(old / 'run.json')['state']
    for name in ['run.memory', 'raw.wav']:
        assert (fresh / name).read_bytes() == (old / name).read_bytes()
    shots = [line.split() for line in (reports / 'tutorial6-found-on-land-gui/gui.shots').read_text().splitlines()]
    assert len(shots) == 10
    for _, step in shots:
        for ext in ['idx', 'pal']:
            name = 'run.cp-' + step + '.' + ext
            assert (fresh / name).read_bytes() == (old / name).read_bytes()
        name = 'run.cp-' + step + '.png'
        assert pixels(fresh / name) == pixels(old / name)
    return {'result': 'PASS', 'status': 'PASS_UNIT_CAPTION_FORMAL', 'binary_sha256': BINARY,
            'current_binary_sha256': current_source_binary(audit),
            'gui_binary_sha256': GUI_BINARY, **result, 'source_events': sources,
            'verified_fields': [{k: sources[0][k] for k in ['candidate_id', 'shown', 'safe', 'font_px']}],
            'soldier_regression_samples': 10, 'capacity_projection': 184,
            'limitations': ['正常抽樣為前鋒與士兵；184組只驗字型容量。',
                           'None／Expert沿定稿字面譯詞，遊戲資料角色仍未知。',
                           'GUI來自正式標籤版本；當前來源保留相同欄位函式與量測。']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
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
