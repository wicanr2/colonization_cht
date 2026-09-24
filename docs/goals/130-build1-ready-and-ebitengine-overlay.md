# 目標130：首張開場字幕的限定 READY 規格與正式視窗中文

狀態：進行中；開始：2026-09-25。承接[目標129](129-build1-runtime-frame-lifecycle.md)、[規格026（DRAFT）](../spec/026-build-intro-and-tutorial-prefetch-draft.md)及[目標128字級決定](128-a-layout-decisions-and-build1-runtime-gate.md)。對應既有 [Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，不新增同義工作。

## 本輪交付範圍

只在固定 DOS 原版、英格蘭正常玩家路徑的第一張 `GAME.TXT:@BUILD1` 字幕上，將已確認的 A 版 38px 繁中譯文接到真正的 Ebitengine 四倍視窗。原版程式、資料、RAM、規則、存檔與輸入不可改；譯文只從現行 UTF-8 TSV 讀取，字模只在本機以固定字型烘製，不入 Git。`Game Options` 九欄的 A 字級已由目標128決定，本輪不重做、不誤算為正式中文字。

## 工作與退出條件

1. 核對工作樹、Git 身分、私有遠端、既有 Issue、合法原版與隔離 dosgolem；先推送本目標與 `CONTEXT.md` 入口，再進行工程。所有原版執行、建置、測試、字模與抓圖只在有界、非 root、預設無網路的 Docker 一次性容器；掛載前驗證每個來源。
2. 補齊字幕 READY 審查所需的原版輸出事件、逐幀畫布／色盤、游標合成與安全矩形證據。將當次印字、1,040點畫布變更、印前多色底圖、離頁立即失效、缺譯／缺字模／錯版本／畫面或色盤變動回退寫成狹窄 typed 契約。來源至最終印字緩衝的未閉合中間搬運應保留分級，不得冒稱完整證實；若會影響安全顯示則先停在 DRAFT 補證。
3. 規格經證據審查升限定 READY **之後**，才在本專案正式視窗適配器加入預設關閉的 `@BUILD1` A 覆蓋。用原版當幀印前背景建立可逆補片；每幀比對原版版本、當次事件權杖、畫布、色盤、模式及游標安全區。錯誤、缺譯、重複鍵、錯字模、溢出或離頁一律保留原文並記錄原因，不把中文字寫回 DOS 記憶體。
4. 以既有真實 Ebitengine 玩家輸入重播英文控制／中文正式分支，跑過字幕出現與離頁；dosgolem 的 CPU、完整 RAM、索引／底層畫布、色盤、虛擬時間、開檔與輸入須同狀態。逐像素確認中文僅在字幕安全矩形、陰影與字級符合 A，缺譯／游標遮擋／錯版／離頁反例回退；既有十七段顯示回歸不退步。只在實際驗收範圍內將限定規格標為 CONFORMED 並更新合適截圖。
5. 若 READY 或真視窗閘門未過，保留 DRAFT、提交具體缺口與可重播證據，不宣稱字幕正式中文或更新截圖。回填 `RESEARCH-LOG.md`、`WORKLOG.md`、`CONTEXT.md` 與 `docs/worklist.json`，重生 `WORKLIST.md`；私有推送並回讀 Issue。收尾檢查原版素材未追蹤、輸出 UID/GID、Docker 容器清理與隔離副本禁推設定。

## 權利與停止線

原版 EXE／TXT、字型原檔、原版像素及含原版像素的對照 PNG／完整收據均只留忽略版控的 `workplace/`。本輪不處理 `@BUILD2–10`、help、其他國家字幕或遊戲選項九欄；它們的草稿與待辦仍有效，不因首張字幕完成而關閉整體中文化 Issue。
