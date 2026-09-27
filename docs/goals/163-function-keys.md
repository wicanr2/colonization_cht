# 目標163：功能鍵、數字鍵盤與組合鍵轉送（Issue #39）

狀態：完成；2026-09-27。對應 [Issue #39](https://github.com/wicanr2/colonization_cht/issues/39)，擴充[規格024](../spec/024-window-keyboard-input.md)。

## 範圍

- 前端新增輸入種類 `key`：以標準 PC BIOS 鍵字轉送 F1～F10 與其 Shift／Ctrl／Alt 組合、Home／End／PgUp／PgDn／Insert／Delete／Tab、數字鍵盤（對應移動鍵，同幀濾掉重複的數字字元）、Alt／Ctrl 加字母。只用 dosgolem 既有的 `PushKey`，不改 dosgolem、不含本遊戲位址。
- 單元測試逐鍵核對鍵字；非法名稱拒絕。
- 真 GUI：英國開局到海上，實按數字鍵盤移動與一個功能鍵報告；以同一份現場輸入重播中文與英文控制，原版狀態一致；移除該鍵的反向對照畫面不同。

## 退出條件

- 規格024 擴充段 CONFORMED；README 與發行說明的按鍵限制更新。

## 結果

- 單元測試逐鍵核對鍵字、非法名稱拒絕、修飾鍵優先序與數字鍵盤去重，全部通過。
- 真 GUI（Ebitengine／Xvfb）英國路徑到海上，實按數字鍵盤 8、7、F1、Esc：船往北、往西北，F1 開啟地形百科，Esc 返回。四張現場截圖與同輸入中文重播逐像素相同；中英原版狀態在五個檢查點一致；移除全部 `key` 事件的反向重播在按鍵後全部不同。檢查器 `tools/check_goal163_window.py` PASS。
- 六點回歸對 `goal161-regress-a` PASS，既有中文顯示不變。
- 驗證矩陣新增「功能鍵、數字鍵盤與組合鍵轉送」列。
- 規格024 擴充段限定 CONFORMED；README 與發行說明的按鍵限制已更新（已發布的 `v.0.1.0-20260927` 不含本功能）。

未驗：其餘功能鍵與組合鍵在本遊戲的效果。收據只在忽略的 `workplace/reports/goal163-keys/`。
