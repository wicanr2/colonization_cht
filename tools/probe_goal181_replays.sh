#!/usr/bin/env bash
# Docker內：正常存檔建城／BUY的中英及缺對話框圖集收據。
set -euo pipefail
base=/repo/workplace/reports/goal180-pedia-rest
export COLONIZATION_GOAL179_OUT=${COLONIZATION_GOAL181_OUT:-/repo/workplace/reports/goal181-colony-rest/load-unit-v6}
export COLONIZATION_WINDOW_BIN=${COLONIZATION_WINDOW_BIN:-$base/sync-final-build/colonization-window}
export COLONIZATION_DIALOG_ATLAS=$base/formatted-dialog-atlas/dialog-atlas.json
export COLONIZATION_STRING_ATLAS=${COLONIZATION_STRING_ATLAS:-$base/final-string-atlas/string-atlas.json}
export COLONIZATION_STRING_TEMPLATES=${COLONIZATION_STRING_TEMPLATES:-$base/final-string-templates.tsv}
export COLONIZATION_GOAL179_SAVE=${COLONIZATION_GOAL181_SAVE:-/repo/workplace/reports/goal178-orders/codex-audit/load-route-v2/scratch/COLONY00.SAV}
if [[ ! -f /game/OPENING.EXE || ! -f "$COLONIZATION_GOAL179_SAVE" ]]; then
  echo 'SKIP：缺合法原版或已驗正常存檔，不宣稱重播通過'
  exit 77
fi
[[ -d "$COLONIZATION_GOAL179_OUT" && $(stat -c %u "$COLONIZATION_GOAL179_OUT") == $(id -u) && $(stat -c %g "$COLONIZATION_GOAL179_OUT") == $(id -g) ]]
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp >/tmp/colonization-colony-replay-xvfb.log 2>&1 &
xp=$!
script=$(mktemp /tmp/colonization-colony-replay.XXXXXX)
trap 'kill "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true; rm -f "$script"' EXIT
python3 - "$script" <<'PY'
from pathlib import Path
import sys
source=Path('/repo/tools/probe_goal179_replays.sh').read_text()
assert 'gui-pedia' in source
source=source.replace('gui-pedia','gui-colony')
import os, hashlib
seed=Path(os.environ['COLONIZATION_GOAL179_SAVE'])
if seed.name=='COLONY01.SAV':
    expected='c27b44665f1a229ca5257ac8f23b2f63dc025d5814aa5172742ffcd69939e647'
    assert hashlib.sha256(seed.read_bytes()).hexdigest()==expected
    old='cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e'
    assert source.count(old)==1
    source=source.replace(old,expected)
    assert source.count('cp "$seed" "$out/$tag-save/COLONY00.SAV"')==1
    source=source.replace('cp "$seed" "$out/$tag-save/COLONY00.SAV"','cp "$seed" "$out/$tag-save/COLONY01.SAV"')
else:
    assert seed.name=='COLONY00.SAV'
Path(sys.argv[1]).write_text(source)
PY
cp "$script" "$COLONIZATION_GOAL179_OUT/replay-source.sh"
bash "$script"
