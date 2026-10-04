#!/usr/bin/env python3
"""正式GUI與同輸入跨平台狀態／音訊核對，只在Pillow驗證容器執行。"""
import hashlib
import json
import argparse
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('--batch', type=Path, default=Path('/repo/workplace/reports/goal183-release'))
p.add_argument('--version', default='v.1.0.0-20261005')
a = p.parse_args()
b = a.batch
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
w, l = b / 'smoke/windows', b / 'smoke/shared-linux'
win = json.loads((w / 'run.json').read_text())
linux = json.loads((l / 'run.json').read_text())
assert win['state'] == linux['state']
for suffix in ['memory', 'final.idx', 'final.pal']:
    assert (w / ('run.' + suffix)).read_bytes() == (l / ('run.' + suffix)).read_bytes(), suffix
assert (w / 'original.wav').read_bytes() == (l / 'original.wav').read_bytes()
normalize = lambda values: [str(value).replace('\\', '/').split('/')[-1].upper() for value in values]
assert normalize(win['opened']) == normalize(linux['opened'])
safe = (320, 356, 968, 584)
reference = Image.open(l / 'run.final.png').convert('RGB')
assert reference.size == (1280, 800)
for platform in ['linux', 'windows']:
    d = b / 'smoke' / platform
    v = json.loads((d / 'version.json').read_text())
    assert v['version'] == a.version and v['os'] == platform and v['arch'] == 'amd64'
    shot = Image.open(d / 'main-menu.png').convert('RGB')
    assert shot.size == (1280, 800) and shot.crop(safe).tobytes() == reference.crop(safe).tobytes()
    frame = json.loads((d / 'run.json').read_text())['frames'][-1]
    applied = {r['candidate_id'] for r in frame['lines'] if r.get('applied')}
    assert len(applied & {'GAME.TXT:0x000001B0', 'GAME.TXT:0x000001CB', 'GAME.TXT:0x000001E4', 'GAME.TXT:0x000001F9', 'GAME.TXT:0x00000204'}) == 5
report = {'result': 'PASS_RELEASE_SMOKE_WITH_MACOS_LIMITATION', 'version': a.version,
          'linux': '正式AppImage展開後AppRun正常GUI', 'windows': '正式ZIP內批次檔Wine正常GUI',
          'macos': '雙架構與臨時簽章資料通過；未驗真機、Gatekeeper或最低系統',
          'same_inputs_sha256': sha(w / 'run.inputs.json'), 'ram_sha256': sha(w / 'run.memory'),
          'wav_sha256': sha(w / 'original.wav'), 'state_equal': True, 'audio_equal': True,
          'safe_rect': safe, 'packages': json.loads((b / 'packages-check.json').read_text())}
(b / 'smoke/summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'packages'}, ensure_ascii=False))
