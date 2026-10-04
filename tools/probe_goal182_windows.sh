#!/usr/bin/env bash
# Docker內：以Wine驗證Windows中間物的完整啟動旗標及正常主選單；非Windows真機驗收。
set -euo pipefail
base=/repo/workplace/reports/goal182-platform-preflight
out=${COLONIZATION_WINDOWS_GUI_OUT:-$base/windows-gui-v2}
stage=/repo/workplace/reports/goal178-orders/codex-audit/staged-package
current=/repo/workplace/reports/goal180-pedia-rest
[[ -f /game/OPENING.EXE && -f "$base/colonization-window.exe" && -d "$stage" ]]
[[ $(stat -c %u "$base") == $(id -u) && $(stat -c %g "$base") == $(id -g) && ! -e "$out.json" ]]
mkdir -p "$base/windows-save"
[[ $(stat -c %u "$base/windows-save") == $(id -u) && $(stat -c %g "$base/windows-save") == $(id -g) ]]
export WINEPREFIX=$base/wine-prefix WINEDEBUG=-all HOME=/tmp DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1600x1000x24 -nolisten tcp -ardelay 60000 >/tmp/colonization-wine-xvfb.log 2>&1 &
xp=$!
game_pid=
trap '[[ -z "$game_pid" ]] || kill "$game_pid" 2>/dev/null || true; wineserver -k 2>/dev/null || true; kill "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true' EXIT
python3 - "$base" "$stage" "$current" "$out" <<'PY'
from pathlib import Path
import json, shlex, sys
base,stage,current,out=map(Path,sys.argv[1:])
source=Path('/repo/tools/release/colonization-cht.sh').read_text()
tokens=shlex.split(source.split('\nexec ',1)[1].replace('\\\n',' '))
assert tokens[-1]=='${args[@]}'
values={'$here/bin/colonization-window':str(base/'colonization-window.exe'),
        '$m':str(stage/'masks'),'$t':'/repo/text','$game':'/game',
        '$save':str(base/'windows-save')}
args=[]
for token in tokens[:-1]:
    if token=='--play':
        continue
    for key,value in values.items():
        token=token.replace(key,value)
    args.append('Z:'+token if token.startswith('/') else token)
for flag,value in (('--out',out),('--dialog-atlas',current/'formatted-dialog-atlas/dialog-atlas.json'),
                   ('--string-atlas',current/'final-string-atlas/string-atlas.json')):
    args[args.index(flag)+1]='Z:'+str(value)
args.extend(['--audio-mute','--window-steps','50000000'])
assert args[0]=='Z:'+str(base/'colonization-window.exe')
Path(str(out)+'.arguments.json').write_text(json.dumps(['wine']+args,ensure_ascii=False,indent=2)+'\n')
PY
python3 - "$out.arguments.json" > "$out.log" 2>&1 <<'PY' &
import json, subprocess, sys
raise SystemExit(subprocess.run(json.load(open(sys.argv[1]))).returncode)
PY
game_pid=$!
window=
for ((i=0; i<600; i++)); do
  window=$(xdotool search --onlyvisible --name 'Colonization CHT prototype' 2>/dev/null | head -1 || true)
  [[ -n "$window" ]] && break
  kill -0 "$game_pid" 2>/dev/null || { cat "$out.log"; exit 1; }
  sleep .1
done
[[ -n "$window" ]]
xdotool windowfocus "$window"
source /repo/tools/gui_step_input.sh
wait_step 3000000
enter_once
wait_step 12000000
click 640 400
wait_stage menu
move_to 64 64
step=$(gui_step)
import -window "$window" "$out.main-menu.png"
echo "main-menu $step" > "$out.shots"
wait "$game_pid"
game_pid=
[[ -f "$out.json" && -f "$out.memory" && -f "$out.inputs.json" ]]
echo 'Windows中間物的正常主選單擷取完成；後續需核對字模與原版狀態。'
