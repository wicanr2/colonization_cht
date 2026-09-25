#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標138 真 GUI 錄下的輸入，對開框（1275M 前綴）與關框終點做中英同輸入重播。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL138_OUT:-$r/goal138-retire}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-retire.inputs.json
[[ -x "$bin" && -f "$gui" && -d "$out/fonts" && -f /game/OPENING.EXE ]]
python3 - "$gui" "$out" <<'PY'
import json, sys
gui, out = sys.argv[1:]
data = json.load(open(gui))
payload = {"inputs": [e for e in data["inputs"] if e["step"] <= 1275000000], "end": 1275000000}
json.dump(payload, open(f"{out}/prefix-1275000000.inputs.json", "w"), indent=2, sort_keys=True)
PY
flags=(--window --all-menu --nation-card-a --game-options-title-a --game-options-rows-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --game-options-title-font "$r/goal133-options-rows/title-font.json"
       --game-options-rows-font-dir "$r/goal134-options-rows/row-fonts"
       --retire-a --retire-font-dir "$out/fonts")
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
pids=()
for mode in zh control; do
  extra=()
  [[ $mode == control ]] && extra=(--control)
  for pair in "dialog:$out/prefix-1275000000.inputs.json:1275000000" "closed:$gui:$end"; do
    IFS=: read -r tag inputs steps <<< "$pair"
    [[ ! -e "$out/$tag-$mode.json" ]]
    "$bin" "${flags[@]}" "${extra[@]}" --replay-inputs "$inputs" --window-steps "$steps" \
      --out "$out/$tag-$mode" > "$out/$tag-$mode.log" 2>&1 &
    pids+=($!)
  done
done
wait "${pids[@]}"
echo '目標138重播完成'
