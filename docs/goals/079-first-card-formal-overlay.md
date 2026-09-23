# 目標079：第一張難度卡片的正式輸出覆蓋

狀態：completed（僅第一張卡片兩行）；日期：2026-09-23。承接[規格016](../spec/016-difficulty-card-text-draft.md)、
[目標078](078-difficulty-card-runtime-guard.md)；對應 Issue
[#6](https://github.com/wicanr2/colonization_cht/issues/6)、
[#7](https://github.com/wicanr2/colonization_cht/issues/7)及
[#26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 範圍與證據閘門

只處理第一張難度卡片的 `DISCOVERER:`／`Easiest` 兩行；兩者分別由
`NAMES.TXT:0x00000C0C` 與 `LABELS.TXT:0x000008A9` 提供來源。先審核
固定版本、真實讀取／繪圖事件、格式化顯示鍵、譯稿唯一性、按欄量測的中文字級、
安全矩形、有紋理底圖、游標回退與缺譯處理。只有建立限定的 READY 契約後，
才准把可丟棄守門接進 `tools/live_menu.go` 的 Ebitengine 正常玩家路徑。

## 工作與退出條件

1. 用既有原版雙次收據及目標078的同狀態、滑鼠進出結果審查規格016；若證據不足，
   保持 DRAFT，明列缺口，不以原型代替正式實作。
2. 建立兩個來源鍵與格式化顯示事件的綁定，從真實 TSV 唯一譯文產生本機字模；
   缺鍵、重複、來源雜湊、譯文或字模不符時逐欄回退原文並記錄原因。字級按原版
   兩行各自的 5／6 邏輯像素墨跡量測，不沿用主選單的固定 24px。
3. 在隔離 dosgolem 的正式前端補入當次原版畫布擷取、原文差分、版本／事件／來源
   與索引畫面守門；游標遮住卡片、後續繪圖或場景切換時逐欄回退，不改原版 RAM、
   畫布、輸入、規則或存檔。
4. 重播同一批正常玩家輸入，對照中文、英文控制、缺譯與游標變體的原版
   CPU／RAM／索引畫面／色盤／虛擬時間；Ebitengine 輸出逐像素驗證差異只在
   各欄安全矩形。記錄已覆蓋幀、回退原因與本機截圖；不把含原版像素的圖加入 Git。
5. 更新規格、`CONTEXT.md`、研究與工作歷程及對應 Issue；私有儲存庫推送前
   檢查權利邊界、工作樹、Docker 容器與擁有權。

## 停止線

本目標不涵蓋其他難度卡片、靜態圖、help 或遊戲內玩法畫面；第一張卡片
完成也不能宣稱全文中文化。若正式前端的守門不具備足夠證據或測試未通過，
保留八段正式中文和規格016 DRAFT，回退原文並把缺口留在 Issue。

## 結果與退出判定

- [規格017](../spec/017-first-difficulty-card-overlay.md)完成限定 READY 審查及
  正式前端同狀態驗收，標為 CONFORMED；規格016對其餘卡片仍為 DRAFT。
  `tools/live_menu.go` 使用唯一來源鍵、固定原版版本、`0E2D:11CF` 真實讀取、
  `0D21:00C6` 格式化顯示位元組、當次有紋理底圖與精確原版像素差分守門；
  中文只合成至四倍輸出，不修改原版記憶體或畫布。
- 本機 `tools/bake_card_fonts.py` 由原始 TSV 與合法原版生成21px／25px逐欄字模。
  無頭正常路徑兩欄各有一次被接受事件與79個套用幀；與無觀測英文控制組
  的原版 CPU／完整 RAM／索引畫面／色盤／時間一致。
- 九筆真視窗輸入的 Ebitengine／Xvfb 中文、重播及英文控制組同狀態；
  `tools/verify_window_prototype.py` 核對新增兩欄只在各自安全矩形變更
  2,752／1,860點，其餘欄位與畫面不被卡片覆蓋改動。
- 真實 TSV 缺稱號鍵或同鍵重複時，稱號逐幀回退原文，副標仍中文；錯誤
  `NAMES.TXT` 指紋在啟動前被拒絕。游標進入卡片兩欄各回退25幀，移開後恢復。
  `tools/verify_goal079_replays.py` 驗證六組
  Ebitengine 受控重播、同輸入原版狀態與最終像素；收據只保留本機。
- 既有私有截圖 `docs/screenshots/difficulty-zh.png` 已換成這次真視窗驗證圖，
  不新增公開原版像素。使用者另指出「選擇難度」標題版式仍不合原版風格，
  已登記[Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)
  作下一階段；此視覺改善未冒充本目標的卡片覆蓋證據。
