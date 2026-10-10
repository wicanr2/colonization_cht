#!/usr/bin/env python3
"""驗證正式儲存失敗中文欄位；與較早英文FAIL收據分開，缺原版回77。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

INPUT = '8689697dbaf3f53c37c50a0897f43eceb0e4953bf720601cef9cdcb53d01f7d6'
BINARY = 'f39336c61f72b27fafb8dd2717d6ed0035c2b1fdb7603167b2d501bbc3193337'
BASELINE = 'baa1eac772f2bc9cee264942813a8915b6af6faba080f3c0bc70dad93b9beee8'


def check(game, reports):
    for name, value in EXPECTED.items():
        assert sha(game/name) == value, name
    gui = reports/'save-error-formal-gui'
    assert sha(gui/'gui.inputs.json') == INPUT
    assert sha(Path(read(gui/'session.json')['binary'])) == BINARY
    fault = read(gui/'fault.json')
    assert fault['kind'] == 'private_save_directory_readonly' and fault['mode'] == '0555'
    assert fault['step'] == 103000000 and fault['after_loaded_world']
    records = {'gui': read(gui/'gui.json')}
    dirs = {mode: reports/('save-error-formal-'+mode) for mode in ('zh', 'control', 'missing', 'baseline')}
    for mode, root in dirs.items():
        record = read(root/'run.json')
        records[mode] = record
        assert record['state'] == records['gui']['state']
        assert record['input_hashes'] == records['gui']['input_hashes']
        assert (root/'run.memory').read_bytes() == (gui/'gui.memory').read_bytes()
        assert (root/'raw.wav').read_bytes() == (gui/'raw.wav').read_bytes()
        assert {p.name: sha(p) for p in (root/'save').glob('COLONY*.SAV')} == {p.name: sha(p) for p in (gui/'save').glob('COLONY*.SAV')}
        command = read(root/'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
    assert records['gui']['state']['steps'] == 141200000
    assert records['gui']['state']['memory_sha256'] == '94f8a05f2d54ddde1617fc3221a4fa85a4367565e9ea79e361382e15d6860085'
    assert not (gui/'save/COLONY00.SAV').exists()
    shots = [line.split() for line in (gui/'gui.shots').read_text().splitlines()]
    assert len(shots) == len({name for name, step in shots}) == 8
    assert {'save-error', 'error-world-return'} <= {name for name, step in shots}
    captures = {r['name']: r for r in map(json.loads, (gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {mode: {r['label']: r for r in record['checkpoints']} for mode, record in records.items() if mode != 'gui'}
    changed = []
    for name, step in shots:
        label = 'cp-'+step
        actual = pixels(gui/f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        assert actual == pixels(dirs['zh']/f'run.{label}.png'), name
        assert pixels(dirs['missing']/f'run.{label}.png') == pixels(dirs['control']/f'run.{label}.png')
        for mode, root in dirs.items():
            for key in ('memory_sha256', 'raw_sha256', 'palette_sha256'):
                assert cps[mode][label][key] == cps['control'][label][key]
            for suffix in ('idx', 'pal'):
                assert (root/f'run.{label}.{suffix}').read_bytes() == (dirs['control']/f'run.{label}.{suffix}').read_bytes()
        with Image.open(gui/f'gui.{name}.png') as im:
            current = im.convert('RGB')
        with Image.open(dirs['baseline']/f'run.{label}.png') as im:
            old = im.convert('RGB')
        diff = ImageChops.difference(current, old).getbbox()
        if name == 'save-error':
            safe = (264, 376, 924, 424)
            assert diff and safe[0] <= diff[0] < diff[2] <= safe[2] and safe[1] <= diff[1] < diff[3] <= safe[3]
            restored = current.copy()
            restored.paste(old.crop(safe), safe[:2])
            assert restored.tobytes() == old.tobytes()
            changed.append({'name': name, 'safe': safe, 'difference': diff})
        else:
            assert diff is None, name
    source = (game/'GAME.TXT').read_bytes()[0x7F0:0x7F0+27]
    assert hashlib.sha256(source).hexdigest() == '1fe8970fc7f4e6a847798b391a98750fef720eb49c9fd7f35bd4c700c8745263'
    shown = source.decode('cp437').replace('%STRING0', 'COLONY00.SAV')
    events = [r for r in records['zh']['events'] if r.get('stage') == 'source' and r.get('shown') == shown]
    assert len(events) == 1
    assert events[0]['candidate_id'] == 'GAME.TXT:0x000007F0' and events[0]['font_px'] == 30 and events[0]['safe'] == [66, 94, 231, 106]
    assert not any(r.get('stage') == 'fallback' and r.get('shown') == shown for r in records['zh']['events'])
    return {'status': 'PASS_SAVE_ERROR_FORMAL', 'scope': '已取證SAVEERROR檔名，私用檔案系統失敗；不外推其他讀檔錯誤',
            'input_sha256': INPUT, 'binary_sha256': BINARY, 'samples': len(shots), 'changes': changed,
            'original_state': records['gui']['state']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game/name).is_file() for name in EXPECTED):
        print('SKIP：缺合法原版輸入')
        return 77
    result = check(a.game, a.reports)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(result['status'], result['samples'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
