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

## 尚未確認

- 印字常式、文字來源、靜態文字資產、字型來源、術語政策與中文化完成門檻。
- Windows 3.x 目標版本的執行策略（Issue #18），以及授權、公開發布與封裝範圍。

## 下一閘門

Issue #18 是目前唯一的架構阻塞：使用者必須選擇擴充 Windows 3.x 路徑或提供合法 DOS 版輸入。
在此之前，Issue #5 的動態文字路徑暫停；靜態 NE 清冊（#19）已完成，不能取代 Windows 3.x 執行收據。
完整阻塞稽核見 `docs/goals/004-execution-strategy-blocker-audit.md`。Issue #10 與 #15 仍需在真實證據與
原型具備後由使用者決定。
