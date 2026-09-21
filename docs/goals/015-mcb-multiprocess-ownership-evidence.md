# 目標 015：通用多行程 MCB 所有權與生命週期證據

狀態：in_progress<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 014](014-mcb-arena-ready-scope-audit.md)；待修訂規格：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 已採用的範圍決定

使用者已選擇「B：通用多行程匯入」。因此本目標採用可表示非根 PSP owner 與 child `EXEC`
狀態的方向；不把固定 `OPENING.EXE` 樣本的單一 root PSP 限制當作實作範圍。這是架構邊界決定，
**不是**任何既有程式碼或原版行為已經支援的宣稱。

## 目的

為 DRAFT 規格 003 的通用多行程路線建立最小充分、可回查的證據：確認現行 dosgolem 的
`AH=4Bh AL=00h`、`AH=4Ch`／`AH=31h`、`curPSP`、parent process stack、arena、MCB 發布與
SaveState／LoadState 如何交互作用；再以受控的一般性 DOS 程序測試和固定 `OPENING.EXE` 冷啟動
分開驗證。結果只可修訂 DRAFT 與下一個 READY 前沿，不得實作。

## 固定前提

- 原始遊戲輸入保持唯讀：`OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；`PSOUND.COL` SHA-256
  `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 執行器固定為隔離副本 `workplace/dosgolem` commit
  `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，upstream push URL 保持 `DISABLED`；不修改
  `/home/anr2/cht/dosgolem`。
- 原版正式路徑目前只確認 overlay `EXEC`（`AH=4Bh AL=03h`）；它不能證明 child `EXEC`
  或任意 owner 的原版需求。通用多行程需求來自使用者已選定的架構範圍，必須與遊戲收據分開標示。

## 執行項目

1. 以現行 Go 原始碼與既有測試追蹤 `AH=48h`／`49h`／`4Ah`、`AH=4Bh AL=00h`、`AH=4Ch`／`31h`，
   記錄原始函式／欄位、目前 PSP 切換、parent stack、釋放與 MCB owner/name 發布資料流；每項標示
   confirmed、強推論、假說或未知。
2. 以 IDA Pro 9.4 對固定 `OPENING.EXE` runtime raw-binary 的 `AH=4Bh`／`4Ch`／`31h` callsite 做有界
   查核，確認原版已見與未見的 EXEC／終止模式；保留原始位址、bytes、工具版本、輸入雜湊與地址空間。
3. 以 Docker 執行現有 dosgolem 的 allocator、EXEC、state 契約測試；必要時只建立可丟棄的受控測試
   探針，取得 child owner、回收、TSR 與 state round-trip 的實際缺口。綠色結果只稱為執行器內部證據。
4. 修訂 DRAFT 規格 003：回填使用者採用 B、資料模型至少需表達的 process／owner/name／arena/state
   關係、尚無證據的 TSR 與外部 owner 邊界，以及 READY 前仍缺的失敗語意與同狀態驗收。
5. 更新 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json` 與生成的 `WORKLIST.md`；
   將結論回填 Issue #24，完成 Git 提交、推送與 Docker 清理檢查。

## 停止線

- 不修改 dosgolem、原版檔、遊戲規則、存檔、中文覆蓋、字型或畫面；DRAFT 不升 READY。
- 不把固定遊戲中未觀測到的 child `EXEC`、`AH=4Ch`／`31h`、TSR 或非根 owner 說成原版已證實；
  它們只能作為使用者選定 B 的通用執行器要求。
- 不以 unit test 綠燈、單一 MCB 形狀或導覽名稱宣稱真 DOS／原版 parity；不以 Colonization 位址特例
  填補所有權或回收規則。
- 遇到資料模型、服務錯誤回傳或 state 遷移仍有未證實的行為時，保留 DRAFT 與明確 unknown，停止於
  下一個最小證據缺口。

## 退出條件

- [ ] 使用者選定 B 的採用／排除範圍已回填適當規格與目前脈絡，且固定遊戲證據與通用執行器需求未混稱。
- [ ] 現行 child `EXEC`、結束／常駐、owner、arena、MCB name 與 state 的資料流都有可回查程式／測試證據。
- [ ] 固定 `OPENING.EXE` 的 `AH=4Bh`／終止模式已以 IDA 與 dosgolem 收據列出已見／未見，不外推。
- [ ] DRAFT 規格 003 已列出 B 的最小資料模型、未知邊界與 READY 前驗收；未實作。
- [ ] 文件、Issue #24、Git 推送與 Docker 清理狀態一致，且沒有追蹤原版或 root-owned 產物。
