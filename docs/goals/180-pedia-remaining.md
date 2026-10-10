# 目標180：其餘五類百科逐篇驗證

## 2026-10-09：目前完成審查

| 原要求 | 目前證據 | 結論 |
|---|---|---|
| 六類其餘146列、逐類清單與正文 | 既有六類150篇正常驗收與22個先決條件保留；目標185另有31GUI／三側代表性抽樣。 | 顯示驗收成立，歷史收據不冒稱重新全部走過。 |
| 翻譯與正式接線 | 全部164正文、19索引／概念名已驗原檔指紋與正式loader；最新正式來源接線重驗PASS，摘要b4a311755238…。 | 來源已接，未觀測的重複地形來源仍保留推論等級。 |
| Miscellaneous／Complete類別 | 原版正常初始化只讀六項，命令0x70～75；heap六項終止鏈與GUI相符，原檔0x72AD3等六處與0x23904分派已核對。 | 本版正常類別入口不存在；不修改原版或注入類別。類別6／7靜態分支保留。 |
| 同狀態與回退、矩陣／普查 | 已驗正文與欄位各有正常GUI、原版及回退；新增入口限制列與大河精確scope，86列合併普查進行中。 | 86列生成報告与完整要求審查PASS，依2026-10-04代表抽樣接受標準完成。 |

正常入口限制的公開檢查器是[check_goal185_pedia_boundary.py](../../tools/check_goal185_pedia_boundary.py)，規格049的單行分類已READY。原版完整SHA、IDA9.4、執行時與檔案位址分開記錄於RESEARCH-LOG。這個結論只排除類別清單入口，不把個別遊戲概念的情境提示全部宣稱不可達。

完整#57審查入口：[check_goal185_pedia_completion.py](../../tools/check_goal185_pedia_completion.py)。核對全部164正文、19索引接線与目前正式來源相同，保留六類逐篇歷史驗收與当前31GUI／三側，確認三個入口分類與同文地形來源限制；通過前不標完成。

