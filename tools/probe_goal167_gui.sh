#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：用真 Ebitengine 視窗與玩家鍵鼠選 Discoverer 難度走英格蘭路徑，登陸、接觸原住民、
# 建殖民地到殖民地畫面，沿途以 Enter 應答各則教學提示與訊息並擷取（目標167，規格035 通用對話框）。
set -euo pipefail

out=${COLONIZATION_GOAL167_GUI_OUT:-/repo/workplace/reports/goal167-tutorial/gui-tutorial}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal167-tutorial/window-src/colonization-window}
help_masks=${COLONIZATION_HELP_MASKS:-/repo/workplace/reports/goal142-help/fonts}
sea_atlas=${COLONIZATION_SEA_ATLAS:-/repo/workplace/reports/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-/repo/workplace/reports/goal167-tutorial/atlas/dialog-atlas.json}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$help_masks" && -f "$sea_atlas" && -f "$dialog_atlas" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.shots" ]]

"$bin" --window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$help_masks" --root /game \
  --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --dialog-atlas "$dialog_atlas" \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 1210000000 --out "$out" > "$out.log" 2>&1 &
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
shot() {
  local s
  s=$(gui_step)
  import -window "$window" "$out.$1.png"
  echo "$1 $s" >> "$out.shots"
}


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
# 第一張難度卡（Discoverer）：原版只在此難度預設開啟教學提示。
click 640 220
wait_step 40000000
click 220 332
wait_step 43500000
click 220 200
wait_step 46000000
click 260 736
move_to 64 64
wait_step 55000000
enter_once
wait_step 65000000
enter_once
wait_step 75000000
enter_once
wait_step 85000000
enter_once
# 目標167：以下交給 tools/gui_auto.py 依畫面自動應答（規則與探針 a5 相同），不依固定步數。
python3 "$(dirname "$0")/gui_auto.py" --out "$out" --window "$window" --pid "$game_pid" \
  --intents "KP_4,KP_4,KP_4,KP_4,KP_4,KP_1,KP_7,KP_8,KP_2,KP_1,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return" \
  --answers "make landfall=Down+Return;Make Landfall=Down+Return" \
  --idle 8000000 --delay 4000000 --start 600000000 --end 1200000000 > "$out.auto.log"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗教學提示路徑現場擷取完成'
