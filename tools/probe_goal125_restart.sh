#!/bin/sh
# 僅在有界 Docker 內執行；複製首輪 Scratch，保留退出後原始檔案收據。
set -eu

repo=/repo
reports=$repo/workplace/reports/goal125-help
origin=${1:?請指定 none-a／once-a／twice-a 或各自 -b／-control}
case "$origin" in
    none-a|none-b|none-control|once-a|once-b|once-control|twice-a|twice-b|twice-control) ;;
    *) echo '未知首輪收據' >&2; exit 2 ;;
esac
case "$origin" in
    *-control) control=-control ;;
    *) control= ;;
esac

test -d /game
test -d "$reports"
test "$(stat -c %u "$reports")" = "$(id -u)"
test -x "$reports/goal125-probe"
source=$reports/$origin-scratch
test -f "$source/COLONY09.SAV"
test -f "$source/HALLFAME.DAT"
out=$reports/restart-$origin
test ! -e "$out.json"
scratch=$reports/restart-$origin-scratch
mkdir "$scratch"
test "$(stat -c %u "$scratch")" = "$(id -u)"
cp "$source/COLONY09.SAV" "$source/HALLFAME.DAT" "$scratch/"
test "$(sha256sum "$source/COLONY09.SAV" | cut -d ' ' -f 1)" = \
     "$(sha256sum "$scratch/COLONY09.SAV" | cut -d ' ' -f 1)"
test "$(sha256sum "$source/HALLFAME.DAT" | cut -d ' ' -f 1)" = \
     "$(sha256sum "$scratch/HALLFAME.DAT" | cut -d ' ' -f 1)"

"$reports/goal125-probe" -root /game -scratch "$scratch" \
    -inputs "$repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json" \
    -out "$out" -nation england -next-enter -after-b enter \
    -after-follow enter -follow-until 1400000000 -post-caption-audit \
    -game-inputs "$repo/tools/goal111-first-row-only.inputs.json" $control

echo "跨次冷啟動完成：$origin；原始暫存收據未覆寫"
