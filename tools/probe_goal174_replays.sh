#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標174 以真 GUI 現場輸入、同一組旗標重播中文與英文控制，並做反向對照：
# draft 移除三種輸入欄標籤譯名、模板表移除 label-trailing（字串層後備），並烘製相符圖集時，輸入列標籤回原文。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL174_OUT:-$r/goal174-input}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-input.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$out/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-$out/atlas/string-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$out/gui-input.shots" && -f "$sea_atlas" && -f "$dialog_atlas" && -f "$string_atlas" &&
   -f "$out/draft-no-labels.tsv" && -f "$out/templates-no-label.tsv" && -f "$out/neg-nolabel-atlas/string-atlas.json" &&
   -f "$out/neg-nolabel-dialog/dialog-atlas.json" && -f /game/OPENING.EXE ]]
shots=$(awk '{print $2}' "$out/gui-input.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --string-a
       --replay-inputs "$gui" --window-steps "$end" --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
run replay-zh --dialog-atlas "$dialog_atlas" --string-atlas "$string_atlas" &
run replay-control --dialog-atlas "$dialog_atlas" --string-atlas "$string_atlas" --control &
run neg-nolabel --dialog-atlas "$out/neg-nolabel-dialog/dialog-atlas.json" --string-atlas "$out/neg-nolabel-atlas/string-atlas.json" \
    --dialog-draft "$out/draft-no-labels.tsv" --string-templates "$out/templates-no-label.tsv" &
wait
echo '目標174重播完成'
