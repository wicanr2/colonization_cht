# 工作歷程

## 2026-09-20：建立專案邊界與工作計畫

- 建立 `AGENTS.md`、私有 GitHub 儲存庫與初始提交 `c29c271`。
- 原始封存檔由 `.gitignore` 排除，未提交或推送。
- 建立 GitHub Issue #1–#16，並以 `docs/worklist.json` 作為其機器可讀索引；#16 已完成，
  其餘未完成項都保留可追溯 Issue。
- 驗證與完整探勘尚未開始；所有尚未自動驗證的工作項目標為 `manual`，不宣稱完成。
- Docker：本輪使用的一次性唯讀容器均以 `--rm` 結束；未清理其他專案的既有容器。

## 2026-09-20：建立首頁與第一輪目標

- 建立 `README.md`，說明遊戲、降低語言隔閡的中文化目的、輸出階段轉譯方式與原版素材邊界。
- 建立 `docs/goals/001-foundation-and-evidence.md`，把第一輪限制為輸入清冊、隔離工具鏈、
  dosgolem 探測與冷啟動基線。
- 對應工作登記為 GitHub Issue #17；尚未處理任何原版遊戲資料。

## 2026-09-20：完成目標 001 的證據與 blocker 收據

- 建立 `workplace/dosgolem` 的獨立 clone（`d9c0c27`），並停用其 upstream push，未改動其他
  專案的 dosgolem 工作樹。
- 建立 `colonization-research:20260920-r1`／`r2` 可重建研究映像；r2 只修正 Go PATH。
- 以唯讀封存檔盤點並解包 ZIP 至 gitignore 的 `workplace/original/colwin/`；完整輸入、格式、
  雜湊、工具和 probe 收據記錄於 `RESEARCH-LOG.md`。
- dosgolem probe 確認目標是 Windows 3.10 NE 程式的 DOS stub，未進入遊戲本體；建立 Issue #18
  等待使用者決定後續執行策略。
- Docker：本輪一次性容器均採 `--rm`；輸出以 UID/GID 1000:1000 建立，未清理其他專案資源。
