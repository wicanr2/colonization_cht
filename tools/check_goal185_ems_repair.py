#!/usr/bin/env python3
"""檢查 EMS 修復的正常 GUI 與三側同輸入收據；只在 Docker 執行。"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(path):
    with Image.open(path) as im:
        return im.size, hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected = {
        'OPENING.EXE': '3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39',
        'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
    }
    if any(not (args.game / name).is_file() for name in expected):
        print('SKIP: 缺少原版輸入')
        return 77
    for name, value in expected.items():
        assert digest(args.game / name) == value, f'原版指紋不符：{name}'
    root = args.reports
    source = root / 'newgame-ems-gui-v3'
    modes = {mode: root / f'ems-new-{mode}' for mode in ['zh', 'control', 'missing']}
    receipt = json.loads((source / 'gui.inputs.json').read_text())
    shots = [line.split() for line in (source / 'gui.shots').read_text().splitlines()]
    assert len(shots) >= 15 and receipt['end'] > 800000000
    gui = json.loads((source / 'gui.json').read_text())
    exit_status = json.loads((source / 'exit-status.json').read_text())
    assert exit_status['steps'] == receipt['end'] and not exit_status['halted'] and not exit_status['exited']
    runs = {mode: json.loads((path / 'run.json').read_text()) for mode, path in modes.items()}
    assert all(run['state'] == gui['state'] for run in runs.values()), 'GUI／三側完整狀態不一致'
    assert all(digest(path / 'run.memory') == gui['state']['memory_sha256'] for path in modes.values())
    assert all(digest(path / 'raw.wav') == digest(source / 'raw.wav') for path in modes.values())
    for mode, run in runs.items():
        assert run['control'] == (mode == 'control')
        # runWindow's replay loop stops on DOS exit or HLT. Reaching this exact
        # horizon, past the old failure, proves no earlier stop occurred.
        assert run['state']['steps'] == receipt['end']
        command = json.loads((modes[mode] / 'command.json').read_text())
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
        assert Path(command[0]).resolve() == (root / 'ems-formal-build/colonization-window').resolve()
        assert Path(command[command.index('--replay-inputs') + 1]).read_bytes() == (source / 'gui.inputs.json').read_bytes()
    cps = {mode: {cp['label']: cp for cp in run['checkpoints']} for mode, run in runs.items()}
    for name, step in shots:
        label = f'cp-{step}'
        for field in ['memory_sha256', 'raw_sha256', 'palette_sha256']:
            assert len({cps[mode][label][field] for mode in modes}) == 1, f'{name}: {field} 不一致'
        for suffix in ['idx', 'pal']:
            assert len({digest(path / f'run.{label}.{suffix}') for path in modes.values()}) == 1
        assert pixels(source / f'gui.{name}.png') == pixels(modes['zh'] / f'run.{label}.png'), f'{name}: GUI 與中文重播不同'
        assert pixels(modes['missing'] / f'run.{label}.png') == pixels(modes['control'] / f'run.{label}.png'), f'{name}: 缺字模未回退'
    existing = json.loads((root / 'existing/gui.json').read_text())
    existing_runs = {
        mode: json.loads((root / f'ems-existing-{mode}/run.json').read_text())
        for mode in ['zh', 'control']
    }
    assert all(run['state'] == existing['state'] for run in existing_runs.values())
    for mode in existing_runs:
        path = root / f'ems-existing-{mode}'
        assert digest(path / 'raw.wav') == digest(root / 'existing/raw.wav')
        for save in (root / 'existing/save').glob('COLONY*.SAV'):
            assert digest(path / 'save' / save.name) == digest(save)
    existing_shots = [line.split() for line in (root / 'existing/gui.shots').read_text().splitlines()]
    for name, step in existing_shots:
        assert pixels(root / f'existing/gui.{name}.png') == pixels(root / f'ems-existing-zh/run.cp-{step}.png')
    formal_gui = root / 'ems-formal-gui'
    session = json.loads((formal_gui / 'session.json').read_text())
    assert digest(Path(session['binary'])) == digest(root / 'ems-formal-build/colonization-window')
    assert all((formal_gui / f'gui.{suffix}').is_file() for suffix in ['json', 'memory', 'inputs.json', 'final.png'])
    assert (formal_gui / 'gui.world.png').is_file() and (formal_gui / 'gui.moved-world.png').is_file()
    assert pixels(formal_gui / 'gui.world.png') != pixels(formal_gui / 'gui.moved-world.png')
    output = {
        'result': 'PASS_EMS_NEWGAME_SAME_STATE',
        'scope': '正常英國發現者開局到1492年春季海上畫面；未驗全部遊玩或其他平台',
        'gui_shots': len(shots),
        'existing_gui_shots': len(existing_shots),
        'existing_state_save_audio': 'PASS',
        'formal_gui': 'world and movement captured; fresh manual save not verified',
        'end': receipt['end'],
        'memory_sha256': gui['state']['memory_sha256'],
        'inputs_sha256': digest(source / 'gui.inputs.json'),
        'binary_sha256': digest(root / 'ems-formal-build/colonization-window'),
        'original_inputs': expected,
    }
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (AssertionError, KeyError, FileNotFoundError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
