#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標176（規格040）以真 GUI 現場輸入重播四組：
# A 數位音效＋音訊＋WAV（與真 GUI 的 WAV 比對）、B 只開數位音效（與 A 比原版狀態）、
# C 只開音訊＋WAV（預設機器設定下開音訊）、D 都不開（與 C 比原版狀態）。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL176_OUT:-$r/goal176-audio}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-audio.inputs.json
sea_atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
dialog_atlas=${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}
string_atlas=${COLONIZATION_STRING_ATLAS:-$r/goal174-input/atlas/string-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$out/gui-audio.shots" && -f "$out/gui-audio.wav" && -f "$sea_atlas" &&
   -f "$dialog_atlas" && -f "$string_atlas" && -f /game/OPENING.EXE ]]
shots=$(awk '{print $2}' "$out/gui-audio.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a --sea-atlas "$sea_atlas" --dialog-a --string-a --dialog-atlas "$dialog_atlas" --string-atlas "$string_atlas"
       --replay-inputs "$gui" --window-steps "$end" --checkpoint-steps "$shots")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
pids=()
run replay-a --sb-digital --audio --audio-wav "$out/replay-a.wav" & pids+=($!)
run replay-b --sb-digital & pids+=($!)
run replay-c --audio --audio-wav "$out/replay-c.wav" & pids+=($!)
run replay-d & pids+=($!)
wait "${pids[@]}"
echo '目標176重播完成'
