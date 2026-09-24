# 目標123：確認 Retire 的正常玩家後果與首則 help 新局路徑

狀態：completed（僅固定 Retire 分支蒐證）；日期：2026-09-24。承接[目標111](111-tutorial-hints-state-and-first-help.md)已驗的 `GAME → Retire` 確認視窗及[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)：`@TUTORIAL1` 目前只有原版 DOS 預讀、雙語譯稿，沒有玩家可見正文。對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，不建立同義 Issue。

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

## 驗收結果與下一入口

固定 1,275M 原版確認框，正常滑鼠點 `(130,117)` 的 No 於 1,350M 回到海上遊戲畫面；點 `(133,105)` 的 Yes 則到 `COLONIZATION SCORE`，顯示 `Total Score: 4`，並載入 `WOODPANL.PIK`。Yes 後在 1,351M 按 Enter，到 1,375M 顯示 `COLONIZATION HALL OF FAME`；再於 1,451M 按 Enter，原版於第 1,451,193,903 步正常離開 DOS。這證實本條路徑**不會在同一次執行內回到新局入口**，不代表其他玩家路徑沒有教學提示，也未檢驗跨次啟動的選項保留。

四條分支（未點、Yes、No、Yes→名人堂→結束）各有雙次冷啟動與同輸入無監看控制；CPU、完整 RAM、原版索引／底層畫布／色盤、時間、開檔、輸入佇列及所有實際取樣檔一致。`tools/check_goal123_retire_route.py` 驗原版檔案和玩家輸入 SHA、雙重播、原始畫面及 DOS 結束旗標；`tools/test_goal123_retire_route.py` 的正例、缺原版 `SKIP 77` 與九類竄改／冒用負例通過。本機完整收據留在已忽略的 `workplace/reports/goal123-retire/`，原版畫素不入 Git。

本輪只修正 `tools/probe_goal098_intro.go` 對**可選、預設關閉**的 `-allow-early-exit` 探針：有界玩家事件後若原版真的結束，記錄實際步數及終止畫面，不再把正常結束誤判為探針失敗。未啟用旗標的既有目標111報告逐 byte 與歷史收據相同。沒有新增中文顯示；規格026仍 DRAFT、正式中文十七段、help 顯示零則。後續要另尋**正常玩家新局或教學實際觸發入口**，不能沿此 Retire 路徑假設已返回新局。
