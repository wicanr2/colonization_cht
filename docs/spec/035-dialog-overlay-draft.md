# 規格035：通用對話框整句中文覆蓋（DRAFT）

## 2026-10-09 DRAFT：四處既有訊息的城市名稱資料回呼

來源審查使用正式addDraft檔案集合，558項TXT來源中440項可逐字查譯、68個MENU單行及37個GAME正文已載入；這些計數不當正常命中或完整#55完成。Join Colony／Pillage模板實際匹配成功。FINDCITY、NOCITY、COLONY、SHIPLAKE的初次未解析只是正文與單行路徑分流，單行探針已通過。冠詞三項有省略記錄；Cooperation／Conquest及Moderate有專屬欄位，Land組句與同文來源仍須審查。

四個城市變數實際匹配會回variable-without-term，沒有正常GUI命中聲明。GAME.TXT完整SHA-256為67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a；以下均為檔案位移，不能當執行期地址。

| 既有模板鍵 | 原始範圍與片段SHA-256 | 城市槽位與證據 |
|---|---|---|
| GAME.TXT:0x00001447（BUILT） | 0x1447／36 bytes；0d15de866821d917cfb02b46f3c847a50597d3751c245adddbbff4f4fd987809 | STRING0；原文「%STRING0 colony produces …」明示殖民地名稱，STRING1產物沿原術語，不猜產物規則。 |
| GAME.TXT:@FULL:0x00001482 | 0x1482／115 bytes；8043e56d414d8c92d5de8507c5fada319eeb1aefa6152d1cdeeb0900cdc27015 | STRING0；原文「The colony of …」明示殖民地名稱。 |
| GAME.TXT:@INDIANFOREST2:0x00004F7B | 0x4F7B／201 bytes；516bbffcee8f67dc619dd51fe58840ec72bcae14356139d5656885c2a71f0cec | STRING1；原文「Your colony at …」明示名稱，STRING0部落沿原術語。 |
| GAME.TXT:@TOONEAR:0x00006A24 | 0x6A24／71 bytes；8daa30c9fed822a24240aab9c45bc14978e187d00624578c2b6419e5b66b9da9 | STRING0；名稱來源另由下述指令與正常記憶體補證據。 |

TOONEAR的confirmed定位：VICEROY.EXE a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3，標記檔案0x1E345、IDA MZ EA0x2BF45，DS相對0x9A5。沒有直接xref不當不可達證據。檔案0x225F7讀ds:8542h，兩次INC後將DS:指標+2與索引0送往原始far call，0x2260A推入9A5h選訊息。此窄匯出IDA EA0x190000映射檔案0x21E72；raw far segment尚未證實為執行期段，不引用為runtime地址。

寫入端confirmed為既有IDA函式sub_15EDC、EA0x15F02至0x15F0B：以索引乘0xCA，加5D46h後寫word_33AE2。原始名稱、DS運算元與偏移均保留。正常建造回歸的完整RAM中，DS=1C6Ah、DS:539Eh為3、DS:8542h為5D46h；DS:5D46h每0xCA一筆，+2起為Jamestown、New Amsterdam、Quebec，+1Ah為0／3／1。記錄名稱欄為confirmed；TOONEAR將最近結果的名稱送入STRING0為強推論，未追整個距離規則。這已足夠限定顯示資料角色，不修改距離或建城規則。

私用候選只對上表四個ID／槽位使用既有colonyValue回呼：已驗預設名雙語、自訂名原樣、拒絕玩家強調碼，缺回呼仍整則回原文。其他槽位、部落、產物、引號內輸入回顯與其他模板保持原機制。不更改既有正文／單行辨識、原版執行、存檔、VGA啟用或排版算法；欄位cap／safe仍依每次原字格量測，不外推任意字級。尚未有這四則的正常畫面，不新增shown或宣稱畫面CONFORMED。資料替換契約測試與原有城市代表抽樣完成後再審名稱回呼的READY。

證據位於目標185私用根sea-source-connection-audit/、ida-toonear-callsite.json、ida-toonear-name-pointer.json及sea-colony-name-table.json，指紋依序9b499c65…、89b2856c…、ec794b81…、cbaa2d29…。工具IDA9.4／py312-v1映像4ac62de8…、Go1.26.7、dosgolem82a14b2；地址空間各自標明。初次探針混合正文與單行集合造成FOREST2假歧義，按正式正文優先流程重跑後確認真正的城市變數缺口。

2026-10-10 READY，限定名稱資料回呼：依使用者先接線、最後代表抽樣的既有決定，資料替換與新畫面驗收分開。私用8e22e0743f26677f16695fafc7dabf3c06676e999368d2c7990637d2df164bac通過169Go／go vet無skip，四模板各驗Jamestown、New Amsterdam、Quebec及My Colony，共16筆名稱資料；錯術語污染、缺回呼、玩家強調碼、產物／部落槽位及引號輸入回顯／國名隔離通過。名稱契約d60e38cf7f33d5f9c3f58a2b0f7fe16bdcba526b8a0b5481d96d83fcaa059e61，正常教學13／建造31圖整合adce00c761215d24e38f71ee0dac65d8e10d45a442a221cc6543a0911d078040，逐圖與完整原版／WAV／存檔皆不變。

只授權上述四個既有ID／槽位沿colonyValue處理，原版BODY、其他槽位、source判定與排版不改。既有通用引擎仍逐次量測原版cap與safe，再決定字級；放不下／缺字仍整則原文。此READY不授權任意固定字級或四則未見畫面的幾何，不新增shown、不單獨宣稱四個畫面CONFORMED。正式來源接線後，仍須當前來源契約與已接受城市代表回歸，才可稱名稱資料契約完成；全#55與Land／同文來源審查保持未完成。

正式資料契約審查入口為[四處城市槽位檢查器](../../tools/check_goal185_sea_city_variables.py)。原始資料、記憶體與指令匯出只留目標185私用根；不以來源計數或資料契約PASS充當四個正常畫面。

2026-10-10名稱資料契約完成：正式8e22e074…通過168Go／go vet無skip；目前來源的16名稱資料與槽位隔離通過，正常教學13／建造31／精簡選單15圖與原版完整狀態、WAV及存檔全等。公開資料契約審查601921652f706002776589843594c9df54b612e5bffffa190e9068cca2199322。第99列及六個受影響列PASS，增量普查狀態變化0。四則未正常命中，維持零新增shown與未驗畫面；本節只完成名稱替換接線，不稱四個畫面CONFORMED或完整#55完成。

## 2026-10-09 DRAFT：正常先驅者選取標籤

正常新局存檔前往海岸、確認陸地名稱、下一回合登陸，再點陸上單位，出現`English Pioneers (None)`肖像標籤。`tutorial6-ashore-checkpoint-v2-gui`完整關窗收據記錄`line-no-template`一次，這是海上地圖／共用名稱的實際接線缺口；不是歐洲港口職業標題已驗的同一欄位。

正常輸入SHA-256 `675b7ca34d10663242f35f917d91e7663474969089590e1a57de5142cf5151b9`，正式41107b24…，新登陸存檔COLONY02 SHA-256 `7a04795926057f19ab9913d97f10383dc598d983992870641ea242c2d0111474`。原版及工具指紋沿目標185。英文原文、實際回退與存檔為confirmed；括號內None的資料角色尚未知，不猜成無專長或任務。後續先查原始字格、來源欄位與名稱角色，再依欄位量測及正常選取／取消驗證授權候選。

追加confirmed：只讀unit-caption-observer沿兩份正常輸入重播，完整CPU／RAM／WAV與原GUI相同。Pioneers由0D21:00C6、20bit RAM175478、81442357步起輸出，原字格[114,95,224,104]；Soldiers同入口／RAM175478、101265789步起，字格[109,95,228,104]。兩者大寫字高8、含陰影高9，色68／47／128；肖像白框18×18，分別[93,90,111,108]與[88,90,106,108]，相對文字左上均為(-21,-5)。觀測SHA-256 f5db70349df2202024de8dc007190d7cfb163f8d8fd82b8ffd015f6a8595f0db，原始堆疊只標未分類位元組。

原詞來源為NAMES.TXT的NATIONALITY國籍與UNIT名稱欄。士兵UNIT列位移0x2351、55 bytes，片段16b28c1d614dcfab05b1b33f5c70178c25fd24e3c9ff4a5d1f96c76e1011c48e；前鋒UNIT列0x238A、55 bytes，片段ffde16e9fdefe5e51dfaf76aff613650cbc449dbc57a0f71c61d599434cf7c06。NAMES完整指紋沿本規格。LABELS.TXT完整SHA-256 e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204；None在0xFB／4 bytes，片段dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91；Expert在0x101／6 bytes，片段8b317b0c50ee0926c73cc837c5892d7229648ff9e55d2c5608ce081dde377ee6。定稿譯名為英國、前鋒、士兵、無、專家，不因括號資料角色未知自行改詞。

私用候選可沿既有國籍角色、已驗UNIT名稱回呼與兩個LABELS值解析整列，拒絕未知角色或控制碼。每列須原cap8、9高、68／47／128色與上述相對18×18完整白框；安全區按當次字格外擴，不覆蓋肖像。多列須各自符合，合併安全區不得碰到任何肖像。字級按原字高、行距及實際寬度量測30至20px候選，放不下回原文。兩種正常標籤、取消與字級審查前仍DRAFT。

2026-10-09 READY：私用候選9790e7c8ab22dc2c70b91ea082dcf56936bd8c86d7e393f30041bb57cdb8e952通過164項Go測試與go vet，另16種來源／控制碼／字高／字色／肖像四邊／缺回呼正反例通過。17張正常GUI輸入三側的完整CPU／RAM／WAV／存檔及每點RAM／索引／色盤一致；缺字模逐像素回原文。只改三張標籤安全區，其他14張與肖像完全相同，原先標籤消失後沒有新增殘字。

前鋒safe為[113,94,226,106]、452×48輸出像素；士兵safe為[108,94,230,106]、488×48。兩者由原cap8與9高墨跡選30至20px候選，實際30px、CJK墨跡28px，陰影4px；與原版字首及頂部對齊，最長整句單行完整。四國籍／23個已驗UNIT名稱／兩個LABELS值共184容量投影，使用較窄實測安全區時均30px放入，最長譯文為西班牙人殖民地居民（專家）。投影不當184次正常命中，也不推測其他來源角色。

候選審查unit-caption-candidate-review.json SHA-256 77a21c0abe2f690f720ba6529631e15d8d644fcc4709621682f9f9b07fe2ca61；實際量測1f089b7b40583e509bdf4d22f2710c1962c32fd3ef78f47d0886b304e45d02a4；穩定排序的容量投影a4143fe48d5fc8a45c8d42bf4c8cdad30f6a1d636ade06c603b718cf320c1058。私用入口在目標185證據根的check_unit_caption_candidate.py及unit-caption-candidate/。

據此授權已驗國籍、UNIT名稱與兩個LABELS字面值的肖像標籤覆蓋，None／Expert的遊戲資料意義仍未知，不更改譯詞或原版狀態。正式新GUI與同狀態驗證前不稱CONFORMED。未知國籍來源、名稱、括號值、字格或肖像框維持原文並記錄。

2026-10-09限定CONFORMED：標籤正式6c3f916e…的新11張GUI，前鋒選取、返回、重開與肖像懸停均完整關窗。合併教學6後正式24b7816b…沿同輸入四側重播，GUI逐像素相同，只有三張標籤安全區相對b4fe380e…改變，其餘八張不變。原版CPU／RAM／索引／色盤／WAV／存檔與缺字模回退全等；士兵路徑10張正式回歸也與已驗候選相同。165項Go測試、go vet及目前來源的兩種標籤量測／184組容量／守門反例通過。容量不算正常命中。

入口[單位標籤檢查器](../../tools/check_goal185_unit_caption.py)，正常輸入a25a19fed531fb05a6f51a27426f2e3f139c4632379e59c92152bbe60191a1ff、終點112400000步、RAM5134fd0f4eb562728717319d3515e15021eafd2c918b88659c7810b15cfc5673。原始定位、字級、安全區與未知角色沿前節READY；沒有改原版單位啟用、任務或存檔。#55整體仍須處理精簡ORDERS及來源總審查。

## 2026-10-09 DRAFT：VIEW情境的精簡ORDERS清單

正常讀COLONY02、檢視陸上單位後開ORDERS，原版只列Activate unit、Wait for next unit、Fortify、Sentry、No Orders及Disband Unit六列。unit-orders-activate-v2-gui的同步圖顯示前五列英文，最後一列中文。已驗完整ORDERS清單的來源與驗收保留，這個動態子集是新的實際缺口，不由六個選單／60個來源已建檔當成此情境已接線。

後續先觀測完整六列的原始字格、啟用／停用字色、熱鍵前綴與MENU來源，再依實際已顯示列逐項對應同一原版選單來源；不推算應顯示哪些命令、不改單位操作或遊戲規則。原版與工具指紋沿目標185，尚未授權正式實作。

追加confirmed：unit-orders-activate-v2-gui正常八張輸入，字串層只讀觀測與原版完整CPU／RAM／WAV一致。第一列從同一20bit RAM175684逐字讀取「字元、NUL」，實模式入口0D21:00C6；79172261至79181285步依序構成Activate unit，墨跡[81,13,123,19]、大寫高5，首字色149、其餘68。接著79182153步同基址開始連續字串`~Wait for next unit`，墨跡[81,21,141,27]；`~Fortify`為[81,29,105,35]、`~Sentry`為[81,37,103,43]、`No Orders (~s~p~a~c~e~ bar)`為[81,53,157,59]，四列cap5、全部色8。最後Disband Unit逐字列[81,69,155,75]已能獨立翻譯，原驗收保留。

confirmed根因：dialogRuntime.onRead在第一個無墨跡`~`後轉連續字串，menuPrefixNext要求之前至少兩列；此時只有Activate unit一列，故清除整段。menuPrefixesValid同樣要求兩列。停用列遂落到字串層，帶`~`的原始串未匹配MENU去標記模板。不能只擴充字串詞典就宣稱整份選單完成。

原版封閉黑框逐點量得[76,9,164,78]，正常畫面索引為權威；MENU.TXT SHA-256 5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702，來源為既有譯稿@ORDERS單行。第一列檔案位移0x264／16 bytes，片段b8723a54dd015fa112dce6b6daf799bc69d0340c6fd0e64f840d6aed4ad67468；下一列0x276。Fortify的0x28D／0x299是同文來源，不能由本次字面比對判定選中了哪一份。原版VICEROY、Go1.26.7、dosgolem82a14b2及Cubic11指紋沿本規格。讀取序列81b9697731045446d9c3441c90ef306e4d55463bf0d02022e458f89a5310785a；欄位觀測e51d5fb0e89ce91562f8aa55346a14c1f08fbb7e70c295b7ec9c594b8d6abd1f。只標原始文字／字格／色號confirmed，不新增原版選項規則。

私用候選可在原cap5、首列文字Activate unit、墨跡[81,13,123,19]、68／149色及無墨跡`~`後接W成立時，暫留此一列與後續連續來源。完整收尾仍須逐行模板、真正後續字格、色層、完整原字存活與字型容量守門，不能由首列暫留直接啟用中文。menuPrefixesValid只對同一首列形狀放行第一個前綴；其他一列來源維持舊守門。安全區、基線、最長譯文、停用色、未知來源／錯位／缺字／關框與其他MENU回歸均須量測。正式來源尚未修改，仍DRAFT。

本機證據入口：目標185證據根的orders-compact-string-observer/、orders-compact-strings-observed-v2/及unit-orders-activate-v2-gui/。初次對話框整句觀測未命中，因原串已被辨識器丟棄；改查字串層後取得四列，再沿第一列窄讀取補足，不把未命中當作靜態文字或不可達。

私用首版c80538e4…通過166Go／go vet及四側完整原版狀態，但六列合成後仍line-colors回退，未採用。原因為四個停用列字元較多，runStyle按整段字元數將8色當一般色，68／149的可選列因此落入未證實第三層混色。原版索引與逐字觀測已證實本組一般68、熱鍵149、停用8、無陰影。

下一私用候選只在上述六個文字、字格、cap5、四個單色8列、首尾68／149混色及完整[76,9,164,78]黑框同時成立時，指定這組欄位色層。沒有符合就沿既有色層守門，不全域放寬第三色混用；未知其他啟用組合仍回原文。首版失敗保留，不把原版同狀態PASS稱為畫面修復。

2026-10-09 READY：第二版cc0ec453a4f7490ea0e095fc4b9e6b0e0d84f370c350c8e812d5520e9cb6e3f7通過167Go／go vet，無skip；原始八GUI輸入四側僅一張選單安全區改變。新15正常GUI四側六張選單改變、其餘九張不變，完整CPU／RAM／索引／色盤／WAV／存檔相同，缺字模逐圖回原文；四個停用列均保留原8色。正常懸停、點停用列後關框、兩次Escape取消、重開與啟用皆逐圖確認。其他VIEW的17張正常GUI與目前正式24b7816b…逐圖及原版狀態全等。

安全區[80,12,159,77]為316×260輸出像素，完整落在原版黑框內。原cap5、最小行距8，候選22至15px，實際21px、中文墨跡高19px，合併墨跡相對[6,4,253,248]；各列沿原13／21／29／37／53／69頂對齊，無陰影。最長「不下指令 (space 空白鍵)」單行完整；10000字負例整段回原文。未知文字、來源前綴、位置、字高、第三色、缺熱鍵色、列數、任一框邊或缺字模均回退，不猜其他ORDERS啟用組合。

授權正式menuPrefixNext及menuPrefixesValid只暫留已證實的Activate unit首列加下一個無墨跡`~W`前綴；暫留不授權繪製。完整六列文字／字格／cap／色層及完整黑框成立時，finish才指定一般68、強調149、停用8；逐行來源模板、存活、VGA啟用及容量守門保持。原版資料、命令選擇、停用／取消行為、輸入與存檔不改，也不調整全域等待時間。

候選審查f5ef7e55e6378e54be82282f538bddec4b4e5f1b777e7ebd6486c0b8a8309e0e，量測35cecc614308c691b82b817b12e4717486986a5a39b95adf67714a1c743870e9；本機入口check_orders_compact_candidate.py指紋1f95cea788b4b66c92b78636854bfab531099577384b9b76a1cb1d0b272aa6ed。新輸入db7d78f488e6cefa7583ae7e24d91d852e3b9e8d36e06546cf19f9da323aae5d、終點159400000、RAM7c70eb93f4ab084c4f4d46c9194b0534e9d35efbb88b990bf0317bec427507e0。兩個Fortify同文來源歸屬仍未知，模板鍵只作導覽，不提升兩來源confirmed。

首次新GUI腳本錯把停用列點擊視為保持選單，後續Escape開啟退出確認；該14圖只留診斷。修正後15圖逐張驗原版框線與操作。量測工具起初比正式addDraft多載入LABELS，造成Fortify假歧義；改用正式檔案集合後通過，沒有改產品模板去配合測試。正式採用後仍須新15GUI四側、原始失敗回歸、當前教學6的13圖及建造31圖整合、目前來源審查與矩陣登錄，才限定CONFORMED。

正式驗收入口為[精簡ORDERS檢查器](../../tools/check_goal185_compact_orders.py)，核對目前正式來源、輸入指紋、原版MENU版本及私用check_orders_compact_formal.py。Fortify的同文來源限制保留，其他ORDERS狀態不由本欄位外推。

2026-10-09限定CONFORMED：正式cc0ec453…通過167Go／go vet無skip，新的15正常GUI四側PASS；六張選單只改safe[80,12,159,77]，其餘九張不變。21px、四列原8色、懸停、停用點擊後關框、兩次Escape取消、重開與啟用均逐圖確認，完整原版／WAV／存檔及缺字模回退全等。原始失敗八圖及17VIEW回歸使用相同二進位；當前教學6的13圖與建造31圖整合也逐圖全等。原版字級、基線、最長譯文、失敗回退與未知來源限制沿READY，不增加其他啟用組合。

正式輸入f30ad4a12957619cb73b1f05097fa40705653ac4610b5c695280ab88b2c1b80b，終點162400000、RAM0b4c97499680247f82471fb3619e633eca03023624283baae8c377bfd679495e。最終審查900da1e18dbfd3eaba99b318b8f8a0a835b29b2b91be93e40d7a3b8069bfe595，私用正式檢查器2af66ea68469b2973a0fee60cf096184be03a3f2899bb769dbe505ca1bca5f7b。第98列及四個受影響列PASS，98列增量普查狀態變化0；五個MENU來源由歷史轉可重驗，Fortify兩個同文來源不新增信用。缺原版SKIP77及錯MENU版本拒絕已驗。完整#55來源審查仍未完成，不由本節關閉Issue。

## 2026-10-09 DRAFT：TUTORIAL6的貨物、城市與母港變數

來源檔GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`，正文檔案位移`0x136C2`、189 bytes、片段SHA-256 `70e89dc8d935a8f6adc0acaf411d22f8518e15007fe3b2678933ac2eb5afd71f`。原文描述數量與貨物存放在 `%STRING1`，船駛入同一名稱後載貨，運回歐洲的 `%STRING2` 出售。

confirmed為原文及占位符；強推論為 `%STRING0` 貨物、兩次 `%STRING1` 殖民地、`%STRING2` 母港的角色。現行match只將TUTORIAL7／12／15的城市變數送入城市回呼，TUTORIAL6仍走一般術語，因此已知Jamestown預設名及玩家名均無專屬接線。先做私用角色候選，僅TUTORIAL6的 `%STRING1` 使用同一已驗城市回呼，貨物與母港沿原有術語來源，缺來源回原文；尚未授權正式程式。

IDA9.4沿既有VICEROY資料庫的一次性複本找到TUTORIAL6標記：EXE檔案位移`0x1E867`、IDA MZ線性EA `0x2C467`，無直接xref。這只證實標記定位，不證實執行時producer。VICEROY SHA-256 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`；私用`ida-tutorial-markers.json` SHA-256 `610bae6d2a9e482419c9b0c0192e91605079d4d86d7f40573a515aa364398ddd`，schema `colonization-tutorial-markers/1`、526個函式。正常事件、欄位字級與同狀態畫面尚待驗證，不從xref缺項推論不可達。

私用候選`2915ea128d7e29cdf4c47f5114e72086697b27d8739a69ebf504da71b213b1d1`通過161項Go測試與go vet，無skip。TUTORIAL6兩次城市占位符均使用同回呼，Jamestown雙語、自訂My Colony原樣、一般術語污染及缺回呼回退已驗。另以原始位移讀取help與corpus兩份清冊，對全部21教學逐則展開文字及數字占位符，實際match均取得對應中文；私用`TestAllTutorialVariableBindings`與`tutorial-all-variables.json`保存審查。這是來源接線測試，未新增正常命中，尚未READY。

2026-10-09 READY，限定名稱資料回呼：依使用者先完成譯文與接線、最後代表性正常抽樣的決定，將資料替換契約與未抽樣畫面分開。原始189 bytes明示兩次同一STRING1為貨物所在、船駛入的名稱；既有已驗城市來源會對預設名雙語顯示、自訂名原樣保留，沒有猜補原版規則或producer。只授權TUTORIAL6的STRING1沿同回呼處理，不改正文辨識、原版執行、HELP幾何、字級選擇或VGA啟用條件。

原有HELP引擎仍從當次原版字格量測cap、基線、框寬高，再由既有字模重排；缺回呼、控制碼、缺字模或放不下仍完整回原文。兩次名稱、貨物與母港的真實來源模板測試及21教學逐變數審查作此資料契約證據，正常抽樣沿已驗教學7／12／15名稱欄位保留。此節不把TUTORIAL6列為正常命中、不增加shown，也不單獨宣稱其畫面CONFORMED；整體#61仍須目前來源及原有各範圍的完整審查。

2026-10-09限定CONFORMED：從既有正常1507存檔續走原版回合，在1508年取得100 Furs、兩次Jamestown及London的教學6。正式24b7816beef942ae685fa367204ddae88454aa65073be5c38346016cafa24a6d的新13張正常GUI四側PASS，只有一張提示安全區改變，另外12張與修正前相同；完整CPU／RAM／索引／色盤／WAV／存檔與缺字模回退全等。這補足前節未命中的限制，不重寫早期失敗歷史。

原版印字實模式0D21:00C6、20bit RAM174958、142330700步起；safe[52,113,271,157]。原文色68／149的墨跡[54,116,260,154]，四行各8px、行距10px。HELP排版依原cap8量測30至20px候選，實際30px，安全區876×176輸出像素；雙語Jamestown譯文墨跡相對[6,2,865,116]，My Colony為[6,4,858,76]，均完整。中文字頂內距4px，拉丁上伸部最小2px，陰影4px，沿既有基線排版。10000字容量負例回原文；不外推未見長城名的原版安全區。

目前來源的全部21教學逐變數審查與貨物／城市／母港隔離通過，來源變數輸出37b1c775a1c1fc375c8c99edcc094cdc247845ff51afcbc65adb1e4ed553b1c9；教學6版面221942aedae3a207c4f4ef6a9570b8a77dc2644a54b99907b513719fde353c74。入口[貨物教學檢查器](../../tools/check_goal185_tutorial_cargo.py)，本機unit-caption-city-connection-audit/及tutorial6-current-formal-*保存重生證據。新輸入d2b67d97ad2265a5e2942af1aea89132c6f24336549f9e752d807ba18a2c1790、終點148400000、RAMc3424de3f3a30798b93b3c14c0da3e7ae4090bd1c1fd0b198adc3d83ac20f443。#61另由完整審查確認開局、存讀、版畫及既有代表抽樣，不把21來源測試當21次新GUI。

## 2026-10-09 DRAFT：15項建造清單分段回退

正常COLONY00返航、木匠到港、關閉TUTORIAL15／7，再處理Adam Smith加入議會的通知、版畫及百科後，進Jamestown開建造面板。`population-three-build-gui`完整正常輸入取得15項可見清單，標題中文、項目英文。此例不同於已驗12項清單；不因已完成標題保留或逐項有譯稿而視為完成。

confirmed：當前正式c30275a8…，標題由實模式`0D21:00C6`、執行時20bit RAM175128，286995354步輸出；安全區`[74,33,154,42]`、21px。Down後清單被觀測成兩段：294812307步起的前五列止於WAREHOUSE，safe`[78,43,241,83]`；294924653步起的後段從`(80 Hammers)`開始，safe`[78,75,241,163]`。初開另有從`ools)`開始的`line-no-template`。這證實現行段落觀測不穩定，尚未證實是逾時、來源位址切換或逐列連續字串轉換。

下一步只讀記錄原始字元、字格、來源基址與各段起訖。先定位分段原因，再決定限定串接方式；不全域延長dialogGap、不猜15項為固定長度，不修改原版可建項目或捲動行為。來源／工具指紋沿本規格與目標185；正常第三居民是否已加入仍需額外狀態證據。

追加confirmed：只讀onRead記錄證實兩次都因20,000步門檻切斷同一來源。初開287277121步讀到Tools的`T`，287313979步才讀同基址+1的NUL，相隔36,858步；舊run的readPos為657奇數，finish直接拒絕，接下來從`ools)`重建。Down時WAREHOUSE與成本之間相隔38,210步，字元來源基址仍為175590。這兩次中斷均未換來源或字格，不能當作兩份清單。

私用候選可在已驗建造標題、當次原版標題快照完整及清單首列、字格與列距成立時，將清單視為同一來源事務，直到來源改變或既有標題身份時效到期。讀取與Update收尾必須使用同一限定守門；字串、畫布、字級或標題失效立即回原文。不能全域改dialogGap，也不能只將20,000改成一個剛好通過的數字。仍須正常導航、取消與舊12項回歸後才READY。

2026-10-09 READY：第二版私用候選`3b0bf4e3e3aaf9c7857a164b535b7ae0fbe509ecb9fbf115f9273231ae60ad27`通過160項Go測試與go vet，另14種來源、快照、標題、字級、字色、位置及時序守門正反例通過。29張正常GUI輸入三側、原GUI逐像素差分與14張舊12項清單回歸PASS。只改15項清單初開及Down兩張的清單／標題安全區，其他27張與區外不變，取消清除正常；完整原版CPU／RAM／WAV／存檔及每個取樣索引、色盤一致。審查入口為目標185證據根的`check_build_transaction_candidate.py`與`build-transaction-v2-review.json`。

