#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：真 Ebitengine 視窗走英國路徑到海上，實按數字鍵盤移動與 F1 報告，再按 Esc 返回（目標163）。
set -euo pipefail

out=${COLONIZATION_GOAL163_GUI_OUT:-/repo/workplace/reports/goal163-keys/gui-keys}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal163-keys/window-src/colonization-window}
atlas=${COLONIZATION_SEA_ATLAS:-/repo/workplace/reports/goal143-sea/atlas/sea-atlas.json}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -f "$atlas" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.kp8.png" ]]

"$bin" --window --all-menu --nation-card-a --sea-status-a --sea-atlas "$atlas" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 720000000 --out "$out" > "$out.log" 2>&1 &
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
# 回合開始訊息佔用頂列，之後原版重印選單列。
wait_step 565000000
import -window "$window" "$out.title.png"
wait_step 590000000
import -window "$window" "$out.before.png"
wait_step 600000000
key_once KP_8
wait_step 612000000
import -window "$window" "$out.kp8.png"
wait_step 620000000
key_once KP_7
wait_step 640000000
import -window "$window" "$out.kp7.png"
wait_step 650000000
key_once F1
wait_step 670000000
import -window "$window" "$out.f1.png"
wait_step 690000000
key_once Escape
wait_step 705000000
import -window "$window" "$out.back.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗功能鍵與數字鍵盤現場擷取完成'
