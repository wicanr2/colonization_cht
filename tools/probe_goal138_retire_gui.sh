#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗走到海上，開 GAME → Retire 確認框，擷取三欄中文，再點 No 關框（目標138）。
set -euo pipefail

out=${COLONIZATION_GOAL138_GUI_OUT:-/repo/workplace/reports/goal138-retire/gui-retire}
retire_fonts=${COLONIZATION_RETIRE_FONTS:-/repo/workplace/reports/goal138-retire/fonts}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal138-retire/window-src/colonization-window}
font=${COLONIZATION_OPTIONS_TITLE_FONT:-/repo/workplace/reports/goal133-options-rows/title-font.json}
rowfonts=${COLONIZATION_OPTIONS_ROW_FONTS:-/repo/workplace/reports/goal134-options-rows/row-fonts}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -f "$font" && -d "$rowfonts" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.options.png" && ! -e "$out.dialog.png" && -d "$retire_fonts" ]]

"$bin" --window --all-menu --nation-card-a --game-options-title-a --game-options-rows-a --retire-a --retire-font-dir "$retire_fonts" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" --game-options-title-font "$font" \
  --game-options-rows-font-dir "$rowfonts" \
  --window-steps 1292000000 --out "$out" > "$out.log" 2>&1 &
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
wait_step 85000000
enter_once

# 對齊已驗錄製輸入：1225M 左移、1250M 開 GAME、1270M 點 Game Options。
wait_step 1225000000
key_once Left
wait_step 1250000000
click 92 12
wait_step 1260000000
# GAME 選單的 Retire（原版座標約 38,104）。
click 152 416
wait_step 1262000000  # 等步數前進再移開，避免與按下同批送達
move_to 800 700
wait_step 1275000000
import -window "$window" "$out.dialog.png"
# 點 No（原版座標約 131,118）：先停留再按住。
move_to 524 472
wait_step 1280000000
gui_act $GUI_HOLD_STEPS xdotool mousedown 1
wait_step 1280600000
gui_act $((2 * GUI_UPDATE_STEPS)) xdotool mouseup 1
wait_step 1281200000
move_to 800 700
wait_step 1290000000
import -window "$window" "$out.closed.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗退休確認框現場擷取完成'
