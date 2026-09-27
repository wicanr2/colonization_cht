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

## 2026-09-24：海上與選項頁具名控制鍵擴充（限定 CONFORMED）

此段只擴充前端鍵盤**轉送**，不改上節已限定 CONFORMED 的姓名輸入，不宣稱遊戲對所有方向鍵均會移動。合法 DOS `OPENING.EXE`／`VICEROY.EXE` 及正常玩家前綴 SHA-256 同上；`GAME.TXT` `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`、`MENU.TXT` `5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`。隔離 dosgolem 固定 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，其 `internal/dos/scancode.go` 已有 `Escape`、`Left`、`Right`、`Up`、`Down` 的具名 BIOS 字組；Ebitengine v2.9.9 的 `KeyEscape`／`KeyArrowLeft`／`KeyArrowRight`／`KeyArrowUp`／`KeyArrowDown` 與 `inpututil.IsKeyJustPressed` 已由鎖版模組原始碼核對。這些是平台／適配器鍵名，非本遊戲地址。

**已證實的玩家路徑：**[目標110](../goals/110-tutorial-hints-player-trigger.md)原版海上左鍵被取走並改變畫面；[目標111](../goals/111-tutorial-hints-state-and-first-help.md)在 `Game Options` 按 Esc 後回海上，左鍵與 Space 待取數各由1降至0；[目標123](../goals/123-retire-confirmation-and-help-route.md)證實 Retire 是結束路徑，不能替代正常遊戲操作。**未知：**右／上／下在各畫面有何玩家效果、Esc 在其他畫面是否關閉、Space 是否真正結束回合，以及 help 觸發。四倍視窗座標、原版320×200畫素、DOS 線性 RAM／實模式位址與按鍵掃描碼不得混用。

型別契約：新收據 `windowInput.kind` 僅增加 `escape`、`left`、`right`、`up`、`down`；每筆 `Text` 空、`X=Y=Button=0`，沿用單調步數檢查。Ebitengine 在視窗有焦點時僅對**按下邊緣**送一筆，由 `DOS.PushKeyNamed` 排入原版鍵盤；無焦點時不排入、不補送。方向鍵及 Esc 不經 `AppendInputChars`。空格仍只走既有一字元 `text`，不可另增具名 Space 造成雙送。現有 `text`／`backspace`／`enter`、滑鼠收據及英文控制保持相容；無效事件、未知鍵及 dosgolem 拒絕一律失敗即關閉，絕不猜掃描碼或改原版 RAM。

驗收契約：先做單元測試，逐筆核對五鍵的 BIOS 字組、非法欄位／未知事件拒絕、既有文字與空格只一筆、舊 Enter 收據可重播；再用真 Ebitengine／Xvfb 冷啟動由玩家滑鼠及 Enter 到英格蘭海上介面，實際按左鍵並看原版畫面／鍵盤消費，另到 `Game Options` 真按 Esc。保存真視窗輸入後以同一收據重播中文與英文控制，原版 CPU、完整 RAM、索引／畫布／色盤、虛擬時間、開檔及終點必一致；舊姓名真視窗驗收不能退步。若僅單元或無頭重播通過，此段維持 READY，不升 CONFORMED；新鍵轉送不增加任何正式中文顯示數。

### 限定 CONFORMED 收據

`tools/window_prototype.go` 新增五種具名鍵事件與焦點內的按下邊緣轉送，並維持 Space 原有單字元路徑。真 Ebitengine／Xvfb 視窗由玩家滑鼠與 Enter 冷啟動抵達英格蘭海上；在1,225,400,000步實按 Left，船隻於真視窗移到左方；打開 `GAME → Game Options` 後於1,290,400,000步實按 Escape，真視窗回到海上。原版輸入收據 SHA-256 `dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98`，來源檔 SHA-256 `2e6d4238d4ed0a49797e6750c2ca5135345c2120a17bbd93aafce01f992ee1eb`，終點原版索引 SHA-256 `95e4fb3efcd7cf0391f46767711274096221d305da97885ed7a1d2f1e06d61c0`。同收據英文控制的原版 CPU、完整 RAM、索引、色盤、開檔及虛擬時間均相同。

