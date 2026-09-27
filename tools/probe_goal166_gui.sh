#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：真 Ebitengine 視窗走英國路徑，擷取載入訊息、主選單版本字串、國王接見，
# 到海上後點開 GAME 下拉選單再按 Esc 關閉（目標166，規格036 與規格034 補充）。
set -euo pipefail

out=${COLONIZATION_GOAL166_GUI_OUT:-/repo/workplace/reports/goal166-spots/gui-spots}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal166-spots/window-src/colonization-window}
atlas=${COLONIZATION_SEA_ATLAS:-/repo/workplace/reports/goal143-sea/atlas/sea-atlas.json}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-/repo/workplace/reports/goal166-spots/atlas/dialog-atlas.json}
static_masks=${COLONIZATION_STATIC_MASKS:-/repo/workplace/reports/goal166-spots/static-masks}
[[ -x "$bin" && -f "$atlas" && -d "$font_dir" && -d "$card_font_dir" && -f "$dialog_atlas" && -d "$static_masks" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.king.png" && ! -e "$out.shots" ]]

"$bin" --window --all-menu --nation-card-a --sea-status-a --sea-atlas "$atlas" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" --dialog-a --dialog-atlas "$dialog_atlas" \
  --static-credits-a --static-mask-dir "$static_masks" --window-steps 630000000 --out "$out" > "$out.log" 2>&1 &
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
# 截圖時記下當下原版步數；重播以同一步數取檢查點，檢查器讀同一份清單。
shot() {
  local s
  s=$(gui_step)
  import -window "$window" "$out.$1.png"
  echo "$1 $s" >> "$out.shots"
}


wait_step 3000000
enter_once
wait_step 12000000
click 640 400
wait_screen loading 300000
shot loading
wait_screen menu 1500000
shot mainmenu
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
wait_step 67500000
shot king
wait_step 75000000
enter_once
wait_step 85000000
enter_once
# 回合開始訊息佔用頂列，之後原版重印選單列。
wait_step 600000000
click 92 12
move_to 300 400
wait_step 612000000
shot gamemenu
wait_step 620000000
key_once Escape
wait_step 625000000
shot after
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗四處動態文字現場擷取完成'
