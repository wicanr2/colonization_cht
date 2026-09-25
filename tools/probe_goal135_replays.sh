#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：規格025英格蘭介紹兩頁，以真玩家錄製輸入前綴做中英同輸入重播與載入期負例。
# 用法：probe_goal135_replays.sh <名稱> <終點步數> [zh|control|neg-missing|neg-no-masks]
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL135_OUT:-$r/goal135-nation-intro}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
masks=$out/masks
full=$r/goal124-keyboard/live-route-b.inputs.json
name=$1 end=$2 mode=${3:-zh}
[[ -x "$bin" && -d "$masks" && -f "$full" && -f /game/OPENING.EXE ]]
[[ "$(sha256sum "$full" | cut -d' ' -f1)" == dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98 ]]
[[ ! -e "$out/$name.json" ]]
prefix=$out/prefix-$end.inputs.json
python3 - "$full" "$end" "$prefix" <<'PY'
import json, sys
src, end, target = sys.argv[1], int(sys.argv[2]), sys.argv[3]
data = json.load(open(src))
payload = {"inputs": [e for e in data["inputs"] if e["step"] <= end], "end": end}
text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
try:
    old = open(target).read()
except FileNotFoundError:
    old = None
if old is not None and old != text:
    raise SystemExit(f"既有前綴內容不同：{target}")
open(target, "w").write(text)
PY
args=(--window --root /game --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
      --england-intro-a --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$masks"
      --replay-inputs "$prefix" --window-steps "$end" --out "$out/$name")
case $mode in
  zh) ;;
  control) args+=(--control) ;;
  neg-missing) args+=(--missing) ;;
  neg-no-masks) mkdir -p "$out/empty-masks"; args=("${args[@]/$masks/$out/empty-masks}") ;;
  *) echo "未知模式 $mode" >&2; exit 2 ;;
esac
"$bin" "${args[@]}" > "$out/$name.log" 2>&1
echo "目標135重播完成：$name"
