#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標150 動態覆蓋綜合驗證。
# 1) 海上欄以多字級圖集重跑目標143 輸入（應與目標143 逐像素相同）；2) 縮字與超長回原文；
# 3) 全部欄位旗標同時開，Explorer 無跳過路徑（字幕→海上→遊戲選項）與 Discoverer 路徑（help），各跑中文與英文控制。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL150_OUT:-$r/goal150-dynamic}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
full=/repo/tools/goal150-full-path.inputs.json
sea=$r/goal143-sea/gui-sea.inputs.json
help=$r/goal142-help/gui-help.inputs.json
[[ -x "$bin" && -f "$full" && -f "$sea" && -f "$help" && -f "$out/atlas/sea-atlas.json" && -f /game/OPENING.EXE ]]
python3 - "$sea" "$out/sea-prefix-620000000.inputs.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in d["inputs"] if e["step"] <= 620000000], "end": 620000000}, open(sys.argv[2], "w"), indent=2, sort_keys=True)
PY
base=(--window --root /game --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified")
all=("${base[@]}" --all-menu --nation-card-a
     --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
     --nation-cards-rest-a --nation-cards-rest-font-dir "$r/goal140-nation-cards/fonts"
     --third-card-a --third-card-font-dir "$r/goal139-third-card/fonts"
     --nation-intro-a --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$r/goal136-nation-intro/masks"
     --build1-a --build1-font "$r/goal133-options-rows/build1-font.json"
     --build-captions-a --build-caption-font-dir "$r/goal141-captions/fonts"
     --tutorial-help-a --help-mask-dir "$r/goal142-help/fonts"
     --sea-status-a --sea-atlas "$out/atlas/sea-atlas.json"
     --game-options-title-a --game-options-title-font "$r/goal133-options-rows/title-font.json"
     --game-options-rows-a --game-options-rows-font-dir "$r/goal134-options-rows/row-fonts"
     --retire-a --retire-font-dir "$r/goal138-retire/fonts")
seaflags=("${base[@]}" --all-menu --nation-card-a
     --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts" --sea-status-a)
run() {  # 名稱 終點 輸入 參數…
  local tag=$1 steps=$2 inputs=$3
  shift 3
  if [[ -n ${COLONIZATION_GOAL150_ONLY:-} && " $COLONIZATION_GOAL150_ONLY " != *" $tag "* ]]; then return 0; fi
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "$@" --replay-inputs "$inputs" --window-steps "$steps" --out "$out/$tag" > "$out/$tag.log" 2>&1
}
seaend=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$sea")
helpend=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$help")
pids=()
run sea-regress "$seaend" "$sea" "${seaflags[@]}" --sea-atlas "$out/atlas/sea-atlas.json" \
  --checkpoint-steps 565000000,590000000,612000000,652000000,662000000,672000000 & pids+=($!)
run shrink-long 620000000 "$out/sea-prefix-620000000.inputs.json" "${seaflags[@]}" \
  --sea-catalog "$out/long.tsv" --sea-atlas "$out/atlas-long/sea-atlas.json" & pids+=($!)
run shrink-toolong 620000000 "$out/sea-prefix-620000000.inputs.json" "${seaflags[@]}" \
  --sea-catalog "$out/toolong.tsv" --sea-atlas "$out/atlas-toolong/sea-atlas.json" & pids+=($!)
fullcp=60000000,110000000,238000000,590000000,1132000000,1215000000,1280000000
run full-zh 1290000000 "$full" "${all[@]}" --checkpoint-steps "$fullcp" & pids+=($!)
run full-control 1290000000 "$full" "${all[@]}" --control --checkpoint-steps "$fullcp" & pids+=($!)
run help-zh "$helpend" "$help" "${all[@]}" --checkpoint-steps 575000000,620000000 & pids+=($!)
run help-control "$helpend" "$help" "${all[@]}" --control --checkpoint-steps 575000000,620000000 & pids+=($!)
wait "${pids[@]}"
echo '目標150重播完成'
