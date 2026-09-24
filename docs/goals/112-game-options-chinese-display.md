# 目標112：遊戲選項視窗九處文字的來源與繁中顯示

狀態：in_progress；日期：2026-09-24。承接[目標111](111-tutorial-hints-state-and-first-help.md)已驗的正常玩家路徑 `GAME` → `Game Options`。對應 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26) 與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

原版選項視窗的來源與候選安全矩形統一記於[規格027](../spec/027-game-options-window-draft.md)；此 DRAFT 不授權正式覆蓋。

## 玩家問題與固定界線

遊戲選項視窗已能由原版海上介面的滑鼠操作開啟，但標題與八列仍顯示英文。本輪優先讓這九處玩家實際可見文字有固定來源、逐欄字級與安全矩形，進而在四倍 Ebitengine 畫布上顯示繁體中文。只翻譯輸出，不改原版選項狀態、滑鼠熱區、鍵盤快捷鍵、EXE、TXT、存檔與規則。`Tutorial Hints` 的圖示「啟用／停用」語意及首則 help 觸發仍未知，不從標籤譯文推定。

固定 DOS `GAME.TXT` SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`、`MENU.TXT` SHA-256 `5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`。前十六筆玩家輸入雜湊 `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`，另由 [選項視窗六筆輸入](../../tools/goal110-game-options.inputs.json)開啟。原版權威為隔離 `workplace/dosgolem` 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，其上游推送位址須維持 `DISABLED`。

## 工作與退出條件

1. 先核對 Git 身分、PRIVATE 遠端、現有 Issue、原版與工具版本；**推送本目標 Markdown 後**才開始新探針或譯文變更。只在限資源、無網路、非 root 的一次性 Docker 工作；原版唯讀、原版文字與畫素只留 `workplace/`。
2. 用正常玩家路徑的 dosgolem 雙冷啟動及無觀測控制，對標題與八列分別建立 `GAME.TXT` 原始位移、DOS 讀入、原版 RAM 印字讀取、實際畫布墨跡的鏈；先區分 `MENU.TXT` 的同名選單項與視窗標題，不因同文就合併來源。固定檔案 SHA、工具版本、地址空間與每項推論等級。若既有收據不足，補最小可重生探針；不得以英文畫面目視取代當次來源事件。
3. 審查 `text/draft.zh-Hant.tsv` 已有的 `@GAMEOPTIONS` 九筆草稿。源 bytes、控制碼 `~`、熱鍵與顯示文案分開記；候選譯文依語境與畫面逐筆校正，源鍵仍綁固定檔案／位移／雜湊。建立獨立正反例，錯版、錯位移、漏譯與重複鍵失敗即關閉或回退原文。
4. 以原版320×200索引畫面量九欄墨跡、基線、色盤、背景與互動狀態；每欄記四倍文字安全矩形、內距、候選字級、最長譯文尺寸及過長策略。可先做可丟棄的 Ebitengine 版面預覽。不同欄不得硬套單一字級；若視覺取捨實質改變原版風格，保留可比較樣本，讓使用者選擇。
5. 只有當來源、狀態與幾何證據足夠，才把專用規格從 DRAFT 審查為限定 READY，接入正式 Ebitengine 輸出。中文與同輸入英文控制、舊十七欄版、缺譯／缺字模／錯版／游標／切換選項／離頁逐幀驗證；原版 CPU、RAM、索引、色盤、時間與開檔不得受影響。全部通過才標限定 CONFORMED、更新正式計數與私有截圖；否則保留草稿／原型，不宣稱已正式顯示。
6. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json` 與由工具產生的 `WORKLIST.md`，推送私有儲存庫並更新、回讀相關 GitHub Issue。收尾核對原版素材未入 Git、輸出擁有權、誤建 root 目錄與 Docker 容器清理。

## 停止線

這輪的九處只限 `Game Options` 真實視窗，不代表所有遊戲選單、help 內文或全遊戲完成；不碰原版功能語意。DRAFT 原型不能算正式中文顯示。若來源或畫面相位不夠確定，先補最小證據，不以相似文本或固定字級猜補。

## 2026-09-24 已完成的來源階段與未達閘門

已先以 `171eb7b` 推送本目標。`-options-audit` 限定開關從正常玩家視窗重播取得九段 `GAME.TXT` 在1,253,314,011步的同一次 DOS 讀入，原版 `0E2D:1F76` 隨後連續讀取與原檔完全相同的168 bytes；原版 `0D21:00C6` 依序印出九段，1,300M畫面可見。雙冷啟動 JSON 指紋皆為 `12ee3876ad4d70a946592dcad667c3fff92ddb31854e584fcf03dd3fadfb08c4`，無監看控制於全部原版狀態檢查點同狀態。獨立來源檢查器 PASS，七項正反例 PASS；既有目標110回歸與379筆草稿控制碼驗證亦 PASS。九欄原文墨跡各為7或8原始像素，候選安全矩形與精確證據見規格027。

本輪把既有九筆草稿「正常路徑輸出未驗」的過時註記訂正為「DOS逐 byte 讀取及同次印字已驗；中間搬運待核對」。這不是新譯稿筆數，也不等於正式畫面。解析緩衝到印字字元緩衝的最後搬運、原版印前多色底圖、反白／游標／離頁及中文字級仍未驗；規格027保持 DRAFT，正式十七段不增加，私有正式截圖不更新。下一個窄工作是以同一來源收據補印前底圖與逐欄回退，並用固定原始 Cubic 11 做可丟棄的 Ebitengine 字級對照。
