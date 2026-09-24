#!/usr/bin/env bash
# 目標124：失焦期間的方向鍵不得延後送入原版。
set -euo pipefail

out=${COLONIZATION_GOAL124_FOCUS_OUT:-/repo/workplace/reports/goal124-keyboard/focus-left}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal124-keyboard/window-src/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
[[ -x "$bin" && -d "$font_dir" && -f /game/VICEROY.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" ]]

common=(--window --all-menu --root /game
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir"
  --window-steps 30000000)
"$bin" "${common[@]}" --out "$out" > "$out.log" 2>&1 &
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
for ((i=0; i<900; i++)); do
  step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true)
  [[ -n "$step" && "$step" -ge 3000000 ]] && break
  kill -0 "$game_pid"
  sleep .1
done
[[ -n "${step:-}" && "$step" -ge 3000000 ]]
xdotool windowunmap "$window"
sleep .3
xdotool key Left
sleep .3
xdotool windowmap "$window"
xdotool windowfocus "$window"
xdotool keydown Return
sleep .2
xdotool keyup Return
wait "$game_pid"
trap - EXIT
"$bin" "${common[@]}" --control --out "$out-control" \
  --replay-inputs "$out.inputs.json" > "$out-control.log" 2>&1
echo '失焦左鍵未送入原版；同輸入英文控制重播完成'
