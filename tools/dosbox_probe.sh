#!/bin/sh
# 僅在有界 Docker 容器內執行；/original 唯讀，/out 為本機研究收據。
set -eu
test -d /original
test -d /out
test "$(stat -c %u /out)" = "$(id -u)"
cp -R /original /tmp/colonization-game
export DISPLAY=:99 SDL_AUDIODRIVER=dummy
Xvfb :99 -screen 0 1024x768x24 > /out/goal053-xvfb.log 2>&1 &
xvfb_pid=$!
dosbox_pid=
cleanup() {
    test -z "$dosbox_pid" || kill "$dosbox_pid" 2>/dev/null || true
    kill "$xvfb_pid" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM
attempt=0
while test ! -S /tmp/.X11-unix/X99; do
    attempt=$((attempt+1))
    test "$attempt" -lt 30
    sleep 0.1
done
dosbox-x -conf /tools/dosbox_probe.conf -c 'mount c /tmp/colonization-game' -c 'c:' -c 'colonize' > /out/goal053-dosbox.log 2>&1 &
dosbox_pid=$!
wait "$dosbox_pid"
