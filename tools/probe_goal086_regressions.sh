#!/usr/bin/env bash
# 目標086：以同一已驗輸入檢查第二張難度卡與國家頁舊欄位無回歸。
set -euo pipefail

base=/repo/workplace/reports/goal086-heading
old_bin=/repo/workplace/reports/goal084-window-src/window-bin
new_bin=/repo/workplace/reports/goal086-window-src/window-bin
old_fonts=/repo/workplace/reports/goal084-fonts-final
new_fonts=/repo/workplace/reports/goal086-fonts
[[ -d /game && -d "$base" && -d "$old_fonts" && -d "$new_fonts" &&
   -x "$old_bin" && -x "$new_bin" && -f "$base/live.inputs.json" &&
   -f "$base/replay-second-40m.inputs.json" ]]

Xvfb :85 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/goal086-regression-xvfb.log 2>&1 &
xvfb_pid=$!
trap 'kill "$xvfb_pid" 2>/dev/null || true; wait "$xvfb_pid" 2>/dev/null || true' EXIT
export DISPLAY=:85
sleep 1

run_case() {
  local label=$1 bin=$2 fonts=$3 inputs=$4 end=$5
  local prefix=$base/$label
  [[ ! -e "$prefix.json" ]]
  "$bin" --window --all-menu --root /game --catalog /repo/text/draft.zh-Hant.tsv \
    --font-dir "$fonts" --out "$prefix" --replay-inputs "$inputs" \
    --window-steps "$end" > "$prefix.log" 2>&1
  printf '%s\n' "$label"
}

run_case old-live-nation-same-input "$old_bin" "$old_fonts" \
  "$base/live.inputs.json" 100000000
run_case new-live-second-same-input "$new_bin" "$new_fonts" \
  "$base/replay-second-40m.inputs.json" 40000000
run_case old-live-second-same-input "$old_bin" "$old_fonts" \
  "$base/replay-second-40m.inputs.json" 40000000
