#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以真 Ebitengine 視窗、玩家鍵鼠抵達首張字幕並擷取現場畫面。
set -euo pipefail

out=${COLONIZATION_GOAL130_OUT:-/repo/workplace/reports/goal130-build1/gui-real}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal130-build1/window-src/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
caption_font=${COLONIZATION_BUILD1_FONT:-/repo/workplace/reports/goal130-build1/goal130-build1-font.json}
[[ -x "$bin" && -d "$font_dir" && -d "$card_font_dir" && -f "$caption_font" ]]
[[ -f /game/GAME.TXT && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.caption.png" ]]

"$bin" --window --all-menu --nation-card-a --build1-a --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" --build1-font "$caption_font" \
  --window-steps 84000000 --out "$out" > "$out.log" 2>&1 &
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
wait_step 82000000
import -window "$window" "$out.caption.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗首張字幕現場擷取完成'
