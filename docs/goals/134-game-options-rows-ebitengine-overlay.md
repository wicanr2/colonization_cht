# 目標134：遊戲選項八列接正式 Ebitengine

狀態：進行中；開始：2026-09-25。承接[目標133](133-game-options-rows-hotkey-and-print-events.md)與[規格031（限定 READY）](../spec/031-game-options-rows-a-ready.md)。對應既有 [Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 工作與退出條件

1. 以現行 TSV 與固定 Cubic 11 本機烘八列字模，綁定來源鍵、整份 TSV、譯文、字型、字級與尺寸。
2. 正式前端新增預設關閉的旗標，依規格031狀態機逐列建立當次權杖、擷取當次印前底圖、等真 VGA 同步後繪製；游標、按住、底層改變、ESC 與錯事件都回英文。不改原版記憶體或輸入。
3. 用真玩家輸入重播做中英同輸入對拍：開窗、懸停、點擊一列、ESC。原版完整狀態相同、差分只在八列安全區；標題與既有十九欄不退步；缺譯／重複鍵／缺字模／錯字級等負例回英文。
4. 真 GUI 以真鍵鼠走到選項視窗並點擊一列，現場截圖與重播逐像素一致，才將規格031標為 CONFORMED。
5. 更新 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json` 與 Issue，私有推送並回讀。

## 停止線

只完成遊戲選項視窗九欄，不外推到其他視窗、其他國家或 help。原版畫素與截圖只留已忽略的 `workplace/`。
