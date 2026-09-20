# 目標 012：追溯 PSOUND 覆蓋段寫入者與後續生命週期

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 011](011-psound-clear-argument-provenance.md)；授權邊界：[READY 規格 002](../spec/002-colonization-sbpro-opl-profile-ready.md)

## 目的

以正式 `OPENING.EXE → PSOUND.COL` 冷啟動追溯執行期 `086C` 寫入
`1C43:0BF9` 與 `0C41:621A` 指標表的來源、呼叫者及回傳後時序，判定它是否來自一個可識別的
覆蓋層載入流程，以及原程式為何在後續仍會用 `00C8 × 0140` 描述元清零同一段。

本輪只建立最小的原始控制流與資料流證據；不是修改 dosgolem、改原版、推論任何單一 DOS／滑鼠
服務、實作音效或開始中文覆蓋。

## 固定前提

- 原始輸入唯讀使用者指定的 DOS `COLONIZE/` 目錄：`OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；`PSOUND.COL` 是
  48,599 bytes、SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 執行器固定為 `workplace/dosgolem` commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，以
  `probe -sbpro` 從零冷啟動；其 upstream push URL 必須保持 `DISABLED`。
- 目標 011 已證實：`03A7:000A` 建立指向 `1C43:0000` 的 `FA00` 描述元；`086C` 於第
  834342 至 834406 步寫入同段程式碼與舊遠指標；`03B1:00A6` 於第 1114003 步清零；
  `087E:005D` 於第 1230847 步消費未更新的指標表。

## 執行項目

1. 以有界 dosgolem 冷啟動收據捕捉 `086C` 進入、內部寫入、返回及其最近外層 caller 的
   CS:IP、SS:SP、暫存器、堆疊、段轉移與絕對指令步數；輸出保留在 gitignore 的
   `workplace/reports/`。
2. 以 IDA Pro 9.4 只讀 raw-binary 匯出實際動態 entrypoint、寫入 site 及 caller 周圍的
   指令，逐列保留原始位址、runtime 段:位移、bytes 與推論等級；不以推測性名稱覆蓋原始定位。
3. 追蹤 `086C` 寫入 bytes／指標的來源與消費端，分辨「直接檔案載入」、「記憶體複製」或
   其他形式；若來源尚不能閉合，明確標示未知，不以檔名時間相鄰推論因果。
4. 對照 `086C` 返回至第 1114003 步清零之間的描述元與指標表讀寫，判定是否有已證實的
   釋放、重配、重新載入或重建表事件。
5. 只有在原版行為證實一項通用機器契約缺口時才提出 DRAFT；否則在 Issue #24 記錄最小未知點，
   不修改 dosgolem。

## 停止線

- 不修改 `workplace/dosgolem`、不擴張 `INT 33h`、不實作 DOS、音效、DMA、PCM、PIT、DAC、IRQ
  或中文化功能。
- 不以 `VICEROY.EXE` direct-entry、DOSBox／DOSBox-X、記憶體注入、單一靜態反組譯或檔案名稱
  推測取代正式 `OPENING.EXE` 冷啟動收據。
- 不追入標準 DOS／MCB、硬體或配置細節；除非已有原版 callsite、資料流與玩家路徑證據表明
  它是最小缺口。
- `086C` 在具備來源、至少一個消費者與 caller／return 收據前，只能稱為執行期寫入者。

## 退出條件

- [x] `086C` 的動態 entrypoint、caller、返回、寫入位址與絕對步數有可重跑收據：`02B2:00AF → 086C:0004 → 02B2:00B4`，第 834,304–834,406 指令完成 `PSOUND.COL` overlay、縮放區塊與遠指標表建立。
- [x] 實際 entrypoint 與寫入 site 有 IDA Pro 9.4 raw-binary 匯出，地址空間與輸入雜湊明確。
- [x] 寫入資料來源與清零前後描述元／指標表時序已分類：`AH=4Bh AL=03h` overlay 載入、客體 MCB 直接寫入、現行 `AH=49h` 回 `AX=9` 與過期 arena 重發佈均為 confirmed；真 DOS 的精確 `AH=49h` 規則與完整後續控制流仍為未知。
- [x] 已建立 [DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)，未實作。
- [x] `CONTEXT.md`、`docs/worklist.json`、`WORKLIST.md`、`README.md`、`WORKLOG.md`、Issue #24 與 Docker
  清理狀態已同步，並完成 Git 提交與推送。
