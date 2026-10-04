#!/usr/bin/env bash
# Docker內：由正常存檔檢查移動模式與單位啟用；保留目標172新局探勘入口。
set -euo pipefail
base=/repo/workplace/reports/goal180-pedia-rest
route=${COLONIZATION_GOAL181_ROUTE:-load-unit-v6}
target=${COLONIZATION_GOAL181_OUT:-/repo/workplace/reports/goal181-colony-rest/$route}
[[ ! -e "$target" && -d "$(dirname "$target")" && $(stat -c %u "$(dirname "$target")") == $(id -u) ]]
[[ $(stat -c %g "$(dirname "$target")") == $(id -g) ]]
if [[ "$route" == city-load-v1 || "$route" == city-jobs-v2 || "$route" == city-lumber-v3 || "$route" == city-join-v4 || "$route" == city-turn-v5 || "$route" == city-stock-v6 || "$route" == city-buy-v7 || "$route" == city-buy-v9 || "$route" == city-more-v18 || "$route" == city-equip-v19 || "$route" == city-arms-v20 || "$route" == city-abandon-v23 ]]; then
  export COLONIZATION_GOAL179_OUT=$target
  export COLONIZATION_GOAL179_SAVE=/repo/workplace/reports/goal181-colony-rest/load-unit-v10/scratch/COLONY01.SAV
  export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
  export COLONIZATION_DIALOG_ATLAS=$base/formatted-dialog-atlas/dialog-atlas.json
  export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
  export COLONIZATION_STRING_TEMPLATES=${COLONIZATION_STRING_TEMPLATES:-$base/final-string-templates.tsv}
  export COLONIZATION_PEDIA_STEPS=200000000
  [[ "$route" != city-buy-v7 && "$route" != city-buy-v9 ]] || export COLONIZATION_PEDIA_STEPS=400000000
  script=$(mktemp /tmp/colonization-city-load.XXXXXX)
  trap '[[ ! -d "$target" ]] || cp "$script" "$target/probe-source.sh"; rm -f "$script"' EXIT
  python3 - "$script" "$route" <<'PY'
from pathlib import Path
import sys
s=Path('/repo/tools/probe_goal179_gui.sh').read_text()
old='cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e'
assert s.count(old)==1
s=s.replace(old,'c27b44665f1a229ca5257ac8f23b2f63dc025d5814aa5172742ffcd69939e647')
s=s.replace('out=$target/gui-pedia','out=$target/gui-colony')
# 移開游標後留足呈現畫格；狀態檔先於 X11 畫面更新，原失敗收據保留。
assert s.count('  move_to 64 64\n  s=$(gui_step)')==1
s=s.replace('  move_to 64 64\n  s=$(gui_step)',
            '  move_to 64 64\n  wait_step $(( $(gui_step)+1200000 ))\n  s=$(gui_step)')
assert s.count('click 620 312\n')==1
s=s.replace('click 620 312\n','click 620 336\n')
anchor='click 1128 12\n'
assert s.count(anchor)==1
s=s.split(anchor)[0]+'''click 608 520
shot_after city-response
'''
if sys.argv[2] in ('city-jobs-v2','city-lumber-v3','city-join-v4','city-turn-v5','city-stock-v6','city-buy-v7','city-buy-v9','city-more-v18','city-equip-v19','city-arms-v20','city-abandon-v23'):
    s+='''click 920 172
shot_after worker-jobs
'''
if sys.argv[2] in ('city-more-v18','city-equip-v19','city-arms-v20','city-abandon-v23'):
    s+='''click 350 668
shot_after worker-more
'''
if sys.argv[2]=='city-abandon-v23':
    s+='''click 350 392
shot_after abandon-confirm
click 350 614
shot_after abandon-cancelled
'''
if sys.argv[2] in ('city-equip-v19','city-arms-v20'):
    s+='''click 350 392
shot_after pioneer-equipped
click 1138 736
shot_after arms-response
'''
if sys.argv[2]=='city-arms-v20':
    s+='''click 350 614
shot_after abandon-cancelled
click 1138 736
shot_after muskets-response
'''
if sys.argv[2] in ('city-lumber-v3','city-join-v4','city-turn-v5','city-stock-v6','city-buy-v7','city-buy-v9'):
    s+='''click 350 316
shot_after lumber-selected
key_once Escape
shot_after colony-exited
key_once space
shot_after turn-response
current=$(gui_step)
wait_step $((current+20000000))
shot_after turn-settled
'''
if sys.argv[2]=='city-join-v4':
    s+='''enter_once
shot_after soldier-active
key_once b
shot_after join-response
'''
if sys.argv[2] in ('city-turn-v5','city-stock-v6','city-buy-v7','city-buy-v9'):
    s+='''enter_once
shot_after soldier-active
key_once space
shot_after next-unit
enter_once
current=$(gui_step)
wait_step $((current+20000000))
shot_after end-turn-response
'''
if sys.argv[2] in ('city-stock-v6','city-buy-v7','city-buy-v9'):
    s+='''enter_once
shot_after father-selected
enter_once
current=$(gui_step)
wait_step $((current+12000000))
shot_after next-year
click 608 520
shot_after colony-stock
'''
if sys.argv[2] in ('city-buy-v7','city-buy-v9'):
    s+='''click 920 172
shot_after carpenter-menu
click 350 570
shot_after carpenter-selected
key_once Escape
shot_after carpenter-colony-exited
key_once space
shot_after carpenter-ship-skipped
key_once space
shot_after carpenter-soldier-skipped
enter_once
current=$(gui_step)
wait_step $((current+12000000))
shot_after carpenter-next-year
'''
    if sys.argv[2]=='city-buy-v9':
        s+='''enter_once
shot_after immigration-dismissed
enter_once
shot_after carpenter-tutorial-dismissed
'''
    s+='''click 608 520
shot_after carpenter-stock
click 1244 676
shot_after progressed-build-panel
click 896 568
shot_after payable-buy
'''
s+='''python3 /repo/tools/gui_close_window.py --window "$window"
wait "$game_pid"
'''
Path(sys.argv[1]).write_text(s)
PY
  bash "$script"
  exit 0
