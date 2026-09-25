# 目標133：遊戲選項八列的快捷鍵呈現與當次印字事件

狀態：進行中；開始：2026-09-25。承接[目標132](132-game-options-title-event-and-overlay.md)的標題限定 CONFORMED、[規格027（DRAFT）](../spec/027-game-options-window-draft.md)與[目標122](122-game-options-nine-field-state-guard.md)的固定相位回退矩陣。對應既有 [Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，不新增同義 Issue。

## 使用者決定（2026-09-25）

八列的 `~` 快捷鍵以英文字母保留、放在中文**前面**、半形括號加一個空格，並與中文**同色**，例如「(I) 顯示原住民行動」。不比照原版把字母另上黃色。字級沿用已定案 A：25／28／28／25／28／28／27／28px。

## 工作與退出條件

1. 先推送本目標與 `CONTEXT.md` 入口，再改譯稿或程式。所有分析、建置、測試、遊戲與抓圖限有界、非 root、預設無網路的 Docker；原版唯讀掛載。
2. 把 `text/draft.zh-Hant.tsv` 八列改成 `(~X) 中文` 形式，譯稿驗證器仍須通過；以固定 Cubic 11 與八列各自 A 字級重量實際墨跡，確認都在四倍安全矩形內且保留內距。改動整份 TSV 後，既有十九欄字模依現行 TSV 重烘，已驗欄位的 Alpha 與像素收據不得退步。
3. 以 dosgolem 正常滑鼠開窗，逐列追 `0D21:00C6` 當次讀字、`0D21:012C` 畫布改色、印前／印後**列局部**底圖與真 VGA 同步；雙冷啟動、無監看控制與負例。檔案位移、實模式 `CS:IP`、20-bit 線性 RAM 與畫布座標分開記錄。
4. 追反白移動、點擊切換核取與 ESC 時，原版是否對受影響列**重新印字**；若有，記錄新事件的讀寫與底圖，作為日後重建權杖的依據；若沒有，記錄為永久撤銷條件。
5. 證據足夠才另立八列 DRAFT→READY 規格；正式 Ebitengine 接線與 CONFORMED 驗收留給後續目標。更新 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json` 與 Issue，私有推送並回讀。

## 停止線

本輪不宣稱八列正式中文。原版畫素、原始資料、字型與含原版畫素的截圖只留已忽略的 `workplace/`。
