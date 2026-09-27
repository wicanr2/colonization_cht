#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗觀看完整開場動畫（玩家不按鍵），擷取製作名單職稱橫幅、人名橫幅與無橫幅畫面（目標151）。
set -euo pipefail

out=${COLONIZATION_GOAL151_GUI_OUT:-/repo/workplace/reports/goal151-static/gui-opening}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal151-static/window-src/colonization-window}
masks=${COLONIZATION_STATIC_MASKS:-/repo/workplace/reports/goal151-static/masks}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$masks" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.design.png" ]]

"$bin" --window --all-menu --nation-card-a --static-credits-a --static-mask-dir "$masks" --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 1130000000 --out "$out" > "$out.log" 2>&1 &
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


# 玩家不按任何鍵；只在各時點擷取畫面。
shot() { wait_step "$1"; import -window "$window" "$out.$2.png"; }
shot 320000000 adventure
shot 460000000 design
shot 480000000 names
shot 555000000 programming
shot 655000000 graphics
shot 810000000 music
shot 960000000 sound
shot 1060000000 nobanner
shot 1115000000 qa
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗開場製作名單現場擷取完成'
