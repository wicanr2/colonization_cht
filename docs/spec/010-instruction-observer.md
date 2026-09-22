# 規格 010：精確指令前只讀觀測

狀態：CONFORMED（下列限定驗收）<br>
日期：2026-09-22<br>
入口：[目標 056](../goals/056-live-menu-overlay.md)、Issue #26

## 範圍與證據審查

本規格只增加隔離 dosgolem 的通用觀測能力，不修改 CPU、DOS、輸入、畫面或遊戲規則。
基底 `22664265ea7d55ea8706448149908c79d3f0897b`，來源為
`workplace/dosgolem/internal/machine/machine.go` 的 `Step()` 與 `oracle/run.go`。
confirmed（源碼查核）：既有 oracle OnCall 在 Machine.Step 前觸發；Step 先派送中斷／
滑鼠回呼，才執行 CPU 指令。故其觀測可能遭中斷重入，不等於一次實際 CPU 指令。
Machine.Step 的快速／追蹤分支有共同的 `insnCS/insnIP` 賦值位置；此處在派送後、CPU.Step前。
本輪不變更既有 OnCall 語意，也不增加沒有需求的 Oracle 包裝：根套件公開 Machine/DOS
別名已可使用 SBPro、正常滑鼠與寄存器介面。

## 契約

- `Machine.SetBeforeInstruction(func())` 註冊單一同步觀測函式；`nil` 解除。
- 在每次真正呼叫 CPU.Step 之前恰呼叫一次，位於指令位址記錄後，快速／追蹤路徑共用。
- 觀測者看到派送後本次真正執行的 CS:IP 與尚未執行指令的寄存器。
  `Machine.Steps` 已遞增，為本次指令編號；與舊探針的 pre-Step 計數相差 1，不能混用。
- 回呼只准同步讀取，不可修改任何機器／DOS 狀態、排入輸入、呼叫 Step 或重入執行器。
  此為使用契約，不宣稱型別系統提供唯讀保證；正式適配器須測開／關觀測的狀態一致。
- 觀測設定不加入快照序列化；Restore 不取消已註冊回呼，對齊既有觀測設定。
  跨 Restore 的遊戲事件狀態由使用端清空，不可把過去的文字事件帶入新時間線。
- 不新增遊戲位址、來源、文字或幾何到 dosgolem。普通 RAM 可直接讀取；mode13h 畫面
  以原始切片的副本觀測。不得將會改 VGA latch 的平面模式 Read8 當純讀觀測。

## 驗收

1. 快速、TraceSegs、WatchDSOn 三路每條實際指令恰一次，nil 解除後不再呼叫。
2. IRQ0、IRQ1、排入滑鼠回呼與目標位置重合時，先見實際 ISR／回呼指令；
   返回原位置後只見一次，不在派送前誤報原位置。
3. 相同合成測試程式及正常原版主選單路徑，觀測開／關後寄存器、RAM、畫面、
   色盤與虛擬時間一致。合成 CPU 測試不冒稱原版驗收。
4. `go test ./...` 在 Docker 通過；原版驗收由本案工具重生，原版輸入缺失需明確 skip。

已審查：輸入、時序、失敗邊界及測試均可由既有源碼確定；無未證實遊戲語意。
允許實作此最小通用觀測，不授權直接將規格 009 的即時未知升為 READY。

## 驗收收據

實作提交 `315d17f6697bcd4040b12749a1038fdf677338f8`；新增
`internal/machine/before_instruction_test.go`，快速／追蹤、IRQ0／IRQ1／滑鼠回呼、
解除與 Restore 保留、狀態不變測試通過；`go test ./...` 通過。
本案 `tools/probe_live_menu.py` 的七組正常冷啟動也得到相同原版狀態，
見 [目標 056](../goals/056-live-menu-overlay.md)。不外推任意遊戲或跨快照事件生命週期。
