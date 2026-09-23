# 目標063：難度卡片文字輸出證據

狀態：in_progress；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#26](https://github.com/wicanr2/colonization_cht/issues/26)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 起點與範圍

難度頁目前僅有標題與完成提示中文化。正常玩家路徑中，選中第一張卡片會顯示
`Discoverer`／`Easiest`；其他卡片文字尚未在同一畫面逐一實測。
既有原版結束快照含 `Discoverer` 於 DOS 線性 `0x4CC6A`，`Easiest` 於
`0x4DF90`，但快照位置不等於已證實的輸出鍵。`GAME.TXT` 與 `NAMES.TXT`
都有難度稱號，不能任意選其中一份譯稿作為顯示來源。

## 工作與退出條件

1. 在固定原版雜湊下，以 dosgolem 正常滑鼠路徑重播選中第一張卡片，
   記錄兩串文字的完整執行期 bytes、來源讀取點、畫布寫入事件、前後差分和安全矩形；
   用第二次獨立重播核對。若有切卡，對其餘卡片先建立顯示清冊。
2. 以證據分級建立 DRAFT 規格。只在來源與畫面守門均可證實時升 READY；
   此前不得把 `Discoverer`／`Easiest` 直接接入正式覆蓋。
3. READY 後由唯一 TSV 產生已確認字型的本機字模，驗證中英文／缺字模回退、
   同狀態、游標遮擋及 Ebitengine 真視窗安全區。只有通過的卡片計入完成數。

這不改變難度規則、卡片點擊命中區、原版檔案、存檔或遊戲流程；
沒有充分輸出證據的卡片維持英文。help 與其他畫面另行處理。

後續現況：[目標079](079-first-card-formal-overlay.md)已將第一張卡片兩行
限定驗收；[目標081](081-second-difficulty-card-output-evidence.md)已閉合
第二張卡片的原文來源至畫素與真視窗點擊，但中文輸出仍待 READY 與驗收。
本目標對其餘卡片仍進行中，不能用本節的歷史起點否定後續證據。
