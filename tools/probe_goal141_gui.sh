#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗與玩家鍵鼠走英格蘭路徑，介紹頁後不再按鍵，擷取十張開場字幕（目標141）。
set -euo pipefail

out=${COLONIZATION_GOAL141_GUI_OUT:-/repo/workplace/reports/goal141-captions/gui-captions}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal141-captions/window-src/colonization-window}
caption_fonts=${COLONIZATION_CAPTION_FONTS:-/repo/workplace/reports/goal141-captions/fonts}
build1_font=${COLONIZATION_BUILD1_FONT:-/repo/workplace/reports/goal133-options-rows/build1-font.json}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$caption_fonts" && -f "$build1_font" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.cp-110000000.png" ]]

"$bin" --window --all-menu --nation-card-a --build1-a --build1-font "$build1_font" \
  --build-captions-a --build-caption-font-dir "$caption_fonts" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 1225000000 --out "$out" > "$out.log" 2>&1 &
game_pid=$!
trap 'kill "$game_pid" 2>/dev/null || true; wait "$game_pid" 2>/dev/null || true' EXIT

window=""
for ((i=0; i<100; i++)); do
  window=$(xdotool search --name 'Colonization CHT prototype' 2>/dev/null | head -1 || true)
  [[ -n "$window" ]] && break
  sleep .1
done
[[ -n "$window" ]]
xdotool windowfocus "$window"
source "$(dirname "$0")/gui_step_input.sh"


wait_step 3000000
enter_once
wait_step 12000000
click 640 400
wait_stage menu
move_to 64 64
click 512 440
wait_stage difficulty
move_to 64 64
wait_step 32000000
click 1060 220
wait_step 40000000
click 220 332
wait_step 43500000
click 220 200
wait_step 46000000
click 260 736
move_to 64 64
wait_step 55000000
enter_once
wait_step 65000000
enter_once
wait_step 75000000
enter_once
# 介紹 B 頁後不再按鍵：任何按鍵都會讓原版在第四張後跳過其餘字幕（目標141探針）。
for cp in 110000000 238000000 348000000 484000000 590000000 699000000 807000000 915000000 1024000000 1132000000; do
  wait_step "$cp"
  import -window "$window" "$out.cp-$cp.png"
done
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗十張開場字幕現場擷取完成'
