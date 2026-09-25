#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：可寫暫存層放入既有存檔，冷啟動主選單「載入遊戲」後分段擷取，並開遊戲選項（目標137）。
set -euo pipefail

out=${COLONIZATION_GOAL137_GUI_OUT:-/repo/workplace/reports/goal137-options-followups/load-explore}
scratch=${COLONIZATION_SCRATCH:-/repo/workplace/reports/goal137-options-followups/load-scratch}
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
  --window-steps 130000000 --out "$out" > "$out.log" 2>&1 &
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
now_step() { sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" | tail -1; }
wait_after() { wait_step $(( $(now_step) + $1 )); }
# 主選單出現時點不固定；以目前步數為基準。第4列「載入遊戲」須先停留再按住，否則只反白不選取。
xdotool mousemove --window "$window" 440 536
wait_after 1000000
xdotool mousedown 1
wait_after 500000
xdotool mouseup 1
wait_after 500000
xdotool mousemove --window "$window" 64 64
wait_after 4000000
import -window "$window" "$out.load-list.png"
enter_once
for n in 1 2 3 4; do
  wait_after 8000000
  import -window "$window" "$out.after-$n.png"
done
# 讀檔後會停在「Loaded ... successfully.」訊息框，需一鍵關閉才回到海上。
enter_once
wait_after 6000000
click 92 12
wait_after 8000000
click 180 64
wait_after 10000000
import -window "$window" "$out.options.png"
wait "$game_pid"
trap - EXIT
echo '讀檔探索完成'
