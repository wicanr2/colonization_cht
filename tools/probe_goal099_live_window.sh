#!/usr/bin/env bash
# 目標099：真 Ebitengine 視窗冷啟動，正常滑鼠抵達第一張旗卡。
# 外層容器管理 Xvfb；本腳本以 trap 清理遊戲程序。
set -euo pipefail

out=${COLONIZATION_GOAL099_LIVE_OUT:-/repo/workplace/reports/goal099-card-fonts/live-card}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal099-window-src/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$font_dir" && -d "$card_font_dir" && -d /game && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" ]]

"$bin" --window --all-menu --nation-card-a --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" --out "$out" \
  --window-steps 60000000 > "$out.log" 2>&1 &
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
  local step
  for ((i=0; i<900; i++)); do
    kill -0 "$game_pid"
    step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true)
    if [[ -n "$step" && "$step" -ge "$1" ]]; then return; fi
    sleep .1
  done
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

wait_step 3000000
xdotool keydown Return
sleep .2
xdotool keyup Return
wait_step 12000000
xdotool mousemove --window "$window" 640 400
sleep .3
xdotool mousedown 1
sleep .3
xdotool mouseup 1
wait_stage menu
xdotool mousemove --window "$window" 64 64
xdotool mousemove --window "$window" 512 440
sleep .3
xdotool mousedown 1
sleep .3
xdotool mouseup 1
wait_stage difficulty
xdotool mousemove --window "$window" 64 64
wait_step 32000000
xdotool mousemove --window "$window" 1060 220
wait_step 33000000
xdotool mousedown 1
wait_step 34000000
xdotool mouseup 1
wait_step 35000000
xdotool mousemove --window "$window" 64 64
wait_step 40000000
xdotool mousemove --window "$window" 220 332
wait_step 41000000
xdotool mousedown 1
wait_step 42000000
xdotool mouseup 1
wait_step 43000000
xdotool mousemove --window "$window" 64 64
wait_step 50000000
import -window "$window" "$out.nation.png"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗已抵達第一張國家旗卡'
