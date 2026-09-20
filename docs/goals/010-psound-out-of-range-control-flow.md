# 目標 010：定位 PSOUND 映像外控制轉移與堆疊邊

狀態：completed（Issue #24 的參數來源追查仍進行中）<br>
日期：2026-09-20<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 009](009-sbpro-profile-and-cold-boot.md)；授權邊界：[READY 規格 002](../spec/002-colonization-sbpro-opl-profile-ready.md)

## 目的

以 dosgolem 的正式 `OPENING.EXE → PSOUND.COL` 冷啟動延續，定位第一次到達
`1C43:FA57` 的控制轉移與堆疊邊，並判定它是檔案／overlay 映像範圍、載入器、控制流或其他
已觀測機器契約的最小缺口。這是為恢復第一個原版畫面與文字輸出所需的證據工作，不是中文
覆蓋、遊戲邏輯或完整音效實作。

## 固定前提

- 原始輸入只讀取使用者指定的 DOS `COLONIZE/` 目錄；`OPENING.EXE` SHA-256 為
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`，`PSOUND.COL` 為
  48,599 bytes、SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 固定 state 是第 1,000,000 指令儲存的 state，SHA-256
  `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`；本輪另以 `OPENING.EXE`
  從零冷啟動交叉驗證，所有步數使用絕對值。
- 執行器固定為 `workplace/dosgolem` 的本地 commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，
  使用 `-sbpro`；不得修改 `/home/anr2/cht/dosgolem`、原始輸入或 profile 行為。
- 已知但尚未解釋的觀察是：第 1,451,566 指令首次觀測到 `1C43:FA57`，它在
  `PSOUND.COL` 原始 offset `0x0000`–`0xBDD6` 之外；第 100,000,000 指令時仍在
  `FA44`–`FA5F` 循環、SP 遞減、A0000 全零。這只證明目前現象，不預設根因。

## 執行項目

1. 以同一固定 state 在首次命中前後建立有界 trace、暫存器、堆疊與 runtime memory bytes 收據；
   記錄入口的前一條控制流指令、CS:IP、SS:SP、flags、原始 bytes 和絕對步數。
2. 監看 runtime 線性範圍 `1C43:FA40` 附近的寫入，回查它是原始 overlay bytes、DOS／EMS 載入、
   自解壓／資料覆寫或未寫入的記憶體；不將「檔案 offset 之外」直接等同程式錯誤。
3. 對可能的 `call`／`ret`／far transfer 或 stack 邊，取得至少兩類獨立證據（執行 trace、memory
   寫入、原始／runtime bytes、DOS 載入紀錄），保留原始定位與 `confirmed`、`強推論`、`假說` 或
   `unknown` 等級。
4. 若證據已能界定要補的機器契約，僅建立 DRAFT 規格並連回本目標；若不足，將最小未知點與可重跑
   收據回填 Issue #24。不得直接修改 dosgolem。

## 執行結果

### 已證實：不是從 `FA57` 直接跳入

- 冷啟動在第 `1,230,846` 指令執行 `087E:005D`，下一指令（第 `1,230,847`）為
  `1C43:0BF9`。IDA Pro 9.4 對執行期傾印的 16 位元解碼為
  `FF 2E 1A 62`／`jmp dword ptr ds:621Ah`；同時的 `0C41:621A` bytes 是
  `F9 0B 43 1C`，即遠指標（far pointer）`0BF9:1C43`。這是 CPU 的正確遠跳轉（far jump），並非字序錯誤。
- `1C43:0BF9` 是到達 `FA57` 前的第一個入口。該區的零 bytes 會順序執行並落入後續
  `FA44`–`FA5F` 循環；固定 state 收據所見的第 `1,451,566` 指令 `1C43:FA57` 因而是下游
  順向落入（fall-through），不是第一個控制轉移目的地。

### 已證實：目標區先載入，後被正式路徑清零

- 冷啟動第 `834,342` 指令，`086C:005D` 寫入 `1D000`–`1D200`，其中包含
  `1C43:0BF9`（線性 `1D029`）的非零執行期 bytes。
- 第 `1,114,003` 指令執行期 `03B1:00A6` 的 `rep stosw` 開始清零；監看器在指令後以
  `03B1:00A8` 標示寫入。其起始暫存器為 `AX=0000`、`DX=00A0`、`SI=00C8`、`ES:DI=1C43:0000`；
  因此迴圈清零 `0xC8 × 0xA0 × 2 = 0xFA00` bytes，涵蓋 `1C43:0BF9`。IDA 16 位元解碼與寫入監看是
  兩類獨立收據。
- 遠指標表在固定 state 的監看範圍內未被改寫，且冷啟動轉移時仍指向已清零的
  `0BF9:1C43`。這排除「讀取 `MPSNAME.SS` 後才覆寫指標」作為目前最小解釋。

### 判定與未解點

此 blocker 分類為**執行期初始化／覆蓋區記憶體生命週期與控制流**，不是 `PSOUND.COL` 檔案範圍、
CPU 遠跳轉字序、PCM／DMA／PIT 或中文覆蓋問題。唯一觀測到的未實作服務是滑鼠
`int 33h AX=0014`；尚未建立它與清零或後續跳轉的因果，故只能列為待驗假說，不能據此實作。

仍未知的是：`03CC` 呼叫鏈為何以 `ES:DI=1C43:0000`、`0xFA00` 長度呼叫清零例程，且為何之後仍選擇
`DS:621A` 的舊遠指標。這是 Issue #24 下一個最小證據工作；尚不足以建立或授權 DRAFT 規格，
也未修改 dosgolem。

本輪 gitignore 收據均在 `workplace/reports/`：控制流報告 SHA-256
`e7ff23bc6241782f9ff0d27e0783bef74b96f01fc4d2f938428cf0091e24f861`、IP log
`f084305312a1e35e448e863f9e764ff58f44314c51990a2abdc86baa3c0949f8`、清零呼叫端傾印
`80387f118eaf01bb4b570581986abc76d85c4cbb7aded8e2ef970676423d19f9`、IDA JSON
`c2a1cb372c449dc9aa656f7801c9ba36a1a45446888769aa7c2075ecf96ab130`。IDA 位址空間是原始二進位（raw-binary）EA；
每一列另保留執行期段:位移，不與原始 EXE／overlay file offset 混用。

## 停止線

- 不重新開啟 PCM、DMA、PIT、DAC、IRQ、完整音效、中文覆蓋、文字抽取或靜態圖像工作。
- 不以 `VICEROY.EXE` direct-entry、DOSBox／DOSBox-X 或未對齊截圖取代 dosgolem 的正式路徑收據。
- 不把異常 PC、單一反組譯輸出或綠色單元測試當成根因；未證實 transfer 一律保留為 unknown。

## 退出條件

- [x] 通向第一個 `1C43:FA57` 的入口、前後控制流、runtime bytes、SS:SP 與步數有可重跑的無原版素材收據。
- [x] `FA40` runtime 範圍的寫入來源已用動態寫入、暫存器與 IDA bytes 分類，並保留未解之處。
- [x] Issue #24／`RESEARCH-LOG.md` 明確記錄仍不足以判定的最小未知點；未實作、未建立 DRAFT。
- [x] `CONTEXT.md`、`docs/worklist.json`、`WORKLIST.md`、`README.md`、`WORKLOG.md` 與 Issue #24 同步，
  Docker 清理、權利邊界及 Git 狀態核對後提交推送。
