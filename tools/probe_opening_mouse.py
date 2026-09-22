#!/usr/bin/env python3
"""在 Docker 內以固定開場快照比較滑鼠座標；原版與快照須唯讀掛載。"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = Path('/dosgolem')
    output = Path('/out')
    state = Path('/inputs/goal033-post-full-copy-5465772.state')
    exe = Path('/game/OPENING.EXE')
    expected = {
        state: 'c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba',
        exe: '3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39',
    }
    for path, sha in expected.items():
        if not path.is_file():
            print(f'SKIP：缺少歷史實驗輸入 {path}，未執行驗收')
            raise SystemExit(77)
        if digest(path) != sha:
            raise SystemExit(f'輸入雜湊不符：{path}')
    if output.stat().st_uid != os.getuid():
        raise SystemExit('輸出目錄擁有者不符')
    # 歷史快照必須配歷史執行器；不切換或修改目前工作樹。
    version = '1435f175e785ea096a9268cd1021a4222300bd43'
    archived = subprocess.check_output(['git', '-C', str(source), 'archive', version])
    binary = '/tmp/colonization-probe'
    with tempfile.TemporaryDirectory(prefix='colonization-baseline-') as build:
        subprocess.run(['tar', '-x', '-C', build], input=archived, check=True)
        subprocess.run(['go', 'build', '-o', binary, './cmd/probe'], cwd=build, check=True, timeout=120)
    variants = {
        'control': [],
        'move-only': ['-mouse-x', '16', '-mouse-y', '16', '-mouse-at', '5465773'],
        'center': ['-click-x', '160', '-click-y', '100'],
        'upper-left': ['-click-x', '16', '-click-y', '16'],
        'lower-right': ['-click-x', '300', '-click-y', '180'],
    }
    result = {'schema': 'colonization-mouse-comparison/1', 'dosgolem_commit': version,
              'inputs': {str(p): h for p, h in expected.items()},
              'coordinate_space': 'probe logical 320x200; int33 CX uses mode-dependent scale',
              'variants': {}}
    timelines = {}
    for name, extra in variants.items():
        prefix = output / f'goal053-{name}'
        command = [binary, '-load-state', str(state), '-root', '/game', '-steps', '7000000',
                   '-click-at', '5465773', '-click-polls', '1',
                   '-regs-at', '0924:0588,0924:05AD,0924:05B0,0110:094F,0110:0952,0110:0956', '-regs-max', '4',
                   '-ip-log', f'5465773:5512000:{prefix}.ip',
                   '-dump-vram', f'{prefix}.idx', '-dump-palette', f'{prefix}.pal'] + extra
        run = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        Path(f'{prefix}.txt').write_text(run.stdout)
        if run.returncode:
            raise SystemExit(f'{name} probe 失敗：{run.returncode}')
        timelines[name] = Path(f'{prefix}.ip').read_bytes()
        result['variants'][name] = {
            'command': command, 'stop': re.findall(r'^停止原因：.*$', run.stdout, re.M),
            'steps': re.findall(r'^執行 (\d+) 道指令$', run.stdout, re.M),
            'mode': re.findall(r'視訊模式 ([0-9A-Fa-f]+)h', run.stdout),
            'hashes': {suffix: digest(Path(f'{prefix}.{suffix}')) for suffix in ['ip', 'idx', 'pal', 'txt']},
        }
    for name in variants:
        timeline = timelines[name]
        reference = timelines['control']
        first = next((i for i in range(0, min(len(timeline), len(reference)), 4)
                      if timeline[i:i+4] != reference[i:i+4]), None)
        result['variants'][name]['first_ip_difference_from_control'] = None if first is None else 5465773 + first // 4
        result['variants'][name]['ip_identical_to_center'] = timeline == timelines['center']
    (output / 'goal053-mouse-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
