#!/usr/bin/env bash
# 殖民帝國繁體中文化（Colonization CHT）技術預覽啟動器。
# 用法：./colonization-cht.sh --game /path/to/COLONIZE [其他前端參數]
# 需要自備合法取得、指紋相符的 DOS 版原版目錄；本包不含任何原版檔案。
# 原版目錄只讀；存檔寫到 $COLONIZATION_CHT_SAVE（預設 ~/.local/share/colonization-cht/save）。
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
game=""
args=()
while (($#)); do
  case "$1" in
    --game) game=${2:-}; shift 2 ;;
    --game=*) game=${1#--game=}; shift ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done
if [[ -z "$game" || ! -f "$game/VICEROY.EXE" ]]; then
  echo "請用 --game 指定含 VICEROY.EXE 的原版 COLONIZE 目錄" >&2
  exit 2
fi
save=${COLONIZATION_CHT_SAVE:-${XDG_DATA_HOME:-$HOME/.local/share}/colonization-cht/save}
mkdir -p "$save"
m=$here/masks
t=$here/text
exec "$here/bin/colonization-window" --window --play --root "$game" --scratch "$save" \
  --catalog "$t/draft.zh-Hant.tsv" --font-dir "$m/menu" --all-menu \
  --nation-card-a --nation-card-catalog "$t/nation-card-fragments.zh-Hant.tsv" --nation-card-font-dir "$m/card" \
  --nation-cards-rest-a --nation-cards-rest-font-dir "$m/cards-rest" \
  --third-card-a --third-card-font-dir "$m/third-card" \
  --nation-intro-a --intro-catalog "$t/nation-introduction.zh-Hant.tsv" --intro-mask-dir "$m/intro" \
  --build1-a --build1-font "$m/build1.json" \
  --build-captions-a --build-values "$t/build-caption-values.zh-Hant.tsv" --build-caption-font-dir "$m/captions" \
  --tutorial-help-a --help-catalog "$t/help-bilingual.tsv" --help-mask-dir "$m/help" \
  --sea-status-a --sea-catalog "$t/sea-status.zh-Hant.tsv" --sea-atlas "$m/sea-atlas.json" \
  --game-options-title-a --game-options-title-font "$m/options-title.json" \
  --game-options-rows-a --game-options-rows-font-dir "$m/option-rows" \
  --retire-a --retire-font-dir "$m/retire" \
  --static-credits-a --static-catalog "$t/static-overlay.zh-Hant.tsv" --static-mask-dir "$m/static" \
  --out "$save/../last-run" "${args[@]}"
