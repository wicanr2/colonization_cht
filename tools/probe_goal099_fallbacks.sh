#!/usr/bin/env bash
# 目標099：同一原版冷啟動正常滑鼠前綴的第一張旗卡逐欄回退。
# 由外層容器啟動、等待並回收 Xvfb；本腳本只執行指定案例。
set -euo pipefail

out=${COLONIZATION_GOAL099_OUT:-/repo/workplace/reports/goal099-card-fonts}
bin=${COLONIZATION_WINDOW_BIN:-/repo/workplace/reports/goal099-window-src/window-bin}
fonts=${COLONIZATION_FONT_DIR:-/repo/workplace/reports/goal096-fonts-verified}
card_fonts=${COLONIZATION_CARD_FONT_DIR:-$out}
catalog=/repo/text/nation-card-fragments.zh-Hant.tsv
[[ -x "$bin" && -d "$out" && -d "$fonts" && -d "$card_fonts" && -d /game ]]

for name in "$@"; do
  case "$name" in
    missing-upper) card_catalog=$out/missing-upper.tsv; card_font_dir=$card_fonts; inputs=$out/card43.inputs.json; end=43000000 ;;
    missing-upper-font)
      card_catalog=$catalog; card_font_dir=$out/missing-upper-font
      inputs=$out/card43.inputs.json; end=43000000
      if [[ ! -e "$card_font_dir" ]]; then
        mkdir "$card_font_dir"
        cp "$card_fonts/LABELS.TXT-0x000008F2.json" "$card_font_dir/"
      fi
      [[ -f "$card_font_dir/LABELS.TXT-0x000008F2.json" &&
         ! -e "$card_font_dir/NAMES.TXT-0x000008EA.json" ]] ;;
    duplicate-lower) card_catalog=$out/duplicate-lower.tsv; card_font_dir=$card_fonts; inputs=$out/card43.inputs.json; end=43000000 ;;
    wrong-size-lower) card_catalog=$catalog; card_font_dir=$out/wrong-size-lower; inputs=$out/card43.inputs.json; end=43000000 ;;
    hover-upper|hover-lower|hover-clear|press-lower|switch-right|leave-page)
      card_catalog=$catalog; card_font_dir=$card_fonts; inputs=$out/$name.inputs.json
      case "$name" in
        hover-upper|hover-lower) end=43500000 ;;
        hover-clear|press-lower) end=44000000 ;;
        switch-right) end=46000000 ;;
        leave-page) end=49000000 ;;
      esac ;;
    *) echo "未知旗卡案例：$name" >&2; exit 2 ;;
  esac
  [[ -f "$card_catalog" && -d "$card_font_dir" && -f "$inputs" && ! -e "$out/$name.json" ]]
  "$bin" --window --all-menu --nation-card-a --root /game \
    --catalog /repo/text/draft.zh-Hant.tsv --font-dir "$fonts" \
    --nation-card-catalog "$card_catalog" --nation-card-font-dir "$card_font_dir" \
    --out "$out/$name" --replay-inputs "$inputs" --window-steps "$end"
done
