# 目標153：第一個中文垂直切片收尾（Issue #26）

狀態：進行中；開始：2026-09-26。對應 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 範圍

Issue #26 的驗收條件大多已由既有收據涵蓋（見[驗證矩陣](../verification-matrix.md)）。本輪補齊：

- 靜態覆蓋的圖檔版本不符：原因獨立記為 `image-version-mismatch`，以暫存副本改動 `OPENCRD1.SS` 一個位元組實測 fail-closed。
- 以目前前端重驗核心原版檔（`OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、`LABELS.TXT`、`NAMES.TXT`）任一不符即拒絕啟動。
- 逐條對照 Issue #26 驗收條件與收據。

## 退出條件

- 兩類版本不符都 fail-closed，原版輸入唯讀。
- 靜態重播與全面回歸不變。
