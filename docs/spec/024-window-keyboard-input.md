# 規格024：視窗鍵盤轉送原版 DOS 輸入

狀態：CONFORMED（僅 Ebitengine 視窗到既有 dosgolem 鍵盤佇列）；日期：2026-09-24。
承接[目標095](../goals/095-player-name-input-and-overlay-gate.md)、
[規格023](023-player-name-screen-draft.md)與
[Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)。
本規格只授權玩家按鍵轉送，**不**授權姓名提示或其他文字的正式中文覆蓋。

## 證據與範圍

- **confirmed（固定原版）**：合法 DOS `OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`，
  `VICEROY.EXE` SHA-256
  `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`。
  目標093在16筆正常玩家前置輸入（SHA-256
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`）
  後，55M步送入 `x`（掃描碼 `0x2D`／ASCII `0x78`）會取代預設姓名；
  57M步送退格（`0x0E`／`0x08`）會清除；Enter（`0x1C`／`0x0D`）
  會進入下一段國家介紹。雙次冷啟動與無觀測控制收據見
  `workplace/reports/goal093-name/verified.json`，指紋記於規格023。
- **confirmed（平台與工具契約）**：隔離 dosgolem 提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f` 的
  `internal/dos/scancode.go` 以 IBM set-1 掃描碼對應英文字母、數字及空格，
  `internal/dos/bios.go` 提供 `DOS.PushText`／`DOS.PushKeyNamed`；
  `internal/dos/keyboard_test.go` 驗證佇列順序及 `int 16h` 讀回。
  Ebitengine v2.9.9 `input.go:AppendInputChars` 提供依目前鍵盤配置產生的可列印字元；
  Backspace／Enter 是控制鍵，不經此字元通道。
- **未知**：原版姓名欄是否接受所有字母、數字、空格、標點、非 ASCII 字元，
  以及存檔持久化語意，不能從平台鍵表推得。此處保證的是如實轉送，
  不是宣稱所有字元都被原版姓名欄接受。原版檔案位移、DOS 實模式
  `CS:IP`、20-bit 線性 RAM 與320×200索引畫布各自獨立；本適配器不
  增加任何遊戲專屬位址。

## 型別、行為與失敗模式

真視窗在焦點內每次 `Update` 讀取 `AppendInputChars`，每個可支援的
單一字元記錄一筆 `text` 輸入（UTF-8 原字元），逐筆交給
`DOS.PushText`；小寫與大寫保留 ASCII 大小寫。只接受 dosgolem 已
證實有映射的 `A–Z`、`a–z`、`0–9`、空格；其他字元不得猜測掃描碼，
不得送半段文字，須在本機診斷及收據中記錄拒絕。失焦時仍清空
Ebitengine 當次文字緩衝，不得待重新聚焦後補送舊鍵。

實體 Backspace／Enter 各記 `backspace`／`enter` 一筆，透過
`PushKeyNamed("Backspace")`／`PushKeyNamed("Return")` 進入同一 DOS
鍵盤佇列；舊 `enter` 收據保持可重播。滑鼠事件及原版遊戲時間
契約不變。收據重播須檢查 `text` 恰為一個支援字元、事件種類、
時間單調及既有滑鼠邊界；拒絕非法輸入而非跳過。

輸入只經原版 BIOS／DOS 鍵盤讀取，不改原版 EXE、TXT、遊戲 RAM、
畫面像素、字型、譯文、規則或存檔格式。姓名欄仍顯示原版可編輯
內容；固定中文提示歸規格023，未 READY 前保持原文。

## 驗收與停止線

1. 容器內單元測試：文字事件的 DOS 掃描碼／ASCII、大小寫、退格、
   Enter、舊收據兼容、非法字元與無效事件拒絕；滑鼠原測試不退步。
2. 真 Ebitengine／Xvfb 視窗由冷啟動以滑鼠走到姓名畫面；實際鍵入
   `x`、退格、Enter，收據保存鍵盤事件。以相同收據重播英文控制
   與中文輸出，原版 CPU、完整 RAM、索引、色盤、時間與開檔一致；
   姓名欄符合目標093的原版可見行為。若只完成無頭重播，維持 READY。
3. 另以一個非法字元和失焦驗證拒絕／不補送，並保持既有滑鼠
   主選單、難度頁及國家頁的正常路徑。

所有驗收收據只存已忽略的 `workplace/`；原版輸入唯讀，原版畫面、
字型與存檔不加入版控。未驗標點、輸入法及其他欄位，不能宣稱
全遊戲鍵盤完整或全文中文化。

## 限定 CONFORMED 收據

實作前已依上述固定原版／dosgolem／Ebitengine 契約審查為限定 READY。
正式視窗接線改用 dosgolem 的 `PushText`／`PushKeyNamed`；不複製
掃描碼表。單元測試從 BIOS 鍵盤環形緩衝讀回 `x`、`A`、`7`、空格、
退格、Enter 的掃描碼與 ASCII，並驗證非法事件、非 ASCII、複字串
及舊 Enter 收據相容。第一次單元測試因缺 `DISPLAY` 停止；同一
Ebitengine 映像改用具 trap 的 Xvfb 後，曾揭露測試誤讀 DOS 後備佇列
（正常鍵其實先進 BIOS 環）；修正測試讀取端後 `go test ./...` 與
`go build` 均通過，未改 dosgolem 程式。

真 Ebitengine／Xvfb 視窗從冷啟動、主選單、難度、選國右卡進入姓名
畫面，實際鍵入 `x`、Backspace、Enter。收據含26筆玩家輸入，其中
姓名鍵在55.2M、59.4M、63.2M步；畫面分別顯示 `x_`、只剩游標及
可見 `FRANCE` 長文。姓名欄兩次差分只在四倍矩形
`(316,392)–(984,448)`；提示安全矩形未變。真視窗姓名／介紹圖
與目標093的 dosgolem 原版控制圖除兩處游標位置外逐像素相同。
同收據中文與英文控制的 CPU、完整 RAM、原版索引、色盤、時間、
開檔及最終狀態完全一致；最終原版索引 SHA-256
`21ec0bf1fa5ce700950c537bd915ec1fe3afbd211400879f9d8d3147d688def4`。

第二次完整真視窗路徑以 `!` 負例及失焦期間 `x` 驗證：前者在
stderr 與本機收據記錄拒絕，後者重新聚焦後沒有補送；事前／事後
畫面逐像素相同。之後正常 `x`／退格／Enter 仍可使用，且與
該次英文控制的完整原版狀態、RAM、索引及色盤相同。
獨立驗證器 `tools/verify_goal095_keyboard.py` 的本機 PASS 收據
`workplace/reports/goal095-keyboard/verified.json` SHA-256
`54ffa9db8a3145f9e93391aa3d557b42c58d968cbd86177a631001f5699c0cae`。
最終版嚴格檢查未使用的收據欄位後，兩份真視窗輸入重播的
CPU、完整 RAM、原版索引、色盤及開檔與先前英文控制逐項相同。
收據中的原版圖、RAM 與字型不入 Git。這只證明已列輸入及拒絕
邊界；其他字元是否被各遊戲欄位接受、輸入法及姓名存檔仍未知。
