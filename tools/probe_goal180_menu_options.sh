#!/usr/bin/env bash
# Docker內：正常鍵盤走訪百科選單，確認呈現項目與環繞邊界；不修改原版。
set -euo pipefail
base=/repo/workplace/reports/goal180-pedia-rest
export COLONIZATION_GOAL179_OUT=${COLONIZATION_GOAL180_OUT:-$base/menu-options}
export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
export COLONIZATION_DIALOG_ATLAS=${COLONIZATION_DIALOG_ATLAS:-$base/formatted-dialog-atlas/dialog-atlas.json}
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
export COLONIZATION_STRING_TEMPLATES=${COLONIZATION_STRING_TEMPLATES:-$base/final-string-templates.tsv}
export COLONIZATION_PEDIA_STEPS=200000000
script=$(mktemp /tmp/colonization-pedia-menu.XXXXXX)
trap 'rm -f "$script"' EXIT
python3 - "$script" <<'PYSCRIPT'
from pathlib import Path
import sys
s=Path('/repo/tools/probe_goal179_gui.sh').read_text()
anchor='category=${COLONIZATION_PEDIA_CATEGORY:-cargo}'
assert s.count(anchor)==1
s=s.split(anchor)[0]+"""for ((choice=0;choice<8;choice++)); do
  key_once Down
  shot_after "pedia-down-$choice"
done
enter_once
shot_after pedia-keyboard-enter
key_once Escape
shot_after pedia-keyboard-return
python3 /repo/tools/gui_close_window.py --window "$window"
wait "$game_pid"
"""
Path(sys.argv[1]).write_text(s)
PYSCRIPT
bash "$script"
