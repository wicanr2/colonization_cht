# 目標178：ORDERS 停用項目、地圖殖民地名稱標籤與遮擋殘行（Issue #55 第二部分）

狀態：進行中；2026-09-30 開始。對應 [Issue #55](https://github.com/wicanr2/colonization_cht/issues/55)，承接[目標177](177-sea-menus-names.md)的移交。

2026-10-02 目前結論：整行暫藏、關框恢復、讀檔城名恢復及船隻 ORDERS 已限定 CONFORMED。六個同文 MENU 來源與 VIEW 補證保留；陸地十列及第一 Fortify28D 經 v79～v83 正常 GUI、四側完整狀態／存檔、來源、欄位量測、八種偽造拒絕及反向對照後限定 CONFORMED。矩陣42PASS，普查807已顯示／1001待接／89不可達，分母1897；移除陸地列後逐位元組恢復 v77。正式前端仍 v65，歷史失敗保留。Join Colony／Pillage 及其餘名稱／詞彙待驗，#55仍進行中。

本輪可重跑入口：`workplace/reports/goal178-orders/codex-audit/hide-save-gui-v55/replays.sh`及`check-hide55.py`；在驗證容器中設定原版唯讀目錄、Xvfb及同名環境參數後執行。正常GUI加四側重播已通過八個取樣點、七張完整GUI像素、缺圖集原文與五側初始存檔不變；摘要`normal-state-summary.json` SHA-256 `e719a34a40f487652a7ab5270c2f4662d3a3a6806061503338899a88bf761c3d`。原型／長流程失敗保留，限定範圍見規格032／038。

下一個窄觀測入口：本機 `codex-audit/load-map-diagnostic-v56/`，從v51完整來源派生，只記錄STRING:colony候選安全區與畫布／VGA的差異、墨跡差異及步數；逾時候選只保留觀測指標，不修改正常狀態機、原版或正式來源。使用v55相同正常讀檔輸入與同一COLONY03.SAV，重播完整79400000終點核對。這是DRAFT蒐證，不授權放寬畫布等值守門或增加正式等待時間。

下一個正常路徑驗證入口：本機 `codex-audit/load-map-move-v57/`與`load-map-move-v57.sh`，從v55讀檔操作器派生，讀回後用普通右方向鍵移船再截圖；驗證單位圖像離開標籤後既有候選是否能啟用。使用正式v51，原始存檔不改、不同步數不當同狀態，必須以該GUI新輸入重播核對。沒有新正式守門或版面猜補。

v57已完成五張正常GUI與五側／觀測側原版狀態驗證，六個共同取樣點相同，未改存檔。第一個完全等值畫格為53295000，晚於52800000候選撤銷；船右移後沒有新城名來源，正式版本仍英文。原型入口本機 `codex-audit/load-map-retain-prototype-v58/`，只為STRING:colony增加不繪製的待複製暫停階段；全部等值、來源／字模／新印字取代與模式切換守門不變。先以v57真GUI輸入及六個既有取樣核對，DRAFT階段不修改正式來源。

v58六點同狀態、延後完整才啟用、原型安全區及功能回歸均通過；規格038已補READY。本機正式乾淨建置入口 `codex-audit/load-map-final-build-v59/`，新正常主選單讀檔與普通右移GUI入口 `codex-audit/load-map-final-gui-v60/`及`load-map-final-gui-v60.sh`；與v57相同玩家路徑，但用新的實際GUI輸入及畫格驗收。重播／檢查器保留在相應目錄，不將原型或舊GUI改名為正式收據。

新v59對已CONFORMED暫藏流程的回歸入口為v55目錄中的`current59`收據、`current59-save/`及`check-hide59.py`，沿同一真GUI輸入及七個固定畫格核對；八個取樣的原版狀態及狀態欄完整像素相同。關閉報告選單後新增城名，所有差異只在原城名安全區；初次要求整張圖等於舊來源的失敗腳本保留為`check-hide59-initial.py`。不重新開啟使用者顯示決定。v60正式檢查入口為同目錄`check-map60.py`。

正式v60驗收：五張完整GUI像素、六個共同原版取樣點與五側CPU／RAM／VGA索引／色盤／輸入／開檔及存檔不變全通過；缺圖集回原文。51810000暫停、52635000完整同步後啟用，字串來源db319a63…、正式二進位57352fb0…；完整雜湊與限定CONFORMED見規格038。摘要`normal-state-summary.json`為cb996a30c7037c0d6259764eba63341c61fd17b3d42f841aeb7d79e5ae77bede。普查與矩陣數量不增加；尚未完整驗其他城名／局勢、#55不關閉。

## 2026-10-02：縮放及船隻選單來源續驗

目前普查#55三類共432列pending。VIEW的Zoom In／Zoom Out與MAPMENU地圖編輯器同文，既有active清單含兩列，但未能唯一歸屬；不能直接以英文相同提高完成數。ORDERS亦有Fortify兩列與Load Cargo等跨畫面同文，須以實際顯示項目及來源個別審查，不把整份原始ORDERS所有列都算已到達。

本輪正常短入口：本機`codex-audit/view-ship-gui-v61.sh`與`view-ship-gui-v61/`，由v60主選單正常讀COLONY03.SAV流程派生，開VIEW、以X縮小、以Z放大、再開船隻ORDERS；使用正式v59與當前圖集。擷取前後frame.step須一致，完整GUI／中英／缺圖集及存檔不變驗證後才採用。Zoom的來源審查以完整12列VIEW上下文及原始MENU.TXT為主，不以兩列孤立同文取代來源。這是蒐證，尚未新增正式來源映射、矩陣或普查完成數。

v61發現船隻ORDERS只有末三列中文，其餘仍英文；陸上單位舊收據不涵蓋這個分支。只讀觀測副本入口為本機`codex-audit/ship-read-diagnostic-v62/`，從v59正式來源快照加入85～87M步的段落收集診斷；同一正常GUI輸入重播，不改原版狀態或正式覆蓋行為。診斷、原文回退與原始來源定位確認後，才提出修正規格。

無墨跡快捷鍵前綴DRAFT及排版審查見規格036；可丟棄原型入口`codex-audit/ship-prefix-prototype-v63/`。它增加暫留前綴及收尾幾何守門，只重播v61實際輸入，並保留原始字元與墨跡診斷。正式來源維持v59。

v63十四列已中文，但關框殘留；不算通過。後續可丟棄原型入口`codex-audit/ship-prefix-prototype-v64/`，只對新暫留前綴的段落要求已記錄文字點完整存活，記錄每列原版字形／顏色及收尾抹除點數。v63收據保留，不覆寫或改名。

v64原型通過完整狀態／關框無殘影與實際欄位量測，規格036補READY。正式乾淨建置入口`codex-audit/ship-prefix-final-build-v65/`；新正常GUI入口`codex-audit/ship-prefix-final-gui-v66.sh`及`ship-prefix-final-gui-v66/`。沿v61正常玩家操作重生，不將原型畫面改名當正式收據。檢查器、重播與量測腳本保留在各自忽略目錄內。

正式檢查入口[tools/check_goal178_ship.py](../../tools/check_goal178_ship.py)，以`--game`、`--reports`指向v66、`--layout`指向v64的固定雜湊量測。只回報實際驗過的船隻清單欄位，正常GUI逐像素、中英原版完整狀態、缺圖集與關閉恢復都須通過；同文來源不自動新增映射。

矩陣及普查候選入口為本機`codex-audit/ship-matrix-v67/`與`ship-census-v67/`；只採檢查器已驗清單欄位，保留相同英文的歧義，不以整份選單模板鍵取代逐列來源。反向檢查與摘要保留在v66，不增加其他VIEW或海上詞彙完成數。

首次普查候選為800已顯示，但三個未歸類診斷被拒絕，尚未發布。DRAFT觀測限制原型在v67的`prototype-text-census.py`、`prototype-all/`與`prototype-without-ship/`；檢查新來源移除後原有分母、完成狀態與來源列是否保持，查清之前不新增分類樣式或原始來源映射。

## 範圍

1. ORDERS 選單停用（灰色）項目：段內連續字串（[規格036 附記](../spec/036-line-list-and-centered-text.md)）與行色層，使上半段可用項目與停用項目都顯示中文。
2. 地圖上的殖民地名稱標籤：取證印字常式，再決定機制與版式。
3. 教學框壓住狀態欄時，被蓋住超過七成或在教學框出現前幾秒改印過的行仍為原文；來源恢復遵循 [規格032附記](../spec/032-sea-menu-and-status-draft.md)。

## 退出條件

普查中本範圍的「已到達但仍是英文」清零（`MENU.TXT:@ORDERS:0x000002D5`、`0x000002FF` 及地圖名稱標籤）；真 GUI、中英同輸入與反向對照；目標165～177 的既有路徑重播回歸不退步；驗證矩陣新增一列並全 PASS。

## 接手時的歷史結果

- 已接手審查 Claude 的未提交修改；`tools/live_menu.go`、對話框、字串與視窗來源和既有 `window-src` 副本逐位元組相同。
- ORDERS 與英國 Jamestown 地圖標籤：`tools/check_goal178_window.py` PASS；真 GUI 輸入 SHA-256 `e733d34f9a3fde277c0979888f3b07c229c9f94076e65db453d2d5282584d7a1`，中英原版終點記憶體 SHA-256 `6d330f414fbf778be459727806e537c8c00d9898e19c5143a371b6cb052a8fa0`。最新保守檢查為 ORDERS 四張、地圖標籤 35 張，符合 GUI／重播安全區相同與中英文輸出不同；原先的 36 張含完全被教學框遮住的 `answer-20`，當時的差異來自中文教學框，已排除。
- 接手重跑驗證矩陣 PASS 27；普查已顯示中文 409、待接 1,149、無法正常觸發 96。這是既有收據檢查，不能外推成全旗標／全畫面已驗收。
- 前端 `go vet`／`go test` 通過；`tools/build_window_prototype.py` 的來源守門雜湊已更新到經審查的 `25a91067d94f22be59fb23325c75c76aea3b055c0f936e56d62f5ad6d5e3a481`，乾淨重建成功。正式來源保留舊定位，新增最低取代資格、讀取位址索引與遮擋後來源恢復。
- 封裝準備：啟動器補齊對話框、字串及音訊參數，來源補齊 13 份 TSV、兩份圖集與 ymfm 授權；`tools/rebake_release_fonts.sh` 以正式字型工具鏈重烘 22 份過期綁定字模，像素與幾何和目標157逐位元組相同。
- 單字元誤撤銷：教學框的 `y`／`c`／`h` 被誤當狀態欄改印，導致森林、道路及 `With:` 覆蓋撤銷；先寫規格038 READY，再修正最低兩個字母的取代資格。`codex-audit/occlusion-regression/` 的完整既有輸入重播通過，森林英文殘字消失；原版 RAM／索引／色盤不變，畫面差異只在狀態欄。此重播只啟用受影響文字層，完整旗標回歸另驗。
- 遮擋後來源恢復：先由可丟棄原型取得完整恢復證據，再將規格032附記升 READY 並實作。暫停行不繪製，只有完整原版墨跡恢復才重新作用；不降低三成門檻。當前來源 `recovery-178` 的 68 個原版檢查點與既有控制相同，45 個中文畫面差異只在狀態欄；ORDERS 四張與地圖標籤 35 張仍和原 GUI 安全區相同。新來源 `recovery-gui` 真 GUI、中英與負例重播已完成，終點 RAM 相同；檢查器在 `intent-36` 地圖標籤安全區拒絕 141 個像素差異。差異涉及藍色水面與文字邊緣背景混合，仍待釐清擷取時點，未升此項為 CONFORMED。
- 大河：`fullflags-river-167` 補取 1,060M 檢查點，來源 `0D21:00C6`、譯文「（大河）」、22px 與原版狀態都通過補充檢查；新增檢查點未與真 GUI 圖核對，不據此提高普查完成數。重跑入口：`tools/check_goal178_window.py --game /game --reports /repo/workplace/reports/goal178-orders --river-reports /repo/workplace/reports/goal178-orders/fullflags-river-167 --tutorial-reports /repo/workplace/reports/goal167-tutorial`。
- 新 GUI 逐張診斷：53 張狀態欄與當前中文重播逐像素相同且與英文控制不同，包含遮擋後還原畫面；地圖標籤 34 張相同、1 張未對齊。規格032只將來源恢復功能升限定 CONFORMED，目標178的整體驗收仍未通過。
- **尚未達退出條件：**低於三成墨跡的遮擋殘字尚未完成驗收，其他名稱／特定局勢仍未完成普查驗收，#55 保持進行中。不得因新增矩陣列 PASS 將本目標或全中文化標為完成。

接手摘要與本機封包啟動收據：`workplace/reports/goal178-orders/codex-audit/`。正式字模入口為 [font/README.md](../../font/README.md)；畫面檢查／Go 工具鏈入口為 [tools/Dockerfile.verification](../../tools/Dockerfile.verification)。

## 2026-10-01：整行暫藏決定後的現行來源審查

使用者已明確選定整行暫藏、關框恢復，排除框外片段；決定與續驗DRAFT見規格032。舊並列原型的實際來源目錄為本機 `codex-audit/hide-prototype-v4-src/`／`clip-prototype-v4-src/`，收據前綴仍為hide-prototype-v4／clip-prototype-v4；不把前綴當成目錄。選定原型適配器400ee620a3a46487d9e1d97671a7192261f728161ab33ac564da952dac41a58c只作取捨來源。

現行來源可丟棄續驗入口為本機 `codex-audit/hide-current-v50/`，從目標181的load-final-build-v42組裝來源派生，只擷取舊原型的海上完整行墨跡、未變英文清除與字串層所有權區塊；保留新讀檔檔名守門、棄城名稱回呼與候選抹除生命週期，不能整份覆寫舊原型。先以原本正常GUI輸入及795800000／993200000／1005000000三個取樣點、1210000000完整終點核對，證據審查升READY前不改正式來源。此原型仍不取代新的正常GUI驗收或intent-36地圖差異修正。

正式續驗入口：本機 `codex-audit/hide-formal-build-v51/` 由正式組裝器乾淨重建並執行全部Go測試；`codex-audit/hide-gui-v52/` 以 `tools/probe_goal178_gui.sh` 使用最新對話框與字串圖集走正常GUI，再以同輸入重播核對。以上名稱沿用既有工作中間物職責，不作發行目錄。

獨立擷取時點驗證入口：`codex-audit/map-frame-timing-v53/`。舊recovery-gui的intent-36記下更新步數1113000000；事先依該GUI的frames紀錄固定最近畫面步數1112925001，而非重播原先選到的1113090001。保存原收據，僅新增此固定步數重播；若像素仍不同，維持原拒絕，不再挑鄰近畫格。這是擷取時點假說驗證，不是新增已中文來源。

2026-10-01擷取勘誤：固定1112925001步重跑後，舊intent-36標籤安全區141點差異清零，完整原版終點與舊英文控制相同；整張變化只在新遮擋策略的右側狀態欄。此證據分類為擷取腳本錯配，不是原版或譯文缺陷。原失敗收據保留。

驗證腳本 `tools/gui_auto.py` 的擷取步數改取狀態檔中 `frame.step`，而非更新步數；擷取前後須為相同畫面來源，變更時保留嘗試並重取，最多八次，不按像素結果選圖。輸入操作與正常玩家路徑不變。修正後正常GUI入口 `codex-audit/hide-frame-gui-v54/`，仍使用已重建的正式hide-formal-build-v51與最新圖集；後續嚴格原檢查器不改門檻、不採舊收據步數重命名。

四側長重播v52退出124，只有英文控制及缺圖集已生成完整收據；中文與舊來源的部分取樣保留，不算完整通過。v54在922M以143退出，最後擷取嘗試均來源穩定、未記錄產品例外；沒有完整輸入或終點收據，退出原因保留未定位，不誤記成產品缺陷。

最小充分續驗改用既有正常生成COLONY03.SAV（v41，d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77），冷啟動主選單第四欄正常讀回，開關REPORTS與COLONIZOPEDIA選單取遮擋／恢復，沒有快照、記憶體或旗標注入。入口 `codex-audit/hide-save-v55.sh`，收據 `codex-audit/hide-save-gui-v55/`；共享實際畫面擷取函式 `tools/gui_auto.py:capture_frame`，中文、英文、缺圖集與舊來源再用同一正常輸入重播。長開場不再作本小項的必要重跑成本，舊冷啟動完整GUI及兩側終點證據仍保留。

2026-10-02短GUI已正常關閉；hide-save-gui-v55開關REPORTS／COLONIZOPEDIA，百科選單遮住季節／金錢行時整行暫藏，關閉後恢復。讀檔後地圖名稱的大字仍英文，是新發現的未驗分支；不由冷啟動建城標籤驗收外推。四側順序重播入口 `hide-save-gui-v55/replays.sh`，避免前批同時長工作重跑。
## 2026-10-02：船隻普查範圍審查

`ship-census-v67/` 的第一個限制原型移除了兩筆既有 EXE 列，拒絕採用；`prototype-known-scope-census.py` 保留列數，但移除兩筆既有未套用觀測，也拒絕採用。第三個 `prototype-source-scope-census.py` 同時保留已分類來源與其他已驗文字，`source-without-ship/census.tsv` 與舊清冊逐位元組相同；`source-all/` 只新增五列已顯示中文。三個原型與失敗明細保留，不覆寫歷史證據。

正式普查與反向檢查入口為本機 `codex-audit/ship-census-v68/`；正式矩陣為 `codex-audit/ship-matrix-v67/`，41 列全部 PASS。規格036已先升普查範圍 READY；未驗片段留在私有明細，不新增人工分類或來源映射。

正式 v68 普查及 `tools/check_goal173_census.py` 通過；清冊800已顯示／1008待接／89不可達。五個新增來源與三筆私有未驗片段見 `ship-census-v68/audit-summary.json`、`detail.json`；41列矩陣全部PASS。船隻顯示與關框恢復限定CONFORMED，#55其餘來源保持進行中。
## 2026-10-02：同文來源補證 DRAFT

下一個唯觀測入口為本機 `codex-audit/menu-source-query-v69/`。沿 v66 已驗正常GUI輸入重播到相同完整終點，以既有 `0E2D:0832` 原始字串比較觀測方法記錄標記、RAM參數、返回位址及MENU檔案讀取。此位置是否服務預載選單仍待確認，不以未命中斷言原版沒有查詢。

只解開實際顯示船隻ORDERS與VIEW的同文來源，不改遊戲、譯文或正式覆蓋。原始觀測與輸入留在workplace，先核對完整原版記憶體及存檔；沒有來源鏈證據時維持pending，不新增人工映射。
唯觀測續證入口 `codex-audit/menu-copy-provenance-v70/`：v69確認MENU在43M附近預載，完整原版終點與v66逐位元組相同。v70記錄已審查讀行指令`0E2D:09F4`的原始讀取／目的RAM，及文字工作緩衝區寫入前的有限讀取脈絡；用於追查預載列到十四行ORDERS與VIEW的搬運。這是DRAFT觀測，不授權正式來源別名。
v70原版終點相同，但讀取掛鉤被後註冊者覆蓋，缺少的紀錄不能作資料流證據。修正觀測入口 `codex-audit/menu-copy-provenance-v71/` 合併單一讀取掛鉤，寫入只取`0E2D:11A5`／`11A9`字串搬運指令；舊失敗觀測保留壓縮副本與SHA-256。仍為DRAFT，不修改dosgolem或正式覆蓋。
v71確認兩個同文Fortify實際位於不同的預載RAM位置，讀行順序也不同；工作緩衝區只含格式化後單字元，不能靠它直接反查來源。下一個最小觀測 `codex-audit/menu-row-provenance-v72/` 追蹤MENU載入期間的字串寫入與正常GUI期間的預載列讀取，保留原始RAM位置，不推定鏈結欄位語意。
v72限定證據：MENU兩個Fortify分別寫入RAM473104與473135，本船隻路徑只將第二列送入字元讀取。停用列由預載字串整串複製，可用列經`9CD1:01AC`／`01F2`逐字讀取。續證入口 `codex-audit/menu-glyph-provenance-v73/` 將兩條搬運路徑與`0D21:00C6`實際印字讀取逐字連接，並保留一個Fortify字元的有限指令trace。驗證前不提高普查完成數。
v73來源檢查拒絕Load Cargo兩個字元，原因為`WatchWrites`只通知值改變的寫入：它們與前一列相同，觀測留下前一列來源。現有逐次寫入API位於 `workplace/dosgolem/internal/machine/probe.go` 的`WatchWrite`，相同值寫入也會通知。續證 `codex-audit/menu-glyph-provenance-v74/` 只替換唯觀測掛鉤，沿相同輸入與完整終點重跑，不保留猜測性的來源標籤。
正式補證準備與VIEW欄位量測入口 `codex-audit/menu-source-layout-v75/`。v74來源原型已通過六個選單列的查詢、載入、印字與正常GUI核對；VIEW另量得十二個文字帶，各列首個大寫字高5。原版一像素分隔線只作版面證據，不誤算成文字列。v75以v65未修改的正式來源及固定圖集量測候選字級、基線、最長譯文與安全矩形，不外推字級到其他欄位。

## MENU 來源限定正式驗證入口（2026-10-02）

規格036已審 READY；`tools/check_goal178_menu_sources.py` 讀取 v74 原始查詢／搬運收據與 v75 VIEW 排版量測，重跑 v66 正常 GUI、中英／缺圖集／存檔同狀態。只授權四個 ORDERS 與兩個 VIEW 原始來源，不將其他同文列算完成。`menu-source-formal-v76/` 保存正式檢查、偽造拒絕及矩陣；`menu-source-census-v77/` 保存正式普查、移除來源授權反向對照與重產結果。兩個目錄均在已忽略的 workplace，不納入原版文字或像素的公開交付。

## 陸地單位 MENU 待驗來源的正常短入口

`codex-audit/land-orders-gui-v78.sh`／`land-orders-gui-v78/` 沿 v66 操作器，由主選單第一欄正常讀取已有 COLONY00.SAV，再點選陸地拓荒者及 ORDERS，擷取開關選單。存檔 SHA-256 `cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e`；原始存檔唯讀，工作副本只讓原版正常讀取。使用未修改的 v65 正式前端與當前圖集，沒有記憶體、座標狀態或旗標注入。此為後續 Fortify 第一列／Join Colony／Pillage 的正常入口探勘，尚未有完整同狀態、來源及排版證據，不提高完成數，也不推定三列均會出現。

## MENU 六列來源限定 CONFORMED（2026-10-02）

v76 全部41列矩陣 PASS，沒有 SKIP／FAIL／過期／原版輸入衝突。`source-check.json` 核對四個 ORDERS 與兩個 VIEW 來源，`negative-checks.json` 的正例副本通過，偽造 MENU 查詢、搬運、印字來源、完整記憶體、GUI 輸入及字級均拒絕，缺原版 SKIP77。v77 `audit-summary.json` 只新增上述六列 shown，其他五個 MENU 列仍 pending；改動欄位安全區、原文或移除 active 後不採來源授權。正式普查兩次重產一致、BUY／可支付／棄城反向對照與分類缺漏／重疊拒絕通過；移除本次欄位授權後與 v68 清冊逐位元組相同。詳細原始定位與字級見規格036，原版資料未修改。

重跑來源檢查器的參數由 `tools/verification-matrix.json` 的 `ship-orders-prefix-close.args` 保存；在驗證容器內使用唯讀原版 `/game`、儲存庫 `/repo`、隔離 dosgolem `/dosgolem`，依該列參數執行 `tools/check_goal178_menu_sources.py`；`menu-source-formal-v76/verify.py` 保存當次驗證步驟，不能在原收據目錄覆寫重跑。v74 `probe.go` 的重生方式為該目錄 `go.mod`／`go.sum` 與 `inputs.json`，以 Go 1.26.7、`GOWORK=off GOPROXY=off GOTOOLCHAIN=local` 執行 `go run . --root /game --inputs inputs.json --out source-query.log --from 0 --to 98800000 --verify-step 98800000 --marker-prefix @ --scratch scratch`。scratch 僅含正常 COLONY03 工作副本，不能寫原版目錄。來源觀測與排版重生輸出必須留在 workplace，未覆蓋歷史失敗收據。

正式清冊 SHA-256 `08d201bd8c4f583284e5184e45101e3e062a2e8e2bf6461f45fcd610a1154bcf`，報表 `e86fba4f4e738e159a87dd5881fcc690d4e78eea885fcbaa9f638e2477f5ba32`，矩陣 JSON `087979294633d5c5a2069012bd872cfae22eb849f3169d163befc093175d4647`。#55 仍 OPEN；此驗收不涵蓋其餘名稱、陸地命令或百科入口。

### v78 正常入口勘誤與 v79

v78正常結束於71400000步，輸入SHA-256 `be95969f3ae2b664d28a94f1ade6b1bbc66d3fabbf581be03b3676340bb7155b`，COLONY00工作副本未改。實際點到的陸地單位為士兵，觸發原版士兵教學框；下一個ORDERS點擊關閉教學框，沒有開出選單。先前操作器意圖寫拓荒者，不能作實際單位或選單命中的證據。保留v78，沒有提高普查完成數。

`codex-audit/land-orders-gui-v79.sh`／`land-orders-gui-v79/` 沿相同正常讀檔與選取士兵操作，先正常Enter關閉教學框、擷取確認，再開ORDERS及關閉。原版輸入、前端與存檔未注入；依畫面與原版事件確認命中後才補來源及排版證據。

### v79 實際命中與同狀態／來源續證入口

v79正常主選單讀COLONY00、點士兵、Enter關教學框後已開出十列ORDERS並正常關閉。GUI輸入SHA-256 `2bfc26e7fe9895a3a11dfca9e3135bf6e54119543a441dca5bb7e2bf9cd6d95c`，終點77000000步RAM `48a1f5bc8e64ea9997df00139d0ec3533780ca60e635ec174a6bed2474e2858b`。實際清單包含Fortify，沒有Join Colony與Pillage；不能由原始MENU內有這兩行就算命中。來源仍須區分兩個同文Fortify。

`land-orders-gui-v79/replays.sh` 從正式 v66 重播器派生，改用同名 COLONY00 工作副本，依七張實際GUI畫格與77000000完整終點重跑中英／缺圖集；沿未改的v65正式前端。`codex-audit/land-menu-source-v80/` 保留v74逐次寫入探針、v79實際輸入與唯讀正常存檔來源，觀測同一MENU查詢／讀行／搬運／印字契約。觀測窗沿既有已證據的位置，缺紀錄時仍拒絕，不猜補原始來源；正式同狀態及來源驗證前不接入矩陣或普查。

### 陸地十列欄位獨立量測 DRAFT

`codex-audit/land-menu-layout-v81/` 使用v79十列實際事件與69465000步原版索引量測，不沿用船隻或VIEW的安全區。逐欄重跑未改v65正式排版、字級候選、最長譯文及正常GUI／中英／缺圖集與存檔同狀態。v80 `source-audit.json`另核對第一個Fortify的原檔位移28D、逐列讀取／預載搬運／印字與完整原版終點。這是下一個來源的DRAFT補證；在規格READY、正式獨立檢查器與矩陣／普查驗收前，806完成數不變。

### v81 證據審查與下次正式入口

v81 `audit-summary.json` PASS_DRAFT，七張GUI逐像素、四側完整原版及存檔不變通過；v80第一Fortify來源確認為28D／線性RAM473104，並非船隻的299。陸地十列安全區[80,12,159,125]、316×452輸出，21px墨跡19、22px墨跡21超高，最長advance252、完整墨跡[5,4,253,440]通過；兩個停用列層為原版色8。規格036已補DRAFT→READY，沒有改正式來源、矩陣或普查。

後續先為此獨立正常GUI新增檢查器及矩陣列，只授權28D來源。原始輸入／完整終點與v66船隻不同，不能把陸地欄位混入船隻列；缺原版／來源／GUI／灰色與完整狀態負例須通過。再重跑全部矩陣、普查與移除新列反向對照，預期只增加一個完成數；尚未完成前官方仍為806。Join Colony、Pillage及百科其他／完整入口仍無正常命中，不猜為不可達。

## 陸地十列正式驗證入口（2026-10-02）

規格036已審READY；[tools/check_goal178_land.py](../../tools/check_goal178_land.py)獨立驗證v79正常GUI及三側重播，v80查詢／搬運／印字與v81欄位量測。只授權第一Fortify原始來源28D，矩陣另立land-orders-source列，不混綁船隻輸入。既有MENU逐列來源檢查抽為同檔共用函式，原條件不改，需重跑船隻／VIEW正例以確認沒有回歸。`codex-audit/land-menu-formal-v82/`保存正式正例、來源／GUI／灰色／完整狀態拒絕與矩陣；`land-menu-census-v83/`保存只新增一列及移除本矩陣列反向對照。來源資料與像素只留workplace。

### 正式檢查器路徑負例勘誤

v82第一次錯灰色負例未被拒絕：測試副本的GUI與重播圖片皆已改錯，但檢查器讀取收據JSON中的舊絕對路徑，仍看到原目錄的正確灰色。此為驗證器缺陷，正式GUI／重播素材未改。失敗副本與wrong-gray.log保留於v82；不是產品驗收通過。

共用圖片解析改由指定收據目錄、前綴及檢查點標籤定位，要求標籤與步數及basename相符；不由JSON的任意絕對路徑取圖。船隻／VIEW及陸地檢查器均採相同定位。`land-menu-formal-v82/retry-v1/`保留修正後的完整正例與全部負例，必須再次通過船隻輸出相同及全部矩陣。沒有改原版、圖集或正式前端。

## Join Colony 正常入口探勘

`codex-audit/colony-orders-gui-v84.sh`／`colony-orders-gui-v84/` 沿目標181已驗equip-two-v49正常主選單第四欄讀COLONY03、進城、點居民／更多／士兵，原版將50火槍裝給士兵。再用原版關閉按鈕回到世界並開ORDERS，核對實際選中的單位與清單。保留原正常存檔SHA-256 d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77，不注入單位或改存檔；工作副本允許原版操作。

前端為未改v65，圖集沿目標180／181。舊v49操作器的擷取換為已驗capture_frame，須前後frame.step相同。此為Join Colony／Pillage缺口的可重播玩家路徑探勘，不推定退出城市後會選中士兵或兩個命令均會出現；GUI／來源／同狀態驗收前不增加完成數。

### v84 實際結果與正常下一單位入口

v84在99200000步正常結束，輸入SHA-256 `9d89c18044a724b7d0622e3a019ca16465e624e0799e9c576a533da150e18926`，原始COLONY03工作副本不變。裝備後已回世界，但右側及十四列ORDERS均為船隻，沒有Join Colony；退出城市不等於已選中新士兵。原版畫面與輸入保留，尚未提高完成數。

`codex-audit/colony-orders-gui-v85.sh`／`colony-orders-gui-v85/` 沿同一正常讀檔、裝備與退出路徑，再用Space執行原版下一單位並取樣，再開關ORDERS。依新畫面與原始事件判定實際選取單位，不假定Space必然選到士兵，也不注入單位狀態。Join Colony／Pillage仍需正常命中與來源／GUI／同狀態證據。

## 陸地正式驗收與807列清冊（2026-10-02）

`land-menu-formal-v82/retry-v1/negative-checks.json` PASS，八種偽造均拒絕，缺原版 SKIP77，船隻／VIEW 回報與 v76 相同；全部42列矩陣 PASS。最初錯灰色讀到舊路徑的失敗收據保留，不當作通過。正式前端及圖集未修改，規格036限定 CONFORMED。

`land-menu-census-v83/audit-summary.json` PASS，只新增 `MENU.TXT:@ORDERS:0x0000028D`。移除陸地矩陣列後，v77 清冊逐位元組恢復；普查重產及 BUY／棄城／分類反向對照通過。正式 TSV SHA-256 `0b06da990bda2ef03ebe04116d986475516d3ba5d1b86deebef989bec2d93521`，報表 `5a97e29f02723cca038e3b670634842d68493f4b3530ceaa4442ee4ff8f2645d`；矩陣 JSON `fe945ec647ee0da69c1de5bfe33a9d9932c67cebd8e49227f4506f523baac17e`、報表 `d2dd9987230a4e1a6b7c31c27fbaddee0766b0277a3385278e78c733f33b5879`。私有診斷增為四筆，新增十列整段組合不當作新來源或完成數。

重生入口為 v82 `verify-retry.py` 與 v83 `check-census.py`，容器掛載與 Go／原版版本沿本目標既有契約。重跑須另選輸出目錄，不覆寫已驗收據。正式欄位與參數保存於 `tools/verification-matrix.json` 的 `land-orders-source`；公開檢查器不含原版像素或完整原始字串副本。

### v85實際結果與唯觀測輸入補證

v85 Space 已記錄於83400000步，但89925000步及後續仍為船隻，ORDERS未開出；沒有 Join Colony／Pillage 命中。終點104400000步 RAM `d3f5d7264809a3efcbf73adcfa7e300a82fd8e596ae8af7b1fab52775d13fc9f`，輸入 `47e26088de653780a87b83530e043e009ae2cac17c830e14c268cac85c6754e5`，COLONY03工作副本不變。這只說明此時畫面與清單結果，原版所處輸入模式尚未定位，不判定鍵盤故障或命令不可達。

`codex-audit/colony-input-observe-v86/` 沿 v85 原始輸入／存檔及完整終點，以 dosgolem 既有 KeyReads 唯觀測 API 保存 BIOS 鍵字、原始 CS:IP、兩層呼叫者及步數，核對 Space 是否被讀取。使用現有 Go 探針及隔離 dosgolem，不修改原版、正式前端或工具核心。觀測結果與完整原版雜湊一致才採用；原始位址只作定位，不猜名稱與玩法。

### v86鍵字消耗與v87正常模式入口

v86 `input-observe-retry.log.keys.json` 與v85輸入／104400000步完整RAM相同，Space鍵字0x3920於83514144步由BIOS讀取，原始CS:IP 0BF7:001D、兩層呼叫者121D:1554，COLONY03工作副本未改。confirmed僅限實際讀鍵，不推定該呼叫者用途或單位規則。初次匯出整個CPU因循環參照失敗，改保存數值欄位後同條件重跑；不是原版執行失敗。

`codex-audit/colony-orders-gui-v87.sh`／`colony-orders-gui-v87/` 沿v84正常裝備回世界，再循已驗目標181 v29的檢視／Home／Enter進入移動棋子模式，然後Space查看下一單位，取樣後正常Enter及開關ORDERS。實際模式、教學框與清單以畫面確認，不由腳本意圖判定。原版、正式前端及存檔未注入；沒有命中及同狀態／來源／排版證據前不提高普查。

### Space意圖勘誤與正常駐軍入口

v87實際開出VIEW、正常Home／Enter離選單，但後續仍選船，沒有Join Colony或ORDERS命中。完整125200000步RAM 4822c9fb450f052a5827e489111c555a982c80c31928a6f68bf2254c6b285974，輸入 fae0d34a33351c4aece7e800c89d66bda9893c49d356b87344d36fe78d37fe68；工作副本不變。v84～v87的實際圖與輸入保留，不提高完成數。

第三波說明書Image020.jpg第24頁明列Space為Skip Movement、W為Wait For Next Unit；Activate Unit段落說駐軍須在殖民地顯示框選取。Image060.jpg第105頁的鍵盤表一致。先前把Space意圖寫為下一單位有誤，BIOS已讀0x3920的觀測不變，不作鍵盤失效證據。兩張本機來源SHA-256依序 `3d080272b44ed97a0a74293be5f91476e168e033123791dbbfd6c4a297b1c0e3`、`37e000a07fd4f0f8217fef3004eef19d63b3312040e733b08a2c69939598e48f`，原始掃描不新增公開副本。

`codex-audit/colony-orders-gui-v88.sh`／`colony-orders-gui-v88/` 沿正常讀COLONY03及裝備路徑，取樣後以城市畫面實際駐軍圖示執行正常選取，再回世界確認。操作器在每個觀察點暫停前端擁有程序，讓操作者根據真GUI圖選擇下一個正常動作；外層300秒限制、trap恢復並關閉擁有程序及Xvfb。暫停只固定擷取／輸入時點，不改原版狀態；未命中選單前不推定駐軍已啟用。正式來源v65未改，收據只在workplace。

### v88有界局部收據與v89正確快捷鍵

v88正常駐軍點擊實際開職業選單，標題「目前：士兵」確認裝備後身分；取消並回世界仍選船，A後點城市實際重新進城。外部同容器正常點擊由v88/drive-city.sh保存。300秒外層逾時已終止並移除容器，只有局部GUI及status，沒有正常關窗的完整輸入、RAM及報告；不能作正式驗收或猜補JSON。後續docker exec因容器已不存在而未執行，沒有新增Escape動作。

`codex-audit/colony-orders-gui-v89.sh`／`colony-orders-gui-v89/` 沿v84正常裝備與退出，使用說明書第105頁M進移動模式、W等待下個單位，取樣後再正常關教學及開關ORDERS；正常關窗保存完整原版及輸入。若仍為船，保留未命中，不改按鍵映射或注入駐軍。GUI擷取沿capture_frame，正式前端／存檔／圖集不改。

### v89與地圖旗標正常取樣

v89 M／W後仍顯示船，ORDERS為十四列船隻選單，沒有Join Colony；正常關窗終點117800000步RAM `fcff01dc67736eace6fbcef25eafd224f8c3936c6084291a3f9b43da0bc7a8f8`，輸入 `930d782a3a4ca893f163ca8bb5b41d0df75951ba28456164c44541d3ba9bc1da`。說明書的按鍵語意修正保留，不推定駐軍必須加入自動單位循環。

`codex-audit/colony-orders-gui-v90.sh`／`colony-orders-gui-v90/` 沿正常裝備回世界，改以真GUI點擊城市上方可見紅旗區600,488輸出像素，取樣確認實際選取結果，再Enter及開關ORDERS。這是畫面幾何導出的可丟棄正常滑鼠原型，不注入地圖或單位座標；旗標是否對應陸地單位未知，命中以新畫面與原始事件裁決。正式前端、圖集、存檔均不改，不計完成數。

### v90擷取同步失敗與有界暫停原型

v90旗標點擊後擷取八次，每次frame.step皆在ImageMagick擷取期間前進，guard全拒絕。只保留八張attempt及status，不補正式flag-selected截圖，也沒有完整關窗輸入／RAM。原版是否選到士兵尚不能由未對齊圖下驗收結論。前次準備命令自動核准審查逾時未執行；工具允許的一次重試成功，並非原版或Docker功能失敗。

`codex-audit/colony-orders-gui-v91.sh`／`colony-orders-gui-v91/` 沿同一正常旗標操作，只在截圖時有界暫停這次前端PID，檢查全部執行緒停止後使用未改capture_frame，finally必恢復。兩秒內停止不成功即拒絕；不增加盲等步數或挑像素。這是私有擷取原型，不改正式前端或通用工具。新GUI必須以實際frame.step重播並逐像素核對才證明標籤對齊，暫停本身不作通過證據；完整原版終點及存檔也須核對。

v91正常關窗後由同目錄replays.sh沿實際GUI輸入及全部取樣步數重跑中英／缺圖集；check-state.py逐像素核對所有GUI、三側共同原版索引／色盤／RAM及四側完整終點／原始COLONY03。只驗擷取及正常原版狀態，不授權未審來源或提高普查。

### v91正常擷取與原版完整狀態限定通過

`normal-state-summary.json` PASS_NORMAL_STATE_AND_CAPTURE，SHA-256 `f56534d0b71520b47fe3cd3bb813913d22e21241df6e581483a3f614ae9de4a6`。十二張GUI與中文重播逐像素相同，十二個共同原版取樣點的RAM／索引／色盤及GUI／中英／缺圖集四側完整CPU、RAM、索引、色盤、輸入與開檔相同，原始COLONY03工作副本四側未改。終點109800000步RAM `c5f315a63afdf64cdcc6d88915ea7e51075dfc24fce369d5210fb9da017aafec`，輸入 `bc9291d0c9b2346a5613ce7975a9f2d9401039976314cd844a1be22d30429a53`。有界暫停擷取原型確實對齊此新路徑，不外推至通用工具已完成；正式程式未改。

旗標取樣實際進城。後續點上方標題開出城市改名框，102465000步可見中文正文與名稱標籤；沒有世界陸地ORDERS或Join Colony／Pillage命中。原始正文候選GAME.TXT:0x00000F5C、0D21:00C6、線性RAM175166、97654865步、安全區[61,86,219,98]、30px；名稱標籤STRING:input-label、RAM175436、97690918步、安全區[61,102,89,113]、29px。原始位址採dosgolem實模式CS:IP／線性RAM，檔案位移另列，不當IDA EA。GAME.TXT、VICEROY與工具版本沿本目標及規格036的固定指紋。輸入文字保留原版英文名稱；沒有完成改名、保存或價格／單位規則的驗收。

此新改名畫面維持DRAFT，不提高807列清冊。交接至[目標181](181-colony-remaining.md)：下一個可裁決閘門是由正常城市標題開框、正常取消並量測兩欄原版字高／基線、候選字級、最長譯文及原始來源歸屬，再走READY與獨立欄位驗證。Join Colony仍缺正常駐軍啟用入口，不繼續用Space、M／W或旗標點擊猜補；重開此切片時先定位原版駐軍輸入擁有者或取得明確操作證據。
