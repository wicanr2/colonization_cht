#!/usr/bin/env bash
# 乾淨容器內從正式封包啟動，正常鍵鼠進主選單。Wine/Linux共用輸入流程。
set -euo pipefail
platform=${1:?linux/windows}
version=${2:?版本}
batch=/repo/workplace/reports/goal183-release
dir=$batch/smoke/$platform
[[ ! -e "$dir" && -f /game/OPENING.EXE ]]
mkdir -p "$dir/save"
out=$dir/run
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 LANG=C.UTF-8 LC_ALL=C.UTF-8
Xvfb :99 -screen 0 1600x1000x24 -nolisten tcp -ardelay 60000 >"$dir/xvfb.log" 2>&1 & xp=$!
game_pid=
trap '[[ -z "$game_pid" ]] || kill "$game_pid" 2>/dev/null || true; if command -v wineserver >/dev/null; then wineserver -k 2>/dev/null || true; fi; kill "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true' EXIT
for ((i=0; i<100; i++)); do
  xdotool getdisplaygeometry >/dev/null 2>&1 && break
  sleep .05
done
if [[ "$platform" == linux ]]; then
  export COLONIZATION_CHT_SAVE="$dir/save"
  linux_root=$(python3 -c 'import json;print(json.load(open("/repo/workplace/reports/goal183-release/packages-check.json"))["appimage"]["root"])')
  "$linux_root/bin/colonization-window" --version >"$dir/version.json"
  "$linux_root/AppRun" --game /game --play=false --audio-mute \
    --window-steps 50000000 --audio-wav "$dir/original.wav" --out "$out" >"$dir/run.log" 2>&1 &
else
  export WINEPREFIX="$dir/wine-prefix" WINEDEBUG=-all
  export COLONIZATION_CHT_SAVE="Z:\\repo\\workplace\\reports\\goal183-release\\smoke\\windows\\save"
  python3 /repo/tools/smoke_release_windows.py "$batch" "$dir" >"$dir/run.log" 2>&1 &
fi
game_pid=$!
window=
for ((i=0; i<900; i++)); do
  window=$(xdotool search --onlyvisible --name "Colonization CHT $version" 2>/dev/null | head -1 || true)
  [[ -n "$window" ]] && break
  kill -0 "$game_pid" 2>/dev/null || { cat "$dir/run.log"; exit 1; }
  sleep .1
done
[[ -n "$window" ]]
xdotool windowfocus "$window"
source /repo/tools/gui_step_input.sh
wait_step 3000000
enter_once
wait_step 12000000
click 640 400
wait_stage menu
move_to 64 64
wait_step 26000000
import -window "$window" "$dir/main-menu.png"
wait "$game_pid"
game_pid=
[[ -f "$out.memory" && -f "$out.inputs.json" ]]
