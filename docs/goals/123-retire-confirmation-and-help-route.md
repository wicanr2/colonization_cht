# 目標123：確認 Retire 的正常玩家後果與首則 help 新局路徑

狀態：in_progress；日期：2026-09-24。承接[目標111](111-tutorial-hints-state-and-first-help.md)已驗的 `GAME → Retire` 確認視窗及[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)：`@TUTORIAL1` 目前只有原版 DOS 預讀、雙語譯稿，沒有玩家可見正文。對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，不建立同義 Issue。

## 玩家問題與固定證據

教學選項雖已在遊戲中證實可切換核取圖示，但是否能在下一局開始前保留尚不明；因此不能憑檔案中有 `@TUTORIAL1` 就宣稱 help 已顯示。目標111的英格蘭正常玩家路徑在1,275M／1,300M顯示原版確認框，實際印字有 `Do you really want to quit? Yes No`。對既有1,275M原版底層畫布的唯讀量測得到 Yes 墨跡半開矩形 `(126,102)–(140,109)`、No `(126,114)–(135,121)`，只是**玩家點擊候選**，還不是兩個熱區已證實。

原版 `OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、`MENU.TXT` 等檔案沿目標111固定 SHA-256 與 `tools/check_goal101_nation_intro.py` 的 `FILE_SHA`，十六筆正常開局輸入 SHA-256 `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`。隔離 `workplace/dosgolem` 固定提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，`upstream` 推送位址維持 `DISABLED`。原始畫面座標為320×200，與四倍中文輸出及 DOS 檔案／RAM／實模式位址分開。

## 工作與退出條件

1. 核對乾淨 Git 身分、PRIVATE 遠端、既有 Issue、合法原版、既有探針及 Docker 映像；**先推送本 goal Markdown**，再新增玩家事件或變更探針。所有分析、建置、原版執行、畫素處理與測試限於無網路、限資源、非 root 的一次性 Docker，原版唯讀，輸出只在已忽略 `workplace/`。
2. 從目標111固定 `Retire` 視窗，分別用原版滑鼠點候選 Yes `(133,105)`、No `(130,117)`，另保留未點選控制。按下／放開前後及有界終點記錄原版 CPU／RAM 雜湊、索引／底層畫布／色盤、時間、開檔、鍵盤與實際輸入。若 Yes 導致原版正常結束，探針須明確保存終止步數和原因，不能把預期終止當環境失敗或偽造終點畫面。
3. 每個有結果的分支做兩次冷啟動與同輸入無監看控制；用獨立檢查器驗原版檔案與事件 SHA、雙重播逐 byte、控制狀態、原始畫面檔。錯版、錯事件、壞畫面、控制分歧、把 No 當 Yes、以及缺合法原版 `SKIP 77` 都須有負例。
4. 若 Yes 到達原版新局入口，再沿**正常玩家路徑**重開並比較教學開關狀態及是否實際印出首則 help；若 Yes 直接離開 DOS 或只到別處，記錄已證實的結果與下一個安全入口，不注入 RAM、不假定選項保留，不無界反覆試鍵。原版硬體 PCM／DAC／PIT 時序不在本輪深挖範圍。
5. 回填規格026、`RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md` 和唯一 `docs/worklist.json`，由 `tools/worklist.py` 重生 `WORKLIST.md`；私有推送並回讀既有 Issue。核對 UID/GID、原版素材未追蹤、誤建 root-owned 目錄及本輪 Docker 容器清理。

## 停止線

本輪的 Yes／No 字樣墨跡不是按鈕熱區的先驗證明；若點擊不生效，要以原版畫面與輸入消費定位，不偷偷改成鍵盤捷徑。`@TUTORIAL1` 預讀與譯稿都不計正式顯示；即使找到正文，仍須另行建立文字來源、逐欄字級／安全矩形、READY 規格、Ebitengine 真視窗及同狀態回退，才能增加正式中文段數。規格026未達上述條件前保持 DRAFT，現行正式十七段與 help 零則不變。
