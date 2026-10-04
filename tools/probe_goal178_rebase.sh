#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標178 以新前端只重播舊目標路徑的中文重播（replay-zh），
# 供 tools/check_rebase_replay.py 與舊基準逐檢查點比對。用法：probe_goal178_rebase.sh <目標號> <舊基準目錄名> [輸出標籤 [二進位]]
# 輸出標籤預設 rebase，二進位預設目標178 的前端；以目標177 的前端另跑一份（標籤 base177）可分離出本目標造成的差異。
# 由舊目標的 probe_goalNNN_replays.sh 衍生：註解掉英文控制與反向對照，資產以符號連結取自舊基準目錄。
set -euo pipefail
g=$1
old=$2
tag=${3:-rebase}
r=/repo/workplace/reports
bin=${4:-$r/goal178-orders/window-src/colonization-window}
new=$r/goal178-orders/$tag-$g
src=/repo/tools/probe_goal${g}_replays.sh
[[ -f "$src" && -d "$r/$old" && ! -e "$new" ]]
mkdir "$new"
for f in "$r/$old"/*; do
  [[ "$f" != "$new" ]] || continue
  b=$(basename "$f")
  case "$b" in replay-*|neg-*.*|*.outer.log|*.replays*.log) continue ;; esac
  ln -s "$f" "$new/$b"
done
awk '/^run (replay-control|neg-)/ {skip=1} skip {print "# " $0; if ($0 !~ /\\$/) skip=0; next} /^run replay-zh / {sub(/[[:space:]]*&.*$/, "")} {print}' "$src" > "$new/derived.sh"
# 只保留一個中文重播，以前景執行讓 set -e 能取得失敗狀態；舊腳本的裸 wait
# 在背景重播失敗時仍可能回傳成功，不能作驗收依據。
export "COLONIZATION_GOAL${g}_OUT=$new"
# 圖集綁定當前譯稿與術語雜湊；舊目標的圖集已過期，一律改用最新烘製的圖集（同目標177 的做法）。
export COLONIZATION_DIALOG_ATLAS=${COLONIZATION_DIALOG_ATLAS:-$r/goal174-input/dialog-atlas/dialog-atlas.json}
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$r/goal174-input/atlas/string-atlas.json}
export COLONIZATION_WINDOW_BIN=$bin
bash "$new/derived.sh"
ls "$new" | grep -c '^replay-zh\.cp-[0-9]*\.png$' | sed "s/^/目標$g 重播檢查點數：/"
