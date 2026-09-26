# 目標152：中文化驗證矩陣與正常玩家路徑收據（Issue #14）

狀態：進行中；開始：2026-09-26。對應 [Issue #14](https://github.com/wicanr2/colonization_cht/issues/14)。

## 範圍

- 矩陣定義 `tools/verification-matrix.json`：每列是一組正式覆蓋（動態或靜態），列出規格、旗標、檢查器、收據目錄、重產腳本與已知差異。
- 執行器 `tools/verification_matrix.py`：逐列跑獨立檢查器，盤點原版基線（英文控制的原始 VGA 索引、色盤與 RAM）、中文、英文與負例收據，記錄輸入雜湊、dosgolem 版本、前端來源雜湊與畫面格式。
- 輸出可提交的 `docs/verification-matrix.md`（只含雜湊、數量與鍵）；未驗範圍逐項列出。

## 退出條件

- 動態與靜態都有原版基線、中文、英文與負例收據，檢查器 PASS。
- 同一環境重跑兩次產生相同報告。
- 報告只宣稱實際抽樣範圍。
