#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標171 以真 GUI 現場輸入、同一組旗標重播中文與英文控制，並做兩個反向對照：
# 缺對話框圖集（百科正文與依賴它的字串層都回原文）、百科雙語稿移除 Cigars 條目並烘製相符圖集（只有該條正文回原文）。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL171_OUT:-$r/goal171-pedia}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-pedia.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$out/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-$out/atlas/string-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$out/gui-pedia.shots" && -f "$sea_atlas" && -f "$dialog_atlas" && -f "$string_atlas" &&
   -f "$out/pedia-no-cigars.tsv" && -f "$out/neg-nocigars-atlas/dialog-atlas.json" && -f /game/OPENING.EXE ]]
[[ ! -e "$out/missing-atlas.json" ]]
shots=$(awk '{print $2}' "$out/gui-pedia.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --string-a --string-atlas "$string_atlas"
       --replay-inputs "$gui" --window-steps "$end" --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
run replay-zh --dialog-atlas "$dialog_atlas" &
run replay-control --dialog-atlas "$dialog_atlas" --control &
run neg-noatlas --dialog-atlas "$out/missing-atlas.json" &
run neg-nocigars --dialog-atlas "$out/neg-nocigars-atlas/dialog-atlas.json" --dialog-pedia "$out/pedia-no-cigars.tsv" &
wait
echo '目標171重播完成'
