#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗走到海上，開 GAME → Save Game，逐段擷取存檔對話框（目標137 探索；寫入只落在可寫暫存層）。
set -euo pipefail

out=${COLONIZATION_GOAL137_GUI_OUT:-/repo/workplace/reports/goal137-options-followups/save-explore}
scratch=${COLONIZATION_SCRATCH:-/repo/workplace/reports/goal137-options-followups/scratch}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal137-options-followups/window-src/colonization-window}
font=${COLONIZATION_OPTIONS_TITLE_FONT:-/repo/workplace/reports/goal133-options-rows/title-font.json}
rowfonts=${COLONIZATION_OPTIONS_ROW_FONTS:-/repo/workplace/reports/goal134-options-rows/row-fonts}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -f "$font" && -d "$rowfonts" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.options.png" && ! -e "$out.key-i.png" && -d "$scratch" ]]

"$bin" --window --all-menu --nation-card-a --game-options-title-a --game-options-rows-a --scratch "$scratch" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" --game-options-title-font "$font" \
  --game-options-rows-font-dir "$rowfonts" \
  --window-steps 1320000000 --out "$out" > "$out.log" 2>&1 &
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

wait_step() {
  local step=""
  for ((i=0; i<72000; i++)); do  # 並行時模擬較慢，單次等待上限兩小時
    kill -0 "$game_pid"
    step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true)
    if [[ -n "$step" && "$step" -ge "$1" ]]; then return; fi
    sleep .1
  done
  echo "等待原版步數 $1 逾時；最後 ${step:-無}" >&2
  return 1
}
wait_stage() {
  for ((i=0; i<900; i++)); do
    kill -0 "$game_pid"
    if grep -q '"stage": "'"$1"'"' "$out.status.json" 2>/dev/null; then return; fi
    sleep .1
  done
  return 1
}
click() {
  xdotool mousemove --window "$window" "$1" "$2"
  sleep .2
  xdotool mousedown 1
  sleep .2
  xdotool mouseup 1
}
enter_once() {
  xdotool keydown Return
  sleep .2
  xdotool keyup Return
}

wait_step 3000000
enter_once
wait_step 12000000
click 640 400
wait_stage menu
xdotool mousemove --window "$window" 64 64
click 512 440
wait_stage difficulty
xdotool mousemove --window "$window" 64 64
wait_step 32000000
click 1060 220
wait_step 40000000
click 220 332
wait_step 43500000
click 220 200
wait_step 46000000
click 260 736
xdotool mousemove --window "$window" 64 64
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
xdotool keydown Left
sleep .2
xdotool keyup Left
wait_step 1250000000
click 92 12
wait_step 1260000000
# GAME 選單的 Save Game（原版座標約 35,63）。
click 140 254
wait_step 1261000000  # 等步數前進再移開，避免與按下同批送達
xdotool mousemove --window "$window" 640 700
for step in 1265000000 1275000000 1285000000; do
  wait_step "$step"
  import -window "$window" "$out.$((step / 1000000))m.png"
done
enter_once
for step in 1295000000 1305000000 1315000000; do
  wait_step "$step"
  import -window "$window" "$out.$((step / 1000000))m.png"
done
wait "$game_pid"
trap - EXIT
echo '存檔對話框探索完成'
