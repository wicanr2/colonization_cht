#!/usr/bin/env bash
# 僅容器內使用；Xvfb生命週期由外層xvfb-run管理。
set -euo pipefail
OUT=/out/goal058-window
/app/window --all-menu --root /game --catalog /repo/text/draft.zh-Hant.tsv --font-dir /out/goal057-fonts --out "$OUT" --window-steps 100000000 > "$OUT.log" 2>&1 &
game_pid=$!
trap 'kill "$game_pid" 2>/dev/null || true; wait "$game_pid" 2>/dev/null || true' EXIT
window=""
for ((i=0;i<100;i++)); do
  window=$(xdotool search --name 'Colonization CHT prototype' 2>/dev/null | head -1 || true)
  [[ -n "$window" ]] && break
  sleep .1
done
[[ -n "$window" ]]
xdotool windowfocus "$window"
wait_step() {
  for ((i=0;i<600;i++)); do
    kill -0 "$game_pid"
    step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$OUT.status.json" 2>/dev/null | tail -1 || true)
    if [[ -n "$step" && "$step" -ge "$1" ]]; then return; fi
    sleep .1
  done
  return 1
}
wait_stage() {
  for ((i=0;i<600;i++)); do
    kill -0 "$game_pid"
    if grep -q '"stage": "'"$1"'"' "$OUT.status.json" 2>/dev/null; then return; fi
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
sleep 1
import -window "$window" "$OUT.menu.png"
xdotool mousemove --window "$window" 512 440
sleep .3
xdotool mousedown 1
sleep .3
xdotool mouseup 1
wait_stage difficulty
xdotool mousemove --window "$window" 64 64
sleep 3
import -window "$window" "$OUT.difficulty.png"
wait "$game_pid"
trap - EXIT
# 記錄的X輸入逐指令重播；對照只改顯示，不再從GUI猜時序。
for mode in replay control; do
  args=()
  [[ "$mode" == control ]] && args+=(--control)
  /app/window --all-menu --root /game --catalog /repo/text/draft.zh-Hant.tsv --font-dir /out/goal057-fonts --out "$OUT-$mode" --replay-inputs "$OUT.inputs.json" "${args[@]}" > "$OUT-$mode.log" 2>&1
done
