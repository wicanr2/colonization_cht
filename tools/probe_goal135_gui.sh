#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以真 Ebitengine 視窗、玩家鍵鼠抵達英格蘭介紹 A、B 頁並擷取現場畫面（規格025）。
set -euo pipefail

out=${COLONIZATION_GOAL135_OUT:-/repo/workplace/reports/goal135-nation-intro/gui-real}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal135-nation-intro/window-src/colonization-window}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
masks=${COLONIZATION_INTRO_MASKS:-/repo/workplace/reports/goal135-nation-intro/masks}
[[ -x "$bin" && -d "$font_dir" && -d "$card_font_dir" && -d "$masks" ]]
[[ -f /game/GAME.TXT && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.page-a.png" && ! -e "$out.page-b.png" ]]

"$bin" --window --all-menu --nation-card-a --england-intro-a --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$masks" \
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
click 220 200
wait_step 46000000
click 260 736
move_to 64 64
wait_step 53000000
import -window "$window" "$out.page-a.png"
wait_step 55000000
enter_once
wait_step 61000000
import -window "$window" "$out.page-b.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗英格蘭介紹兩頁現場擷取完成'
