#!/bin/sh
# 僅在有界 Docker 容器內執行；原版 /game 與隔離 dosgolem 均唯讀。
set -eu

repo=/repo
game=/game
out=$repo/workplace/reports/goal131-options-title
test -d "$repo/workplace/dosgolem"
test -d "$game"
test -f "$repo/tools/goal116-exit.inputs.json"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test -f "$repo/workplace/reports/goal113-options/preprint-a.1300m.canvas"
test -d "$repo/workplace/reports"
test "$(stat -c %u "$repo/workplace/reports")" = "$(id -u)"
mkdir -p "$out"
test "$(stat -c %u "$out")" = "$(id -u)"

export GOCACHE=/tmp/colonization-go-build-cache
export GOMAXPROCS=2
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal131-probe "$repo/tools/probe_goal098_intro.go"

for spec in a b control; do
    if [ "$spec" = control ]; then
        set -- -control
    else
        set --
    fi
    /tmp/goal131-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$out/$spec" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until 1400000000 -post-caption-audit \
        -game-inputs "$repo/tools/goal116-exit.inputs.json" -options-audit -options-preprint \
        -options-title-screen-audit "$repo/workplace/reports/goal113-options/preprint-a.1300m.canvas" "$@"
done
