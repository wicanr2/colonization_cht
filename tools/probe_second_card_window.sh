#!/usr/bin/env bash
# 目標081：容器 Xvfb 下真 Ebitengine 視窗操作第二張難度卡片。
# 外層擁有並清理 Xvfb；本檔只管理原版視窗程序與本機收據。
set -euo pipefail

out=${COLONIZATION_SECOND_CARD_OUT:-/out/window-second-card}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal079-window-bin}
[[ -x "$bin" && ! -e "$out.json" && ! -e "$out.inputs.json" ]]

"$bin" --window --all-menu --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv \
  --font-dir /repo/workplace/reports/goal057-fonts \
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
wait_stage() {
  for ((i=0; i<600; i++)); do
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
import -window "$window" "$out.second-card.png"
wait "$game_pid"
trap - EXIT

"$bin" --window --all-menu --control --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv \
  --font-dir /repo/workplace/reports/goal057-fonts \
  --out "$out-control" --replay-inputs "$out.inputs.json" \
  --window-steps 100000000 > "$out-control.log" 2>&1
