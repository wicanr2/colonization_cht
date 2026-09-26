# 目標152：中文化驗證矩陣與正常玩家路徑收據（Issue #14）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #14](https://github.com/wicanr2/colonization_cht/issues/14)。

## 範圍

- 矩陣定義 `tools/verification-matrix.json`：每列是一組正式覆蓋（動態或靜態），列出規格、旗標、檢查器、收據目錄、重產腳本與已知差異。
- 執行器 `tools/verification_matrix.py`：逐列跑獨立檢查器，盤點原版基線（英文控制的原始 VGA 索引、色盤與 RAM）、中文、英文與負例收據，記錄輸入雜湊、dosgolem 版本、前端來源雜湊與畫面格式。
- 輸出可提交的 `docs/verification-matrix.md`（只含雜湊、數量與鍵）；未驗範圍逐項列出。

## 退出條件

- 動態與靜態都有原版基線、中文、英文與負例收據，檢查器 PASS。
- 同一環境重跑兩次產生相同報告。
- 報告只宣稱實際抽樣範圍。

## 結果

- [驗證矩陣](../verification-matrix.md)十四列（動態十二、靜態一、回歸一）檢查器全數 PASS；原版輸入六個檔案雜湊跨收據無衝突；dosgolem `9dd36726`。
- 動態與靜態各有原版基線、中文、英文與負例收據。
- 同一環境連跑兩次：JSON 報告 SHA-256 `e11496fa9ac3e7320c8af219726abc4c7c05c7df803650fbe0ecf3007253f926`、Markdown `d396936b18a4f766ba73461d2991fd10ca5be5e0c7ba8673c4b7aebac4a05d74`，兩次位元組相同。
- 原版缺失時十四列都 SKIP、整體回 77。
- 矩陣定義 `tools/verification-matrix.json` SHA-256 `fef698db34d70673e095a6c1eadfabade293a200c4426f4abc3458c578335fae`；回歸比對改由 `tools/check_regression.py` 提交進版控。

## 已知限制

- 矩陣重跑檢查器，不重跑模擬；各列收據由 `regenerate` 腳本重產，耗時數十分鐘到數小時。
- 「其他國家遊戲選項」列無專屬負例；資料模型列是探針收據，不含中文畫面。
- 未驗範圍見矩陣文末。
