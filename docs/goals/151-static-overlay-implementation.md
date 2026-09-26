# 目標151：靜態文字覆蓋正式實作與驗證（Issue #13）

狀態：進行中；開始：2026-09-26。對應 [Issue #13](https://github.com/wicanr2/colonization_cht/issues/13)，依[規格034](../spec/034-static-text-overlay-draft.md)。

## 範圍

- 開場製作名單七個職稱橫幅（`OPENCRD1.SS`），譯稿 `text/static-overlay.zh-Hant.tsv`。
- 前端旗標 `--static-credits-a`：指紋矩形索引位元組 SHA-256 完全相符才清文字帶並畫中文；不符一律原樣。
- 字級依規則：欄位 22px 起，放不下縮到 15px（2/3 下限），仍放不下回原文。

## 退出條件

- 真 GUI（玩家不按鍵看完開場）七個職稱橫幅都套用，人名橫幅與無橫幅畫面不變。
- 中英同輸入重播：原版記憶體狀態相同；中文差異只在文字帶。
- 負例：缺字模、指紋竄改、重複鍵時 fail-closed。
- 全面回歸六點與目標138收據相同。
