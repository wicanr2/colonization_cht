#!/usr/bin/env bash
# 目標096：同一真視窗輸入前綴下的提示逐欄回退；外層容器管理 Xvfb。
set -euo pipefail

out=${COLONIZATION_GOAL096_NEGATIVES:-/repo/workplace/reports/goal096-negatives}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal096-window-src/window-bin}
fonts=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
catalog=/repo/text/draft.zh-Hant.tsv
old_fonts=/repo/workplace/reports/goal086-fonts
[[ -x "$bin" && -d "$out" && -d "$fonts" && -d "$old_fonts" && -d /game ]]
[[ -f "$out/idle.inputs.json" && -f "$out/cursor.inputs.json" ]]

run_idle() {
  local name=$1
  local source_catalog=$2
  local source_fonts=$3
  [[ ! -e "$out/$name.json" ]]
  "$bin" --window --all-menu --root /game --catalog "$source_catalog" \
    --font-dir "$source_fonts" --out "$out/$name" \
    --replay-inputs "$out/idle.inputs.json" --window-steps 55000000
}

run_idle baseline "$catalog" "$fonts"
[[ ! -e "$out/control.json" ]]
"$bin" --window --all-menu --control --root /game --catalog "$catalog" \
  --font-dir "$fonts" --out "$out/control" \
  --replay-inputs "$out/idle.inputs.json" --window-steps 55000000
run_idle missing "$out/missing.tsv" "$fonts"
run_idle duplicate "$out/duplicate.tsv" "$fonts"
run_idle missing-mask "$catalog" "$old_fonts"
run_idle wrong-size "$catalog" "$out/wrong-size-fonts"

[[ ! -e "$out/cursor.json" && ! -e "$out/cursor-control.json" ]]
"$bin" --window --all-menu --root /game --catalog "$catalog" \
  --font-dir "$fonts" --out "$out/cursor" \
  --replay-inputs "$out/cursor.inputs.json" --window-steps 58000000
"$bin" --window --all-menu --control --root /game --catalog "$catalog" \
  --font-dir "$fonts" --out "$out/cursor-control" \
  --replay-inputs "$out/cursor.inputs.json" --window-steps 58000000

if "$bin" --window --all-menu --root "$out/wrong-game" --catalog "$catalog" \
    --font-dir "$fonts" --out "$out/wrong-version" \
    --replay-inputs "$out/idle.inputs.json" --window-steps 55000000; then
  echo '錯版原版未被拒絕' >&2
  exit 1
else
  code=$?
  [[ "$code" -eq 2 ]]
fi
echo '姓名提示缺譯、重複鍵、字模、游標與錯版負例已重播'
