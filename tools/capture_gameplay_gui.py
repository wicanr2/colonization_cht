#!/usr/bin/env python3
"""Docker內錄製正式AppImage，所有遊玩操作經X11送入視窗。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit-seconds', type=int, default=3000)
    parser.add_argument('--capture-fps', type=int, choices=(10, 15, 30), default=30)
    parser.add_argument('--go-workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--cpu-profile', action='store_true', help='保存正式前端的效能取樣，不改原版規則')
    parser.add_argument('--edition', choices=('original', 'hd'), default='original')
    parser.add_argument('--graphics', choices=('original', 'hd'), default='original')
    parser.add_argument('--initial-capture', type=Path, help='只供HD後段正常載入本次建城存檔，主段保持空存檔')
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file(), '只可在Docker內執行'
    assert 120 <= args.limit_seconds <= 5400
    sums = json.loads((args.delivery / 'SHA256SUMS.json').read_text())
    candidates = [(name, item) for name, item in sums['packages'].items()
                  if name.endswith('-' + args.edition + '-linux-x86_64.AppImage')]
    assert len(candidates) == 1 and sums['private_only']
    name, item = candidates[0]
    app = (args.delivery / name).resolve()
    assert app.is_file() and digest(app) == item['sha256']
    d = args.output
    assert d.parent.is_dir() and d.parent.stat().st_uid == os.getuid() and not d.exists()
    d.mkdir()
    (d / 'save').mkdir()
    initial = {}
    if args.initial_capture:
        assert args.edition == 'hd'
        previous = json.loads(args.initial_capture.read_text())
        assert previous['version'] == sums['version'] and previous['initial_saves'] == []
        source = args.initial_capture.parent / 'save/COLONY00.SAV'
        assert digest(source) == previous['save_files']['COLONY00.SAV']
        shutil.copy2(source, d / 'save/COLONY00.SAV')
        initial['COLONY00.SAV'] = digest(source)
    assert args.graphics == 'original' or args.edition == 'hd'
    config = d / 'config/colonization-cht'
    config.mkdir(parents=True)
    (config / 'display.json').write_text(json.dumps({'language': 'zh-Hant', 'graphics': args.graphics, 'speed': 32}) + '\n')
    for name in ('commands.jsonl', 'results.jsonl'):
        (d / name).touch()
    env = dict(os.environ, DISPLAY=':95', GOMAXPROCS=str(args.go_workers), LP_NUM_THREADS='1', GOMEMLIMIT='6800MiB',
               APPIMAGE_EXTRACT_AND_RUN='1', XDG_CONFIG_HOME=str(d / 'config'),
               XDG_CACHE_HOME=str(d / 'cache'), COLONIZATION_CHT_SAVE=str(d / 'save'),
               PYTHONDONTWRITEBYTECODE='1')
    env.pop('LIBGL_ALWAYS_SOFTWARE', None)
    child = xvfb = recorder = None
    started = time.monotonic()
    events, metadata = [], None

    def run(argv, timeout=25):
        return subprocess.run(argv, env=env, capture_output=True, text=True, timeout=timeout, check=True)

    def xd(*values):
        return run(['xdotool', *map(str, values)]).stdout.strip()

    def state():
        path = d / 'gui.status.json'
        return json.loads(path.read_text()) if path.is_file() else {}

    def wait(check, seconds=120):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            assert child.poll() is None, (d / 'gui.log').read_text()[-2500:]
            value = state()
            if check(value):
                return value
            time.sleep(.1)
        raise RuntimeError('正常視窗等待逾時')

    def brief():
        value = state()
        frame = value.get('frame') or {}
        live = frame.get('native_live') or {}
        return {'step': value.get('step'), 'stage': value.get('stage'), 'dialog': value.get('dialog'),
                'display': value.get('display'), 'items': live.get('items'), 'hd': live.get('hd')}

    try:
        with (d / 'xvfb.log').open('w') as log:
            xvfb = subprocess.Popen(['Xvfb', ':95', '-screen', '0', '1280x1024x24', '-noreset', '-nolisten', 'tcp'],
                                    env=env, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(.8)
        gpu_info = run(['/opt/VirtualGL/bin/vglrun', '-d', 'egl0', '/opt/VirtualGL/bin/glxinfo', '-B']).stdout
        assert 'llvmpipe' not in gpu_info.lower()
        (d / 'gpu-info.txt').write_text(gpu_info)
        command = ['/opt/VirtualGL/bin/vglrun', '-d', 'egl0', '-c', 'proxy', '-fps', '0', '+sp', '+pr',
                   str(app), '--play=true', '--audio-mute', '--display-speed', '32',
                   '--window-steps', '6000000000', '--out', str(d / 'gui')]
        if args.cpu_profile:
            command += ['--window-cpu-profile', str(d / 'cpu.pprof')]
        with (d / 'gui.log').open('w') as log:
            child = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        wait(lambda s: bool(s.get('frame')), 360)
        window = xd('search', '--onlyvisible', '--name', 'Colonization CHT').splitlines()[-1]
        xd('windowfocus', '--sync', window)
        geometry = dict(line.split('=', 1) for line in xd('getwindowgeometry', '--shell', window).splitlines() if '=' in line)
        assert (int(geometry['WIDTH']), int(geometry['HEIGHT'])) == (1280, 848)
        actual = []
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
                if int(fields[2]) != child.pid or not (proc / 'comm').read_text().startswith('colonization-wi'):
                    continue
                devices = [os.readlink(p) for p in (proc / 'fd').iterdir() if '/dev/dri/render' in os.readlink(p)]
                actual.append({'pid': int(proc.name), 'binary_sha256': digest(proc / 'exe'), 'render_devices': devices})
            except FileNotFoundError:
                continue
        assert len(actual) == 1 and actual[0]['render_devices']
        from PIL import Image
        # 原始錄影保留啟動過程；不能在送出開場按鍵前等待可見遊戲內容。
        shot = d / 'startup.png'
        run(['import', '-window', window, str(shot)])
        with Image.open(shot) as image:
            visible = sum(image.crop((0, 48, 1280, 848)).convert('L').histogram()[16:])
        record_command = ['ffmpeg', '-y', '-hide_banner', '-nostdin', '-loglevel', 'warning',
                          '-threads', '1', '-filter_threads', '1', '-init_hw_device', 'vaapi=va:/dev/dri/renderD128',
                          '-filter_hw_device', 'va', '-f', 'x11grab', '-framerate', str(args.capture_fps), '-video_size', '1280x848',
                          '-i', f":95+{geometry['X']},{geometry['Y']}", '-vf', 'format=bgra,hwupload,scale_vaapi=format=nv12',
                          '-an', '-c:v', 'h264_vaapi', '-qp', '20', '-r', str(args.capture_fps), '-t', str(args.limit_seconds),
                          '-progress', str(d / 'record-progress.txt'), str(d / 'gameplay-x11.mp4')]
        recorder_start = time.monotonic()
        with (d / 'ffmpeg.log').open('w') as log:
            recorder = subprocess.Popen(record_command, env=env, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(1)
        assert recorder.poll() is None, (d / 'ffmpeg.log').read_text()[-2500:]
        metadata = {'version': sums['version'], 'package': app.name, 'package_sha256': item['sha256'],
                    'binary_sha256': actual[0]['binary_sha256'], 'processes': actual, 'geometry': geometry,
                    'initial_saves': list(initial), 'initial_save_sha256': initial, 'command': command, 'capture_command': record_command,
                    'method': ('new local Intel GPU X11 recording; normal physical window inputs from an empty save directory; no engine input injection, RAM changes or initial save'
                               if not initial else 'new local Intel GPU X11 recording; normal load of the first-colony save created in the recorded new game; no RAM or engine input injection'),
                    'cpu_quota': Path('/sys/fs/cgroup/cpu.max').read_text().strip(), 'audio': 'device muted; original OPL recording used separately in post-production',
                    'capture_fps': args.capture_fps, 'color_conversion': 'Intel VPP BGRA to NV12',
                    'startup_visible_game_pixels': visible,
                    'go_workers': args.go_workers,
                    'recorder_started_monotonic': recorder_start}
        (d / 'session.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
        print('READY', json.dumps({'window': window, 'state': brief()}, ensure_ascii=False)[:1200], flush=True)
        seen, stop = 0, False
        while not stop and time.monotonic() - recorder_start < args.limit_seconds - 30:
            assert child.poll() is None and recorder.poll() is None
            lines = (d / 'commands.jsonl').read_text().splitlines()
            if len(lines) <= seen:
                time.sleep(.1)
                continue
            instruction = json.loads(lines[seen])
            seen += 1
            action, values = instruction['action'], instruction.get('values', [])
            event = {'seq': instruction['seq'], 'action': action, 'values': values,
                     'video_start': time.monotonic() - recorder_start}
            try:
                xd('windowfocus', window)
                if action in ('key', 'game-key'):
                    step = state()['step']
                    xd('keydown', values[0])
                    try:
                        if action == 'game-key':
                            wait(lambda s: s.get('step', 0) >= step + 600000, 120)
                        else:
                            time.sleep(.12)
                    finally:
                        xd('keyup', values[0])
                    time.sleep(.3)
                elif action in ('click', 'game-click', 'move'):
                    xd('mousemove', '--window', window, *values[:2])
                    if action == 'game-click':
                        step = state()['step']
                        wait(lambda s: s.get('step', 0) >= step + 400000, 120)
                    if action in ('click', 'game-click'):
                        xd('mousedown', '1')
                        try:
                            if action == 'game-click':
                                step = state()['step']
                                wait(lambda s: s.get('step', 0) >= step + 600000, 120)
                            else:
                                time.sleep(.12)
                        finally:
                            xd('mouseup', '1')
                    time.sleep(.3)
                elif action == 'wait':
                    start = state()['step']
                    wait(lambda s: s.get('step', 0) >= start + int(values[0]), 360)
                elif action == 'until-step':
                    wait(lambda s: s.get('step', 0) >= int(values[0]), 360)
                elif action == 'seconds':
                    assert 0 <= float(values[0]) <= 30
                    time.sleep(float(values[0]))
                elif action == 'shot':
                    assert Path(values[0]).name == values[0]
                    path = d / (values[0] + '.png')
                    run(['import', '-window', window, str(path)])
                    event['screenshot_sha256'] = digest(path)
                elif action == 'status':
                    pass
                elif action == 'close':
                    stop = True
                else:
                    raise ValueError('未知操作')
                event.update(video_end=time.monotonic() - recorder_start, **brief())
            except Exception as error:
                event['error'] = str(error)
            events.append(event)
            with (d / 'results.jsonl').open('a') as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + '\n')
            print(json.dumps({k: event.get(k) for k in ('seq', 'action', 'values', 'video_end', 'step', 'error')}, ensure_ascii=False), flush=True)
        assert stop, '有界錄影期限已到'
        recorder.send_signal(signal.SIGINT)
        recorder.wait(timeout=30)
        run(['python3', '/repo/tools/gui_close_window.py', '--window', window])
        child.wait(timeout=60)
        assert child.returncode == 0
        metadata.update(video_sha256=digest(d / 'gameplay-x11.mp4'), normal_inputs_sha256=digest(d / 'gui.inputs.json'),
                        recording_seconds=time.monotonic() - recorder_start, actions=len(events), exit_code=child.returncode,
                        save_files={p.name: digest(p) for p in (d / 'save').glob('*.SAV')})
        (d / 'capture.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
        print('CAPTURE_CLOSED', flush=True)
    finally:
        if recorder and recorder.poll() is None:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=30)
        if child and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=10)
        if xvfb and xvfb.poll() is None:
            xvfb.terminate()
            xvfb.wait(timeout=10)


if __name__ == '__main__':
    main()
