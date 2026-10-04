#!/usr/bin/env python3
"""Docker/Xvfb：從實際 Linux 啟動器重現主選單懸停、恢復與執行速度。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--launcher', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--game', type=Path)
p.add_argument('--sweep', action='store_true', help='正常滑鼠走過五列與欄位邊界，再移到視窗內空白')
p.add_argument('--end', type=int, default=50000000)
p.add_argument('--unbounded', action='store_true', help='不指定指令上限，達到end後送正常關窗要求')
a = p.parse_args()
assert a.launcher.is_file() and a.output.parent.stat().st_uid == os.getuid()
assert not a.output.exists()
a.output.mkdir()
(a.output / 'save').mkdir()
env = dict(os.environ, DISPLAY=':98', LIBGL_ALWAYS_SOFTWARE='1',
           COLONIZATION_CHT_SAVE=str(a.output / 'save'))
out = a.output / 'run'
timeline = []
start = time.monotonic()
game = None
with (a.output / 'xvfb.log').open('w') as xl, (a.output / 'run.log').open('w') as gl:
    xvfb = subprocess.Popen(['Xvfb', ':98', '-screen', '0', '1600x1000x24', '-nolisten', 'tcp'], env=env, stdout=xl, stderr=xl)
    try:
        time.sleep(.3)
        args = [str(a.launcher), '--audio-mute', '--out', str(out)]
        if not a.unbounded:
            args += ['--window-steps', str(a.end)]
        if a.game:
            args += ['--game', str(a.game)]
        game = subprocess.Popen(args, env=env, stdout=gl, stderr=gl)
        window = None
        def command(*words):
            return subprocess.check_output(words, env=env, text=True).strip()
        def status():
            try:
                return json.loads(Path(str(out) + '.status.json').read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                return {'step': 0}
        def wait(step):
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                s = status()
                if s['step'] >= step:
                    timeline.append({'seconds': time.monotonic()-start, 'status': s})
                    return s['step']
                assert game.poll() is None, (game.returncode, gl.name)
                time.sleep(.03)
            raise TimeoutError(step)
        for _ in range(300):
            found = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', 'Colonization CHT'], env=env, text=True, capture_output=True)
            if found.returncode == 0:
                window = found.stdout.splitlines()[0]
                break
            assert game.poll() is None
            time.sleep(.1)
        assert window
        command('xdotool', 'windowfocus', window)
        def act(*words, advance=600000):
            step = status()['step']
            command('xdotool', *words)
            wait(step + advance)
        def move(x, y):
            act('mousemove', '--window', window, str(x), str(y), advance=400000)
        def shot(label):
            wait(status()['step'] + 400000)
            command('import', '-window', window, str(a.output / (label+'.png')))
            (a.output / (label+'.json')).write_text(json.dumps(status(), ensure_ascii=False, indent=2)+'\n')
        wait(3000000)
        act('keydown', 'Return')
        act('keyup', 'Return', advance=400000)
        wait(12000000)
        move(640, 400)
        act('mousedown', '1')
        act('mouseup', '1', advance=400000)
        wait(24000000)
        move(64, 64)
        shot('menu-before')
        move(512, 440)
        shot('menu-hover')
        move(64, 64)
        shot('menu-after')
        if a.sweep:
            for i, (x, y) in enumerate([(88,107),(160,107),(231,107),(128,115),(88,115),(160,123),(231,123),
                                        (88,131),(128,131),(160,139),(231,139),(86,146),(230,114),(128,130)]):
                move(x*4,y*4)
                shot('sweep-%02d-hover' % i)
                move(64,64)
                shot('sweep-%02d-away' % i)
        if a.unbounded:
            wait(a.end)
            command('python3', '/repo/tools/gui_close_window.py', '--window', window)
        assert game.wait(timeout=180) == 0
        (a.output / 'timing.json').write_text(json.dumps({'arguments': args, 'wall_seconds': time.monotonic()-start, 'timeline': timeline}, ensure_ascii=False, indent=2)+'\n')
    finally:
        for proc in (game, xvfb):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
