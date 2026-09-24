#!/bin/sh
# 僅在 Docker 內執行；原版唯讀、輸出僅限已忽略的 workplace/reports。
set -eu

repo=/repo
game=/game
reports=$repo/workplace/reports/goal117-options
test -d "$game"
test -d "$reports"
test "$(stat -c %u "$reports")" = "$(id -u)"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test -f "$repo/tools/probe_goal098_intro.go"

export GOCACHE=/tmp/colonization-go-build-cache
export GOMAXPROCS=2
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal117-probe "$repo/tools/probe_goal098_intro.go"

for spec in baseline-a baseline-b baseline-control fourth-a fourth-b fourth-control seventh-a seventh-b seventh-control; do
    case "$spec" in
        baseline-*) fixture=goal111-first-row-only.inputs.json ;;
        fourth-*) fixture=goal117-fourth-then-first.inputs.json ;;
        seventh-*) fixture=goal117-seventh-then-first.inputs.json ;;
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
    /tmp/goal117-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$reports/$spec" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until 1400000000 -post-caption-audit \
        -game-inputs "$repo/tools/$fixture" -options-audit "$@"
done
