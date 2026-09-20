# 目前脈絡

日期：2026-09-20

## 已確認

- 目標是《Sid Meier's Colonization》（1994）的繁體中文**輸出階段轉譯層**，不是 remake。
- 動態輸出文字與靜態圖像內嵌文字都在研究範圍；原版檔案不修改。
- GitHub 儲存庫 `wicanr2/colonization_cht` 是私有儲存庫。
- 本機兩份原始封存檔僅能唯讀使用，已由 `.gitignore` 排除；雜湊與清冊見 `RESEARCH-LOG.md`。
- 未完成項的唯一機器可讀來源是 `docs/worklist.json`；每筆都有 GitHub Issue。
- `README.md` 是專案首頁；第一輪目標見 `docs/goals/001-foundation-and-evidence.md`。
- `workplace/dosgolem` 是提交 `d9c0c27` 的獨立副本，push URL 為 `DISABLED`；不得修改其他
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
  僅作未消費的 delay；此外它以三組 `0x226=1 → 0` reset、`0x22E` status 和 `0x22A=0xAA` 判定 DSP
  成功。預設 probe 對這些 port 回 `0xFF`，使這些常式失敗；「它是無畫面的唯一原因」仍只屬
  strong inference。可實作的最小 profile 見 `docs/spec/002-colonization-sbpro-opl-profile-ready.md`。

## 尚未確認

- 印字常式、文字來源、靜態文字資產、字型來源、術語政策與中文化完成門檻。
- `OPENING.EXE` 的第一個可見畫面或可證實 `VICEROY.EXE` 轉交（目前需先經 #22／#23 處理 OPL
  相容層），以及字型來源、術語政策、中文化完成門檻、授權、公開發布與封裝範圍。

## 下一閘門

Issue #22 已以 READY 規格完成。新的執行前沿是 #23：只依規格 002 實作可選的 `-sbpro` profile，並以
相同 state 的正式 `OPENING.EXE` 路徑重新取得 reset、可見或轉交收據。#5 與 #8 在 #23 之前維持阻塞。
Windows NE 清冊（#19）只保留為歷史輸入證據。Issue #10 與 #15 仍需在真實證據與原型具備後由使用者決定。
