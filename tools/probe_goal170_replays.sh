#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標170 以真 GUI 現場輸入、同一組旗標重播中文與英文控制，並做兩個反向對照：
# 缺字串圖集（字串層整個回原文、對話框照常）、模板表移除港口標題並烘製相符圖集（只有港口標題回原文）。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL170_OUT:-$r/goal170-eu}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-eu.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$out/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-$out/atlas/string-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$out/gui-eu.shots" && -f "$sea_atlas" && -f "$dialog_atlas" && -f "$string_atlas" &&
   -f "$out/templates-no-port.tsv" && -f "$out/neg-noport-atlas/string-atlas.json" && -f /game/OPENING.EXE ]]
[[ ! -e "$out/missing-atlas.json" ]]
shots=$(awk '{print $2}' "$out/gui-eu.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --dialog-atlas "$dialog_atlas" --string-a
       --replay-inputs "$gui" --window-steps "$end" --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
run replay-zh --string-atlas "$string_atlas" &
run replay-control --string-atlas "$string_atlas" --control &
run neg-noatlas --string-atlas "$out/missing-atlas.json" &
run neg-noport --string-atlas "$out/neg-noport-atlas/string-atlas.json" --string-templates "$out/templates-no-port.tsv" &
wait
echo '目標170重播完成'
