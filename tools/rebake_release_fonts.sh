#!/usr/bin/env bash
# 在 font/README.md 指定的 rich2-py 固定映像內，以現行譯稿重烘既有正式欄位。
# /game 與 /font 唯讀；/font/Cubic_11.ttf 的 SHA-256 由各烘製器核對。
# 不改既定字級或版面；輸出為 workplace 的封裝中間物，不是正式交付。
set -euo pipefail
out=${COLONIZATION_RELEASE_FONTS:-/repo/workplace/reports/goal178-orders/release-fonts}
font=/font/Cubic_11.ttf
[[ -f /game/OPENING.EXE && -f "$font" && ! -e "$out" ]]
[[ -d "$(dirname "$out")" && "$(stat -c %u "$(dirname "$out")")" == "$(id -u)" ]]
mkdir -p "$out"/{row-fonts,retire,captions}
cd /repo/tools
python3 bake_local_font.py --game /game --font "$font" --candidate GAME.TXT:0x000004CD --output "$out/title-font.json"
python3 bake_local_font.py --game /game --font "$font" --candidate GAME.TXT:0x000153CC --output "$out/build1-font.json"
for key in 0x000004E9 0x000004FD 0x00000512 0x00000525 0x00000533 0x0000053E 0x00000550 0x00000566; do
  python3 bake_local_font.py --game /game --font "$font" --candidate "GAME.TXT:$key" --output "$out/row-fonts/GAME.TXT-$key.json"
done
for key in 0x00000122 0x00000141 0x00000146; do
  python3 bake_local_font.py --game /game --font "$font" --candidate "GAME.TXT:$key" --output "$out/retire/GAME.TXT-$key.json"
done
python3 bake_build_captions.py --game /game --font "$font" --output "$out/captions"
touch "$out/done"
