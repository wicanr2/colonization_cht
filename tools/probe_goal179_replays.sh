#!/usr/bin/env bash
# 有界 Docker 內：正常讀檔後逐篇貨物百科的中英與缺圖集反向對照。
set -euo pipefail
r=/repo/workplace/reports
out=${COLONIZATION_GOAL179_OUT:-$r/goal179-pedia-cargo}
bin=${COLONIZATION_WINDOW_BIN:-$r/goal178-orders/codex-audit/rebuild-recovery/colonization-window}
seed=${COLONIZATION_GOAL179_SAVE:-$r/goal178-orders/codex-audit/load-route-v2/scratch/COLONY00.SAV}
if [[ ! -f /game/OPENING.EXE || ! -f "$seed" ]]; then
  echo 'SKIP：缺合法原版或原版正常存檔入口；不宣稱百科驗證完成'
  exit 77
fi
[[ -x "$bin" && -f "$out/gui-pedia.inputs.json" && -f "$out/gui-pedia.shots" ]]
[[ $(stat -c %u "$out") == $(id -u) ]]
[[ $(sha256sum "$seed" | cut -d' ' -f1) == cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e ]]
steps=$(awk '{print $2}' "$out/gui-pedia.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$out/gui-pedia.inputs.json")
flags=(--window --all-menu --root /game --catalog /repo/text/draft.zh-Hant.tsv
  --font-dir "$r/goal096-fonts-verified" --sea-status-a --sea-atlas "$r/goal143-sea/atlas/sea-atlas.json"
  --dialog-a --string-a --string-atlas "${COLONIZATION_STRING_ATLAS:-$r/goal174-input/atlas/string-atlas.json}"
  --string-templates "${COLONIZATION_STRING_TEMPLATES:-/repo/text/string-templates.zh-Hant.tsv}"
  --replay-inputs "$out/gui-pedia.inputs.json" --window-steps "$end" --checkpoint-steps "$steps")
pids=()
trap 'for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; for p in "${pids[@]}"; do wait "$p" 2>/dev/null || true; done' EXIT
run() {
  local tag=$1; shift
  [[ ! -e "$out/$tag.json" && ! -e "$out/$tag-save" ]]
  mkdir "$out/$tag-save"
  cp "$seed" "$out/$tag-save/COLONY00.SAV"
  "$bin" "${flags[@]}" --scratch "$out/$tag-save" "$@" --out "$out/$tag" >"$out/$tag.log" 2>&1
}
run replay-zh --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}" & pids+=($!)
run replay-control --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}" --control & pids+=($!)
run neg-noatlas --dialog-atlas "$out/missing-dialog-atlas.json" & pids+=($!)
failed=0
for p in "${pids[@]}"; do wait "$p" || failed=1; done
((failed==0))
trap - EXIT
