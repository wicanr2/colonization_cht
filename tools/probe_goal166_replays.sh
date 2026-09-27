#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標166 以真 GUI 現場輸入、同一組旗標重播中文與英文控制，並做兩個反向對照：
# 缺對話框圖集（版本字串、國王接見、下拉選單回原文）、空的靜態字模目錄（載入訊息回原文）。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL166_OUT:-$r/goal166-spots}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-spots.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$out/atlas/dialog-atlas.json}
static_masks=${COLONIZATION_STATIC_MASKS:-$out/static-masks}
[[ -x "$bin" && -f "$gui" && -f "$sea_atlas" && -f "$dialog_atlas" && -d "$static_masks" && -f /game/OPENING.EXE ]]
[[ ! -e "$out/missing-atlas.json" ]]
mkdir -p "$out/empty-static-masks"
shots=$(awk '{print $2}' "$out/gui-spots.shots" | paste -sd,)
[[ -n "$shots" ]]
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --sea-status-a --sea-atlas "$sea_atlas" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --dialog-a --static-credits-a --replay-inputs "$gui" --window-steps "$end"
       --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
run replay-zh --dialog-atlas "$dialog_atlas" --static-mask-dir "$static_masks" &
run replay-control --dialog-atlas "$dialog_atlas" --static-mask-dir "$static_masks" --control &
run neg-nodialog --dialog-atlas "$out/missing-atlas.json" --static-mask-dir "$static_masks" &
run neg-nostatic --dialog-atlas "$dialog_atlas" --static-mask-dir "$out/empty-static-masks" &
wait
echo '目標166重播完成'
