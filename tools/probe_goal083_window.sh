#!/usr/bin/env bash
# 目標083：真 Ebitengine 視窗從冷啟動點選第二張卡片，再點難度完成區。
# 容器外層擁有並以 trap 清理 Xvfb；本檔只擁有原版前端程序。
set -euo pipefail

out=${COLONIZATION_GOAL083_OUT:-/out/goal083-window}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal082-second-card/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal082-fonts}
[[ -x "$bin" && -d "$font_dir" && ! -e "$out.json" && ! -e "$out.inputs.json" ]]

"$bin" --window --all-menu --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --out "$out" --window-steps 100000000 > "$out.log" 2>&1 &
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
  for ((i=0; i<600; i++)); do
    kill -0 "$game_pid"
    step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true)
    if [[ -n "$step" && "$step" -ge "$1" ]]; then return; fi
    sleep .1
  done
  return 1
}
wait_opened() {
  for ((i=0; i<600; i++)); do
    kill -0 "$game_pid"
    if grep -q '"stage": "'$1'"' "$out.status.json" 2>/dev/null; then return; fi
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
wait_opened menu
xdotool mousemove --window "$window" 64 64
xdotool mousemove --window "$window" 512 440
sleep .3
xdotool mousedown 1
sleep .3
xdotool mouseup 1
wait_opened difficulty
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
import -window "$window" "$out.before-finish.png"
xdotool mousemove --window "$window" 220 332
wait_step 41000000
xdotool mousedown 1
wait_step 42000000
xdotool mouseup 1
wait_step 43000000
xdotool mousemove --window "$window" 64 64
wait_step 60000000
import -window "$window" "$out.after-finish.png"
wait "$game_pid"
trap - EXIT

"$bin" --window --all-menu --control --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --out "$out-control" --replay-inputs "$out.inputs.json" \
  --window-steps 100000000 > "$out-control.log" 2>&1
