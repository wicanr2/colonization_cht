#!/bin/sh
# 僅供 Docker 內執行：固定原版的四列同焦點玩家輸入收據。
set -eu

repo=/repo
game=/game
reports=$repo/workplace/reports/goal118-options
test -d "$game"
test -d "$reports"
test "$(stat -c %u "$reports")" = "$(id -u)"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test -f "$repo/tools/probe_goal098_intro.go"

export GOCACHE=/tmp/colonization-go-build-cache
export GOMAXPROCS=2
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal118-probe "$repo/tools/probe_goal098_intro.go"

for spec in second-a second-b second-control third-a third-b third-control fifth-a fifth-b fifth-control sixth-a sixth-b sixth-control; do
    case "$spec" in
        second-*) fixture=goal118-second-then-first.inputs.json ;;
        third-*) fixture=goal118-third-then-first.inputs.json ;;
        fifth-*) fixture=goal118-fifth-then-first.inputs.json ;;
        sixth-*) fixture=goal118-sixth-then-first.inputs.json ;;
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
    /tmp/goal118-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$reports/$spec" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until 1400000000 -post-caption-audit \
        -game-inputs "$repo/tools/$fixture" -options-audit "$@"
done
