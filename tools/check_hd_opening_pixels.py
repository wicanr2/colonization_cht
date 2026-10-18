#!/usr/bin/env python3
"""規格069 R82：從原PNG與獨立原版來源模型核對開場RGBA；只在非root Docker執行。"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import struct

from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def mapped(image, box, size):
    x0, y0, x1, y1 = box
    w, h = size
    result = Image.new('RGBA', size)
    source, target = image.load(), result.load()
    xs = [x0 + (2*x+1)*(x1-x0)//(2*w) for x in range(w)]
    for y in range(h):
        sy = y0 + (2*y+1)*(y1-y0)//(2*h)
        for x, sx in enumerate(xs):
            target[x, y] = source[sx, sy]
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('assets', 'model', 'formal', 'decoded', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--gui', action='store_true')
    args = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.geteuid() != 0
    assert args.output.resolve().is_relative_to('/out') and not args.output.exists()
    assert args.output.parent.stat().st_uid == os.getuid()
    manifest = read(args.assets/'manifest.json')
    assert manifest['schema'] == 1
    arts = {1: Image.new('RGBA', (1280, 800)), 2: Image.new('RGBA', (3840, 528))}
    selected = {}
    for name, item in manifest['assets'].items():
        source = item.get('original_source', {})
        if source.get('file') not in ('OPENBORD.PIK', 'OPENING.PIK'):
            continue
        path = args.assets/name
        assert path.is_file() and not path.is_symlink() and sha(path) == item['sha256']
        image = Image.open(path).convert('RGBA')
        assert list(image.size) == item['size']
        kind = 1 if source['file'] == 'OPENBORD.PIK' else 2
        opaque = name in ('openbord-000.png', 'opening-000.png')
        if opaque:
            assert image.getchannel('A').getextrema() == (255, 255)
        else:
            assert image.getchannel('A').getextrema()[0] == 0
        for native, generated in zip(item['native_display_rects'], item['generated_display_rects']):
            x0, y0, x1, y1 = native
            assert 0 <= x0 < x1 <= arts[kind].width//4 and 0 <= y0 < y1 <= arts[kind].height//4
            piece = mapped(image, generated, ((x1-x0)*4, (y1-y0)*4))
            if opaque:
                arts[kind].paste(piece, (x0*4, y0*4))
            else:
                arts[kind].alpha_composite(piece, (x0*4, y0*4))
        selected[name] = item['sha256']
    assert len(selected) == 13 and all(im.getchannel('A').getextrema() == (255, 255) for im in arts.values())
    arts = {k: v.tobytes() for k, v in arts.items()}
    native = {1: (args.decoded/'1092.idx').read_bytes(), 2: (args.decoded/'1179.idx').read_bytes()}
    assert hashlib.sha256(native[1]).hexdigest() == 'ee23b1d787958481210fb6c328ccc067805bdbd8d83300c5d8157dd40cf90816'
    assert hashlib.sha256(native[2]).hexdigest() == '9aa042dfb838820ea8d7d1c9953478f44dd7d8f85db4d5cc4aa0bb9bb0006b95'
    points = {v['step']: v for v in read(args.model/'model.json')['points']}
    states = {v['step']: v for v in read(args.model/'check.json')['points']}
    if args.gui:
        capture = read(args.formal/'capture.json')
        samples = capture['samples']
    else:
        formal = read(args.formal/'check.json')
        samples = [{'label': path.stem, 'graphics': 'hd', 'state': {'step': int(path.stem[6:])}, 'image': str(path)}
                   for path in sorted(args.formal.glob('point-*.png'))]
        assert len(formal['records']) == len(points)
    totals, results = collections.Counter(), []
    for sample in samples:
        step = sample['state']['step']
        state, point = states[step], points[step]
        actual = Image.open(sample['image']).convert('RGBA')
        assert actual.size == (1280, 800)
        if args.gui:
            for key in ('memory_sha256', 'indexed_sha256', 'palette_sha256', 'registers', 'segments', 'ip', 'flags'):
                assert sample['state'][key] == state[key], (sample['label'], key)
            shot = Image.open(sample['x11']).convert('RGBA').crop((0, 48, 1280, 848))
            assert shot.tobytes() == actual.tobytes()
            totals['x11_rgba'] += 1280*800
            if sample['scene_label'] != 'opening':
                assert sample.get('native_live', {}).get('hd', {}).get('opening_picture', {}).get('painted', 0) == 0
                results.append({'label': sample['label'], 'step': step, 'opening_painted': 0, 'scope': 'exit and X11 only; main-menu translations inherit their own checks'})
                continue
            assert not sample['native_live'].get('items')
        stem = 'point-%08d' % step
        indexed = (args.model/(stem+'.idx')).read_bytes()
        palette = (args.model/(stem+'.palette')).read_bytes()
        memory = (args.model/(stem+'.memory')).read_bytes()
        assert hashlib.sha256(indexed).hexdigest() == state['indexed_sha256']
        assert hashlib.sha256(memory).hexdigest() == state['memory_sha256']
        original = Image.frombytes('P', (320, 200), indexed)
        original.putpalette([v << 2 | v >> 4 for v in palette])
        expected = bytearray(original.convert('RGBA').resize((1280, 800), Image.Resampling.NEAREST).tobytes())
        cells = list(struct.iter_unpack('<BIB', (args.model/point['owners_file']).read_bytes()))
        assert len(cells) == 64000
        masks, counts = [bytearray(8000), bytearray(8000)], collections.Counter()
        for at, (kind, local, value) in enumerate(cells):
            if kind:
                assert kind in native and local < len(native[kind]) and native[kind][local] == value == memory[115760+at]
            if not kind or not point['paintable'] or sample['graphics'] == 'original':
                counts['original_rgba'] += 16
                continue
            assert indexed[at] == value
            width = 320 if kind == 1 else 960
            sx, sy, x, y = local % width*4, local//width*4, at % 320*4, at//320*4
            for dy in range(4):
                dst, src = ((y+dy)*1280+x)*4, ((sy+dy)*width*4+sx)*4
                expected[dst:dst+16] = arts[kind][src:src+16]
            masks[kind-1][at >> 3] |= 1 << (at & 7)
            counts['border_rgba' if kind == 1 else 'map_rgba'] += 16
        assert actual.tobytes() == expected, (sample['label'], 'RGBA differs')
        if args.gui and sample['graphics'] == 'hd':
            import base64
            receipt = sample['native_live']['hd']['opening_picture']
            assert [base64.b64decode(v) for v in receipt['masks']] == [bytes(v) for v in masks]
            assert receipt['border_painted']*16 == counts['border_rgba'] and receipt['map_painted']*16 == counts['map_rgba']
        totals.update(counts)
        totals['full_rgba'] += 1280*800
        results.append({'label': sample['label'], 'step': step, 'paintable': point['paintable'], 'counts': dict(counts)})
    assert totals['border_rgba'] > 0 and totals['map_rgba'] > 0
    report = {'result': 'PASS_OPENING_INDEPENDENT_GUI_PIXELS' if args.gui else 'PASS_OPENING_INDEPENDENT_NATIVE_PIXELS',
              'raw_assets': selected, 'manifest_sha256': sha(args.assets/'manifest.json'),
              'source_model_sha256': sha(args.model/'model.json'), 'totals': dict(totals), 'samples': results,
              'scope': 'Canonical-palette opening PIK only. Unknown foreground preserved. No animation, fade, full-HD or release claim.'}
    args.output.mkdir()
    (args.output/'check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(report['result'], dict(totals))


if __name__ == '__main__':
    main()
