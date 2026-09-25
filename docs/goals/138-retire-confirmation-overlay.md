# 目標138：退休確認框三欄接正式 Ebitengine（A 版）

狀態：進行中；開始：2026-09-25。對應 [Issue #32](https://github.com/wicanr2/colonization_cht/issues/32)，承接[規格028（DRAFT）](../spec/028-retire-confirmation-overlay-draft.md)、[目標126](126-retire-confirmation-three-field-overlay.md)、[目標127](127-retire-source-to-print-dataflow.md)與使用者 2026-09-25 選定的 A 版（三欄 34px、共同置中）。

## 工作與退出條件

1. 以九欄事件探針記錄開框、滑過 Yes／No、移開、點 No 的讀字、改色、其他寫入者與畫布，雙冷啟動與無監看控制；判定三欄的事件結構、逐欄底圖、真 VGA 同步與互動時是否重印。
2. 依證據把規格028 升限定 READY：逐欄當次事件權杖、印前底圖、字模綁定、游標與按鍵回退、離框撤銷。
3. 正式前端接上預設關閉的旗標；錄製或現場輸入中英同輸入對拍（開框、Yes／No 兩分支）、負例、真 GUI 截圖與重播一致後標 CONFORMED；既有欄位回歸不退步。
4. 更新文件、worklist 與 #32，私有推送並回讀。

## 停止線

不改 Yes／No 熱區與結果；原版像素與截圖只留已忽略的 `workplace/`。
