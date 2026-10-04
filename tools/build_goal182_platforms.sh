#!/usr/bin/env bash
# Docker內：跨平台建置中間物，不產生正式發行包。
set -euo pipefail
source_dir=${COLONIZATION_GOAL182_SOURCE:-/repo/workplace/reports/goal181-colony-rest/20261004-woodcut-titles/formal-modal2/stable-build}
out=${COLONIZATION_GOAL182_OUT:-/repo/workplace/reports/goal182-platform-preflight}
platform=${1:?請指定windows-amd64或macos-universal}
[[ -d "$source_dir" && -d "$out" && $(stat -c %u "$out") == $(id -u) && $(stat -c %g "$out") == $(id -g) ]]
case "$platform" in
  windows-amd64)
    [[ ! -e "$out/colonization-window.exe" ]]
    export GOOS=windows GOARCH=amd64 CGO_ENABLED=0
    binary=$out/colonization-window.exe
    info=$out/windows-build-info.txt
    sums=$out/windows-build.sha256
    ;;
  macos-universal)
    [[ -x /osxcross/bin/o64-clang && -x /osxcross/bin/oa64-clang && -x /osxcross/bin/lipo ]]
    [[ ! -e "$out/colonization-window-macos-amd64" && ! -e "$out/colonization-window-macos-arm64" && ! -e "$out/colonization-window-macos-universal" ]]
    export GOOS=darwin CGO_ENABLED=1
    ;;
  *) echo "尚未核准此建置入口：$platform" >&2; exit 2 ;;
esac
export GOPROXY=off GOTOOLCHAIN=local GOPATH=/go GOMODCACHE=/go/pkg/mod GOFLAGS=
export PATH=/usr/local/go/bin:$PATH
version_flags=
if [[ -n ${COLONIZATION_RELEASE_VERSION:-} ]]; then
  [[ $COLONIZATION_RELEASE_VERSION =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
  version_flags="-X main.frontendReleaseVersion=$COLONIZATION_RELEASE_VERSION"
fi
[[ $(go env GOVERSION) == go1.26.7 ]]
cd "$source_dir"
if [[ "$platform" == macos-universal ]]; then
  for arch in amd64 arm64; do
    export GOARCH=$arch
    if [[ "$arch" == amd64 ]]; then
      export CC=/osxcross/bin/o64-clang CXX=/osxcross/bin/o64-clang++
    else
      export CC=/osxcross/bin/oa64-clang CXX=/osxcross/bin/oa64-clang++
    fi
    binary=$out/colonization-window-macos-$arch
    # Intel 合併 DWARF 後不重簽，規格043只封裝不附除錯資料的臨時簽章產物。
    go build -mod=readonly -trimpath -ldflags="-w -extldflags=-Wl,-adhoc_codesign $version_flags" -o "$binary" .
    go version -m "$binary" > "$out/macos-$arch-build-info.txt"
  done
  /osxcross/bin/lipo -create "$out/colonization-window-macos-amd64" "$out/colonization-window-macos-arm64" -output "$out/colonization-window-macos-universal"
  /osxcross/bin/lipo -info "$out/colonization-window-macos-universal" > "$out/macos-universal-architectures.txt"
  sha256sum "$out/colonization-window-macos-"{amd64,arm64,universal} > "$out/macos-build.sha256"
else
  go build -mod=readonly -trimpath -ldflags="$version_flags" -o "$binary" .
  go version -m "$binary" > "$info"
  sha256sum "$binary" > "$sums"
fi
