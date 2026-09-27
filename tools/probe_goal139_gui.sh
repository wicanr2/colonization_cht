#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗與玩家鍵鼠翻開第三張難度卡，擷取中文、游標壓欄與離頁（目標139）。
set -euo pipefail

out=${COLONIZATION_GOAL139_GUI_OUT:-/repo/workplace/reports/goal139-third-card/gui-third}
third_fonts=${COLONIZATION_THIRD_CARD_FONTS:-/repo/workplace/reports/goal139-third-card/fonts}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal139-third-card/window-src/colonization-window}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$third_fonts" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.card.png" && ! -e "$out.hover.png" && ! -e "$out.nation.png" ]]

"$bin" --window --all-menu --nation-card-a --third-card-a --third-card-font-dir "$third_fonts" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 46000000 --out "$out" > "$out.log" 2>&1 &
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
# 第三張卡邏輯 (55,145)；點完等步數前進再移開，避免游標守門擋住。
click 220 580
wait_step 33500000
move_to 64 64
wait_step 37000000
import -window "$window" "$out.card.png"
# 游標只壓上欄：該欄應回英文。
move_to 220 528
wait_step 38500000
import -window "$window" "$out.hover.png"
move_to 64 64
wait_step 40000000
import -window "$window" "$out.away.png"
# 點第二張卡離開難度頁；第三張卡中文必須隨頁撤銷。
click 1060 220
move_to 64 64
wait_step 45000000
import -window "$window" "$out.nation.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗第三張難度卡現場擷取完成'
