#!/bin/sh
# 僅在有界 Docker 容器內執行；原版 /game 唯讀，輸出留已忽略 workplace。
# 目標140：以目標136真 GUI 錄下的選國輸入，對法國／西班牙／荷蘭各做兩次冷啟動與無監看控制。
set -eu

repo=/repo
game=/game
out=$repo/workplace/reports/goal140-nation-cards/probe
test -d "$repo/workplace/dosgolem" && test -f "$game/OPENING.EXE"
test "$(stat -c %u "$out")" = "$(id -u)"
export GOCACHE=$repo/workplace/gocache
cd "$repo/workplace/dosgolem"
/usr/local/go/bin/go build -p 1 -o /tmp/goal140-probe "$repo/tools/probe_goal140_nation_cards.go"
pids=""
for nation in france spain netherlands; do
    inputs=$repo/workplace/reports/goal136-nation-intro/gui-$nation.inputs.json
    test -f "$inputs"
    for run in a b control; do
        test ! -e "$out/$nation-$run.json"
        flag=""
        [ "$run" = control ] && flag="-control"
        /tmp/goal140-probe -root "$game" -inputs "$inputs" -nation "$nation" $flag \
            -out "$out/$nation-$run" > "$out/$nation-$run.log" 2>&1 &
        pids="$pids $!"
    done
done
for p in $pids; do wait "$p"; done
echo '目標140旗卡探針完成'
