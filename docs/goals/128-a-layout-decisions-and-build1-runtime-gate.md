# 目標128：定版兩處 A 字級，推進首張開場字幕的執行期守門

狀態：進行中；開始：2026-09-25。承接[目標106](106-build-opening-caption-overlay-gate.md)、[目標122](122-game-options-nine-field-state-guard.md)與[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)／[規格027](../spec/027-game-options-window-draft.md)。對應既有 [Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)、[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，不另開同義項目。

## 已確認的獨立視覺決定

- 首張開場字幕 `@BUILD1` 選 A：Cubic 11 字級 38px、實際墨跡高 35px，單行共同置中，保留原版淡黃字與暗影；排除 42px 的 B。只適用已驗的這一張字幕，不外推其餘九張。
- `Game Options` 視窗九欄選 A：標題 34px，八列依序 25／28／28／25／28／28／27／28px，較貼近各欄原版字高；排除較大的 B。這只是逐欄版面決定，不等於規格027已 READY，也不授權省略 `~` 快捷鍵資訊。
- 第一張國家旗卡的 A 版 21／25px 已由目標099驗收，不重做；退休框及第三張難度卡另有自己的待決版式，不受本輪選擇影響。

## 工作與退出條件

1. 核對 Git 身分、私有遠端、既有 Issue、合法原版與獨立 dosgolem；先推送本目標和目前脈絡，再執行工程。原版與字型唯讀；所有探針、測試及抓圖在限資源、無網路、非 root 的一次性 Docker 內。
2. 把兩處 A 字級及排除的 B 寫回各自 DRAFT 規格，訂正舊的「待使用者決定」文字；以既有逐像素對照為依據，檢查最長譯文、熱鍵資訊、字模、陰影和安全矩形。未驗條件照實保留。
3. 對 `@BUILD1` 建立狹窄的執行期原版輸出／頁相位守門證據：固定原版雜湊、當次英文印字、印前與印後畫布、色盤及離頁失效；同一路徑雙次冷啟動和無監看控制核對 CPU、完整 RAM、索引畫面、虛擬時間、開檔與輸入。觀測器不得改遊戲狀態。
4. 做獨立正反例：錯來源／錯版／缺譯／缺字模／畫布變動／離頁殘留均須保留原文或拒絕；缺合法原版須明確 `SKIP 77`。逐項審查規格026：只有限定 `@BUILD1` 的來源、相位、幾何及失敗模式皆閉合並升 READY 後，才接 Ebitengine 正式疊字；再經真視窗中英文同輸入、dosgolem 原版同狀態及既有十七段回歸，才能限定標為 CONFORMED。
5. 回填 `CONTEXT.md`、規格、研究與工作紀錄及唯一工作清單；私有推送並回讀既有 Issue。收尾核對未追蹤原版素材、UID/GID、誤建目錄與 Docker 容器清理。

## 停止線

本輪不修改原版 EXE／TXT、規則、存檔或玩家輸入，不公開原版像素／字型。字級選定不會自動補足來源鏈或逐幀守門；任一閘門不成立時交付可重播缺口與安全回退，不把兩處 DRAFT 冒稱正式中文。首則 help 仍只有預讀證據，不計顯示完成。
