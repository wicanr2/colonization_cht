# 目標126：退休確認框三欄繁中顯示

狀態：完成（限定原版證據與可丟棄 A/B 對照；正式版式待使用者決定）；開始與完成：2026-09-25。承接[目標123](123-retire-confirmation-and-help-route.md)已驗的正常玩家 `GAME → Retire` 確認框與 `Yes`／`No` 真滑鼠分支；[主譯稿](../../text/draft.zh-Hant.tsv)已有 `GAME.TXT:0x122` 問句、`0x141`「是」、`0x146`「否」三筆草稿。對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)及[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)，不新增重複 Issue。這是輸出畫面的轉譯層，不改原版遊戲規則、資料或存檔。

規格入口：[規格028（DRAFT）](../spec/028-retire-confirmation-overlay-draft.md)。

## 玩家價值與目前界線

正常玩家打開退休確認框時，三段關鍵文字仍是英文。既有收據錄到 `Do you really want to quit? Yes No` 與兩個實際有效的滑鼠分支，但先前沒有把三筆 `GAME.TXT` 來源、逐欄印字事件、原版墨跡、可逆底圖、安全矩形及中文大小接成正式覆蓋規格。正式中文目前十七段；原先的 21／25px 旗卡決定只適用第一張旗卡，不能外推到本框。

## 工作與退出條件

1. 核對乾淨工作樹、Git 身分、PRIVATE 遠端、既有 Issue、合法原版與隔離 dosgolem；**先推送本 goal Markdown 與 CONTEXT 入口**，再動探針或正式前端。所有搜尋、畫素分析、建置、測試、抓圖和原版執行只在無網路、限資源、非 root 的一次性 Docker；每個掛載來源先驗存在與形態，原版唯讀，收據只在已忽略 `workplace/`。
2. 以固定原版檔案雜湊，從 `GAME.TXT:0x122/0x141/0x146` 原始位元組對到 DOS 讀入、原版實模式印字讀取與可見畫布；逐項標明檔案位移、20-bit RAM、`CS:IP`、320×200 原版座標及推論等級。核對未點、Yes、No 三條正常玩家路徑；不足的中間搬運不得冒稱已證實。
3. 量測三欄原版字高、基線、原文筆畫、安全矩形與印前底圖。依每欄原版比例與四倍畫布選中文字級、內距及溢出／缺譯回退，檢查「確定要離開遊戲嗎？」、「是」、「否」的實際字模，不採全域固定 24px。若有實質版式取捨，先產生可丟棄對照供使用者決定，不擅自定案。
4. 先建立 DRAFT 規格；僅在原版事件、逐欄守門及版面證據足夠時審為限定 READY，才接正式 Ebitengine 覆蓋。正常玩家真視窗抓圖，與同輸入英文控制核對原版 CPU、完整 RAM、索引／色盤、時間及開檔；Yes／No 真點擊與未點、離頁、錯版、缺譯、重複鍵、缺字模、底圖／游標變化須失敗即關閉。若 gate 未閉合，只交付證據與原型，不增加正式中文段數。
5. 做雙次冷啟動、無監看控制及獨立正反例；缺合法原版明確 `SKIP 77`。回填規格、`RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md` 和唯一 `docs/worklist.json`，由工具重生 `WORKLIST.md`；私有推送並回讀既有 Issue。收尾核對原版素材未追蹤、輸出 UID/GID、root-owned 誤建目錄與 Docker 容器清理。

## 停止線

原版按鈕熱區與字樣墨跡不是同一幾何；中文只能蓋在安全文字區，不可改原版點擊或存檔。`GAME.TXT` 原文片段存在也不代表輸出事件已閉合；缺一段即保留原文並記錄命中。此框完成也不代表 `Tutorial Hints` 的 help 已顯示，規格026繼續 DRAFT，help 正式顯示仍零則。

## 本輪實際結果與後續決策

原版 `GAME.TXT` 三筆短句於正常玩家退休框前的 DOS 讀取及其後實際 `0D21:00C6` 印字均取得固定收據；逐欄首字前底圖與1,275M畫布改色分別441／64／54點，顏色、bbox及安全區見規格028。兩次冷啟動報告逐 byte 相同；無監看控制在四個晚期取樣的 CPU／完整 RAM／畫面／開檔同狀態。探針預設關閉時，舊目標123確認框 JSON 與歷史逐 byte 相同。

用固定 Cubic 11 製作兩套**本機 Ebitengine 可丟棄畫面**，並以獨立逐像素驗證器核對原版控制、三欄安全區外零差異、底圖恢復、前景／陰影；A 與 B 全部通過。A「問句34px共同置中、按鈕34px共同置中」；B「問句38px保留兩行左起點、按鈕34px貼近原版左起點」。本機檔案：[原文控制](../../workplace/reports/goal126-retire/prototype/retire-original.png)、[A 對照](../../workplace/reports/goal126-retire/prototype/retire-zh.png)、[B 對照](../../workplace/reports/goal126-retire/prototype-b/retire-zh.png)；這些檔案已被 Git 忽略，僅供同工作區審查，不把原版像素推上遠端。正例、缺原版 `SKIP 77`、錯版／改鍵／改字型／譯稿／原版畫布等負例通過。

**未完成且不冒稱正式：**A/B 的原版忠實度取捨仍待使用者選；`@RETIRE` 中間逐 byte 搬運、真視窗動態字模／游標／底圖回退、同輸入英文原版狀態及正式錯版負例尚未閉合。[規格028](../spec/028-retire-confirmation-overlay-draft.md)保持 DRAFT；正式中文仍十七段、help 正式顯示零則。建議 B，因其問句高35輸出像素接近原版9邏輯像素×4、且文字左起點保留原版排列；選擇 A 則版面更整齊但較不像原版。本輪不替使用者定案。
