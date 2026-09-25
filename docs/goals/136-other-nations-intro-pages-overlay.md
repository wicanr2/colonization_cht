# 目標136：法國、西班牙、荷蘭首次國家介紹接正式 Ebitengine

狀態：進行中；開始：2026-09-25。對應 [Issue #30](https://github.com/wicanr2/colonization_cht/issues/30)，承接[目標135](135-england-intro-pages-overlay.md)與[規格025](../spec/025-first-nation-introduction-draft.md)。

## 範圍與做法

三國沒有既有真玩家錄製輸入。本輪以真 Ebitengine 視窗、真鍵鼠在選國頁點對應旗卡後走到兩頁，錄下的現場輸入再做中英同輸入重播；頁面常數取自目標101／102 已證實的探針收據（可見字數、序列 SHA、改色點數、bbox、同一印前底圖與讀取位址）。前端新增 `-nation-intro-a` 涵蓋四國八頁，`-england-intro-a` 不變。

## 退出條件

1. 以相同版式烘製三國六頁字模；新換行規則下三國版面與目標102 相同。
2. 每國：真 GUI 兩頁現場截圖；該現場輸入的 A、B、離頁三點中英同輸入原版狀態相同、差分只在頁內；現場截圖與重播逐像素相同。
3. 英格蘭兩頁與既有欄位回歸不退步。更新規格025、文件、worklist 與 #30；完成後關閉 #30。

## 停止線

原版像素、原文與截圖只留已忽略的 `workplace/`。
