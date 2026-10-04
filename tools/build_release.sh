#!/usr/bin/env bash
# 固定容器內建置正式版；來源由build_window_prototype.py先組裝。
set -euo pipefail
version=${1:?版本}
platform=${2:?linux/windows/macos}
[[ $version =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
batch=${COLONIZATION_RELEASE_WORK:-/repo/workplace/reports/goal183-release}
source_dir=/source
[[ -d "$source_dir" && $(stat -c %u:%g "$batch") == "$(id -u):$(id -g)" ]]
mkdir -p "$batch/binaries"
export GOCACHE=/cache GOPROXY=off GOTOOLCHAIN=local
export COLONIZATION_RELEASE_VERSION=$version COLONIZATION_GOAL182_SOURCE=$source_dir COLONIZATION_GOAL182_OUT=$batch/binaries
case "$platform" in
  linux)
    [[ ! -e "$batch/binaries/colonization-window" ]]
    cd "$source_dir"
    go build -mod=readonly -trimpath -ldflags="-X main.frontendReleaseVersion=$version" -o "$batch/binaries/colonization-window" .
    go version -m "$batch/binaries/colonization-window" >"$batch/binaries/linux-build-info.txt"
    ;;
  windows) bash /repo/tools/build_goal182_platforms.sh windows-amd64 ;;
  macos) bash /repo/tools/build_goal182_platforms.sh macos-universal ;;
  *) exit 2 ;;
esac
