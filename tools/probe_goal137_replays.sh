#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標137 真 GUI 錄下的現場輸入，用與 GUI 相同旗標做中英同輸入重播。
# 用法：probe_goal137_replays.sh <GUI 收據名稱，如 options-france 或 gui-hotkey>
# 讀檔例另設 COLONIZATION_SCRATCH_SOURCE：中英兩組各自複製一份只含同一存檔的乾淨暫存層。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL137_OUT:-$r/goal137-options-followups}
bin=${COLONIZATION_WINDOW_BIN:-$r/goal136-nation-intro/window-src/colonization-window}
name=$1
inputs=$out/$name.inputs.json
[[ -x "$bin" && -f "$inputs" && -f /game/OPENING.EXE ]]
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$inputs")
flags=(--window --all-menu --nation-card-a --nation-intro-a --game-options-title-a --game-options-rows-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$r/goal136-nation-intro/masks"
       --game-options-title-font "$r/goal133-options-rows/title-font.json"
       --game-options-rows-font-dir "$r/goal134-options-rows/row-fonts"
       --replay-inputs "$inputs" --window-steps "$end")
for mode in zh control; do
  [[ ! -e "$out/$name-replay-$mode.json" ]]
  extra=()
  [[ $mode == control ]] && extra=(--control)
  if [[ -n "${COLONIZATION_SCRATCH_SOURCE:-}" ]]; then
    scratch=$out/$name-replay-$mode.scratch
    [[ -d "$COLONIZATION_SCRATCH_SOURCE" && ! -e "$scratch" ]]
    cp -r "$COLONIZATION_SCRATCH_SOURCE" "$scratch"
    extra+=(--scratch "$scratch")
  fi
  "$bin" "${flags[@]}" "${extra[@]}" --out "$out/$name-replay-$mode" > "$out/$name-replay-$mode.log" 2>&1 &
done
wait
echo "目標137重播完成：$name"
