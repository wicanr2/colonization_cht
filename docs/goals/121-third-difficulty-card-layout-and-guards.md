# 目標121：第三張難度卡片的可逆 Ebitengine 排版與滑鼠守門

狀態：in_progress；日期：2026-09-24。承接[目標120](120-third-difficulty-card-output-evidence.md)與
[規格016](../spec/016-difficulty-card-text-draft.md)，對應既有
[Issue #6](https://github.com/wicanr2/colonization_cht/issues/6)、
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)及
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與範圍

第三張難度卡片原版 `CONQUISTADOR:`／`Moderate` 的來源、兩行5／6個
邏輯像素高的墨跡及印前多色底圖已驗，但「征服者／普通」尚未在畫面
安全呈現。原版畫布放大四倍後，每欄須分別量測中文字模與內距，
不能沿用全域字級；滑鼠在卡片上時也不能蓋掉游標或新繪製的背景。
本輪只做可丟棄 Ebitengine 版式對照與原版互動守門證據，不修改
原版 EXE、資料、規則、存檔、正式 `tools/live_menu.go` 或成果截圖。

## 工作與退出條件

1. 核對 PRIVATE 遠端、Git 作者、既有 Issue、固定 DOS 原版與隔離
   `workplace/dosgolem`；先把本目標推送 `origin/main` 再執行。
   原版及固定 Cubic 11 字型唯讀，原版畫素／字模／報告只留
   已忽略 `workplace/`。所有分析、烘製、建置、測試與 GUI 都在
   限資源、無網路、非 root、一次性 Docker 中執行。
2. 從目標120的雙次 dosgolem 原版收據與同輸入無監看控制，逐欄
   核對 TXT 真譯稿、5／6像素原文墨跡、半開安全矩形、各自行
   印前紋理底圖及固定字型 SHA。量測兩組**欄位專屬**候選字級：
   A 貼近原版字高，B 略增可讀性；各自檢查寬高、四邊內距、
   同中心、換行／裁切政策和最長實際譯文。不能把前兩張卡片
   字級直接當成本卡定案。
3. 沿用現有 `tools/card_preview.go` 以 Ebitengine 輸出同狀態
   原文／A／B 本機 PNG；獨立逐像素驗證原文等於 dosgolem
   索引畫面放大、中文字與恢復背景只在各自安全矩形，
   透明字模下仍是原版紋理。負例至少涵蓋錯原版、錯來源鍵、
   缺字、錯字型、溢出與變造底圖。
4. 用 dosgolem 原版滑鼠事件或既有逐相位收據檢查第三張卡片
   游標移入／移開、左鍵按住／放開及離開卡片的原始畫布與合成
   索引畫面；建立**保守**的逐欄原文回退候選條件及失效邊界。
   不能因單一終點畫面就宣稱所有幀都安全，也不能把未驗條件
   寫入正式前端。
5. 回填規格016的 DRAFT 證據、`RESEARCH-LOG.md`、
   `CONTEXT.md`、`WORKLOG.md` 與唯一工作清單；更新並回讀
   既有 Issue，推送私人儲存庫。收尾核對原版素材／字型未入 Git、
   UID/GID、root-owned／誤建目錄、隔離 dosgolem 禁推及 Docker
   執行中／已停止容器清理。

## 停止線

本輪的 A／B 只是可丟棄視覺樣本，不替使用者決定正式版式；
兩筆譯文仍為 `draft`，規格016仍 DRAFT，正式中文保持十七段。
只有欄位版式經確認、事件與逐欄回退規格審查成 READY 後，才可
另輪接入正式 Ebitengine 輸出並依同狀態驗收升 CONFORMED。
Game Options 的 A／B 字級是另一個待決問題，本輪不代答。
