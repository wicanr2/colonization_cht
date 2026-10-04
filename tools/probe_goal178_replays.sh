#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標178 以真 GUI 現場輸入重播中文與英文控制，並做反向對照：
# draft 移除 MENU.TXT 的 ORDERS 停用項目（Clear Forest、Build Road）並烘製相符圖集時，ORDERS 選單整段回原文。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL178_OUT:-$r/goal178-orders}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-sea.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-$r/goal174-input/atlas/string-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$out/gui-sea.shots" && -f "$sea_atlas" && -f "$dialog_atlas" && -f "$string_atlas" &&
   -f "$out/draft-no-orders-disabled.tsv" && -f "$out/neg-string/string-atlas.json" &&
   -f "$out/neg-dialog/dialog-atlas.json" && -f /game/OPENING.EXE ]]
shots=$(awk '{print $2}' "$out/gui-sea.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --string-a
       --replay-inputs "$gui" --window-steps "$end" --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
pids=()
trap 'for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done; for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done' EXIT
run replay-zh --dialog-atlas "$dialog_atlas" --string-atlas "$string_atlas" & pids+=($!)
run replay-control --dialog-atlas "$dialog_atlas" --string-atlas "$string_atlas" --control & pids+=($!)
run neg-noorders --dialog-atlas "$out/neg-dialog/dialog-atlas.json" --string-atlas "$out/neg-string/string-atlas.json" \
    --dialog-draft "$out/draft-no-orders-disabled.tsv" & pids+=($!)
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
((failed == 0))
trap - EXIT
echo '目標178重播完成'
