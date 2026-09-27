# 目標163：功能鍵、數字鍵盤與組合鍵轉送（Issue #39）

狀態：進行中；開始：2026-09-27。對應 [Issue #39](https://github.com/wicanr2/colonization_cht/issues/39)，擴充[規格024](../spec/024-window-keyboard-input.md)。

## 範圍

- 前端新增輸入種類 `key`：以標準 PC BIOS 鍵字轉送 F1～F10 與其 Shift／Ctrl／Alt 組合、Home／End／PgUp／PgDn／Insert／Delete／Tab、數字鍵盤（對應移動鍵，同幀濾掉重複的數字字元）、Alt／Ctrl 加字母。只用 dosgolem 既有的 `PushKey`，不改 dosgolem、不含本遊戲位址。
- 單元測試逐鍵核對鍵字；非法名稱拒絕。
- 真 GUI：英國開局到海上，實按數字鍵盤移動與一個功能鍵報告；以同一份現場輸入重播中文與英文控制，原版狀態一致；移除該鍵的反向對照畫面不同。

## 退出條件

- 規格024 擴充段 CONFORMED；README 與發行說明的按鍵限制更新。
