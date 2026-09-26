# 目標147：靜態文字覆蓋 DRAFT 規格與最小原型（Issue #9）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #9](https://github.com/wicanr2/colonization_cht/issues/9)。

## 結果

- [規格034](../spec/034-static-text-overlay-draft.md) DRAFT：畫面指紋觸發、文字帶清除、失配不覆蓋。
- 原型只用 ST5「GAME DESIGN BY」橫幅；命中、兩張別的畫面、改一像素四組對照 PASS，命中時差異全在指紋矩形內。
- 初版以純色平塗整個矩形，蓋掉卷軸紋理與邊框；改為只清文字帶內的暗色像素並以同列底色補回，門檻依區內色號亮度分布定為 122。

## 停止線

原型不接正式前端；字級與譯名待 #10。
