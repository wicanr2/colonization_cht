# CONFORMED 規格 005：已註冊多行程 MCB importer

狀態：CONFORMED<br>
日期：2026-09-21<br>
前置：[READY 規格 004](004-colonization-registered-process-mcb-importer-ready.md)、[目標 021](../goals/021-mcb-registered-process-implementation.md)<br>
範圍：僅隔離的 `workplace/dosgolem` 通用 DOS MCB／程序模型；不含 Colonization 位址、文本、規則或原版檔案修改。

實作版本：隔離 dosgolem 本地提交 `1435f17`（`upstream` push URL 為 `DISABLED`）。

## 已驗證實作

- `memBlock`、state v3 與程序 registry 保存 raw 16-byte header、owner、opaque 8-byte name、parent、
  lifecycle 與 owned block；v2 state 直接拒絕，沒有遷移猜測。
- importer 從 List-of-Lists 的 root MCB 走至唯一 `Z`，驗證嚴格前進、`MemTop`、M/Z、free owner、
  registered owner 與重複段；拒絕時保存 `MCBImportFailures`，不寫回客體記憶體。
- `48h/49h/4Ah/4B00h/4Ch/31h/51h/62h` 由 current PSP 與 registry 驅動。normal child exit 回收其 owner
  blocks；TSR 僅接受「初始 child block、無額外 child 配置、可用 keep 範圍」的已驗證子集。
- publisher 只從已接受的 typed model 重建 MCB 必要欄位，保留 raw header 的 opaque bytes/name；失敗服務不發布
  舊 arena。

## 驗收收據

一次性、無網路、UID/GID 1000:1000 的 Docker 容器在隔離副本執行：

```text
go test ./...
```

所有 dosgolem package 均通過。新增的 `internal/dos/mcb_import_contract_test.go` 覆蓋 direct `$sys$`
header 匯入／失敗 `49h` 不重發、未登錄 owner 拒絕且客體 bytes 不變、child current PSP/owner、TSR
矛盾拒絕，以及 state v3 raw header round-trip／v2 拒絕。

固定原版 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）以 `-sbpro` 從冷啟動執行
2,000,000 指令；報告 `workplace/reports/dosgolem-goal021-opening-overlay-20260921.txt`（gitignore，
SHA-256 `2fa18b931afac4bf15f7d89a1712cb7e98de2a7e29a054097202589cb4a58e00`）確認：

- `PSOUND.COL` 仍在第 834,342 指令以 `AH=4Bh AL=03h` 載入；
- 之後持續讀取 `MPSLOGO.SS`、`MPSNAME.SS`，至 2,000,000 指令仍存活；
- 最終 MCB arena 保留 `$sys$`、`FONTINTR`、`$sound$`、`S$MPSLOG`、`S$MPSNAM`、`$sp-load` 等 raw name；
  owner 為 root `0100`，free owner 為 `0000`；
- 15 次 `AH=49h` 與 1 次成功／1 次容量失敗的 `AH=48h` 未把 chain 發布回舊的 `1C43` arena。

此收據只證明固定 root direct-write／overlay 路徑與已測 synthetic executor 子集；不證明 child EXEC、
TSR、跨程序釋放或完整遊戲的原版 parity。

## 保留停止線

external／未登錄 owner、跨程序 `49h/4Ah`、手改後未知 lifecycle、無法表達的 TSR 與 v2 state 都維持
失敗即關閉（fail-closed）。原版仍未出現可見畫面、文字輸出或 `VICEROY.EXE` 轉交；本規格的 CONFORMED
不得外推為中文化或 Issue #24 已完成。
