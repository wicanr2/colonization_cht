# 規格049：普查的歷史驗收與本輪證據

## 2026-10-09 DRAFT：正常入口限制的單行分類

本版正常PEDIA初始化只建立六項命令0x70～75，未讀入MENU末兩行Miscellaneous／Complete。原始MENU資料仍保留兩行，PEDIA也保留12個雜項名与類別6／7靜態分支。正常初始化原檔位移0x72AD3等六處与唯一選單分派0x23904、原始標記查詢、heap鏈与31GUI已由[入口限制檢查器](../../tools/check_goal185_pedia_boundary.py)核對，摘要643df87c928a52e9ea38c4214c274b012546264ceb854613c3e8546ce128763c。此結論只限正常類別入口，不把個別概念提示一併宣稱不可達。

現有census-map只按段落分類，無法把MENU同段落中两個不可觸發項与六個可觸發項分開。候選保持TSV欄位与原始鍵格式，只允許LIST_FILES的分類pattern額外精確匹配「段落:0x行位移」；精確單行有且只有一條時優先，其他行仍按原段落唯一規則。未知位移／重疊／未使用pattern拒絕；原始輸入完整雜湊仍由規格049与入口限制檢查器驗證。只把MENU:@PEDIA:0x6E4／0x6F5及PEDIA:@MISCELLANEOUS類別清單標成本版本無正常類別入口，其他PEDIA內容与示範命中不變。

先在私用原型驗證原分類逐位元組保持、兩行覆盖優先與反例、正常入口proof，通過後才READY。不手改生成census，不改原版MENU或新增遊戲入口。

READY審查：私用行分類原型PASS_ROW_MAPPING_PROTOTYPE，沒有單行override時與原分類逐項完全相同；加override只改已證明的三個鍵，重疊規則拒絕、未知位移標為unused並由正式入口拒絕未使用pattern。正常類別入口檢查器另核對唯一原版SHA、六項命令bytes、MENU查詢、heap分隔節點与31GUI，scope包含六個原始MENU行，未將診斷前綴當新GUI。

合併補正DRAFT：首場86列正式重產50列PASS、current-census的三鍵分類正確，但歷史merge只更新shown，忽略已驗pending→unreachable。候選只採這一輪checked-matrix的confirmed unavailable_source_ids更新分類；沒有proof維持原歷史狀態，原歷史shown遇此聲明拒絕衝突而不靜默覆蓋。先驗真實86列輸入合併、三個鍵與反例，再READY；不手改生成TSV。

合併補正READY：真實86列current-census与50個PASS結果原型只改三個已證實鍵，維持全部歷史shown；沒有proof與舊merge完全相同，未證實分類与歷史shown衝突均拒絕。候選905shown／959pending／92unreachable。授權merge新增confirmed鍵集合參數，由本批checked-matrix取得，不從任意map宣告推定。只修報表合併時，可重用剛完成的同一批不可變current-census／summary／checked-matrix，必驗原始來源、矩陣與檢查器雜湊不變，明列「同一批重合併」而不宣稱新跑50列。正式合併後才CONFORMED。

單行分類与confirmed合併限定CONFORMED：正式86列重產50列PASS、36歷史證據保留，current-census已正確生成兩個MENU行与PEDIA雜項清單unreachable，入口proof缺失／錯鍵／錯版／未confirmed与分類重疊／未知位移反例全部拒絕。歷史merge補正後以同一批不可變current-census、summary、checked-matrix重合併；逐一核對原始完整SHA、矩陣SHA、檢查器SHA、收據JSON SHA不變，只有三個confirmed鍵與舊合併結果不同，既有shown全保留。完整操作與輸入SHA見私用history-census-86-confirmed-merge/operation.json。

正式生成1956／905shown／959pending／92unreachable，284本批可重驗、621僅歷史；TSV d122059cf52326d6f64ff826e0c9098ffe0c3176a55196a1cb4c53fd468b4fd1，報表c136ee8717bda8215a7ce77fc30f40e18450398b51df2148099dba7fecbe0a6f，矩陣報表4c461c12e0ec9c1a568830b8f4d608cdd9f9911b01b06f26d996b3ad5f52ebfc。這不是新跑50列聲明，也不把其他概念提示改不可達；#57完整要求審查已通過，四項Goal其他三項繼續。

據此授權通用LIST_FILES「段落:0x位移」優先分類。三個unreachable聲明必須同時由矩陣列的census_scope檢查器輸出unavailable_source_ids、confirmed原始EXE SHA並与列宣告完全一致；Census對精確行override与本次MISCELLANEOUS分類逐鍵核對證明，缺列／錯鍵／錯版拒絕。此驗證metadata不修改原版或玩家流程，不將其他概念提示改列不可達。正式報表重產与負例前只READY，不稱CONFORMED。

狀態：DRAFT。只授權可丟棄報表原型，不修改正式普查工具。

## 範圍與依據

使用者2026-10-04決定保留既有驗收，先完成接線再作代表性抽樣。原矩陣63列的普查為1945項、882已顯示、974待驗、89不可達。其後的15個新矩陣列只採實際已驗欄位，不將容量投影或同文模板當成原始來源。

2026-10-09盤點confirmed：矩陣設定78列，本輪42列檢查器PASS。35列舊收據目錄不存在，另有text-model列依賴已不存在的舊收據，共36列只能引用歷史驗收。無法把它們重命名成新PASS，也不以檔案不在判定產品缺接線。

歷史清冊SHA-256 a2a7be55c47c3084527d6169627d80a9206970069170c830922d004a89999c3c，歷史普查報表8989817b42dfab0d23536ab95ec61596630ba2120254a7649fd8c2e71c01b953，矩陣報表1c0090c9c74671ddb35f53e5abc41f20dd018c3d3df2b8ed34996454466d479a。凍結副本只讀保存在目標185私用證據根，來源檔未覆寫。

