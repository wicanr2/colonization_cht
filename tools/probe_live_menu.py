#!/usr/bin/env python3
"""Docker 中建置即時切片，對照中文開／關／缺譯的原版狀態。"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dosgolem-commit', required=True, help='已提交且含規格010／011的隔離執行器版本')
    args = parser.parse_args()
    repo, source, game, out = map(Path, ['/repo', '/dosgolem', '/game', '/out'])
    for name in ['OPENING.EXE', 'VICEROY.EXE', 'GAME.TXT']:
        if not (game / name).is_file():
            print(f'SKIP：缺少合法原版 {name}')
            return 77
    if not (out / 'goal056-font-mask.json').is_file():
        print('SKIP：缺少本機已確認字型產生的字模，先執行 bake_local_font.py')
        return 77
    if (out.stat().st_uid, out.stat().st_gid) != (os.getuid(), os.getgid()):
        raise ValueError('輸出目錄擁有權不符')
    for path in out.glob('goal056-live-*'):
        if path.stat().st_uid != os.getuid():
            raise ValueError(f'舊輸出擁有權不符：{path}')
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', args.dosgolem_commit + '^{commit}'], text=True).strip()
    receipt = {'dosgolem_commit': commit, 'adapter_sha256': sha(repo / 'tools/live_menu.go'),
               'catalog_sha256': sha(repo / 'text/draft.zh-Hant.tsv'),
               'font_mask_sha256': sha(out / 'goal056-font-mask.json'), 'variants': {}}
    with tempfile.TemporaryDirectory(prefix='colonization-live-') as temp:
        root = Path(temp)
        engine, app = root / 'dosgolem', root / 'app'
        engine.mkdir()
        app.mkdir()
        archive = subprocess.check_output(['git', '-C', str(source), 'archive', commit])
        subprocess.run(['tar', '-x', '-C', str(engine)], input=archive, check=True)
        # 容器暫存 Go workspace，不改使用者的 go.mod 或取得不存在的遠端版本。
        (app / 'go.mod').write_text('module colonization-live-check\n\ngo 1.24.0\n')
        (root / 'go.work').write_text('go 1.24.0\n\nuse (\n ./app\n ./dosgolem\n)\n')
        shutil.copyfile(repo / 'tools/live_menu.go', app / 'main.go')
        binary = root / 'live-menu'
        subprocess.run(['go', 'build', '-o', str(binary), '.'], cwd=app, check=True, timeout=120)
        common = [str(binary), '-root', str(game), '-catalog', str(repo / 'text/draft.zh-Hant.tsv'),
                  '-font-mask', str(out / 'goal056-font-mask.json')]
        catalog_missing = root / 'missing.tsv'
        with (repo / 'text/draft.zh-Hant.tsv').open() as src:
            reader = csv.DictReader(src, delimiter='\t')
            fields, rows = reader.fieldnames, list(reader)
        with catalog_missing.open('w') as dst:
            writer = csv.DictWriter(dst, fieldnames=fields, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(r for r in rows if r['candidate_id'] != 'GAME.TXT:0x000001B0')
        mask = json.loads((out / 'goal056-font-mask.json').read_text())
        stale_mask = root / 'stale-mask.json'
        stale_mask.write_text(json.dumps(dict(mask, translation_sha256='0' * 64)))
        wide_mask = root / 'wide-mask.json'
        wide_mask.write_text(json.dumps(dict(mask, width=585)))
        variants = [('zh', []), ('control', ['-control']), ('missing', ['-missing']),
                    ('missing-translation', ['-catalog', str(catalog_missing)]),
                    ('stale-font', ['-font-mask', str(stale_mask)]),
                    ('wide-font', ['-font-mask', str(wide_mask)]),
                    ('missing-font', ['-font-mask', str(root / 'absent-font.json')])]
        for name, extra in variants:
            prefix = out / f'goal056-live-{name}'
            run = subprocess.run(common + ['-out', str(prefix)] + extra,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
            Path(str(prefix) + '.log').write_text(run.stdout)
            if run.returncode:
                raise RuntimeError(f'{name} 失敗，見 {prefix}.log')
            receipt['variants'][name] = json.loads(Path(str(prefix) + '.json').read_text())
        # 錯版本不得碰真正原檔；只在容器暫存目錄建立控制組。
        wrong = root / 'wrong-game'
        wrong.mkdir()
        for path in game.iterdir():
            if path.is_file():
                (wrong / path.name).symlink_to(path)
        (wrong / 'VICEROY.EXE').unlink()
        (wrong / 'VICEROY.EXE').write_bytes(b'wrong-version-test')
        bad_prefix = root / 'wrong-result'
        run = subprocess.run(common + ['-root', str(wrong), '-out', str(bad_prefix)],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20)
        receipt['wrong_version_rejected'] = run.returncode != 0 and not Path(str(bad_prefix) + '.json').exists()
        if not receipt['wrong_version_rejected']:
            raise RuntimeError('錯版本未被拒絕')
    zh, control, missing = [receipt['variants'][n] for n in ['zh', 'control', 'missing']]
    receipt['same_original_state'] = all(v['state'] == zh['state'] for v in receipt['variants'].values())
    if not receipt['same_original_state']:
        raise RuntimeError('中文觀測／合成改變原版狀態')
    tables = [{v['label']: v for v in run['checkpoints']} for run in receipt['variants'].values()]
    if any(set(table) != set(tables[0]) for table in tables[1:]):
        raise RuntimeError('檢查點不一致')
    for label in tables[0]:
        for key in ['raw_sha256', 'palette_sha256', 'step']:
            if len({table[label][key] for table in tables}) != 1:
                raise RuntimeError(f'原版檢查點不一致：{label}/{key}')
    for label in ['menu-clear', 'menu-away', 'switch-on']:
        if not tables[0][label]['applied']:
            raise RuntimeError(f'已驗證場景未顯示中文：{label}')
    for label in ['menu-hover', 'switch-off', 'difficulty', 'difficulty-clear']:
        if tables[0][label]['applied']:
            raise RuntimeError(f'應回退的場景仍顯示中文：{label}')
    if any(c['applied'] for name, run in receipt['variants'].items() if name != 'zh' for c in run['checkpoints']):
        raise RuntimeError('英文／缺譯組意外套用中文')
    for name, expected in [('missing-translation', 'missing-or-invalid-translation'),
                           ('stale-font', 'font-binding-mismatch'),
                           ('wide-font', 'font-mask-out-of-bounds'),
                           ('missing-font', 'font-mask-unavailable')]:
        clear = next(c for c in receipt['variants'][name]['checkpoints'] if c['label'] == 'menu-clear')
        if clear['reason'] != expected:
            raise RuntimeError(f'{name} 回退原因不符：{clear["reason"]}')
    if not any(f['applied'] for f in zh['frames']):
        raise RuntimeError('沒有實際顯示幀套用中文，不得以checkpoint代替逐幀驗收')
    receipt['status'] = 'passed'
    receipt['limitations'] = '僅第一列、無頭即時幀合成；游標遮擋回退英文，未交付互動前端或難度文字'
    (out / 'goal056-live-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'passed', 'dosgolem_commit': commit,
                      'same_original_state': True, 'wrong_version_rejected': True,
                      'checkpoints': len(tables[0]), 'frames': len(zh['frames']),
                      'applied_frames': sum(f['applied'] for f in zh['frames']),
                      'limitations': receipt['limitations']}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