只讀守門觀測又證實：初開36,858步停頓時標題仍為waiting-screen，VGA啟用後才產生的afterSafe尚不存在。候選因此在建造標題收尾時另存只讀來源安全區快照，供讀取事務識別；不將它當成已顯示到VGA，不放寬原有啟用閘門。首次及後續來源事務各自上限為既有2M步，仍要求有效標題生命週期、相同來源快照、首列`(No Production)`、x79至80、原版cap5、每列8邏輯像素、68／149／8色及原版框內界。來源位址改變仍立即收尾。

15項安全區`[78,43,241,163]`，標題`[74,33,154,42]`；原版大寫墨跡高5、含小寫最長墨跡高6、列距8。沿欄位候選22至15px實際選21px，中文基線與每列頂對齊，成本右對齊，所有15項最長完整譯文與雙成本均無裁切。導航標題保留只接受同安全區、同完整列組、相同列數及仍完整的原版標題快照，依當次高度計算，舊12項條件不退步。

原正常輸入SHA-256 `efdc0d9188f7d715befa6e9c6a1deecec8470c778f820eb035b1c9248e398741`，終點314000000步、RAM `0ebe14d094bb60bc68eb4cef1d8041ac179cf41d67d8b532bf1794c1713a4bd7`；字格觀測SHA-256 `e4d31c0f22cf83f4ac748255d2f63b44d782ae223f55d03655a868c928c9e725`，逐讀觀測 `d33f23b60a259241dbb725e2f9ede23bba7f2f6205ce2686991ffd9353112e13`。據此授權限定建造來源事務與標題保留；正式新GUI、同狀態回退及回歸前不稱CONFORMED，也不將15項全部可見當成真正超出視窗的捲動。

2026-10-09限定CONFORMED：正式`41107b24535321a35da898ccff5a49843a456d97e08f306a71f8b59e741715b2`、161項Go測試與go vet無skip。新31張正常GUI包括完整15項初開、兩次Down、Up及Escape；四側完整CPU／RAM／WAV／存檔及每個取樣RAM／索引／色盤一致，缺字模回原文，正常GUI與中文重播逐像素一致。新GUI只改三張導航畫面的核准標題／清單區，其他28張不變；新輸入的初開舊程式亦未分段，因此另用原始失敗29張輸入重播正式程式，確認兩張原始錯誤清單修復、其他27張不變。舊12項14張正常清單回歸逐像素相同。

公開入口[check_goal185_build_transaction.py](../../tools/check_goal185_build_transaction.py)，正式審查`build-transaction-formal-review.json` SHA-256 `ba5e258cbed9929c305d1da5f7d73de8452dd16ac04c63548ccb61ff68414013`。新輸入`df243a8d39ff39edae3f2ffb4a1afc48163dbf5a98b619c8ab013f411cc6d99f`，終點344400000步、RAM `e1ac9caf5b670d87c2420e175bb76e4ec4e982b10548ba0e9cdcccb997b703e1`。適配器來源SHA-256 `b51b76ca2e2ce24ae7d3fb063a01d9f4002c6aefd0aa86e62bb49dd20b075439`，隔離dosgolem82a14b2不變。原版15項字級21px、矩形與原始資料維持READY契約；第三居民及超出視窗的實際捲動仍未由本例證明，#56維持OPEN。

## 2026-10-09 DRAFT：TUTORIAL15到港居民的城市變數

正常出航存檔讀回、三回合後G選Jamestown並等候，原版出現New colonists have arrived in Jamestown教學。population-harbor-continue-gui完整關窗收據記錄152460000步variable-without-term，五行[52,106]起，模板已載入卻整段英文。來源實際為GAME.TXT:@TUTORIAL15，原文兩次{%STRING0}均為當前Jamestown，非TUTORIAL12。

既有城市回呼已供TUTORIAL12使用；候選只讓TUTORIAL15的%STRING0使用同回呼，預設名雙語、玩家自訂名原樣，拒絕強調碼。來源GAME.TXT完整SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，VICEROY a17ed64c…；工具與位址基準沿目標185，回退位置是執行時事件，不是EXE偏移。

這是#61新正常情境揭露的接線缺口，先前21模板載入審查不足以證明所有變數已處理。原有正常驗收保留，整體Goal仍active，修復與此則正常輸入驗證完成前不據舊完成旗標略過。TUTORIAL6／7的城市變數另有來源語意，尚未以本節授權擴張。

追加 confirmed：`population-join-after-help-gui` 在同一返航流程按 B 後，實際輸出 `Jamestown is growing rapidly`，原因同為 `variable-without-term`。原始來源為 `GAME.TXT:@TUTORIAL7`，檔案位移 `0x1379B`、551 bytes，片段 SHA-256 `ecd207f1c7e076bb6cf73c6b9fd0069edb2d4c77c644c620774b2cce087d662a`。這一則的 `%STRING0` 亦為當前殖民地名稱。私用候選可對 TUTORIAL7 與 TUTORIAL15 各自的 `%STRING0` 測試既有城市回呼；不能將一般術語當成城市，也不據此開放 TUTORIAL6 的其他變數。兩則正常輸入、缺回呼與不安全名稱回退、字級及安全區驗證完成前仍為 DRAFT。

2026-10-09 READY：私用候選 `4e0e9058473fa616b001e38e2418b3a7aa7103fd3aa3cc11862c013f0b17f575` 通過158項Go測試與go vet，無skip。真實GAME.TXT與help清冊驗證TUTORIAL7／12／15的預設名、自訂名、一般術語污染、缺回呼及強調碼拒絕。正常返航17張GUI輸入的中文、原文、缺字模與正式基準四側，完整CPU／RAM／原始WAV／存檔與每個索引畫面、色盤相同。只有兩張提示的各自安全區改變，其餘15張與區外逐像素不變；缺字模完整回原文。

原版實模式印字入口 `0D21:00C6`，TUTORIAL7執行時20bit RAM175056、174859717步；TUTORIAL15 RAM175218、150610632步。安全區分別 `[50,32,269,166]` 與 `[50,103,269,157]`；原版可見字高7邏輯像素，沿既有help候選30至20px逐欄量測，這兩則含雙語Jamestown完整譯文均選30px、行距40px，墨跡與原版左側及首行對齊，長文折行。目視無裁切，超出安全區或缺字模仍回原文。輸入SHA-256 `da34e364c9077a8377a69cc7211a2a43d13c6fda7d726bc2013cd2ffc538d666`，終點199200000步、RAM `e419ba7d47e71170e385d0214a6934634740bd9694589c2731d2bb7628cd8a3b`。私用審查入口為目標185證據根的 `check_tutorial_city_candidate.py` 與 `tutorial-city-candidate-review.json`。

據此只授權TUTORIAL7／15的 `%STRING0` 使用已驗城市顯示回呼。正式新GUI及同狀態驗證前不稱CONFORMED；TUTORIAL6的城市變數仍另列未完成，不據兩則修復重新關閉完整#61。

2026-10-09限定CONFORMED：正式 `c30275a86d256dbb9cc1ccb424ebb50096e5a751b64af9ad99522608f21c720d` 通過160項Go測試與go vet，無skip。新17張正常GUI包含到港提示、成長提示、各自關閉與返回地圖；中文、原文、缺字模及舊正式四側完整CPU／RAM／WAV／存檔、每個取樣RAM／索引／色盤一致。只有兩張提示各自安全區改變，其他15張及區外不變；正式GUI與中文重播逐像素相同，已核對實際frame_step。既有TUTORIAL12真實語料城市回呼與自訂名、缺回呼、強調碼回退均保留。

公開入口[check_goal185_tutorial_cities.py](../../tools/check_goal185_tutorial_cities.py)，審查 `tutorial-city-formal-review.json` SHA-256 `1965c12686f82aa83d418fb66a85ee67cbf758c2ac36d7a970597dfc2b57e8d2`。新輸入SHA-256 `1ab38904541829e10363fb497678798a31cad09db2c6b18b7a40f7e4749ae0d7`，終點206200000步、RAM `7351c5c86d5f6def40f869b87bd080c4accd4234fe6231a7cd38ed441b9414e3`。來源RAM與安全區沿READY，正式來源步數分別181316076與155342525。#61維持OPEN；本節不聲稱TUTORIAL6或所有教學局勢完成。

## 2026-10-09 DRAFT：G單一母港列

正常讀回已驗新局COLONY00，在尚未建立殖民地時按G，原版只有London (England)一列；標題中文，該列仍英文，既有兩列清單守門不接受此形狀。六張正常GUI、三側与只讀觀測的完整原版、WAV与存檔相同，沒有注入城市或改命名。

confirmed：原版0D21:00C6，單列RAM175470、58296061起／58410000步收尾，face[77,103,155,112]、cap8、68／47／128。標題來源GAME.TXT:0x1CBB，safe[66,88,176,100]、30px、waiting-screen，完成58296061步；此safe原版像素SHA-256243bbad99dab8e3b061f63862dd8765c1b1b24a364c674fabf47b1aab849c2af与既有兩列相同，位置上移下移另核對。one-port-observer/fields.jsonl SHA-2560cb8012f933f5a10ce751c5961843b1788af2f045cfac2191fe29c7c8ece4a63；输入2eb0b84ceeba4fa8d48c73902f8015a9660e0033f156d7df9bb79feba6a19876，終點74800000、RAMa24fa07d78e1e880f549c5a064d99d92508a540925cd4ffc8edebcd2849740a9。原版VICEROY／NAMES、dosgolem82a14b2、Go1.26.7、Cubic11与image指紋沿本規格。

候選只在單列cap8／x77／y103、原標題身份／safe／30px／原像素与2M步时效成立時，將完整「母港 (國名)」按已驗NAMES:@HOMEPORT四名与@COUNTRY四名角色解析，各自以既有詞典翻譯；不以任意詞典詞或玩家城名借用母港角色。新增country角色只從完整NAMES SHA與區塊驗證取得，不推定國名／母港對應或修改遊戲規則。安全區与字級先量測，缺字模／未知角色／混色／其他行數或位置原文回退，原型与兩列回歸前不READY。

2026-10-09 READY：原型90e73148d49c4da8b9e9f309571fedb9916af5fa8216789bb8256573d0eaa292，六張正常GUI输入／三側与完整原版、每點索引／色盤、WAV、存檔、回退一致。只改單列一張safe[76,102,157,114]，其他五圖不變，Escape清除。原版cap8／9px含陰影，中文候選30～20px，實際30px、CJK28px墨跡与原版行距12／字首對齊；「倫敦（英國）」單行完整清楚。十一個角色／位置／字級／混色／時效／標題／像素／行數／缺查譯條件拒絕，四母港／四國名的16容量投影均20～30px可用，不當正常配對或命中。

原型審查791cd52883dce81888af9ee518b2d3fcf3d47643f44ea5b4e062c98ed5d89338，角色容量2023fb4d1dd0800b1c24d214716f3c125b0738f28ecddbb2396c310936d9ea01。兩列可選10GUI与灰色／返歐14GUI原版、像素、音訊、存檔回歸全等。據此授權單列母港來源角色回呼与此形狀字格守門，既有兩列處理不放寬；新正式GUI、懸停／取消与四側前不CONFORMED。其他行數、玩家城名与多城市清單仍按#55完整範圍處理。

2026-10-09限定CONFORMED：正式70462b912fee1c1277c34c5200df7299d00991ab852a769ac8c673b2f140c79a、156Go／go vet無skip。新九張正常GUI包含單列G、懸停、取消、重開与重取消；四側完整原版、每點索引／色盤、WAV、存檔与回退一致。只改三張單列safe[76,102,157,114]，其他六圖与區外不變，實際30px，已目視清楚。兩列可選／灰色及返歐24圖回歸全等；新增country角色后已完成百科164正文／19索引接線与完整#57回歸仍PASS。

正式入口[check_goal185_one_port.py](../../tools/check_goal185_one_port.py)，摘要5bdefe4711c6ec2389e8f375dc6d7fefd3f66a7f119b587bae892351c8dddfe3。輸入787b2ebcea066a62a729d9f8a3285ea83d4b580ab2700e2e81506e25010d21d2，終點107800000、RAM0175da9a17f7cade0bb254d7f49672b26a9ee45fff3281e2497aacf3597cf297；兩次RAM175470源事件與字格一致。第87矩陣单列PASS，摘要acd65ea7c955f71fb9ac3436619cbdbab4c4927585061da33957f30c9c6ed30d。報告仍保存前86列合併結果待下一批，不将四母港16容量投影或其他行数算正常命中。

## 2026-10-09 DRAFT：建造清單標題被導航重畫撤銷

正常COLONY03兩居民讀檔、View進城、開建造面板，再點更換按鈕，12項清單已有中文。清單初開的「Select An Item To Build」標題中文，按Down後標題回英文；Escape取消後面板保持原版。這是顯示保留缺口，不能由12項已翻譯或一次首屏PASS判定建造導航／捲動完成。

confirmed：初始存檔d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77；正常輸入4284aa84e98c749b3eff5d030e46769a7405e0079b34ec9031afaf0c1df392d3、十張GUI，終點125200000步、RAMd2f6489ae49bf148e614fd8bc1cb4029d90bdc94e7a8cc72b97d5ce7fe96f0b4。原版標題由實模式0D21:00C6、20bitRAM175132於98384560步進入STRING:line，safe[74,45,154,54]、21px，98835001步active；107923065步原因superseded-by-new-dialog撤銷。標題原始LABELS.TXT:@CTITLE:0xBC6，片段SHA-256b588ce2ef1bba9ff638c11234af3b95ee38681bbc81f211e0baf8c3f7115c719，譯文「請選擇要建造的項目」已有。檔案、工具、字型指紋沿本規格，dosgolem82a14b2、Go1.26.7、前端a1d43865…。

下一步只讀觀測導航重畫的完整列組、標題當前原版像素與生命週期。若仍可見且與新清單不重疊，才依原版身份與像素建立限定保留原型；不延長通用逾時或全域保留STRING:line。正常取消／新GUI與四側前不READY，正式目前未修復。

追加confirmed：只讀build-lifecycle-observer沿同輸入取得三次來源轉換。初開完整12列safe[78,55,241,151]、21px；Down後同12列與安全區重印，舊清單已expired，前一標題仍active且afterSafe720bytes逐位元組等於目前原版標題區。標題區SHA-25675c2266d34b564291c468cbd19682f11b887ca2deb220f83e92e2771ff4f5cbd，兩者不重疊。dialogs.jsonl SHA-25613bea47f919c9b66e5ee76947b06e18acd02ac58689e2cdbc3bfc2229d728ca6，觀測完整原版、音訊及存檔與凍結基準一致。

候選只在prev為已驗單項建造標題、相同safe／21px、active且原版標題快照完整，cur與next都是STRING:line+list、同safe[78,55,241,151]與相同完整12列時保留標題。cur可已因清單重畫expired，但身份與完整items仍必須一致。值仍由既有完整模板／詞典翻譯；其他標題、缺列、換序、位移、像素變化與重疊回原文。先做私用原型與錯條件負例，不全域延長時間。

2026-10-09 READY：兩欄原型005a3aef122c99748b447a17098eb831f299968df74138e65513b7a8bf9de5f0沿十張正常GUI輸入／三側完整原版、每點索引／色盤、WAV及存檔一致。導航後標題保留21px；只在同完整12列重印、原版720byte標題快照仍完整時保留，十三種錯身份／位置／尺寸／來源快照／行數／順序／重疊／時序負例通過。原型只改標題一張及貨車面板可見區四張，其他六圖與所有選項區不變，Escape後無標題殘字。已目視清楚。

審查672b47b426d793a281e41ab99f0b0cbf3122dd6257ad990ba266cc4e1e3f15e2，輸入與原版終點沿DRAFT。據此授權此同一完整建造清單的來源限定保留，不能把13張其他清單或不同可建項目列數都算完成；新正式GUI／多次導航／取消／四側與既有對話框回歸前不称CONFORMED。其他建造名与列組的接線仍按原Issue繼續審查。

2026-10-09限定CONFORMED：正式89e63cae4628d85ecf6febef5a386614837c5ef327772f26a485eeed8dc50fd5、156Go／go vet無skip。新14GUI／四側包含開建造清單、兩次Down、Up返回、11次Down到末列、Escape取消与返回世界。完整原版、每點索引／色盤、WAV与存檔一致；7圖僅兩核准區改變，其餘7圖完全相同，選項區不變，取消無新增殘字。碼頭12圖、職業14圖、地圖7圖回歸通過；標題維持21px、原版720byte快照守門，不延長全域逾時。

正式入口[check_goal185_build_lifecycle.py](../../tools/check_goal185_build_lifecycle.py)，摘要1174a5e90b9cc70efee65dc5cd9d90d0eb74306cfaccf17951981f7a113aeea8。輸入4580f33158a01847d3a563162e0386c51b3684b37f09aeb44c249a18ae050258，終點182000000步、RAM019c27566ad9ef95e860917a5517fa1dc1789ba915ef11cc91097fbe5b4d5892。矩陣第85列单列PASS，摘要ac037788b27dc59109476f51ced5a931e52718dc5cf9c5c9605948ceb0a75cd5；普查保存前84列合併結果待下一批。這證明同一可見12列導航保留，未驗真正長清單捲動或其他列組，不由本例關閉完整#56。

## 2026-10-09 DRAFT：地圖載入的居中標題

正常主選單美洲開局，選地圖編輯器地圖後到檔名輸入。正文、兩選項與AMER2.MP檔名維持原版，只有「Select Map File to Load」標題未中文化。既有GAME.TXT:0x2C8譯稿是「^^選擇要載入的地圖檔」，addDraft排除含^的單行，因此這筆從未進正式逐行／居中模板；不能全域刪掉控制碼或加入未驗居中列。

confirmed：原版GAME.TXT SHA-25667a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，片段0x2C8／25bytes SHA-256ad915d9da6889a4865c513ae4f25420af80af59cd87e4387f727236d671ce56b。實模式印字入口0D21:00C6、20bit實體RAM174110，52114132步；單行face[108,89,212,98]、cap8、色68／47／128，runStyle68／149／47。原版、工具、字型沿本規格及自訂頁規格038，dosgolem82a14b2、Go1.26.7、固定hr-go-ebiten1430a2cf…。字格觀測map-title-observer/fields.jsonl SHA-2563470c3197505369ff2e21f67e24193067a1e52437f9dea315ce2f519c097b3d7；觀測重播完整原版與正常GUI一致。

正常輸入efb4b3b7efc7b6b3c72d58ce2847c6f6777c690a7a23f96089d43e24ad40952b，終點62200000步、RAMd3cd41fe940b1d138f5df05804c978f9bc2ff951453c92bfcdfb5fe75a64d108。美洲原版地圖與此地圖檔選擇共七張GUI／兩路各三側，只有此標題仍英文，私用start-america-baseline-review.json保留缺口，不登錄成新完成。

下一個原型只載入已驗0x2C8的單行居中模板，原文與譯文的^^按既有居中語意處理；依cap8與安全矩形量測候選字級、基線與最長譯值。限制此標題的字格／色層與原版框，檔名繼續原樣；缺譯、來源變更、超界或其他^列回原文。原型及正常取消／四側前不升READY，正式程式目前不含此修正。

2026-10-09 READY：四張正常GUI輸入／三側原型完整原版、每點索引／色盤、WAV、存檔及回退一致，只改最後標題safe[106,87,214,100]，其他三圖及AMER2.MP輸入欄逐像素不變。原版cap8、含陰影墨跡高9邏輯像素；安全區432×52、行距40px，現有30～20px圖集與實際最長整句量得30px、CJK墨跡28px，陰影47、一般68。中文整句單行置中，與原版框及標題帶對齊，已目視。來源、欄位、八種錯字格／字高／字色／行數負例通過。

原型878437f21c765123cdf90e2dd30f439bf835ed50e8a8132751a93ee7a964f58e，審查31f58a8b269293bd8b9b04ef7c6be7114afdd2746f31fafad601375def00d180，量測ea8622ee4691e25e24697611ff2b2a885b7e72273f2cb02995c878dd37a8dc8c；輸入及原版終點沿DRAFT。據此授權唯一已驗0x2C8／25bytes居中模板及單行字格守門，其餘含^譯稿排除不變，檔名原樣。正式新GUI／正常取消、四側及其他標題回歸前不稱CONFORMED。

2026-10-09限定CONFORMED：正式a1d43865238a63e4658aee2d5bd37daa64b655c0619b7d0e4930c74109969567、155Go／go vet無skip，新正常七張GUI包含開地圖檔名框、Escape取消回主選單、重新選美洲原版地圖至難度。四側完整原版、每點索引／色盤、WAV與存檔全等；只改地圖標題safe[106,87,214,100]，AMER2.MP與其他六圖不變，取消／重入無殘字。自訂頁六張回歸也全等；30px居中已目視。

入口[check_goal185_map_title.py](../../tools/check_goal185_map_title.py)，摘要7df30ac21c0f63715696c9975affc15c5970e50302350ba7af8ff251021d4bb2。輸入fb4cc37ef9f2bf7accf8234c4e9708b8d13e69ba0bed67bd74c558a5d2720181，終點92600000步、RAM69a82936be1ce23b7380fdce4f6c80d7ad3b805596817ce633d6be2bd25e134c。第84矩陣列單列PASS，摘要fbb54b104e2d9a92b6bcf5d4b668d28fb8abcfadeda8449d28241f526a494cb2，普查合併重產中。本節只完成唯一居中標題，其他^列及完整#61範圍不由本例推定。

## 2026-10-09 DRAFT：職業標題的兩行模板分流

正常兩居民COLONY03先選政治家，再改派農夫或甘蔗種植者。農夫標題只有一行，現行字串層已顯示中文；甘蔗標題兩行，因現行守門限定政治家原文而回原文。兩者整句查譯均成功，沒有新增譯文。候選改用完整職業標題格式分流，同時維持兩行位置、cap5、68單色與既有整句查譯、原版黑框及容量守門。

confirmed：原版印字入口0D21:00C6；甘蔗標題20bit實體RAM174818、113666014步。第一行「Select a Profession for Veteran Soldiers(Sugar」face[67,19,230,25]，第二行「Planter):」face[67,25,97,31]，cap5，runStyle68／68／0。政治家與甘蔗兩行的字首、行距與框內標題區相同，折行點隨字寬改變。農夫單行face[67,22,242,28]、RAM174818；仍沿既有字串層，不進兩行候選。原版VICEROY.EXE、GAME.TXT、NAMES.TXT及字型雜湊沿前節，工具dosgolem82a14b2、Go1.26.7、固定hr-go-ebiten映像1430a2cf…。

私用正常入口play_profession_variants_v2.py／v3.py逐次點擊後確認實際原版標題才選任，沒有注入職業或單位。v3來源fields.jsonl SHA-256 dc5b30ddb227a44b225c9b24a2c5b95357f781e743f7a412fd1c71f250007b40，輸入d426783ee348a716496b99e39bed0a08d4715f315aae2c8f9f3eb1ce6f568ec1，終點142000000步、RAM2841ea369fd65a106353a9909d6def262beda2f4f2e4cf734cd3b95175661fde。第一份v1選單被連續點擊略過，保留為探勘，不能算職業標題驗收。

候選只接受兩行、x67、y19／25、墨跡底25／31、右界不超254、每行cap5且只有68色。整句須符合既有「Select a Profession for 單位(職業):」格式，兩個值非空且括號完整；仍由已驗原文指紋的整則profession-title模板與詞典查譯。未知值、缺字、混色、移位、三行及安全區不足回原文。安全區由既有黑框掃描，不硬寫新的字級；先量測兩個已觀測折行及最長候選，再做三側原型與單行回歸，通過前不升READY。

2026-10-09 READY：原型141c2a48720edf3fbd36ff9988d51b43951caacae9d0829091f48ebf4a136adc沿v3的12張正常GUI輸入完成三側重播；完整原版、各點索引／色盤、WAV、存檔與回退一致。相對觀測前端，只有甘蔗標題一張安全區[65,16,254,33]改變，其他11張及原選項區不變。兩個實際折行均22px，甘蔗中文整句單行清楚，正常取消無新增殘字。農夫單行另已在正常v2顯示中文，維持既有路徑。

原型17種格式／行數／位置／邊界／cap／色層守門與未知值回退通過；三個已觀測整句在756×68輸出安全區依cap5量得22px。量測JSON中的ink是字模畫布矩形，不能當作非零墨跡大小。原型審查摘要fc2d22232e9acf9c70d5c8ffa72c4576716418f0bedbd3f9ebd5de465be0d14b，量測b85a0d079ba5be7cc05815df5164d8cf3cf9500af121bc410327a50ba6565d47；完整指紋與終點沿DRAFT。首次原型測試錯用排版方法名及單詞lookup介面，已改為正式dialogMasks與translate並於同一映像乾淨通過，沒有為測試改正式守門。

據此授權兩行完整職業標題按本節幾何與來源模板分流；不再把單一單位／職業原文寫成唯一允許值。正式仍依原版字高、黑框與實際中文容量選字級，未驗行數及欄位保持原文。新正常GUI／四側與已驗政治家、農夫單行回歸前不稱CONFORMED；模板接線不等於所有職業组合均有原版正常命中。

2026-10-09限定CONFORMED：正式7236f28bd489acbe80b25116c0aef9640317dc000bc8884d6954e3d705520008、154Go與go vet、無skip。新14GUI包含正常兩居民城市的政治家、甘蔗、農夫改派、取消及返回世界；四側完整原版、全部取樣索引／色盤、WAV、存檔及回退全等。相對上一正式前端只改甘蔗標題一張safe[65,16,254,33]，其他13張及選項區不變。兩個實際折行皆22px，已目視；政治家9張與農夫單行12張回歸逐像素相同。

正式入口[check_goal185_profession_family.py](../../tools/check_goal185_profession_family.py)，摘要250419ddf9e8f131d107bdae4a78ced7145e6960cf429ed3d5d78253b8ed1309。輸入c23d2c88fa9fdde4e07d917d972a3bdc8a21faafdfe00d0e3cc09b3324ec0878，終點161800000步、RAMe407ab2bc6dac6225b55fab08fb957b6fbc9af464df89a3292a7e96a9576ba2c。矩陣第81列獨立PASS，守門摘要20887dda88a6e4effdc9660845a6982da08f50312e56324d20fbdebd70547dbf；合併普查待重產。完整兩行模板已接，其他職業組合未抽樣與三行／其他位置拒絕分開，不外推完整Issue完成。

## 2026-10-09 DRAFT：兩行職業標題

正常COLONY03冷啟動、View進Jamestown、兩次點城內駐軍後，原版標題為「Select a Profession for Veteran Soldiers(Statesman):」。譯文與整則profession-title模板已接，整則查譯成功為「為老手級士兵選擇職業（目前：政治家）：」；逐行引擎把兩個折行當成兩個選項，各行不能單獨匹配而回原文。這是標題折行接線問題，不能因此宣稱老手或政治家缺譯。

confirmed：來源實模式印字入口0D21:00C6、20bit實體RAM174822，87862472步收尾；兩行face[67,19,176,25]／[67,25,140,31]、cap5，只有68色，無原版陰影，runStyle 68／68／0。原版、工具與NAMES指紋沿本規格既有契約，私用profession-title-observer/fields.jsonl及title-87862472.idx由正常population-double-select-gui輸入取得，完整RAM2857e83ebffb139b1eefe3e932627ec7ee3c8b6431899b086616fc9be469c2fb。

候選只在該兩行字格／cap／色／完整標題格式與整則現有查譯成功時，改走既有對話框段落排版，不把兩行當選項；原版黑框掃描與安全區／字模容量仍守門。候選字級依cap5沿既有dialogSizes求得，不預設30px，不改譯稿／圖集／原版資料。原型須核對字級、安全區、選項區不變、原版／音訊／存檔及回退、錯來源／字格／色／格式反例後才READY。

2026-10-09 READY：職業標題原型七張正常GUI輸入／三側與只讀觀測的原版CPU／RAM／VGA、每點索引／色盤、WAV及存檔一致。只改最後一張兩行標題安全區[65,16,254,33]，其餘六張及全部選項像素不變；缺字模回原文。原版cap5、兩行無陰影，候選字級依既有對話框規則量測為22px，中文墨跡與原版字首／框內距一致，長譯文在同一標題區單行完整，已目視清楚。错cap／位置／標題內容／一般色／混色／陰影／強調色／行數反例均拒絕。

