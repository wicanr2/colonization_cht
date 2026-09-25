#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：改八列譯稿後，以現行 TSV 與重烘字模重播既有正式欄位，核對不退步。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL133_OUT:-$r/goal133-options-rows}
bin=${COLONIZATION_WINDOW_BIN:-$r/goal132-options-title-event/window-src/colonization-window}
fonts=$r/goal096-fonts-verified
cards=$r/goal099-card-fonts
[[ -x "$bin" && -d "$fonts" && -d "$cards" && -f /game/OPENING.EXE &&
   -f "$out/title-font.json" && -f "$out/build1-font.json" ]]
[[ ! -e "$out/regression-title-1280m.json" && ! -e "$out/regression-build1-82m.json" ]]

"$bin" --window --game-options-title-a --root /game --catalog /repo/text/draft.zh-Hant.tsv \
  --font-dir "$fonts" --game-options-title-font "$out/title-font.json" \
  --replay-inputs "$r/goal132-options-title-event/window-prefix-1280000000.inputs.json" \
  --window-steps 1280000000 --out "$out/regression-title-1280m" > "$out/regression-title-1280m.log" 2>&1
"$bin" --window --all-menu --nation-card-a --build1-a --root /game \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$fonts" \
  --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$cards" --build1-font "$out/build1-font.json" \
  --replay-inputs "$r/goal130-build1/window-prefix-82000000.inputs.json" \
  --window-steps 82000000 --out "$out/regression-build1-82m" > "$out/regression-build1-82m.log" 2>&1
echo '目標133回歸重播完成'
