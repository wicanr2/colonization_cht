#!/usr/bin/env bash
# 只在有界 Docker/Xvfb 內：目標153 版本不符 fail-closed。
# 1) 五個核心原版檔各改暫存副本一個位元組，前端必須拒絕啟動；2) 只改 OPENCRD1.SS，靜態覆蓋必須回原文並記 image-version-mismatch。
# 圖檔守門在載入時判定；改過的圖檔會讓原版開場解碼跑進無效指令，所以只跑到 2M 步。
# 原版輸入唯讀；暫存副本以符號連結組成，只有被改的那一個檔是複本。
set -euo pipefail

r=/repo/workplace/reports
out=${COLONIZATION_GOAL153_OUT:-$r/goal153-slice}
bin=${COLONIZATION_WINDOW_BIN:-$out/window-src/colonization-window}
masks=$r/goal151-static/masks
prefix=$r/goal151-static/neg/prefix-470000000.inputs.json
[[ -x "$bin" && -d "$masks" && -f "$prefix" && -f /game/OPENING.EXE && -f /game/OPENCRD1.SS ]]
rm -rf "$out/wrong-image" "$out"/wrong-image-run.* "$out"/version-*.json
for name in OPENING.EXE VICEROY.EXE GAME.TXT LABELS.TXT NAMES.TXT; do
  python3 /repo/tools/check_goal082_wrong_version.py --game /game --binary "$bin" --target "$name" \
    --output "$out/version-$name.json" > /dev/null
done
mkdir "$out/wrong-image"
for f in /game/*; do ln -s "$f" "$out/wrong-image/$(basename "$f")"; done
rm "$out/wrong-image/OPENCRD1.SS"
python3 - "$out/wrong-image/OPENCRD1.SS" <<'PY'
import sys
data = bytearray(open("/game/OPENCRD1.SS", "rb").read())
data[-1] ^= 1  # 只改最後一個位元組，不破壞影格表
open(sys.argv[1], "wb").write(data)
PY
python3 - "$prefix" "$out/prefix-2000000.inputs.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
json.dump({"inputs": [e for e in d["inputs"] if e["step"] <= 2000000], "end": 2000000}, open(sys.argv[2], "w"), indent=2, sort_keys=True)
PY
"$bin" --window --all-menu --nation-card-a --root "$out/wrong-image" --catalog /repo/text/draft.zh-Hant.tsv \
  --font-dir "$r/goal096-fonts-verified" --nation-card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --nation-card-font-dir "$r/goal099-card-fonts" --static-credits-a --static-mask-dir "$masks" \
  --replay-inputs "$out/prefix-2000000.inputs.json" --window-steps 2000000 --checkpoint-steps 1000000 \
  --out "$out/wrong-image-run" > "$out/wrong-image-run.log" 2>&1
echo '目標153版本不符探測完成'
