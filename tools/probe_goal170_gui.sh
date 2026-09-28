#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：沿目標169 路徑建立殖民地後離開，開歐洲港口（說明框與招募、購買、訓練三個對話框），
# 離開港口後依序開顧問報告 F2～F10 與 F1（目標170，規格038 連續字串）。
set -euo pipefail

out=${COLONIZATION_GOAL170_GUI_OUT:-/repo/workplace/reports/goal170-eu/gui-eu}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal170-eu/window-src/colonization-window}
help_masks=${COLONIZATION_HELP_MASKS:-/repo/workplace/reports/goal142-help/fonts}
sea_atlas=${COLONIZATION_SEA_ATLAS:-/repo/workplace/reports/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-/repo/workplace/reports/goal170-eu/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-/repo/workplace/reports/goal170-eu/atlas/string-atlas.json}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_font_dir=${COLONIZATION_CARD_FONT_DIR:-/repo/workplace/reports/goal099-card-fonts}
[[ -x "$bin" && -d "$help_masks" && -f "$sea_atlas" && -f "$dialog_atlas" && -f "$string_atlas" && -d "$font_dir" && -d "$card_font_dir" &&
   -f /game/OPENING.EXE && -d "$(dirname "$out")" ]]
[[ ! -e "$out.json" && ! -e "$out.inputs.json" && ! -e "$out.shots" ]]

"$bin" --window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$help_masks" --root /game \
  --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --dialog-atlas "$dialog_atlas" --string-a --string-atlas "$string_atlas" \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$font_dir" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$card_font_dir" \
  --window-steps 1360000000 --out "$out" > "$out.log" 2>&1 &
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
# 目標170：@TUTORIAL4 應答後接 Escape 離開殖民地（意圖在教學提示上屏前就可能送出，故併入應答），再空兩個閒置間隔（離開後會出現士兵教學提示），e 開歐洲港口（說明框按 Return），逐一點三個按鈕
# （對話框依文字按 Escape，不招募、不購買），點 Exit 離開港口，再依序開報告並以 Return 翻頁或關閉；F1 會開百科條目，放最後。
# 目標169：沿用目標167 的意圖序列直到拓荒者登陸；@TUTORIAL13（拓荒者已登陸）應答後立刻按 b 建殖民地，
# 其餘訊息（含木刻畫、命名與 @TUTORIAL4）按 Return；每次應答後 6M 步再截一張還原後畫面。
# 建城後只再送一個 Return 關掉木刻畫（它不是訊息框，不會觸發應答）；殖民地畫面出現時緩衝區若還有按鍵，
# 原版會在 @TUTORIAL4 上屏前就把它關掉。呼叫端須以 Xvfb -ardelay 60000 關閉自動重複，否則按住 b 期間
# 出現的命名欄會收到重複的 b。
python3 "$(dirname "$0")/gui_auto.py" --out "$out" --window "$window" --pid "$game_pid" \
  --intents "KP_4,KP_4,KP_4,KP_4,KP_4,KP_1,KP_7,KP_8,KP_2,KP_1,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,wait,wait,e,click:1190x374,move:40x700,click:1190x418,move:40x700,click:1190x462,move:40x700,click:1246x726,F2,Return,F3,Return,Return,F4,Return,F5,Return,Return,F6,Return,Return,F7,Return,F8,Return,F9,Return,F10,Return,F1" \
  --answers "make landfall=Down+Return;Make Landfall=Down+Return;Our pioneers have arrived=Return+b;individuals will=Escape;items are available=Escape;Royal University=Escape;On the Colony Screen=Return+Escape" \
  --idle 8000000 --delay 4000000 --start 600000000 --end 1350000000 --after 6000000 --intent-shots-from 980000000 > "$out.auto.log"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗歐洲港口與報告路徑現場擷取完成'
