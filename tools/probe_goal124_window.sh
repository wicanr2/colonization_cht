#!/usr/bin/env bash
# 目標124：真 Ebitengine 視窗正常玩家輸入到海上，按左鍵並以 Esc 離開選項。
# 只在有界 Docker/Xvfb 容器內執行；原版 /game 為唯讀掛載。
set -euo pipefail

out=${COLONIZATION_GOAL124_OUT:-/repo/workplace/reports/goal124-keyboard/live-route}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal124-keyboard/window-src/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$font_dir" && -d "$card_font_dir" && -f /game/VICEROY.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" ]]

common=(--window --all-menu --nation-card-a --root /game
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir"
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv
  --nation-card-font-dir "$card_font_dir" --window-steps 1350000000)

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

wait_step() {
  local step last_report=0
  for ((i=0; i<18000; i++)); do
    kill -0 "$game_pid"
    step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true)
    if [[ -n "$step" && "$step" -ge $((last_report + 100000000)) ]]; then
      echo "原版仍在前進：$step"
      last_report=$step
    fi
    if [[ -n "$step" && "$step" -ge "$1" ]]; then
      echo "原版步數 >= $1：$step"
      return
    fi
    sleep .1
  done
  echo "等待原版步數 $1 逾時；最後觀測 ${step:-無}" >&2
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
key_once() {
  xdotool keydown "$1"
  sleep .2
  xdotool keyup "$1"
}

wait_step 3000000
key_once Return
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
key_once Return
wait_step 65000000
key_once Return
wait_step 75000000
key_once Return
wait_step 85000000
key_once Return

wait_step 1225000000
import -window "$window" "$out.sea-before.png"
key_once Left
wait_step 1250000000
import -window "$window" "$out.sea-after-left.png"
click 92 12
wait_step 1270000000
import -window "$window" "$out.game-menu.png"
click 180 64
wait_step 1290000000
import -window "$window" "$out.game-options.png"
key_once Escape
wait_step 1320000000
import -window "$window" "$out.after-escape.png"

wait "$game_pid"
trap - EXIT
"$bin" "${common[@]}" --control --out "$out-control" \
  --replay-inputs "$out.inputs.json" > "$out-control.log" 2>&1
echo '真視窗原版左鍵與 Esc 路徑、英文控制重播完成'
