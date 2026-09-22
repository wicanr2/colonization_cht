#!/usr/bin/env python3
"""用獨立 Pillow 解碼核對即時 Go 合成結果，不執行或修改遊戲。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from prototype_overlay import original_image, SAFE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('/out'))
    args = parser.parse_args()
    receipt = json.loads((args.out / 'goal056-live-receipt.json').read_text())
    assert receipt['status'] == 'passed'
    checked, translated = 0, 0
    for variant, run in receipt['variants'].items():
        for point in run['checkpoints']:
            prefix = args.out / f'goal056-live-{variant}.{point["label"]}'
            raw = Path(str(prefix) + '.idx').read_bytes()
            palette = Path(str(prefix) + '.pal').read_bytes()
            assert hashlib.sha256(raw).hexdigest() == point['raw_sha256']
            assert hashlib.sha256(palette).hexdigest() == point['palette_sha256']
            base = original_image(raw, palette)
            actual = Image.open(str(prefix) + '.png').convert('RGB')
            assert actual.size == base.size
            bounds = ImageChops.difference(base, actual).getbbox()
            if point['applied']:
                assert bounds is not None and bounds[0] >= SAFE[0] and bounds[1] >= SAFE[1]
                assert bounds[2] <= SAFE[2] and bounds[3] <= SAFE[3]
                translated += 1
            else:
                assert bounds is None, (variant, point['label'], bounds)
            checked += 1
    # 使用者看過的本機原型存在時，綁定原型指紋再比較像素，不以不同PNG壓縮雜湊誤判。
    approved = args.out / 'goal055-first-zh.png'
    approved_compared = False
    if approved.is_file():
        assert hashlib.sha256(approved.read_bytes()).hexdigest() == 'ff47ad685134dae6c28951bc7a796e0bc1ded81781309cf909b31dfe36d325e7'
        a = Image.open(approved).convert('RGB')
        b = Image.open(args.out / 'goal056-live-zh.menu-clear.png').convert('RGB')
        assert a.size == b.size and ImageChops.difference(a, b).getbbox() is None
        approved_compared = True
    result = {'status': 'passed', 'images_checked': checked, 'translated_checkpoints': translated,
              'approved_prototype_pixels_equal': approved_compared,
              'note': '不套用中文者逐像素等於當下原版；套用者差異只在安全區'}
    (args.out / 'goal056-live-images.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
