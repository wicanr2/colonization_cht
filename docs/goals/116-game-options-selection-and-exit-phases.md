# 目標116：遊戲選項選取、游標與離頁畫面相位

狀態：in_progress；日期：2026-09-24。承接[目標115](115-game-options-source-chain-correction.md)與[規格027](../spec/027-game-options-window-draft.md)，對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 和 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，不另建同義 Issue。

## 玩家問題與邊界

原版九欄的來源讀寫與第一次印前底圖已有直接收據，但選項視窗在滑鼠移到不同列、游標遮字與按 ESC 離頁時的原版畫布相位仍未驗。不能僅用1,300M單張穩定圖作九欄正式中文覆蓋的失效條件。本輪沿已驗英格蘭正常玩家路徑，建立不改規則的可丟棄互動觀測，釐清第一列／末列選取、游標位置與離頁前後可見畫面。原版資料、存檔及正式 Ebitengine 輸出均不修改。

## 工作與驗收

1. 核對 PRIVATE 遠端、Git 作者、原版與隔離 dosgolem；**先推送本目標 Markdown 與 `CONTEXT.md` 入口**，再新增測試輸入或探針。所有執行、搜尋大量資料、測試與抓圖都在無網路、限資源、非 root 的一次性 Docker，原版唯讀。
2. 從 `tools/goal110-game-options.inputs.json` 的六筆正常滑鼠開窗事件出發，只新增有界的移鼠／ESC 玩家事件；比較同一步數的第一列、末列、框外游標及離頁分支。固定原版索引畫面、色盤、CPU／RAM／時間、原版開檔與輸入消費；不得以事件檔內容本身證明互動生效。
3. 如既有樣本只在25M間隔，先用最小可丟棄探針補事件前後相位；針對選取底色、核取圖示、文字墨跡、游標與整張畫布分別量差，區分無關的時鐘／動畫。至少兩次獨立冷啟動及一組無監看控制，建立獨立正反例，缺原版明確 `SKIP 77`。
4. 把已證實的相位與仍未知的回退條件記入規格027、`RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md` 和唯一 `docs/worklist.json`，由工具重生 `WORKLIST.md`；只推自製輸入、探針與檢查器，原版畫素／原文轉存只留忽略的 `workplace/`。推送私有儲存庫並更新、回讀既有 Issue；檢查輸出擁有權、Git 素材邊界及 Docker 清理。

## 停止線

若只能證明部分互動相位，就明列未驗步數與座標，不用抽樣推論所有列或所有動畫幀。原版解析至高位址 RAM 的中間資料邊、中文字級／快捷鍵呈現和正式逐欄回退仍是獨立閘門；規格未 READY 前保持原文，不把可丟棄預覽計入十七段正式中文顯示。
