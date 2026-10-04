#!/usr/bin/env bash
# Docker內：正常讀檔、切換檢視模式、點選已探索地形並按F1；只探勘，不修改原版。
set -euo pipefail
base=/repo/workplace/reports/goal180-pedia-rest
export COLONIZATION_GOAL179_OUT=${COLONIZATION_GOAL180_OUT:-$base/context-v2}
export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
export COLONIZATION_DIALOG_ATLAS=${COLONIZATION_DIALOG_ATLAS:-$base/formatted-dialog-atlas/dialog-atlas.json}
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
export COLONIZATION_STRING_TEMPLATES=${COLONIZATION_STRING_TEMPLATES:-$base/final-string-templates.tsv}
export COLONIZATION_PEDIA_STEPS=600000000
script=$(mktemp /tmp/colonization-pedia-context.XXXXXX)
trap 'rm -f "$script"' EXIT
python3 - "$script" <<'PY'
from pathlib import Path
import sys
s=Path('/repo/tools/probe_goal179_gui.sh').read_text()
anchor='click 1128 12\n'
assert s.count(anchor)==1
s=s.split(anchor)[0]+'''key_once v
shot_after view-pieces
# 只走已確認的第一個針葉林位置；原版點選後會置中，不沿用原螢幕座標猜下一格。
points=("544 304")
for ((tile=0;tile<${#points[@]};tile++)); do
  read -r px py <<< "${points[tile]}"
  click "$px" "$py"
  shot_after "context-tile-$tile"
  key_once F1
  shot_after "context-f1-$tile"
  key_once Escape
  shot_after "context-return-$tile"
done
python3 /repo/tools/gui_close_window.py --window "$window"
wait "$game_pid"
'''
Path(sys.argv[1]).write_text(s)
PY
bash "$script"
