#!/usr/bin/env bash
# 只在有界 Docker 中：其餘五類百科的正常 GUI 逐篇路徑。
set -euo pipefail
category=${1:?請指定 unit、terrain、job、building 或 father}
case "$category" in
  unit) count=23; menu_y=94; steps=900000000 ;;
  terrain) count=21; menu_y=126; steps=800000000 ;;
  job) count=27; menu_y=190; steps=1100000000 ;;
  building) count=38; menu_y=222; steps=1600000000 ;;
  father) count=25; menu_y=254; steps=1000000000 ;;
  *) echo '不支援的百科類別' >&2; exit 2 ;;
esac
export COLONIZATION_PEDIA_CATEGORY=$category COLONIZATION_PEDIA_COUNT=$count
export COLONIZATION_PEDIA_MENU_Y=$menu_y COLONIZATION_PEDIA_STEPS=$steps
export COLONIZATION_GUI_CLOSE_AFTER_ROUTE=1
base=/repo/workplace/reports/goal180-pedia-rest
export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
export COLONIZATION_DIALOG_ATLAS=${COLONIZATION_DIALOG_ATLAS:-$base/formatted-dialog-atlas/dialog-atlas.json}
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
export COLONIZATION_STRING_TEMPLATES=${COLONIZATION_STRING_TEMPLATES:-$base/final-string-templates.tsv}
export COLONIZATION_GOAL179_OUT=${COLONIZATION_GOAL180_OUT:-/repo/workplace/reports/goal180-pedia-rest/$category}
# 容器內固定這次操作腳本，避免工作樹更新改變 Bash 開啟中的檔案位移。
script=$(mktemp /tmp/colonization-pedia-gui.XXXXXX)
cp /repo/tools/probe_goal179_gui.sh "$script"
trap 'rm -f "$script"' EXIT
bash "$script"