工具沿固定hr-go-ebiten image SHA-256 1430a2cfb652c5733914e8116dd2011da21da53ec6b4de3a1482b2a94472f5b5、Python3.11。原版13份TXT指紋必須與歷史報表相符；VICEROY.EXE仍為a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3。本文無反組譯位址或遊戲規則變更。

## 候選規則

- 保持現行TSV欄位、訊息键及shown／pending／unreachable狀態。
- 以既有清冊為歷史輸入，驗證其精確SHA-256、列數、唯一鍵及來源版本。未符合即拒絕，不自行找替代清冊。
- 本輪輸入必須由通過檢查器的42列產生。仍保留各列census_scope及source_identity守門，同文TERRAIN16～19／23不憑模板提高來源數。
- 本輪已顯示者採本輪證據；僅歷史已顯示者保留shown，證據欄標明歷史。沒有本輪收據不降格為產品缺接線。
- 新鍵只採本輪實際觀測，不憑字模、詞典或模板載入建立新完成項。
- 報表分列本輪可重驗與僅歷史驗收數量，不稱78列全PASS或全部文字已中文顯示。
- 對超出欄位验收範圍的未套用診斷，先核對同一收據其他層的實際套用事件；已由其他層顯示者不稱為仍英文，不因此提高正式完成數。

原型須核對歷史shown不遺失、未知仍未知、實際新增16項與8個新執行期鍵、重複鍵拒絕、錯指紋／錯版本拒絕、未驗欄位不提高完成數。審查後才READY；正式工具重產與反例通過後才CONFORMED。

## READY審查（2026-10-09）

原型保持全部882個歷史shown，新增16個實際完成項與8個執行期鍵；候選1953項、898shown、966pending、89unreachable。本輪42列可重驗證據涵蓋270shown，僅歷史shown628。TERRAIN16～23仍pending，未因詞典／模板載入提高數字。候選TSV SHA-256 3e03b78ddb41cd28b5d90f885dd5ff2f438c871ba5cbc300844c859745780ad5。

精確清冊／列數／唯一鍵／狀態總數與15份原版完整SHA-256正例通過，修改清冊位元組、錯PEDIA版本及缺GAME均拒絕。來源metadata候選SHA-256 7b1b8c10a523965333d7c6eedfbf16859fb85f552632f3e65c9bc3442495181e。正式只讀基準為[歷史鍵清冊](../text-census-baseline.tsv)與[來源及列清冊](../text-census-baseline.json)，目前輸出仍為text-census.tsv；基準的職責是可重現輸入，不能當成最新驗收表。

據此升READY，授權新增報表工具依上述固定基準重產，正式每次重跑目前可用列的檢查器，36個歷史列不記作新PASS。原生成工具的來源歸屬與欄位守門保持原有契約；覆蓋條件、原版、遊戲流程及存檔均不變。正式輸出及反例驗證前不稱CONFORMED。

正式入口為[tools/text_census_history.py](../../tools/text_census_history.py)。在固定Docker工具鏈內，以`--game /game --repo /repo --reports /repo/workplace/reports --output <本輪私用輸出目錄>`重產；原版與基準唯讀，輸出父目錄須存在並屬目前UID。只將text-census.tsv／md核對後回填docs，含原文明細留在輸出目錄。

## 限定CONFORMED（2026-10-09）

正式重跑42列檢查器、來源身份及欄位守門，全部PASS。生成1953項／898shown／966pending／89unreachable，270項本輪可重驗、628項僅歷史；與原型TSV逐位元組相同。修改兩份基準、重複鍵、錯原版版本均拒絕，缺合法原版明確77。沒有新遊戲狀態、UI或原始來源完成數的外推。

採用清冊SHA-256 3e03b78ddb41cd28b5d90f885dd5ff2f438c871ba5cbc300844c859745780ad5，普查報表9c58aefce4f5e2bae57ce37483673f99f3502cb32ce45b028a807b7f324b8adf。矩陣報表e6d1b692bab52f71f804f2c85637412f4d85019addb88f2915127f36ac699254明列42本輪PASS與36歷史列；原63PASS報表全文封存在WORKLOG的同日歷史矩陣段。私用重產`history-census-formal-v2`及`history-formal-review.json`為完整收據。首次200秒逾時未產生結果，屬驗證逾時；以同工具鏈有界600秒重跑通過，沒有將空目錄當成PASS。

入口：[目標185](../goals/185-player-experience.md)。原始像素、音訊、存檔與含原文明細只留workplace；正式清冊仍只保存鍵、指紋與證據分類。

## 2026-10-09收尾增量證據

`history-census-88/`完整執行52個可重驗列及普查，另36列僅歷史，1956項／906shown／958pending／92unreachable。追加第89列時，先核對前88列設定的完整SHA-256、52個檢查器、各側JSON收據、15份原版與基準未變，再通過新列完整審查及欄位守門。

`merge_census_89_delta.py`只讓已驗AMERICA正文與選項進入增量普查，狀態改變唯一鍵為GAME.TXT:@AMERICA；全部舊shown與三個confirmed入口限制保留。採用1956項／907shown／957pending／92unreachable，286可重驗、621僅歷史，TSV SHA-256 `7af46663e3b901f2c643bd31c57742ef01176b36f3c97599563061bca0931df9`。這是52列完整批次加1列追加，不聲稱前52列又重跑一次。

資料格式與正式覆蓋條件沒有改變。三種事件版畫只授權對應代表標題，報表明寫WOODCUT段落shown不等於17種事件全部正常命中。私用入口與公開檢查器見[目標185](../goals/185-player-experience.md)的完成#61段落。
