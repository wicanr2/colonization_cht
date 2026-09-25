#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標139 真 GUI 錄下的輸入，在翻卡、游標壓上欄、移開、離頁四點做中英同輸入重播與三項負例。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL139_OUT:-$r/goal139-third-card}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-third.inputs.json
[[ -x "$bin" && -f "$gui" && -d "$out/fonts" && -f /game/OPENING.EXE ]]
mkdir -p "$out/empty-fonts"
# 重複鍵負例：唯一 TSV 內第三卡上欄出現兩次，必須兩欄之一以上回原文。
awk -F'\t' '{print} $1=="NAMES.TXT:0x00000C22"{print}' /repo/text/draft.zh-Hant.tsv > "$out/duplicate-upper.tsv"
python3 - "$gui" "$out" <<'PY'
import json, sys
gui, out = sys.argv[1:]
data = json.load(open(gui))
for end in (37000000, 38500000, 40000000):
    payload = {"inputs": [e for e in data["inputs"] if e["step"] <= end], "end": end}
    json.dump(payload, open(f"{out}/prefix-{end}.inputs.json", "w"), indent=2, sort_keys=True)
PY
flags=(--window --all-menu --nation-card-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts")
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
run() {  # 名稱 輸入 步數 其他參數…
  local tag=$1 inputs=$2 steps=$3
  shift 3
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "${flags[@]}" "$@" --replay-inputs "$inputs" --window-steps "$steps" \
    --out "$out/$tag" > "$out/$tag.log" 2>&1
}
pids=()
# zh：啟用第三卡；base：同為中文前端但不啟用第三卡（隔離其他已正式欄位）；control：英文無監看。
only=${COLONIZATION_GOAL139_MODES:-zh base control}
for mode in $only; do
  extra=(--third-card-a --third-card-font-dir "$out/fonts")
  [[ $mode == control ]] && extra+=(--control)
  [[ $mode == base ]] && extra=()
  run "card-$mode" "$out/prefix-37000000.inputs.json" 37000000 "${extra[@]}" & pids+=($!)
  run "hover-$mode" "$out/prefix-38500000.inputs.json" 38500000 "${extra[@]}" & pids+=($!)
  run "away-$mode" "$out/prefix-40000000.inputs.json" 40000000 "${extra[@]}" & pids+=($!)
  run "nation-$mode" "$gui" "$end" "${extra[@]}" & pids+=($!)
done
[[ -z ${COLONIZATION_GOAL139_MODES:-} ]] || { wait "${pids[@]}"; echo '目標139重播完成'; exit 0; }
run neg-missing "$out/prefix-37000000.inputs.json" 37000000 --third-card-a --third-card-font-dir "$out/fonts" --missing & pids+=($!)
run neg-duplicate "$out/prefix-37000000.inputs.json" 37000000 --third-card-a --third-card-font-dir "$out/fonts" --catalog "$out/duplicate-upper.tsv" & pids+=($!)
run neg-no-fonts "$out/prefix-37000000.inputs.json" 37000000 --third-card-a --third-card-font-dir "$out/empty-fonts" & pids+=($!)
wait "${pids[@]}"
echo '目標139重播完成'
