#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗與玩家鍵鼠開遊戲選項，再以鍵盤快捷鍵 i、t 切換第1、8列（目標137）。
set -euo pipefail

out=${COLONIZATION_GOAL137_GUI_OUT:-/repo/workplace/reports/goal137-options-followups/gui-hotkey}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal136-nation-intro/window-src/colonization-window}
font=${COLONIZATION_OPTIONS_TITLE_FONT:-/repo/workplace/reports/goal133-options-rows/title-font.json}
rowfonts=${COLONIZATION_OPTIONS_ROW_FONTS:-/repo/workplace/reports/goal134-options-rows/row-fonts}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -f "$font" && -d "$rowfonts" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.options.png" && ! -e "$out.key-i.png" ]]

"$bin" --window --all-menu --nation-card-a --game-options-title-a --game-options-rows-a --root /game \
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
wait_step 1270000000
click 180 64
wait_step 1280000000
import -window "$window" "$out.options.png"
# 鍵盤快捷鍵：按住約一個畫格再放開，等原版重印與真 VGA 同步後擷取。
key_once i
wait_step 1284000000
import -window "$window" "$out.key-i.png"
wait_step 1285000000
key_once t
wait_step 1290000000
import -window "$window" "$out.key-t.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗遊戲選項快捷鍵現場擷取完成'
