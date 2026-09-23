#!/usr/bin/env bash
# 僅供 Docker 內一次性真視窗驗收；自行回收 Xvfb，不留下背景容器。
set -euo pipefail
export DISPLAY=:97
Xvfb :97 -screen 0 1280x800x24 -nolisten tcp > /tmp/colonization-goal079-xvfb.log 2>&1 &
xvfb_pid=$!
trap 'kill "$xvfb_pid" 2>/dev/null || true; wait "$xvfb_pid" 2>/dev/null || true' EXIT
for ((i=0;i<50;i++)); do
  if xdotool getmouselocation >/dev/null 2>&1; then
    if (($#)); then
      "$@"
    else
      bash /repo/tools/probe_window_prototype.sh
    fi
    exit $?
  fi
  sleep .1
done
echo 'Xvfb 無法啟動' >&2
sed -n '1,30p' /tmp/colonization-goal079-xvfb.log >&2
exit 1
