#!/usr/bin/env bash
# 規格009–020：從真 TSV 與固定 Cubic 11 重建目前正式畫面的14個本機字模。
set -euo pipefail

out=${COLONIZATION_GOAL084_FONT_OUT:-/repo/workplace/reports/goal084-fonts-full}
catalog=/repo/text/draft.zh-Hant.tsv
font=/font/Cubic_11.ttf
[[ -d "$out" && -d /game && -f "$catalog" && -f "$font" ]]
[[ -z "$(find "$out" -maxdepth 1 -type f -name '*.json' -print -quit)" ]]

for key in \
  GAME.TXT:0x000001B0 GAME.TXT:0x000001CB GAME.TXT:0x000001E4 \
  GAME.TXT:0x000001F9 GAME.TXT:0x00000204 \
  LABELS.TXT:0x00000888 LABELS.TXT:0x00000890 LABELS.TXT:0x0000086E; do
  python3 /repo/tools/bake_local_font.py --catalog "$catalog" --game /game \
    --font "$font" --candidate "$key" --output "$out/${key//:/-}.json"
done
python3 /repo/tools/bake_card_fonts.py --catalog "$catalog" --game /game \
  --font "$font" --output "$out"
[[ "$(find "$out" -maxdepth 1 -type f -name '*.json' | wc -l)" -eq 14 ]]
echo '14 欄本機字模完成'
