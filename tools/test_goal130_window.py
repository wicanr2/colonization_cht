#!/usr/bin/env python3
"""真視窗字幕獨立檢查器的篡改拒絕測試；不改原始收據。"""
import argparse
import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from check_goal130_window import KEY, check_pair


def expect_reject(root, mutate, label):
    with tempfile.TemporaryDirectory(prefix='goal130-window-negative-') as name:
        target = Path(name)
        for variant in ('live', 'control'):
            for extension in ('json', 'memory', 'final.idx', 'final.pal', 'final.png'):
                file = f'{variant}-82000000.{extension}'
                shutil.copy2(root / file, target / file)
        mutate(target)
        try:
            check_pair(target, 82000000, True)
        except ValueError:
            return
        raise AssertionError(f'{label} 未遭拒絕')


def change_json(target, edit):
    file = target / 'live-82000000.json'
    report = json.loads(file.read_text())
    edit(report)
    file.write_text(json.dumps(report))


def flip_byte(target, name):
    file = target / name
    raw = file.read_bytes()
    file.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reports', type=Path, required=True)
    args = p.parse_args()
    check_pair(args.reports, 82000000, True)
    cases = [
        ('RAM狀態', lambda t: change_json(t, lambda d: d['state'].update(memory_sha256='0'*64))),
        ('來源位址', lambda t: change_json(t, lambda d: next(e for e in d['events']
                            if e.get('candidate_id') == KEY).update(source_linear=0))),
        ('改色數', lambda t: change_json(t, lambda d: next(e for e in d['events']
                            if e.get('candidate_id') == KEY and e['stage'] == 'active').update(changed_pixels=1039))),
        ('字幕套用', lambda t: change_json(t, lambda d: next(x for x in d['checkpoints'][-1]['lines']
                            if x['candidate_id'] == KEY).update(applied=False))),
        ('原版索引', lambda t: flip_byte(t, 'live-82000000.final.idx')),
        ('原版色盤', lambda t: flip_byte(t, 'live-82000000.final.pal')),
        ('畫面區外像素', lambda t: paint_outside(t)),
    ]
    for label, mutate in cases:
        expect_reject(args.reports, mutate, label)
    print(f'PASS：真視窗正例與 {len(cases)} 項篡改拒絕')


def paint_outside(target):
    path = target / 'live-82000000.final.png'
    image = Image.open(path).convert('RGB')
    pixel = image.getpixel((0, 0))
    image.putpixel((0, 0), ((pixel[0]+1) % 256, pixel[1], pixel[2]))
    image.save(path)


if __name__ == '__main__':
    main()