fi
if [[ "$route" == load-unit-v4 || "$route" == load-unit-v5 || "$route" == load-unit-v6 || "$route" == load-unit-v7 || "$route" == load-unit-v8 || "$route" == load-unit-v9 || "$route" == load-unit-v10 ]]; then
  export COLONIZATION_GOAL179_OUT=$target
  export COLONIZATION_WINDOW_BIN=$base/sync-final-build/colonization-window
  export COLONIZATION_DIALOG_ATLAS=$base/formatted-dialog-atlas/dialog-atlas.json
  export COLONIZATION_STRING_ATLAS=$base/final-string-atlas/string-atlas.json
  export COLONIZATION_STRING_TEMPLATES=$base/final-string-templates.tsv
  export COLONIZATION_PEDIA_STEPS=360000000
  script=$(mktemp /tmp/colonization-colony-unit.XXXXXX)
  trap '[[ ! -d "$target" ]] || cp "$script" "$target/probe-source.sh"; rm -f "$script"' EXIT
  python3 - "$script" "$route" <<'PY'
from pathlib import Path
import sys
s=Path('/repo/tools/probe_goal179_gui.sh').read_text()
anchor='click 1128 12\n'
assert s.count(anchor)==1
s=s.split(anchor)[0]+'''click 250 12
shot_after view-menu
key_once Home
enter_once
shot_after movement-mode
click 608 520
shot_after selected-land-unit
key_once b
shot_after build-response
python3 /repo/tools/gui_close_window.py --window "$window"
wait "$game_pid"
'''
s=s.replace('out=$target/gui-pedia','out=$target/gui-colony')
if sys.argv[2] in ('load-unit-v5','load-unit-v6','load-unit-v7','load-unit-v8','load-unit-v9','load-unit-v10'):
    anchor='python3 /repo/tools/gui_close_window.py --window "$window"\n'
    assert s.count(anchor)==1
    extra='''python3 /repo/tools/gui_auto.py --out "$out" --window "$window" --pid "$game_pid" \\
  --intents "b,Return" --answers "Exit to DOS=Escape" \\
  --idle 8000000 --delay 4000000 --start 80000000 --end 240000000 --after 6000000 \\
  --intent-shots-from 80000000 > "$out.auto.log"
'''
    if sys.argv[2] in ('load-unit-v6','load-unit-v7','load-unit-v8','load-unit-v9','load-unit-v10'):
        extra+='''click 1244 676
shot_after production-panel
click 896 568
shot_after buy-response
'''
    if sys.argv[2] in ('load-unit-v7','load-unit-v8','load-unit-v9','load-unit-v10'):
        extra+='''key_once Escape
shot_after buy-closed
click 1136 568
shot_after build-list
'''
    if sys.argv[2]=='load-unit-v8':
        extra+='''key_once End
shot_after build-last-item
enter_once
shot_after build-last-selected
click 1244 676
shot_after wagon-panel
click 896 568
shot_after wagon-buy-response
key_once Escape
click 20 584
shot_after dock-unit-profession
'''
    if sys.argv[2] in ('load-unit-v9','load-unit-v10'):
        extra+='''for ((choice=0;choice<9;choice++)); do key_once Down; done
shot_after wagon-highlight
enter_once
shot_after wagon-selected
click 896 568
shot_after wagon-buy-response
key_once Escape
shot_after wagon-buy-closed
click 1244 676
shot_after production-closed
key_once Escape
shot_after colony-exited
'''
    if sys.argv[2]=='load-unit-v9':
        extra+='''
key_once ctrl+s
shot_after save-dialog
enter_once
shot_after colony-saved
'''
    if sys.argv[2]=='load-unit-v10':
        extra+='''click 96 12
shot_after game-menu
click 192 252
shot_after save-slots
click 480 336
shot_after save-name
enter_once
shot_after colony-saved
'''
    s=s.replace(anchor,extra+anchor)
Path(sys.argv[1]).write_text(s)
PY
  bash "$script"
  exit 0
fi
[[ "$route" == colony-v3 ]]
mkdir "$target"
export COLONIZATION_GOAL172_GUI_OUT=$target/gui-colony
export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
export COLONIZATION_DIALOG_ATLAS=${COLONIZATION_DIALOG_ATLAS:-$base/formatted-dialog-atlas/dialog-atlas.json}
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ardelay 60000 >/tmp/colonization-xvfb.log 2>&1 &
xp=$!
script=$(mktemp /tmp/colonization-colony-route.XXXXXX)
trap 'kill "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true; rm -f "$script"' EXIT
python3 - "$script" <<'PY'
from pathlib import Path
import sys
s=Path('/repo/tools/probe_goal172_gui.sh').read_text()
s=s.replace('source "$(dirname "$0")/gui_step_input.sh"','source /repo/tools/gui_step_input.sh')
s=s.replace('python3 "$(dirname "$0")/gui_auto.py"','python3 /repo/tools/gui_auto.py')
Path(sys.argv[1]).write_text(s)
PY
cp "$script" "$target/probe-source.sh"
bash "$script"
