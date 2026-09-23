#!/usr/bin/env python3
"""從唯一 TSV 與本機確認字型產生 Alpha 字模；只輸出本機研究產物。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from prototype_overlay import FONT_SHA, cmap_coverage
from validate_translation_draft import read_catalog, validate_sources


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, default=Path(__file__).resolve().parents[1] / 'text/draft.zh-Hant.tsv')
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--font', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--candidate', default='GAME.TXT:0x000001B0',
                   choices=['GAME.TXT:0x000001B0', 'GAME.TXT:0x000001CB',
                            'GAME.TXT:0x000001E4', 'GAME.TXT:0x000001F9', 'GAME.TXT:0x00000204',
                            'LABELS.TXT:0x00000888', 'LABELS.TXT:0x00000890',
                            'LABELS.TXT:0x0000086E', 'GAME.TXT:0x00000A7A'],
                   help='規格 009／012／014／015 已審查的畫面文字；字模各自獨立綁定')
    args = p.parse_args()
    rows = read_catalog(args.catalog)
    if any(not (args.game / row['source_file']).is_file() for row in rows):
        print('SKIP：缺少合法原版，未產生字模')
        return 77
    validate_sources(rows, args.game)
    key = args.candidate
    text = next(r['zh_hant'] for r in rows if r['candidate_id'] == key)
    if key == 'GAME.TXT:0x00000A7A':
        if not text.startswith('^^') or '^' in text[2:]:
            raise ValueError('姓名提示控制碼不符')
        text = text[2:]
    data = args.font.read_bytes()
    if hashlib.sha256(data).hexdigest() != FONT_SHA:
        raise ValueError('字型指紋不符已確認版本')
    coverage = cmap_coverage(data)
    if any(ord(c) not in coverage for c in text):
        raise ValueError('譯文含缺字，不產生部分字模')
    sizes = {'LABELS.TXT:0x00000888': 34,
             'LABELS.TXT:0x00000890': 38,
             'GAME.TXT:0x00000A7A': 38}
    font_size = sizes.get(key, 24)
    font = ImageFont.truetype(str(args.font), font_size)
    left, top, right, bottom = font.getbbox(text)
    width, height = right - left, bottom - top
    expected_ink = {'LABELS.TXT:0x00000888': (74, 32),
                    'LABELS.TXT:0x00000890': (82, 35),
                    'GAME.TXT:0x00000A7A': (328, 35)}
    if key in expected_ink and (width, height) != expected_ink[key]:
        raise ValueError('此欄字模尺寸不符已驗證規格')
    bounds = {'LABELS.TXT:0x00000888': (148, 48),
              'LABELS.TXT:0x00000890': (304, 52),
              'LABELS.TXT:0x0000086E': (380, 36),
              'GAME.TXT:0x00000A7A': (476, 52)}
    max_width, max_height = bounds.get(key, (584, 28))
    if not (0 < width <= max_width and 0 < height <= max_height):
        raise ValueError('譯文超出已確認安全矩形，不裁切')
    mask = Image.new('L', (width, height))
    ImageDraw.Draw(mask).text((-left, -top), text, fill=255, font=font)
    receipt = {'candidate_id': key, 'translation_sha256': hashlib.sha256(text.encode()).hexdigest(),
               'catalog_sha256': hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
               'font_sha256': FONT_SHA, 'font_size': font_size, 'width': width, 'height': height,
               'alpha': base64.b64encode(mask.tobytes()).decode(),
               'scope': 'local-only；衍生字模不加入 Git 或散布包'}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False) + '\n')
    print(f'本機字模已產生：{key}，{width}×{height}；字型及譯文指紋已綁定')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
