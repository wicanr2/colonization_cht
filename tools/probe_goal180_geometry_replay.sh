#!/usr/bin/env bash
# Docker 內只觀測正常 GUI 輸入的固定前綴；不是新增玩家驗收。
set -euo pipefail
category=${1:?請指定 job、father、building 或 terrain}
case "$category" in job) end=230000000 ;; father) end=650000000 ;; building) end=1187600000 ;; terrain) end=800000000 ;; *) exit 2 ;; esac
end=${COLONIZATION_GOAL180_GEOMETRY_END:-$end}
prefix=${COLONIZATION_GOAL180_GEOMETRY_PREFIX:-geometry-body}
[[ $prefix =~ ^[a-z][a-z0-9-]*$ ]] || exit 2
r=/repo/workplace/reports
target=${COLONIZATION_GOAL180_GEOMETRY_OUT:-$r/goal180-pedia-rest/$category}
bin=${COLONIZATION_GOAL180_GEOMETRY_BIN:-$r/goal180-pedia-rest/diagnostic-build-v5/colonization-window}
seed=$r/goal178-orders/codex-audit/load-route-v2/scratch/COLONY00.SAV
[[ -f /game/OPENING.EXE && -f "$seed" ]] || exit 77
[[ -x "$bin" && ! -e "$target/$prefix.json" && ! -e "$target/$prefix-save" ]]
[[ $(stat -c %u "$target") == $(id -u) ]]
[[ $(sha256sum "$seed" | cut -d' ' -f1) == cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e ]]
python3 - "$target" "$end" "$prefix" <<'PY'
import json, sys
from pathlib import Path
p, end, prefix = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
d = json.loads((p / "gui-pedia.inputs.json").read_text())
assert end <= d["end"] and not d.get("rejected")
d["inputs"] = [e for e in d["inputs"] if e["step"] <= end]
d["end"] = end
(p / (prefix + ".inputs.json")).write_text(json.dumps(d))
PY
mkdir "$target/$prefix-save"
cp "$seed" "$target/$prefix-save/COLONY00.SAV"
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp >/tmp/xvfb.log 2>&1 & xp=$!
trap 'kill "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true' EXIT
steps=$(awk -v end="$end" '$2<=end {print $2}' "$target/gui-pedia.shots" | paste -sd,)
"$bin" --window --all-menu --root /game --scratch "$target/$prefix-save" \
  --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified" \
  --sea-status-a --sea-atlas "$r/goal143-sea/atlas/sea-atlas.json" \
  --dialog-a --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}" \
  --dialog-pedia "${COLONIZATION_DIALOG_PEDIA:-/repo/text/pedia-bilingual.tsv}" \
  --string-a --string-atlas "${COLONIZATION_STRING_ATLAS:-$r/goal174-input/atlas/string-atlas.json}" \
  --string-templates "${COLONIZATION_STRING_TEMPLATES:-/repo/text/string-templates.zh-Hant.tsv}" \
  --replay-inputs "$target/$prefix.inputs.json" --window-steps "$end" \
  --checkpoint-steps "$steps" --out "$target/$prefix" >"$target/$prefix.log" 2>&1
