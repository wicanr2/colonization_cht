#!/usr/bin/env bash
# 容器內的正常第三欄讀檔與三側重播；不改原版或注入快照。
set -euo pipefail
mode=${1:-gui}
r=/repo/workplace/reports
target=${COLONIZATION_LOAD_OUT:?須指定新的讀檔收據目錄}
out=$target
seed=${COLONIZATION_LOAD_SAVE:-}
bin=${COLONIZATION_WINDOW_BIN:?須指定已重建前端}
case "$mode" in
 gui)
if [[ ! -f /game/OPENING.EXE || ! -f "$seed" ]]; then echo "SKIP：缺合法原版或正常存檔入口"; exit 77; fi
[[ ! -e "$target" && $(sha256sum "$seed" | cut -d' ' -f1) == f683eb9132406e1dc7de5c90372f933b724b71b78a327551a305ba19d9a7d991 ]]
[[ -d "$(dirname "$target")" && $(stat -c %u "$(dirname "$target")") == $(id -u) ]]
mkdir "$target" "$target/scratch"
cp "$seed" "$target/scratch/"
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -ardelay 60000 >/tmp/xvfb.log 2>&1 &
xp=$!
game_pid=''
trap '[[ -z "$game_pid" ]] || kill -CONT "$game_pid" 2>/dev/null || true; [[ -z "$game_pid" ]] || kill "$game_pid" 2>/dev/null || true; kill "$xp" 2>/dev/null || true; [[ -z "$game_pid" ]] || wait "$game_pid" 2>/dev/null || true; wait "$xp" 2>/dev/null || true' EXIT
out=$target/gui-colony
"$bin" --window --root /game --scratch "$target/scratch" \
  --all-menu --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified" \
  --sea-status-a --sea-atlas "$r/goal143-sea/atlas/sea-atlas.json" \
  --dialog-a --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:?須指定現行圖集}" \
  --string-a --string-atlas "${COLONIZATION_STRING_ATLAS:?須指定現行圖集}" \
  --string-templates "${COLONIZATION_STRING_TEMPLATES:-/repo/text/string-templates.zh-Hant.tsv}" \
  --window-steps "100000000" --out "$out" >"$out.log" 2>&1 &
game_pid=$!
window=''
for ((i=0;i<600;i++)); do
  window=$(xdotool search --name 'Colonization CHT prototype' 2>/dev/null | head -1 || true)
  [[ -z "$window" ]] || break
  sleep .1
done
[[ -n "$window" ]]
xdotool windowfocus "$window"
source /repo/tools/gui_step_input.sh
shot_after() {
  local s=$(gui_step)
  wait_step $((s+4000000))
  move_to 64 64
  wait_step $(( $(gui_step)+1200000 ))
  s=$(gui_step)
  import -window "$window" "$out.$1.png"
  echo "$1 $s" >>"$out.shots"
}
wait_step 3000000
enter_once
wait_step 12000000
click 640 400
move_to 64 64
wait_step 30000000
click 512 536
shot_after load-slots
click 620 360
shot_after loaded-notice
enter_once
shot_after loaded-world
python3 /repo/tools/gui_close_window.py --window "$window"
wait "$game_pid"

 ;;
 replays)
if [[ ! -f /game/OPENING.EXE || ! -f "$seed" ]]; then
  echo 'SKIP：缺合法原版或原版正常存檔入口；不宣稱百科驗證完成'
  exit 77
fi
[[ -x "$bin" && -f "$out/gui-colony.inputs.json" && -f "$out/gui-colony.shots" ]]
[[ $(stat -c %u "$out") == $(id -u) ]]
[[ $(sha256sum "$seed" | cut -d' ' -f1) == f683eb9132406e1dc7de5c90372f933b724b71b78a327551a305ba19d9a7d991 ]]
steps=$(awk '{print $2}' "$out/gui-colony.shots" | sort -un | paste -sd,)
end=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["end"])' "$out/gui-colony.inputs.json")
flags=(--window --all-menu --root /game --catalog /repo/text/draft.zh-Hant.tsv
  --font-dir "$r/goal096-fonts-verified" --sea-status-a --sea-atlas "$r/goal143-sea/atlas/sea-atlas.json"
  --dialog-a --string-a --string-atlas "${COLONIZATION_STRING_ATLAS:?須指定現行圖集}"
  --string-templates "${COLONIZATION_STRING_TEMPLATES:-/repo/text/string-templates.zh-Hant.tsv}"
  --replay-inputs "$out/gui-colony.inputs.json" --window-steps "$end" --checkpoint-steps "$steps")
pids=()
trap 'for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; for p in "${pids[@]}"; do wait "$p" 2>/dev/null || true; done' EXIT
run() {
  local tag=$1; shift
  [[ ! -e "$out/$tag.json" && ! -e "$out/$tag-save" ]]
  mkdir "$out/$tag-save"
  cp "$seed" "$out/$tag-save/COLONY02.SAV"
  "$bin" "${flags[@]}" --scratch "$out/$tag-save" "$@" --out "$out/$tag" >"$out/$tag.log" 2>&1
}
run replay-zh --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:?須指定現行圖集}" & pids+=($!)
run replay-control --dialog-atlas "${COLONIZATION_DIALOG_ATLAS:?須指定現行圖集}" --control & pids+=($!)
run neg-noatlas --dialog-atlas "$out/missing-dialog-atlas.json" & pids+=($!)
failed=0
for p in "${pids[@]}"; do wait "$p" || failed=1; done
((failed==0))
trap - EXIT

 ;;
 *) echo "模式須為gui或replays"; exit 2 ;;
esac
