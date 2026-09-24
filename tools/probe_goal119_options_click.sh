#!/bin/sh
# 僅供 Docker 內執行：選項第一／末列真實點擊的細相位原版收據。
set -eu

repo=/repo
game=/game
reports=$repo/workplace/reports/goal119-options
test -d "$game"
test -d "$reports"
test "$(stat -c %u "$reports")" = "$(id -u)"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test -f "$repo/tools/probe_goal098_intro.go"

export GOCACHE=/tmp/colonization-go-build-cache
export GOMAXPROCS=2
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal119-probe "$repo/tools/probe_goal098_intro.go"

phases=1302000001,1302001000,1302100000,1302500000,1303000001,1303001000,1303100000,1303500000,1304000000,1305000000,1310000000,1320000000
for spec in first-a first-b first-control eighth-a eighth-b eighth-control; do
    case "$spec" in
        first-*) fixture=goal119-first-row-click.inputs.json ;;
        eighth-*) fixture=goal110-toggle-tutorial.inputs.json ;;
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
    /tmp/goal119-probe -root "$game" \
        -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
        -out "$reports/$spec" -nation england -next-enter -after-b enter \
        -after-follow enter -follow-until 1350000000 -post-caption-audit \
        -game-inputs "$repo/tools/$fixture" -options-audit \
        -options-phase-samples "$phases" "$@"
done
