#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標178 沿目標174 路徑（士兵教學框壓住右側狀態欄、Find Colony 與 "J" not found.），
# 之後依序點 GAME、ORDERS、REPORTS、TRADE、COLONIZOPEDIA 的標題切換下拉選單，各截一張（VIEW 已在前段）。
# 不用 Escape 關選單：選單開著時按 Escape 會開離開確認框（只有「Yes No」，與部族和約選項同字，無法以應答區分）。
set -euo pipefail

out=${COLONIZATION_GOAL178_GUI_OUT:-/repo/workplace/reports/goal178-orders/gui-sea}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal178-orders/window-src/colonization-window}
help_masks=${COLONIZATION_HELP_MASKS:-/repo/workplace/reports/goal142-help/fonts}
sea_atlas=${COLONIZATION_SEA_ATLAS:-/repo/workplace/reports/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-/repo/workplace/reports/goal174-input/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-/repo/workplace/reports/goal174-input/atlas/string-atlas.json}
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
  --window-steps 1210000000 --out "$out" > "$out.log" 2>&1 &
game_pid=$!
trap 'kill "$game_pid" 2>/dev/null || true; wait "$game_pid" 2>/dev/null || true' EXIT

window=""
for ((i=0; i<600; i++)); do  # 載入兩份圖集可能超過 10 秒
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
# 目標174：命名新陸地與命名殖民地兩個輸入欄沿用預設名按 Return；@TUTORIAL4 關閉後按 Escape 離開殖民地，
# 點頂端 VIEW 開下拉選單（應答 none，不按鍵），再點第 4 項 Find Colony（無熱鍵，列位 (268,190)）；
# 輸入欄出現時打 J，等兩個意圖截圖後按 Return。不送 Escape：地圖上的 Escape 會開離開確認框。
# 目標169：沿用目標167 的意圖序列直到拓荒者登陸；@TUTORIAL13（拓荒者已登陸）應答後立刻按 b 建殖民地，
# 其餘訊息（含木刻畫、命名與 @TUTORIAL4）按 Return；每次應答後 6M 步再截一張還原後畫面。
# 呼叫端須以 Xvfb -ardelay 60000 關閉自動重複，否則按住 b 期間出現的命名欄會收到重複的 b。
python3 "$(dirname "$0")/gui_auto.py" --out "$out" --window "$window" --pid "$game_pid" \
  --intents "KP_4,KP_4,KP_4,KP_4,KP_4,KP_1,KP_7,KP_8,KP_2,KP_1,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,KP_9,KP_1,Return,KP_8,b,Return,KP_4,KP_7,Return,KP_2,KP_6,space,Return,wait,Escape,wait,click:224x12,click:268x190,wait,wait,Return,wait,click:96x12,wait,click:352x12,wait,click:500x12,wait,click:670x12,wait,click:1090x12,wait,wait" \
  --answers "make landfall=Down+Return;Make Landfall=Down+Return;Our pioneers have arrived=Return+b;Find Colony=none;Save Game=none;Disband Unit=none;Religious=none;Trade Route=none;Cargo Types=none;Where the heck=J;Exit to DOS=Escape" \
  --idle 8000000 --delay 4000000 --start 600000000 --end 1200000000 --after 6000000 --intent-shots-from 980000000 > "$out.auto.log"
wait "$game_pid"
trap - EXIT
echo '真 Ebitengine 視窗殖民地操作路徑現場擷取完成'
