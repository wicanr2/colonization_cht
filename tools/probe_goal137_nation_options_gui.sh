#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以真 Ebitengine 視窗、玩家鍵鼠選指定國家，走過介紹與字幕到海上，開遊戲選項並擷取（目標137）。
# 用法：COLONIZATION_NATION=france|spain|netherlands probe_goal137_nation_options_gui.sh
set -euo pipefail

nation=${COLONIZATION_NATION:?需指定 COLONIZATION_NATION}
case $nation in
  france) card=(1020 200) ;;
  spain) card=(620 580) ;;
  netherlands) card=(1020 580) ;;
  *) echo "未知國家 $nation" >&2; exit 2 ;;
esac

out=${COLONIZATION_GOAL137_OUT:-/repo/workplace/reports/goal137-options-followups/options-$nation}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal136-nation-intro/window-src/colonization-window}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
masks=${COLONIZATION_INTRO_MASKS:-/repo/workplace/reports/goal136-nation-intro/masks}
[[ -x "$bin" && -d "$font_dir" && -d "$card_font_dir" && -d "$masks" ]]
[[ -f /game/GAME.TXT && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.options.png" ]]

"$bin" --window --all-menu --nation-card-a --nation-intro-a --game-options-title-a --game-options-rows-a --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$masks" \
  --game-options-title-font /repo/workplace/reports/goal133-options-rows/title-font.json \
  --game-options-rows-font-dir /repo/workplace/reports/goal134-options-rows/row-fonts \
  --window-steps 1282000000 --out "$out" > "$out.log" 2>&1 &
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
  for ((i=0; i<${COLONIZATION_WAIT_TICKS:-18000}; i++)); do  # 每 0.1 秒一次；主機高負載時以 COLONIZATION_WAIT_TICKS 放寬，只影響牆鐘等待
    kill -0 "$game_pid"
    step=$(sed -n 's/.*"step": \([0-9]*\).*/\1/p' "$out.status.json" 2>/dev/null | tail -1 || true)
    if [[ -n "$step" && "$step" -ge "$1" ]]; then return; fi
    sleep .1
  done
  echo "等待步數 $1 逾時；最後 ${step:-無}" >&2
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
# 選國頁旗卡中心（四倍座標）；英格蘭為預設。比照探針節奏：先停在旗卡上，再按住、放開，
# 移動與按下落在同一畫格時原版不會改選。
wait_step 44000000
xdotool mousemove --window "$window" "${card[0]}" "${card[1]}"
wait_step 44500000
xdotool mousedown 1
wait_step 45000000
xdotool mouseup 1
wait_step 45500000
xdotool mousemove --window "$window" 64 64
wait_step 46000000
click 260 736
xdotool mousemove --window "$window" 64 64
# 非英格蘭會先停在姓名畫面；之後比照英格蘭錄製路徑按 Enter 走過介紹與國王頁、字幕。
for step in 50000000 58000000 68000000 78000000 88000000; do
  wait_step "$step"
  enter_once
done
wait_step 1100000000
import -window "$window" "$out.sea.png"
wait_step 1230000000
xdotool keydown Left
sleep .2
xdotool keyup Left
wait_step 1250000000
click 92 12
wait_step 1270000000
click 180 64
wait_step 1280000000
import -window "$window" "$out.options.png"
wait "$game_pid"
trap - EXIT
echo "真 Ebitengine 視窗 $nation 遊戲選項現場擷取完成"
