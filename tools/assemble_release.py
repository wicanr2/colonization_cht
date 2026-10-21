#!/usr/bin/env python3
"""Docker內彙整已驗三平台公開封包與影片；完整版改由規格041的成對封裝入口建立。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('--version', required=True)
p.add_argument('--staging', type=Path, required=True)
p.add_argument('--promo', type=Path, required=True)
p.add_argument('--smoke', type=Path, required=True)
p.add_argument('--output', type=Path, default=Path('/repo/dist-all'))
p.add_argument('--full-game', type=Path, help='舊參數已停用；完整版請使用package_release.py的成對封裝入口')
p.add_argument('--full-only', action='store_true', help='舊參數已停用，避免產出未分兩類的完整版')
a = p.parse_args()
if a.full_game or a.full_only:
    p.error('此入口只彙整公開交付。三平台兩類完整版請用tools/package_release.py --full-game及對應format，再以tools/package_full_release.py彙整；契約見docs/spec/044-release-and-promo.md。')
sha = lambda data: hashlib.sha256(data).hexdigest()
assert a.output.is_dir() and a.output.stat().st_uid == os.getuid()
assert not (a.output / a.version).exists()
packages = sorted(a.staging.glob(f'*/{a.version}/patch/*'))
assert len(packages) == 3 and {x.suffix for x in packages} == {'.AppImage', '.zip'}
for package in packages:
    source = json.loads((package.parent.parent / 'SHA256SUMS.json').read_text())
    entry = source['packages']['patch/' + package.name]
    assert entry == {'sha256': sha(package.read_bytes()), 'bytes': package.stat().st_size}
film = a.promo / f'colonization-cht-{a.version}-promo.mp4'
video_check = json.loads((a.promo / 'validation.json').read_text())
assert video_check['sha256'] == sha(film.read_bytes()) and video_check['visual_sampling'] == 'PASS_EIGHT_FRAMES'
checks = json.loads((a.smoke / 'summary.json').read_text())
assert checks['result'] == 'PASS_RELEASE_SMOKE_WITH_MACOS_LIMITATION'
root = a.output / a.version
root.mkdir()
(root / 'patch').mkdir()
shutil.copytree(a.promo, root / 'promo')
shutil.copytree(a.smoke, root / 'smoke', ignore=shutil.ignore_patterns('wine-prefix'))
public = {}
for package in packages:
    dst = root / 'patch' / package.name
    shutil.copyfile(package, dst)
    dst.chmod(0o755 if dst.suffix == '.AppImage' else 0o644)
    public['patch/' + dst.name] = {'bytes': dst.stat().st_size, 'sha256': sha(dst.read_bytes())}
public['promo/' + film.name] = {'bytes': film.stat().st_size, 'sha256': video_check['sha256']}
(root / 'SHA256SUMS.json').write_text(json.dumps({'version': a.version, 'packages': public}, ensure_ascii=False, indent=2) + '\n')
print(root)
