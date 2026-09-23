# 目標082：第二張難度卡片的逐欄中文覆蓋

狀態：completed（第二張卡片兩行限定範圍）；日期：2026-09-23。承接[目標081](081-second-difficulty-card-output-evidence.md)與
[規格016](../spec/016-difficulty-card-text-draft.md)；對應 Issue
[#6](https://github.com/wicanr2/colonization_cht/issues/6)、
[#7](https://github.com/wicanr2/colonization_cht/issues/7)、
[#12](https://github.com/wicanr2/colonization_cht/issues/12)及
[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍與前置證據

本輪只處理正常玩家點選第二張難度卡片後，原版輸出的
`EXPLORER:`／`Easy` 兩行；來源鍵分別是 `NAMES.TXT:0x00000C18` 與
`LABELS.TXT:0x000008B2`。目標081已以雙次 dosgolem 冷啟動和真
Ebitengine 視窗閉合來源、原版格式化輸出與畫布像素。譯文「探險家／簡單」
目前仍為草稿，不因原文命中就算正式中文顯示。

## 工作與退出條件

1. 由固定原版版本與當次印字前後畫布，量測第二張卡片兩欄的原版墨跡、
   紋理底圖、四倍安全矩形與中文字型候選。每欄分別記錄字級、實際墨跡、
   內距、頂列錨點及最長譯文；基線未知時明寫未知。先產生可丟棄的
   Ebitengine 原文／中文對照，逐像素確認安全區外不變。
2. 以第二張卡片的真實滑鼠點擊路徑，驗證當次背景擷取、格式化顯示鍵、
   原版畫布差分與游標／按鍵保持回退；同輸入無觀測英文控制的 CPU、
   完整 RAM、索引畫面、色盤及虛擬時間必須一致。缺譯、重複鍵、
   錯誤來源指紋及舊背景都須失敗即關閉。
3. 只有前兩項足以形成限定 READY 規格，才從真實 TSV 唯一譯文烘製
   欄位專屬字模，將第二張卡片接入既有輸出層；不修改原版 RAM、
   畫布、規則、存檔、滑鼠命中區或玩家流程。若證據不足，保持 DRAFT
   與英文原樣，回填具體缺口。
4. 正式接線後重播真 Ebitengine 視窗及英文控制、缺譯和游標反例；
   驗證所有新增輸出差異只在第二張卡片兩個核准安全矩形，並目視成果。
   通過後才將本限定規格標為 CONFORMED、更新已顯示中文數及相關 Issue。
5. 更新 `CONTEXT.md`、`WORKLOG.md`、`RESEARCH-LOG.md` 和工作清單現況；
   推送私有儲存庫前核對原版素材、字型及本機畫面未被誤追蹤，並檢查
   Docker 容器與檔案擁有權。

## 停止線

本輪不替 Issue #28 選定難度標題新版式，也不外推到第三至第五張卡片、
help、靜態圖像或完整遊玩。第一張卡片規格017與其安全矩形保持不變。
原版截圖、畫布快照、字型與可丟棄收據只留在 gitignore 的 `workplace/`；
沒有使用者另行授權，不更新已上傳的私有成果截圖。

## 本輪結果

逐欄 21／25px 字模、可逆背景及執行期守門已依
[規格019](../spec/019-second-difficulty-card-overlay.md)通過 READY 審查並
接入正式 Ebitengine 輸出層。從冷啟動真視窗點選第二張卡片，中文與
無觀測英文控制組原版 CPU、完整 RAM、索引畫面、色盤及時間相同；
新增中文差異只在兩個核准矩形。真實 TSV 兩欄各自的缺鍵／重複鍵、
游標進出、錯版本拒絕，以及第一張卡片逐位元組回歸均通過，規格019
僅就這兩行標為 CONFORMED。已驗收正常玩家路徑中文由十段增為十二段。
本機原版畫面不推送；Issue #28 的標題版式與其餘卡片仍待後續處理。
