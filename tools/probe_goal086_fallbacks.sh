#!/usr/bin/env bash
# 目標086：固定真視窗輸入的逐欄缺鍵、重複鍵與字模失敗反例。
# 由有界 Docker 執行，Xvfb 在本腳本 trap 內明確收尾。
set -euo pipefail

Xvfb :87 -screen 0 1280x800x24 -nolisten tcp -ac >/tmp/goal086-fallback-xvfb.log 2>&1 &
xvfb_pid=$!
trap 'kill "$xvfb_pid" 2>/dev/null || true; wait "$xvfb_pid" 2>/dev/null || true' EXIT
export DISPLAY=:87
sleep 1

base=/repo/workplace/reports/goal086-heading
bin=/repo/workplace/reports/goal086-window-src/window-bin
fonts=/repo/workplace/reports/goal086-fonts
catalog=/repo/text/draft.zh-Hant.tsv
inputs=$base/replay-45m.inputs.json
[[ -x "$bin" && -d /game && -d "$fonts" && -f "$catalog" && -f "$inputs" && -d "$base" ]]

run_case() {
  local label=$1 source_catalog=$2 source_fonts=$3
  local prefix=$base/fallback-$label
  [[ ! -e "$prefix.json" ]]
  "$bin" --window --all-menu --root /game --catalog "$source_catalog" \
    --font-dir "$source_fonts" --out "$prefix" --replay-inputs "$inputs" \
    --window-steps 45000000 > "$prefix.log" 2>&1
  printf '%s\n' "$label"
}

run_case baseline "$catalog" "$fonts"
"$bin" --window --all-menu --control --root /game --catalog "$catalog" \
  --font-dir "$fonts" --out "$base/fallback-baseline-control" \
  --replay-inputs "$inputs" --window-steps 45000000 \
  > "$base/fallback-baseline-control.log" 2>&1
for field in choose level; do
  for reason in missing duplicate; do
    run_case "$reason-$field" "$base/catalog-$reason-$field.tsv" "$fonts"
  done
  for reason in missing-mask wrong-size; do
    run_case "$reason-$field" "$catalog" "$base/fonts-$reason-$field"
  done
done
