#!/usr/bin/env bash
# 固定Go1.26.7與AppImage工具容器內執行，產生兩份可重現暫存封包。
set -euo pipefail
version=${1:?版本}
batch=${COLONIZATION_RELEASE_WORK:-/repo/workplace/reports/goal183-release}
[[ $(go env GOVERSION) == go1.26.7 && -x "$batch/inspect-version" ]]
for side in a b; do
  for format in appimage windows-zip macos-zip; do
    case "$format" in
      appimage) binary=colonization-window; readme=README.txt ;;
      windows-zip) binary=colonization-window.exe; readme=README.windows.txt ;;
      macos-zip) binary=colonization-window-macos-universal; readme=README.macos.txt ;;
    esac
    python3 /repo/tools/package_release.py --version "$version" --format "$format" \
      --binary "$batch/binaries/$binary" --version-inspector "$batch/inspect-version" \
      --readme "/repo/tools/release/$readme" --output "$batch/packages-$side/$format" \
      >"$batch/package-$side-$format.json"
  done
done
