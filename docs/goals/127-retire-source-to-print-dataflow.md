# 目標127：退休確認框來源至印字緩衝追證

狀態：進行中；開始：2026-09-25。承接[目標126](126-retire-confirmation-three-field-overlay.md)與[規格028（DRAFT）](../spec/028-retire-confirmation-overlay-draft.md)，對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)及[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)，不重複開單。

## 界線

第一張國家旗卡的 A 版（「英格蘭：」21px、「移民」25px）已由[目標099](099-first-nation-card-a-overlay.md)限定正式驗收；本輪不重做、不改正式截圖，也不把它外推到退休框。退休框的 A/B 版式仍待使用者另行選擇；本輪不代選、不接正式前端。

## 工作與退出條件

1. 核對乾淨工作樹、Git 身分、私有儲存庫、既有 Issue、合法原版、隔離 dosgolem 及其禁推設定；先推送本目標與目前脈絡入口，再執行工程。
2. 在原版只讀、無網路且限資源的 Docker 中，新增預設關閉的狹窄資料流觀測：固定 `GAME.TXT` 雜湊與三筆檔案位移，記錄 DOS 讀入後、`0D21:00C6` 印字前的候選 RAM 讀寫及原始 `CS:IP`。保留完整原始定位、步數、字節值及推論等級；觀測器不得修改遊戲 RAM、輸入、時間或畫布。
3. 用相同正常玩家輸入雙次冷啟動重播；以無監看控制核對 CPU、完整 RAM、索引畫面、色盤、虛擬時間與開檔。設獨立正反例，測試錯版原文、資料流缺口及觀測上限；缺合法原版回報 `SKIP 77`。探針預設關閉時要保持舊收據逐 byte 不變。
4. 只把真正閉合的來源邊標為「已證實」；若有間接搬運或相同短字串歧義，保留「強推論／未知」並說明下一個最小證據。不以檔案中出現 `Yes`／`No` 或 `@RETIRE` 預讀冒稱已顯示。
5. 更新規格028、研究與工作紀錄、目前脈絡及唯一工作清單，重生可讀工作表；私有推送並回讀既有 Issue。核對未追蹤原版素材、輸出 UID/GID、Docker 容器與 root-owned 誤建目錄。

## 停止線

本輪不修改原版 EXE、TXT、存檔、規則或點擊熱區，不公開原版像素／字型／畫面。若資料流只證到部分邊，交付有界證據，不把規格028升 READY；正式中文數仍十七段，help 正式顯示仍零則。
