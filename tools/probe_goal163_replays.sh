#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標163 以真 GUI 輸入重播中文與英文控制，並以「移除全部 key 事件」做反向對照。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL163_OUT:-$r/goal163-keys}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-keys.inputs.json
atlas=${COLONIZATION_SEA_ATLAS:-$r/goal143-sea/atlas/sea-atlas.json}
[[ -x "$bin" && -f "$gui" && -f "$atlas" && -f /game/OPENING.EXE ]]
python3 - "$gui" "$out/neg-nokeys.inputs.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in d["inputs"] if e["kind"] != "key"], "end": d["end"]}, open(sys.argv[2], "w"), indent=2, sort_keys=True)
PY
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --sea-status-a --sea-atlas "$atlas" --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --checkpoint-steps 590000000,612000000,640000000,670000000,705000000 --window-steps "$end")
run() { local tag=$1; shift; [[ ! -e "$out/$tag.json" ]]; "$bin" "${flags[@]}" "$@" --out "$out/$tag" > "$out/$tag.log" 2>&1; }
run replay-zh --replay-inputs "$gui" &
run replay-control --replay-inputs "$gui" --control &
run neg-nokeys --replay-inputs "$out/neg-nokeys.inputs.json" &
wait
echo '目標163重播完成'
