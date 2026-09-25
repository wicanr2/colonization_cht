#!/bin/sh
# 僅在有界 Docker 容器內執行；原版 /game 唯讀，輸出留已忽略 workplace。
# 目標141：沿英格蘭正常玩家路徑，對 @BUILD1～10 字幕各做兩次冷啟動與無監看控制。
set -eu

repo=/repo
game=/game
# 用法：probe_goal141_captions.sh [輸出子目錄 輸入檔]；預設為十張字幕全顯示的無跳過輸入。
out=$repo/workplace/reports/goal141-captions/${1:-full}
inputs=${2:-$repo/tools/goal141-captions.inputs.json}
test -d "$repo/workplace/dosgolem" && test -f "$game/OPENING.EXE" && test -f "$inputs"
test "$(stat -c %u "$out")" = "$(id -u)"
export GOCACHE=$repo/workplace/gocache
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal141-probe "$repo/tools/probe_goal141_captions.go"
pids=""
for run in a b control; do
    test ! -e "$out/$run.json"
    flag=""
    [ "$run" = control ] && flag="-control"
    /tmp/goal141-probe -root "$game" -inputs "$inputs" $flag -out "$out/$run" > "$out/$run.log" 2>&1 &
    pids="$pids $!"
done
for p in $pids; do wait "$p"; done
echo '目標141字幕探針完成'
