#!/usr/bin/env python3
"""重驗已接受的三種事件版畫收據；不聲稱17種事件全部正常命中。"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from check_goal185_remaining import EXPECTED, read, sha

CHECKER_SHA = 'd8c38848ea41baba2f89bb2cd2031db5844a640f1d2616de33b122a92bfeb304'
SUMMARY_SHA = '3bbaebeab6dd8371c8fa8f954fc0ffa608b911e3bf3da70091e7f0d05a1fde7b'


def check(game, reports):
    for name, digest in EXPECTED.items():
        assert sha(game / name) == digest, name
    batch = reports / '20261004-woodcut-titles'
    checker = batch / 'sample/check.py'
    summary = batch / 'final-sample/summary.json'
    assert sha(checker) == CHECKER_SHA and sha(summary) == SUMMARY_SHA
    run = subprocess.run([sys.executable, str(checker), '--reports', str(batch / 'final-sample'),
                          '--formal', str(batch / 'formal-modal2'), '--baseline', str(batch / 'sample'),
                          '--no-write'], capture_output=True, text=True, timeout=90)
    assert run.returncode == 0, run.stderr[-1500:]
    checked = json.loads(run.stdout)
    assert checked['result'] == 'PASS_REPRESENTATIVE_WOODCUT_SAMPLE'
    assert checked['samples'] == 11 and checked['titles'] == 3
    proof = read(summary)
    zh = read(batch / 'final-sample/zh.json')
    assert proof['input_sha256'] == sha(reports / 'colony-v3/gui-colony.inputs.json')
    for name, digest in zh['input_hashes'].items():
        assert sha(game / name) == digest, name
    sources = [e for e in zh['events'] if e.get('stage') == 'source'
               and e.get('candidate_id') in {t['key'] for t in proof['titles']}]
    assert len(sources) == 3
    return {'result': 'PASS', 'status': 'PASS_RETAINED_WOODCUT_SAMPLE', 'samples': 11, 'titles': 3,
            'inputs_sha256': proof['input_sha256'], 'final_step': zh['state']['steps'],
            'final_memory_sha256': zh['state']['memory_sha256'],
            'verified_fields': [{'candidate_id': e['candidate_id'], 'shown': e['shown'], 'safe': e['safe']}
                                for e in sources],
            'scope': '重驗既有正常GUI輸入的三種事件、十一點同原版狀態與精確標題像素；其餘14種事件未抽樣。'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if not all((a.game / name).is_file() for name in EXPECTED):
        print(json.dumps({'result': 'SKIP', 'reason': 'original-files-missing'}))
        return 77
    result = check(a.game, a.reports)
    if a.output:
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
