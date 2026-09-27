# 真 GUI 腳本共用的步數對齊輸入（目標164，Issue #40）。只在有界 Docker/Xvfb 內由各 probe 腳本 source。
# 需要呼叫端先設定 $out（前端 --out）、$game_pid 與 $window。
#
# 前端每次 Update 先讀一次滑鼠與鍵盤、再執行 200,000 步、最後寫 $out.status.json。
# 動作後等狀態步數至少前進兩次 Update，才能保證那個動作已被某次 Update 讀到；
# 按住期間再多等一次 Update，原版至少看到兩個畫格的按下狀態。牆鐘長短不影響送達的畫格。

GUI_UPDATE_STEPS=200000
GUI_HOLD_STEPS=${COLONIZATION_GUI_HOLD_STEPS:-600000}

gui_step() {
  sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true
}
wait_step() {
  local step=""
  for ((i=0; i<${COLONIZATION_WAIT_TICKS:-72000}; i++)); do  # 每 0.1 秒一次；主機高負載時以 COLONIZATION_WAIT_TICKS 放寬
    kill -0 "$game_pid"
    step=$(gui_step)
    if [[ -n "$step" && "$step" -ge "$1" ]]; then return; fi
    sleep .1
  done
  echo "等待原版步數 $1 逾時；最後 ${step:-無}" >&2
  return 1
}
wait_stage() {
  for ((i=0; i<${COLONIZATION_WAIT_TICKS:-72000}; i++)); do
    kill -0 "$game_pid"
    if grep -q '"stage": "'"$1"'"' "$out.status.json" 2>/dev/null; then return; fi
    sleep .1
  done
  echo "等待畫面階段 $1 逾時" >&2
  return 1
}
# 等畫面階段出現後再前進指定步數，讓原版畫完該頁；點擊時機跟著畫面走，不跟固定步數。
wait_screen() {
  local start
  wait_stage "$1"
  start=$(gui_step)
  wait_step $(( ${start:-0} + $2 ))
}
# 執行一個 xdotool 動作，等前端確定讀到後才返回；$1 為動作後至少要前進的步數。
gui_act() {
  local need=$1 start
  shift
  start=$(gui_step)
  "$@"
  wait_step $(( ${start:-0} + need ))
}
move_to() {
  gui_act $((2 * GUI_UPDATE_STEPS)) xdotool mousemove --window "$window" "$1" "$2"
}
click() {
  move_to "$1" "$2"
  gui_act "$GUI_HOLD_STEPS" xdotool mousedown 1
  gui_act $((2 * GUI_UPDATE_STEPS)) xdotool mouseup 1
}
key_once() {
  gui_act "$GUI_HOLD_STEPS" xdotool keydown "$1"
  gui_act $((2 * GUI_UPDATE_STEPS)) xdotool keyup "$1"
}
enter_once() {
  key_once Return
}
