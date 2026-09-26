#!/usr/bin/env bash
# 只在有界 Docker 內：目標157 以現行 TSV 重烘改稿影響的正式欄位字模（遊戲選項九欄、首張字幕、退休框、
# 其餘九張字幕、第一張旗卡、四國介紹、@TUTORIAL1、海上圖集）；輸出到 $out，不覆寫既有目錄。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL157_FONTS:-$r/goal157-reverify/fonts}
font=/font/Cubic_11.ttf
[[ -f /game/OPENING.EXE && -f "$font" && ! -e "$out/done" ]]
mkdir -p "$out"/{row-fonts,retire,captions,card,help,atlas}
cd /repo/tools
python3 bake_local_font.py --game /game --font "$font" --candidate GAME.TXT:0x000004CD --output "$out/title-font.json"
python3 bake_local_font.py --game /game --font "$font" --candidate GAME.TXT:0x000153CC --output "$out/build1-font.json"
for k in 0x000004E9 0x000004FD 0x00000512 0x00000525 0x00000533 0x0000053E 0x00000550 0x00000566; do
  python3 bake_local_font.py --game /game --font "$font" --candidate "GAME.TXT:$k" --output "$out/row-fonts/GAME.TXT-$k.json"
done
for k in 0x00000122 0x00000141 0x00000146; do
  python3 bake_local_font.py --game /game --font "$font" --candidate "GAME.TXT:$k" --output "$out/retire/GAME.TXT-$k.json"
done
python3 bake_build_captions.py --game /game --font "$font" --output "$out/captions"
python3 bake_nation_card_a_from_font.py --catalog /repo/text/nation-card-fragments.zh-Hant.tsv --game /game --font "$font" --output "$out/card"
python3 bake_help_masks.py --game /game --font "$font" --output "$out/help"
python3 bake_sea_atlas.py --game /game --font "$font" --output "$out/atlas"
mkdir -p "$out/intro"
for n in england france spain netherlands; do
  python3 bake_nation_intro_masks.py --game /game --catalog /repo/text/nation-introduction.zh-Hant.tsv --font "$font" \
    --old "$r/goal101-intro" --reports "$r/goal102-intro" --output "$out/intro" --nation "$n"
done
touch "$out/done"
echo '目標157重烘完成'
