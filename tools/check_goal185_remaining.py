#!/usr/bin/env python3
"""四項收尾的限定 GUI 收據檢查；原版缺失回 SKIP 77，不代表整個 Issue 完成。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

EXPECTED = {
    'OPENING.EXE': '3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39',
    'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
    'PEDIA.TXT': 'cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1',
}
INPUT_SHA = '8202dd84ea66a59aa58de44ec02baec4f320fe3f589e0d44098823b683300234'
BINARY_SHA = 'fe58445ee2dd33a891c8ab2ec6ee509b2289bf86a83b67737d1de6cb7c5e4be0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def pixels(path):
    with Image.open(path) as im:
        assert im.size == (1280, 800), (path, im.size)
        return im.convert('RGBA').tobytes()


def check(game, reports, profile='pedia'):
    for name, value in EXPECTED.items():
        assert sha(game/name) == value, f'原版指紋不符：{name}'
    if profile == 'pedia':
        session, input_sha, binary_sha, count, end = 'closure-pedia-v1', INPUT_SHA, BINARY_SHA, 22, 386200000
        side_prefix = 'closure-pedia-'
        scope = '六類百科選單環繞、單位20、F1海洋頁、正常空槽與讀COLONY03、關百科後城名恢復；不證明雜項、額外地形或整個Issue完成'
    elif profile == 'reports':
        session = 'closure-report-gui'
        input_sha = 'fb72ffd260bed6b968f0dec672ed0f78f318e57284cea49fcf7b3be6b1c41a1a'
        binary_sha = 'baa1eac772f2bc9cee264942813a8915b6af6faba080f3c0bc70dad93b9beee8'
        count, end = 10, 448600000
        side_prefix = 'closure-report-formal-'
        scope = '經濟報表港口貨物頁、殖民地軍事與自由之民頁的三處城名；173個预設名容量是量測，不是各名稱正常命中'
    else:
        session = 'closure-save-error-gui'
        input_sha = '574643c8d3bdd816ac3e0d0fce39a03434142777f8b0a375eb16f6d15ba7d8cb'
        binary_sha = 'baa1eac772f2bc9cee264942813a8915b6af6faba080f3c0bc70dad93b9beee8'
        count, end = 9, 151800000
        side_prefix = 'closure-save-error-'
        scope = '獨立存檔目錄唯讀時的正常儲存失敗GUI；三側原版與回退一致，但SAVEERROR檔名被當成術語而未中文顯示'
    gui = reports/session
    assert sha(gui/'gui.inputs.json') == input_sha, '正常 GUI 輸入被更換'
    assert sha(Path(read(gui/'session.json')['binary'])) == binary_sha, 'GUI 前端版本不符'
    shots = [line.split() for line in (gui/'gui.shots').read_text().splitlines()]
    names = [x[0] for x in shots]
    assert len(names) == len(set(names)) == count, '取樣缺失或重複'
    if profile == 'pedia':
        assert all(f'pedia-down-{i}' in names for i in range(8))
        assert {'pedia-article', 'pedia-world-return', 'terrain-context', 'load-slots', 'loaded-fourth-slot'} <= set(names)
    elif profile == 'reports':
        assert {'report-f5-b', 'report-f6-a', 'report-f6-b', 'world-f6'} <= set(names)
    else:
        assert {'save-description', 'save-error', 'error-world-return'} <= set(names)
        fault = read(gui/'fault.json')
        assert fault['kind'] == 'private_save_directory_readonly' and fault['mode'] == '0555'
        assert fault['after_loaded_world'] and fault['step'] == 104000000
        assert not (gui/'save/COLONY00.SAV').exists()
    sides = {mode: reports/(side_prefix+mode) for mode in ('zh', 'control', 'missing')}
    data = {mode: read(path/'run.json') for mode, path in sides.items()}
    original = read(gui/'gui.json')
    state = original['state']
    assert state['steps'] == end
    for mode, path in sides.items():
        command = read(path/'command.json')
        assert sha(Path(command[0])) == binary_sha
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
        assert data[mode]['state'] == state, f'完整原版狀態不同：{mode}'
        assert (path/'run.memory').read_bytes() == (gui/'gui.memory').read_bytes()
        assert (path/'raw.wav').read_bytes() == (gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes'] == original['input_hashes']
        for filename, value in data[mode]['input_hashes'].items():
            assert sha(game/filename) == value
        saves = {f.name: sha(f) for f in (path/'save').glob('COLONY*.SAV')}
        assert saves == {f.name: sha(f) for f in (gui/'save').glob('COLONY*.SAV')}
    captured = {}
    for line in (gui/'gui.capture-attempts.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('aligned'):
            captured[row['name']] = row
    cp = {mode: {r['label']: r for r in value['checkpoints']} for mode, value in data.items()}
    for name, step in shots:
        label = 'cp-'+step
        assert int(step) == captured[name]['frame_step']
        image = pixels(gui/f'gui.{name}.png')
        assert hashlib.sha256(image).hexdigest() == captured[name]['capture_rgba_sha256']
        assert image == pixels(sides['zh']/f'run.{label}.png'), f'GUI 與中文重播不同：{name}'
        assert pixels(sides['missing']/f'run.{label}.png') == pixels(sides['control']/f'run.{label}.png'), f'原文回退不同：{name}'
        for mode in ('zh', 'missing'):
            for field in ('memory_sha256', 'raw_sha256', 'palette_sha256'):
                assert cp[mode][label][field] == cp['control'][label][field], (name, mode, field)
            for suffix in ('idx', 'pal'):
                assert (sides[mode]/f'run.{label}.{suffix}').read_bytes() == (sides['control']/f'run.{label}.{suffix}').read_bytes()
    active = {r['candidate_id'] for r in data['zh']['events'] if r.get('stage') == 'active'}
    if profile == 'pedia':
        assert {'PEDIA.TXT:@UNIT20', 'PEDIA.TXT:@TERRAIN25', 'STRING:colony'} <= active
        for name in ('pedia-article', 'terrain-context', 'pedia-world-return'):
            step = dict(shots)[name]
            assert pixels(gui/f'gui.{name}.png') != pixels(sides['control']/f'run.cp-{step}.png'), name
    elif profile == 'reports':
        baseline = reports/'closure-report-formal-baseline'
        assert read(baseline/'run.json')['state'] == state
        assert (baseline/'run.memory').read_bytes() == (gui/'gui.memory').read_bytes()
        assert (baseline/'raw.wav').read_bytes() == (gui/'raw.wav').read_bytes()
        assert sha(Path(read(baseline/'command.json')[0])) == BINARY_SHA
        areas = {'report-f5-b': (4, 172, 264, 204), 'report-f6-a': (96, 104, 356, 136), 'report-f6-b': (96, 104, 356, 136)}
        for name, step in shots:
            with Image.open(gui/f'gui.{name}.png') as im:
                new = im.convert('RGB')
            with Image.open(baseline/f'run.cp-{step}.png') as im:
                old = im.convert('RGB')
            diff = ImageChops.difference(new, old).getbbox()
            if name in areas:
                assert diff is not None, name
                left, top, right, bottom = areas[name]
                assert left <= diff[0] < diff[2] <= right and top <= diff[1] < diff[3] <= bottom
                restored = new.copy()
                restored.paste(old.crop(areas[name]), areas[name][:2])
                assert restored.tobytes() == old.tobytes()
            else:
                assert diff is None, f'其他畫面改變：{name}'
        sources = [r for r in data['zh']['events'] if r.get('stage') == 'source' and r.get('candidate_id') == 'STRING:colony'
                   and r.get('safe') in ([1, 43, 66, 51], [24, 26, 89, 34])]
        assert len(sources) == 3 and all(r.get('font_px') == 22 and r.get('shown') == 'Jamestown'
                                       and r.get('zh') == '詹姆斯敦（Jamestown）' for r in sources)
    else:
        source = (game/'GAME.TXT').read_bytes()[0x7F0:0x7F0+27]
        assert hashlib.sha256(source).hexdigest() == '1fe8970fc7f4e6a847798b391a98750fef720eb49c9fd7f35bd4c700c8745263'
        shown = source.decode('cp437').replace('%STRING0', 'COLONY00.SAV')
        fallback = [r for r in data['zh']['events'] if r.get('stage') == 'fallback' and r.get('shown') == shown]
        assert len(fallback) == 1 and fallback[0]['reason'] == 'line-variable-without-term'
        # 這張實際是儲存錯誤框；舊腳本誤命名為save-description，保留原始名稱與勘誤。
        step = dict(shots)['save-description']
        area = (264, 376, 920, 420)
        with Image.open(gui/'gui.save-description.png') as im:
            actual = im.convert('RGB').crop(area).tobytes()
        with Image.open(sides['control']/f'run.cp-{step}.png') as im:
            english = im.convert('RGB').crop(area).tobytes()
        assert actual == english, '舊版英文缺口收據已改變'
    return {'status': 'FAIL_TRANSLATION_SAVE_ERROR' if profile == 'save-error' else 'PASS_LIMITED_GUI', 'profile': profile, 'scope': scope,
            'gui_samples': len(shots), 'input_sha256': input_sha, 'binary_sha256': binary_sha,
            'original_inputs': EXPECTED, 'original_state': state}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--profile', choices=['pedia', 'reports', 'save-error'], default='pedia')
    a = p.parse_args()
    if any(not (a.game/f).is_file() for f in EXPECTED):
        print('SKIP：缺合法原版輸入')
        return 77
    result = check(a.game, a.reports, a.profile)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(result['status'], result['gui_samples'])
    return 1 if result['status'].startswith('FAIL') else 0


if __name__ == '__main__':
    raise SystemExit(main())
