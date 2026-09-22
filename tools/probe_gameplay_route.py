#!/usr/bin/env python3
"""Docker 內冷啟動、點選新世界，並驗證安全快照重播的畫面一致性。"""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    game, source, out = Path('/game'), Path('/dosgolem'), Path('/out')
    inputs = {
        'OPENING.EXE': '3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39',
        'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
        'COLONIZE.BAT': '4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db',
    }
    for name, expected in inputs.items():
        if not (game / name).is_file():
            print(f'SKIP：缺少合法原版輸入 {name}，未執行驗收')
            raise SystemExit(77)
        if sha(game / name) != expected:
            raise SystemExit(f'原版輸入不符：{name}')
    if out.stat().st_uid != os.getuid():
        raise SystemExit('輸出目錄擁有者不符')
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True):
        raise SystemExit('請先保存隔離 dosgolem 的修改，不能驗收未識別版本')
    binary = '/tmp/colonization-gameplay-probe'
    subprocess.run(['go', 'build', '-o', binary, './cmd/probe'], cwd=source, check=True, timeout=120)
    menu = out / 'goal053-route-menu.state'
    results = {'dosgolem_commit': commit, 'inputs': inputs, 'variants': {}}
    variants = {
        'continuous': ['-exe', '/game/OPENING.EXE', '-args=-g', '-sbpro',
                       '-bios-keys', '\n', '-bios-key-from', '3000000',
                       '-clicks', '12000001:160:100,30000001:128:110',
                       '-save-state', f'30000000:{menu}'],
        'replay': ['-load-state', str(menu), '-clicks', '30000001:128:110'],
        'control': ['-load-state', str(menu)],
    }
    for name, options in variants.items():
        prefix = out / f'goal053-route-{name}'
        command = [binary, '-root', '/game', '-steps', '40000001',
                   '-click-premove', '2', '-click-polls', '1',
                   '-dump-vram', f'{prefix}.idx', '-dump-palette', f'{prefix}.pal'] + options
        run = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=90)
        Path(f'{prefix}.txt').write_text(run.stdout)
        if run.returncode:
            raise SystemExit(f'{name} 執行失敗；請查看 {prefix}.txt')
        results['variants'][name] = {
            'command': command,
            'hashes': {suffix: sha(Path(f'{prefix}.{suffix}')) for suffix in ['idx', 'pal']},
            'difficulty_asset_opened': 'DIFFICUL.PIK' in run.stdout,
        }
    continuous, replay, control = (results['variants'][x] for x in variants)
    results['same_output'] = continuous['hashes'] == replay['hashes']
    results['input_changes_scene'] = replay['hashes'] != control['hashes']
    results['menu_state_sha256'] = sha(menu)
    (out / 'goal053-route.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    if not (results['same_output'] and results['input_changes_scene']
            and continuous['difficulty_asset_opened'] and replay['difficulty_asset_opened']
            and not control['difficulty_asset_opened']):
        raise SystemExit('路徑驗證未通過；不得標成同狀態驗證完成')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
