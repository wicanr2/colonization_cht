# 目標153：第一個中文垂直切片收尾（Issue #26）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 範圍

Issue #26 的驗收條件大多已由既有收據涵蓋（見[驗證矩陣](../verification-matrix.md)）。本輪補齊：

- 靜態覆蓋的圖檔版本不符：原因獨立記為 `image-version-mismatch`，以暫存副本改動 `OPENCRD1.SS` 一個位元組實測 fail-closed。
- 以目前前端重驗核心原版檔（`OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、`LABELS.TXT`、`NAMES.TXT`）任一不符即拒絕啟動。
- 逐條對照 Issue #26 驗收條件與收據。

## 退出條件

- 兩類版本不符都 fail-closed，原版輸入唯讀。
- 靜態重播與全面回歸不變。

## 驗收條件對照

| Issue #26 條件 | 收據 |
|---|---|
| 至少一則真實動態訊息 | 主選單到海上共十二列動態矩陣列 PASS（[驗證矩陣](../verification-matrix.md)） |
| 以獨立條件驗證一個靜態候選 | 製作名單七個職稱（[目標151](151-static-overlay-implementation.md)）：畫面指紋觸發，與動態事件無關 |
| 不具覆蓋資格者明確記錄 | [目標146 清冊](146-static-text-inventory.md)其餘五項不覆蓋，理由逐項記錄 |
| 英／中／缺譯回退 | 各列英文控制、中文與負例（缺字模、缺譯、重複鍵）收據 |
| 最長譯文幾何 | [目標150](150-dynamic-overlay-verification.md)縮字與超長回原文；規格034 最長職稱 215px／文字帶 748px |
| 輸入版本不符失敗即關閉 | 本輪：五個核心原版檔各改一位元組都拒絕啟動；製作名單圖檔改一位元組時七項記 `image-version-mismatch` 並回原文 |
| 可重生的 dosgolem 正常路徑收據 | 矩陣每列列出 GUI 輸入雜湊與 `regenerate` 腳本 |

## 結果（`tools/check_goal153_slice.py` PASS）

- 前端 `tools/live_menu.go` SHA-256 `85dd7a23166d88a1bfad57e9f849d442e373f8c1c855de78896c0ff3149eea25`：靜態圖檔雜湊不符的原因獨立為 `image-version-mismatch`。
- 新前端重跑目標151 中英重播：九個檢查點原版狀態、套用結果與輸出畫面逐位元組相同；全面回歸六點與目標138收據相同。
- 檢查器摘要 SHA-256 `55df5c7af8f7e230ef2becdaecc015758be06c98760dc647647014c12cbbc2ff`。

## 已知限制

- 改動圖檔會讓原版開場解碼跑進未實作的 80186 指令而中止，因此圖檔負例只跑到 2M 步；守門在載入時判定，這段已涵蓋所有幀。首輪崩潰紀錄在 `workplace/reports/goal153-slice/attempts/image-last-byte/`。
