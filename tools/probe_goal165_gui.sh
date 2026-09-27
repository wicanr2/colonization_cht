#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：真 Ebitengine 視窗走英國路徑到海上，往西航行遇到 Land Ho 命名框、登陸詢問與
# 蘇族三則訊息，逐一以玩家按鍵回應並擷取（目標165，規格035 通用對話框）。
set -euo pipefail

out=${COLONIZATION_GOAL165_GUI_OUT:-/repo/workplace/reports/goal165-dialog/gui-dialog}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal165-dialog/window-src/colonization-window}
atlas=${COLONIZATION_SEA_ATLAS:-/repo/workplace/reports/goal143-sea/atlas/sea-atlas.json}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-/repo/workplace/reports/goal165-dialog/atlas/dialog-atlas.json}
[[ -x "$bin" && -f "$atlas" && -d "$font_dir" && -d "$card_font_dir" && -f "$dialog_atlas" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.landho.png" ]]

"$bin" --window --all-menu --nation-card-a --sea-status-a --sea-atlas "$atlas" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" --dialog-a --dialog-atlas "$dialog_atlas" \
  --window-steps 930000000 --out "$out" > "$out.log" 2>&1 &
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
wait_step 590000000
import -window "$window" "$out.before.png"
# 往西四格到新大陸：木刻畫以 Enter 關閉，接著 Land Ho 命名框以 Enter 接受預設名稱。
for step in 600000000 615000000 630000000 645000000; do
  wait_step "$step"
  key_once KP_4
done
wait_step 675000000
enter_once
wait_step 690000000
import -window "$window" "$out.landho.png"
wait_step 695000000
enter_once
for step in 715000000 730000000 745000000 760000000 775000000 790000000 805000000 820000000; do
  wait_step "$step"
  key_once KP_4
done
wait_step 830000000
import -window "$window" "$out.landfall.png"
wait_step 835000000
key_once Down
wait_step 845000000
enter_once
wait_step 860000000
key_once KP_4
wait_step 870000000
import -window "$window" "$out.welcome.png"
wait_step 875000000
enter_once
wait_step 885000000
import -window "$window" "$out.peace.png"
wait_step 890000000
key_once KP_4
wait_step 900000000
import -window "$window" "$out.come.png"
wait_step 905000000
key_once KP_4
wait_step 920000000
import -window "$window" "$out.after.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗通用對話框現場擷取完成'
