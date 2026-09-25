#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以目標140 真 GUI 錄下的輸入，在三國選卡、游標壓欄、移開與離頁六點做中英同輸入重播與三項負例。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL140_OUT:-$r/goal140-nation-cards}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-cards.inputs.json
[[ -x "$bin" && -f "$gui" && -d "$out/fonts" && -f /game/OPENING.EXE ]]
mkdir -p "$out/empty-fonts"
# 重複鍵負例：旗卡片段 TSV 內西班牙國名出現兩次。
awk -F'\t' '{print} $1=="NAMES.TXT:0x00000921"{print}' /repo/text/nation-card-fragments.zh-Hant.tsv > "$out/duplicate-spain.tsv"
python3 - "$gui" "$out" <<'PY'
import json, sys
gui, out = sys.argv[1:]
data = json.load(open(gui))
for end in (46500000, 49500000, 52500000, 54000000, 55500000, 60000000):
    payload = {"inputs": [e for e in data["inputs"] if e["step"] <= end], "end": end}
    json.dump(payload, open(f"{out}/prefix-{end}.inputs.json", "w"), indent=2, sort_keys=True)
PY
flags=(--window --all-menu --nation-card-a --root /game
       --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
       --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv --nation-card-font-dir "$r/goal099-card-fonts")
run() {  # 名稱 終點步數 其他參數…
  local tag=$1 steps=$2
  shift 2
  # COLONIZATION_GOAL140_ONLY：以空白分隔的組名，只補跑這些組。
  if [[ -n ${COLONIZATION_GOAL140_ONLY:-} && " $COLONIZATION_GOAL140_ONLY " != *" $tag "* ]]; then return 0; fi
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "${flags[@]}" "$@" --replay-inputs "$out/prefix-$steps.inputs.json" --window-steps "$steps" \
    --out "$out/$tag" > "$out/$tag.log" 2>&1
}
rest=(--nation-cards-rest-a --nation-cards-rest-font-dir "$out/fonts")
pids=()
# zh：啟用其餘旗卡；base：同為中文前端但不啟用（隔離第一張旗卡等既有欄位）；control：英文無監看。
for point in france:46500000 spain:49500000 netherlands:52500000 cursor:54000000 away:55500000 name:60000000; do
  IFS=: read -r tag steps <<< "$point"
  run "$tag-zh" "$steps" "${rest[@]}" & pids+=($!)
  run "$tag-base" "$steps" & pids+=($!)
  run "$tag-control" "$steps" "${rest[@]}" --control & pids+=($!)
done
run neg-missing 49500000 "${rest[@]}" --missing & pids+=($!)
run neg-no-fonts 49500000 --nation-cards-rest-a --nation-cards-rest-font-dir "$out/empty-fonts" & pids+=($!)
run neg-duplicate 49500000 "${rest[@]}" --nation-card-catalog "$out/duplicate-spain.tsv" & pids+=($!)
wait "${pids[@]}"
echo '目標140重播完成'
