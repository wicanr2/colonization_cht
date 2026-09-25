#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：規格031八列＋標題，以真玩家錄製輸入做中英同輸入重播與載入期負例。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL134_OUT:-$r/goal134-options-rows}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
rowfonts=$out/row-fonts
title=$r/goal133-options-rows/title-font.json
prefix=$r/goal132-options-title-event/window-prefix-1280000000.inputs.json
full=$r/goal124-keyboard/live-route-b.inputs.json
[[ -x "$bin" && -d "$rowfonts" && -f "$title" && -f "$prefix" && -f "$full" && -f /game/OPENING.EXE ]]
[[ "$(sha256sum "$full" | cut -d' ' -f1)" == dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98 ]]

common=(--window --root /game --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified")
zh=(--game-options-title-a --game-options-title-font "$title" --game-options-rows-a --game-options-rows-font-dir "$rowfonts")
run() { local name=$1; shift; [[ ! -e "$out/$name.json" ]]; "$bin" "${common[@]}" --out "$out/$name" "$@" > "$out/$name.log" 2>&1; }

if [[ "${1:-all}" == gui ]]; then
  # 真 GUI 錄下的玩家輸入（含點擊第2列）做中英同輸入重播，終點與現場視窗相同。
  gui=$out/gui-real.inputs.json
  [[ -f "$gui" ]]
  end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
  run gui-replay-zh "${zh[@]}" --replay-inputs "$gui" --window-steps "$end" &
  run gui-replay-control --control "${zh[@]}" --replay-inputs "$gui" --window-steps "$end" &
  wait
  echo '目標134現場輸入重播完成'
  exit 0
fi
if [[ "${1:-all}" == all ]]; then
run zh-1280m "${zh[@]}" --replay-inputs "$prefix" --window-steps 1280000000 &
run control-1280m --control "${zh[@]}" --replay-inputs "$prefix" --window-steps 1280000000 &
run zh-full "${zh[@]}" --replay-inputs "$full" --window-steps 1350000000 &
run control-full --control "${zh[@]}" --replay-inputs "$full" --window-steps 1350000000 &
wait
fi
mkdir -p "$out/empty-fonts"
# 載入期負例不帶重播，只跑一百萬步即可讀到逐列回退原因。
run neg-missing-ink "${zh[@]}" --missing --window-steps 1000000
run neg-no-fonts --game-options-title-a --game-options-title-font "$title" --game-options-rows-a \
  --game-options-rows-font-dir "$out/empty-fonts" --window-steps 1000000
for variant in blank duplicate wrong-hotkey no-hotkey; do
  [[ -f "$out/goal134-catalog-$variant.tsv" ]]
  "$bin" --window --root /game --catalog "$out/goal134-catalog-$variant.tsv" \
    --font-dir "$r/goal096-fonts-verified" "${zh[@]}" --window-steps 1000000 \
    --out "$out/neg-$variant" > "$out/neg-$variant.log" 2>&1
done
echo '目標134重播與負例完成'
