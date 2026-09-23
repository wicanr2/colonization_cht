#!/usr/bin/env bash
# 目標084：已驗真視窗輸入與受控反例，重播正式顯示與同輸入原版控制。
# Xvfb 由外層擁有並以 trap 清理；所有輸出只留本機 workplace。
set -euo pipefail

group=${1:?請指定 catalog 或 interaction}
out=${COLONIZATION_GOAL084_OUT:-/repo/workplace/reports/goal083-post-difficulty}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal084-window-src/window-bin}
font_dir=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal084-fonts}
prefix_name=${COLONIZATION_GOAL084_PREFIX:-goal084-replay}
window_input=${COLONIZATION_GOAL084_WINDOW_INPUT:-$out/goal084-window.inputs.json}
catalog=/repo/text/draft.zh-Hant.tsv
[[ -x "$bin" && -d "$out" && -d "$font_dir" && -d /game ]]

run_one() {
  local name=$1 inputs=$2 text=$3 limit=$4 mode=$5
  local prefix="$out/$prefix_name-$name"
  [[ -f "$inputs" && -f "$text" && ! -e "$prefix.json" ]]
  local flags=()
  if [[ "$mode" == control ]]; then flags+=(--control); fi
  "$bin" --window --all-menu --root /game \
    --catalog "$text" --font-dir "$font_dir" \
    --out "$prefix" --replay-inputs "$inputs" --window-steps "$limit" \
    "${flags[@]}" > "$prefix.log" 2>&1
  echo "$name PASS"
}

case "$group" in
  catalog)
    input="$window_input"
    run_one zh "$input" "$catalog" 100000000 normal
    run_one control "$input" "$catalog" 100000000 control
    for action in missing duplicate; do
      for field in select power; do
        run_one "$action-$field" "$input" "$out/goal084-catalog-$action-$field.tsv" 100000000 normal
      done
    done
    ;;
  interaction)
    for variant in hover-select hover-power button; do
      run_one "$variant" "$out/$variant.inputs.json" "$catalog" 68000000 normal
      run_one "$variant-control" "$out/$variant.inputs.json" "$catalog" 68000000 control
    done
    ;;
  regression)
    run_one first-card-regression "$out/goal084-first-card-40m.inputs.json" "$catalog" 40000000 normal
    run_one second-card-regression /repo/workplace/reports/goal082-second-card/goal082-window.inputs.json "$catalog" 100000000 normal
    ;;
  *)
    echo "未知驗證組：$group" >&2
    exit 2
    ;;
esac