原型483683611f31b2c81bc03e447f756d8b0ce32c7ad56bcb7c8b2eee619fa70c98，輸入6987ace2052db71ce50bdfbab9f4129012f82af43455c551f98df7ac399d3ec2；私用profession-title-candidate-review.json保存完整端點與差異。據此授權此已觀測兩行標題接正式段落路徑，文字與圖集不變；正式新GUI／取消及四側前不稱CONFORMED。其他折行標題仍須來源與欄位審查，不以本例縮小#56範圍。

兩行職業標題限定CONFORMED：正式4cf2b7d30672794cdfc3e2c924f391a632b2e09f96397bfc59d8e8c4353a87f1，新9GUI包含正常進城、第二次選駐軍、取消職業及返回世界。四側完整原版、每點索引／色盤、原始WAV、存檔與回退一致；只有標題一張[65,16,254,33]改變，其他八張与原選項區相同。實際22px，已目視清楚；153Go／go vet、無skip。

正式[check_goal185_profession.py](../../tools/check_goal185_profession.py)PASS，摘要cf451f8f1b6ccd424b158c167d9a2979a003c639d452277d39451d418d35b4c7。輸入d8a6c631501d8221ac7042b4a22d18ec8a4be131d304ed45e4c00672181d905d，終點116000000步、RAM ab1b916929162cc7b29584ece81856ad3fdd93a15b900209ecb06260392a44d2。來源觀測db7e6949bfd8684b957a985dd17405ad77428485ef1e0b5372d097ff761cac88；原版來源與資料指紋沿本節，原始像素／音訊／存檔只留workplace。其他標題或折行數仍屬後續範圍，不由本例關閉#56。

## 2026-10-09 DRAFT：G兩列目的地皆可選

正常存檔09冷啟動後，m／c回移動模式，數字鍵盤向東一格，以G開目的地再Escape取消，八張正常GUI完整關窗。現行前端只接受Jamestown灰色8，因此此處兩列均68色時整列回原文。只修顯示，原版可選性、移動與取消保持。

confirmed：私用coast-options-observer沿相同正常輸入，在86955000步收尾；標題GAME.TXT:0x1CBB、safe[66,82,176,94]、30px、waiting-screen、完成86839164步。London (England)與Jamestown各cap8，face分別[77,97,155,106]、[77,109,127,118]；兩列主色68，陰影47／128，runStyle為68／149／47。工具與原版指紋沿規格038返歐三欄，20bit實體RAM來源與檔案位移不混用；觀測完整RAM00dc6afa7109cc20b9d86f23d55e65c82cc2d46af71857f3b41e6b0797fe710f。

候選只增加第二列68色到既有已驗8色集合。第一列68、完整原文／兩列字格、標題身份／字級／位置／像素及兩百萬步時效守門保持；其他顏色、額外行色、角色或目的地形狀仍拒絕。字模沿既有安全區[76,96,157,120]及候選30～20px，須重測27px與正常／灰色兩分支的色層。原型同輸入的三側、原版、音訊、存檔、區外及舊灰色回歸通過後才READY；正式新GUI前不稱CONFORMED。

2026-10-09 READY：可選68色原型八張正常GUI輸入／三側與只讀觀測的原版端點、每點索引／色盤、原始WAV及存檔一致。只改G兩列的一張安全區，其餘七張相同；缺字模回原文。27px／[76,96,157,120]量測、錯cap／字格／原文／標題／時間／像素及9色反例通過，兩列色層均一般68。已目視清楚且雙語城名未裁切；原版灰色8仍是允許分支，正式還須灰色回歸。

原型二進位08edee1ddcd320be0384f8f5fb09a1c79c18be53847317f2c0fc3a90099b4082，輸入d2925c87f14ae8c62443eefdbceb9e333013ede5c8b74468d115c627f00cbd19，量測fcb227d755f7bdcdc6dfc16a3b9f861de6ecfc996881541f020c6832cc0fb907。據此授權正式第二列接受68或8，其他守門保持；新GUI懸停／取消、四側及既有灰色回歸前不稱CONFORMED。

限定CONFORMED：正式54a1cf49e822558100bc503f11e37adf49e85dc447d91100addcc7fd9ad3a30f，新10GUI包含兩次懸停及取消；中文／原文／缺字模／上一版完整原版、每點索引／色盤、WAV及存檔相同。只有初開與兩次懸停三張的[76,96,157,120]改變，其他七張相同。兩列27px保持68色可選；原灰色分支及返歐14張像素／原版／音訊／存檔回歸全等。153項含子項Go／go vet、無skip。

正式入口[check_goal185_coast.py](../../tools/check_goal185_coast.py)PASS_COAST_FORMAL。新輸入db4377de8bd11270d17262df89d513160a41c68c03ca7b56032d13285acf6f99，終點121800000步、RAM aae1163c190ee216dc9df5a5b36b9845dab1a7cdf30c3b8e4b04e0398df7dc08。只完成已觀測兩列的第二列68／8色分支，其他城市／母港或行數仍须取得正常來源並審查，不以本例縮小#55／#56原範圍。

## 2026-10-09 READY：正常G兩列目的地

此新增逐行分支依[規格038的返歐旅程READY審查](038-string-overlay-draft.md)授權。兩個原版字格、68／8色層、原始標題身份／位置／像素與生命週期全部符合才覆蓋；27px保留停用灰色與預設雙語城名。貿易編輯器的原有回呼不放寬，其他目的地或玩家命名維持原文。正式新GUI與原版同狀態驗收前不稱CONFORMED。

2026-10-09兩列限定CONFORMED：新14GUI／四側與24張港口回歸通過，正式來源、字級、灰色、輸入、終點與完整指紋見規格038同節。矩陣與普查只採本次已驗欄位，不外推其他目的地組合。

## 2026-10-08 DRAFT：港口帶貨四列的清單分流

目前狀態限定CONFORMED；下方保留DRAFT、READY及原型證據。正常原版自動存檔COLONY09 f5982c9974e6b7e6…由目標181 v153健康玩家路徑產生，從主選單載入、正常進Jamestown，Shift拖曳27噸毛皮入船艙，回移動模式，以G選London並正常推進回合抵達。貨物版畫與歐洲教學仍依原版流程；未注入貨物、座標或金錢。原版正常另存COLONY00 c9655cc23ed5eaa1dff004161d99dd57c339c58f49e2635a49e71127f0ec3cd7，後續從此存檔重啟。

confirmed：新四列文字完整命中EUROPESHIPOPTIONS 0x9B3D／75bytes的既有正文模板，因而走段落排版，中文四項擠成框頂一段。原版清單與選項仍照常運作，須修正顯示分流，不能把已匹配正文當成正確清單。標題EUROPESHIPCLICK安全區[63,68,265,82]；現行錯誤段落安全區[54,68,265,132]。三列已有規格與驗收保留，四列需要本欄原版行距／cap／墨跡／色層重新量測及容量檢查。

候選只在固定港口指紋、來源已驗完整四列、完整逐行墨跡及有效EUROPESHIPCLICK正文像素中，優先走逐列清單；不排除全部段落、不改原版選項、流程或資料。逐列選字級、基線與安全區後，再核對原版同狀態、回退與正常取消。正常GUI及來源觀測入口在[目標185](../goals/185-player-experience.md)，私用收據`loaded-cargo-options-re-gui`與`port-four-observer`。

首次長旅程GUI關窗後腳本只等待檔案出現，尚未等前端結束，造成18MB JSON末端截斷；該收據不採完整終點。已補等待自有PID退出及JSON／記憶體／輸入end一致；重啟的四列新GUI有完整終點。這是驗證腳本競態，不當作產品缺陷。

READY審查：四列cap8、正常68／強調149／陰影47及128，行距12，墨跡依序[82,85,145,94]、[82,97,205,106]、[82,109,159,118]、[82,121,136,130]。中文30px、安全區[81,84,207,132]，原版基線逐列對齊。固定來源、場景、位置／cap／內容／有效正文像素及時序反例通過。原型先設分流標記list-source，既有switch只接受no-template而拒絕；修正內部分流標記，未放寬來源條件。

原型v2八張正常GUI輸入的中文／原文／缺字模與原始前端完整原版、各點RAM／索引／色盤、WAV及存檔全等；只修四列畫面原錯誤段落及清單區，其他7圖相同，取消無殘字。輸入8c079a535aa3fed3ef093defb0942d0efb1dfbbc7090361f193e2627c084ee7c，終點RAM3a8bab4f9ccd4bc300804297e8a108ca9e9dd43ea017c14bc43efd10caf5fd4d，候選28862e262ec30ed335c30862bb9e86629927278aba2dd30caba1ad046d649ac2，版面9caff252d06c744315e98143da5c4f12eacbe7457eede8bde5b8f5f5c8d0373c。

授權固定四列完整來源先分流到清單，三列沿原已驗組合。正文關係保存完整四列，三列重繪時只取第1／2／4列作已驗保留，不改一般段落匹配與全域等待。正式驗收另錄四列懸停、取消／返回及三列回歸，原型不代替正式正常GUI。

限定CONFORMED：正式8e27f92bc4a73ded8289f19e664e62b5eae1185b21bad3866c33c7e7a94af015、154项含子項Go及go vet通過，新13GUI／四側的完整原版、每點RAM／索引／色盤、WAV及正常存檔一致，GUI與中文重播逐像素相同。四列各30px，四次懸停仍為逐列清單，取消／返回無殘字；只修五張四列頁的原錯誤段落與清單區，其他8圖相同。空貨艙三列11圖及灰色裝備13圖共24回歸與舊GUI逐像素／原版／WAV／存檔相同。返歐完整原版控制重播也產生相同COLONY00，補足種子的正常流程來源；舊截斷JSON仍不採完整終點。

[check_goal185_port_four.py](../../tools/check_goal185_port_four.py)PASS，輸入f6233915b1bbc44c53642967de145b86dd81d1a3e3f7c16912cf2af6f58b1ecb、終點138000000步／RAM af5adc7a3dd3045043da684ef7ad75791420006b3f49fd3cc60fd427a6768aa3，摘要36706c6b16f29ec2a4bda8cd76846ca3ce2829e504f57c13c87fcf27e0715b93。矩陣第66列／完整四列來源守門PASS，摘要c876f64f4cddcd0175e1f1bfad49cf6e4d5581c4ff4dd6e3c74f560d1f678f84；全矩陣與普查未重算。其他船型、旅程新命中的整串標題／狀態與完整#56仍依工作清單審查。

## 2026-10-08 DRAFT：碼頭資金不足的灰色裝備列

目前狀態限定CONFORMED；下方保留DRAFT、READY及原型證據。正常存檔、工具與指紋沿下方港口船隻證據；本輪從正常購船後COLONY00冷啟動，開歐洲、點木匠、正常取消「搭乘下一艘船」預約後重開。原版兩組六列都回line-colors，其他畫面正常，沒有注入貨物或資金。

confirmed：原版六列左界82、上界73加12倍列號、cap8；三項裝備位於第2～4列，原價150$／200$／150$。這三列前景只有色8，其他三列前景為68／149，陰影為47與128。每列完整色號由原版寫字事件取得；已存在的observedDockOptions拒絕色8，通用lineRoles又把傳教士列的68判為強調色，因而把149混色列當成未知第三層而拒絕。這是顯示辨識缺口，不改原版資金、灰色狀態或可選性。

原始ARMOPTIONS偏移0x98AC／362bytes、SHA-256 56d19f3e5b4344d1f6c5a4745ed009f6f0f251ed4e45032792da48ad66de45ed，完整來源與六列組合譯文已有建檔。候選只在固定港口指紋、六列已驗位置／cap／內容及68／149／47配色中，接受第2～4列單色8，渲染為獨立灰色層；未知色、混色灰列、其他列號或場景仍拒絕。沿本欄cap8量測30～20px候選、原版基線／行距及最長數值，缺字／超界回原文。原型須核對原版、同輸入、字級、灰色遮罩、區外及反向回退，READY後才接正式來源。

私用取證`port-board-cargo-re-gui`及`port-dim-observer/lines.jsonl`位於[目標185](../goals/185-player-experience.md)的證據根。搭乘預約不等於實際登船；本次尚未取得帶貨四列，不將它當成四列收據。

READY審查：實際兩組六列均30px、安全區[81,72,236,144]；原型八個正常取樣與中文／原文／缺字模三側完整原版、取樣RAM／索引／色盤、WAV及存檔相同，只改兩張六列安全區，其他6張逐像素相同。依每列原版前景判斷灰色，三個裝備列可各自為色8，其他列及混色灰字仍拒絕；兩組各八種灰色組合與九位數30px容量是投影，沒有宣稱正常命中。原始數字模板不接受千分逗號，反例維持拒絕，不擴張來源格式。

原型輸入f6316873548f944ae2a9bd0519aacd8985c78fd6dcd77d5bf157e83b9fd9099e、終點RAM d67927651e3370b30a654f9cfbd941afa6fa34c41880f3cd99d2e3bf8e1e357a，前端90055d3a74b9cbcd0739bff44db81e4c963265e60b67a6227875ba97b2501525；摘要6b755139d12a9ed5fc2787a989892da182b3cedfaeac6deb3681c664dfb03c30、版面c0c9d104c4ccb6bce8a54cdab6e1e891f0284a32f38e3aef32922adbb75a68b6。首次測試未載對話字模、第二次把字模範圍誤填20而違反已烘floor12，均為測試設定，已按實際字模契約在同一映像／命令重跑，未放寬正式綁定。

授權按既有完整六列來源、位置、cap與固定港口指紋限定加入色8及獨立灰層；逐行取原版色，不按譯文或金錢推算是否可選。正式驗收須新GUI的兩組清單、灰列懸停／點選、取消／返回，以及三側回退和同狀態核對；完整12列來源不因六列子集增加普查。

限定CONFORMED：正式前端2f0fbafd16e677e12774e8bdc11d093e8f2e46f5fb6aa2b99d3f67afcb051dcd，154項含子項Go及go vet通過。新13張GUI／四側同輸入、完整原版／各點RAM／索引／色盤／原始WAV及正常存檔全等，GUI與中文重播逐像素相同。兩組六列均30px；三個灰列前景索引8逐列核對，沒有68／149綠色或強調色混入，懸停／點灰列仍保持原版不可選，取消及返回無殘字。新增差異只在五張六列安全區，其他8圖与舊前端相同。

[check_goal185_port_dim.py](../../tools/check_goal185_port_dim.py)獨立PASS，輸入3e66ba5bc8f77d8c25220e1f488e1d9ff5968e8523eb82d1cfbdea461b4be7d8、終點143400000步／RAM c22b6dc2d5318b119698837448a84be7279b79063ea23da0e0239b43ac373864，摘要8338305ec8bb49c91695948182544a64664bfcd3f9c8f32b589b17314d872ae9。矩陣第65列與欄位守門PASS，摘要e673e819bcb583bb66fec166a73860c3ab6347a91539546b0176b0140451e8bf；僅採完整標題，六列不提升完整12列來源，全矩陣與普查尚未重算。其他碼頭列數／色層、帶貨四列及完整#56仍按工作清單審查。

## 2026-10-08 DRAFT：歐洲港口空貨艙船隻選項

目前狀態限定CONFORMED；下方保留DRAFT、READY與原型失敗。正常GUI來源、存檔與工具沿規格038的港口船隻頂列附記。選輕帆船後，原前端已翻譯EUROPESHIPCLICK標題，三列操作仍以line-no-template回原文；Escape正常取消後返回港口。

confirmed：三列原版墨跡半開矩形依序為[82,91,145,100]、[82,103,205,112]、[82,115,136,124]，原版行距12。固定GAME.TXT的EUROPESHIPOPTIONS來源偏移0x9B3D、長度75、SHA-256為9f32942301758e884038362e26a03eebf1bbd02076aedc5d5b07983875e1d370；完整四列及譯文已有建檔，這次正常空貨艙只顯示第1、2、4列。這是顯示子集的確認，不據此推測未驗貨艙規則。

候選須同時符合既有港口三按鈕畫面指紋、EUROPESHIPCLICK的有效標題及印後像素、三列完整內容／順序／位置；只取上述原始四列的第1、2、4列譯文，不加入任意短語全域比對。先量測本欄原版cap、色層、框界與22～30px候選，依原版基線及行距求合適字級；缺字／超界或身份不符回原文。正式接線前要求同輸入原版狀態與音訊不變、缺字模回退及正常取消無殘字。私用取證入口為[目標185](../goals/185-player-experience.md)。

READY審查：原版三列cap8、行距12，最終中文30px，安全區[81,90,207,126]。原型先借標題的afterSafe而拒絕，診斷證實標題當時仍waiting-screen且afterSafe尚未形成；不能把拒絕解讀為原版缺字。既有同框選項工具的框界亦未直接匹配這個版面。改用正文完成時已保存的optionBody原版像素、確定來源鍵及完整三列的固定墨跡／cap；仍須既有港口畫面指紋與68／149／47色層。保留原型v1／v2失敗，不提高時間上限。

原型v3三側與原觀測副本8個取樣、完整原版、WAV及存檔全等；三列30px均完整顯示，選船以外7圖與原前端相同，Escape取消無殘字。收據與輸入指紋沿規格038的READY審查。授權正式載入經來源驗證的第1／2／4列，與EUROPESHIPCLICK建立正文關係，使用上述欄位限定條件及既有字模排版；其他列組合繼續回原文。正式驗收另錄新GUI及三列懸停，不以原型代替。

限定CONFORMED：正式來源與新11GUI／四側收據沿規格038的港口船隻頂列正式驗收。三列均30px，三次懸停後正文與選項保持中文，Escape取消及返回世界無殘字。正常原版／WAV／存檔保持相同；新差異僅四张選船／懸停畫面內的核准欄位，其餘7圖與舊前端相同。固定位置／cap／內容／來源／年代／場景／正文像素反例通過，來源完整四列只授權已觀測的第1／2／4列組合；帶貨四列仍回原文，不以本次子集關閉#56。[獨立檢查器](../../tools/check_goal185_port_units.py)另輸出此普查限制。

## 2026-10-08 DRAFT：讀檔失敗的檔名變數

目前狀態：四個讀檔來源與來源限定槽位標題保留已限定CONFORMED。以下保留DRAFT、READY與最初FAIL。

新增取證的LOADNOT／LOADOLD／LOADSIZE仍維持DRAFT。正常讀檔清單形成後，僅變更私用副本的明示標頭byte；原始輸入保持唯讀，測試後副本還原。byte0變更觸發LOADNOT，byte10變更觸發LOADOLD；byte9變更正常載入，不當作版本欄。byte12變更由主選單觸發LOADERROR，由已載入世界的GAME讀檔入口才取得LOADSIZE。不把試驗檔名當成原版資料語意，不修改正式存檔格式。

| 原始来源鍵 | 原檔偏移／長度／SHA-256 | 原版輸出及墨跡 |
|---|---|---|
| GAME.TXT:0x0000088B | 0x88B／34／e35a1a140176f9b2d726851129a705bacc09b6ebf15cf47a78d54d6c1df359c3 | COLONY03.SAV為無效存檔；[67,95,246,104] |
| GAME.TXT:0x000008C7 | 0x8C7／34／0bc46b070b022832e503f1cac7755f0e037fbc1387906619ea08742d1556301b | COLONY03.SAV為舊版存檔；[67,95,251,104] |
| GAME.TXT:@LOADSIZE:0x00000904 | 0x904／81／bf636a831f7676d0669a32481ac9ca783f03c13f0c0ae308389b39815e064d41 | COLONY03.SAV與目前地圖不符；三行墨跡[67,85,224,94]、[67,95,248,104]、[67,105,109,114] |

以上原檔雜湊與工具沿本節。現有譯文與模板已載入，三種原版提示均因檔名术語守門回英文。私用load-validation-magic-gui、load-validation-size-gui與load-world-dimension-gui保存正常GUI；重播依清單檢查點施加同一明示條件，全部取樣／完整原版／WAV與還原存檔須一致。下一步共同量測三欄，僅允許這些來源鍵的%STRING0保留經既有格式核對的檔名，不授權一般變數。

LOADERROR檔名原型已顯示中文，但啟用新框使仍可見的讀檔標題被superseded撤銷。標題原版像素未改且與新框不重疊；候選須從cur或prev保留已核對的active槽位標題，仍核對完整afterSafe、不重疊、先後順序與來源限定錯誤鍵。尚未通過區外像素比較前，不升READY、不放寬比較容差。

SAVEERROR已限定CONFORMED後，再由正式f39336c6…走正常主選單讀COLONY03。清單顯示後暫移私用副本，原版顯示LOADERROR；原始输入與存檔內容不改，副本最後恢復。這是檔案缺失條件，不當作一般成功讀檔驗收。

confirmed：GAME.TXT:0x00000971，28bytes，片段SHA-256 3e57ec4ec97e1f19e060fe85e56704bc1f18fec357fcb053f8c4423d48dec53a，原檔SHA沿SAVEERROR。現有譯稿「載入遊戲 %STRING0 時發生錯誤。」已載入；原版輸出事件84975000步顯示檔名COLONY03.SAV，墨跡[67,95,231,104]，回退line-variable-without-term。檔名來源限定處理、字高與安全區仍待原型審查，不能從SAVEERROR外推。

三張同步GUI與中文／原文／缺字模重播的完整原版狀態一致，另有重播終點圖，不當第四張GUI。輸入SHA-256 30ee7a5e12ebe86600bf2f3b29d8e8054b3b1170422e6e108f67f0cca773b43b，終點RAM f79a3491351a44bcdb55688a691fc8a113294dfa8c6535c4bbbfa4311dbc0243。重播在正常清單檢查點暫停自有程序、移走同一私用檔再恢復；沒有改客體記憶體或原版控制流。按Return後原版與三側都結束程序，原腳本預期返回選單而報「前端已結束」；完整終點與輸入已保存，不當產品缺陷，也不更改原版退出行為。

本機load-error-explore-gui及load-error-explore-{zh,control,missing}保存收據；play_load_error.py與replay_load_error.py為重生入口，經[目標185](../goals/185-player-experience.md)索引。初始存檔標頭第一byte變更的獨立無效測試副本，在清單階段已被排除，沒有觸發LOADNOT，不算該錯誤驗收。其餘LOADNOT／LOADOLD／LOADSIZE與這個LOADERROR修正仍DRAFT，下一步先完成來源限定原型及量測。

READY審查：四個來源已各取得原版GUI與同條件重播。私用候選僅保留這四個鍵的%STRING0檔名，維持原格式核對、缺字／超界回原文与一般變數拒絕。LOADERROR、LOADNOT、LOADOLD各cap8／pitch12，安全區依序[66,94,233,106]、[66,94,248,106]、[66,94,253,106]；各自候選30～20px，實際30px。相對中文墨跡依序[6,4,559,32]、[4,4,483,32]、[4,4,516,32]。

LOADSIZE另量原版cap9，安全區[65,82,254,116]／四倍756×136；候選30～20px，選30px，中文正常折為兩行，墨跡相對[4,4,714,72]。既有正文內距、基線與換行規則不改，缺字或高度／寬度不適合回原文，不以畫布裁切充作策略。四欄各100個合法格式容量共400筆通過，容量不當成正常命中。

標題來源限既有LOAD／SAVE槽位標題鍵，需active、完整afterSafe與目前原版畫布一致、與新框不重疊、時間順序合法；從cur或prev找到後只保留該標題，其餘段照舊撤銷。七種錯位／錯鍵／過期／變更／重疊／逆序／不完整拒絕通過。最初只延伸retainSlotTitle失敗，是因它要求cur與新段同id；已查原始轉移流程後改用來源限定的獨立標題選取，不調全域時限。

獨立審查load-family-candidate-review.json指紋c8ca2822923647e21850a6acb037e6af6c2546099f7126f96ea6825a7344cecf，容量92dcce88d97f0d914e7af77182afb9f51c3d691015c48adbe2d08a731f0834f6，多行原版量測a0b9f21d1e799bb21ed1cd0ddc461fdf40c8633bd1f83cbf818c08e26376d3ad。各路徑完整原版CPU／RAM／VGA、每點索引／色盤、原始WAV與還原存檔相同；只改各自錯誤安全區，標題與其他圖不變，缺字模回原文。據此授權同一檔名分支与來源限定標題保留接入正式來源，尚須四種新正常GUI／三側及既有SAVEERROR、報表與世界路徑抽樣回歸。

限定CONFORMED：正式前端ed5444ea648d551cf8d512d282c1a9b970b6737dd9d5596f048c1869f4d7ad8c，149項含子項Go與go vet通過。四种新正常GUI共16圖及中文／原文／缺字模／舊前端同輸入的完整CPU／RAM／VGA、取樣RAM／索引／色盤、原始WAV與還原存檔全等；只改各自錯誤安全区、標題及其他12圖不變。檔名保留原樣，原版LOADERROR確認後退出不改。LOADNOT／LOADOLD為清單後明示無效副本，LOADSIZE由既有世界正常GAME讀檔取得；不是健康存檔錯誤或正式格式變更。

独立檢查器[check_goal185_load_failures.py](../../tools/check_goal185_load_failures.py)PASS_LOAD_FAILURES_FORMAL，彙整0e76d0136bf6aff8d2b0310576bda2277bff957986ac76b1bd7de67783f45ee9。既有SAVEERROR8圖與報表10圖的新前端回歸逐像素、完整原版與原始WAV相同，共18圖。四欄各自cap8／cap9、30px、内距／基線／換行、最長格式與拒絕策略沿READY，不新增固定全域字級。這只完成五種存讀檔檔名顯示；Issue #61其餘教學、開局與事件範圍尚須完成審查。

## 2026-10-08 DRAFT：儲存失敗的檔名變數

目前狀態：SAVEERROR來源限定CONFORMED。以下保留DRAFT、READY與最初FAIL。

Issue #61的新正常GUI在獨立存檔目錄設定0555後，正常GAME→Save Game→第一空槽觸發SAVEERROR。原版資料唯讀，客體記憶體與存檔未注入或改格式；這是檔案系統失敗條件，不能當成普通可写目錄的成功存檔驗收。原目錄在測試後恢復0755。

confirmed：GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，原始檔案偏移0x7F0／27bytes、片段SHA-256 1fe8970fc7f4e6a847798b391a98750fef720eb49c9fd7f35bd4c700c8745263。譯稿已有「儲存遊戲 %STRING0 時發生錯誤。」並實際載入；顯示訊息為`Error saving game COLONY00.SAV.`。`matchIn`把%STRING0當術語，導致`line-variable-without-term`回退。這是檔名處理缺口，不是缺譯。

原版印字入口沿0D21:00C6的執行期CS:IP；fallback事件記錄124575000步、墨跡[67,95,229,104]。欄位字高、30～20px候選、安全矩形與最終字級仍待私用原型量測，不從其他成功提示外推。候選只對這個來源鍵的%STRING0使用既有dialogSaveFilename格式核對並保留原檔名，其他未知變數仍拒絕；LOADNOT／LOADOLD／LOADSIZE／LOADERROR尚未因此授權新行为。

closure-save-error-gui輸入SHA-256 574643c8d3bdd816ac3e0d0fce39a03434142777f8b0a375eb16f6d15ba7d8cb，正式前端baa1eac7…、隔離dosgolem82a14b2、Go1.26.7與固定HR映像1430a2cf…；初始DOS時鐘0與未修改的正常COLONY03同前述驗收。三側9張GUI的取樣RAM／索引／色盤、完整CPU／RAM／VGA、原始WAV及存檔一致；缺字模回原文，錯誤正文仍英文。終點RAM e4357b523280be91193ec410966e2dc2b0c15a327cd1e1a0d86d342757d125ce。

[check_goal185_remaining.py](../../tools/check_goal185_remaining.py)的`--profile save-error`以退出碼1保留FAIL_TRANSLATION_SAVE_ERROR；彙整指紋9385e8ad6abbee32b6a808010c57f662713151758b640e5b8f3377901c2039bd。原腳本把實際錯誤框誤命名save-description，132495000步才是已核對錯誤圖；save-error圖已回世界。保留原名與輸入，不挪用後者冒充錯誤截圖。正式修正仍須DRAFT→原型／量測→READY→新正常GUI，不把這份FAIL改成PASS。

READY審查：私用save-error-candidate只對GAME.TXT:0x000007F0的%STRING0保留經dialogSaveFilename核對的檔名；一般變數與其他錯誤來源不改。原型148項Go與go vet、檔名格式／來源錯置拒絕通過；100個合法格式容量是壓力測試，不是100次正常存檔。原型、原文、缺字模與舊前端的完整原版、九點RAM／索引／色盤、原始WAV及所有存檔相同，缺字模回原文；只改實際錯誤框，其他8圖相同，關閉無新增殘字。

