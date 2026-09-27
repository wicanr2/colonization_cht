#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標165 以真 GUI 現場輸入重播中文與英文控制，並做兩個反向對照：
# 缺圖集（整個引擎回原文）、術語表與語料 NAMES.TXT 部落列都移除現場遇到的部落名並烘製相符圖集（原住民三則回原文，其餘照常）。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL165_OUT:-$r/goal165-dialog}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-dialog.inputs.json
atlas=${COLONIZATION_DIALOG_ATLAS:-$out/atlas/dialog-atlas.json}
noterm_atlas=$out/neg-noterm-atlas/dialog-atlas.json
[[ -x "$bin" && -f "$gui" && -f "$atlas" && -f "$noterm_atlas" && -f "$out/terms-no-tribe.tsv" && -f "$out/corpus-no-tribe.tsv" && -f /game/OPENING.EXE ]]
[[ ! -e "$out/missing-atlas.json" ]]
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --root /game --dialog-a --replay-inputs "$gui" --window-steps "$end"
       --checkpoint-steps 690000000,830000000,870000000,885000000,900000000,920000000)
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
tags=" ${COLONIZATION_GOAL165_TAGS:-replay-zh replay-control neg-noatlas neg-noterm} "
[[ $tags == *" replay-zh "* ]] && run replay-zh --dialog-atlas "$atlas" &
[[ $tags == *" replay-control "* ]] && run replay-control --dialog-atlas "$atlas" --control &
[[ $tags == *" neg-noatlas "* ]] && run neg-noatlas --dialog-atlas "$out/missing-atlas.json" &
[[ $tags == *" neg-noterm "* ]] && run neg-noterm --dialog-atlas "$noterm_atlas" --dialog-terms "$out/terms-no-tribe.tsv" --dialog-corpus "$out/corpus-no-tribe.tsv" &
wait
echo '目標165重播完成'
