#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標143 真 GUI 錄下的輸入重播海上頂列與狀態欄，中英同輸入六個檢查點；
# 另跑四項負例，以及與遊戲選項視窗並用的組合重播。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL143_OUT:-$r/goal143-sea}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-sea.inputs.json
atlas=$out/atlas/sea-atlas.json
[[ -x "$bin" && -f "$gui" && -f "$atlas" && -f /game/OPENING.EXE ]]
# 重複鍵負例：Ocean 列重複；缺詞負例：移除 Ocean 列（該行應保留英文，其他行照常中文）。
awk -F'\t' '{print} $7=="Ocean"{print}' /repo/text/sea-status.zh-Hant.tsv > "$out/duplicate-ocean.tsv"
awk -F'\t' '$7!="Ocean"' /repo/text/sea-status.zh-Hant.tsv > "$out/missing-ocean.tsv"
# 缺詞負例的圖集須由同一份缺詞 TSV 以 tools/bake_sea_atlas.py 事先烘到 atlas-missing-ocean/（圖集綁定詞典雜湊）。
[[ -f "$out/atlas-missing-ocean/sea-atlas.json" ]]
python3 - "$gui" "$out/prefix-620000000.inputs.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in data["inputs"] if e["step"] <= 620000000], "end": 620000000},
          open(sys.argv[2], "w"), indent=2, sort_keys=True)
PY
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --sea-status-a)
run() {  # 名稱 終點 輸入 其他參數…
  local tag=$1 steps=$2 inputs=$3
  shift 3
  if [[ -n ${COLONIZATION_GOAL143_ONLY:-} && " $COLONIZATION_GOAL143_ONLY " != *" $tag "* ]]; then return 0; fi
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "${flags[@]}" "$@" --replay-inputs "$inputs" --window-steps "$steps" --out "$out/$tag" > "$out/$tag.log" 2>&1
}
cps=565000000,590000000,612000000,652000000,662000000,672000000
prefix=$out/prefix-620000000.inputs.json
pids=()
run replay-zh "$end" "$gui" --sea-atlas "$atlas" --checkpoint-steps "$cps" & pids+=($!)
run replay-control "$end" "$gui" --sea-atlas "$atlas" --checkpoint-steps "$cps" --control & pids+=($!)
run neg-missing 620000000 "$prefix" --sea-atlas "$atlas" --missing & pids+=($!)
run neg-no-atlas 620000000 "$prefix" --sea-atlas "$out/absent-atlas.json" & pids+=($!)
run neg-duplicate 620000000 "$prefix" --sea-atlas "$atlas" --sea-catalog "$out/duplicate-ocean.tsv" & pids+=($!)
run neg-missing-word 620000000 "$prefix" --sea-atlas "$out/atlas-missing-ocean/sea-atlas.json" --sea-catalog "$out/missing-ocean.tsv" & pids+=($!)
# 組合：與遊戲選項標題／八列並用，1280M 選項視窗開啟時兩者各自套用。
run combo-options 1280000000 "$r/goal132-options-title-event/window-prefix-1280000000.inputs.json" --sea-atlas "$atlas" \
  --game-options-title-a --game-options-title-font "$r/goal133-options-rows/title-font.json" \
  --game-options-rows-a --game-options-rows-font-dir "$r/goal134-options-rows/row-fonts" & pids+=($!)
wait "${pids[@]}"
echo '目標143重播完成'
