#!/usr/bin/env bash
# 在有界 Docker/Xvfb 內依真 GUI 輸入重播；沿用貨物百科的三側守門。
set -euo pipefail
category=${1:?請指定百科類別}
case "$category" in unit|terrain|job|building|father) ;; *) exit 2 ;; esac
export COLONIZATION_GOAL179_OUT=${COLONIZATION_GOAL180_OUT:-/repo/workplace/reports/goal180-pedia-rest/$category}
base=/repo/workplace/reports/goal180-pedia-rest
export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
export COLONIZATION_DIALOG_ATLAS=${COLONIZATION_DIALOG_ATLAS:-$base/formatted-dialog-atlas/dialog-atlas.json}
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
export COLONIZATION_STRING_TEMPLATES=${COLONIZATION_STRING_TEMPLATES:-$base/final-string-templates.tsv}
script=$(mktemp /tmp/colonization-pedia-replays.XXXXXX)
cp /repo/tools/probe_goal179_replays.sh "$script"
xp=''
trap 'rm -f "$script"; [[ -z "$xp" ]] || kill "$xp" 2>/dev/null || true; [[ -z "$xp" ]] || wait "$xp" 2>/dev/null || true' EXIT
if [[ -z ${DISPLAY:-} ]]; then
  export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
  Xvfb :99 -screen 0 1280x800x24 -nolisten tcp >/tmp/colonization-pedia-replay-xvfb.log 2>&1 &
  xp=$!
fi
bash "$script"
