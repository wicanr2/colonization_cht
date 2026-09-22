#!/usr/bin/env python3
"""獨立解碼五列合成圖，逐列驗證回退與安全區，不以執行器自己的合成結果作預期。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from prototype_overlay import original_image
from probe_multi_menu import KEYS


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=Path('/out'))
    args = p.parse_args()
    receipt = json.loads((args.out / 'goal057-live-receipt.json').read_text())
    if receipt['status'] != 'passed':
        raise ValueError('正常路徑收據未通過')
    regions = {key: (344, y * 4, 928, (y + 7) * 4)
               for key, y in zip(KEYS, [107, 115, 123, 131, 139])}
    lifecycle = json.loads((args.out / 'goal056-lifecycle-analysis.json').read_text())
    evidence = {}
    for key, event in zip(KEYS, lifecycle['events'][1:6]):
        prefix = args.out / Path(event['capture']).name
        before = Path(str(prefix) + '.before').read_bytes()
        after = Path(str(prefix) + '.after').read_bytes()
        if hashlib.sha256(before).hexdigest() != event['before_sha256'] or hashlib.sha256(after).hexdigest() != event['after_sha256']:
            raise ValueError('原始事件畫布雜湊不符')
        mask = json.loads((args.out / 'goal057-fonts' / (key.replace(':', '-') + '.json')).read_text())
        evidence[key] = (before, event['changed_indices'], mask)
    checked = applied = 0
    for variant, run in receipt['variants'].items():
        for point in run['checkpoints']:
            prefix = args.out / f'goal057-live-{variant}.{point["label"]}'
            raw = Path(str(prefix) + '.idx').read_bytes()
            palette = Path(str(prefix) + '.pal').read_bytes()
            if hashlib.sha256(raw).hexdigest() != point['raw_sha256'] or hashlib.sha256(palette).hexdigest() != point['palette_sha256']:
                raise ValueError('檢查點原圖雜湊不符')
            base = original_image(raw, palette)
            actual = Image.open(str(prefix) + '.png').convert('RGB')
            if actual.size != base.size:
                raise ValueError('尺寸不符')
            remaining = ImageChops.difference(actual, base)
            restored = bytearray(raw)
            for line in point['lines']:
                rect = regions[line['candidate_id']]
                changed = remaining.crop(rect).getbbox() is not None
                if changed != line['applied']:
                    raise ValueError(f'{variant}/{point["label"]}/{line["candidate_id"]} 回退或顯示不符')
                if line['applied']:
                    applied += 1
                    before, indices, _ = evidence[line['candidate_id']]
                    for index in indices:
                        restored[index] = before[index]
                remaining.paste((0, 0, 0), rect)
            if remaining.getbbox() is not None:
                raise ValueError('安全區外像素變動')
            expected = original_image(bytes(restored), palette)
            color = tuple((v << 2) | (v >> 4) for v in palette[254 * 3:254 * 3 + 3])
            for line in point['lines']:
                if line['applied']:
                    _, _, mask = evidence[line['candidate_id']]
                    alpha = Image.frombytes('L', (mask['width'], mask['height']), base64.b64decode(mask['alpha']))
                    expected.paste(color, regions[line['candidate_id']][:2], alpha)
            if ImageChops.difference(expected, actual).getbbox() is not None:
                raise ValueError(f'{variant}/{point["label"]} 背景還原或中文字模像素不符獨立合成')
            checked += 1
    # 已確認第一列不得因擴展四列而改變外觀。
    old = Image.open(args.out / 'goal056-live-zh.menu-clear.png').convert('RGB')
    new = Image.open(args.out / 'goal057-live-zh.menu-clear.png').convert('RGB')
    if ImageChops.difference(old.crop(regions[KEYS[0]]), new.crop(regions[KEYS[0]])).getbbox():
        raise ValueError('原首列外觀退步')
    result = {'status': 'passed', 'images_checked': checked, 'applied_line_checkpoints': applied,
              'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'first_line_pixels_unchanged': True,
              'note': '各回退列與當下原版逐像素相等，所有中文差異只落在各列安全框'}
    (args.out / 'goal057-live-images.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
