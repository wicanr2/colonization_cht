# 目標 016：通用多行程 MCB 服務轉移 DRAFT 審核

狀態：in_progress<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 015](015-mcb-multiprocess-ownership-evidence.md)；待修訂規格：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

使用者已選擇 B（通用多行程 MCB 匯入）。本目標將現行 dosgolem 對 `AH=48h`、`49h`、`4Ah`、
child `AH=4Bh AL=00h`、`AH=4Ch` 與 `AH=31h` 的 process／owner／arena／state 資料流，整理為
可回查、明確區分 executor 現況與原版觀測的 DRAFT 轉移矩陣。這是讓 Issue #24 的執行期記憶體
blocker 往可驗證 READY 前沿移動，不是中文覆蓋或遊戲規則的實作。

## 固定前提

- 原始輸入保持唯讀；`OPENING.EXE` SHA-256 是
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`。
- dosgolem 僅使用隔離副本 `workplace/dosgolem` 的
  `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，upstream push URL 維持 `DISABLED`。
- 目標 015 的固定原版冷啟動只見 `AH=4Bh AL=03h` overlay；child EXEC、終止、常駐與外部 owner
  是 B 的通用執行器範圍，不得宣稱為 Colonization 已證實行為。

## 執行項目

1. 從目前 Go 原始碼與選定既有測試逐項建立 service transition ledger：輸入 PSP／MCB、arena 與
   process stack 的前置狀態、成功與失敗輸出、MCB header 發布、owner/name 保存、child return／TSR
   的處理；每項保留檔案、函式、測試與推論等級。
2. 在 Docker 中只用可刪除的受控測試探針，量測 child 的 `AH=48h`／`4Ah`／`49h` 與 normal exit／TSR
   後 parent 配置、客體 MCB chain、SaveState／LoadState 的實際結果；探針不得留在 dosgolem 工作樹。
3. 將結果與目標 015 的固定 `OPENING.EXE`／IDA 收據相互限制：明列哪些是原版已見 overlay，哪些是
   executor-only 證據，哪些因缺原版正常路徑而仍屬 unknown。
4. 修訂 DRAFT 規格 003，加入 B 的 service transition table、失敗即關閉的匯入拒絕條件、state
   representation 的必要驗收與不能從現有證據推導的行為；不升 READY。
5. 更新 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json` 與生成的 `WORKLIST.md`；
   回填 Issue #24，完成 Git 提交／推送與 Docker 清理檢查。

## 停止線

- 不修改 dosgolem、原版檔、遊戲規則、存檔、中文覆蓋、字型或畫面；DRAFT 不得授權 production code。
- 不用 executor 單元測試、MS-DOS 公開 API 或單一 synthetic MCB 形狀，冒稱 Colonization 的 child／TSR
  原版 parity；固定遊戲的未觀測仍要保持有界。
- 若 `AH=49h`／`4Ah` 的跨程序精確回傳、外部 owner、客體直接改寫 MCB 後的 TSR 回收，或 state
  migration 仍無法由證據定義，保留 unknown 與 DRAFT，停止在最小缺口。

## 退出條件

- [ ] 現行 service／process／arena／state 資料流有可回查 source 與受控 executor 收據，且 owner/name
  遺失或保留行為可重現。
- [ ] normal exit 與 TSR 的 child 後續行為已各自量測，未量測或不適用的狀態明列為 unknown。
- [ ] 固定 `OPENING.EXE` evidence 與 executor-only 行為未混稱，且沒有新增未證實的原版語意。
- [ ] DRAFT 規格 003 已包含 B 的 transition／拒絕／state 驗收前沿，仍未 READY、未實作。
- [ ] 文件、Issue #24、Git 推送與 Docker 清理狀態一致，且沒有追蹤原版或 root-owned 產物。
