#!/usr/bin/env bash
# 只在有界 Docker 內：目標151 靜態覆蓋同輸入重播（中文、英文控制）與負例（缺字模、字模目錄空、譯稿改動、重複鍵）。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL151_OUT:-$r/goal151-static}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
gui=$out/gui-opening.inputs.json
masks=$out/masks
[[ -x "$bin" && -f "$gui" && -d "$masks" && -f /game/OPENING.EXE ]]
mkdir -p "$out/replay" "$out/neg/empty-masks"
python3 - "$gui" "$out/neg/prefix-470000000.inputs.json" /repo/text/static-overlay.zh-Hant.tsv "$out/neg" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in d["inputs"] if e["step"] <= 470000000], "end": 470000000}, open(sys.argv[2], "w"), indent=2, sort_keys=True)
lines = open(sys.argv[3], encoding="utf-8").read().rstrip("\n").split("\n")
design = next(l for l in lines if ":role:design\t" in l)
cells = design.split("\t")
cells[7] = cells[7] + "者"  # 譯文改動但未重烘字模
open(sys.argv[4] + "/edited.tsv", "w", encoding="utf-8").write("\n".join(l if l != design else "\t".join(cells) for l in lines) + "\n")
open(sys.argv[4] + "/duplicate.tsv", "w", encoding="utf-8").write("\n".join(lines + [design]) + "\n")
PY
base=(--window --all-menu --nation-card-a --root /game --catalog /repo/text/draft.zh-Hant.tsv
      --font-dir "$r/goal096-fonts-verified" --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv
      --nation-card-font-dir "$r/goal099-card-fonts" --static-credits-a)
run() {  # 名稱 終點 輸入 參數…
  local tag=$1 steps=$2 inputs=$3
  shift 3
  if [[ -n ${COLONIZATION_GOAL151_ONLY:-} && " $COLONIZATION_GOAL151_ONLY " != *" $tag "* ]]; then return 0; fi
  [[ ! -e "$out/$tag.json" ]]
  "$bin" "$@" --replay-inputs "$inputs" --window-steps "$steps" --out "$out/$tag" > "$out/$tag.log" 2>&1
}
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$gui")
cp=320000000,460000000,480000000,555000000,655000000,810000000,960000000,1060000000,1115000000
neg=$out/neg/prefix-470000000.inputs.json
pids=()
run replay/zh "$end" "$gui" "${base[@]}" --static-mask-dir "$masks" --checkpoint-steps "$cp" & pids+=($!)
run replay/control "$end" "$gui" "${base[@]}" --static-mask-dir "$masks" --control --checkpoint-steps "$cp" & pids+=($!)
run neg/missing 470000000 "$neg" "${base[@]}" --static-mask-dir "$masks" --missing --checkpoint-steps 460000000 & pids+=($!)
run neg/nomasks 470000000 "$neg" "${base[@]}" --static-mask-dir "$out/neg/empty-masks" --checkpoint-steps 460000000 & pids+=($!)
run neg/edited 470000000 "$neg" "${base[@]}" --static-mask-dir "$masks" --static-catalog "$out/neg/edited.tsv" --checkpoint-steps 460000000 & pids+=($!)
run neg/duplicate 470000000 "$neg" "${base[@]}" --static-mask-dir "$masks" --static-catalog "$out/neg/duplicate.tsv" --checkpoint-steps 460000000 & pids+=($!)
wait "${pids[@]}"
echo '目標151重播完成'
