#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標167 以真 GUI 現場輸入、同一組旗標重播中文與英文控制，並做兩個反向對照：
# 缺對話框圖集（通用引擎整個回原文）、help 清冊移除第 2～19 則並烘製相符圖集（教學提示回原文，其他訊息照常）。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL167_OUT:-$r/goal167-tutorial}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-tutorial.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$out/atlas/dialog-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$out/gui-tutorial.shots" && -f "$sea_atlas" && -f "$dialog_atlas" &&
   -f "$out/help-no-tutorials.tsv" && -f "$out/neg-nohelp-atlas/dialog-atlas.json" && -f /game/OPENING.EXE ]]
[[ ! -e "$out/missing-atlas.json" ]]
shots=$(awk '{print $2}' "$out/gui-tutorial.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --replay-inputs "$gui" --window-steps "$end" --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
run replay-zh --dialog-atlas "$dialog_atlas" &
run replay-control --dialog-atlas "$dialog_atlas" --control &
run neg-noatlas --dialog-atlas "$out/missing-atlas.json" &
run neg-nohelp --dialog-atlas "$out/neg-nohelp-atlas/dialog-atlas.json" --help-catalog "$out/help-no-tutorials.tsv" &
wait
echo '目標167重播完成'
