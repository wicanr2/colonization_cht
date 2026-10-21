#!/usr/bin/env python3
"""Docker內重播已保存的正常GUI輸入，按指定片段擷取正式顯示畫布。"""

import argparse
import bisect
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    assert re.fullmatch(r'v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}', config['version'])
    output = args.output
    assert output.parent.is_dir() and output.parent.stat().st_uid == os.getuid()
    output.mkdir()
    assert output.stat().st_uid == os.getuid()
    repo, bundle, game, binary = (Path(config[key]) for key in ['repo', 'bundle', 'game', 'binary'])
    normal_inputs = Path(config['normal_inputs'])
    original_capture = Path(config['source_capture'])
    source_capture = json.loads(original_capture.read_text())
    receipt = json.loads(normal_inputs.read_text())
    assert sha(normal_inputs) == source_capture['normal_inputs_sha256']
    assert sha(binary) == config['binary_sha256']
    actions_path = Path(config['source_actions'])
    actions = [json.loads(line) for line in actions_path.read_text().splitlines()]
    offset = config.get('source_recorder_offset', source_capture.get('recorder_offset'))
    assert isinstance(offset, (int, float))
    knots = [(row['wall_end'] - offset, row['step']) for row in actions if 'step' in row]
    assert all(a[0] <= b[0] and a[1] <= b[1] for a, b in zip(knots, knots[1:]))
    times = [row[0] for row in knots]

    def instruction_at(seconds):
        assert times[0] <= seconds <= times[-1]
        i = max(0, min(len(knots) - 2, bisect.bisect_right(times, seconds) - 1))
        a, b = knots[i:i + 2]
        return round(a[1] + (b[1] - a[1]) * (seconds - a[0]) / (b[0] - a[0]))

    fps, steps, clips = config.get('sample_fps', 30), [], []
    assert fps in {10, 15, 30}
    for clip in config['clips']:
        count = round(clip['seconds'] * fps)
        start = len(steps) / fps
        steps.extend(instruction_at(clip['start'] + (clip['end'] - clip['start']) * (i + .5) / count)
                     for i in range(count))
        result = {key: value for key, value in clip.items() if key not in {'start', 'end', 'video', 'video_sha256'}}
        result.update(start=start, end=len(steps) / fps)
        clips.append(result)
    proof_step = config.get('first_colony_step')
    proof_index = None
    if proof_step is not None:
        assert min(steps) <= proof_step <= max(steps)
        proof_index = min(range(len(steps)), key=lambda i: abs(steps[i] - proof_step))
        steps[proof_index] = proof_step
    assert all(a <= b for a, b in zip(steps, steps[1:]))
    checkpoints = sorted(set(steps + [row['step'] for row in config.get('verify', [])]))
    assert checkpoints[-1] <= receipt['end']
    write(output / 'frame-plan.json', {'fps': fps, 'steps': steps, 'clips': clips,
                                      'source_recorder_offset': offset, 'checkpoints': checkpoints})
    shutil.copy2(normal_inputs, output / 'normal-inputs.json')
    save = output / 'save'
    save.mkdir()
    initial = config.get('initial_save')
    if initial:
        shutil.copy2(initial, save / 'COLONY00.SAV')
    initial_saves = sorted(path.name for path in save.glob('*.SAV'))
    initial_hashes = {name: sha(save / name) for name in initial_saves}
    assert initial_saves == source_capture['initial_saves']
    settings = output / 'config/colonization-cht'
    settings.mkdir(parents=True)
    write(settings / 'display.json', {'language': 'zh-Hant', 'graphics': config['graphics']})
    source = (repo / 'tools/release/colonization-cht.sh').read_text()
    anchor = 'here=$(cd "$(dirname "$0")" && pwd)'
    command = 'exec "$here/bin/colonization-window"'
    assert source.count(anchor) == source.count(command) == 1
    source = source.replace(anchor, 'here=' + shlex.quote(str(bundle)))
    source = source.replace(command, 'exec ' + shlex.quote(str(binary)))
    launch = output / 'launch.sh'
    launch.write_text(source)
    env = dict(os.environ, DISPLAY=':90', LIBGL_ALWAYS_SOFTWARE='1', LC_ALL='C.UTF-8',
               GOMAXPROCS='1', XDG_CONFIG_HOME=str(output / 'config'),
               XDG_CACHE_HOME=str(output / 'cache'), COLONIZATION_CHT_SAVE=str(save))
    hd = repo / 'graphics' if config['graphics'] == 'hd' else output / 'no-generated-assets'
    assert config['graphics'] in {'original', 'hd'} and (hd.is_dir() or not hd.exists())
    argv = ['bash', str(launch), '--game', str(game), '--replay-inputs', str(output / 'normal-inputs.json'),
            '--replay-checkpoints-only', '--window-steps', str(receipt['end']),
            '--checkpoint-steps', ','.join(map(str, checkpoints)), '--hd-assets', str(hd),
            '--audio-mute', '--out', str(output / 'replay')]
    if config.get('native_text_diagnostics', False):
        argv.append('--native-text-diagnostics')
    started = time.monotonic()
    with (output / 'xvfb.log').open('w') as xvfb_log:
        xvfb = subprocess.Popen(['Xvfb', ':90', '-screen', '0', '1280x1024x24', '-noreset', '-nolisten', 'tcp'],
                                stdout=xvfb_log, stderr=subprocess.STDOUT, env=env)
        try:
            time.sleep(.8)
            print('CAPTURE_REPLAY_STARTED', len(checkpoints), 'frames, end', receipt['end'], flush=True)
            with (output / 'replay.log').open('w') as log:
                subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT,
                               timeout=config.get('timeout_seconds', 5100), check=True)
        finally:
            xvfb.terminate()
            xvfb.wait(timeout=10)
    report_path = output / 'replay.json'
    report = json.loads(report_path.read_text())
    actual = {row['label']: row for row in report['checkpoints']}
    assert all(f'cp-{step}' in actual for step in checkpoints)
    verified = []
    for check in config.get('verify', []):
        row = actual[f"cp-{check['step']}"]
        items = row['native_live']['items']
        for key in check.get('ids', []):
            assert any(item['id'] == key and re.search(r'[\u3400-\u9fff\uac00-\ud7af\u3040-\u30ff]', item['text'])
                       for item in items), (check['step'], key)
        for term in check.get('source_terms', []):
            assert any(item.get('source', '').strip() == term and
                       re.search(r'[\u3400-\u9fff\uac00-\ud7af\u3040-\u30ff]', item['text'])
                       for item in items), (check['step'], term)
        verified.append({'step': check['step'], 'items': items})
    write(output / 'display-checks.json', verified)
    frames = output / 'frames'
    frames.mkdir()
    for i, step in enumerate(steps):
        os.link(output / f'replay.cp-{step}.png', frames / f'{i:05d}.png')
    video = output / 'gameplay-replay.mp4'
    encode = ['ffmpeg', '-y', '-hide_banner', '-nostdin', '-loglevel', 'warning', '-threads', '1',
              '-framerate', str(fps), '-i', str(frames / '%05d.png'), '-vf', 'fps=30',
              '-frames:v', str(round(len(steps) * 30 / fps)),
              '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '16', '-threads', '1',
              '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)]
    with (output / 'encode.log').open('w') as log:
        subprocess.run(encode, stdout=log, stderr=subprocess.STDOUT, timeout=900, check=True)
    capture = {'version': config['version'], 'binary_sha256': sha(binary), 'initial_saves': initial_saves,
               'initial_save_sha256': initial_hashes, 'normal_inputs_sha256': sha(normal_inputs),
               'video_sha256': sha(video), 'geometry': {'WIDTH': 1280, 'HEIGHT': 800},
               'method': 'original program replay of recorded normal GUI inputs; current formal frontend canvas sampled by instruction; no RAM or direct-entry changes',
               'source_gui_capture': str(original_capture), 'source_gui_capture_sha256': sha(original_capture),
               'source_gui_actions_sha256': sha(actions_path), 'frame_plan_sha256': sha(output / 'frame-plan.json'),
               'report_sha256': sha(report_path), 'original_exe_sha256': sha(game / 'VICEROY.EXE'),
               'rendering': 'frontend canvas, CPU; no new GPU claim', 'command': argv,
               'capture_command': encode, 'recording_seconds': time.monotonic() - started,
               'frames': len(steps), 'sample_fps': fps, 'video_fps': 30,
               'encoded_frames': round(len(steps) * 30 / fps),
               'native_text_diagnostics': config.get('native_text_diagnostics', False),
               'source_contains_cuts': True}
    write(output / 'capture.json', capture)
    write(output / 'clips.json', clips)
    if proof_index is not None:
        assert initial_saves == [] and (save / 'COLONY00.SAV').is_file()
        screenshot = output / 'first-colony.png'
        shutil.copy2(output / f'replay.cp-{proof_step}.png', screenshot)
        proof = {'result': 'FIRST_COLONY_CREATED_VIA_NORMAL_INPUTS', 'version': config['version'],
                 'name': 'Jamestown', 'initial_saves': [], 'video_sha256': sha(video),
                 'screenshot': str(screenshot), 'screenshot_sha256': sha(screenshot),
                 'video_time': proof_index / fps, 'video_clock_method': f'replay sample frame index / {fps}',
                 'save_sha256': sha(save / 'COLONY00.SAV'), 'normal_inputs_sha256': sha(normal_inputs),
                 'source_exe_sha256': sha(game / 'VICEROY.EXE'), 'source_step': proof_step,
                 'method': capture['method']}
        write(output / 'first-colony.json', proof)
    print('CAPTURE_REPLAY_COMPLETE', capture['video_sha256'], flush=True)


if __name__ == '__main__':
    main()
