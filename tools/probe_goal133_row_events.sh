#!/bin/sh
# 僅在有界 Docker 容器內執行；原版 /game 唯讀，輸出留已忽略 workplace。
# 目標133：開窗後依輸入檔操作（預設第8列懸停、第2列點擊；toggle-all 為逐列點擊），
# 記錄九欄讀字／改色／逐幀雜湊。用法：probe_goal133_row_events.sh [名稱 輸入檔 終點 另存畫布(0/1)]
set -eu

repo=/repo
game=/game
out=$repo/workplace/reports/goal133-options-rows
name=${1:-row}
inputs=${2:-$repo/tools/goal133-row-events.inputs.json}
until=${3:-1375000000}
dump=${4:-0}
test -d "$repo/workplace/dosgolem" && test -f "$game/OPENING.EXE"
test -f "$inputs"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test "$(stat -c %u "$out")" = "$(id -u)"
test ! -e "$out/$name-a.json" && test ! -e "$out/$name-b.json" && test ! -e "$out/$name-control.json"
extra=""
[ "$dump" = 1 ] && extra="-row-canvas-dump"

export GOCACHE=$repo/workplace/gocache
export GOMAXPROCS=1
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal133-probe "$repo/tools/probe_goal098_intro.go"

run() {
    /tmp/goal133-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$out/$name-$1" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until "$until" -post-caption-audit \
        -game-inputs "$inputs" \
        -row-event-from 1253000000 $extra > "$out/$name-$1.log" 2>&1
}
run a & pa=$!
run b & pb=$!
( set -- ; /tmp/goal133-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$out/$name-control" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until "$until" -post-caption-audit \
        -game-inputs "$inputs" \
        -row-event-from 1253000000 -control > "$out/$name-control.log" 2>&1 ) & pc=$!
wait $pa; wait $pb; wait $pc
echo '目標133九欄事件探針完成'
