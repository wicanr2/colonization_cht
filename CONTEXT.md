# 目前脈絡

日期：2026-09-20

## 已確認

- 目標是《Sid Meier's Colonization》（1994）的繁體中文**輸出階段轉譯層**，不是 remake。
- 動態輸出文字與靜態圖像內嵌文字都在研究範圍；原版檔案不修改。
- GitHub 儲存庫 `wicanr2/colonization_cht` 是私有儲存庫。
- 本機兩份原始封存檔僅能唯讀使用，已由 `.gitignore` 排除；雜湊與清冊見 `RESEARCH-LOG.md`。
- 未完成項的唯一機器可讀來源是 `docs/worklist.json`；每筆都有 GitHub Issue。
- `README.md` 是專案首頁；第一輪目標見 `docs/goals/001-foundation-and-evidence.md`。
- `workplace/dosgolem` 是提交 `1b0efdf` 的獨立副本，push URL 為 `DISABLED`；不得修改其他
  專案使用的 `/home/anr2/cht/dosgolem`。
- 固定雜湊的 `COLONIZE.EXE` 是 Windows 3.10 NE 程式。dosgolem probe 只走到 DOS stub，
  無法進入 Windows 應用程式本體；這是可重現 blocker，不是已支援的冷啟動。
- 固定 NE 的靜態載入面已完成清冊：33 個區段、7 個模組、176 個 ordinal import target、
  42 個資源項目；這只描述檔案結構，不能證實任何 Win16 API 的實際呼叫或文字輸出。
- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標；
  該目錄由 `.gitignore` 排除，291 個檔案／390,317,887 bytes 的 manifest SHA-256 是
  `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。
- 正常 DOS 冷啟動入口是 `OPENING.EXE`（SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）。dosgolem 已在此路徑跑過
  1 億指令、進入 mode 13h／PIT／滑鼠／overlay 與資料讀取，沒有未實作服務；但還沒有第一個
  非零畫面或 `VICEROY.EXE` 轉交收據。
- 正式路徑唯一已記錄的 `EXEC` 是 `PSOUND.COL`（不是 `VICEROY.EXE`）。從第 1,000,000 指令快照
  到第 100,000,000 指令，A0000 維持全零、沒有視訊寫入、沒有字型服務呼叫，且程式停留在
  `PSOUND.COL` 的 `1C43:0087`；這是 confirmed blocker 收據，不是可見畫面。
- `PSOUND.COL` 的 `0x220` status 讀取是已證實的 `0x00 → 0xC0` AdLib 偵測條件，`0x222` 在此版本
  僅作未消費的 delay；此外它以 `0x226=1 → 0` reset、`0x22E` status 和 `0x22A=0xAA` 判定 DSP 成功。
  最小 READY profile 已以 `-sbpro` 實作於隔離副本：固定 state 的第一組 reset 在第 1,004,428 指令
  直接讀得 `0xAA`，隨後正式路徑載入 `MPSLOGO.SS` 與 `MPSNAME.SS`，且沒有未實作 DOS 服務。
- `-sbpro` 路徑至第 100,000,000 指令仍沒有非零 A0000 像素、`VICEROY.EXE` EXEC 或文字輸出。從
  第 1,451,566 指令開始，CPU 進入 `1C43:FA57`；`PSOUND.COL` 只有 `0x0000`–`0xBDD6` bytes，故該位置
  在固定映像外。採樣顯示 `1C43:FA44`–`FA5F` 循環且 SP 持續下降。這是 confirmed 的目前 blocker，
  但其第一個控制轉移邊及根因仍是 unknown；不得推論為音效、DMA 或中文化問題。

## 尚未確認

- 印字常式、文字來源、靜態文字資產、字型來源、術語政策與中文化完成門檻。
- `OPENING.EXE` 的第一個可見畫面或可證實 `VICEROY.EXE` 轉交（目前需先釐清 #24 的映像外控制流），
  以及字型來源、術語政策、中文化完成門檻、授權、公開發布與封裝範圍。

## 下一閘門

Issue #23 已完成 READY profile 的實作與同狀態收據。新的執行前沿是 #24：定位從正常
`OPENING.EXE` 路徑首次進入 `1C43:FA57` 映像外循環的控制轉移／堆疊邊，證據足夠時只建立 DRAFT，
不直接修正。#5 與 #8 在 #24 之前維持阻塞。Windows NE 清冊（#19）只保留為歷史輸入證據。Issue
#10 與 #15 仍需在真實證據與原型具備後由使用者決定。
