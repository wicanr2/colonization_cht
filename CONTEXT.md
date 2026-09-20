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
- `PSOUND.COL` 在 1,000,000–2,000,000 指令向 `0x220/0x221`、`0x222/0x223` 寫入 38,846 次，並在
  動態位置 `1C43:0082` 對 `0x220`、`0x222` 各讀取十次；預設 `cmd/probe` 的 `machine.New()` 對這些
  Sound Blaster 相容 OPL 埠回 `0xFF`。公開硬體 port 契約、IDA 位址對照與 DRAFT 規格見
  `docs/spec/001-colonization-sbpro-opl-profile.md`。缺少相容層仍是 strong inference，不能誤稱為
  已證實的卡住原因或硬體逐週期需求。

## 尚未確認

- 印字常式、文字來源、靜態文字資產、字型來源、術語政策與中文化完成門檻。
- `OPENING.EXE` 的第一個可見畫面或可證實 `VICEROY.EXE` 轉交（目前需先經 #22／#23 處理 OPL
  相容層），以及字型來源、術語政策、中文化完成門檻、授權、公開發布與封裝範圍。

## 下一閘門

Issue #21 已以正式冷啟動的最小 blocker 收據完成。Issue #22 的 DRAFT 已完成，但第二組／advanced
OPL status 與 reset 後必要 DSP port 尚未足以升 READY；必須先補足該窄證據，才可由 #23 實作並重新取得
可見／轉交收據。#5 與 #8 在那之前維持阻塞。Windows NE 清冊（#19）只保留為歷史輸入證據。Issue #10
與 #15 仍需在真實證據與原型具備後由使用者決定。
