#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以真 Ebitengine 視窗、玩家鍵鼠在選國頁點指定旗卡，抵達該國介紹 A、B 頁並擷取現場畫面（規格025）。
# 用法：COLONIZATION_NATION=france|spain|netherlands probe_goal136_gui.sh
set -euo pipefail

nation=${COLONIZATION_NATION:?需指定 COLONIZATION_NATION}
case $nation in
  france) card=(1020 200) ;;
  spain) card=(620 580) ;;
  netherlands) card=(1020 580) ;;
  *) echo "未知國家 $nation" >&2; exit 2 ;;
esac

out=${COLONIZATION_GOAL136_OUT:-/repo/workplace/reports/goal136-nation-intro/gui-$nation}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal136-nation-intro/window-src/colonization-window}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
masks=${COLONIZATION_INTRO_MASKS:-/repo/workplace/reports/goal136-nation-intro/masks}
[[ -x "$bin" && -d "$font_dir" && -d "$card_font_dir" && -d "$masks" ]]
[[ -f /game/GAME.TXT && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.page-a.png" && ! -e "$out.page-b.png" ]]

"$bin" --window --all-menu --nation-card-a --nation-intro-a --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$masks" \
  --window-steps 65000000 --out "$out" > "$out.log" 2>&1 &
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
source "$(dirname "$0")/gui_step_input.sh"


wait_step 3000000
enter_once
wait_step 12000000
click 640 400
wait_stage menu
move_to 64 64
click 512 440
wait_stage difficulty
move_to 64 64
wait_step 32000000
click 1060 220
wait_step 40000000
click 220 332
# 選國頁（NATIONS.PIK）畫完後才點旗卡；英格蘭為預設。先停在旗卡上，再按住、放開。
wait_screen nations 2000000
move_to "${card[0]}" "${card[1]}"
gui_act $GUI_HOLD_STEPS xdotool mousedown 1
gui_act $((2 * GUI_UPDATE_STEPS)) xdotool mouseup 1
move_to 64 64
click 260 736
move_to 64 64
# 非英格蘭會先停在姓名畫面；Enter 確認預設名後才進介紹 A 頁。
wait_step 50000000
enter_once
wait_step 56000000
import -window "$window" "$out.page-a.png"
wait_step 58000000
enter_once
wait_step 64000000
import -window "$window" "$out.page-b.png"
wait "$game_pid"
trap - EXIT
echo "真 Ebitengine 視窗 $nation 介紹兩頁現場擷取完成"
