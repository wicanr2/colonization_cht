# 規格 007：滑鼠事件回呼交換

狀態：CONFORMED<br>
日期：2026-09-22<br>
工作入口：[目標 053](../goals/053-mouse-and-gameplay-route-replan.md)、Issue #25

## 證據

規格 006 修正後，固定 `OPENING.EXE -g` 已正常載入 `VICEROY.EXE` 並畫出主選單。
`workplace/reports/goal053-fixed-g-30m.txt` 仍記錄兩次未實作的 `int 33h AX=0014`；
從主選單快照於 #30,000,001 點 `(128,110)`，#30,000,415 的輪詢讀到按下，
至 #40,000,001 沒有新檔案或選單轉移，畫面游標仍留在中心。固定輸入 SHA-256 見
[規格 006](006-bios-motor-timeout.md)；`VICEROY.EXE` SHA-256
`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`。

confirmed：此服務未實作，dosgolem 的既有 callback 僅由 `AX=000C` 註冊。
假說：缺少 `AX=0014` 使遊戲自身座標及游標未隨事件更新；須修正後由正常玩家路徑裁決。

## 平台契約與最小實作

[DOSBox-X `mouse.cpp` 的 `case 0x14`](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/mouse.cpp)
提供標準介面：輸入 `CX` 為新遮罩，`ES:DX` 為新 far callback；回傳相同三欄的舊值。
實作先保存舊值，再安裝新值，最後回傳舊值；與 `AX=000C` 共用同一 handler 及既有事件佇列。
遮罩為零時不送事件；reset 後沒有有效 handler 時回傳零遮罩與零指標。其他暫存器保持原樣。

只在 `workplace/dosgolem/internal/dos/bios.go` 增補標準服務，不含遊戲位址、座標或專屬條件。
回呼按既有機器層在指令邊界投遞，包含滑鼠移動、按下、釋放，不改寫原版資料。

## 驗收

- 未註冊→註冊、A→B→A 交換，舊指標與遮罩均正確；與 `000C` 互通。
- 新 handler 真的收到相符事件，遮罩零時不送；未實作清單不再出現 `0014`。
- reset 後再交換不得返回舊的有效 handler；既有 callback 暫存器保存測試仍通過。
- 同版本原版由 `-g` 冷啟動抵達主選單，移動後點選「新世界」進入難度畫面；
  以 DOSBox-X 輔助畫面對照畫面類別，不宣稱逐像素相等。

## 審查

2026-09-22：DRAFT 經審查升為 READY。DOSBox-X 標準交換實作與 dosgolem `Mouse.Handler`
三個 uint16 欄位直接對應；沿用 `fireMouseEventMickeys` 與機器 callback 佇列。
平台介面有明確的獨立測試，不依賴未證實的遊戲語意；是否解除選單滑鼠失效仍由原版重播裁決。

## 實作驗收

隔離 dosgolem `22664265ea7d55ea8706448149908c79d3f0897b` 的交換、遮罩與 reset 測試通過，
全套 `go test ./...` 通過。連續冷啟動已能以 `(128,110)` 點選新世界到難度畫面，
未實作服務清單不再包含 `0014`。快照還需規格 008 才能保留該回呼；不能把兩個問題混成一個。
最終畫面、無輸入對照與重播入口見目標 053。DOSBox-X 僅用於畫面類別對照。
