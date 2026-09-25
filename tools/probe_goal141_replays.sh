#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標141無跳過輸入重播十張開場字幕，中英同輸入並於每張字幕同步後 30M 步另存檢查點；另跑三項負例。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL141_OUT:-$r/goal141-captions}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
inputs=${COLONIZATION_GOAL141_INPUTS:-/repo/tools/goal141-captions.inputs.json}
[[ -x "$bin" && -f "$inputs" && -d "$out/fonts" && -f "$r/goal133-options-rows/build1-font.json" && -f /game/OPENING.EXE ]]
mkdir -p "$out/empty-fonts"
# 負例只跑到第三張字幕（350M），另產同輸入的前綴檔。
python3 - "$inputs" "$out/prefix-350000000.inputs.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in data["inputs"] if e["step"] <= 350000000], "end": 350000000},
          open(sys.argv[2], "w"), indent=2, sort_keys=True)
PY
# 重複鍵負例：@BUILD3 譯稿列出現兩次；變數負例：英格蘭 @BUILD3 的 London 原文被改。
awk -F'\t' '{print} $1=="GAME.TXT:0x00015482"{print}' /repo/text/draft.zh-Hant.tsv > "$out/duplicate-build3.tsv"
awk -F'\t' 'BEGIN{OFS="\t"} $1=="england" && $2=="@BUILD3" {$9="Londen"; $10="Londen"} {print}' \
  /repo/text/build-caption-values.zh-Hant.tsv > "$out/values-wrong-build3.tsv"
checkpoints=110000000,238000000,348000000,484000000,590000000,699000000,807000000,915000000,1024000000,1132000000
flags=(--window --all-menu --nation-card-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts"
       --build1-a --build1-font "$r/goal133-options-rows/build1-font.json"
       --build-captions-a --build-caption-font-dir "$out/fonts")
run() {  # 名稱 終點步數 其他參數…
  local tag=$1 steps=$2
  shift 2
  if [[ -n ${COLONIZATION_GOAL141_ONLY:-} && " $COLONIZATION_GOAL141_ONLY " != *" $tag "* ]]; then return 0; fi
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "${flags[@]}" "$@" --window-steps "$steps" --out "$out/$tag" > "$out/$tag.log" 2>&1
}
pids=()
prefix=$out/prefix-350000000.inputs.json
run replay-zh 1225000000 --replay-inputs "$inputs" --checkpoint-steps "$checkpoints" & pids+=($!)
run replay-control 1225000000 --replay-inputs "$inputs" --checkpoint-steps "$checkpoints" --control & pids+=($!)
run neg-missing 350000000 --replay-inputs "$prefix" --missing & pids+=($!)
run neg-no-fonts 350000000 --replay-inputs "$prefix" --build-caption-font-dir "$out/empty-fonts" & pids+=($!)
run neg-duplicate 350000000 --replay-inputs "$prefix" --catalog "$out/duplicate-build3.tsv" & pids+=($!)
run neg-values 350000000 --replay-inputs "$prefix" --build-values "$out/values-wrong-build3.tsv" & pids+=($!)
wait "${pids[@]}"
echo '目標141重播完成'
