#!/bin/sh
# 僅在有界、無網路、非 root Docker 內執行；/game 必須為唯讀原版掛載。
set -eu

repo=/repo
reports=$repo/workplace/reports/goal125-help
spec=${1:?請指定 none-a／once-a／twice-a 或各自 -b／-control}

case "$spec" in
    none-*) fixture=goal125-untouched-retire.inputs.json; end=1650000000 ;;
    once-*) fixture=goal125-toggle-once-retire.inputs.json; end=1650000000 ;;
    twice-*) fixture=goal125-toggle-twice-retire.inputs.json; end=1675000000 ;;
    *) echo '未知分支' >&2; exit 2 ;;
esac
case "$spec" in
    *-a|*-b) control= ;;
    *-control) control=-control ;;
    *) echo '未知重播組別' >&2; exit 2 ;;
esac

test -d /game
test -d "$reports"
test "$(stat -c %u "$reports")" = "$(id -u)"
test -f "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json"
test -f "$repo/tools/$fixture"
test -f "$repo/workplace/dosgolem/go.mod"
test ! -e "$reports/$spec.json"

scratch=$reports/$spec-scratch
mkdir "$scratch"
test "$(stat -c %u "$scratch")" = "$(id -u)"
export GOCACHE=/tmp/colonization-go-build-cache
export GOMAXPROCS=2
cd "$repo/workplace/dosgolem"
if [ ! -x "$reports/goal125-probe" ]; then
    /usr/local/go/bin/go build -p 1 -o "$reports/goal125-probe" \
        "$repo/tools/probe_goal098_intro.go"
fi

"$reports/goal125-probe" -root /game -scratch "$scratch" \
    -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
    -out "$reports/$spec" -nation england -next-enter -after-b enter \
    -after-follow enter -follow-until "$end" -post-caption-audit \
    -game-inputs "$repo/tools/$fixture" -allow-early-exit $control

echo "原版實驗完成：$spec；暫存層只在 $scratch"
