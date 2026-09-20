# 目標 008：補足 PSOUND 的 OPL status 與 DSP reset READY 證據

狀態：completed（READY 規格已建立；實作交給 Issue #23）  
日期：2026-09-20  
對應 Issue：[ #22 ](https://github.com/wicanr2/colonization_cht/issues/22)  
前置規格：[規格草案 001](../spec/001-colonization-sbpro-opl-profile.md)

## 目的

只補足規格草案 001 明列的兩個 READY 未知項：第二組／advanced OPL status 的可測語意，及
`0x226` DSP reset 後正式 `OPENING.EXE → PSOUND.COL` 路徑實際讀取的最小 DSP port 集。結果必須能
提升或否定特定 DRAFT 條款；不得因「音效相關」擴張成 PCM、DMA、PIT 或逐週期聲音考古。

## 固定前提

- 原始輸入仍是使用者指定的 DOS `COLONIZE/` 目錄，唯讀；`OPENING.EXE` SHA-256 為
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`，`PSOUND.COL` SHA-256 為
  `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 執行器只用 `workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`；不得修改
  `/home/anr2/cht/dosgolem` 或原始輸入。
- 動態收據從固定 `opening-1000000-visible-20260920.state`（SHA-256
  `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`）開始，使用正式冷啟動延續，
  不以 `VICEROY.EXE` direct-entry 或 DOSBox 取代。

## 執行方法

1. 以 IDA Pro 9.4 的 16 位元資料庫列出 `PSOUND.COL` 所有**已解碼且執行期可觀測**的 I/O 指令，
   保留 IDA 線性位址、原始 bytes、DOS overlay `CS:offset` 的明確映射與推論等級；靜態誤解碼不能
   當作 port 使用證據。
2. 以同一固定 state 對這些候選位置設置有界的暫存器觀察，記錄真正在 `PSOUND.COL` 路徑執行的
   `IN`／`OUT`、`DX`、`AX`、步數及 reset 邊緣前後呼叫鏈；必要時只建立可丟棄的診斷輸出。
3. 對標準 OPL3／Sound Blaster port 語意只引用權威公開文件；遊戲 RE 僅確認它採用哪個埠、何時
   讀寫、是否消費結果。若公開文件沒有給出所需位元值，明列為 unknown，不以現有 dosgolem 的
   回退值反推硬體。
4. 依蒐得證據審查規格草案 001：若輸入、啟用條件、兩組 status、DSP reset 後最小 port、失敗模式
   與驗收均足夠，建立 READY；否則保留 DRAFT 並將確切缺口回填 Issue #22。

## 排除項目

- 不實作或修改任何正式 dosgolem 行為；Issue #23 仍受 READY 閘門約束。
- 不把音樂是否可聽、PCM／DMA 的完整支援、第一個畫面或 `VICEROY.EXE` 轉交當成本輪完成條件。
- 不輸出、提交或發布原版資料、反組譯資料庫、原文文本、截圖或音訊。

## 退出條件

- [x] `RESEARCH-LOG.md` 有固定輸入、工具、位址空間、靜態／動態交叉證據與每項等級。
- [x] 規格草案 001 已依證據審查；固定路徑符合 READY 最小契約，已新建 READY 規格 002。
- [x] `CONTEXT.md`、README、`docs/worklist.json`、`WORKLOG.md` 與 Issue #22 同步；`WORKLIST.md` 由工具
  重新產生，Docker 清理後提交並推送。
