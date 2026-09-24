#!/bin/sh
# 僅供 Docker 內執行：固定原版、正常玩家滑鼠事件的選項視窗相位收據。
set -eu

repo=/repo
game=/game
reports=$repo/workplace/reports/goal116-options
test -d "$game"
test -d "$reports"
test "$(stat -c %u "$reports")" = "$(id -u)"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test -f "$repo/tools/probe_goal098_intro.go"

export GOCACHE=/tmp/colonization-go-build-cache
export GOMAXPROCS=2
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal116-probe "$repo/tools/probe_goal098_intro.go"

for spec in hover-last-a hover-last-b hover-last-control hover-first-a hover-first-b hover-first-control exit-a exit-b exit-control; do
    case "$spec" in
        hover-last-*) fixture=goal116-hover-last.inputs.json ;;
        hover-first-*) fixture=goal116-hover-first.inputs.json ;;
        exit-*) fixture=goal116-exit.inputs.json ;;
        *) exit 2 ;;
    esac
    test -f "$repo/tools/$fixture"
    if [ -e "$reports/$spec.json" ]; then
        printf '保留既有收據 %s\n' "$spec"
        continue
    fi
    if [ "${spec##*-}" = control ]; then
        set -- -control
    else
        set --
    fi
    printf '開始 %s\n' "$spec"
    /tmp/goal116-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$reports/$spec" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until 1400000000 -post-caption-audit \
        -game-inputs "$repo/tools/$fixture" -options-audit "$@"
done
