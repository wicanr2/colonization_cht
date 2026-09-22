"""Docker 中建立固定執行器的暫存研究探針，重播兩次文字事件。"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source, out, game = Path('/dosgolem'), Path('/out'), Path('/game')
    expected = {
        'OPENING.EXE': '3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39',
        'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
        'GAME.TXT': '67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a',
    }
    for name, value in expected.items():
        if not (game / name).is_file():
            print(f'SKIP：缺少合法原版 {name}，未執行文字驗收')
            raise SystemExit(77)
        if sha(game / name) != value:
            raise SystemExit(f'版本不符：{name}')
    if out.stat().st_uid != os.getuid():
        raise SystemExit('輸出目錄擁有者不符')
    version = '22664265ea7d55ea8706448149908c79d3f0897b'
    archive = subprocess.check_output(['git', '-C', str(source), 'archive', version])
    with tempfile.TemporaryDirectory(prefix='colonization-text-') as build:
        subprocess.run(['tar', '-x', '-C', build], input=archive, check=True)
        subprocess.run(['cp', '/tools/trace_text.go', f'{build}/goal054.go'], check=True)
        binary = f'{build}/text-trace'
        subprocess.run(['go', 'build', '-o', binary, 'goal054.go'], cwd=build, check=True, timeout=120)
        for label in ['clear', 'repeat']:
            subprocess.run([binary, '-capture-text', '-move-away', '25000000',
                            '-out', str(out / f'goal054-{label}-events.json')], check=True, timeout=90)
    hashes = {}
    for suffix in ['.idx', '.pal', '.event0.before', '.event0.after', '.memory']:
        a, b = (out / f'goal054-{label}-events.json{suffix}' for label in ['clear', 'repeat'])
        if sha(a) != sha(b):
            raise SystemExit(f'兩次重播不一致：{suffix}')
        hashes[suffix] = sha(a)
    a, b = (json.loads((out / f'goal054-{label}-events.json').read_text()) for label in ['clear', 'repeat'])
    # 輸出路徑不是遊戲狀態，先排除再比對完整事件。
    for payload in [a, b]:
        for event in payload['events']:
            event.pop('capture', None)
    if a != b or len(a['events']) != 1:
        raise SystemExit('事件重播不一致或非單一目標文字')
    if hashes['.idx'] != '559df11e83c1fb01e2d844a4379af6369e279bf4ea7b4b30c95cbf2d4062c4a1':
        raise SystemExit('畫面不符已驗證基線')
    # 提供 IDA 的已定位段視窗；只留本機，EA 0 對應 runtime 937C:0000。
    segment = (out / 'goal054-clear-events.json.memory').read_bytes()[0x937c0:0x967c0]
    if hashlib.sha256(segment).hexdigest() != 'a199bf5285da8b0ecb0a4bed80f14c772068a3b2212d8077577bda1cf4b2bf21':
        raise SystemExit('IDA 輸入段不符已驗證基線')
    (out / 'goal054-runtime-937c.bin').write_bytes(segment)
    receipt = {'status': 'passed', 'dosgolem_commit': version, 'inputs': expected,
               'probe_source_sha256': sha(Path('/tools/trace_text.go')), 'hashes': hashes,
               'event': a['events'][0], 'limitations': '只驗證固定正常主選單文字，不宣稱全部文字或任意快照'}
    (out / 'goal054-text-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
