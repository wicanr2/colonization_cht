#!/usr/bin/env bash
# 正常 GUI 貨物百科逐篇驗證；只在有界 Docker 內執行。
set -euo pipefail
r=/repo/workplace/reports
audit=$r/goal178-orders/codex-audit
target=${COLONIZATION_GOAL179_OUT:-$r/goal179-pedia-cargo}
seed=${COLONIZATION_GOAL179_SAVE:-$audit/load-route-v2/scratch/COLONY00.SAV}
if [[ ! -f /game/OPENING.EXE || ! -f "$seed" ]]; then echo "SKIP：缺合法原版或正常存檔入口"; exit 77; fi
[[ ! -e "$target" && $(sha256sum "$seed" | cut -d' ' -f1) == cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e ]]
[[ -d "$(dirname "$target")" && $(stat -c %u "$(dirname "$target")") == $(id -u) ]]
mkdir "$target" "$target/scratch"
cp "$seed" "$target/scratch/"
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ardelay 60000 >/tmp/xvfb.log 2>&1 &
xp=$!
game_pid=''
trap '[[ -z "$game_pid" ]] || kill "$game_pid" 2>/dev/null || true; kill "$xp" 2>/dev/null || true; [[ -z "$game_pid" ]] || wait "$game_pid" 2>/dev/null || true; wait "$xp" 2>/dev/null || true' EXIT
out=$target/gui-pedia
"${COLONIZATION_WINDOW_BIN:-$audit/rebuild-recovery/colonization-window}" --window --root /game --scratch "$target/scratch" \
  --all-menu --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified" \
  --sea-status-a --sea-atlas "$r/goal143-sea/atlas/sea-atlas.json" \
  --dialog-a --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}" \
  --string-a --string-atlas "${COLONIZATION_STRING_ATLAS:-$r/goal174-input/atlas/string-atlas.json}" \
  --string-templates "${COLONIZATION_STRING_TEMPLATES:-/repo/text/string-templates.zh-Hant.tsv}" \
  --window-steps "${COLONIZATION_PEDIA_STEPS:-600000000}" --out "$out" >"$out.log" 2>&1 &
game_pid=$!
window=''
for ((i=0;i<600;i++)); do
  window=$(xdotool search --name 'Colonization CHT prototype' 2>/dev/null | head -1 || true)
  [[ -z "$window" ]] || break
  sleep .1
done
[[ -n "$window" ]]
xdotool windowfocus "$window"
source /repo/tools/gui_step_input.sh
shot_after() {
  local s=$(gui_step)
  wait_step $((s+4000000))
  move_to 64 64
  s=$(gui_step)
  import -window "$window" "$out.$1.png"
  echo "$1 $s" >>"$out.shots"
}
wait_step 3000000
enter_once
wait_step 12000000
click 640 400
move_to 64 64
wait_step 30000000
click 512 536
shot_after load-slots
click 620 312
shot_after loaded-notice
enter_once
shot_after loaded-world
click 1128 12
shot_after pedia-menu
category=${COLONIZATION_PEDIA_CATEGORY:-cargo}
click 1100 "${COLONIZATION_PEDIA_MENU_Y:-62}"
shot_after "$category-list"
for ((entry=0;entry<${COLONIZATION_PEDIA_COUNT:-16};entry++)); do
  # 原版每次返回清單都選第一列，從已確認的起點走到該項。
  for ((down=0;down<entry;down++)); do key_once Down; done
  enter_once
  shot_after "$category-article-$entry"
  key_once Escape
  shot_after "$category-list-$entry"
done
if [[ ${COLONIZATION_GUI_CLOSE_AFTER_ROUTE:-0} == 1 ]]; then
  python3 /repo/tools/gui_close_window.py --window "$window"
fi
wait "$game_pid"
