#!/usr/bin/env bash
# 目標095：真 Ebitengine 視窗走到姓名欄，再送字元、退格、Enter。
# 外層容器擁有 Xvfb；本腳本以 trap 清理遊戲子程序。
set -euo pipefail

out=${COLONIZATION_GOAL095_OUT:-/repo/workplace/reports/goal095-keyboard/live-name}
negative=${COLONIZATION_GOAL095_NEGATIVE:-0}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal095-keyboard/window-src/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal086-fonts}
[[ -x "$bin" && -d "$font_dir" && -d /game && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" ]]

"$bin" --window --all-menu --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --out "$out" --window-steps 90000000 > "$out.log" 2>&1 &
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
wait_step 43500000
xdotool mousemove --window "$window" 1020 200
wait_step 44000000
xdotool mousedown 1
wait_step 45000000
xdotool mouseup 1
wait_step 46000000
xdotool mousemove --window "$window" 260 736
wait_step 47000000
xdotool mousedown 1
wait_step 48000000
xdotool mouseup 1
xdotool mousemove --window "$window" 64 64
wait_step 55000000
import -window "$window" "$out.idle.png"
if [[ "$negative" == 1 ]]; then
  # 不在 dosgolem 鍵表中的標點須明確拒絕，且失焦時的鍵不可延遲送入。
  xdotool key exclam
  sleep .3
  xdotool windowunmap "$window"
  sleep .3
  xdotool key x
  sleep .3
  xdotool windowmap "$window"
  xdotool windowfocus "$window"
  wait_step 57000000
  import -window "$window" "$out.rejected-and-refocused.png"
fi

xdotool keydown x
sleep .2
xdotool keyup x
wait_step 59000000
import -window "$window" "$out.letter.png"
xdotool keydown BackSpace
sleep .2
xdotool keyup BackSpace
wait_step 63000000
import -window "$window" "$out.backspace.png"
xdotool keydown Return
sleep .2
xdotool keyup Return
wait_step 68000000
import -window "$window" "$out.after-enter.png"
wait "$game_pid"
trap - EXIT

"$bin" --window --all-menu --control --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --out "$out-control" --replay-inputs "$out.inputs.json" \
  --window-steps 90000000 > "$out-control.log" 2>&1