confirmed字級：原版此欄cap8、pitch12，安全矩形[66,94,231,106]，四倍660×48；候選30～20px，實際30px，中文墨跡相對[6,4,559,32]，上緣沿原版墨跡對齊，內距與陰影沿既有單行清單策略。100個檔名都採30px且墨跡不越界；缺字、超界或非法檔名維持原文並記錄，不裁切。原始定位與輸入指紋沿上方DRAFT。

量測layout.json指紋71f3eab659a7f976ec4d106d1aec04c6f499995c37a55f7e1aea953e665570dc，geometry-review.json指紋1759f8d096d9b390372be2c46082fd537a17e58b8c6d8cf8afbd5e6b9104b9c5，九點原型審查save-error-prototype-review.json指紋1a1def01bc2dee2b349a36de94a131668847031d4a43e9a051423103de5101e0。按已載入規格閘門升READY，授權同一來源限定檔名分支接入；新正式GUI及三側驗收前不稱CONFORMED。其他LOAD系列仍未授權泛化。

限定CONFORMED：正式前端f39336c61f72b27fafb8dd2717d6ed0035c2b1fdb7603167b2d501bbc3193337，148項含子項Go與go vet通過。新正常8GUI在實際錯誤框擷取後才關閉；中文／原文／缺字模及舊前端同輸入的完整CPU／RAM／VGA、每點RAM／索引／色盤、原始WAV與存檔一致，只改核准錯誤安全區、其他7圖相同，缺字模回原文。來源7F0、cap8／pitch12、30px及安全區沿READY；未放寬一般變數或其他錯誤來源。

独立檢查器[check_goal185_save_failure.py](../../tools/check_goal185_save_failure.py)PASS_SAVE_ERROR_FORMAL。新GUI輸入8689697dbaf3f53c37c50a0897f43eceb0e4953bf720601cef9cdcb53d01f7d6，終點RAM94f8a05f2d54ddde1617fc3221a4fa85a4367565e9ea79e361382e15d6860085，彙整481d9b0641bf27961e92e03ff05f85380e51674b73f80b3cb82b441eef9dd30a。較早9圖英文FAIL仍保留，由不同輸入的限定修正補足，不改寫舊收據；Issue #61其他範圍仍未完成。

