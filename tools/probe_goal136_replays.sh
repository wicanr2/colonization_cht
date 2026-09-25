#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：以真 GUI 錄下的該國現場輸入做介紹兩頁中英同輸入重播。
# 用法：probe_goal136_replays.sh <france|spain|netherlands>
# 56M／64M 取現場輸入前綴；離頁 75M 另在現場輸入後補一筆 68M Enter（B 頁顯示後），屬明示補充輸入。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL136_OUT:-$r/goal136-nation-intro}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
nation=$1
gui=$out/gui-$nation.inputs.json
[[ -x "$bin" && -d "$out/masks" && -f "$gui" && -f /game/OPENING.EXE ]]
python3 - "$gui" "$out" "$nation" <<'PY'
import json, sys
gui, out, nation = sys.argv[1:]
data = json.load(open(gui))
for end in (56000000, 64000000):
    payload = {"inputs": [e for e in data["inputs"] if e["step"] <= end], "end": end}
    json.dump(payload, open(f"{out}/{nation}-prefix-{end}.inputs.json", "w"), indent=2, sort_keys=True)
extended = [e for e in data["inputs"] if e["step"] <= 64000000]
extended.append({"step": 68000000, "kind": "enter", "x": 0, "y": 0, "button": 0})
json.dump({"inputs": extended, "end": 75000000}, open(f"{out}/{nation}-exit-75000000.inputs.json", "w"),
          indent=2, sort_keys=True)
PY
common=(--window --root /game --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$r/goal096-fonts-verified"
        --nation-intro-a --intro-catalog /repo/text/nation-introduction.zh-Hant.tsv --intro-mask-dir "$out/masks")
run() {
  local name=$1 inputs=$2 end=$3; shift 3
  [[ ! -e "$out/$name.json" ]]
  "$bin" "${common[@]}" --replay-inputs "$inputs" --window-steps "$end" --out "$out/$name" "$@" > "$out/$name.log" 2>&1
}
for end in 56000000 64000000; do
  run "$nation-zh-$((end / 1000000))m" "$out/$nation-prefix-$end.inputs.json" "$end" &
  run "$nation-control-$((end / 1000000))m" "$out/$nation-prefix-$end.inputs.json" "$end" --control &
done
run "$nation-zh-75m" "$out/$nation-exit-75000000.inputs.json" 75000000 &
run "$nation-control-75m" "$out/$nation-exit-75000000.inputs.json" 75000000 --control &
wait
echo "目標136重播完成：$nation"
