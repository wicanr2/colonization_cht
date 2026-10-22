#!/usr/bin/env python3
"""Docker內驗證正式工具列與HD視窗輸出；不把編碼幀率當作執行幀率。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import statistics
import subprocess
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'bundle', 'binary', 'game', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--sample-seconds', type=int, default=12)
    parser.add_argument('--profile-only', action='store_true', help='只收集遊玩與暫停的CPU profile，不列幀率通過')
    parser.add_argument('--renderer', choices=('software', 'vgl-egl'), default='software', help='vgl-egl需容器明確掛入已授權render裝置')
    parser.add_argument('--boot-inputs', type=Path, help='已保存的正常GUI收據；只沿用第一個Enter及其原始步數跳過片頭')
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file(), '必須在有界Docker容器內執行'
    assert args.sample_seconds >= 8
    output = args.output
    assert output.parent.is_dir() and output.parent.stat().st_uid == os.getuid()
    output.mkdir()
    save = output / 'save'
    save.mkdir()
    config = output / 'config/colonization-cht'
    config.mkdir(parents=True)
    (config / 'display.json').write_text('{"language":"zh-Hant","graphics":"hd","speed":32}\n')
    script = (args.bundle / 'colonization-cht.sh').read_text()
    anchor, command = 'here=$(cd "$(dirname "$0")" && pwd)', 'exec "$here/bin/colonization-window"'
    assert script.count(anchor) == script.count(command) == 1
    script = script.replace(anchor, 'here=' + shlex.quote(str(args.bundle)))
    script = script.replace(command, 'exec ' + shlex.quote(str(args.binary)))
    launcher = output / 'launch.sh'
    launcher.write_text(script)
    env = dict(os.environ, DISPLAY=':93', LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='1', GOMAXPROCS='1',
               GOMEMLIMIT='6800MiB', XDG_CONFIG_HOME=str(output / 'config'),
               XDG_CACHE_HOME=str(output / 'cache'), COLONIZATION_CHT_SAVE=str(save))
    if args.renderer == 'vgl-egl':
        env.pop('LIBGL_ALWAYS_SOFTWARE', None)

    def run(argv):
        return subprocess.run(argv, env=env, check=True, capture_output=True, text=True, timeout=20)

    def read_status():
        path = output / 'gui.status.json'
        return json.loads(path.read_text()) if path.is_file() else {}

    def has_hd_art(value):
        if not isinstance(value, dict):
            return False
        return any((key.endswith('painted') and isinstance(item, int) and item > 0) or
                   (isinstance(item, dict) and has_hd_art(item))
                   for key, item in value.items() if 'cursor' not in key and key != 'native_minimap')

    def wait(check, seconds=40):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            assert child.poll() is None, (output / 'gui.log').read_text()[-2000:]
            status = read_status()
            if check(status):
                return status
            time.sleep(.1)
        raise AssertionError('正常GUI狀態等待逾時：' + json.dumps(read_status(), ensure_ascii=False)[:800])

    def click(x, y):
        run(['xdotool', 'mousemove', '--window', window, str(x), str(y)])
        run(['xdotool', 'mousedown', '1'])
        time.sleep(.12)
        run(['xdotool', 'mouseup', '1'])
        time.sleep(.15)

    def screenshot(name):
        time.sleep(.25)  # 等設定狀態真正繪入視窗，再擷取畫面。
        path = output / (name + '.png')
        run(['import', '-window', window, str(path)])
        return {'file': path.name, 'sha256': digest(path)}

    def open_panel(x=1090):
        click(x, 24)
        return wait(lambda s: s.get('display', {}).get('phase') == 2)

    def apply(key, value):
        click(912, 740)
        return wait(lambda s: s.get('display', {}).get('phase') == 0 and
                    s['display']['current'].get(key) == value)

    child = xvfb = None
    checks, shots = [], []
    try:
        with (output / 'xvfb.log').open('w') as log:
            xvfb = subprocess.Popen(['Xvfb', ':93', '-screen', '0', '1280x1024x24', '-noreset', '-nolisten', 'tcp'],
                                    env=env, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(.8)
        argv = ['bash', str(launcher), '--game', str(args.game), '--audio-mute',
                '--hd-assets', str(args.repo / 'graphics'), '--display-ui-catalog', str(args.repo / 'text/frontend-ui.tsv'),
                '--out', str(output / 'gui'), '--window-steps', '400000000']
        if args.profile_only:
            argv += ['--window-cpu-profile', str(output / 'cpu.pprof')]
        gpu = None
        if args.renderer == 'vgl-egl':
            info = run(['/opt/VirtualGL/bin/vglrun', '-d', 'egl0', '/opt/VirtualGL/bin/glxinfo', '-B']).stdout
            assert 'llvmpipe' not in info.lower() and 'OpenGL renderer string:' in info
            (output / 'gpu-info.txt').write_text(info)
            argv = ['/opt/VirtualGL/bin/vglrun', '-d', 'egl0', '-c', 'proxy', '-fps', '60', '-sp', '+pr', *argv]
            gpu = {'driver': info, 'transport': 'uncompressed X11 proxy; frame spoiling disabled; transport limit 60fps'}
        with (output / 'gui.log').open('w') as log:
            child = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        wait(lambda s: bool(s.get('frame')) and s.get('display', {}).get('current', {}).get('graphics') == 'hd', 300)
        if gpu is not None:
            gpu['process_render_devices'] = []
            for p in Path(f'/proc/{child.pid}/fd').iterdir():
                try:
                    name = os.readlink(p)
                except FileNotFoundError:
                    continue
                if '/dev/dri/render' in name:
                    gpu['process_render_devices'].append(name)
            assert gpu['process_render_devices'], '正式前端行程未開啟render裝置'
            (output / 'gpu-runtime.json').write_text(json.dumps(gpu, ensure_ascii=False, indent=2) + '\n')
        window = run(['xdotool', 'search', '--onlyvisible', '--name', 'Colonization CHT']).stdout.splitlines()[-1]
        run(['xdotool', 'windowfocus', '--sync', window])
        if args.profile_only:
            time.sleep(8)
            open_panel()
            time.sleep(6)
            run(['python3', str(args.repo / 'tools/gui_close_window.py'), '--window', window])
            child.wait(timeout=60)
            assert child.returncode == 0 and (output / 'cpu.pprof').is_file()
            (output / 'diagnostic.json').write_text(json.dumps({'result': 'CPU_PROFILE_ONLY_NOT_FPS_ACCEPTANCE',
                'binary_sha256': digest(args.binary), 'profile_sha256': digest(output / 'cpu.pprof')}, indent=2) + '\n')
            print('CPU_PROFILE_COMPLETE', flush=True)
            return
        boot = None
        if args.boot_inputs:
            original_inputs = json.loads(args.boot_inputs.read_text())['inputs']
            first = next(row for row in original_inputs if row['kind'] != 'move')
            assert first['kind'] == 'enter'
            wait(lambda s: s.get('step', 0) >= first['step'], 120)
            run(['xdotool', 'keydown', 'Return'])
            time.sleep(.15)
            run(['xdotool', 'keyup', 'Return'])
            boot = {'inputs_sha256': digest(args.boot_inputs), 'source_first_enter_step': first['step'],
                    'method': 'normal GUI Enter at or after the recorded original-program instruction; no state injection'}
        # 等原版正常啟動出現可見遊戲內容，不能以黑畫面的Draw計數驗收HD。
        from PIL import Image
        deadline = time.monotonic() + 240
        visible = 0
        while visible < 10000 or not has_hd_art(read_status().get('frame', {}).get('native_live', {}).get('hd', {})):
            status = read_status()
            assert status.get('display', {}).get('phase') == 0, '載入量測期間不應開啟設定面板'
            shot = output / 'startup-visible.png'
            run(['import', '-window', window, str(shot)])
            with Image.open(shot) as im:
                visible = sum(im.crop((0, 48, 1280, 848)).convert('L').histogram()[16:])
            assert time.monotonic() < deadline, '尚未出現可見遊戲內容'
            if visible < 10000 or not has_hd_art(status.get('frame', {}).get('native_live', {}).get('hd', {})):
                time.sleep(2)
        open_panel()
        click(353, 577)
        stable = apply('speed', 1)
        native_input_baseline = stable['dos_input_count']
        time.sleep(3)
        perf_path = output / 'gui.performance.json'
        previous = json.loads(perf_path.read_text())['samples']
        start = previous[-1]['seconds_since_first_frame']
        time.sleep(args.sample_seconds)
        samples = [s for s in json.loads(perf_path.read_text())['samples']
                   if s['seconds_since_first_frame'] > start + 1 and not s['paused'] and s['graphics'] == 'hd']
        assert len(samples) >= 4, samples
        seconds = sum(s['sample_seconds'] for s in samples)
        fps = sum(s['output_fps'] * s['sample_seconds'] for s in samples) / seconds
        benchmark = {'output_fps': fps, 'median_output_fps': statistics.median(s['output_fps'] for s in samples),
                     'max_draw_interval_ms': max(s['max_draw_interval_ms'] for s in samples), 'samples': samples,
                     'cpu_quota': Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').is_file() else 'unknown',
                     'cpu_model': next((s.split(':', 1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')), 'unknown'),
                     'rendering': ('Intel/AMD/NVIDIA EGL via VirtualGL with uncompressed X11 proxy' if gpu else 'Xvfb software OpenGL, LP_NUM_THREADS=1') + '; audio device muted; normal original-program startup',
                     'gpu': gpu,
                     'visible_game_pixels': visible,
                     'scope': 'actual Draw output, separate from changed canvases and DOS instruction throughput'}
        (output / 'benchmark.json').write_text(json.dumps(benchmark, ensure_ascii=False, indent=2) + '\n')
        shots.append(screenshot('toolbar-hd'))
        checks.append({'hd_startup': read_status()})
        print('HD_OUTPUT_FPS', round(fps, 3), flush=True)

        for index, speed in enumerate((1, 2, 4, 8, 16, 32)):
            paused = open_panel()
            step = paused['step']
            click(353 + index * 114, 577)
            time.sleep(.25)
            assert read_status()['step'] == step, '設定期間DOS仍在推進'
            result = apply('speed', speed)
            checks.append({'speed': speed, 'state': result['display']})
        time.sleep(2)
        start32 = json.loads(perf_path.read_text())['samples'][-1]['seconds_since_first_frame']
        time.sleep(8)
        samples32 = [s for s in json.loads(perf_path.read_text())['samples']
                     if s['seconds_since_first_frame'] > start32 + 1 and not s['paused'] and s['requested_cpu_speed'] == 32]
        assert len(samples32) >= 4
        seconds32 = sum(s['sample_seconds'] for s in samples32)
        fps32 = sum(s['output_fps'] * s['sample_seconds'] for s in samples32) / seconds32
        benchmark['speed32_output_fps'], benchmark['speed32_samples'] = fps32, samples32
        (output / 'benchmark.json').write_text(json.dumps(benchmark, ensure_ascii=False, indent=2) + '\n')
        print('HD_SPEED32_OUTPUT_FPS', round(fps32, 3), flush=True)
        shots.append(screenshot('toolbar-speed-32'))
        open_panel(380)
        shots.append(screenshot('settings-speed-32'))
        before = (config / 'display.json').read_bytes()
        click(353, 577)
        click(768, 740)
        wait(lambda s: s.get('display', {}).get('phase') == 0)
        assert (config / 'display.json').read_bytes() == before, '取消改寫偏好'

        for index, language in enumerate(('zh-Hant', 'zh-Hans', 'ja', 'ko', 'en')):
            open_panel(380)
            click(363 + index * 136, 374)
            result = apply('language', language)
            assert result['display']['current']['speed'] == 32
            shots.append(screenshot('toolbar-' + language))
            checks.append({'language': language, 'state': result['display']})
        for index, graphics in enumerate(('original', 'hd')):
            open_panel(740)
            click(464 + index * 344, 480)
            result = apply('graphics', graphics)
            assert result['display']['current']['language'] == 'en' and result['display']['current']['speed'] == 32
            checks.append({'graphics': graphics, 'state': result['display']})
        run(['python3', str(args.repo / 'tools/gui_close_window.py'), '--window', window])
        child.wait(timeout=60)
        assert child.returncode == 0
        inputs = json.loads((output / 'gui.inputs.json').read_text())
        assert not [e for e in inputs['inputs'][native_input_baseline:] if e['kind'] != 'move'], '工具列輸入穿透DOS'
        assert list(save.glob('*.SAV')) == [], '工具列測試產生了遊戲存檔'
        receipt = {'result': 'PASS_TOOLBAR_AND_HD_OUTPUT' if min(fps, fps32) >= 30 else 'FAIL_HD_OUTPUT_BELOW_30',
                   'binary_sha256': digest(args.binary), 'ui_catalog_sha256': digest(args.repo / 'text/frontend-ui.tsv'),
                   'benchmark': benchmark, 'checks': checks, 'screenshots': shots,
                   'dos_inputs': inputs, 'toolbar_input_baseline': native_input_baseline, 'boot': boot,
                   'save_files': [], 'command': argv, 'manual_platforms': ['Windows', 'macOS']}
        (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        assert min(fps, fps32) >= 30, '實際HD視窗輸出未達30fps'
        print(receipt['result'], flush=True)
    finally:
        if child and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=10)
        if xvfb and xvfb.poll() is None:
            xvfb.terminate()
            xvfb.wait(timeout=10)


if __name__ == '__main__':
    main()
