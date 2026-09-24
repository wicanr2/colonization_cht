# 目標132：遊戲選項標題的當次事件與正式中文覆蓋

狀態：進行中；開始：2026-09-25。承接[目標131](131-game-options-title-a-runtime-gate.md)已驗的真 VGA 晚一幀同步與 ESC 失效、[規格027](../spec/027-game-options-window-draft.md)九欄 DRAFT，以及使用者確認的 A 字級。對應既有 [Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，不新增同義 Issue。

## 本輪玩家結果

沿 DOS 原版正常鍵鼠路徑開啟 `GAME → Game Options`，讓無快捷鍵標記的標題 `GAME.TXT:0x4CD` 以使用者已選的 A／34px 顯示「遊戲選項設定」，並在關窗、資料不符、字模缺失或游標遮擋時保留原文。八列仍不得以其 A 字級選擇取代各列輸出、快捷鍵與回退證據；本輪同時整理可共用的欄位閘門與八列後續工作，但不改原版遊戲規則、資料、存檔或輸入。

## 工作與退出條件

1. 核對乾淨工作樹、原版 SHA、隔離 dosgolem 禁推、私有遠端與 Issue；**先推送本目標和 `CONTEXT.md` 入口**再改探針或正式程式。所有分析、建置、測試、遊戲與抓圖限有界、非 root、預設無網路的 Docker；原版唯讀掛載。
2. 從固定開窗到 ESC 離頁，追標題當次 `0D21:00C6` 完整讀字、`0D21:012C` 原版畫布寫入、印前多色底圖及真 VGA 同步。雙冷啟動、無監看控制及負例檢查須區分檔案位移、實模式 `CS:IP`、20-bit 線性 RAM 和畫布座標；未閉合的中間搬運保持分級，不因同文或單張畫面猜事件。
3. 用現行 TSV 與固定 Cubic 11 字型重烘標題 A／34px；量實際墨跡、色號、陰影、基線與四倍安全矩形，建立缺鍵、重複鍵、缺字模、錯字級及溢出回退。只有標題的證據與 typed 契約達 READY，才另立限定規格授權正式 Ebitengine 覆蓋。
4. READY 後將標題接到正式視窗的預設關閉開關；逐幀檢查當次事件權杖、原版底層／VGA、色盤、模式、開檔與游標，不重用舊背景。以正常玩家鍵鼠中英同輸入，在出現、焦點／按鍵、ESC 離頁和反例各相位檢查原版完整狀態不變、新畫素只在標題安全區；既有正式欄位回歸不退步。完成才將限定標題規格標 CONFORMED，更新已授權的正式截圖；否則保留 DRAFT、原文與具體缺口。
5. 更新 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json`／生成的 `WORKLIST.md` 與相關 Issue；私有推送並回讀。收尾查權利邊界、原版素材未追蹤、輸出擁有權、Docker 容器與隔離副本禁推。

## 停止線

只驗標題不能宣稱九欄或全文中文化；八列 `~` 快捷鍵可見形式會改玩家資訊，未確認前不代選。原版畫素、原始資料、字型與含原版畫素的截圖只留已忽略的 `workplace/`，不因私有儲存庫而擴張公開權利。
