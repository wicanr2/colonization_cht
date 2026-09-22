#!/usr/bin/env python3
"""在 Docker 驗證規格 012：逐列中文與失配回退不得影響原版狀態。"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

KEYS = ['GAME.TXT:0x000001B0', 'GAME.TXT:0x000001CB', 'GAME.TXT:0x000001E4',
        'GAME.TXT:0x000001F9', 'GAME.TXT:0x00000204']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dosgolem-commit', required=True)
    args = p.parse_args()
    repo, engine_source, game, out = map(Path, ['/repo', '/dosgolem', '/game', '/out'])
    for name in ['OPENING.EXE', 'VICEROY.EXE', 'GAME.TXT']:
        if not (game / name).is_file():
            print('SKIP：缺少原版 ' + name)
            return 77
    masks = out / 'goal057-fonts'
    for key in KEYS:
        if not (masks / (key.replace(':', '-') + '.json')).is_file():
            print('SKIP：缺少已確認字型的本機字模 ' + key)
            return 77
    for path in [out, *out.glob('goal057-live-*')]:
        if (path.stat().st_uid, path.stat().st_gid) != (os.getuid(), os.getgid()):
            raise ValueError('輸出擁有權不符：' + str(path))
    commit = subprocess.check_output(['git', '-C', str(engine_source), 'rev-parse',
                                      args.dosgolem_commit + '^{commit}'], text=True).strip()
    receipt = {'dosgolem_commit': commit, 'adapter_sha256': sha(repo / 'tools/live_menu.go'),
               'catalog_sha256': sha(repo / 'text/draft.zh-Hant.tsv'),
               'font_masks': {key: sha(masks / (key.replace(':', '-') + '.json')) for key in KEYS},
               'variants': {}}
    with tempfile.TemporaryDirectory(prefix='colonization-multi-') as temporary:
        root = Path(temporary)
        engine, app = root / 'dosgolem', root / 'app'
        engine.mkdir()
        app.mkdir()
        archive = subprocess.check_output(['git', '-C', str(engine_source), 'archive', commit])
        subprocess.run(['tar', '-x', '-C', str(engine)], input=archive, check=True)
        (app / 'go.mod').write_text('module colonization-menu-check\n\ngo 1.24.0\n')
        (root / 'go.work').write_text('go 1.24.0\nuse (\n ./app\n ./dosgolem\n)\n')
        shutil.copyfile(repo / 'tools/live_menu.go', app / 'main.go')
        binary = root / 'menu'
        subprocess.run(['go', 'build', '-o', str(binary), '.'], cwd=app, check=True, timeout=120)
        missing_catalog = root / 'missing.tsv'
        with (repo / 'text/draft.zh-Hant.tsv').open() as src:
            reader = csv.DictReader(src, delimiter='\t')
            fields, rows = reader.fieldnames, list(reader)
        with missing_catalog.open('w') as dst:
            writer = csv.DictWriter(dst, fieldnames=fields, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(row for row in rows if row['candidate_id'] != KEYS[1])
        fixtures = {}
        for kind in ['stale-font', 'wide-font', 'missing-font']:
            target = root / kind
            shutil.copytree(masks, target)
            path = target / (KEYS[1].replace(':', '-') + '.json')
            if kind == 'missing-font':
                path.unlink()  # 僅刪除此函式剛建立的容器暫存測例。
            else:
                mask = json.loads(path.read_text())
                mask['translation_sha256' if kind == 'stale-font' else 'width'] = '0' * 64 if kind == 'stale-font' else 585
                path.write_text(json.dumps(mask))
            fixtures[kind] = target
        variants = [('zh', []), ('control', ['-control']), ('missing', ['-missing']),
                    ('missing-translation', ['-catalog', str(missing_catalog)])]
        variants += [(kind, ['-font-dir', str(path)]) for kind, path in fixtures.items()]
        common = [str(binary), '-root', str(game), '-catalog', str(repo / 'text/draft.zh-Hant.tsv'),
                  '-all-menu', '-font-dir', str(masks)]
        for name, extra in variants:
            prefix = out / ('goal057-live-' + name)
            run = subprocess.run(common + ['-out', str(prefix)] + extra, capture_output=True, text=True, timeout=180)
            Path(str(prefix) + '.log').write_text(run.stdout + run.stderr)
            if run.returncode:
                raise RuntimeError(name + ' 執行失敗，見 ' + str(prefix) + '.log')
            receipt['variants'][name] = json.loads(Path(str(prefix) + '.json').read_text())
    runs = receipt['variants']
    baseline = runs['control']
    for name, run in runs.items():
        if run['state'] != baseline['state']:
            raise RuntimeError(name + ' 改變原版狀態')
        if len(run['checkpoints']) != len(baseline['checkpoints']):
            raise RuntimeError('檢查點數不同')
        for actual, control in zip(run['checkpoints'], baseline['checkpoints']):
            for key in ['label', 'step', 'raw_sha256', 'palette_sha256']:
                if actual[key] != control[key]:
                    raise RuntimeError(name + ' 原始檢查點不一致：' + key)
    def lines(name, label):
        point = next(c for c in runs[name]['checkpoints'] if c['label'] == label)
        result = {r['candidate_id']: r for r in point['lines']}
        if set(result) != set(KEYS):
            raise RuntimeError('每列狀態缺漏或重複')
        return result
    for label in ['menu-clear', 'menu-away', 'switch-on']:
        if not all(r['applied'] for r in lines('zh', label).values()):
            raise RuntimeError('清晰畫面未有五列中文：' + label)
    hover = lines('zh', 'menu-hover')
    # 舊原版收據：第三列墨跡完整，但 (133,123)/(134,123) 背景被游標尾端改變。
    # 必須比較整個安全區，不得只看原文墨跡存續。
    if [hover[key]['applied'] for key in KEYS] != [False, False, False, True, True]:
        raise RuntimeError('游標必須逐列回退，不得遮住游標或撤掉其他列')
    for label in ['switch-off', 'difficulty', 'difficulty-clear']:
        if any(r['applied'] for r in lines('zh', label).values()):
            raise RuntimeError('關閉或切場殘留中文：' + label)
    reasons = {'missing-translation': 'missing-or-invalid-translation',
               'stale-font': 'font-binding-mismatch', 'wide-font': 'font-mask-out-of-bounds',
               'missing-font': 'font-mask-unavailable'}
    for name, reason in reasons.items():
        clear = lines(name, 'menu-clear')
        if clear[KEYS[1]]['applied'] or clear[KEYS[1]]['reason'] != reason:
            raise RuntimeError(name + ' 第二列回退不符')
        if not all(clear[key]['applied'] for key in KEYS if key != KEYS[1]):
            raise RuntimeError(name + ' 其他列被錯誤撤掉')
    for name in ['control', 'missing']:
        if any(c['applied'] for c in runs[name]['checkpoints']):
            raise RuntimeError(name + ' 不應出現中文')
    for key in KEYS:
        if not any(any(r['candidate_id'] == key and r['applied'] for r in f['lines']) for f in runs['zh']['frames']):
            raise RuntimeError(key + ' 沒有 OnFrame 真實命中')
    receipt.update(status='passed', same_original_state=True,
                   limitations='五列主選單，未驗各選項分支、難度中文或互動前端')
    (out / 'goal057-live-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print('五列、七組原版狀態及逐列回退驗證通過')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