只刪除 Left／Escape 的兩個本機反向重播，其終點原版索引各與真視窗不同；失焦真視窗 Left 不入收據、不在重聚焦時補送，英文控制的完整原版狀態相同。先前已驗姓名真視窗收據由新前端重播，與舊英文控制的原版狀態、完整 RAM、索引、色盤及開檔一致。`tools/check_goal124_keyboard.py` 正例、`tools/test_goal124_keyboard.py` 缺原版 `SKIP 77` 與八類篡改負例，以及 Go／Ebitengine 單元測試均通過。本節只把**具名鍵轉送與已驗 Left／Escape 正常玩家路徑**升為限定 CONFORMED；右／上／下在本遊戲的效果、其他畫面的 Escape、help 觸發及新增中文顯示仍未知。所有原版收據與畫面僅存已忽略 `workplace/reports/goal124-keyboard/`。

## 2026-09-27：功能鍵、數字鍵盤與組合鍵（限定 CONFORMED，目標163）

型別契約：`windowInput.kind` 新增 `key`，`Text` 為前端鍵名、`X=Y=Button=0`。鍵名對應標準 PC BIOS 鍵字（高位元組 set-1 掃描碼、低位元組 ASCII），以 dosgolem 既有 `PushKey` 排入 BIOS 環形緩衝，不改 dosgolem、不含本遊戲位址：

| 鍵名 | 鍵字 |
|---|---|
| `f1`～`f10` | `3B00`～`4400` |
| `shift-f1`～`shift-f10` | `5400`～`5D00` |
| `ctrl-f1`～`ctrl-f10` | `5E00`～`6700` |
| `alt-f1`～`alt-f10` | `6800`～`7100` |
| `home`／`end`／`pgup`／`pgdn`／`insert`／`delete` | `4700`／`4F00`／`4900`／`5100`／`5200`／`5300` |
| `tab` | `0F09` |
| `kp1`～`kp9`、`kp0`、`kpdot` | NumLock 關閉時的移動鍵字（`kp5` 為 `4C00`） |
| `alt-a`～`alt-z` | 字母掃描碼、ASCII 0 |
| `ctrl-a`～`ctrl-z` | 字母掃描碼、ASCII 1～26 |

Ebitengine 焦點內只取按下邊緣；修飾鍵依 Alt、Ctrl、Shift 的優先順序判斷。Alt／Ctrl 按住時不另送字元；數字鍵盤按下的同一幀去掉平台另產生的數字或小數點字元，避免重複輸入。

驗收：單元測試逐鍵核對鍵字、非法名稱拒絕、Shift+F1、數字鍵盤去重與 Alt 組合（`tools/window_prototype_test.go`）。真 Ebitengine／Xvfb 以玩家鍵鼠走英國路徑到海上，實按數字鍵盤 8（船往北）、7（往西北）、F1（開啟地形百科）、Esc（返回）；現場四張截圖與同輸入中文重播逐像素相同；中英原版狀態在五個檢查點一致；移除全部 `key` 事件的反向重播在按鍵前狀態相同、按鍵後全部不同。前端 `tools/window_prototype.go` SHA-256 `139bce614327c675e13f3808035d2ebcc12241f8dd804a513d46e6c622a57e60`，檢查器 `tools/check_goal163_window.py` PASS（摘要 `0901f25b…`），收據只在忽略的 `workplace/reports/goal163-keys/`。

未驗：其餘功能鍵與 Alt／Ctrl 組合在本遊戲的效果（轉送已驗，遊戲語意逐項未驗）；輸入法與非 ASCII 字元仍拒絕。