狀態：正文段限定 CONFORMED（2026-09-28，見文末）；READY 2026-09-28；DRAFT 2026-09-27（[目標165](../goals/165-dialog-overlay-engine.md)，[Issue #41](https://github.com/wicanr2/colonization_cht/issues/41)）。本規格推廣規格026 的首則 help 做法：不再以固定畫布雜湊鎖定單一則訊息，而以逐字事件重組的原版顯示字串對 GAME.TXT 模板整句比對。

## 固定輸入與工具

- 原版 DOS `GAME.TXT` SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`，其餘四個核心檔同規格033 的版本閘門。
- 隔離 dosgolem `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；研究映像 `colonization-research:20260920-r2`。
- 路徑輸入 `workplace/reports/goal165-dialog-explore/r6/route.inputs.json` SHA-256 `214815efae00148c5723a656caa5912ceb8858a3c511894289512ad6fef59900`：目標163 真 GUI 英國海上路徑的 5.9 億步前綴（Explorer），加上 6.0／6.15／6.3／6.45 億步數字鍵盤 4（往西）、6.75 與 6.95 億步 Enter、8.35 億步下鍵與 8.45 億步 Enter（選「Make Landfall」）、8.75 億步 Enter（接受條約）、其後每 1,500 萬步數字鍵盤 4，終點 9.3 億步。輸入檔只在已忽略的 `workplace/`；日後前端 GUI 腳本以同一序列重錄。
- 探針 `tools/probe_goal165_dialogs.go` SHA-256 `f09213501de9a5998ad873a3b8f84e8c9b12cfd6280f92efadc6df2ae33d56ef`，預覽 `tools/preview_goal165_dialogs.py` SHA-256 `63cf75bc0d0796236c4893e61054b2f911c890057f4b1cee26a17fd18825a24f`。

位址空間：`0D21:00C6`、`0D21:012C`、`0CAE:00A8`、`0B68:051C` 是實模式 `CS:IP`；`0x2AC7A` 等是 20-bit 線性 RAM；座標是 320×200 索引畫布，`×4` 標示者為放大輸出像素；步數是 dosgolem 指令步數。

## 原版證據（confirmed）

雙冷啟動 `a`、`b` 的印字事件與終點狀態逐位元組相同；無監看控制 `control` 的終點記憶體 SHA-256 `51dedd6b472d220ddb40d305f76bc81a0a6c1214506e79591945671942078f81` 與索引畫面相同。

| 步數 | 訊息鍵 | 原版顯示（重組） | 外框（色號 0） | 墨跡 bbox |
|---|---|---|---|---|
| 678,298,707 | `GAME.TXT:@LANDHO` | `Land Ho! What shall we call this new land, Your Excellency?` | `(59,111)–(265,159)` | `(64,117)–(253,136)` |
| 820,465,468 | `GAME.TXT:@LANDFALL` 正文 | `Shall we make landfall, Your Excellency, and leave the ships behind?` | `(62,116)–(257,171)` | `(67,122)–(250,141)` |
| 864,416,055 | `GAME.TXT:@INDIANWELCOME` 正文 | `"The Sioux tribe welcomes you. We are a glorious nation of 9 Camps. …"` | `(6,52)–(201,147)` | `(11,58)–(195,117)` |
| 876,276,899 | `GAME.TXT:@INDIANPEACE` | `"The Sioux welcome peace with our brothers the English. …"` | `(6,74)–(201,125)` | `(11,80)–(180,119)` |
| 891,283,948 | `GAME.TXT:@INDIANCOME` | `"We hope you will soon visit Sioux villages …"` | `(6,74)–(201,125)` | `(11,80)–(177,119)` |

- **逐字事件：**`0D21:00C6` 每字從同一 `SS:BX` 基址讀「字元、0」兩個位元組；下一字又從同一基址重讀。基址隨堆疊深度不同（正文 `0x2AC7A`／`0x2AC76`，help `0x2AC72`），不能當鍵。字距約 800～1,400 步，換行約 2,500 步；一段正文 13.8～26 萬步印完。空白也讀，但沒有改色點。
- **改色：**`0D21:012C` 以色號 68 畫一般字、149 畫強調字（原文 `{}` 包住的部分與變數值），47／128 畫陰影；字形墨跡高 7 邏輯像素、行距 10。陰影色是對話框與 help 共有、狀態欄與選單列沒有的特徵。
- **換行：**原版依框寬重新換行，不照 GAME.TXT 的 `\n`；連續兩個空白顯示為一個；`{}` 不顯示。重組規則：逐字 x 回捲即換行，行間以一個空白相接、連續空白壓成一個，即與模板正規化後相同。
- **選項與輸入欄是另一段：**`@LANDFALL` 的兩個選項、`@INDIANWELCOME` 的 Yes／No、`@LANDHO` 的 `Name: New England_` 都在正文印完 6.5～26 萬步後以另一個基址另成一段；選項反白底由 `0CAE:00A8` 畫。
- **框線：**從首字位置在印前畫布向四方掃描到色號 0 即得外框；內側一像素 134、一像素 128 斜面，框內是木紋（132～138），不是單色，擦字必須還原印前像素。
- **其他寫入者：**正文印字期間只有游標常式 `0B68:051C`（游標附近）；`@INDIANWELCOME` 期間另有 `0CAE:00A8` 在選項列範圍。

## 覆蓋設計

1. **辨識：**`0D21:00C6` 讀取且 `SS:BX` 等於被讀位址時開始候選段；後續讀取必須是「基址字元、基址+1 為 0」交錯，兩萬步內無讀取即結束。段內沒有陰影色 47／128 改色點者不處理（排除狀態欄與選單列）。
2. **逐點記錄：**段內每個 `0D21:012C` 寫入記下第一次改寫前的值與最後寫入者；其他寫入者落在最終安全區內即整段回原文。
3. **重組與比對：**依上述重組規則得到顯示字串，對語料 `text/corpus.zh-Hant.tsv` 的 GAME.TXT 列（檔案 SHA 相符、不含 `^` 置中碼）整句比對：模板取 `\n\n` 前的正文，去 `{}`、`\n` 換成空白、壓縮空白；`%NUMBERn` 比對十進位數字，`%STRINGn`／`%COUNTRY` 比對非貪婪任意字。必須恰好一列命中。
4. **變數：**數字原樣保留；其餘變數值查 `text/terms.zh-Hant.tsv`（英文→定稿譯名），查不到再查 NAMES.TXT 語料列以逗號對齊的對照（原文與譯文逗號數相同才採用）；兩處給出不同譯名或都查不到，整段回原文。
5. **安全區：**橫向為外框內側 `[左框+3, 右框−3)`；縱向為 `[上框+3, 原版正文墨跡下緣+2)`，中文不得侵入其下的選項列或輸入欄。
6. **版面（A 版）：**Cubic 11 30px（字高 28 輸出像素，對應原版 7 邏輯像素墨跡），行距 40 輸出像素（原版 10 邏輯像素），頂端對齊安全區上緣 +4，左緣 +4；一般字色號 68、`{}` 強調字 149、陰影 47 向右下 4 輸出像素。這與使用者 2026-09-26 為同一字型、同一木紋框的 help 選定的 A 版相同。譯文的 `\n` 不採用，依安全區寬度重排，行首／行尾禁則同規格025。放不下時逐級縮到 20px（30px 的 2/3），行距隨字高等比，仍放不下回原文。
7. **啟用與撤銷：**段落結束、比對與版面都成立後，等真 VGA 在安全區（游標範圍除外）與畫布相同才啟用；安全區畫布之後任何改變（關閉、換頁）、影像模式改變即撤銷，回到待命以接下一則。按住滑鼠時回原文，游標以原版像素疊在中文之上。
8. **分工：**已由專屬欄位處理的訊息（例如 `--tutorial-help-a` 開啟時的 `@TUTORIAL1`）不進本引擎。

## 版面量測（預覽）

`tools/preview_goal165_dialogs.py` 以探針 `a` 的畫布產生 A（30px）與 B（26px）候選；A 版結果：

| 訊息 | 框內安全區（×4） | 行數 | 中文 |
|---|---|---|---|
| `@LANDHO` | `(248,456)–(1048,564)` | 1 | 發現陸地了！閣下，這片新大陸該如何命名呢？ |
| `@LANDFALL` 正文 | `(260,476)–(1016,576)` | 1 | 閣下，我們要不要登陸，把船留在原地？ |
| `@INDIANPEACE` | `(36,308)–(792,488)` | 2 | 「蘇族樂於與我們的兄弟英國和平共處。…」 |
| `@INDIANCOME` | `(36,308)–(792,488)` | 2 | 「希望貴方能盡快造訪蘇族的村莊，…」 |

預覽時 `@INDIANWELCOME` 的 `Camps` 只查定稿譯名表而回原文；正式實作依設計第 4 點另查 NAMES.TXT 對照，解為「營地」。預覽的縱向安全區以下一段起點為界，正式實作以原版正文墨跡下緣為界（設計第 5 點）。

## 未知與停止線

- 其他對話框類型（報告、殖民地內訊息、多頁訊息、含 `^` 置中的標題）是否同一常式與框線：未知，逐類取證。
- 選項列、輸入欄、LABELS.TXT 拼接片段：本規格不處理，維持原文並記錄。
- 本規格沒有未標示的假說；變數譯名的語境是否恰當（例如 `the English` 譯「英國」）屬譯稿品質，另依術語表修訂。

## 2026-09-28：證據審查（READY）

- 辨識條件、重組規則、框線與陰影色都有雙冷啟動＋無監看控制收據（上表）；模板比對與變數譯名有單元測試（`tools/dialog_overlay_test.go`，以自製假 GAME.TXT，不含原版文字）。
- 版面沿用使用者 2026-09-26 為同一字型、同一木紋框 help 選定的 A 版字級與行距；字級依原版 7 邏輯像素墨跡量測，縮字下限依使用者決定為 2/3。每則的安全區由框線掃描與原版墨跡決定，不是全域常數。
- 字元圖集 `tools/bake_dialog_atlas.py`（SHA-256 `b37ae6cb…`）烘製 30～20px 共 11 級、1,500 字，綁定 Cubic 11、語料清冊與術語表雜湊；任一不符整個引擎回原文。
- 本規格正文段據此升 READY；選項列、輸入欄仍不在範圍。

## 2026-09-28：正文段限定 CONFORMED（目標165）

- **實作：**`tools/dialog_overlay.go`（SHA-256 `28d53ef8…`，模板、變數、重排、三層字模與執行期狀態機）；`tools/live_menu.go`（SHA-256 `bf123b43…`）新增預設關閉的 `--dialog-a`、`--dialog-corpus`、`--dialog-terms`、`--dialog-atlas`，只加讀寫監看掛鉤、真 VGA 同步、撤銷與繪製。輸出 JSON 另記 `dialog_misses`（有陰影色但未中文化的顯示字串與原因）。
- **真 GUI：**`tools/probe_goal165_gui.sh` 以真鍵鼠（步數對齊，見目標164）走英國海上路徑往西，現場輸入 SHA-256 `0b17d0a9…`。本次船停在河口，登陸詢問為 `@LANDFALL2`（同類型），遇到的是 Iroquois 部落。五則依序啟用並由玩家按鍵關閉：`@LANDHO` 678,645,001～695,310,001、`@LANDFALL2` 762,135,001～845,295,001、`@INDIANWELCOME` 864,600,001～875,325,001、`@INDIANPEACE` 876,645,001～890,010,001、`@INDIANCOME` 891,495,001～905,355,001，撤銷原因都是安全區畫布改變。
- **同輸入驗證：**`tools/probe_goal165_replays.sh` 以現場輸入重播中文與英文控制，原版 CPU、完整 RAM、索引畫面、色盤與六個檢查點狀態相同（終點 `26caf797…`）；有對話框時中英差異只在該則安全區，無對話框時畫面相同；真 GUI 截圖的對話框安全區與中文重播逐像素相同。
- **反向對照：**缺圖集時整個引擎回原文（`font-mask-unavailable`），六個檢查點畫面與英文控制逐像素相同；術語表與 NAMES.TXT 部落列都移除現場遇到的部落名並烘製相符圖集時，原住民三則以 `variable-without-term` 回原文，另兩則照常中文。
- **檢查器：**`tools/check_goal165_window.py`（SHA-256 `c8236f59…`）PASS，缺原版回 SKIP 77。收據只在忽略的 `workplace/reports/goal165-dialog/`。
- **範圍：**本節只把正文整句中文與上述五則的正常玩家路徑升為限定 CONFORMED。選項列、輸入欄標籤（#46）、LABELS.TXT 拼接片段與其他畫面（#45 普查）未做；含 `^` 置中碼或 `@` 指令的段落不進本引擎。

## 2026-09-28：教學提示附記（目標167）

- **模板來源：**help 雙語清冊 `text/help-bilingual.tsv` 的 GAME.TXT `@TUTORIALn` 列加入整句模板；`--tutorial-help-a` 開啟時 `@TUTORIAL1` 仍由規格026 專屬欄位處理。
- **其他寫入者：**教學提示印字期間顧問肖像壓在框上。木紋框正文不再以其他寫入者重疊安全區為撤銷條件；逐點記錄最後寫入者，只把最後由改色常式 `0D21:012C` 寫下的像素還原為印前值，肖像像素保留原版印後值。
- **框線掃描：**肖像會擋住首字左側，改由最後一行墨跡的左緣與垂直中點向左右掃色號 0，再由首行右端向上掃上框。
- **變數譯名優先序：**定稿術語表優先；NAMES.TXT 語料與譯稿的 NAMES.TXT 列作弱對照，只在術語表沒有時採用，同一英文以先出現者為準。譯稿列必須通過檔案與位元組雜湊核對。
- **驗收：**目標167 五則限定 CONFORMED（`tools/check_goal167_window.py`；`tools/dialog_overlay.go` SHA-256 `a4743794…`、`tools/live_menu.go` `3b46b17f…`）。其餘教學提示見目標167 的移交清單。

## 2026-09-28：上框掃描附記（目標169）

- 殖民地畫面的 `@TUTORIAL4` 顧問肖像壓住框的上緣中段，原本「首行最右側那一欄往上掃」會穿過肖像一路掃到畫面頂端，安全區因而錯到畫面上方。上框改為首行整段寬度內逐欄往上掃到色號 0，取最多欄一致的列；左右框仍由最後一行掃。單元測試 `TestScanDialogBoxPortrait` 以自製畫布重現肖像壓框。

## 2026-09-29：無陰影木框與字級附記（目標170）

- 歐洲港口的說明框（`@TUTORIAL17`）與訓練對話框是色號 0 外框的木紋框，但沒有陰影色 47／128，字高 5；原本以「有陰影色」為木框條件而回原文（`no-box-style`）。改為模板命中後只要掃得到外框即成立；原版無陰影時中文也不加陰影。
- 字級依原版大寫字高量測：起始 ⌊字高×4.4⌋（上限 30），下限為起始的 2/3。字高 7 仍為 30～20px（使用者 2026-09-26 決定），字高 5 為 22～15px，與規格032、038 同一規則。對話框圖集字級範圍擴為 30～12px。
- 前端公開給 GUI 自動化的「像訊息框」判斷（不影響覆蓋）不再限制墨跡右緣 x<240。

## 2026-09-29：選項列、無框整句與前後兩段附記（目標172）

- **逐行清單改問字串層：**逐行清單的行查不到逐行模板時，改以規格038 字串層的字典與模板翻譯（對話框選項列、殖民地職業選單、建造清單）。逐行文字會把連續空白壓成一個，模板另備單一空白的寫法。對話框圖集因此也收字串層來源（模板、海上詞典、殖民地名稱）的字，但不綁定其雜湊（字串層圖集已綁定；改動模板的反向對照不必另烘對話框圖集），缺字時該行回原文。
- **右對齊欄：**行內 `=` 是原版的右對齊標記（不出墨）。含 ` = ` 的行分左右兩欄各自翻譯：左欄靠原版行左緣，右欄右緣對齊原版右欄墨跡右緣；兩欄重疊即整段回原文。
- **行內空隙欄：**沒有 `=` 的行，若出現至少 16 邏輯像素的無墨空隙、或原文在下一個有墨字元前已有連續兩個以上空白（歐洲港口購買、訓練對話框的 `(Cost: N)` 欄；殖民地建造清單的成本欄，名稱較長時空隙只剩約 9 點），分界前後視為左右兩欄各自翻譯，右欄右緣對齊原版墨跡右緣；任一欄查不到時整行照一般逐行方式翻譯。原版一般字間空白為 3～6 點且只有一個空白，不觸發。右欄模板見模板表 `col-*` 列。
- **次色行：**某行的主要色號是整段第二色（例如買不起的選項為色號 8），該行以第二色繪製。
- **無框整句：**整句命中模板但掃不到色號 0 外框（殖民地 BUY 說明框），改用置中段落型的無框版面，安全區為原版墨跡外擴 2 邏輯像素；原本回原文（`ink-outside-box`）。
- **前後兩段：**新一段與目前一段不重疊、且在 2,000,000 步內先後完成時（選單標題與清單），兩段都保留並各自合成；否則舊段撤銷。字串層（規格038）只在其墨跡與對話框安全區內縮 2 點的範圍重疊時才不繪製。
- **驗收（目標172）：**逐行清單改問字串層、右對齊欄、行內空隙欄、次色行、前後兩段限定 CONFORMED（`tools/check_goal172_window.py`；`tools/dialog_overlay.go` SHA-256 `5f9138f0…`）。無框整句（BUY 說明框）只有單元測試與乾跑，真 GUI 未到達。


## 2026-09-29：輸入列標籤附記（目標174）

- **證據：**命名新陸地（`@LANDHO`）、命名殖民地（`@COLONY`）的輸入列在收據中是一段獨立的逐字印字，內容為「標籤＋輸入內容＋游標」（`Name: New England_`、`Name: Jamestown_`），提示句是另一段；所有收據中的輸入列都帶游標 `_`（強推論：游標不閃爍）。GAME.TXT 的輸入欄標籤只有 `Name:`、`Colony:`、`Amount:`；`@LEADERNAME` 沒有標籤。
- **輸入列：**單行、第一個冒號之前有墨跡、結尾為 `_` 的逐字印字。只翻譯「第一個冒號（含）為止」的標籤：先查逐行字典（draft 單行列），其次字串層；查不到回原文（`input-label-*`）。中文右緣對齊原版標籤墨跡右緣，字級依原版字高選擇並逐級縮小；安全區只含標籤墨跡外擴 1 點，輸入內容與游標保留原版像素。
- **鍵：**同一標籤出現在多個段落（新陸地、殖民地、改名），候選鍵固定為 `STRING:input-label`，不以命中的譯稿列當鍵。
- **決定：**輸入框內是玩家正在編輯的英文字元（含預填的預設名），不翻譯（目標174）。
- **譯稿：**`Amount:` 五處（`@HOWMUCH1`～`5`）補入 draft 單行列，譯為「數量：」。
- **標籤的譯名來源：**`Colony:` 只來自 draft 單行列與字串層 `{w1}:` 模板；`Name:` 另可由字串層片段字典（語料中貿易路線命名框等多行譯文拆出）取得，所以只拿掉 draft 與模板時仍會翻譯。
- **開局姓名提示：**`@LEADERNAME` 的提示句由規格023 專屬欄位（`--nation-cards-rest-a`）處理，只開對話框層的路徑中是英文；姓名欄沒有標籤，預填姓名屬輸入內容，保留原樣。
- **驗收（目標174）：**命名新陸地、命名殖民地、Find Colony 三個輸入列限定 CONFORMED（`tools/check_goal174_window.py`；`tools/dialog_overlay.go`、`tools/live_menu.go` 雜湊見 RESEARCH-LOG）。改名、貿易路線命名、貨物數量未觸發。


## 2026-09-30：引號變數附記（目標177）

- **證據：**Find Colony 找不到時印出 `"J" not found.`（`@NOCITY`，語料模板 `"%STRING0" not found.`），變數是玩家剛輸入的文字；逐步到「術語表查不到」而回原文（`variable-without-term`）。
- **規則：**模板原文中以一對雙引號緊貼包住的變數（`"%STRINGn"`）視為玩家輸入，值不查術語表、原樣代入譯文，可為空字串（玩家直接按 Enter 時印出 `"" not found.`）；其他變數維持「查不到回原文」。

## 2026-10-01：BUY實際分支補證

目標181的BUYME1資金不足正文與建造面板三欄已通過正常GUI及三側同狀態。實際模板因第二行段落指令走規格036置中段落，詳見[規格036的BUY限定驗收](036-line-list-and-centered-text.md)。早期「無框整句（BUY）」是乾跑分類；本輪沒有觸發掃框失敗回退，該分支仍未由此收據驗收，不能把畫面名稱當作實作分支證據。可支付選項未到，四行來源仍pending。

## 2026-10-01：ABANDON2殖民地名稱變數（DRAFT）

由[目標181](../goals/181-colony-remaining.md)正常單居民職業第二頁點前鋒，實際收到棄城確認；正文回原文並記錄variable-without-term，兩選項已有中文。正常點第二選項已回到殖民地；未接受棄城或完成裝備。

confirmed：固定GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`中@ABANDON2唯一標記在檔案位移0x1A38，至下一真正段落前共274位元組、片段SHA-256 `b8cbc33af3cf5f227f5443923ac1f01400dcec0a49ac2e273d49fefd4055f891`，含%STRING0。版面指令不是段落終點。GUI正文實際代入Jamestown；目前一般文字變數只能查譯名，缺少此值時依既有守門回原文。

待補：原版名稱參數與來源搬運的最小定位、正文逐欄墨跡／安全區及最長預設／玩家自訂名稱排版。使用者既有殖民地名稱顯示決定仍沿規格038，但未據此擴張全部未知文字變數。來源輸入、工具及地址空間由目標181／研究日誌提供；本節不授權正式匹配器修正，不宣稱原版規則或棄城結果已驗。

## 2026-10-01：棄城正文來源勘誤與名稱欄位補審（READY）

本節訂正前述DRAFT把選項模板ABANDON2當成實際正文來源的歸屬；舊GUI、DRAFT與兩份查詢未命中的收據保留。正文唯一本體模板為`GAME.TXT:@ABANDON:0x00001994`；ABANDON2包含1600年後的額外警告，未在本次正文顯示，不得加入中文正文或推定它已觸發。正文的名稱修正只授權ABANDON的%STRING0，ABANDON2仍未知。

- **confirmed，原始來源：**GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；@ABANDON唯一標記檔案位移6514（0x1972），正文及兩選項片段位移6548（0x1994）、158位元組、SHA-256 `d9cf0aa7ce8612c94a9da8b0f4b02b74f6319cabb1cb0803bc304a421ae36f67`。原版74066614步由真實模式CS:IP 0E2D:0832、F3A6／CX1完成@ABANDON比較，標記／查詢鍵線性RAM149980／174894，返回9320:00D7；74050818步從GAME.TXT位移6144讀512位元組至1C6A:E962，涵蓋原始段落標記。原版與正常COLONY01.SAV指紋、工具版本沿目標181；上述RAM、檔案位移與CS:IP基準分列，不替函式改名。
- **confirmed，玩家可見值：**正常單居民職業第二頁點前鋒後，正文代入Jamestown，並保留兩個確認選項；正常取消可回到殖民地。175個排版案例不是175個原版局勢，只驗固定來源的譯稿與名稱欄位。
- **名稱契約：**只在上述已取證正文模板的%STRING0使用殖民地名稱顯示回呼；由規格038已核對COLONY.TXT原始位移／片段／版本的colony-bilingual.tsv取得預設名，沿使用者決定顯示「中文（原名）」。其他名稱原樣顯示，且優先於一般術語查譯，以免自訂名被誤譯。只有字串層的來源與字模綁定均有效、對話框層有效時才接回呼；缺少回呼維持原守門。含花括號而不能按原樣交給既有強調碼解析器的名稱回原文並記錄；百分號未解與缺字／超界沿既有回退。不得將此回呼套到其他未取證模板、變數或原版記憶體。
- **逐欄量測：**正文由0D21:00C6在74341060步讀取，線性RAM來源174672；原始墨跡[67,104,249,132]，安全區[65,101,254,134]，放大756×132。首個S獨立墨跡[67,104,72,111]、高7、基線110；三行原版基線按10邏輯像素前進，觀測器整段最大大寫高度8，包含各字的既有墨跡量測。沿30～20px候選，實際採30px；中文字頂端按安全區與既有字模上緣對齊，仍由dialogMasks重排換行。172個預設名稱與一個一般自訂名、27個W壓力皆30px、最右753及最低116，在安全區內；255個W壓力回退0。壓力長度不宣稱原版名稱上限，未增刪正文或自行加入1600年警告。
- **READY審查：**可在dialogCatalog增加只作用於上述名稱欄的顯示回呼，live_menu在有效字串層／對話框層接入現有名稱清冊；不新增翻譯文本、資料格式或原版規則。正文及同文選項的普查都須以相同GUI輸入／完整原版終點的@ABANDON查詢定位歸屬，不由選項模板名推定。
- **正式驗收：**匹配器須驗預設名、自訂名優先於術語、缺回呼、花括號拒絕、其他模板與變數維持拒絕；現行Go回歸通過後重建前端，從正常主選單讀檔到棄城確認、正常取消，核對GUI正文／兩選項、中文／英文／缺圖集完整原版狀態，保存原始查詢證據並再重跑矩陣／普查，才升限定CONFORMED。

原型與排版入口在[目標181](../goals/181-colony-remaining.md)；abandon-prototype-v22/layout.json SHA-256 `635bcbed964f458629bcea8aa5177108006f0aeb4f919acef0edc7c3646a90f3`、source-layout.json `2396f9a2faf607fab85e8c54c35c49b905d08af41198b64d3f425bd40bd3790e`；abandon-source-v21/source-abandon.log.matches.json `a9dac580bb4ff283e07eb653d42d200f6d554e826976878a5569ecf7714c4734`。正式來源尚未改動時，原型完整RAM與原版GUI86800000步均為`fd49783470638455412ab136f5d549281042ce7f55e0b645e8d2bc8b89eed1fc`。

## 2026-10-01：候選印字被抹除的收尾補審（READY）

city-abandon-v23正式驗收拒絕取消後的中文選項殘留，不能升CONFORMED。原版英文控制已正常回到殖民地；本節修正的是覆蓋候選生命週期，沒有改變原版流程。輸入與原版檔案指紋沿本規格及[目標181](../goals/181-colony-remaining.md)，工具為dosgolem隔離副本b0bf259、Go1.26.7、colonization-verification:20260930-r1；只比較觀測器事件步數與線性畫布0x2CAE0，不將其當成檔案位移或原版函式地址。

- **confirmed：**最後一次選項重印從81024875步開始、81075401步最後讀字，直到81176439步才由下一個來源收尾。舊觀測只在最後讀字後20000步內記錄寫入，漏掉其後正常城市重畫。延長到實際收尾後，762個仍由印字常式最後寫入的點降為0；第一、第二次正常選項重印仍各有762點，不被拒絕。原型文字被完全抹除時回原文，確認正文／兩選項不變，取消後選項區恢復原版；完整CPU、RAM、輸入、開檔、索引、色盤與八個GUI取樣點均相同。摘要city-abandon-v23/lifecycle-prototype-summary.json SHA-256 `8316de306b217a41dbb823b1a6d5ae2d296072b6b5cc097db08f12af2ab9eb20`；基準／候選紀錄SHA-256分別`5bf562a167cbe8f4e9121c25682c50608a486460017a03b7f6a7289082e4712d`／`987bc7b5334bbfbca5772ba1cb840ecf83213a5c412d24a21b038b950dbca971`。
- **READY契約：**dialogRun存在期間持續記錄畫布寫入，直到實際finish或onRead切換候選；dialogGap只控制讀字分段，不提早停止寫入觀測。候選已有印字寫入紀錄，但收尾時沒有任何最後寫入者仍為印字常式，則整段拒絕並記錄text-erased-before-finish；不產生中文遮罩或啟用事件。部分墨跡被肖像、游標或選項背景覆蓋仍沿既有規則，不由此改變遮擋顯示策略。
- **驗收：**用自製畫布驗證完整抹除被拒絕、部分抹除及游標不被此條件拒絕；Go回歸通過後重建正式前端，重走主選單正常讀檔、確認與取消，三側原版狀態相同、GUI安全區相同且取消後無選項覆蓋。重跑矩陣與普查前不增加完成數。原型只有同輸入重播，不取代正常GUI；不宣稱其他關閉路徑已驗。

## 2026-10-01：ABANDON正文與正常取消限定CONFORMED

名稱欄位與完全抹除候選契約已正式實作。全部前端Go測試通過，包含預設／自訂名稱、缺回呼、其他變數拒絕，以及完整／部分抹除、游標覆蓋的回歸。正式二進位abandon-final-build-v25/colonization-window SHA-256 `8ac21a84e0792917a6e20c13ff0239a1f3a2c8c1300c41774ee71e94591465ec`，適配器`7824fcf0958fb5a967667e2c17b5ab22bb6cce8c88a89c1e5d4471610ef67d15`、對話框模組`4cb731eacdad036cfc57fbf53d6036d5ce52318e070c416a48cb9b5b8be0eb7b`。譯稿與正式字模未改，175案例的逐欄量測沿READY證據，不重新聲稱原版名稱長度上限。

city-abandon-v25正常從主選單讀COLONY01.SAV、進城、職業第二頁點前鋒、棄城確認及取消；正文74036409步、選項74150826步，兩欄安全區與30px字級符合READY。八個GUI取樣點、中文／英文／缺圖集完整CPU、RAM、索引、色盤與輸入相同。取消後城市三欄恢復，原棄城安全區扣除這三個已驗城市欄位後與英文控制逐像素相同，沒有選項殘像。終點86800000步RAM `3a2a2f6271ee237570af64c244805325f798f6658f4299a8573151277ce7ed61`，正常GUI輸入`48041fe90d4a4b7f4272dc1b6bea460e2c3dafd7d455d9407af59b164d050f5c`；原版來源在73876380步查詢ABANDON、73860584步讀GAME.TXT6144／512位元組，RAM參數、返回位址、指令與片段雜湊沿READY定位。選項同文模板ABANDON2仍只映射到本次實際ABANDON，不提高ABANDON2完成數。

check_goal181_city.py --require-jobs --require-more --require-abandon --lookup-reports同收據目錄通過；確認像素、取消殘像、錯誤來源鍵、錯讀取位移、錯輸入綁定與偽造RAM六個負例均拒絕，原版缺失SKIP77。matrix-v25為39PASS、無失敗／過期／原版指紋衝突；census-v25為794已顯示／1013待接／89不可達，分母1896。移除本收據後只少ABANDON，ABANDON2兩側均pending。具體摘要、雜湊及重生入口見[目標181](../goals/181-colony-remaining.md)。只驗本次正文、選項與正常取消，不宣稱接受棄城、ABANDON2警告、武裝或其他關閉路徑已驗。

## 2026-10-01：讀檔成功檔名欄位續驗（DRAFT）

本節只探勘 `GAME.TXT:0x00000854` 的 `%STRING0`，不改存檔名稱、資料格式或原版記憶體。GAME.TXT SHA-256 沿本規格；原始片段為29位元組，SHA-256 `9c7e7034756620ffc8d6b3a3e7675e61cf78e4d5a3062341857986af099ec14c`。譯文沿既有 `text/draft.zh-Hant.tsv`，檔名保留原值。

**confirmed，限定來源：**由正常主選單第三欄讀取已驗 COLONY02.SAV，原版在38655172步以實模式 CS:IP `0E2D:0832`、指令 `F3A6`／CX1 比較 `@LOADGOOD`；標記／查詢鍵線性RAM149980／174438，返回 `9320:00D7`。38646026步由GAME.TXT檔案位移2048讀512位元組至 `1C6A:E962`。觀測器44200000步終點RAM為 `edb32fb3f9a784dbf5e6f3ef85799af29979f10bf9d42dfd8a7f725b9e6125fb`，正常GUI輸入雜湊 `d8a123bf1bd29045b3082566cbc9437a816250a89aa7d8a74df6abec8eb43189`。工具為dosgolem隔離副本b0bf259、Go1.26.7、colonization-verification:20260930-r1；檔案位移、線性RAM與實模式位址分列，不以名稱取代定位。

**候選契約，未授權正式程式：**只在上述模板及變數接受 `COLONY` 加兩位十進位數字與 `.SAV` 的完整原值；不經一般術語翻譯。其他格式記錄 `unverified-save-filename` 並回原文，其他模板及變數沿既有守門。這是顯示欄位的有限候選集合，不能據此推定原版允許的所有檔名。SAVEGOOD有其他變數，不能沿用本例外。

來源入口為[目標181](../goals/181-colony-remaining.md)索引的本機 `load-source-v39/`；可丟棄原型 `load-prototype-v40/`。原版墨跡高度、基線、安全矩形、中文字級候選、最長檔名量測及正常GUI驗證仍待補齊；證據審查升READY前不得接入正式路徑或增加完成數。

## 2026-10-01：讀檔成功欄位證據補審（READY）

**confirmed，逐欄量測：**沿上述原始檔、片段及工具版本，正常GUI印字38689888步由 `0D21:00C6` 開始，線性RAM來源174216。完整墨跡 `[67,95,235,104]`，首字L含陰影的墨跡 `[67,95,71,103]`；大寫字最大高度8，單行預設行距12。逐行清冊命中既有譯稿，沿規格036的安全矩形 `[66,94,237,106]`，放大為684×48。中文字級候選30～20px，實際選30px；文字上緣依原版行上緣95對齊，陰影仍由原版色號決定，不將中文字型基線冒稱為原版字型相同。原始主色／陰影的逐字墨跡與色號在 `load-prototype-v40/geometry.log`，沒有套用其他欄位的固定字級。

**confirmed，有限排版集合：**100個 `COLONY00.SAV`～`COLONY99.SAV` 候選檔名均沿既有譯文與字模採30px，墨跡最右423、最低36，位於684×48內；不需要截斷。候選格式長度固定，其他格式回原文並記錄，不能據此宣稱原版全部檔名規則。排版 `layout.json` SHA-256 `689de4963ead52e353d44cf602306e536877d0b52099b10cf72cd83178b5391d`。格式拒絕、一般術語優先序隔離與其他模板／變數的拒絕皆已由私有原型測試；兩次測試誤用語料載入入口的紀錄保留，改用正式 `addDraft` 後乾淨通過。

**READY契約：**正式匹配器可僅在 `GAME.TXT:0x00000854`／`%STRING0` 對完整格式 `^COLONY[0-9]{2}[.]SAV$` 保留原值；其他格式回退原因 `unverified-save-filename`，其他模板／變數照舊。正規式預先編譯，不在每次命中時重建。不新增翻譯字串、資料欄位或圖集；不改原版RAM、DOS讀寫或存檔名稱。現有逐行排版、缺字與超界回退、來源與圖集指紋守門仍適用。

**審查及驗收：**原型與原文控制107400000步的完整CPU／RAM／輸入／原始畫布相同，讀檔取樣在實際44220000步的RAM／索引／色盤也相同。來源觀測器v39終點44200000不是該取樣步，不把不同步數的RAM並列當同狀態證據。正式實作後須跑全部Go回歸，從正常主選單第三欄讀取v35初始COLONY02.SAV、關閉提示回世界，核對中文／英文／缺圖集原版狀態、中文安全區及保存檔未改；再以同一GUI輸入重生 `@LOADGOOD` 來源與完整終點。正式收據通過前不增加矩陣／普查，不外推SAVEGOOD或讀檔失敗訊息。

## 2026-10-01：LOADGOOD成功提示與正常關閉限定CONFORMED

READY檔名守門已正式實作，全部前端Go回歸通過。前端load-final-build-v42/colonization-window SHA-256 `a04326118f6667326da8b02b13013cfd8bee2227022713bc10b9da3cdc365bff`；對話框模組 `225c520a353c2b70565925dbd010c9171e0ed41b58afa68de61e50e964722c2c`。適配器及正式譯稿／圖集未變，原始片段、100檔名量測與30px逐欄策略沿READY證據。

load-normal-v43正常主選單第三欄讀COLONY02.SAV，取樣讀檔選單／成功提示／回世界；三個共同原版取樣點、正常GUI安全區、中文／英文／缺圖集完整CPU、RAM、索引、色盤及原始存檔一致。中文差異只在核准安全區，關閉提示後沒有LOADGOOD覆蓋，缺圖集整幅回原文。完整終點51000000步RAM `a20427ebaa4975b5cae8f525560a3e19d62657565113a000dc497b48f5774565`，正常GUI輸入 `e0daa812a14004e4440f9b087248349ac8a8e61f62a4743fa2541df0b94919e2`；同輸入觀測器load-source-v44重新生成LOADGOOD查詢，完整終點RAM相同，原始實模式位址、線性RAM與DOS讀取定位沿READY。來源證據完整副本在同收據目錄trace.json.matches.json。

check_goal181_load.py通過；超界像素、GUI像素、錯來源鍵、錯讀取位移、錯輸入綁定及偽造RAM六個負例拒絕，原版缺失SKIP77。初次負例夾具重寫輸入JSON導致來源鍵／位移負例先被輸入守門拒絕，舊紀錄保留；保留原始輸入位元組的乾淨重跑確實由來源／位移守門拒絕。正式負例為load-negative-v46/negative-final.json。matrix-v47為40PASS、0SKIP／FAIL／過期／指紋衝突；普查只將LOADGOOD升shown，正常讀檔槽位的合併觀測另列來源位址未知的pending，不把成功提示當作整個清單已驗。

重生入口、摘要與雜湊見[目標181](../goals/181-colony-remaining.md)。本次只驗COLONY02正常成功提示與關閉，不宣稱其他檔名格式、SAVEGOOD、讀檔失敗、全部存讀檔或整局中文化完成。

## 2026-10-02：城市改名兩欄來源與排版審查（READY）

本節承接目標181的DRAFT。正常主選單第四欄讀COLONY03、進城並點標題，原版於57470473步實際查詢RENAMECOLONY。GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；檔案位移3917～3977的61位元組段落SHA-256 `da21c1451e15435126a4ab5c6eb15a1413b92a08531fbb09cd0deb3fbd19158c`，提示始於3932，Name標籤始於3969。

confirmed：實模式CS:IP `0E2D:0832`、F3A6／CX1；標記／查詢鍵線性RAM149980／175388，返回9320:00D7。57451427步從GAME.TXT位移3584讀512位元組至1C6A:E962。來源觀測器與GUI及三側重播的89000000步完整RAM均為 `27aad5118f3560b3f139702e81c784e4378cb60bcc9211f5d6a11e7e9cf9bea9`，輸入SHA-256 `3857d61dc51181fa36874b2729fc4a197ef94279bf26241efdb807f15f282cf1`。工具為隔離dosgolem b0bf259、Go1.26.7、colonization-verification:20260930-r1；檔案位移、線性RAM及實模式位址分列。

| 欄位 | 原版墨跡／含陰影大寫字高 | 安全矩形及四倍畫布 | 中文候選與選用 | 最長現行譯文量測 |
|---|---|---|---|---|
| 提示 | [62,87,217,96]；W為[62,87,68,95]，高8 | [61,86,219,98]，632×48 | 30～20px；30px | 這座殖民領地要改成什麼名字？；進位寬462，含陰影墨跡[6,4,462,36] |
| 輸入標籤 | 全行[62,103,152,112]；Name標籤[62,103,88,111]，N高8 | [61,102,89,113]，112×44 | 30～20px；29px | 名稱：；進位寬93，含陰影墨跡[17,4,98,35] |

confirmed：兩欄行距12，中文墨跡上緣分別對齊原版y87／103；中文基線由字模定位，不稱為原版字型基線相同。標籤沿既有輸入前綴右緣對齊，30px進位寬99使起點9低於欄間留白界12，29px起點15可容納。提示30px中文墨跡高28，標籤29px高27。超長200次重複均回退0，不裁切或猜測分頁。量測為rename-layout-v52的body／label-measurement.json，SHA-256分別 `3c6a049c882eda8d0768afa0b61237b56bea045fb0c428863985be9b3c1bd6d3`／`b6a8734d1b0fa0a43c5835f6aee9292da31278afc2689dbe284b66cbd624c428`。私有診斷只附加觀測，正式排版函式未改；第二輪完整原版終點一致。首輪診斷把不含標籤定位的姓名重印當新欄位而退出，已保留attempt1.log，不作完成收據。

READY契約：提示沿規格036逐行清冊，標籤沿本規格既有輸入前綴；保留Jamestown及編輯游標原文。缺來源、缺圖集、超界或不識別的前綴維持原文。兩欄均通過正常GUI、中英／缺圖集同狀態、英文姓名編輯及取消無殘字後，檢查器才可對提示欄附加唯一來源GAME.TXT:@RENAMECOLONY；標籤本身不建立另一個原始來源。此規則只採本次已確認的段落，不外推同文Name標籤或其他輸入結果。正式來源與譯文均不需要變更。

驗收入口為[目標181](../goals/181-colony-remaining.md)索引的tools/check_goal181_rename.py；正常GUI、來源v51及量測v52各自保留輸入與完整終點。尚未完成矩陣／普查前不提高807完成數，不聲稱接受改名或任意名稱長度已驗。

## 2026-10-02：城市改名提示、輸入標籤與正常取消限定CONFORMED

沿READY既有正式v65前端、譯稿與圖集，沒有修改原版或正式Go來源。rename-gui-v50正常讀COLONY03、進城、點標題；九張GUI與中文重播逐像素相同，中文／原文／缺圖集九個原版取樣點及四側完整CPU、RAM、索引、色盤、輸入與開檔一致，初始存檔不變。Backspace後原版姓名變為Jamestow，再輸入n，Escape取消；兩欄保持中文，英文姓名區逐像素保留，取消後兩安全區無殘字，返回世界。完整89000000步RAM及來源觀測器雜湊沿READY，不把來源工具的完整RAM雜湊記錄冒稱為匯出RAM副本。

tools/check_goal181_rename.py正例通過，十種偽造收據拒絕，缺合法原版SKIP77。新檢查器曾誤用中文比較函式於原文控制、未涵蓋STRING:input-label生命週期、要求來源工具不存在的RAM檔；均為檢查器問題，按實際輸出格式及source／active／expired事件修正，正式前端未改。矩陣43PASS、無SKIP／FAIL／過期／原始輸入衝突。普查兩次逐位元組相同：1897列，808已顯示／1000待接／89無法正常觸發、EXE346，未歸類及未使用樣式0。唯一完成狀態變更為GAME.TXT:@RENAMECOLONY，兩個顯示欄位只算一個段落。移除改名矩陣列，TSV及Markdown均逐位元組恢復原807／1001清冊；其他五列只追加本收據的命中或既有欄位紀錄，不升完成。

逐欄字高、候選30～20px、正文30px／標籤29px、基線對齊與超界回退沿READY量測；原版姓名資料保留。普查夾具首輪錯把新增命中／收據欄當完成狀態變化，已用同一組收據修正核對，不重擲或挑選執行結果。此結論只涵蓋兩欄、編輯及取消，接受改名與其他輸入長度尚未驗。摘要、雜湊及重生入口見[目標181](../goals/181-colony-remaining.md)。

## 2026-10-02：SAVEGOOD複合描述與完整正文（READY）

本節承接目標181的DRAFT；只顯示原版正常保存成功提示，不修改存檔、檔名、遊戲資料或流程。GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；正文位移1977、長27、片段SHA-256 `68950b5338b58ed3b14b56bcc94333d8794be024547b7be88d4323e44ed64284`，含STRING1複合描述與STRING0檔名。沿既有draft譯稿，不新增文字語料或圖集字元。

confirmed：v41正常主選單讀COLONY02、加入第二居民、離城、GAME→SAVE第四列生成COLONY03，95040000步提示已顯示三行；v45實際於94757031步查SAVEGOOD。實模式CS:IP `0E2D:0832`、F3A6／CX1，標記／查詢鍵線性RAM149980／175356，返回9320:00D7；94735602步從GAME.TXT檔案位移1536讀512位元組至1C6A:E962。輸入SHA-256 `5fc362812c6b1d17d083c2000edf137889ac4d97b0ede17fcd5ee25be57e29ca`；私有原型v55完整107400000步CPU、RAM、索引、色盤、開檔／輸入與原文控制相同，完整RAM逐位元組一致，SHA-256 `b16aa0a125e455172585e26d7fca028e3a23714525ea1f7d66346b6ebbfdebd0`。工具Go1.26.7、隔離dosgolem b0bf259、colonization-verification:20260930-r1；位址空間分列，不以原始查詢位址冒充存檔DOS呼叫位址。

confirmed，顯示成分：正常描述含難度Discoverer、Walter Raleigh、English、Spring及1496。NAMES.TXT SHA-256 `4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061`；SEASONS標記位移182，NATIONALITY2395，LEADERNAME2842，DIFFICULTY3071。現有F10 score-title模板使用相同角色及詞典。難度、國籍、季節經已綁定來源的字串詞典翻譯；姓名沿既有輸入內容保留原文的決定。候選姓名／年份的字串守門測試只證明顯示層能力，不宣稱原版接受長度、編碼或年份範圍。

confirmed，逐欄量測：v55原版印字94810072步、入口0D21:00C6、線性RAM175134。三行墨跡[67,85,216,94]、[67,95,216,104]、[67,105,139,113]，各行大寫／數字含陰影字高8／9／8，行距10。首字D含陰影[67,85,72,93]，原版墨跡末列92；中文依本規格木框內距在安全區[65,82,254,115]重排，畫布756×132，中文墨跡上緣按既有內距4輸出像素，ASCII字模可高出2像素，均在安全區內，不宣稱與原版字型基線相同。候選30～20px，現行描述與100個COLONY00～99.SAV候選均選30px；現行含陰影墨跡[6,2,730,76]，長200次重複回退0。排版及匹配摘要在save-prototype-v55/save-measurement.json／matcher-layout-cases.json，匹配器160個成分組合、七種拒絕及其他模板隔離已通過。這些是排版／值守門候選，不冒稱160條原版玩家路徑。

READY契約：addDraft在原檔SHA、片段位移／長度／SHA核對後，只讓GAME.TXT:0x000007B9加入完整段落模板，避免把原版折行後的三行分別猜譯。只有此模板的STRING0接受完整COLONY兩位十進位數字.SAV並保留原值；只有STRING1經存檔描述回呼。回呼由字串層來源與圖集綁定有效時接入，接受已取證的五種難度、四種國籍、Spring／Autumn及十進位年份形狀，姓名保持原值。姓名只接受可列印ASCII，拒絕{}與%等模板控制碼，其他成分均查既有詞典，任一缺項拒絕；缺回呼／未知格式記錄unverified-save-description，檔名錯誤記錄unverified-save-filename，超界沿既有layout-overflow回原文。這是顯示字串形狀契約，不推定原版可產生所有候選。其他模板／變數不取得例外，LOADGOOD、ABANDON及F10行為保持既有規則。

正式驗收：全部Go回歸後，從正常主選單讀已驗COLONY03並由GAME→SAVE選另一個空列，核對正常中文GUI安全區、三側共同原版點及完整CPU／RAM／索引／色盤／開檔／輸入相同、新舊存檔位元組相同、關閉成功提示無殘字、缺圖集回原文。來源探針須用同一GUI輸入重生SAVEGOOD與正常DOS建立／寫入結果，不沿用v41來源冒充新收據。完成之前不提高808或聲稱其他存檔結果已中文化。入口見[目標181](../goals/181-colony-remaining.md)。

## 2026-10-02：SAVEGOOD正常另存成功提示限定CONFORMED

依前節READY實作，正式save-final-build-v55全部Go回歸通過。只有已核對的正文鍵提升完整模板、STRING1限定描述回呼及STRING0兩位數檔名保留；其他模板不取得新例外。正常save-gui-v56從主選單第四列讀COLONY03，GAME→SAVE第一空列生成COLONY00，再正常Enter關提示、關窗。七張真GUI與中文重播逐像素相同，中文／原文／缺圖集七個原版取樣點及四側完整CPU、RAM、索引、色盤、輸入與開檔一致；新COLONY00在四側及來源重播的24343位元組相同，舊COLONY03不變。

confirmed：新正常輸入SHA-256 `4fa9a6d33dfc54ed7c17ebb11de0bafbf541e4f6a0e713cb0d877e4c2f511d0f`，完整77200000步RAM `8f465db64ffdc0eb4ffb0afa74ecdd51e956458b1ab6e03eb308429f3d8743a8`。v57同輸入原版於64895084步查SAVEGOOD，64873669步從GAME.TXT位移1536讀512位元組至1C6A:E962；原始0E2D:0832、F3A6／CX1、標記／鍵線性RAM149980／175356、返回9320:00D7與READY一致。正常DOS64761371步建立COLONY00、64761411步開啟，22次寫入只指向00且總24343；工具未記DOS操作CS:IP，不用查詢位址冒充寫檔位址。來源僅記完整RAM雜湊，沒有匯出RAM副本。

confirmed：正文原版64948187步印字、0D21:00C6、線性RAM175134；安全區[65,82,254,115]、原版三行行距10及字高8／9／8，最高9是數字9含陰影[155,95,160,104]，大寫D高8。v58正式函式量測候選30～20px，選30px／中文字墨跡高28，實際含陰影墨跡[6,2,730,76]在756×132內，基線與內距沿READY。200次正文重複回退0；100檔名與160描述組合沿v55回歸，只證明顯示守門及排版，不冒稱原版接受全部組合。最初候選量測用僅含單一字級的圖集，缺起始30px時提早回退；已改用正式dialogWrap及高度契約補算，原版重播、正式排版及選定30px不變。

tools/check_goal181_savegood.py正例、十二種破壞收據拒絕、缺原版SKIP77通過。提示中文不超出核准區，關框後SAVEGOOD停用，區內與開框前的既有中文狀態欄差異逐像素相同。初次檢查把安全區右緣既有狀態欄當殘字，經開框前／後對照訂正，沒有放寬原版同狀態或邊界驗證。完整矩陣44PASS，無SKIP／FAIL／過期／指紋衝突；普查兩次一致，1897列、809已顯示／999待接／89無法正常觸發，唯一完成變更GAME.TXT:@SAVEGOOD。移除本矩陣列後TSV／報表逐位元組回到808／1000。本結論只採本次正常保存成功提示及關閉，其他存檔錯誤、槽位清單及其餘教學／事件仍待驗。來源與雜湊索引見[目標181](../goals/181-colony-remaining.md)；原版資料／像素只留workplace。

## 2026-10-02：正常存讀檔標題與槽位清單（READY）

由目標181的v61～v65 DRAFT證據審查而來。正式來源仍為save-final-build-v55，原型尚未接入正式程式。本節只授權顯示層處理兩個標題及其緊接的原版槽位清單；不修改原版畫布、槽位、存檔、滑鼠或遊戲流程。

原始來源：GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`，LOADGAME正文位移2086、長19、片段SHA-256 `e0ab1b9b4e583ecfb817c85c871ee3b4bd090c0ece407d5a16f3b4c3747b2060`；SAVEGAME正文位移1934、長16、片段SHA-256 `878776aeff5b72d1b8452611a0d8c64f65b145fc574db91ed3867c7689aab5a3`。VICEROY.EXE SHA-256 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`，唯一EMPTY片段位移129678、長7、片段SHA-256 `9251e2d6e3d0ccd4ce35aa27a82a36251ad36af2cb17b229c34a3daa2f0cdaa7`。NAMES.TXT角色、來源指紋及姓名保留規則沿SAVEGOOD READY。工具為Go1.26.7、Ebiten2.9.9、隔離dosgolem b0bf259與colonization-verification:20260930-r1。

confirmed：v62正常輸入 `4fa9a6d33dfc54ed7c17ebb11de0bafbf541e4f6a0e713cb0d877e4c2f511d0f` 的原版查詢為LOADGAME31975372步與SAVEGAME57879026步。兩者在實模式0E2D:0832執行F3A6／CX1，標記線性RAM149980，查詢鍵分別173808／174726，返回9320:00D7。GAME.TXT分別於31969125步讀位移2048、57860500步讀位移1536，各512位元組至1C6A:E962。77200000步完整RAM `8f465db64ffdc0eb4ffb0afa74ecdd51e956458b1ab6e03eb308429f3d8743a8` 與正常GUI相同；來源工具只記錄完整RAM雜湊，沒有RAM副本。位址基準分列，不把查詢位置冒充檔案操作呼叫位置。

confirmed：31985970步從線性RAM124814讀EMPTY，原指令位置0E2D:07F9；後續複製、讀字串與印字觀測保留於v62 read-diagnostic。此點前後39位元組與VICEROY.EXE129660～129698相同，含EMPTY與SAVEGAME鄰接字串。只確認該片段，不以局部吻合宣稱整份EXE的載入位址。描述的難度、姓名、國籍、季節與年份由原版展開；顯示層不解析或改寫SAV。

confirmed：LOADGAME原文墨跡[65,67,133,73]、大寫／數字高5。舊安全區[64,66,135,75]只有(64,74)不同：真VGA為130、邏輯畫布為138，其餘638點相同。31852549步原版已複製該點到VGA，32059113步0CAE:00A8只改邏輯畫布位址206752，VGA位址679104沒有同步更新。它在下一槽位反白區的留白，沒有標題墨跡。新安全區底緣限定原文末端後一列，即[64,66,135,74]，保留全部原文字形與中文墨跡。不放寬像素比對、不延長逾時。

| 欄位 | 原版字高／行距 | 安全矩形 | 輸出畫布 | 選定字級／墨跡 |
|---|---|---|---|---|
| LOADGAME標題 | 大寫5、單行回退行距9 | [64,66,135,74] | 284×32 | 21px／[6,4,186,23] |
| SAVEGAME標題 | 墨跡[66,65,119,71]、大寫5、回退行距9 | [65,64,121,73] | 224×36 | 21px／[6,4,140,23] |
| 讀檔10列 | 大寫／數字5、行距6 | [68,74,254,136] | 744×248 | 21px／[5,2,422,241] |
| 存檔8列 | 大寫／數字5、行距8 | [69,74,255,138] | 744×256 | 21px／[5,2,422,249] |

每欄候選22～15px，22px中文字墨跡高21超過原版字高四倍20；21px高19可容納。沿lineLayerMasks原位對齊，中文字上緣對齊各原版行上緣，ASCII可高出2輸出像素，均在安全區內。未改全域字級。兩份清單各160描述候選均21px，最長前進寬516像素，為西班牙發現者與Anne-Marie O'Neil組合。它們是顯示／排版候選，不稱為原版可輸入範圍或320條玩家路徑。200次中文重複與1000字元ASCII姓名均回退0，不裁切。

READY實作契約：

- 沿現有TSV欄位，以新VICEROY.EXE片段列保存空欄譯文「（空白）」。只把唯一且片段核對正確的列載入槽位專用值，不加進一般字串詞典。原檔、位移、長度或片段SHA不同即拒絕；缺列、空譯文或有效字模不足時整份清單回原文。
- 槽位回呼只在目前候選為LOADGAME／SAVEGAME標題，或目前候選為本清單且其前一個標題仍有效時開放。只採8列或10列，每行須為完整EMPTY或已確認描述語法；其他行數、項目與畫面回原文。標題由原始GAME片段核對後的鍵確認，不靠寬度或顏色猜畫面。
- 描述形狀為難度、原名、of the、國籍、逗號、季節、十進位年份。角色查既有來源綁定詞典，姓名沿SAVEGOOD的可列印ASCII與{}／%拒絕規則保留原值；未知值拒絕。逗號語法只在槽位回呼，不加入F10、一般字串或SAVEGOOD模板。
- 本清單所有已觀測、最後由文字常式改色的像素須完整存活。部分墨跡存活時拒絕整份清單，不沿一般正文的單點alive條件。反白重印只替換同一清單，保留仍active、不重疊且完整安全區與原版畫布相同的前一標題。其他新訊息仍依原有規則撤銷。
- 字級仍由原版cap高、安全矩形與行距量測選擇；未知原始字形或布局不擴張這次READY範圍。維持原文並記錄原因。

v65原型完整CPU、RAM、索引、色盤、輸入／開檔及新舊存檔與v56相同；六個清單反白取樣點啟用，最後部分擦除清單在64845000步拒絕。兩個首屏新增中文差異只在核准區，關閉後四個畫面與既有正式結果逐像素相同。尚未正式實作或正常新GUI／三側／負例驗收，不宣稱CONFORMED。正式驗收須用新正式前端走正常GUI，涵蓋兩標題、清單、反白重印、實際讀檔／另存成功、關閉及缺字模回原文，重生同GUI輸入的來源及完整原版對照。清冊只採檢查器實際驗過的欄位，EXE:e4351e498b79合併觀測不因本READY升shown；不得先合併未知來源或以新組合數提高完成數。證據、量測與重生入口見[目標181](../goals/181-colony-remaining.md)。

## 2026-10-02：正常存讀檔標題與槽位清單（限定 CONFORMED）

READY 後已接入正式三個 Go 來源及一筆既有欄位的空槽譯稿。譯稿 status 沿原有 draft 契約，授權狀態以本規格為準。空槽只透過來源綁定專用值載入，不進一般字典；全檔、位移、長度、片段雜湊、唯一鍵與零結尾邊界不符均拒絕。既有 TXT 的完整 CRLF 行契約不變。

- 正式 v66 完整 Go 回歸、格式與來源拒絕、8／10列上下文、關框前部分抹除、未知列與缺字模整段回退通過。沿固定 rich2-py 重烘兩圖集、15個選單字模及封裝專用欄位。四欄量測沿 READY 原版字高5及基線，每欄候選22～15px選21px；新正式圖集兩清單各160描述候選、最長516輸出像素及1000字元真寬度回退通過。320組不當作320條原版路徑。
- v67為新正常 GUI：讀第四列COLONY03、存第一空列COLONY00，九張截圖包含移入槽位及關框。GUI與中文重播逐像素相同，中文／原文／缺圖集及v55程式五側完整CPU、RAM、畫布、色盤與原始輸入相同。新舊存檔與獨立原版來源重播逐位元組相同。v55程式對照使用同一份現行譯稿與字模，新增像素只在兩個讀檔矩形與存檔清單；五個關框後畫面完全相同。
- v68以相同新 GUI 輸入重生原版LOADGAME／SAVEGAME查詢、EMPTY片段及描述讀取。原始實模式CS:IP、線性RAM、檔案位移與字節沿 READY 的分開基準保存。終點88600000步、RAM SHA-256為6e446d715610ba27c698ec5e22f5e4bdcc0c0b11fce4b1ad50ea1336b1e7b578。讀取上限100只涵蓋先遇到的讀檔清單，不宣稱所有寫入或讀取已匯出。
- v69正例、16種破壞性反例拒絕及缺原版SKIP77。v70完整矩陣45PASS、零失敗／略過／過期／指紋衝突；普查兩次與移除新列的反向比對逐位元組相同。815已顯示、997待接、89不可達、分母1901；兩既有標題由pending升shown，新增四筆實際空槽、描述與兩份完整清單觀測。第三列有存檔的舊合併觀測EXE:e4351e498b79仍pending，沒有來源別名或160組灌入。

限定於上述正常存讀檔、來源與幾何。其他存讀檔錯誤、未知描述與列數、玩家原版接受範圍、三平台完整版及公開發行未完成。字級與回退不外推其他欄位。完整指紋與重生入口見[目標181](../goals/181-colony-remaining.md)及 tools/check_goal181_slots.py；私有畫面只留忽略的workplace。

## 2026-10-02：港口三正文與教學（限定CONFORMED）

新正式v74／v75正常GUI、109逐欄字級量測、26共同原版點及五側完整原版／存檔通過；十二偽造拒絕與缺原版SKIP77，全矩陣46PASS。正文TUTORIAL17實際26px、RECRUIT／PURCHASE30px、KINGRECRUIT26px；每欄完整原版文字、cap高、候選、基線對齊、安全區與墨跡留v76/batch.json，不外推其他欄位。完整範圍、來源與普查反向比對沿[規格036](036-line-list-and-centered-text.md)最新歐洲CONFORMED節及[目標181](../goals/181-colony-remaining.md)。


## 2026-10-03：歐洲砲台購入確認正常來源（DRAFT，待限定驗收採用）

v79由正式v74正常讀COLONY03、E進歐洲、選500$砲台、Enter確認及正常返回世界，不注入存檔或原版狀態。@REALLYBUY當次完整顯示為Purchase Artillery for 500$?，來源GAME.TXT:0x000126E3，原文43bytes包含正文及Yes／No，SHA-256 4e570fb347e82ac3e9d23cda48b85641ab5c8b91726b4330a1094c12c478cccf；GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a。既有corpus已載「要購買%STRING0，花費%NUMBER0$嗎？」與是／否，正式來源及譯稿未改。

confirmed原版查詢於73859638步，CS:IP 0E2D:0832、F3 A6、CX1、header/key均@REALLYBUY；原版DOS於73848580步讀GAME.TXT，檔案偏移75264、512bytes，覆蓋本模板原始位置。正文印字起點73993832步、選項74025391步，均經0D21:00C6讀字；兩欄74250000步啟用，76065000正常GUI取樣完整中文，確認後關閉回原文底圖。字體證據為原版cap高8、候選30～20px，兩欄實際均30px；正文safe[65,119,254,133]／墨跡[6,4,399,37]，選項safe[70,135,88,158]／行距12邏輯像素／墨跡[6,4,38,84]。沿既有原文字頭／CJK上緣及木紋陰影規則，兩欄1000字壓力量測拒絕。

原版流程確認後國庫1000$→500$，碼頭出現砲台；此為正常畫面與原版狀態觀測，不重寫或逆向推測購入規則。v80核對9GUI與中文重播／觀測副本逐像素相同，五側原版完整終點89600000步、RAM 16aebf0e301c528342f50ca9fa8a9b7c96ceff1714d93a77f25cd16e512f50ea，四個重播／觀測側各9個原版RAM／索引／色盤取樣相同；GUI只記錄完整終點，其餘以實際截圖核對，未補造GUI逐點RAM。全部原版COLONY03字節不變，沒有新存檔。

工具Go1.26.7、dosgolem b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8；輸入SHA-256 0ac94418337b8f120f1bfbd890a605a7c385c8138357c343d7c716fb364c8d3b。字模仍為slot-fonts-v66/dialog，字型SHA-256 8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c。新收據為未採用候選，還須完整名稱／數值排版邊界、公開可重生檢查器與破壞性反例、矩陣及反向普查；不提高850已顯示或將其他單位、其他國家及稅率事件稱已驗。重生入口見[目標181](../goals/181-colony-remaining.md)。

### 購入確認限定READY（2026-10-03）

v81用正式函式及固定實際圖集量測六個原版列表單位、各500／1000／5000／1234567890，共24組，全部30px，最長advance551px，落在756×56安全區。未知單位在模板代入時拒絕，1000位數字在排版時拒絕；組合不當正常原版命中。原版字高、原文字頭對齊、內距、正文與兩選項的生命週期沿本節正常收據與既有規格，沒有新資料格式或顯示演算法。

證據足以授權既有正式實作的限定驗收，升READY；只採v79實際Artillery／500$、正常Enter接受及回到世界，不外推取消、其他單位或稅率事件。v82凍結清冊SHA-256 7abe110f339b307ab58974efcdea20b5c02ccff99b6e720d2a19331edadb56c5，含三個GUI仍啟用的已量測欄位。需通過公開檢查器、破壞收據拒絕、矩陣與反向普查後才限定CONFORMED；正式來源／二進位／譯稿／字模均不改。


## 2026-10-03：正常砲台購入確認限定CONFORMED

READY契約已由v82公開限定檢查器、13種破壞收據拒絕、缺原版SKIP77及v83全矩陣47PASS驗收。正文及是／否在76065000步正常GUI啟用，接受後消失；9GUI全畫面等於中文重播及觀測副本，五側完整原版終點、四側9共同取樣、原版查詢及六份存檔均相同。原版素材／規則／檔案不改，既有正式v74來源與圖集不改。本項只CONFORMED正常Artillery／500$及Enter接受，不外推其他單位、取消、稅率事件。

普查852已顯示／994待接／89不可達、分母1935；僅GAME.TXT:@REALLYBUY由pending升shown，另新增EXE:e9b353ec7941實際500$標題。兩次與移除新列的反向逐位元組相同；24個合成排版不計命中。重生入口及完整SHA-256在[目標181](../goals/181-colony-remaining.md)及purchase-census-v83/formal-hashes.json。

## 2026-10-03：正常職業清單選漁夫與NODOCKS（READY）

v84正常點擊工作者實際開職業清單；拖到水域不出NODOCKS，不以此判定正式規則。v85正常COLONY03進城、點工作者、在職業清單選Fisherman，出現未建碼頭提示，Escape關閉並返回世界。只處理這條提示路徑，不推測拖曳與選單的不同遊戲規則。

原版GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，NODOCKS文字檔偏移0x0000222F、88bytes、原始SHA-256 c1f2938cc745bb4e72761a5f7a586eff3f7f80af0fe89ebc344ee51bad6c1d78。v86同輸入查詢於65265105步，原版CS:IP 0E2D:0832／F3 A6／CX1，header/key均@NODOCKS；65258822步讀GAME.TXT檔案偏移8704、512bytes，完整覆蓋本段原始位置。這些定位為confirmed，檔案偏移與dosgolem CPU位址基準分開。

正文讀字起點65407784步、0D21:00C6／線性174690；原版cap高8，safe[67,118,256,152]，候選30～20px，實際30px／兩行／行距40輸出像素，墨跡[6,4,731,76]在756×136安全區。沿既有原文字頭／CJK上緣、內距與木紋字色／陰影；1000字壓力回0。只採70290000步fisherman-selected的當次完整正文，其他職業列表與名稱不納入本欄。

工具Go1.26.7、dosgolem b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8，字型SHA-256 8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c。正式v74函式、譯文及圖集不改；本固定正文沒有替換變數，長度／換行及超界以實際字模量測，缺字／錯版沿既有原文回退。

證據足以升限定READY並驗收既有實作。v85輸入SHA-256 ff53f8e784f0fdc00e2ff6f35b9a095bb3766e11bc0023eb9b06a9d1d59eafdc，原版終點83800000步、RAM a4489e2908256283354fbc7a140dbaac8e8108357d3f1d7839edb16bc79d41fb；單欄凍結清冊574bac53bd0b5e55ee46a977789153571e03550ee9e15324b5fac6e522732e25。需八GUI、五側完整原版、四側共同取樣、不變存檔、反向原文、破壞收據、矩陣／反向普查全部通過才CONFORMED。原始像素只留workplace，入口見[目標181](../goals/181-colony-remaining.md)。


## 2026-10-03：未建碼頭正常提示限定CONFORMED

上述READY契約由v87單欄限定檢查、13種破壞收據拒絕及缺原版SKIP77通過。v85八張正常GUI與中文重播／逐欄觀測全畫面相同；五側完整原版終點與四側八共同取樣、原版查詢及各側COLONY03存檔均相同。實際字級30px、兩行，候選字級、基線、安全區與超界回退沿本節READY證據。現行v74正式程式、譯稿與圖集不改。

v88全矩陣48PASS，零SKIP／FAIL／過期／指紋衝突。普查853已顯示／993待接／89不可達、分母1935；只將GAME.TXT:@NODOCKS提升，沒有新來源。兩次普查及移除新列恢復v83逐位元組相同。只CONFORMED正常職業清單選Fisherman後的正文及關閉，不外推拖曳、其他職業或COLONYUNIT／UNITOPTIONS。完整雜湊與重生入口見[目標181](../goals/181-colony-remaining.md)及unit-census-v88/formal-hashes.json。

## 2026-10-03：正常單位面板士兵選項（DRAFT）

v90沿正常COLONY03讀檔、職業第二頁選任士兵、切換右下單位面板，再點面板中的士兵。91245000步正常GUI顯示士兵標題，以及警戒／登船、駐守、不做更動三列。標題因術語不識別回原文，清單因實際三列不匹配既有完整五列而回原文。只觀測當次狀態，不自行補顯示原版沒有畫出的兩列。

confirmed查詢來自v91同輸入原版重播。87304385步原版CS:IP 0E2D:0832、F3 A6、CX1，header/key均@COLONYUNIT；89006868步同入口查詢@UNITOPTIONS。兩次前置DOS讀GAME.TXT分別87296831／88996947步，檔案位置39424、512bytes，涵蓋兩段來源。GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a；標題檔案偏移0x9A33、31bytes、片段98b75b596028b5fb6713ca8044c29433a0af0eaad291bba5cfd3a6780577b90f；完整清單檔案偏移0x9A64、74bytes、片段966a3ac7f25ba2a24d86dcccdebdc4e83cb18b596e45474f65d7ef9ab724979f。檔案位移與dosgolem原版CPU位址分開。

工具Go1.26.7、dosgolem b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8；輸入6f6f25dd68756363c2870a0b1e7696c7d45011e7b8710743c3428cd024249d4e。原版來源重播終點104800000步、RAM 6bf7c93b6bbd3b4ad98a9429e2b510905bb7afca7943e61313913ef534281b13，與正常GUI完整RAM雜湊相同。其他完整狀態、三側畫面、字級／基線／安全區、標題兩個變數的代入邊及缺字／未知列表回退仍待驗；本節保持DRAFT，不授權正式新覆蓋或提高853已顯示。重生入口見[目標181](../goals/181-colony-remaining.md)。

v91原版逐字觀測得到三列墨跡矩形[82,91,179,100]、[82,103,116,112]、[82,115,136,124]，cap高均8、行距12邏輯像素；清單讀字起點89081560、線性RAM 175420。墨跡矩形不等於安全區，中文字級及基線仍待候選量測。

既有Go匹配器的窄重現確認兩個相鄰變數均要求非空，實際顯示名稱被拆成S與oldiers，即使完整名稱譯名存在仍回原文。這是內部匹配器證據，不是原版兩個變數的實際值。adjacent_test.go／adjacent-test.sh及結果保存在v91觀測目錄。可丟棄原型可驗同一強調群組的完整名稱及當次三列；未達READY前不得改正式路徑，也不把三列驗收外推至其餘兩列或其他單位狀態。

### 士兵單位標題：限定READY（2026-10-03）

v93原型沿v90正常輸入，完整CPU／RAM／索引／色盤及11共同原版取樣相同；10張畫面完全相同，91245000步只有兩個核准文字矩形改變。單位圖示區[54,74,73,94]逐像素不變，v92錯誤安全區會被同一檢查拒絕。原型審查SHA-256 11a1f87384f55aa0eca7a7cf139ab56bfdf79e63cd737025f0a4aac8141b8925、22個名稱字模量測b5c15ea82caa7f30d9aae163796fa88efad8c38961c5270e8aa9c8de0a2b0b25，入口為目標181的v93/check.py及test.sh。這些是confirmed原版觀測及內部回歸，合成名稱不計正常命中。

限定契約：GAME.TXT:@COLONYUNIT:0x00009A33原始模板、譯稿及來源沿本節DRAFT已列完整指紋。僅該模板同一強調群組中的兩個相鄰變數，按畫面輸出的完整名稱匹配，不推測原版兩個變數的分界。名稱只接受原版NAMES.TXT的@UNIT資料列第一欄；NAMES.TXT完整SHA-256 4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061，每列另驗證資料列邊界、檔案位移、長度、片段雜湊及欄數。Soldiers來源偏移0x2351、55bytes、片段16b28c1d614dcfab05b1b33f5c70178c25fd24e3c9ff4a5d1f96c76e1011c48e，譯名士兵。錯版、衝突、未知名稱與純數字不沿一般術語補譯，維持原文並記錄原因。原版資料只讀，typed輸入為完整已顯示名稱，輸出為既有中文畫布遮罩，不修改原版記憶體、操作或存檔。

標題原版cap高8，墨跡起點[78,77]；沿框掃描取得右緣，將安全區左／上緣至少縮到墨跡左／上緣減1，保留左側圖示。當次safe[77,76,265,88]，752×48輸出像素，候選30～20px，實際30px／單行，中文墨跡[6,4,190,36]。CJK上緣按原版墨跡對齊，強調士兵沿原版149、其他文字68、木紋陰影47；不設定全域字級。22個原版資料列名稱的合成量測最長Colonists、289輸出像素，均在本欄安全區；缺字與1000字元超界均回0並沿既有原文回退。

證據足以授權正式標題匹配修正及名稱來源綁定，升限定READY。正式後須新正常GUI、中文／原文／缺圖集及原型對照、原版來源重播、存檔不變、公開限定檢查與破壞收據、矩陣及普查反向比對，才可將當次Soldiers升CONFORMED。其他22個名稱只有合成排版證據，不宣稱正常路徑已驗。


## 2026-10-03：正常單位面板士兵標題限定CONFORMED

READY後v94正式最小修正、完整Go回歸、go vet及22個名稱的實際字模／來源拒絕通過。v95新正常GUI選任士兵、切右下單位面板，91245000步顯示標題；v96觀測及原版來源、公開check_goal181_unit.py限定檢查與19種破壞收據拒絕、缺原版SKIP77通過。11GUI與中文／觀測全畫面相同，六側完整原版、五側11共同取樣、COLONY03及圖示不變，對舊正式新增像素只在標題和三列安全區。原版查詢@COLONYUNIT為87304386步，正文起點89057791、線性175062；原版cap8、safe[77,76,265,88]、30px單行及墨跡[6,4,190,36]沿READY。原版字框[78,77,175,86]及色號另外記v96/observer/runs.jsonl，沒有抹除圖示。

v97全矩陣49PASS，零略過／失敗／過期／指紋衝突；兩次普查及移除新列反向逐位元組相同。855已顯示／991待接／89不可達、分母1935，只提升COLONYUNIT與UNITOPTIONS既有段落，不新增來源。段落已顯示只代表本次正常Soldiers標題與可見三列命中，不宣稱完整五列、其他名稱或其他單位狀態。其他21個名稱只有合成排版證據。正式字模、譯稿與原版資料不改，沒有新版本或Release。

正式輸入ef063063f70ad0ec29b4ffbd05d4016907f14862a4a5456979259dd906b6236b，終點104800000步、RAM 07b1f33ee16df535112b56cbeb07f517e5b39f4b299ce21d74c9dfac6997e9cc。凍結清冊956e79529691fa8ccdb2eec656f7018b44c6725605a97a787aa8f3835b67cf03、工具及完整來源／圖集指紋入口在目標181與unit-formal-census-v97/formal-hashes.json；含原版像素及存檔只留忽略的workplace。


## 2026-10-03 DRAFT：正常抵港教學與Caravel標題

v113正常COLONY03的Go to Port選Jamestown，沿原版回合推進至1497春，再正常點城市／港口船隻，首次觸發抵港教學，Enter關閉後再點船隻。無座標或存檔狀態注入。v114原版CS:IP 0E2D:0832、F3A6、CX1查詢@TUTORIAL12於107370229，前置GAME.TXT讀107362675、檔案位置81408、512bytes；@COLONYUNIT查詢125235887，前置讀125228860、位置39424、512bytes。原版GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a。工具Go1.26.7及dosgolem b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8；原版CS:IP、檔案位置與dosgolem線性RAM分開。

TUTORIAL12既有譯稿在text/help-bilingual.tsv，原文正文0x00013E94、482bytes、片段SHA-256 11549559cc72e09c0afbf892cdfec59691727500c2051c82a3c0d109c9095559。當次%STRING0為Jamestown；原版11行、上緣76～176、行距10，逐行墨跡cap8／9。ESC及G沿原版149強調，其餘68、陰影47、木紋128。城市名稱代入、完整安全矩形、中文候選字級與最長名稱／回退仍待原型；不補新譯稿或全域固定字級。

Caravel標題沿同一已驗COLONYUNIT模板，原始0x9A33／31bytes及片段指紋沿既有READY。讀字127000936、線性RAM175050，墨跡[78,77,172,86]、cap8；Caravel沿149強調。Caravel原始NAMES.TXT UNIT第一欄0x25FD／7bytes已在sea-status.zh-Hant.tsv與terms.zh-Hant.tsv，譯名輕帆船，來源NAMES.TXT完整SHA-256 4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061、片段840586e8ffd9c2c87d252364e6307a4d380f6adc6e5d72b5e84bd2fd99236255。現有完整名稱綁定只取corpus的22個UNIT資料列，此已覆蓋短名不在其中；不能重複新增譯稿，亦不能以未驗一般術語／數字補過。新的來源綁定與逐欄安全區／候選字級仍待審查與原型，正式Caravel標題保持原文。

正常GUI與未改顯示的觀測13圖全等，完整CPU／RAM／輸入檔／讀檔一致；來源探針另驗完整RAM，三份COLONY03均不改。輸入415d51f9db985d31992f75e3e6c85f60aa649b4e41d863b1274f2eeddaf64543，終點128200000，RAM a7dd7d0fe3e5355bb6deaef09dc4a064229face22b99084359e90431a1ce64a9。這是confirmed原版來源及兩副本觀測，不當三側或新中文CONFORMED。重生與原始資料入口為目標181的ship-source-observer-v114/prepare.py、source/replay.sh、observer/replay.sh、check.py／discovery-summary.json。


### 2026-10-03 DRAFT勘誤：抵港教學尚未取得可見收據

v114證明原版查詢與正文輸出，沒有證明13張GUI取樣中教學仍顯示。v116原型TUTORIAL12在108405000至108570000短暫啟用；舊腳本的ship-options取樣114345000已關框，後來Enter不能當教學關閉證據。名稱回呼與30px五行排版測試通過，原版完整RAM不變，仍僅DRAFT。來源、畫面存活區間及勘誤見RESEARCH-LOG最新節及目標181 v116/state-only-summary.json；v117正常等待抓圖後才可審查READY。


### 2026-10-03 READY：Caravel單位標題

v115原型已通過正常v113同輸入13圖、安全區、完整原版與不變存檔；兩種既有士兵狀態11／13圖、來源鍵及原版完整狀態完全一致，審查清冊SHA-256 e823b0ac1deaf00bd2adbbd9c685c4d0aa10e05e109e5fe4b6449c573ecf862a。只授權COLONYUNIT的Caravel標題及其名稱來源綁定，TUTORIAL12仍DRAFT。

NAMES.TXT完整SHA-256 4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061。原始@UNIT資料列第一欄偏移0x25FD、7bytes、SHA-256 840586e8ffd9c2c87d252364e6307a4d380f6adc6e5d72b5e84bd99236255，所屬整列55bytes。Caravel已有text/sea-status.tsv及核准術語輕帆船，不新增重複語料。保留原本22列的個別來源／欄數／衝突拒絕；只補完整NAMES版本與UNIT列邊界驗證後，尚未有資料列譯名且既有核准術語有安全譯文的首欄名稱。不復活衝突空值，不接受非UNIT國名、數字、未知或控制碼；原版只讀。

標題原版讀字127000936、線性RAM175050、墨跡[78,77,172,86]、cap8；來源@COLONYUNIT查詢125235887步及原版0E2D:0832／F3A6／CX1沿抵港DRAFT。safe[77,76,265,88]，752×48輸出像素；候選30～20px、實際30px單行，CJK墨跡[6,4,223,36]，上緣沿原字首，強調149／一般68／陰影47，左側船隻圖示不變。23個合成UNIT名稱實際字模量測及未知／錯版／缺字／超界拒絕通過，不作23個正常命中聲明。

工具Go1.26.7、dosgolem b0bf259；檔案偏移、dosgolem線性RAM與原版分段地址分開記錄。正式後另跑新正常GUI、中文／原文／缺圖集／舊正式、來源與逐欄觀測、存檔、限定檢查及矩陣／普查才CONFORMED。已測原型輸入SHA-256 415d51f9db985d31992f75e3e6c85f60aa649b4e41d863b1274f2eeddaf64543、終點128200000、RAM a7dd7d0fe3e5355bb6deaef09dc4a064229face22b99084359e90431a1ce64a9；只涵蓋當次港口Caravel，不外推其他船隻局勢。


### 2026-10-03 DRAFT：教學已可見，GUI對齊尚有缺口

v117先等待原版進城教學後再操作，已取得可見30px五行的TUTORIAL12及正常Enter關閉，safe[50,73,269,187]、原版cap9、候選30～20px、CJK墨跡[6,2,863,199]；ESC與G沿原版149強調，一般68／陰影47。名稱使用既有殖民地顯示回呼，未知玩家名稱原樣保留，拒絕強調控制符。正式來源仍沒有此分支。

v120五側完整原版及四側14原版取樣、來源RAM與03／原版新增09存檔全等，教學及關閉畫面均與重播相同。14張GUI有一張harbor-after-voyage過渡圖未對齊，不能聲稱14GUI全等或完整原型通過；保持DRAFT。強推論根因是windowGame.Update在Draw前發布畫面標記，凍結取樣可能取得前一個已呈現畫面；須用獨立呈現同步／畫布指紋觀測核對，不靠更改容忍值或挑有利圖片。限制收據SHA-256 6446c4d5e6b78ff25b2195b735286ab246d8169dc5a25c55a54e440edbe7448a，重生入口目標181的v120/limit-check.py；原始圖片、輸入與差異都留workplace，未公開。


## 2026-10-03 CONFORMED：Caravel標題

v115私有原型與23個合成名稱、兩種士兵11／13圖的來源鍵／畫面／完整原版回歸通過後，按本日READY接入v118。正式完整Go與go vet、新正常v119共14GUI、v121限定檢查及21種破壞收據拒絕、原版缺失SKIP77已通過。兩欄30px，標題safe[77,76,265,88]、當次三列safe[81,90,218,126]；一般68／陰影47／強調149，左側船隻圖示與兩核准區外不變。原版cap8、清單pitch12、候選30～20px、基線與墨跡沿READY逐欄量測，不外推全域字級。

新輸入SHA-256 fe018f22d9599a3e3647c3a713017b9ba9123b30a38deeb0e2949410e1c63a51，終點133000000，RAM 484aec7405a62fa4e2ae8c5dd379aa4b638dbf4b3cc587a2d1dfbebe4ce01e45，凍結清冊55dd04e6ca91b737a7793cfe03b39caab2ca3cb1a0fb0afe133368d21049221e，正式二進位20bb53f0aa2e84c4fd655623a136da56e16888ca6b5ddf971d30a56ec82be95a。六側完整原版、五側14原版取樣、來源探針RAM及全部存檔全等；初始COLONY03不變，原版正常路徑新增COLONY09，SHA-256 a7d934a5f4c594b379830ad3c6119475905ad839b9cd32400c8dee06d2f75862。共用驗收只在此凍結案例使用精確03／09清冊，舊案例仍只接受03，新增未知存檔反例已拒絕。工具Go1.26.7、dosgolem b0bf259與原始檔案指紋／位址空間沿READY；來源查詢及正常印字完整定位在v121/source／observer。

v122全矩陣51PASS，零SKIP／FAIL／過期／原版指紋衝突；兩次普查與移除新列反向逐位元組相同。1935列中856已顯示／990待接／89不可達，只提升SHIPOPTIONS，COLONYUNIT既有來源只加當次Caravel收據。不表示完整六列或其他船隻局勢完成。TUTORIAL12原型仍DRAFT，13／14GUI對齊限制保留，未採用或提高完成數。檢查入口tools/check_goal181_ship.py，完整重生與證據沿目標181。


### 2026-10-03 DRAFT：真GUI抓圖的畫布指紋同步

程式觀測confirmed：windowGame.Update先發布status.frame，Draw後續才寫入texture並呈現；既有capture_frame只比較前後frame.step，不能證明PNG來自該發布畫布。v120海上過渡圖差異的實際來源仍標強推論。v123私有原型在Update附1280×800、row-major RGBA SHA-256；原版解碼與覆蓋畫布各像素Alpha為255。抓圖只接受指定自有colonization-window程序、PNG的RGBA指紋與尺寸及前後標記全等，缺指紋即拒絕。每次暫停均有恢復，最多32次；未對齊嘗試保留，不送遊戲輸入或修改原版。這是驗證同步原型，尚不授權正式教學，完整GUI／重播與原版狀態仍須獨立核對。


### 2026-10-03 READY：正常抵港教學TUTORIAL12

v123私有原型與v124正常14GUI經v125獨立中文／原文／缺圖集／v118基準及來源探針驗證通過，原型清冊SHA-256 9930833d349a92c16a4be9a40236e36ac86a581788069637a03dc7e95c800732。全部14張真GUI與中文重播逐像素相同，只有dock-arrival-tutorial的教學安全區相對v118改變，正常Enter關閉後無殘留。五側完整原版及四側14個索引／色盤／RAM取樣、來源探針RAM和初始03／原版新增09存檔一致。只授權此次Jamestown抵港教學，不外推其他教學或拖曳裝貨結果。

GAME.TXT完整SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a；header檔案偏移0x13E75，正文0x13E94、482bytes、SHA-256 11549559cc72e09c0afbf892cdfec59691727500c2051c82a3c0d109c9095559，既有譯稿text/help-bilingual.tsv。原版查詢0E2D:0832／F3 A6／CX1與GAME.TXT的512bytes讀取、各步號見v125/source/source-query.log.matches.json；正文入口0D21:00C6、dosgolem線性RAM175180。檔案偏移與CPU分段／線性位址基準分開記錄，均confirmed。工具Go1.26.7、Ebitengine2.9.9、dosgolem b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8。

typed輸入為該完整模板匹配出的%STRING0名稱，僅交既有colonyValue顯示回呼；已驗證的預設名顯示中文與原名，未知玩家名保留原字串，不經一般術語表。缺回呼或名稱含花括號時回原文並記錄，避免玩家名稱被解釋為強調碼。除此不改其他模板、資料格式、原版記憶體／輸入／規則／存檔。名稱只在獨立中文畫布處理。

原版11行、pitch10、各行cap8／9，safe[50,73,269,187]即876×456輸出像素。候選30～20px，實際30px五行、墨跡[6,2,863,199]；字首與CJK上緣沿原版墨跡，內距沿既有dialogMasks，ESC／G149強調、一般68／陰影47／木紋128。五個名稱的實際字模通過，最寬32個W的墨跡[4,4,871,239]；64個連續W、1000個W及缺字均整則回原文，不裁切或擴大安全區。合成名稱不算正常命中，量測清冊SHA-256 6ee995a286372093b7f6be54e1898c0d46cbe5c57d342a586d76ceaba4412bbc。

正式後須新正常GUI、中文／原文／缺圖集／v118基準與逐欄觀測、原版來源、完整存檔清冊、公開限定檢查與破壞收據及矩陣／反向普查通過才CONFORMED。原版圖片及存檔只留忽略的workplace。v120限制收據保留，不重寫歷史。


## 2026-10-03 CONFORMED：正常Jamestown抵港教學

v123～v125私有正常14GUI與完整原版審查後依READY接入v126，86個正式Go測試、go vet及實際字模／同步反例通過，無SKIP。新正常v127共14GUI的畫布指紋與中文重播逐像素全等；v128六側完整原版、五側14共同原版取樣、原版來源探針RAM及各側03／新增09存檔相同。相對v118只有抵港教學安全區改變，正常Enter關閉、後續船隻選單與Escape關閉沒有殘留。教學cap9、safe[50,73,269,187]、30px五行及玩家名／ESC／G的處理沿READY逐欄契約，不外推其他教學或裝貨結果。

正式輸入SHA-256 acc0b870bb5c3a4d57eb1757c7a33d6bdd9ff1a510ae1164a50ba9d52c68bf4d，終點134000000，RAM e72d072a604d1ec7dc1b44cf634bb934f4400ed7bcb91de51923d249f7ed7bf6，凍結清冊5c236781c08f1cbffcbe43dc0f58a6e12a2c59588b6a1b8f46ca1680e7904af4，正式二進位763989f737b674d6aff9742181a853a99bbaf89ae477de003c4421196feaca08。初始COLONY03不變；原版新增COLONY09的SHA-256 3f3fc49dd46f7f590db8f72902c528d2fbc398edbc45dd7d8f6cf1615476c2f5，只與本次等價輸入的原版來源比較，未沿用舊輸入的新增存檔預期。23種破壞收據拒絕及缺原版SKIP77通過。限定檢查tools/check_goal181_tutorial.py，同步反例tools/test_gui_capture.py，重生入口與完整指紋見目標181的v126～v129。

v129全矩陣52PASS，零SKIP／FAIL／過期／指紋衝突；兩次普查與移除新列反向逐位元組相同。1935列中857已顯示／989待接／89不可達，只提升GAME.TXT:@TUTORIAL12。字模、譯稿與原版素材／規則／資料格式不改；原版圖片及存檔仍只留workplace。v120舊GUI對齊限制保留為歷史證據，此次新正常收據獨立通過。


### 2026-10-03 DRAFT：貿易路線裝卸貨提示的城市名稱

目標181 v161原版0E2D:0832已正常查詢CARGOLOAD及CARGOUNLOAD，對應既有GAME.TXT語料0x862B／37bytes及0x866E／39bytes。檔案SHA-256及原始keys沿語料清冊，沒有新增來源文字。v156裝貨與卸貨提示都因城市Jamestown不是一般術語而回退；來源角色已由正常操作及原始查詢證實，不將玩家城市名視為單位名。

可丟棄候選只將兩個已綁定語料鍵的%STRING0交給既有colonyValue回呼；既有預設名用中文／原名，玩家自訂名保留原字，{}不可解析則回原文。其他模板及ABANDON沿原契約。原版兩行cap5、pitch6：首行裝貨墨跡[102,30,184,36]、卸貨[102,30,192,36]，城市行[102,36,142,42]；主色68、強調149、無陰影。候選22～15px與實際矩形／最長名字量測仍待原型重播，不能僅因詞典命中稱CONFORMED。

READY前須正常兩提示的原版查詢、覆蓋來源事件、兩色墨跡及安全區、超長／未知名回退、同名城市原字保留與完整原版不變性。九欄與海上目的地清單依規格038同輪審查，不改原版玩家流程或存檔。


### 2026-10-03 READY：第一路線的裝卸貨城市提示

v161正常查詢及v165兩提示來源／原版墨跡與實際字模通過，審查清冊b622bb2084e0e41d93ad55537acd71d1d0a17fdad1e037c6612377eba7032612；GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，已綁定CARGOLOAD 0x862B／37bytes、CARGOUNLOAD 0x866E／39bytes。查詢0E2D:0832與印字0D21:00C6、工具及位址基準沿DRAFT／規格038同輪READY。兩個已驗來源鍵的%STRING0為城市名稱，交既有colonyValue；已驗預設Jamestown顯示中文與原名，自訂城市名稱保留原字，不經單位詞典。缺回呼、花括號／缺字或超界整則回原文。城市角色反例Caravel／My Port由測試驗證；正常新命名反例本輪驗的是路線名稱，不能冒稱新同名城市GUI。原有正常Caravel城市及來源角色證據保留。

原版兩行cap5／pitch6、68一般／149強調、無陰影。safe[100,27,219,44]、候選22～15px、實際22px，中文上緣及內距沿dialogMasks，兩個正文實際墨跡／1000字超界回0由唯讀量測保存。僅此兩來源改城市回呼，ABANDON等其他模板不改，原版規則及RAM／存檔不修改。正式新正常兩提示與安全區／缺字模、原版及存檔全等、限定矩陣／普查前維持未CONFORMED。


### 2026-10-03 限定CONFORMED：第一路線裝卸城市提示

正式v175、v176正常海上GUI與v178六側完整原版／存檔、正文核准區、缺圖集回退通過；收據與限制沿[規格038](038-string-overlay-draft.md)同日第一路線附記。CARGOLOAD／CARGOUNLOAD原始模板各一行37／39bytes，原版按寬分成兩行，完整普查來源鍵GAME.TXT:@CARGOLOAD／@CARGOUNLOAD，語料candidate_id仍帶0x862B／0x866E定位。城市槽只交colonyValue，不用單位詞典。

原版cap5／pitch6、色68／149、無陰影；safe[100,27,219,44]，候選22～15px，選22px。實際中文墨跡相對安全區[6,3,449,54]，絕對畫布[406,111,849,162]。採dialogMasks的安全區上緣與內距，原版正文墨跡y120～168；此量測不宣稱中文逐字基線與原版相同。1000字超界回原文，未知城市保留原名，正常新同名城市GUI未驗。裝卸兩提示加入限定普查，不外推其他城市情境；未修改原版資料或存檔。


### 2026-10-03 DRAFT：歐洲碼頭六列選項

v192正常讀原版COLONY03後進歐洲，點碼頭工作者；v193來源及五側完整原版／16GUI／全部存檔通過，v194觀測另與原版及全部GUI像素相同。GAME.TXT SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a；查詢0E2D:0832、bytes F3 A6、CX1，EUROPEARM標記檔案位移38948、ARMOPTIONS標記39071。正文鍵GAME.TXT:@ARMOPTIONS:0x000098AC、362bytes、SHA-256 56d19f3e5b4344d1f6c5a4745ed009f6f0f251ed4e45032792da48ad66de45ed。檔案位移、執行期分段位址及RAM來源175430分開記錄，均confirmed。工具dosgolem b0bf259、Go1.26.7、驗證映像8aaaec77，重生入口見目標181的v192～v194。

只試來源12列中的第1／4／6／8／10／12列完整組合，沿既有譯稿與已確認術語槍／馬。原版六列左緣82、上緣73／85／97／109／121／133、cap8、pitch12、最右234；一般68、強調149、陰影47及底紋128。私有候選逐列對齊原版墨跡上緣，safe[81,72,236,144]，依cap8候選30～20px；最長價格與缺字／溢位整份回原文，實際候選字模尚待量測。只在完整六列、該字格與已觀測色層成立時採用，其他組合、價格或位置的正常原版證據未完成，不把12列全算完成。原版輸入、規則、RAM與存檔不修改，正式v187保持。


### 2026-10-03 DRAFT：六種已觀測碼頭清單

v196正常33GUI、v198三側完整原版／33取樣／所有存檔全等，11次0E2D:0832 ARMOPTIONS查詢證實原始GAME.TXT來源；輸入271085697965db3ffff3fb39336a9cce819ca2995919ac8150612495b50ede8c，終點259600000、RAM6821681eb1f3bbfd752c62e3757484e2a06f21d3dde79003e25fad06f10cec15。工具、原始檔案雜湊及位址空間沿v193／v198。原版源12列中，已觀測完整組合為第[1,4,6,8,10,12]／[2,4,6,8,10,12]／[1,5,8,12]／[2,5,8,12]／[2,7,12]／[2,4,9,12]列。實際碼頭狀態包含登船切換、配備／賣出槍與工具、配備馬；v196截圖檔名為探勘意圖，傳教士取消與賣出馬操作沒有因此獲得正常GUI信用。

各組原版左緣82、cap8、pitch12，六列上緣73起、四列85起、三列91起；一般68、強調149、陰影47與木紋128，各列墨跡和色號詳v198/source-summary.json。三列工具列的149像素93大於68像素89，通用lineRoles把68當minor而誤選為accent，故回line-colors。私有候選先完整核對六種來源模板、字格與色號集合，再為這些已證實組合固定正確色層；不修改其他清單的色彩推斷。各組安全區沿實際墨跡外擴左1／上1／右2／下2，候選30～20px，依原版墨跡上緣繪字。所有列全命中且排得下才覆蓋，缺字／超界／未知組合整份回原文。實際字模投影、六組邊界及同輸入差分仍待v200，不審READY，不把來源12列全部標完成。


### 2026-10-03 READY：歐洲碼頭六種清單與固定輕帆船港口標題

證據審查收據v200/ready-evidence.json，SHA-256 e4329183621f57dcd40d93a00e62ef706106855561040859e80d4b88dbf3b8cb。v200私有123Go／go vet／同步抓圖、v196正常33GUI與v192正常16GUI實際輸入、完整原版／所有存檔及限定像素／缺圖集全通過。原版來源、GAME／LABELS／NAMES清冊、dosgolem b0bf259、Go1.26.7與驗證映像8aaaec77沿本日DRAFT及v193／v197／v198。原始程式與資料全程唯讀，未改規則、玩家流程、輸入或存檔。只授權下列已觀測範圍；其他船型、Move to front、取消傳教士、其他價格／組合正常GUI與完整Issue #56未驗，合成容量與反例不計原版命中。正式後須新正常GUI、同輸入原版／存檔、字級／安全區／回退／關框、公開限定檢查與破壞收據、矩陣及重複／反向普查通過才CONFORMED。

規格035授權來源GAME.TXT:@ARMOPTIONS:0x000098AC，原始12列只加入DRAFT列出的六個完整已驗組合。完整來源雜湊／位移／長度核對後建立逐列模板，動態價格只解析原始%NUMBER槽；整份來源／字格／色號皆成立才採68一般／149強調／47陰影，128只作原版木紋。讀lineRoles之前的實測accentC，不改其他清單的推斷；任何未知／第三色／錯字格／部分列表／缺字／超界整份回原文。正常21筆覆蓋逐筆與v198原版印字start／RAM來源／全文／列值相同，不要求11次開框只有11次印字。

原版cap8／pitch12，左緣82；六列起73、四列85、三列91。候選30～20px，六組實際全30px。safe依組合分別[81,72,236,144]兩組、[81,84,236,132]兩組、[81,90,194,126]及[81,84,234,132]；最長正常含150$／200$／100$的原文與譯文、相對中文墨跡逐組見profiles-layout.json。CJK墨跡上緣對原版行上緣，左內距4輸出像素、陰影偏移4；各列保留原版pitch48輸出像素。原型價格十位數仍30px，1000位價格各組回0；六組缺圖集回原文，錯位置／色號／不完整與未驗Move to front拒絕。原型33圖僅相應清單safe改變，關框、角色結果、回世界及Save Game無新增差異。
### 2026-10-04 DRAFT：碼頭傳教士取消身分三列

v206正常由03進歐洲，選六列的Bless as Missionaries再重開碼頭清單；v207核對15張同步GUI、三側完整原版／全部存檔與兩次ARMOPTIONS原版查詢通過，completion_credit=0。已證實當次三列為Don't get on next ship.／Cancel Missionary Status.／No changes.，正文來源GAME.TXT:0x98AC，普查段落鍵GAME.TXT:@ARMOPTIONS；兩種鍵不混用。完整GAME.TXT與362bytes片段雜湊、工具及0E2D:0832查詢／0D21:00C6原版印字的位址空間沿前節READY證據。

原版x82、y91／103／115、cap8、行距12，矩形右界183／203／136、底界100／112／124，一般68／強調149／陰影47／木紋128。候選安全區[81,90,205,126]來自三列墨跡聯集外擴；中文字級待量測30～20px，逐列左緣與字頂對齊、長文／缺字模整份原文回退。譯文沿既有ARMOPTIONS第1／11／12列，不能為此改譯稿或字模綁定。尚未驗Board變體、正常取消身分、中文字墨跡及關框復原，不升READY或接production。[目標181](../goals/181-colony-remaining.md)保存v207來源與後續v208正常GUI入口。


### 2026-10-04 限定CONFORMED：歐洲碼頭六組與購船裝載標題

六種完整ARMOPTIONS組合依本節READY正式接入，實際30px；六／四／三列安全區與68一般／149強調／47陰影、行距12、原版cap8均由本次唯讀觀測重驗。三列工具清單維持149強調，不改其他對話框的通用色層推斷。只採已驗六組，Move to front及取消傳教士仍保持原文；顯示Sell Horses選項不等於已驗賣馬操作。

正式v201 SHA-256 5fb225cd4baae4dce17e7f37cdc3cbc42f379cd0e86537d059cce6984955bbd3；123Go／go vet／抓圖同步、穩定入口113Go通過。新正常v202購船16GUI與v203狀態29GUI皆由主選單載入原版03開始，正常操作後Save Game與關閉；各含真GUI共六側的完整CPU／RAM／原版索引與色盤／輸入／開檔全等，所有取樣與全部新舊存檔相同。正式／唯讀觀測與同步GUI逐像素相同，相對v187新增差異只在READY核准區，關框／返回世界／存檔畫面不留新增殘字。缺圖集回原文。清冊SHA-256 9a17519fd79e2df51263ea271c5276d229a49e74791ba4f37d1a4e22eae0a051；原始檔名與雜湊、工具／位址空間及字級與最長值／超界策略沿本節READY，不新增任意字級或來源。

限定獨立檢查器[tools/check_goal181_dock.py](../../tools/check_goal181_dock.py)兩側、31種收據破壞與錯版拒絕、缺原版SKIP77通過。v205矩陣60PASS，重複普查逐位元組相同，移除兩新列逐位元組還原1945項／881已顯示。採用1945項／882已顯示／974待驗／89不可達，段落單位的已顯示不表示ARMOPTIONS全部12列已驗。傳教士取消、移到碼頭最前面、其他船型與完整Issue #56仍未驗；原版、RAM、存檔、GUI只在忽略的workplace，沒有原版或遊戲規則修改。[目標181](../goals/181-colony-remaining.md)。


### 2026-10-04 READY：碼頭傳教士取消身分兩組

v208／v209正常19GUI、三側完整原版／所有取樣／全部存檔、四次ARMOPTIONS查詢確認Don't get on next ship.與Board next ship.各配Cancel Missionary Status.／No changes.，取消後恢復原六列。v210私有124Go／go vet與v211五側完整原版／存檔、19取樣及限定像素／缺圖集回退通過，來源／容量審查充分。清冊SHA-256 ac14cdde82055e44735cc3dfb296b73940219a50365c294a303f9644b32cfd16。

GAME.TXT完整SHA-25667a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，正文檔案位移0x98AC、362bytes片段SHA-25656d19f3e5b4344d1f6c5a4745ed009f6f0f251ed4e45032792da48ad66de45ed；原版@ARMOPTIONS查詢0E2D:0832／f3a6，marker位移39071，正文39084，普查段落鍵GAME.TXT:@ARMOPTIONS。0D21:00C6是執行期印字入口，175430是此次RAM來源，不當檔案位移。dosgolem b0bf259、Go1.26.7／verification8aaaec77，原版只讀。

只允許零起算[0,10,11]／[1,10,11]兩種完整來源模板，各三列x82、y91／103／115、cap8、行距12，取消列右界203／底界112，木紋128／一般68／強調149／陰影47。沿既有完整列表／來源／字格守門；缺列、錯序、錯起點／字高／色層及Move to front均不接受。safe[81,90,205,126]由墨跡聯集外擴，候選30～20px，兩組實際30px，最大墨跡[6,4,292,132]，Board組為[6,4,259,132]，每列左緣與墨跡頂對齊原版，基線與陰影沿原位。譯文沿既有corpus第1／11／12與第2／11／12列，缺字模／缺字／1000字超界整份原文回退，不改字模綁定、資料格式、原版或存檔。

原始資料→驗證362bytes來源→完整模板組合→既有色層及逐欄字模→正常GUI→Save Game皆已在私有候選核對。只在兩個清單安全區新增中文，取消後原六列／Escape／返回世界與保存畫面相對v201全等。正式實作後仍需新正常GUI、六側完整原版／存檔、來源與逐像素核對、獨立凍結檢查及破壞／缺原版、矩陣／普查才CONFORMED。未驗Move to front與其他船型；港口English Colonists／Missionaries標題仍原文，本READY不授權翻譯。原版／RAM／存檔／畫面均只留忽略的workplace，[目標181](../goals/181-colony-remaining.md)。


### 2026-10-04 限定CONFORMED：傳教士兩種三列清單與正常取消

依前節READY，正式v212只增加[0,10,11]／[1,10,11]兩種完整來源組合。v213由主選單正常讀03，進歐洲祝福、切登船、取消傳教士、重開原清單、關框與Save Game，共19張新GUI。v214含真GUI共六側完整CPU／RAM／原版索引及色盤／輸入／開檔全等，全部19取樣與新舊存檔一致；真GUI、中文重播與唯讀觀測畫面逐像素相同。相對v201只在兩個三列safe[81,90,205,126]新增中文，其餘17圖全等；正常取消後恢復六列，關框、世界及存檔無新增殘字。缺圖集兩組整份回原文，不啟用新來源。

原版來源與字級證據沿READY，並以本次新輸入重生四次0E2D:0832／f3a6查詢、0D21:00C6原版印字與逐列墨跡／色號。x82、y91／103／115、cap8、pitch12，68一般／149強調／47陰影；候選30～20px，實際30px、溢位0，兩組相對中文墨跡分別[6,4,292,132]與[6,4,259,132]。基線、逐列對齊與缺字／超長／錯序／錯字格的整份原文回退沿前節，未改原版資料、流程、RAM或存檔。

正式程式SHA-256 0a1bf028ea6ea0a57050cae438576565b94ec95fb4c88113457b5c771e112a5e，124Go／go vet／抓圖同步、穩定入口113Go通過；凍結清冊f78d6fd6c608e89aba8101a5f7cb17dd0eaddaca536956d668ca64d030efd4b3，新實際輸入fc12ab83597912fb59c9253ee7fa9b1f0efe2317af8f4fb79384396d60302bf8，終點161200000、完整RAM 1d3241d43717a10a60d3a3116614d7c41bfd7ea5773a315f4d49591ed5dd22ab。所有新舊存檔指紋見清冊，不能沿用v208的不同GUI時間所產生的新存檔預期。限定檢查[tools/check_goal181_dock.py](../../tools/check_goal181_dock.py)的missionary側、29項收據破壞／錯版拒絕與缺原版SKIP77通過。

v215完整矩陣61PASS，零SKIP／FAIL／過期／指紋衝突；兩次普查逐位元組相同，移除新列還原原普查。1945項／882已顯示／974待驗／89不可達不變，因GAME.TXT:@ARMOPTIONS段落已shown，本次不加完成信用。Move to front、港口單位標題與其他未驗局勢仍原文，Issue #56未完成；原版像素、RAM與存檔只留忽略的workplace。重生入口見[目標181](../goals/181-colony-remaining.md)的v206～v215。

### 2026-10-04 DRAFT：正常招募後的碼頭七列

v217／v218正常招募自由移民後開第二單位清單，15GUI、三側完整原版／取樣／存檔與一次ARMOPTIONS查詢通過。v219／v220正常選Move to front、重開兩單位清單與Save Game，19GUI、三側完整原版／存檔及三次查詢通過。已證實移到第一位後該單位清單變六列，原第一單位退到第二位後清單變七列；此為原版操作結果，不重寫規則。來源仍為已驗GAME.TXT:0x98AC／362bytes，完整與片段雜湊、工具及位址空間沿前節READY，原版唯讀。

新完整組合為零起算[0,2,3,5,7,9,11]。原版x82、y67起每列12，cap8、一般68／強調149／陰影47／木紋128；Move列墨跡[82,79,181,88]，最右234、最後列底148。候選safe[81,66,236,150]由實際聯集外擴，逐欄試30～20px，逐列對齊原墨跡上緣，不能直接將六列的30px當七列已驗。缺字、超長、部分／錯序／錯字格或未驗Board七列整份回原文。譯文沿既有ARMOPTIONS，不改語料、字模、原版資料或存檔；候選投影與同輸入差分尚待v221／v222，不升READY。新七列與港口單位標題目前仍原文。


### 2026-10-04 READY：碼頭七列與正常移到最前面

v218／v220已證實正常招募後七列與Move to front結果，三次原版查詢、19GUI及三側完整原版／存檔全等。v221私有125Go／go vet／抓圖同步、逐欄字級與缺字／超界／錯字格測試，v222五側原版／存檔、19取樣及核准區／缺圖集通過。審查清冊SHA-256 b1bf2671949b84470707c99e6db9e6725368baa8f31f3d145fc269f12c157960。

原始GAME.TXT完整SHA-25667a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，正文0x98AC／362bytes片段SHA-25656d19f3e5b4344d1f6c5a4745ed009f6f0f251ed4e45032792da48ad66de45ed；查詢0E2D:0832／f3a6、marker檔案位移39071，印字0D21:00C6、RAM175430均標執行期分段或線性RAM，不與檔案位移混用。工具dosgolem b0bf259、Go1.26.7、verification8aaaec77，字型Cubic11 SHA-2568de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c。

只增加已觀測完整[0,2,3,5,7,9,11]來源組合，沿既有12列來源綁定與完整模板／色層守門。七列x82、y67起每12、cap8、最大右界234、每列底界不超上緣9；68一般／149強調／47陰影／128木紋。safe[81,66,236,150]由墨跡外擴，候選30～20px，實際30px、中文相對墨跡[6,4,361,324]、溢位0；逐列墨跡頂對齊原版，左內距4輸出像素，陰影與基線沿既有lineLayerMasks。最長正常價150$／200$、1000字超界回0、缺字模與缺列／錯序／錯位置／字高／色號整份原文回退。未驗Board七列不接受。

原始資料→來源驗證→七列模板→既有色層／字模→正常招募及Move to front→兩清單與Save Game已核對。相對正式v212只改前後兩個七列安全區，其他17圖與所有存檔全等；移到第一位後的既有六列、Escape關框與保存畫面不變。只授權兩處最小顯示變更，譯稿、字模、適配器、原版資料／規則／流程／存檔不改。正式後仍須新正常GUI、六側原版／存檔／逐像素、獨立凍結檢查及破壞／缺原版、矩陣與普查才CONFORMED；港口單位標題仍未授權。原版像素／RAM／存檔只在workplace，重生入口見[目標181](../goals/181-colony-remaining.md)。


### 2026-10-04 限定CONFORMED：碼頭七列與正常移到最前面

正式v223依前節READY只增加完整[0,2,3,5,7,9,11]來源組合與七列y67起點。新正常v224由主選單讀03、招募、開第二單位清單、選Move to front、重開前後兩清單、Escape與Save Game，共19GUI。v225含真GUI共六側完整CPU／RAM／原版索引及色盤／輸入／開檔全等，所有19取樣與新舊存檔一致；GUI、正式中文及唯讀觀測全圖相同。相對v212只在前後兩個七列safe[81,66,236,150]新增中文，其他17圖相同；移到第一位後該單位變既有六列，關框與存檔無新增殘字，缺圖集七列整份回原文。

本次新輸入重生三次0E2D:0832／f3a6查詢及0D21:00C6原版印字，逐筆覆蓋與原版start／RAM來源／全文／列值相同。原版x82、y67起每12、cap8、68一般／149強調／47陰影；30～20px候選採30px、相對墨跡[6,4,361,324]、溢位0，逐列對齊與最長值／缺字／超界／未知整份回退沿前節READY。原始檔名與雜湊、工具、位址空間及字型指紋沿READY與凍結清冊，不新增任意字級或來源，不改原版資料、規則、流程或存檔。

正式程式SHA-256 e84d4c157a190ae04c5a1c3f291e105abaff8b336006f0de29423ed37e31558c；125Go／go vet／抓圖同步與穩定入口113Go通過，清冊4b65c62b9c8c1840d79ae197605590d13e485dcdba01270717e9aa2536e3b5df，新實際輸入c3b69af723dd708aff78d236f0a6d89f15775ad2156936725ac180bc33d2521b，終點160800000、完整RAM d524dd7ac626e5d3f37c10905ae0f21df8c0abbb0d8f1c9addd2ddfa9ff85515。存檔指紋見清冊；不同GUI時間的v219新存檔不拿來當本次預期。獨立檢查[tools/check_goal181_dock.py](../../tools/check_goal181_dock.py)的front側、29項收據破壞／錯版拒絕與缺原版SKIP77通過。

v226完整矩陣62PASS，零SKIP／FAIL／過期／指紋衝突；重複普查逐位元組相同，移除新列還原原普查。1945項／882已顯示／974待驗／89不可達不變，ARMOPTIONS段落已shown，本次完成信用0。Board七列、港口單位標題及其他未驗組合仍原文，Issue #56未完成；原版像素／RAM／存檔只留忽略的workplace。重生入口見[目標181](../goals/181-colony-remaining.md)的v216～v226。


### 2026-10-06 READY：碼頭Board七列

v227／v228已證實切換登船後重開見Board七列，v229四次原版查詢、21GUI及四側完整原版／存檔全等，正式無source事件。v230私有142Go／go vet／抓圖同步、逐欄字級與缺字／超界／錯字格測試，v231六側原版／存檔、21取樣及核准區／缺圖集通過。審查清冊SHA-256 96bc4e52575a3c495e3ea0b29062e0b0d46c8bea0cebdf851d1286785820c4e9。

原始GAME.TXT完整SHA-256 67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，正文0x98AC／362bytes片段SHA-256 56d19f3e5b4344d1f6c5a4745ed009f6f0f251ed4e45032792da48ad66de45ed；查詢0E2D:0832／f3a6、marker檔案位移39071，印字0D21:00C6均標執行期分段或線性RAM，不與檔案位移混用。工具dosgolem c5953b9、Go1.26.7、verification 20260930-r1，字型沿既有Cubic 11。

只增加已觀測完整[1,2,3,5,7,9,11]來源組合，沿既有12列來源綁定與完整模板／色層守門。七列x82、y67起每12、cap8、最大右界234、每列底界不超上緣9；68一般／149強調／47陰影／128木紋。safe[81,66,236,150]由墨跡外擴，候選30～20px，實際30px、溢位0；逐列墨跡頂對齊原版，左內距4輸出像素，陰影與基線沿既有lineLayerMasks。最長正常價150$／200$、1000字超界回0、缺字模與缺列／錯序／錯位置／字高／色號整份原文回退。其他未驗組合不接受。

原始資料→來源驗證→七列模板→既有色層／字模→正常切換登船及重開→清單與Save Game已核對。相對正式只改Board七列安全區，其他20圖與所有存檔全等；既有六列、Escape關框與保存畫面不變。只授權一處最小顯示變更，譯稿、字模、適配器、原版資料／規則／流程／存檔不改。正式後仍須新正常GUI、六側原版／存檔／逐像素、獨立凍結檢查及破壞／缺原版、矩陣與普查才CONFORMED；港口單位標題仍未授權。原版像素／RAM／存檔只在workplace，重生入口見[目標181](../goals/181-colony-remaining.md)。


### 2026-10-06 限定CONFORMED：碼頭Board七列

正式v232依前節READY只增加完整[1,2,3,5,7,9,11]來源組合。新正常v233由主選單讀03、招募、開第二單位七列、選第0列切換登船、重開Board七列、開第一單位六列及切換、Escape與Save Game，共21GUI。v234含真GUI共六側完整CPU／RAM／原版索引及色盤／輸入／開檔全等，所有21取樣與新舊存檔一致；GUI、正式中文及唯讀觀測全圖相同。相對v223只在登船切換後七列safe[81,66,236,150]新增中文，其他20圖相同；切換前Don't七列、六列、關框與存檔無新增殘字，缺圖集七列整份回原文。

本次新輸入重生四次0E2D:0832／f3a6查詢及0D21:00C6原版印字，逐筆覆蓋與原版start／RAM來源／全文／列值相同。原版x82、y67起每12、cap8、68一般／149強調／47陰影；30～20px候選採30px、溢位0，逐列對齊與最長值／缺字／超界／未知整份回退沿前節READY。原始檔名與雜湊、工具、位址空間及字型指紋沿READY與凍結清冊，不新增任意字級或來源，不改原版資料、規則、流程或存檔。

正式程式SHA-256 a10dbd94e357d56c8fbaec55ea189ebb6e2ad75cfd14ad58542cc3100aca4f6e；142Go／go vet與穩定入口138Go通過，清冊d0818ae05f94b94d64c9e96747efe3ef9c9f47b077c9ac439f71ded9b06cea8b，新實際輸入ff567645cdb576ca8797a4e2b7bbba92eea31bbdf0cfab16632a7cf403e852df，終點235000000、完整RAM c6177d0118016c914ff22518b1fd297c4c8610705d1b9affe5d62dba203e2d9e。存檔指紋見清冊。獨立檢查[tools/check_goal181_dock.py](../../tools/check_goal181_dock.py)的board側、29項收據破壞／錯版拒絕與缺原版SKIP77通過。

v235完整矩陣63PASS，零SKIP／FAIL／過期／指紋衝突；重複普查逐位元組相同，移除新列還原原普查。1945項／882已顯示／974待驗／89不可達不變，ARMOPTIONS段落已shown，本次完成信用0。港口單位標題及其他未驗組合仍原文，Issue #56未完成；原版像素／RAM／存檔只留忽略的workplace。重生入口見[目標181](../goals/181-colony-remaining.md)的v227～v235。

### 2026-10-09 DRAFT：G兩列目的地的名稱變數

正常讀取既有COLONY03後，從城市標題開改名欄，將Jamestown改為原版名稱清冊已有的Quebec，再從VIEW選單切回移動模式並按G。13張GUI、中文／原文／缺字模三側完整原版、WAV、存檔與回退一致；目的地兩列仍是英文。此路徑沒有建立第二城，不證明三列以上選單已驗。

來源版本為VICEROY.EXE `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`、GAME.TXT `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。工具沿固定hr-go-ebiten映像1430a2cf、Go1.26.7、隔離dosgolem82a14b2；地址為執行時線性記憶體或原版邏輯畫布座標，非EXE偏移。

| 欄位 | confirmed原版證據 | 候選處理 |
|---|---|---|
| 標題 | 0D21:00C6、RAM175112，完成155132956步；墨跡[67,83,174,92]、cap8，safe[66,82,176,94]、30px；局部指紋243bbad99dab8e3b061f63862dd8765c1b1b24a364c674fabf47b1aab849c2af | 保留既有來源鍵、2M步期限、phase及原版像素守門。 |
| 第一列 | RAM175470起、155265001步完成；London (England)，墨跡[77,97,155,106]、cap8，色68／47／128 | 由已驗四個母港及四個國名角色解析，不猜母港與國家的配對。 |
| 第二列 | 同段Quebec，墨跡[77,109,109,118]、cap9，色68／47／128；Q的墨跡高度與舊Jamestown的cap8不同 | 以已驗城市名稱回呼取雙語預設名，玩家自訂名稱保留；拒絕控制碼，保持兩列的位置與完整清單守門。 |

目前正式程式70462b91只接受London／Jamestown及固定cap8，故此段line-no-template。候選須先量測30～20px、墨跡頂端／基線、最長名稱及safe，再驗證容量、錯位／色號／標題像素／逾時／缺譯／缺字回退。候選未建立、未READY，不修改正式行為。單列母港與兩列既有正常驗收保留。

本機入口為目標185的`play_renamed_port_move_probe.py`、`check_renamed_port_gap.py`、`prepare_renamed_port_observer.py`與`renamed-port-observer/fields.jsonl`；輸入fee75757b770de38b68b1f584efca9f745f737170ec7b55ec33a56b9c369b83b、觀測293c01cbe94efc2bd07f33bd1222f042e739c687eaf446760f5fcfe6e3810045，終點173200000步、RAM190ee2baa3aeb012d62d5f3cb79d07b11a363501f73efef46630ae0585d6e3de。[目標185](../goals/185-player-experience.md)保存後續閘門。

#### 私用候選進度，仍DRAFT

`variable-two-port-candidate/`只新增兩列來源／角色／城市回呼候選，正式來源未改。候選09e8b2ba2d0b19e81ff38b6bf7df812a2deef051dfe3cccd615418bf9c999631，157Go與go vet通過，無skip。首場155PASS／2skip是未設定既有COLONIZATION_MUSIC_ROOT；補唯讀/game後在同映像乾淨重跑，不算產品失敗。

同13GUI實際輸入三側與基線完整原版／WAV／存檔相同，只在renamed-destinations的safe[76,96,157,120]新增中文，其他12圖不變；兩列實際採30px、墨跡頂端對齊，已目視完整畫面。候選摘要ee21d703251a8c04cfb534cd29605d9775189082f5ea3e12fa1883a1e39e7283。16個守門反例通過，玩家名稱保留與超長排版回退已驗。

172個唯一預設名均使用本次Quebec的同一墨跡矩形投影，166個可容納、6個回退：Corpus Christi、Fort Crevecoeur、Fort Francois Xavier、Fort Pontchartain、New Amsterdam、Rensselaerswyck。這不是各名稱的原版字寬或正常命中，不能由此判定六個名稱在實際原版欄位必定溢出。下一步先量測原版選單完整內框及長名稱，決定安全區內的排版，再審READY；三列以上未抽樣，維持DRAFT。

### 2026-10-09 DRAFT：VIEW選Move Pieces後殘字

相同正常輸入在154275001步，原文控制只剩世界底圖；中文GUI與中文重播卻仍畫VIEW十二項選單，木框已關閉。中文PNG 22ff1044e98b160a18669f1f5c476fc3a1b179fa594fa4cd19578602b1affe23、原文PNG c26c8b7b4dc2d725a7fb4b6227c854e36d82a2ad6095647900434e6e202903a1；完整原版與缺字回退仍一致。這是confirmed顯示缺口，不由目的地候選掩蓋。

MENU.TXT:0x00000240+list在145860001步因canvas-page-changed expired，146664144步從RAM175688重建source、safe[48,12,120,141]、21px，146850001步又active，155100001步才再次expired。根因仍是假說：原版清單重畫與關框期間，來源被重新活化；尚須追字元寫入、VGA及afterSafe的順序，不直接加計時特例或猜測隱藏條件。

同版本、工具、輸入指紋與位址基準沿前節。本機`check_view_move_residual.py`與`view-move-residual-review.json`保存失敗，下一個觀測切片限定145～148M步，不重跑城市改名或已完成#61。

#### confirmed收尾證據與候選守門

只讀`view-residual-observer/finish.jsonl`在146825614步記錄同178字元／12列、1092個原印字位置，僅5點lastText仍true。Move Pieces、View Pieces等八列存活0點，四列各1／1／1／2點；原版VGA已是世界底圖。五點現值都是68，位置為邏輯(114,89)、(111,105)、(114,113)、(117,127)、(115,128)，與新地圖森林同色。資料SHA-256 025f7669e4fc92f6268f6a81a9ceb4c437f4fb38c7e9c4f81fe2b684cfd73910；觀測側完整原版終點與13GUI輸入一致。

已證實的直接原因是finish只要求任一墨跡存活，隨後把已關框的畫布當成啟用快照，重畫整份中文。同色寫入在適配器前段被略過，是五點殘留標記的強推論；不需為修復而全域改動寫入監看。

DRAFT候選只對最終來源鍵為MENU.TXT的完整清單要求所有已觀測印字位置仍存活。任何位置被非游標寫入抹除，整份清單回原文；其他對話框的部分遮擋、既有前綴／槽位規則不變。不加時間或特定步數特例。須先有舊正式FAIL／候選PASS的局部回歸，再驗同13GUI、原文／缺字回退、安全區及既有選單開啟／懸停／Escape／點選關閉，才審READY。

#### 長名稱實際內框，仍DRAFT

新增正常改名New Amsterdam的13GUI及只讀觀測／原文控制。標題與第一列位置沿既有兩列；第二列[77,109,148,118]、cap8，仍短於London第一列[77,97,155,106]。既有合併safe[76,96,157,120]確實不能因名稱變長而自動提供更多空間。

既有scanDialogBox在原版像素取得left62／top77／right257，標題與清單相同；右框內仍有空白木紋，沿既有框內三邏輯像素內距可取right254。候選可依當次原版內框擴展文字安全區，不更動框或原圖，仍由30～20px量測、基線及最長譯文決定字級。先驗Quebec與New Amsterdam、172個唯一預設名容量、陰影／右框／其他欄位不變與缺字回退，再審READY。

若接可變列數，須讀當次完整列組的實際位置與12邏輯像素行距，綁定同一原版標題、局部像素、母港／國名角色與城市回呼，不推算或改動遊戲城市數。正常只驗單列與兩列；未抽樣行數不當成新GUI命中。超出原版內框或未知字格仍回原文。

長名稱輸入54609c3ca6f9b51d7cce70b4f3eeb0a3f80c58efdcffdd7460d560d5f40f1dd6，終點187200000／RAMd5f4f97a31b37a8dfbd07fcad3d4b169ca942209c81d1d24c908b81280c0d518；觀測fields.jsonl SHA-256 7eaff385ff221ebde7408029df494d53acb9c73daba058bcfa864cc1ae26c2e8。來源0D21:00C6、RAM175112／175470，169387762步標題完成、169455001步清單完成，版本與工具沿前節。

### 2026-10-09 READY：完整MENU抹除後禁止重活化

1092位置只剩5點仍會建立整份清單的原版觀測，舊正式的真實目錄回歸及可攜自製字串回歸皆FAIL；完整清單正例PASS。候選444c01b2a59422075c56cdf59bd8748ec875f84f1455a4fc5b79f4a24dc14360、157Go／go vet無skip，既有一般對話框部分遮擋測試仍PASS。

原13GUI實際輸入三側只改Move Pieces關閉後一區，逐像素等於原版世界，另外12圖不變；31百科與10個VIEW回歸不變，摘要c54237dc488c982fd599e73afafe575aa65198d4a81bd07423bc1b46d7bc063f。首場31圖比到已完成VIEW欄位的舊基線，差異只在右欄；改用目前正式70462b91同輸入基線乾淨重跑，沒有改產品或放寬比較。

另有17張新正常GUI，實際懸停Move Pieces／Center View、Escape、重開及點選關框均通過四側原版／WAV／存檔與回退。兩種關閉區等於原版；只在點選Move Pieces後清除殘字，其他16圖與舊正式相同。新輸入aa421dfc0f04ac0701a3b0c729b231f351bbf26f117c6ed848e8af262bb91aab，終點213400000／RAMc472104bc50de89146ea2d8dfbe3cfb0eab3ad48877b7938107e80eab547ac09。

據此授權正式finish在完成來源鍵以MENU.TXT開頭的清單中，要求firstOld的每個位置仍有lastText標記；任一被抹除即text-erased-before-finish。不修改寫入監看、原版輸入、資料、存檔、條件比較或其他對話框。原版VIEW墨跡cap5、既有21px、安全區[48,12,120,141]及字模保持；不加步數、特定選單或文字值特例。正式採用後仍須新17GUI及四側、正常懸停／關閉、回歸與已完成#57／#61接線審查，才CONFORMED。

### 2026-10-09限定CONFORMED：完整MENU存活守門

正式f8d65786000bbaecd037fbdf17050bb19ed7d1f9cd5e31d5f0e69450f87ff687，157Go／go vet無skip。新17GUI、中文／原文／缺字／舊正式四側的完整原版、每個取樣RAM／索引／色盤、WAV與存檔相同。實際懸停兩列、Escape、重開、點選Move Pieces與G取消均正常；只在點選Move Pieces後的MENU區清除殘字，另外16圖與舊正式一致，兩個VIEW關框區逐像素等於原版。

正式31百科及10VIEW回歸全部不變；當前正式來源PEDIA164／19、開局27、教學21／版畫17接線與公開#57／#61完成檢查仍PASS。來源與字級沿READY，沒有新的固定文字值、步數或寫入者特例。

正式輸入98294d85323cd4aac191121ac93d09f00de5fb5b675ba0c26a0ce6d3141668dd，終點194600000／RAM8578cf2d71e7def997019b5fbba8d7f980955f618ae67b86773e0b0fa82bab76。公開[MENU存活檢查器](../../tools/check_goal185_menu_survival.py)摘要cb4e981e5b5133b5463b6a55a43c58a5ae52b8d58d9d35b0d8ceaafb3d6a7bfb，第90列PASS。只重驗新增列與受影響#61列並作欄位增量普查，舊shown全保留、狀態變化0；1956／907／957／92，288可重驗、619歷史，不聲稱54列全部本次重跑。目的地名稱內框候選仍DRAFT，#55整體未完成。

### 2026-10-09 READY：目的地名稱按原版內框排版

候選1cead102289fa8b45b939d29e4aa7b34b457d0e361aa43bd0c89e7dd1016efa6、158Go／go vet無skip。Quebec與New Amsterdam的26個正常GUI輸入取樣、各三側、完整原版／WAV／存檔與回退PASS；只改兩張G清單安全區，其他24圖不變。原有單列9圖、可選兩列10圖、航程與灰色兩列14圖全部不變。摘要1bc5b7f83c09cd2543e5ac53952222080507769a1b288ebc111cc278c954f6d3。

依原版cap8／Quebec cap9、12邏輯像素行距、框62～257及右內距3，候選safe[76,96,254,120]採30px，墨跡頂端對齊原版、陰影沿已驗樣式；172個唯一預設名在此內框全部可容納。容量投影不當成172次正常命中，未抽樣行數也不當成新GUI證據。

授權在既有單列／兩列守門未處理時，使用當次完整列組及原版內框。綁定標題GAME.TXT:0x00001CBB、完整標題像素243bbad9…、30px、2M時效；各列x77、同一12像素行距、cap8或9、原色68或8與47／128陰影，必須在320×200內。第一列由已驗NAMES母港／國名角色解析，其餘由既有城市名稱回呼顯示；未知字格、來源、角色、控制碼、缺字或超界整段原文回退。15個錯誤守門案例PASS。

不改遊戲目的地、城市數、輸入或存檔。原有已驗路徑先處理，保留單列30px與舊兩列27px結果；新族群才使用原版空白內框。正式採用後仍須短名／長名新正常GUI、四側、懸停／取消／重開、33張既有目的地回歸與#57／#61接線回歸，才CONFORMED。

### 2026-10-09限定CONFORMED：目的地名稱內框族群

正式6ea4f982d2467421f42eeb00b2ea05060068bfe29d296e901187694fa7e0d394，157Go／go vet無skip。Quebec及New Amsterdam各17新GUI、共34張，四側完整原版、每個取樣索引／色盤、WAV及存檔一致；實際懸停母港／城市、取消、重開均正常。僅八張G清單安全區[76,96,254,120]改成中文，其他26圖不變。原單列9、可選兩列10及航程／灰色兩列14回歸全部不變。

原版字高、30px選擇、基線與陰影沿READY；172唯一名容量全部可容納，不當成172次正常命中。首次正式來源的PEDIA164／19、開局27、教學21／版畫17接線審查三項PASS，摘要仍與先前相同。短名輸入adc3167c26870fa0c1926eb5e5c7e0ee7edecd9a1d4f29b1a9ad6e811969f573、197600000／RAM4a8792ad4efa33916d8aec75e3da82a6636f387ae59f2bd55e4c806ec68715b3；長名edbf6f163aacba5b5646385d2d3142967ce245dd4da506093e1f765d45226d4d、219600000／RAMffbcbb726e5b0b7e693f4e8eb6c3ea7c2fa204e68ae6db1b2cc988a02bf5d10e。

公開[目的地族群檢查器](../../tools/check_goal185_port_family.py)摘要d0b44771a5bab81f0d9bdd9cbf2cb7a03a9d94afacb79b147a94637c5b124cbc。第91／92列PASS；普查只新增原版SAILPORT標題，不把玩家改名反推為COLONY原始行命中。92設定／56可重驗／36歷史，1956／908／956／92，290可重驗、618歷史；只重驗新增兩列與受影響#61列，不稱其餘重新執行。#55仍須處理End of Turn重印及完整來源審查，不以本族群代替整個Issue完成。
## 2026-10-10 READY：貿易目的地單列與刪除選項

原版正常22GUI與欄位觀測沿[規格038](038-string-overlay-draft.md)本日confirmed證據及READY審查，工具、版本、輸入檔雜湊與地址空間相同。原型入口與完整收據由[目標185](../goals/185-player-experience.md)索引。首版誤設框頂81，原版scanDialogBox實測為83；另一檢查器錯改非掃描列，已依實際最後列中點訂正。失敗收據保留，未因失敗放寬正式框線。

| 欄位 | confirmed來源與原版字級 | 安全區與中文量測 |
|---|---|---|
| 首／次目的地Jamestown | 0D21:00C6、RAM175374／175478；face[77,103,127,112]、cap8、68／47／128 | 原框左62、頂83、右257；safe[76,102,254,114]，30至20px候選，實際30px |
| 編輯器三列目的地 | 同入口／RAM175256／175360；起點(77,91)、(77,103)、(77,115)，各cap8、原色68／47／128 | 原框左62、頂71、右257；safe[76,90,254,126]，行距12，30至20px候選，實際30px |

單列只接受已驗Jamestown與其完整字格。當次TRADESTART標題ID為GAME.TXT:@TRADESTART:0x00008390、safe[65,86,254,100]、30px、active或waiting-screen，距完整標題小於2M步；此正文沒有逐列items，不虛構items身份。標題完整原版像素SHA-256必為第一目的地d92e03cf4309db02c1a6a5ed417be009b17af97534757f8b2206daaf316fcdb6或第二目的地f3903c8fd43c9bda810654eda5e24304db5ecf164850eb754b99cc24b2df7f16。按已驗原版內框擴大右側文字預算，字模墨跡上緣對齊原文；不沿Jamestown的原英文寬度截斷中文。

三列沿既有familyPortChoices的完整Select a port標題、角色、色層、原版快照及掃描框線。僅第三且最後一列的(Delete Destination)改查固定LABELS來源：檔案SHA-256 e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204、位移0xB57、20bytes、片段9c0e99371be9be6f0ed9261c72872d8d210b4585da90dd1e7079628531e16ae2，鍵LABELS.TXT:@ROUTE:0x00000B57，譯文「（刪除目的地）」。不把固定操作交給玩家城市名稱回呼。缺來源、重複刪除列、錯身份／字格／色層／時間／原版像素／框線、缺字或超界全部回原文。其他城市名維持原回呼，玩家資料不改。

170項Go、go vet、候選22圖及九圖限定差異通過，其他13圖不變；來源、字模與原版資料均未新增。候選審查摘要沿規格038本日READY。正式新GUI須涵蓋選取、懸停、取消、刪除第四列、重加目的地及正常存檔；中文、原文、缺字模與舊正式四側的完整原版與存檔必須相同，正常關框不能殘留中文。未完成正式收據前不稱CONFORMED。

## 2026-10-10限定CONFORMED：貿易路線2與第三、第四目的地

本節依本日READY正式實作，不擴張未觀測編號或母港。正式二進位SHA-256 0484e99b5a03456b9910eca55fb27c384857b162c25b9ba364d68d3f63c93a27；169項Go與go vet通過，無skip。固定Go1.26.7、Ebitengine2.9.9、隔離dosgolem82a14b2，原版輸入與地址空間沿READY。

34張新正常GUI從主選單讀檔，建立兩路線、加入第三London與第四Jamestown，實際懸停、取消／重開、刪除第四列、重新加入及GAME手動存檔後正常關窗。中文GUI逐像素等於中文重播；中文／原文／缺字模／舊正式四側完整CPU、RAM、每點RAM／VGA索引／色盤、WAV與存檔相同。只在READY安全區改變16圖，另外18圖不變；標題與表格22px，目的地選單30px，基線及最長名稱量測沿READY。

輸入SHA-256 427ff3182a6a73342eb6c5405be97e10c8dba6463c6742019a36618a87e6b333；終點352400000步，RAM 4e94481caf722e06d823898f514136329af0c18dce66a9b4003bf8dc3d3afd8e。原版正常新存檔COLONY01.SAV為77ea2c698f9bda7dfdbc43df7c561a9d8f901bdee7854a71966de38bb66f6ad7，只留本機。公開[貿易欄位檢查器](../../tools/check_goal185_trade_fields.py)摘要535ee7112cf5198632688e3f3b91df959a15258dbb9eac2d902b2184f5d81960，完整入口見[目標185](../goals/185-player-experience.md)。

教學13／建造31／精簡選單15圖回歸與已驗來源全等，百科與開局接線摘要保持。錯版、錯程式、不同原版狀態、未核准字級與安全區外差異均拒絕，缺原版SKIP77。346組名稱只驗容量；完整#55／56、其他路線編號／母港／第五列／自動跑商與真正超出視窗建造捲動仍未驗，不由本節宣稱完成。

## 2026-10-10 READY：四則條件訊息的城市名稱資料契約

本節只授權變數資料接線。四則訊息尚未各自取得正常GUI，不宣稱其畫面CONFORMED，也不增加普查shown。原版VICEROY.EXE SHA-256為a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3，GAME.TXT、NAMES.TXT雜湊沿前節。IDA Pro 9.4在唯讀正式資料庫的一次性副本匯出原始位元組；重生入口由[目標185](../goals/185-player-experience.md)的ida_issue56_code.py索引，檔案位移與新增的16位元IDA分析區段分列，不當作執行期CS:IP。

| 來源鍵 | 角色與證據 |
|---|---|
| GAME.TXT:@ABANDON2:0x00001A5B | %STRING0為城市名。confirmed檔位移0x288C8取ds:8542h的城市指標、加2，複製至9CD2h；0x288DB建立ABANDON，0x28902的分支加後綴2。兩種正文共用同一城市字串。 |
| GAME.TXT:@ALREADYHAVE:0x0000AD9D | %STRING0為城市名，%STRING1仍為建築術語。confirmed檔位移0x2E5A5設定槽位1，0x2E5C5以標記DS偏移0xE95呼叫0x2EF5F。 |
| GAME.TXT:@NOMOREWAREHOUSE:0x0001527E | %STRING0為城市名。confirmed檔位移0x2D145以標記DS偏移0xD52呼叫0x2EF5F。 |
| GAME.TXT:@NOMOREWAGONS:0x00015315 | %STRING0為城市名。confirmed檔位移0x2D1F2以標記DS偏移0xD62呼叫0x2EF5F。 |

後三則沿同一城市通知端：0x2EF5F為EA DC09 1F19遠跳板，原始191F:09DC定位的檔位移0x1BFCC指向overlay 3／entry 0。檔位移0x2CFD0的通知入口於0x2D01D取ds:8542h、加2，於0x2D026設定字串槽位0。原始取值與寫入位元組已證實；overlay入口關聯為強推論，沒有直接xref或這三則獨立執行期收據，不升格為完整動態資料流已證實。另有實際來源模板中的城市／建築上下文，支持上述欄位角色，不把其他STRING0外推為城市名。

審查結論：四個精確鍵的%STRING0可沿既有colonyValue回呼。玩家自訂名保留原字，預設名沿既有已核對名稱表；不得轉入一般術語表，不改原版資料。回呼缺失或名稱含強調控制碼時，整則保留原文並記錄原因。其他槽位與來源維持原路徑。

字級、基線、安全區與換行仍由當次原版印字量測及既有正文排版契約決定，本節不指定新固定字級。沒有完整原版欄位量測、缺字或最長譯文放不下時維持既有回退。驗收須包含四則真實原始模板、定稿術語與名稱衝突、自訂名、缺回呼及控制碼負例，以及既有正常GUI的原版狀態與畫面回歸。資料契約PASS只證明接線，不能代替這四則各自的正常畫面收據。

## 2026-10-10當前來源延續驗證

正式程式73d863baa358dce354bf2d13b232735c2e9109a48d1b1c15a61d88df031e4ee2，Go1.26.7以`go build -trimpath`重建，180Go與go vet通過。新34正常貿易GUI四側的原版狀態、每點RAM／VGA索引／色盤、WAV及存檔一致；中文畫面與0484e99b…版全等，未改前節字級、基線或安全區。教學13／建造31／精簡選單15／貿易34共93圖與前一驗收版全等，既有10列殖民地／港口／報表抽驗保留。入口為[完成檢查器](../../tools/check_goal185_colony_completion.py)，摘要bd42464d1208d4144dc5efd4c6daf5e795a392efd1d751d3bda01b03c6b9e3cc。

本批只新增四則精確城市槽位的READY資料契約，其正常情境尚未逐一取得GUI；不能由既有欄位的限定CONFORMED升格這四則。建造換頁及其他貿易局勢維持未抽樣，來源接線完成不增加shown。當前#56依既有代表性抽樣決定完成，較早「本節不代表#56完成」保留為當時驗收範圍。
