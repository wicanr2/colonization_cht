#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標142 真 GUI 錄下的輸入重播首則教學提示，中英同輸入四個檢查點，另跑三項負例。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL142_OUT:-$r/goal142-help}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-help.inputs.json
[[ -x "$bin" && -f "$gui" && -d "$out/fonts" && -f /game/OPENING.EXE ]]
mkdir -p "$out/empty-fonts"
awk -F'\t' '{print} $1=="GAME.TXT:@TUTORIAL1"{print}' /repo/text/help-bilingual.tsv > "$out/duplicate-help.tsv"
python3 - "$gui" "$out/prefix-580000000.inputs.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in data["inputs"] if e["step"] <= 580000000], "end": 580000000},
          open(sys.argv[2], "w"), indent=2, sort_keys=True)
PY
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
flags=(--window --all-menu --nation-card-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --tutorial-help-a)
run() {  # 名稱 終點 輸入 其他參數…
  local tag=$1 steps=$2 inputs=$3
  shift 3
  if [[ -n ${COLONIZATION_GOAL142_ONLY:-} && " $COLONIZATION_GOAL142_ONLY " != *" $tag "* ]]; then return 0; fi
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "${flags[@]}" "$@" --replay-inputs "$inputs" --window-steps "$steps" --out "$out/$tag" > "$out/$tag.log" 2>&1
}
cps=575000000,585000000,592000000,620000000
prefix=$out/prefix-580000000.inputs.json
pids=()
run replay-zh "$end" "$gui" --help-mask-dir "$out/fonts" --checkpoint-steps "$cps" & pids+=($!)
run replay-control "$end" "$gui" --help-mask-dir "$out/fonts" --checkpoint-steps "$cps" --control & pids+=($!)
run neg-missing 580000000 "$prefix" --help-mask-dir "$out/fonts" --missing & pids+=($!)
run neg-no-fonts 580000000 "$prefix" --help-mask-dir "$out/empty-fonts" & pids+=($!)
run neg-duplicate 580000000 "$prefix" --help-mask-dir "$out/fonts" --help-catalog "$out/duplicate-help.tsv" & pids+=($!)
wait "${pids[@]}"
echo '目標142重播完成'
