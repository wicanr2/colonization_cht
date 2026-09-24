# 目標125：教學選項跨次啟動與首則 help 的正常玩家入口

狀態：完成（限固定跨次玩家路徑）；開始與完成：2026-09-25。承接[目標111](111-tutorial-hints-state-and-first-help.md)在海上切換 `Tutorial Hints` 後仍未見正文，以及[目標123](123-retire-confirmation-and-help-route.md)已證實 `Retire → Yes` 會正常離開 DOS。[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)仍 DRAFT，`@TUTORIAL1` 只證實預讀。對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，不建立重複 Issue。

## 玩家問題與已知界線

第一則原文提示船上載著拓荒者與士兵，可向西尋找陸地；語料已翻譯，卻尚未在原版玩家畫面出現。先前於開局後進入 `Game Options`，點 `Tutorial Hints` 再離頁，不足以證明選項會在下一局啟動前保留。`Retire → Yes` 不會在同一執行中返回主選單，因此本輪只測**正常退出後、下一次冷啟動**的持久性與可見結果，不把它冒充同局重開。

固定合法 DOS 輸入及檔案 SHA-256 依 `tools/check_goal101_nation_intro.py`、`tools/check_goal112_options_source.py` 與[目標123](123-retire-confirmation-and-help-route.md)；隔離 `workplace/dosgolem` 固定 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，其 `upstream` 推送位址 `DISABLED`。原版檔案位移、20-bit 線性 RAM、實模式 `CS:IP`、320×200 索引及四倍視窗座標分開記錄。

## 工作與退出條件

1. 核對乾淨工作樹、Git 作者、PRIVATE 遠端及既有 Issue；先將**本 goal Markdown 與 CONTEXT 入口推送**，再新增事件、探針或原版重播。所有搜尋、編譯、測試和執行限於無網路、限資源、非 root 的一次性 Docker；原始 DOS 輸入唯讀，可寫暫存層只在已忽略的 `workplace/`。先核對掛載來源及輸出擁有者。
2. 以已驗滑鼠與鍵盤路徑製作三個同狀態分支：未切換教學選項、點擊一次、點擊兩次；各自從英格蘭冷啟動抵達海上，再經真正 `Retire → Yes → 分數 → 名人堂 → DOS 正常結束`。只要有一支未正常退出，就記錄實際終點，不偽造跨次比較。
3. 三支各用獨立、目前使用者持有的 dosgolem `DOS.Scratch` 暫存層，原版 `Root` 始終唯讀；執行前逐檔核對原始雜湊，暫存層不入 Git。量測退出前後暫存層檔案清單與 SHA-256、原版開檔／寫入結果及跨次冷啟動的 `Game Options` 同焦點圖示狀態；清楚區分原版持久化與 dosgolem 尚未支援造成的結果。不得直接寫入使用者原始目錄或擅改原版設定檔。
4. 若玩家操作確實保留設定，在第二次正常開局尋找 `@TUTORIAL1` 的實際原版印字與畫面。若顯示，固定 `GAME.TXT` 原始片段、DOS 讀入、印字常式、畫布、安全矩形與變數值，再審查 READY 規格；沒有正式輸出與中文同狀態前不得增加正式中文段數。若未保留或未顯示，提供對照收據與下一個能由玩家介面驗證的入口，不反覆盲目送鍵。
5. 有結果的分支做雙次冷啟動、無讀寫監看控制與獨立正反例；原版缺失明確 `SKIP 77`。回填規格026、`RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md`、唯一 `docs/worklist.json`，重生 `WORKLIST.md`；私有 push、更新及回讀既有 Issue。收尾檢查原版／像素未入 Git、輸出 UID/GID、root-owned 誤建目錄和本輪 Docker 容器清理。

## 停止線

本輪先驗「玩家點選 → 原版正常退出 → 檔案差分 → 下次冷啟動畫面」這條鏈；單一檔案改動、核取像素或 `@TUTORIAL1` 預讀都不能單獨證明 help 已顯示。跨次檔案變更若影響存檔格式，僅觀測，不修改原版規則或正式前端。第三張難度卡、`Game Options` 與開場字幕的 A／B 字級仍待各自決定；不沿用第一張旗卡的 A 決定。正式中文目前十七段，help 正式顯示零則。

## 開工後的工具契約訂正

原稿的「原版實驗副本」會造成假陰性：固定版 dosgolem 預設只記寫入意圖、不落地，複製 `Root` 本身不能讓下次啟動讀到設定。已核對隔離版 `docs/spec/009-scratch-writes.md` 與 `internal/dos/files.go`，本輪改用上列每支獨立 `DOS.Scratch`；它先於唯讀 `Root` 解析已寫檔案。原稿保留在 Git 歷史，本節記錄修正理由，不把未啟用暫存層的實驗當作持久性證據。

## 驗收結果與下一入口

以原版唯讀 `Root` 與每支獨立 `DOS.Scratch`，英格蘭正常玩家路徑於 `Game Options` 未點／點一次／點兩次 `Tutorial Hints`，再各自 `Retire → Yes → 分數 → 名人堂 → DOS 正常退出`。三支在教學操作前同狀態；同焦點核取中心四點依序為色號47／149／47，確認一次點擊當局確實變更、兩次返回原狀。三支正常終止步數分別為1,601,103,496／1,601,103,503／1,626,215,180，所有玩家事件送達。

三支退出後暫存層都**只**有 `COLONY09.SAV`（23,847 bytes，SHA-256 `52bfd407b7c3b0a0cfce9362a0b352d1e7296b3ee85f715e4b904703064e3696`）與 `HALLFAME.DAT`（210 bytes，SHA-256 `886a85752b852d15ffdd1b689eb0c8c72b653c2e1f7a6af3f4b0844371a00838`），兩檔跨三支逐 byte 相同。以各自退出後暫存檔的**精確副本**第二次冷啟動，走同一正常玩家新局／打開選項路徑，三支1,400M完整 JSON 逐 byte 相同，SHA-256 `ec3a785c9e0faf0247a4928ac5cf3479ffa45177d1ed909afde97239e7d94049`；完整 RAM、原版索引／畫布／色盤、開檔與時間均合流，教學中心四點均回色號47。固定取樣與已監看的印字讀取仍未見首則 help；**只限這條退出後另開新局的玩家路徑**，不排除載入存檔、其他入口或檢查點間短暫畫面。

首輪與第二局每支各兩次獨立冷啟動、一次無讀寫監看控制；`tools/check_goal125_tutorial_persistence.py` 逐一核對固定原版／玩家事件 SHA、每個原版取樣實檔、完整控制狀態、DOS 終止及兩份暫存檔。正例、缺原版 `SKIP 77` 與錯版、改鍵、改 RAM／畫面／存檔、偽造終止及假合流等負例均通過。本機驗證摘要 SHA-256 `8ca851ecc6ce8816bcaddf2d2638e211ef53cfd8449a66aec7a40d1e4a2ef97e`；原版素材和收據僅在已忽略 `workplace/reports/goal125-help/`。未開 Scratch 的舊目標123 `Retire` 路徑用新探針重播，JSON SHA-256 仍為 `902d557aaf7f86d4fb913d4891e4c7e584f10963e8b0217e2afc8401bde20efa`，逐 byte 相同。

下一輪不再把 `Retire` 當設定後新局入口；應從原版玩家介面找另一條**能在提示預期相位啟用教學**的路徑，或先釐清原版在當局選項變動後有哪些實際可見觸發。`@TUTORIAL1` 仍僅有預讀與譯稿，規格026保持 DRAFT；正式中文十七段、help 正式顯示零則。
