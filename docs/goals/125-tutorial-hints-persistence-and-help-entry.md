# 目標125：教學選項跨次啟動與首則 help 的正常玩家入口

狀態：in_progress；開始：2026-09-25。承接[目標111](111-tutorial-hints-state-and-first-help.md)在海上切換 `Tutorial Hints` 後仍未見正文，以及[目標123](123-retire-confirmation-and-help-route.md)已證實 `Retire → Yes` 會正常離開 DOS。[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)仍 DRAFT，`@TUTORIAL1` 只證實預讀。對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，不建立重複 Issue。

## 玩家問題與已知界線

第一則原文提示船上載著拓荒者與士兵，可向西尋找陸地；語料已翻譯，卻尚未在原版玩家畫面出現。先前於開局後進入 `Game Options`，點 `Tutorial Hints` 再離頁，不足以證明選項會在下一局啟動前保留。`Retire → Yes` 不會在同一執行中返回主選單，因此本輪只測**正常退出後、下一次冷啟動**的持久性與可見結果，不把它冒充同局重開。

固定合法 DOS 輸入及檔案 SHA-256 依 `tools/check_goal101_nation_intro.py`、`tools/check_goal112_options_source.py` 與[目標123](123-retire-confirmation-and-help-route.md)；隔離 `workplace/dosgolem` 固定 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，其 `upstream` 推送位址 `DISABLED`。原版檔案位移、20-bit 線性 RAM、實模式 `CS:IP`、320×200 索引及四倍視窗座標分開記錄。

## 工作與退出條件

1. 核對乾淨工作樹、Git 作者、PRIVATE 遠端及既有 Issue；先將**本 goal Markdown 與 CONTEXT 入口推送**，再新增事件、探針或原版重播。所有搜尋、複製、編譯、測試和執行限於無網路、限資源、非 root 的一次性 Docker；原始 DOS 輸入唯讀，實驗副本只在已忽略的 `workplace/`。先核對掛載來源及輸出擁有者。
2. 以已驗滑鼠與鍵盤路徑製作三個同狀態分支：未切換教學選項、點擊一次、點擊兩次；各自從英格蘭冷啟動抵達海上，再經真正 `Retire → Yes → 分數 → 名人堂 → DOS 正常結束`。只要有一支未正常退出，就記錄實際終點，不偽造跨次比較。
3. 三支各用獨立、目前使用者持有的原版實驗副本；副本建立前逐檔核對原始雜湊，副本不入 Git。量測退出前後檔案清單與 SHA-256、原版開檔／寫入結果及跨次冷啟動的 `Game Options` 同焦點圖示狀態；清楚區分原版持久化與 dosgolem 尚未支援或副本只讀造成的結果。不得直接寫入使用者原始目錄或擅改原版設定檔。
4. 若玩家操作確實保留設定，在第二次正常開局尋找 `@TUTORIAL1` 的實際原版印字與畫面。若顯示，固定 `GAME.TXT` 原始片段、DOS 讀入、印字常式、畫布、安全矩形與變數值，再審查 READY 規格；沒有正式輸出與中文同狀態前不得增加正式中文段數。若未保留或未顯示，提供對照收據與下一個能由玩家介面驗證的入口，不反覆盲目送鍵。
5. 有結果的分支做雙次冷啟動、無讀寫監看控制與獨立正反例；原版缺失明確 `SKIP 77`。回填規格026、`RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md`、唯一 `docs/worklist.json`，重生 `WORKLIST.md`；私有 push、更新及回讀既有 Issue。收尾檢查原版／像素未入 Git、輸出 UID/GID、root-owned 誤建目錄和本輪 Docker 容器清理。

## 停止線

本輪先驗「玩家點選 → 原版正常退出 → 檔案差分 → 下次冷啟動畫面」這條鏈；單一檔案改動、核取像素或 `@TUTORIAL1` 預讀都不能單獨證明 help 已顯示。跨次檔案變更若影響存檔格式，僅觀測，不修改原版規則或正式前端。第三張難度卡、`Game Options` 與開場字幕的 A／B 字級仍待各自決定；不沿用第一張旗卡的 A 決定。正式中文目前十七段，help 正式顯示零則。
