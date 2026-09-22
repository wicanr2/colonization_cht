# 目標062：難度頁完成提示中文顯示

狀態：in_progress；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#26](https://github.com/wicanr2/colonization_cht/issues/26)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 起點

主選單五列與難度頁兩行標題已接原版輸出事件，Ebitengine 真視窗與同輸入英文控制通過。難度頁仍可見 `Click Here When Finished`；`LABELS.TXT` 檔案位移 `0x86E` 有「完成後點此」譯稿，但檔案候選不等於已驗證執行期鍵。既有唯讀探針已捕捉該提示附近的讀取、畫布寫入及前後畫面，須獨立審查。

## 本輪工作與退出條件

1. 由固定 DOS 版與正常玩家輸入雙次重播，確認完整原文字節、執行期來源、讀取／繪製入口、前後畫布差分及安全矩形；區分檔案位移候選與實際資料流。
2. 建立限定此提示的 DRAFT 規格；證據足夠才升 READY，並由唯一 TSV 與已確認字型生成本機字模。不得把同一字串可能出現的其他畫面直接納入。
3. 在原版輸出階段覆蓋；缺譯、缺字模、錯版、游標／背景變更時回退英文。用 dosgolem 正常路徑與 Ebitengine 真視窗比較中英文 CPU、RAM、原始索引畫面、色盤與虛擬時間，逐像素驗證安全區。
4. 若驗收通過，更新截圖、目前狀態、工作清單與既有 Issue；README 只保留穩定成果，不加入逐輪目標連結。

若來源事件或安全矩形不能證實，保留英文與可重播缺口，不把譯稿升格為畫面完成。卡片標籤、help 訊息及全遊戲完成率不屬此切片。
