#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗與玩家鍵鼠選 Discoverer 難度走英格蘭路徑，擷取首則教學提示、游標壓字與按 Enter 關閉（目標142）。
set -euo pipefail

out=${COLONIZATION_GOAL142_GUI_OUT:-/repo/workplace/reports/goal142-help/gui-help}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal142-help/window-src/colonization-window}
help_masks=${COLONIZATION_HELP_MASKS:-/repo/workplace/reports/goal142-help/fonts}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$help_masks" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.help.png" ]]

"$bin" --window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$help_masks" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 640000000 --out "$out" > "$out.log" 2>&1 &
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
# 第一張難度卡（Discoverer）：原版只在此難度預設開啟教學提示。
click 640 220
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
wait_step 575000000
import -window "$window" "$out.help.png"
# 游標壓在 help 文字上：只有游標範圍回原版像素，其餘中文保留。
move_to 400 480
wait_step 585000000
import -window "$window" "$out.cursor.png"
move_to 64 64
wait_step 592000000
import -window "$window" "$out.away.png"
wait_step 600000000
enter_once
wait_step 620000000
import -window "$window" "$out.closed.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗首則教學提示現場擷取完成'
