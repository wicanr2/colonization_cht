#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗與玩家鍵鼠依序選法國、西班牙、荷蘭旗卡，擷取中文、游標壓欄與離頁（目標140）。
set -euo pipefail

out=${COLONIZATION_GOAL140_GUI_OUT:-/repo/workplace/reports/goal140-nation-cards/gui-cards}
rest_fonts=${COLONIZATION_REST_CARD_FONTS:-/repo/workplace/reports/goal140-nation-cards/fonts}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal140-nation-cards/window-src/colonization-window}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$rest_fonts" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.france.png" && ! -e "$out.name.png" ]]

"$bin" --window --all-menu --nation-card-a --nation-cards-rest-a --nation-cards-rest-font-dir "$rest_fonts" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 62000000 --out "$out" > "$out.log" 2>&1 &
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
# 選國頁：先停在旗卡上，再按住、放開、移開（目標136已驗節奏），畫面穩定後擷取。
pick() {  # 四倍座標 x y 起始百萬步 截圖名
  local base=$3
  wait_step "${base}000000"
  move_to "$1" "$2"
  wait_step "${base}500000"
  gui_act $GUI_HOLD_STEPS xdotool mousedown 1
  wait_step "$((base + 1))000000"
  gui_act $((2 * GUI_UPDATE_STEPS)) xdotool mouseup 1
  wait_step "$((base + 1))500000"
  move_to 64 64
  wait_step "$((base + 2))500000"
  import -window "$window" "$out.$4.png"
}
pick 1020 200 44 france
pick 620 580 47 spain
pick 1020 580 50 netherlands
# 游標只壓荷蘭上欄：該欄回英文、下欄維持中文。
wait_step 53000000
move_to 1020 424
wait_step 54000000
import -window "$window" "$out.cursor.png"
move_to 64 64
wait_step 55500000
import -window "$window" "$out.away.png"
# 點左下完成提示離開選國頁，三張旗卡中文都必須撤銷。
wait_step 56000000
click 260 736
move_to 64 64
wait_step 60000000
import -window "$window" "$out.name.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗其餘三張旗卡現場擷取完成'
