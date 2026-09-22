# 規格 006：BIOS 計時器的磁碟機馬達倒數

狀態：CONFORMED<br>
日期：2026-09-22<br>
工作入口：[目標 053](../goals/053-mouse-and-gameplay-route-replan.md)、Issue #25

## 證據與影響

固定 `OPENING.EXE` SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`，
以原版 `COLONIZE.BAT` 的 `-g` 參數冷啟動，略過開場後停在執行期 `0562:0032–0037`。
IDA Pro 9.4 解碼的 runtime dump SHA-256 為
`b11e4e6a599ce3b38dc2c44bfeb30785d1d45ec07c2baad1a085b17988111cde`：

- `0562:002E = 26 A2 40 04` 寫入 `0000:0440 = 1`。
- `0562:0032 = 26 38 06 40 04` 比較同一位元組，`0562:0037 = 74 F9` 相等時迴圈。
- dosgolem `1435f175e785ea096a9268cd1021a4222300bd43` 在 30M→31M 期間到達 BIOS
  `0080:0420`，卻沒有任何 `0x440` 寫入，終值仍是 1；至 100M 仍停在此處。

以上是 confirmed 的有限停滯證據，不涉及音訊逐週期逆向。原始 dump／trace 留在
`workplace/reports/goal053-*`；IDA 位址零點為 raw dump 起點，文件位址均為 dosgolem 執行期段:位移。

## 平台契約

[DOSBox-X BIOS 資料區定義](https://github.com/joncampbell123/dosbox-x/blob/master/include/bios.h)
將線性 `0x440` 定義為磁碟馬達倒數，`0x43F` 為運轉狀態。
[DOSBox-X INT8_Handler](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/bios.cpp)
在 BIOS timer 處理時遞減非零倒數；較新 EGA/VGA 機型在零停止，1→0 時清掉運轉狀態低四位。
本規格採此平台契約，屬硬體規格近似（hardware-spec approximation），不宣稱逐週期精確。

## 最小實作範圍

1. 在既有 BIOS `int 08h` stub 的 tick 更新後、`int 1Ch` 前處理 byte `0040:0040`。
2. 值為 0 時保持 0；非零時減 1；僅在 1→0 時把 `0040:003F` 與 `F0h` 做 AND。
3. 保留既有暫存器、堆疊、旗標還原與 `int 1Ch` 鏈。自訂 `int 08h` 未鏈回 BIOS 時不代為倒數。
4. 機器層不含遊戲名稱、原版位址或輸入腳本。實作在 `workplace/dosgolem`，上游不修改或推送。
5. 舊快照含舊 BIOS bytes，不能用來驗收新行為；驗證須由固定原版重新冷啟動產生新快照。

## 驗收與停止線

- 合成機器測試涵蓋 0、1、2、255，確認倒數、狀態高位保留、`int 1Ch` 觀測順序及暫存器還原。
- 掛自訂 `int 08h` 且不鏈回時，倒數不得變更。
- 執行 `go test ./internal/machine ./internal/dos ./internal/state ./cmd/probe`。
- 以 `OPENING.EXE -g` 的冷啟動正常輸入重播，確認已離開 `0562:0032–0037` 並取得下一個畫面／具體缺口。
- 不擴充磁碟實際轉速、DMA 或實機音訊時序。

## 審查

2026-09-22：DRAFT 經證據審查升為 READY。已核對 `machine.go:initVectors` 的 BIOS stub
只有 tick 與 `int 1Ch`，缺少倒數；動態收據確認遊戲確實鏈回此 stub。新增 18 bytes 後，
stub 長 42 bytes，範圍 `0080:0420–0449` 不與特殊入口 `0400–040E` 或 per-vector stub 重疊。
0／1／2／255 及不鏈回的測試可獨立裁決本契約；無剩餘遊戲語意假設。來源與測試之外的硬體行為維持未知。

## 實作驗收

隔離 dosgolem `22664265ea7d55ea8706448149908c79d3f0897b` 已通過全套 `go test ./...`。
原版正常冷啟動的 `goal053-fixed-g-30m.txt` 記錄 #12,368,859 寫入 `0x440=1`，
#12,836,218 在 BIOS stub 變為零，隨後載入 `VICEROY.EXE` 及主選單。
最終可重播工具與同狀態畫面驗收見目標 053；本規格不擴大為逐週期硬體相等宣稱。