狀態：進行中；日期：2026-10-01。對應 [Issue #57](https://github.com/wicanr2/colonization_cht/issues/57)，承接[目標179](179-pedia-cargo.md)。目前入口：[CONTEXT.md](../../CONTEXT.md)。

沿用既有規格036／038；新增顯示修正須先補原版證據與欄位量測，再通過READY。由冷啟動主選單正常載入原版自行儲存的 `COLONY00.SAV`，依原版清單走訪單位23、地形21、職業27、建築38、開國元勳25項。來源清冊在本機 `workplace/reports/goal170-census-explore/REPORT.md` 與 `census/pedia-all2.tsv`；清單項數不能直接當成不同正文來源鍵的數量。

存檔 SHA-256 與固定前端、原版指紋沿用目標179。原版每次返回清單重設至第一項，因此每次從第一項按相應次數 Down，再按 Enter 開篇、Escape 返回；不注入快照，不修改原版。

重產入口：在 [tools/Dockerfile.verification](../../tools/Dockerfile.verification) 的既有映像及有界、無網路、目前 UID/GID 的容器內執行 `bash /repo/tools/probe_goal180_gui.sh <類別>`；五個類別參數為 `unit`、`terrain`、`job`、`building`、`father`。本機收據保存於 `workplace/reports/goal180-pedia-rest/<類別>/`。重播沿用 `tools/probe_goal179_replays.sh`，以 `COLONIZATION_GOAL179_OUT` 指定該類別目錄。

重播入口另由 `bash /repo/tools/probe_goal180_replays.sh <類別>` 固定類別路徑；獨立檢查器為 `python3 /repo/tools/check_goal180_window.py --game /game --reports /repo/workplace/reports/goal180-pedia-rest/<類別> --category <類別>`。重播需要有界 Xvfb 擁有程序及退出 trap，三側使用相同原版正常存檔與真 GUI 輸入。

退出條件：每個清單項目正常進入；正文與字串欄位真 GUI／中文重播安全區逐像素一致；中英與缺圖集負例的原版完整狀態相同；指紋異版拒絕、缺原版明確 skip。只有通過者接入矩陣與普查。尚未到達的 Miscellaneous／Complete 不因本目標改列不可達，Issue #57 不提前關閉。

## 地形鍵勘誤與證據界線

原始地形21項走訪及中英、負例重播已完成，現有正文與已啟用字串檢查通過；漏譯欄位另修正後重驗，不能據此宣稱整頁完成。收據鍵是比對器選中的模板鍵，不能直接當成原版讀取的段落位移。現行 `dialogCatalog.matchIn` 在正規化正文與譯文都相同時採最後一筆；`TERRAIN8/16`、`9/17`、`10/18`、`11/19`、`15/23` 五組均符合此條件（confirmed：固定指紋的雙語稿與當前程式核對）。其餘三組不完全相同，不能混併。

地形現場啟用的21個模板鍵是 `TERRAIN0`～`7`、`12`～`14`、`16`～`19`、`23`～`28`。舊普查將 `16`～`23` 全列不可達的判定是目標173保留的假說，不能據此宣稱這些相同文字未顯示，也不能由新模板鍵反推其原始段落來源。正常清單項目與畫面顯示已證實，精確重複段落歸屬仍未知；普查需保留這個限制，不用改名掩蓋。

## 漏譯欄位

候選欄位量測使用 `tools/measure_goal180_layout.py --reports <目標180本機收據根目錄> --assembly <當前可丟棄前端組裝目錄>`，在既有 Go 容器及唯讀 dosgolem 掛載下執行；只呼叫正式 `centeredMasks`／`stringMasks`，量測結果另存候選目錄，不修改正式譯稿。診斷工具另記錄長段落的原始位元組與完整性，供三篇項目符號正文追查。

版面量測輸入由 `tools/prepare_goal180_layout.py --game /game --output <新本機目錄>` 建立，包含原版可定位的 `JOB27`、既有163篇與8個候選字串模板；全部維持 DRAFT，只供固定正式字型工具鏈烘製與欄位量測，不是正式譯稿。候選目錄使用 `workplace/reports/goal180-pedia-rest/layout-prototype/`，其 `dialog-atlas/`、`string-atlas/` 為本機字模中間物。

單位 GUI 收據的 `string_misses` 包含合併單位名稱與船艦貨艙、老手、火砲加成數值列，既有模板沒有涵蓋。正文23篇有啟用事件，不等於單位頁全文完成。可丟棄量測入口 `tools/probe_goal180_string_geometry.py --source <當前已組裝前端目錄> --output <新本機目錄>`，只在既有 Docker 內複製當前來源、加入未翻譯字串的墨跡／字高／安全區診斷；診斷來源雜湊另存，原版與正式來源維持不變。新模板必須先由這些欄位證據補到規格038，經 READY 後才實作及重烘、重驗，不能以正文檢查通過宣稱整頁完成。

## 驗證生命週期

項目符號正文對應的原版來源為 BUILDING12（Schoolhouse）、13（College）、14（University）；不能由清單位置反推來源編號。三篇長段落診斷皆在第一個 `0xF9` 後留下奇數 `read_pos`，因此先被完整性守門略過。窄追蹤沿用 `tools/probe_goal178_trace.go --scratch <正常存檔副本目錄> --from 186327000 --to 186340000 --verify-step 189090001`，輸入為 `building-v2/gui-pedia.inputs.json`；追蹤 CS:IP 與線性讀取位址，驗證終點另核對完整 RAM。這是追查線索，完整讀取契約尚未確認前不更動分段。

七篇正文的欄位量測入口為 `tools/probe_goal180_geometry_replay.sh job|father`；使用 `diagnostic-build-v5` 的固定正常 GUI 前綴，保留共同取樣點的 RAM、索引與色盤。只採共同 `cp-*` 取樣點比較，不將前綴與完整流程不同的 `final` 終點互比；這些診斷不能取代新中文的正常 GUI 驗收。

首版建築走訪抓到38項，但25分鐘外層逾時於1,437.4M步中斷，未留下完整 GUI 終點與輸入，不能驗收。資料保留於 `building/`；同一操作腳本與映像的乾淨重跑使用 `COLONIZATION_GOAL180_OUT=/repo/workplace/reports/goal180-pedia-rest/building-v2`，有界外層上限提高至2200秒。

正常走訪完畢後，可在同一容器使用 `tools/gui_close_window.py --window <自有視窗ID>` 送 Xlib `WM_DELETE_WINDOW`；原生前端已明確處理正常關閉並保存輸入／完整終點（`tools/window_prototype.go` 的 `runWindow`／`Update`）。該工具先核對視窗宣告的關閉協定及既有映像的 Xlib 資料布局，失敗不送事件；不是強制殺程序。正常關閉後仍須以真 GUI 輸入記錄的實際終點重播核對，不把關閉訊息本身當成驗證通過。

## 本輪現況與固定來源

原始五類走訪均完成；單位23／59個既有字串欄位、地形21／93個既有字串欄位通過舊來源檢查。職業缺JOB8、27；元勳缺五篇百分比；建築缺五篇百分比與三篇教育建築正文、22個先決條件欄位，不能標為完成。

規格036／038已補READY並實作百分比、Tab空段、JOB27、六個單位／地形模板與Savannah場景守門。正式百科稿為164篇，原始Tab與%%仍保留；Go自測與來源驗證通過。字模由固定rich2-py映像、Python3.12.13、Pillow12.3、FreeType2.14.3及固定Cubic 11重烘；正文圖集SHA-256 `78081567c823fd025246d84d2b1bf7f8bbf614bfd268ca08eb59aaa48c487e55`，六模板字串圖集 `0c5eec38140bb6b3431584f355ece607fa343dc44ef87da6b52d4f41e945236e`。候選量測25欄通過，擴充到五篇建築百分比與22個先決條件後52欄均通過；新增建築模板尚未因此直接進正式路徑。

新來源正常GUI保存於 `unit-fixed/`、`terrain-fixed/`、`job-fixed-v2/`、`father-fixed-v2/`；正文啟用數分別23、21、27、25，中英與負例完整重播尚待獨立檢查。前兩類使用 `strings-fixed-build`；後兩類使用 `formatted-build-v2` 與經原字模綁定驗證的 `baseline-string-templates.tsv`。各自保留精確來源與字模，不把兩種組裝混稱相同二進位。

第一次 `job-fixed/`、`father-fixed/` 因執行中的Bash檔案被編輯而中斷，缺完整輸入／終點，收據不採用。包裝入口現於容器內先複製操作腳本到/tmp，固定本次內容後執行；乾淨v2重跑正常關閉並保存完整輸入。首版量測因沒有DISPLAY而被Ebiten初始化拒絕，在同一映像加有界Xvfb後原命令通過；沒有分類為產品缺陷。

項目符號仍是DRAFT。可丟棄 `bullet-prototype-build` 只修觀測配對，不改原版；完整正常建築輸入重播與三篇欄位量測待完成。正式分段尚未含此候選。

## 2026-10-01續驗勘誤

上述「四類重播待驗」與「項目符號仍為DRAFT」是較早階段的紀錄。四類完整檢查已PASS：單位23篇／75個字串欄位、地形21篇／95個已啟用欄位、職業27篇／118欄、元勳25篇／52欄；同狀態與正常GUI安全區均通過。地形仍有兩個海岸／河流欄位漏譯，不能由既有檢查宣稱整頁完成。

項目符號已經規格036補審READY並實作，三篇教育建築的可丟棄原型全事件與版面56欄量測通過。正式來源對話框SHA-256 `f0771e8b6c864e89748f80215eaf1a73d87769f99f226a823ae65f5287b040f2`；正式八模板稿 `b29a5c443529686193bf0f020bf2c73ee3e64823e5422bf1c6fdfe0b2c8be27e`；字串圖集 `d7bbeaf411504689213b146ddeca2b48d7d55837a2df92e551ce86d96e07d240`；二進位 `ae41d5f6b17908a6a7086326879f76b7ea10097d577da7a6f604ea56a1183fcd`。正式正常GUI與三側重播驗收仍待完成，尚未升CONFORMED。

`building-final/`與`terrain-final/`均停止於部分頁面，缺完整輸入與終點，沒有可回收的退出碼；停止原因未知，不能將其分類成產品缺陷或宣稱逾時。乾淨重跑入口仍是相同映像與 `probe_goal180_gui.sh`，輸出改為 `building-final-v2/`、`terrain-final-v2/`；容器內10800秒、外層10900秒上限，每次保存 `<類別>-final-v2.run-status.json` 的退出碼及耗時。未覆寫舊收據。

矩陣新增四類已通過收據；地形五個等價模板鍵的 `key_evidence` 明列強推論，普查保留原始段落來源未知。舊「16～23全部不可達」假說撤回，改為待核對情境路徑；不把相同畫面正文重複算作多個已證實來源。


重複地形的可丟棄來源觀測入口為 `tools/probe_goal180_pedia_keys.go`，在既有Go容器、唯讀原版與dosgolem掛載下執行；正常輸入使用 `terrain-fixed/gui-pedia.inputs.json`、獨立存檔暫存層，`--from 58000000 --to 500400000 --verify-step 500400000`。輸出位於本機 `terrain-key-all.log`及 `.state.json`。完整原版RAM與控制相同；同一局部RAM `0x2AE9E` 在各頁開啟前由 `0E2D:11EB/11EF` 寫入21種TERRAIN鍵，集合為0～15、24～28。這是已證實的RAM寫入事實，角色為來源查詢鍵仍屬強推論；不是正式覆蓋條件，也未將模板16～19／23的來源歸屬升confirmed。早期窄觀測的76M檢查點命令把76000000與實際76065000混用，另外誤讀`.verify.json`檔名；已用完整500400000終點重新核對，不能把前次差異算成產品缺陷。


## 先決條件同步缺口：DRAFT（2026-10-01）

`building-final-v2`的正文38篇與已啟用53個字串欄位通過，但來源22個先決條件只有5個啟用、17個`screen-sync-timeout`；`string_misses=0`不能證明全部欄位已顯示。檢查器新增`--require-pedia-fields`，要求22個來源都有實際啟用區間；既有部分驗收不改稱整頁通過。規格038的先決條件維持READY，尚未CONFORMED。

本機`sync-prototype-build`只在候選副本暫緩先決條件的2M步等待螢幕逾時，畫布改變仍立即撤銷、其他欄位維持原守門；目的為量測原版從來源完成到VGA同步的延遲，不是正式修法。沿`building-final-v2/gui-pedia.inputs.json`完整正常輸入重播，候選輸出由`probe_goal180_geometry_replay.sh building`及`COLONIZATION_GOAL180_GEOMETRY_PREFIX=sync-prototype`保存；對照完整原版終點及所有共同取樣點，再決定READY修法。不得單純提高全域逾時讓檢查通過。


同步候選已完成：22欄均active，81個原版共同取樣點及完整終點相同，延遲1,760,277～2,351,390步。規格038補READY，僅先決條件模板等待預算3M，其他字串維持2M；3M是有界工程裕度，不是原版固定時序。正式修正後需新`sync-final-build`與`building-final-v3/`正常GUI、三側重播，並以`--require-pedia-fields`核對22欄實際取樣啟用。


Miscellaneous／Complete入口補查保存於本機`menu-options/`，使用固定正常存檔與當前正式組裝，從主選單載入後開百科下拉選單，逐次按八次Down、Enter、Escape，再正常關閉。原始MENU.TXT確有這兩列，既有實際GUI只呈現六類，中間有分隔列；不能把資料檔有列等同可達，也不能只憑未顯示就宣稱不可達。此補查先核對鍵盤分支，不修改原版選單。


正常選單補查的可重產入口已保存為`tools/probe_goal180_menu_options.sh`，輸出用`COLONIZATION_GOAL180_OUT`指定新目錄。已走訪八次Down：前六項依序為貨物、單位、地形、技能、建築、元勳，第七／八次回到貨物／單位；Enter進入單位清單，沒有Miscellaneous／Complete選單列。原版鍵盤可達的此下拉選單界線已取得，三側同狀態補驗中；未因此宣稱其他程式路徑沒有資料讀取端。


選單邊界的正常GUI獨立檢查入口為`tools/check_goal180_menu_options.py --game /game --reports <新收據目錄>`；14個原版檢查點、GUI與中文選單安全區、六項環繞全部PASS。為核對資料殘留的來源契約，本機`ida-pedia/`由固定`ida-pro-9.4-idapython:locked-v1`、UID1000從唯讀VICEROY.EXE新建一次性資料庫；先用`probe.py`檢查工具版本、原始輸入指紋、函式數與原始字串xref，只為選單邊界取最小證據。匯出保留IDA EA、原名稱、bytes、運算元，所有語意初始unknown，不覆寫正式DB或自訂名稱。


## 建築正式v3驗收（2026-10-01）

森林情境百科的安全探勘入口為[正常F1操作腳本](../../tools/probe_goal180_context.sh)，從同一原版正常存檔載入，切換檢視模式，只點選已確認的第一個針葉林位置後按F1、Escape。原版會重新置中，因此不繼續沿舊螢幕座標猜下一格。輸出預設本機`context-v2/`，可由`COLONIZATION_GOAL180_OUT`指定不存在的新目錄；沿用目標180正式來源與圖集。不注入地形或快照，不自行把未命中條目改列不可達，也不新增正式覆蓋條件。

`building-final-v3`正常GUI退出碼0、705秒；加強檢查`--require-no-string-misses --require-pedia-fields`PASS：38篇正文、70個字串安全區、全部22個先決條件在逐篇取樣點啟用。中英／缺圖集完整原版狀態及81個共同取樣點一致。GUI輸入SHA-256 `217af6321b916e9e79f236dc3ed78d03329e5f80c913387a79689b945a7c4eba`，終點RAM `fca0c413fe8cf37004db2078fd6917a21459c5bd1ea986a80b71451918203d66`；正式二進位 `b2813d1db94cc329f5fb93221fc0669b7f3dedd8b33e6f254e763efd1015b31f`。規格038先決條件與同步等待限定CONFORMED；v2的17欄失效已解決，舊失敗與候選量測仍保留。

矩陣改取v3並要求全部先決條件，另納入正常下拉選單六項環繞收據。最新重產報告入口為本機`matrix-v3/`、`census-v3.json`；以生成後的矩陣／普查數字為準。Miscellaneous／Complete其他入口與同文同譯地形的原始來源仍待窄查，Issue #57尚未完成。


## 2026-10-01：v3矩陣與普查重產

矩陣34PASS、0SKIP、0FAIL、0原版輸入衝突；彙整JSON SHA-256 `24ff75c8a6449f8b4e92c2a5be5c1698b3a7eec219ae9decf5e604a754530a4e`，可讀矩陣 `ee533b4b11893e90373fe2a62dee2eea55b21b421ce840ac61ec9c9ebf1657fb`。普查分母1,866列，已顯示761、待接1,016（正常649／特定局勢367）、無法正常觸發89；未分類及未使用樣式0。新增17列來自v3實際啟用的先決條件執行期字串，不是取消待接項或推定其他來源完成。普查TSV `d4a9472715ad6bbf3acba72d0fd4a4cb4250453d1a48f6b55206ca6f884eaa04`，報表 `306c7e1fd22b536c7afbdad2ad2730f5b1ba96a6ce2efd68a5e4476dd734fa69`；本機`matrix-v3/`、`census-v3.json`。

首次普查命令誤以矩陣彙整JSON取代原始矩陣定義，缺少dir欄位而停止；改用`tools/verification-matrix.json`後於同一容器工具鏈乾淨重跑通過。這是命令輸入問題，非產品缺陷。


## 2026-10-01：百科雜項取址窄查

工具為固定`ida-pro-9.4-idapython:locked-v1`的IDA Pro 9.4，原版`VICEROY.EXE` SHA-256 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`唯讀。原始MZ新建資料庫的檔案位移`0x1FC7E`對應IDA linear EA `0x2D87E`，原`dseg`起點`0x2B5A0`，差值`0x22DE`；字串為Miscellaneous，附近直接xref為0。xref缺項不證明無間接讀取。

原檔唯一`DE 22`出現在檔案位移`0x7530C`。另建窄二進位資料庫，IDA EA `0x0`映射原檔位移`0x75000`；EA `0x30B`／原檔`0x7530B`原位元組`68 DE 22`解碼為`push 22DEh`，後接`push 22ECh`及原始far call `191Fh:0928h`。這些數字是原檔運算元，不宣稱等於目前執行期CS:IP。匯出56個原始指令，保留bytes、原始EA、檔案偏移、函式名及局部xref。資料庫未重命名、原版未修改。

已證實：原始字串與上述取址指令bytes、檔案位移／IDA映射。強推論：此處向共用初始化讀取呼叫傳遞雜項名稱。未知：呼叫語意與後續玩家可達讀取端；不能由此關閉Miscellaneous待驗項。正常GUI六項選單環繞已由獨立收據證實，靜態取址與GUI邊界不互相替代。

本機入口`goal180-pedia-rest/ida-pedia/xrefs.py`、`overlay.py`；收據與派生原版片段均留忽略的`workplace`，不公開。最初UTF-8寫入未指定編碼及二進位自動資料項阻止建立指令，屬匯出腳本問題；明確UTF-8、核對載入bytes、在一次性資料庫清除資料項後重跑，非原版缺陷。

- `xrefs.json` SHA-256 `9fd1ba68e27e0e829cd65a372c3f050fd3ae7c25e9e2f0414fc2787ba2ee29e2`。
- `overlay-window.json` SHA-256 `3ad007140ada2436e7e14adf47cc1f7641990288c2397b1d257ae5578efb5427`。
- `overlay-window.bin` SHA-256 `b383cd41f1d763b5aa625c068bb34ad3c5bdb18e8b9e9957c0083a5bd8fa42c9`。
- `xrefs.py` SHA-256 `70a1dce5664d8daa0265653e80907be44e25860fece2dcf0758e22b88d41f198`。
- `overlay.py` SHA-256 `5861c5c225065e34fc1bd06a3e7ee6b4a7911a91288676e03d687441ada75ffd`。


## F1情境探勘與來源讀取端（2026-10-01）

TERRAIN8局部來源的可重跑檢查入口：[來源身份檢查器](../../tools/check_goal180_source_identity.py)；原版與正常存檔、六個窄觀測的原版檢查點、DOS原始讀入、CRLF轉換有效前綴、成功比較分支、隨後標題讀取及IDA實際函式邊界都須通過。只提高這項有限來源結論，不自動回填其他模板的原始身份或宣稱跨緩衝全文已逐位元組驗證。

已開兩頁的獨立檢查入口為[情境百科檢查器](../../tools/check_goal180_context.py)，要求全部GUI取樣點原版狀態一致，僅在實際開啟的兩頁核對正文及已啟用欄位安全區；不要求八次嘗試都曾開啟百科，也不取消未驗來源。

`context-v1/`八次F1嘗試只有第0／3次實際開啟正文，模板鍵為TERRAIN12與TERRAIN23；原版點選後會重新置中地圖，後續固定座標不保證仍落在已探索地形。沒有開百科時按Escape會打開離開確認，不能拿這些取樣點充作百科頁面。此路徑不證實TERRAIN20～22可達或不可達。中英與缺圖集重播只驗實際已開兩頁及完整原版狀態，不納入全篇完成數。

局部來源追查保存兩個獨立本機入口：`key-read-probe.go`觀測線性RAM `0x2AE9E～0x2AEA9`，`key-lookup-probe.go`觀測後續局部副本 `0x2AC87～0x2AC90`；兩者都由受版控`tools/probe_goal180_pedia_keys.go`產生，沿`terrain-fixed/gui-pedia.inputs.json`及正常存檔冷啟動，不注入快照。輸出`key-reads.log`／`key-lookup.log`及`.state.json`。首個讀取端顯示TERRAIN8由`0E2D:07D7/07DB`複製到`0x2AC87`；這只是已證實的局部讀寫事實，查找／正文來源連接尚待審查。兩個原始CS:IP為dosgolem實模式，RAM為20-bit線性，不與IDA EA混用。

三側情境重播首次因缺DISPLAY於GLFW初始化停止，沒有執行遊戲。保留各`.environment-error.log`，只刪除本輪產生且指紋吻合的三份暫存種子副本後重跑；`probe_goal180_replays.sh`已補缺DISPLAY時的有界Xvfb與退出trap。這是工具鏈入口問題，不記為產品缺陷。


正常F1入口已收斂為第一次已確認的針葉林，預設新`context-v2/`；舊八次嘗試腳本逐字保存在`context-v1/probe-source.sh`，其輸入／收據仍原樣。context-v1限定檢查PASS：兩篇正文、20個字串欄位安全區與正常GUI一致，28個原版取樣點及三側完整狀態相同；GUI輸入SHA-256 `49edd1f67e46a2561ad8bee9a9cd6e0826fc8d88a6850f076e8a68e78804bfd7`，終點RAM `4e47c3d8752ae69646215ce578b8ba0b6b718295d79ab0f57011a5eb6fdf30b5`。這不是新增兩個原始來源完成數，TERRAIN23歸屬仍強推論。

下一段比較觀測由本機`key-compare-probe.go`及`key-compare.log`補足：72,515,485步於`0E2D:0832`將局部TERRAIN8與標記緩衝的`@TERRAIN8`連同零字元比完。300步控制流入口`key-match-trace.go`產生`key-match.log`、`.sources.json`與兩個runtime片段，只用於IDA關係補證；字串／解析片段分別對應實模式`0E2D:0000`、`0C0B:0000`，不沿用原EXE的MZ線性EA。輸出只留本機，不將片段或傾印公開。


## 2026-10-01：TERRAIN8來源有限補證通過

`tools/check_goal180_source_identity.py`PASS，本機`source-identity.json`：原版PEDIA.TXT標記檔案位移`0x65A5`、正文起點`0x65B0`。72495279步，DOS由PEDIA位移`0x6400`讀入512位元組至實模式`1C6A:E962`／20-bit線性RAM `0x2B002`，剛讀入內容逐位元組相同；原始讀入SHA-256 `130bfa6dbd8e58eda11f639a942febd3879bea89fc7c4c8ae424ab8dc58db27b`。稍後文字模式刪除CRLF的CR，有效489位元組前綴相同；尾端23位元組是殘留，不當成有效來源。

72515484步，`0E2D:0832`的原始`F3 A6`將RAM `0x249DC`標記與`0x2AC86`局部查詢鍵的`@TERRAIN8`及零字元完整同值比較。隨後走`0E2D:083B`與`9320:00DE`匹配成功分支；後續`0E2D:09F4`讀取正文最前29位元組（版面指令及標題），與該原始段落完全相同。跨下一個stdio緩衝的全文並未逐位元組串接驗證，不能把只取09F4時漏掉的邊界字元當成原版文字缺失。

IDA Pro 9.4 runtime原始二進位EA `0x001A`映射實模式`9320:001A`，函式原名`sub_1A`、邊界至`9320:0106`；無推測改名。正式關係庫`ida-pedia/runtime-lookup-final.i64`、匯出`runtime-lookup-final.json`，輸入片段SHA-256 `25adc1a8eefe200749aa0aff70c0c0c0a1255f99c4252c80f17519813e073825`，匯出 `ee89eb8a805ff3edbff87569b3d4ac5673ccea7cdffb30def24df5ab468e9b71`；此空間不是原始EXE的MZ EA。

已證實僅限本正常路徑查詢並讀取TERRAIN8初始正文；GUI字典選中的TERRAIN16只是同文同譯模板，不能據此宣稱原版讀取16。既有21頁／95已啟用欄位GUI、中英與缺圖集檢查仍通過；六個窄觀測在76065000步的RAM皆為`7a1b5da22c71b95e8d38a8de0590cc7cebb89cd176125c58aded6bbbd955e8f5`。原版、dosgolem、Go與正常存檔指紋沿目標180；精確工具及收據SHA由來源檢查JSON列出。

其餘四組同文來源與特殊森林仍未提高證據等級。完整正常路徑的標記比較補查入口本機`key-matches-all.go`，輸出`key-matches-all.log.matches.json`，每筆保留原CS:IP、兩個RAM參數、比較原bytes及最近PEDIA DOS讀取位置；追蹤58M～500400000步，原版終點須與terrain-fixed控制相同。此工具只觀測，尚未授權正式覆蓋條件／資料格式或普查改鍵。


### 同文地形的普查來源更正：DRAFT→READY（2026-10-01）

事實：原版正常地形清單21次完整標記比較皆從已審`9320:001A～0106`呼叫到`0E2D:0832`，返回位址均`9320:00D7`、零字元比較前CX=1，marker與key完整相同。最後一筆PEDIA DOS讀入範圍含該唯一標記的結尾；每次匹配與逐篇正常GUI有唯一時序關聯，原段落與所用模板的正規化英文／譯文完全相同。獨立Go觀測的完整原版終點與正式地形控制一致。原版檔案指紋、工具、原始RAM及IDA位址契約見本目標。這足以更正本正常路徑的來源歸屬；不宣稱全部正文的每一位元組搬運或其他玩家情境已驗。

受審映射為模板TERRAIN16→實際查詢TERRAIN8、17→9、18→10、19→11、23→15。前端模板鍵與譯文不改；只更正普查來源，未查詢16～19／23仍是特定情境待驗，不能把同一中文畫面算成兩個原始來源都完成。未知20～22亦保留待驗，不猜為不可達。

普查矩陣的內部證據欄位`source_identity`保存`checker`、`args`及`aliases`。只在檢查器`tools/check_goal180_source_identity.py --all-markers --lookup-reports <該列GUI目錄>`PASS、輸入／完整終點精確綁定該列、回報映射與聲明逐項相同時採用。普查及矩陣都自動重跑此證據檢查，缺原版skip、錯版或資料不符拒絕；不能只信手填aliases。映射只套用該列收據；其他未提供來源證據的同文模板不歸屬為原始段落，避免舊模板事件再次讓16～19／23被計入已顯示。

DRAFT審查完成：當前`terrain-final-v2`的正常GUI、中英、缺圖集與96個欄位安全區通過，21個查詢來源與五個同文模板關聯由現行輸入重生，獨立source-query原版終點相同。故本證據欄位與上述五項來源更正升READY；實作需核對來源8／9／10／11／15顯示、同文16～19／23仍待驗、總完成數不因同文翻倍、拒絕偽造映射。此欄位只屬報表內部，不改遊戲、存檔、譯稿格式或正式覆蓋判定。

當前來源收據SHA-256 `fa81707be19760513cc9542a4054970ddbf1fcd2871c8af5ee3c13cb4e633fdb`；GUI輸入 `6b248028dbd22aa9e363a8c5b6469079821dc904eac8d560b12ddde143a1d4be`。


### 同文地形普查來源更正：限定CONFORMED（2026-10-01）

READY後矩陣與普查皆重跑來源檢查器，核對該列正常GUI輸入、完整原版終點與五項映射。`source-identity-negative.json`確認正例PASS，偽造映射、錯GUI輸入與另一列綁定均拒絕。生成普查中TERRAIN8／9／10／11／15列shown、證據confirmed；16～19／23仍pending，20～22亦pending。總完成數仍761，未同文重複計數。矩陣34 PASS、無SKIP／FAIL／過期／版本衝突；普查1,866列、pending1,016（normal644、conditional372）、unreachable89、未分類0。

本限定CONFORMED只授權這份正常地形收據的來源歸屬；前端模板鍵、正式判定與原版未修改，不外推其他玩家情境或正文每位元組鏈。內部矩陣入口`tools/verification-matrix.json`的`pedia-terrain-all.source_identity`、實作`tools/verification_matrix.py`與`tools/text_census.py`；本機報告`goal180-pedia-rest/matrix-v4/`與`census-v4/`。

來源檢查器輸出SHA-256 `90fd57502cae0d0f0ff3ce3061837a401ea63c6f9fe666b61797040f0ab6ada5`；負例收據 `2b3b972d02b9995dbb8c70c579b26ce645233d843792a8f490fe6d6917aa77be`。其他F1情境來源仍另驗，Issue #57不關閉。


F1來源補查已核對實際鍵12／15，輸入與完整原版終點和context-v1控制相同；沒有命中額外16～23，不提高完成數。為確認情境選擇端的可達範圍，下一份窄觀測入口本機`context-v1/key-selector-trace.go`，由受版控`tools/probe_goal178_trace.go`複製，增加原版指紋與本次遇到的原始程式段傾印；僅追59633000～59645000步，結束仍核對188400000步完整RAM。傾印、IDA一次性DB與追蹤只留workplace，所有新語意初始未知，不改原版或正式覆蓋。


情境runtime傾印的位址核對入口本機`context-v1/mapping-check.py`，讀IDA原始file-region映射並逐位元組與傾印比較；中段匯出不能單獨證明函式入口。這項核對通過前，情境選擇語意維持未知。


情境IDA初版使用`-b16`，該選項設定載入段0x16，檔案位移0實際映射EA0x160，不能當作16位元模式開關。位址檢查確認載入位元組未變，但中段匯出的runtime映射錯置，因此`selector-window`及`selector-function`不採用語意；更正`-b0`重生`selector-function-v2.i64/json`。匯出工具新增EA0／原始全檔位元組守門；既有TERRAIN查找資料庫96筆EA／runtime／原始指令全數一致，來源檢查器也已納入逐筆核對，偽造位元組拒絕。原版指紋與正常來源關聯不受本次情境工具錯誤影響。


2026-10-01位址守門補驗：IDA情境初版`-b16`使檔案位移0載入EA0x160，runtime映射不能採用；更正`-b0`後的selector-function-v2每筆bytes與原始傾印相同，函式原名sub_EAC、IDA EA0x0EAC～0x1820映射實模式8C35:0EAC～1820。原始8C35:17D7的FF 76 06在59637458步讀取RAM0x2AF40／2AF41為12；這只證實本次地形參數，不外推呼叫者全集。既有查找資料庫96筆原始指令核對全部通過，偽造位元組拒絕；加強後matrix-v5仍34 PASS、census-v5仍761／1,016／89，來源映射限定CONFORMED不變。原版VICEROY與PEDIA、dosgolem及工具版本沿目標180固定指紋。


21項來源觀測的受版控重產入口為[tools/probe_goal180_pedia_sources.go](../../tools/probe_goal180_pedia_sources.go)，從本輪已使用的本機key-matches-caller.go保留完整程式行為，只更新說明。既有驗證映像內於`/dosgolem`執行`/usr/local/go/bin/go run /repo/tools/probe_goal180_pedia_sources.go --root /game --inputs <該列gui-pedia.inputs.json> --scratch <獨立正常存檔副本> --out <新來源收據前綴> --from 58000000 --to <GUI終點步數> --verify-step <同一GUI終點步數>`；GOPROXY=off、GOTOOLCHAIN=local、GOCACHE指定已驗擁有權的快取。工具SHA-256 `f61e9c4fd79819e56cb95bd36e5a793101720b29f762fe93fdc7210303afcf8b`；工具只是觀測入口，不單獨授權來源歸屬。

## 2026-10-09完成#57

公開完成審查PASS，摘要c1a1dbd1871b8006dbfc5b17b4075e7592a281f91ad82930ea6d4c15759448a4。164正文与19索引正式來源接線、六類逐篇歷史驗收、31正常GUI／三側、正常兩類入口版本限制、矩陣与生成普查逐項核對。保留同文地形原始段落強推論，不稱全164個來源均新命中；不新增原版類別入口。先前未知結論按新證據更新，歷史紀錄不刪。完整四項Goal其他工作繼續。
