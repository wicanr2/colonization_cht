# 目標 014：界定 MCB arena 重新協調的 READY 範圍與缺口

狀態：completed（範圍決策待使用者確認）<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 013](013-mcb-arena-draft-evidence-review.md)；待審查規格：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

把 DRAFT 規格 003 從「已知要協調活躍（active）客體 MCB 鏈」推進為可評估的 READY
邊界：以現行 dosgolem 的 arena、`AH=48h`／`49h`／`4Ah`、`AH=52h`、EXEC 與 state
模型，逐項確認哪些資料可無損表示、哪些必須失敗即關閉（fail-closed），以及固定
`OPENING.EXE` 路徑尚缺哪些同狀態收據。此輪只做證據與規格審查，不實作。

## 固定前提

- 原始 DOS 輸入唯讀：`OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；`PSOUND.COL`
  SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 執行器固定為隔離副本 `workplace/dosgolem` commit
  `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，upstream push URL 是 `DISABLED`；不修改
  `/home/anr2/cht/dosgolem`。
- 目標 013 已確認 `1C42` 是由 `AH=52h` 可走訪的活躍 MCB 記錄；兩個 `AH=49h` caller
  都覆寫 wrapper 返回值。真 DOS 對 `ES=2C9A`／`2C5D` 的精確服務結果仍是 unknown。

## 執行項目

1. 對照 `workplace/dosgolem/docs/spec/012-mcb-chain.md` 與現行 `arena`／`memBlock`／`syncMCB()`，列出
   DRAFT 匯入時必須驗證及目前無法表示的 MCB 欄位、段連續性、owner、PSP 與鏈終止條件。
2. 追蹤 `AH=48h`／`49h`／`4Ah`、`AH=52h`、`AH=4Bh` 與 SaveState／LoadState 的實際資料流，
   分辨可由現有模型保證的事項、需新增的一般性狀態，及不能以本遊戲特例猜補的事項。
3. 以 dosgolem 正式冷啟動收據擷取一次直接寫入後、下一次服務前的完整 MCB headers，確認
   固定路徑能否滿足候選驗證條件；不得用記憶體注入或 DOSBox 取代原版收據。
4. 以 Docker 執行現有 dosgolem 記憶體與 state 契約測試，記錄其實際覆蓋範圍，不把綠色測試
   誤稱為 Colonization parity。
5. 修訂 DRAFT 003：明確寫出可驗證資料模型、拒絕條件、snapshot 原子性與仍需使用者／原版證據
   的架構選擇；若無法安全縮小範圍，提出單一決策問題而不越級實作。

## 停止線

- 不修改 dosgolem、原版檔、遊戲規則、存檔、中文覆蓋、字型或畫面。
- 不把目前單一 PSP／overlay 路徑外推為已支援 EXEC 多行程；不以 owner 值相同或 MCB 外觀相似
  當作可匯入的充分條件。
- 不聲稱真 DOS 的 `AH=49h` parity；僅記錄本原版 callsite 與現行 dosgolem 行為。
- 未取得完整輸入驗證、狀態轉移、失敗語意、snapshot 與同狀態驗收條件前，DRAFT 003 不得升 READY。

## 退出條件

- [x] DRAFT 003 的每個匯入欄位與拒絕條件都有現行 dosgolem／原版收據或明確標為 unknown。
- [x] 固定 `OPENING.EXE` 的直接 MCB 寫入後鏈，已以 headers 與 `AH=52h` 起點交叉驗證。
- [x] 現有 arena、EXEC／PSP 與 state 模型的可表示範圍與缺口已列出，未以推測補洞。
- [x] DRAFT 003 已修訂為較精確的 DRAFT，保留一個清楚的使用者決策前沿；未實作。
- [x] `CONTEXT.md`、`docs/worklist.json`、`WORKLIST.md`、`README.md`、`WORKLOG.md`、`RESEARCH-LOG.md`、
  Issue #24 與 Docker 清理狀態已同步，並完成 Git 提交與推送。

## 審核結論

固定 `OPENING.EXE` 樣本可被嚴格表示為 root PSP `0100` 的連續單一 owner MCB 鏈，且 MCB 的 owner
與八位元組 program name 必須保存。現行 arena／state 沒有這些欄位；既有 child EXEC 路徑也不足以
支持「通用多行程匯入」的結論。範圍選擇會決定資料模型、state migration、服務拒絕語意與驗收矩陣，
故本輪只完成審核並等待使用者在 DRAFT 規格 003 所列 A／B 間作出一項選擇。
