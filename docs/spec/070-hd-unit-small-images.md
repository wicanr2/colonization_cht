# 單位小圖像的來源與HD覆蓋

狀態：五艘船、三種車輛／火炮及22幀殖民者的正常百科顯示限定CONFORMED，2026-10-17；其他新來源維持DRAFT。正式HD為103張生成原PNG，完整玩家可見分母仍未知。

## 範圍與來源

涵蓋尚未接線的船隻、人物、火炮及其他單位小圖像。既有31來源的正式契約維持[規格065](065-hd-small-images.md)；完整範圍與完成條件維持[目標186](../goals/186-display-settings-and-gameplay-video.md#全量覆蓋與完成判準)。

| 輸入或工具 | 固定版本或SHA-256 |
|---|---|
| ICONS.SS | a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716 |
| VICEROY.EXE | a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3 |
| 原版SS／PIK解碼收據 | e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d |
| 唯讀基底探針 | tools/probe_hd_building_batch.go，5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6 |
| dosgolem隔離副本 | 82a14b266e1b5bc904e2d0fe507daf6bea41a013 |
| 編譯與檢查 | Go1.26.7、Python3.11.2、Pillow9.4.0 |

逐幀原始序號、尺寸、完整編碼、索引指紋與區段位移沿[來源索引](../hd-source-catalog.json)。位址採dosgolem實模式CS:IP與20bit線性RAM，不能當作IDA位址。

## 唯讀研究契約

- [組裝器](../../tools/build_hd_unit_lifecycle_probe.py)載入全部131個ICONS候選及完整SS清冊的編碼別名。原始序號與AX低15bit、尺寸及完整編碼須同時相符。全清冊有多個候選時記錄集合，不授予來源身分。
- 從冷啟動第0步觀測0D46:000A，核對原碼c828000052535057568b4702、堆疊與描述子。返回須符合原CS:IP、SP增加10及100000步上限。
- 主畫布0x2CAE0及暫存畫布0x3C500分別觀測。來源寫入、透明底圖、周圍底圖、實際指令碼、返回邊界及來源撤銷均保存；未知寫入包含同值寫入。
- 高位、裁切、其他描述子及編碼別名保持未驗，不因一張圖看起來相同就套用。未命中幀與空幀不排除全量範圍。
- GUI以既有合法存檔、正常載入與選單操作取得。所有截點由畫面外設定暫停，保留完整CPU、RAM、可見索引、DAC與實際輸入；X11遊戲區須與標準診斷PNG相同。
- 逐寫觀測、無觀測控制及GUI收據須在相同步數與輸入數相符。來源、索引像素、RAM與存檔不寫入原版。
- 逐寫事件以串流JSON保存，上限800萬筆；呼叫與每次繪製也有原有界限。研究工具不被正式組裝器引用。

組裝時指定--catalog為R49本機decoded-public-r3/catalog.json，--gui-capture為正常GUI的capture.json，--inputs為其gui.inputs.json，--reference為R49 small-public-r1模組，--output為新的/out子目錄。輸出包含small-probe、points.json及build.json。探針以--root、--seed、--inputs、--sources、--lifecycle-points及--out執行；另加--control產生無觀測對照。所有命令只在有界Docker內執行，/game與dosgolem唯讀掛載，原版像素與完整收據留在workplace。

[獨立檢查器](../../tools/check_hd_unit_lifecycle.py)以--observed、--control、--build、--sources、--entry-report、--points及--output核對。--entry-report在本切片指定GUI的capture.json。它從原始事件重建每筆寫入、來源建立、未知後畫撤銷與每個截點的來源圖，不以探針輸出的來源圖自行證明相同；未驗暫存轉送或別名命中會拒絕。

## 目前證據與待決格式

歐洲港口的招募、購買與訓練選單已完成正常GUI研究。131候選中只命中既有31種，沒有新增來源完成數。15個原版截點、41筆輸入、324次完整繪製與122252個事件已由獨立模型核對；至124400000步的完整原版狀態與初始存檔相同。檢查收據為本機hd-sprite-batch-r71/icons-europe-check-r1.json，SHA-256為f82a9853d92cdfd01419ecd996120b95a7a1b5209e7fbac9bb2e5905bbd2668e。

百科返回清單會重設選取列。首個探索腳本後續重複開啟火炮，不能算24種單位驗證。修正後以實際方向鍵重新選取各列，確認23個不同條目；第24次選取循環回首列。

R71正常百科研究已confirmed：80種來源、196次完整繪製、5048144個逐寫／撤銷事件、35個GUI截點與353筆實際輸入。獨立模型重建全部來源，239次同值後畫也撤銷來源；暫存轉送為0，沒有增加這條路徑的信用。80種中包含既有31種，另49種尚未正式接線。至601800000步的CPU、完整RAM、可見索引、DAC及初始COLONY09.SAV與無觀測控制相同，六個真實收據反例均拒絕。

本機根為workplace/reports/goal186-display-hd/hd-sprite-batch-r71。正式工具產生的icons-public-probe-r2/build.json為f1146a68f288fece3a1d8d187de6b82429133069d7c6e181c67483bcb0f42c48；獨立檢查icons-pedia-check-r3.json為f47871e4eb52f5ddd74ff2fc977a53f86d8b5df164b3c9e22e7db84b9aba8eaf。六反例收據unit-model-negatives-r1.json為6f8aa5a7195a4629ce24d417190d1ae30eebfdb74a63165afdbb7ce899320404。

船隻用途由百科標題、正常選取及當次完整來源確認：

| ICONS原始序號 | 正常百科條目 | 原版尺寸 |
|---|---|---|
| 006 | Merchantman | 13×16 |
| 007 | Galleon | 14×16 |
| 014 | Privateer | 13×16 |
| 015 | Frigate | 13×16 |
| 127 | Man-o-War | 14×16 |

[來源索引組裝器](../../tools/build_hd_source_index.py)新增--unit-report與--unit-build，分別指定上述檢查及綁定收據。1552筆既有資料、73張正式素材連結與所有舊證據逐欄保持，只附加80種正常百科來源的數值與雜湊；沒有公開像素。原版音訊與動畫在本切片未驗，不授予信用。

五艘船的圖集及取樣比較保存在本機，圖集格式提案仍待使用者回覆。R72先沿用既有已核准的單幀PNG清冊，完成五張新原稿；原PNG與alpha原樣保存。生成原稿數、來源幀數與正式覆蓋數分別記錄。

## R72五艘船的READY契約

本節只授權第006、007、014、015及127幀接入既有小圖像來源群組。來源檔、完整編碼、逐寫指紋、幾何與三個writer沿前述confirmed證據；五幀尺寸均不超過既有256格上限。保留既有31幀的槽位順序，在尾端加入五幀，不增加第二個觀測器。

109筆正常X11輸入取得24個截點，重播至227400000步。五次完整船隻繪製與65983個事件已由獨立模型重建，CPU、完整RAM、索引、DAC及初始存檔與無觀測控制相同。五艘船在移開、懸停、返回的15個截點皆保持相同主畫布來源身分，合計679格；另外三個原版不透明格被後畫旗標覆蓋，保持撤銷。

百科的游標疊在輸出畫面，這段路徑沒有船隻主畫布的RAM保存、還原或游標反向配對事件，三者均為0。沿[規格066](066-hd-standard-cursor.md)的256bytes來源、兩個游標緩衝區與實際位置，核對整幅可見索引等於主畫布加原版游標。五艘船各有46、48、43、42、48格被不透明游標遮擋，共227格；移開後均恢復相同來源身分。

[游標表面檢查器](../../tools/check_hd_ship_cursor_surfaces.py)以--root指定本機hd-sprite-batch-r71，--output指定新收據。它核對24個原版截點，其中22個通過完整游標表面契約。load-menu與load-slot有游標外差異且沒有本批來源，沿既有守門回退，不計HD覆蓋；本批15個船隻截點必須全部通過。六個反例分別破壞游標來源、RAM來源、背景緩衝、合成緩衝、位置及游標外索引，均拒絕後再重驗正向資料。

五張原稿沿已定稿精細像素風與既有icons-005原稿生成。下表尺寸為原PNG，取樣框以alpha至少128量幾何；實際取樣保留原RGBA，不套alpha門檻。

| 原始序號 | 原PNG尺寸 | 取樣框 | 原PNG SHA-256 |
|---|---|---|---|
| 006 | 1122×1402 | [198,144,947,1191] | c862cdfa55ab3de416018c3450dc90c392ed7fd54c7fb5f2a9c31538f23442bb |
| 007 | 1121×1403 | [167,176,980,1226] | 191f23d8ec4b49fbeff41864c0fd812f08b88fd0abbb83255955e3625da647a8 |
| 014 | 1120×1404 | [205,171,953,1261] | 22e18c47baaf6f5188d9dcfadd4e69ab41812acaf39274b3f377ae7bba059c39 |
| 015 | 1122×1402 | [204,275,940,1116] | 4b938de1299c6c0f5895993715325ad66b8328b9616f5c98fc0f2bce8f09c3a9 |
| 127 | 1122×1402 | [114,183,1039,1256] | c18b01f9ab0af49f84184c9fb11bcd582af71b5b8bccd7f3e07b01b2d7e5b235 |

依既有像素中心最近鄰算法，將取樣框對應到原版完整13×16或14×16內容矩形，輸出52×64或56×64。只繪當前已驗來源格，透明RGBA保留底圖，文字及已驗游標依既有順序最後處理。第007、015、127幀各有3、6、17個原版來源格的取樣alpha全為0，明確保留原版，不計實際HD繪製格。其他兩幀沒有整格透明缺口。本批原始682格在旗標後剩679格有效，依原alpha實際可繪653格；不得宣稱682格全像素重繪。

入口、來源、writer、完整逐寫、返回或當前原版色號不符時不取得來源；未知後畫含同值撤銷。缺件、錯指紋、錯尺寸與連結沿既有載入拒絕及HD不可用契約。原版模式、輸入、存檔、色盤、遊戲規則及原PNG皆保持。

正式驗收須在新程式重跑五幀來源及反例、既有31幀回歸、正常五語切換與懸停、獨立RGBA、原版狀態／音訊／存檔、缺件恢復及封裝白名單。百科驗證只授予這條正常顯示路徑，世界單位、移動、戰鬥與動畫另驗。圖集提案與其色彩延伸取樣原型仍為DRAFT，本節沿用單幀PNG與既有RGBA取樣算法。

實作在[共用小圖像層](../../tools/hd_small_image_runtime.go)，[原版路徑測試](../../tools/hd_small_image_runtime_test.go)另驗五船24點／109輸入與每幀20個真實來源反例，既有31幀仍走其49點原版模型。[獨立RGBA檢查器](../../tools/check_hd_ship_pixels.py)以--root指定本機R71根、--assets指定graphics、--runtime-output指定該Go測試輸出，--output寫入新收據；從原PNG、原版索引／色盤與獨立來源模型重算15個畫面全部RGBA，包含原alpha、旗標保留與最後還原的原版游標。

## R72正式驗收與限定CONFORMED

規格070 R72五艘船限定CONFORMED，正常百科的商船、帆船、私掠船、快速艦與戰船已接線。合計78張生成原PNG／清冊79檔，59Go／42綁定。4個頂層／248個含子案例測試零skip及go vet通過；五船24點／109輸入與100個來源反例、既有31來源49點回歸通過。15個畫面共15360000個RGBA全等；正式109項GUI中100項五船畫面驗343040個來源RGBA、84960個游標RGBA與101710048個區外保留RGBA。264筆實際輸入四側至335800000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。6種啟動回退／恢復、79檔封裝與238項拒絕通過；73張繼承原PNG保持。679格有效來源中653格實際HD繪製，26格沿原alpha透明保留。世界單位、移動、戰鬥與動畫未由百科驗證外推，全量HD未完成，沒有新發行。

正式船隻資料追加於共用來源表尾端，既有31幀槽位與取樣／來源演算法保持。第100幀仍由既有人物層繪製，共用小圖像層現為36來源與35張美術。來源守門及未知同值撤銷保持。

正式GUI以play=true啟動。109項包含8項載入／導航、100項五船顯示及關閉；100項為每船五語各自原版／HD、懸停與返回。實際X11遊戲區全部等於診斷PNG，設定交易期間原版步數、CPU、完整RAM、索引、DAC及輸入凍結。商船來源原點為[11,33]，其餘四艘為[10,33]；檢查器由獨立來源的local與位置推得，不套統一原點。色盤120至127的循環未用於當前畫面，逐樣本仍使用實際DAC。

[RGBA檢查器](../../tools/check_hd_ship_pixels.py)另加--gui，以本機R71根的standalone-ships-gui-r1核對100項。它從原PNG、獨立來源圖與當次原版索引／DAC重算船隻、旗標與原alpha，再還原實際原版游標並覆蓋已驗HD游標。來源區及兩次實際游標矩形外逐RGBA保持。原版模式25項與HD75項分別記錄，不能把船隻透明處算成HD像素。

本機證據根仍為workplace/reports/goal186-display-hd/hd-sprite-batch-r71。以下為R72收據：

| 收據 | SHA-256 |
|---|---|
| standalone-ships-ready-review-r1.json | 5815102fd348b0f8507ed594b9396e3fd49336230f77c6ab86b4ee5e97446f6d |
| standalone-ships-conformance-r1.json | fb5400b2190c423b5875e64eec63fcf3b9b4544baceb87b7e80e3dc91117b978 |
| standalone-ships-build-r2.json | c0cad36a22af78f6ba2022fa204260d33e4e237cdd826efe27bbe6e21f5bed3a |
| standalone-ships-gui-pixels-public-r1.json | eb269e11f3dd5ce99ca663589471ca61e37246bc211dabdc58104704bba869f8 |
| standalone-ships-replay-r1-check.json | 248a36f3a52af8d845157f15a655cf94dd916b15d8f392e051fdf6cbee025bf7 |
| source-index-ships-r1.json | d01874681e0e8d8ea8884a895c4ddfe2bc4a64b74da715a22946e4364fef9410 |

正式二進位為52fd12fb78b298c5827ccff226c2a3f21c32517e77a1a4641d47521ae5bd07e4，素材清冊為0c78251ffc365a49e229ede4e88715b095359ff85bd16c0508a5a738b2eee33c。
來源索引組裝器新增--ship-ready-report與--ship-conformed-report，核對本批及R70的73張繼承原稿後附加五船CONFORMED。R71的80種研究證據及1552筆原始欄位保持，原49種未接線來源現剩44種。原版像素、參考、遮罩、完整RAM、錄音及未選圖集繼續只留本機。

## R73貨車、砲台與寶藏：READY契約及限定CONFORMED

第008、009及016幀沿R71已確認來源、R73正常原版觀測及現行單幀PNG格式完成正式接線，2026-10-17限定CONFORMED。下列READY契約保留實作前的證據與界限。百科名稱沿既有譯稿為貨車、砲台與寶藏；原稿描述為篷車、火炮與寶藏車。
第008幀為貨車，第009幀為砲台，第016幀為寶藏；用途須沿各次正常百科條目與來源確認，不由外觀授予規則語意。

| 原始序號 | 原PNG尺寸 | 原版不透明內容框 | 原PNG SHA-256 |
|---|---|---|---|
| 008 | 1254×1254 | [0,4,14,16] | 19045ad0de2cd24bf172f0dcbb5466ee677e1d3270b741dee66df81e7b2b5203 |
| 009 | 1254×1254 | [0,9,14,16] | 9ae2a857a9f143a9747753d36e5d16dd506b0d2984fac310b20056c926d47ec2 |
| 016 | 1254×1254 | [0,7,14,16] | edfb3e4e2eed371c6d8fe5fb9c905af05dd62b515fd4b81455e0f50d037e8889 |


原稿與alpha原樣保存在本機R71根的candidates/icons-008-v1.png、icons-009-v1.png及icons-016-v1.png。
內建imagegen完整提示、參考指紋及框位見r73-three-unit-generation-r1.json，SHA-256為30ea5503d6b5eb0b689dcb7c0c8d33d00a14a03728eed295c9fbd1f7563d4e81。
參考由原始索引及當次正常畫面的DAC產生，原版參考不入Git。篷車、火炮與寶藏車的上方原版空白高度不同，後續取樣須依各幀內容框；不能照搬五艘船的完整16格高度。

本節授權三幀在既有36來源表尾端追加，共39來源、38張小圖像美術，第100幀仍沿人物層。來源檔、原碼、完整編碼、AX、描述子、三個writer、逐寫指紋、未知同值撤銷、返回及原版索引守門沿規格065，來源表與既有演算法不變。三幀皆14×16，正常矩形[10,33,24,49]；008／009 writer位元為7，016為5。

86筆正常X11輸入取得18個原版截點，至175200000步；三個唯讀／無觀測執行器的CPU、完整RAM、索引、DAC及輸入逐點等於實際GUI。3次完整來源繪製與52959事件經獨立模型重建，三幀原始290格不透明像素在篷車後畫字形後剩287格有效來源。16個截點完整符合規格066的主畫布加原版游標表面，load-menu與load-slot兩點沒有本批來源且沿既有守門回退。9個本批截點的來源在移開／懸停／返回均相同，原版不透明游標分別遮擋41、30、43格，共114格。主畫布保存、RAM還原與游標反向配對均0，不新增還原信用。六個真實表面反例全部拒絕，逐次重驗正向資料。

取樣只在各幀內容框內，框外透明。以像素中心最近鄰取原RGBA，alpha至少128只量原稿框位，不改alpha。原始290格皆有至少一個非零alpha輸出點，後畫字形撤銷3格，實際可繪287格；這是原稿取樣量測，正式逐寫與旗標仍按當前來源決定。透明處保留原畫面，已驗文字及游標最後處理。原PNG與alpha皆保持，來源、writer、返回、後畫或原版色號不符即不覆蓋；缺件、錯件及連結沿既有HD不可用契約。

READY來源修訂r73-vehicles-ready-review-r2.json為1f01163ee78a7c042f696f9fa8a55a63b382f80dc1f76fea428204658623ebec，獨立原版模型vehicles-ram-r1/model-r1/check.json為1c8c59a9a36b36f5feb1cec12d925111b96619098213bc5a4e171bccb2e5d057，游標表面r73-vehicle-cursor-surfaces-r1.json為48e565bfd93424a81275cea7a8235b9c5b2599a646e5d11fadd551072b6b22de。
實際輸入baseline-vehicles-r1/gui.inputs.json為26f0bcb8bab7fce4fe0ea47c712fd9a236911a7b9cb00f361b4a65c177c934a7。

清冊容量READY補訂：81張原稿含完整提示的現行清冊為268375bytes，原256KiB限制不足。執行期與封裝同步限定512KiB，仍須逐byte符合固定清冊指紋；PNG各自維持8MiB限制。新增大於512KiB清冊的明確拒絕反例。這只放寬有界檔案容量，不改JSON格式、原稿、取樣、來源或遊戲行為。第一版正式測試／GUI／封裝因容量拒絕，不授予通過信用，修正後用新輸出乾淨重跑。

R73原始來源數勘誤：第一版驗收預期將篷車141格原始不透明像素當成有效來源，正式GUI正確拒絕此預期。獨立模型從始至終只保留138格，另外3格由原版字形寫入撤銷。三格為[16,37]、[17,37]、[18,37]，由dosgolem實模式0D21:012C字形寫入，原碼26882547feca740afecd75dfacb504eb；旗標語意只作畫面導覽，不取代逐寫證據。修正檢查器預期至138，另兩幀保持67與82；正式來源撤銷、取樣、PNG及旗標保護均未改。原READY收據保留，修訂收據記錄來源及差異。

正式驗收須重跑三幀18點與真實來源反例、既有31幀49點及五船24點，另驗五語原版／HD、懸停與返回、獨立RGBA、實際GUI狀態／音訊／存檔及四側play=true、缺件恢復與全量封裝白名單。百科用途不外推世界移動、戰鬥或動畫。正式素材數以通過CONFORMED為準，本節READY時仍78張。

## R73正式驗收收據

規格070 R73三幀限定CONFORMED，貨車008、砲台009及寶藏016正式接線，合計81張生成原PNG／清冊82檔、59Go／42綁定。5個頂層／259個含子案例分批完成，所有計入案例零skip及go vet通過。新三幀18點／86輸入與60個來源反例、既有31來源49點及五船24點回歸通過；新9畫面9216000個RGBA與繼承五船15360000個RGBA全等。正式69項GUI中60項五語原版／HD及游標畫面驗215040個來源RGBA、50720個游標RGBA及61068416個區外保留RGBA。153筆實際輸入四側至223000000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。4種啟動回退／恢復、82檔封裝及248項拒絕通過。78張繼承原PNG保持；原始290格在後畫字形撤銷3格後剩287格有效，原alpha保持。世界移動、戰鬥、受損砲台065及動畫未由本批外推，全量HD未完成，沒有新發行。

本批共用小圖像層為39來源、38張美術，第100幀沿既有人物層。原稿現已原樣收於graphics/icons-008.png、icons-009.png及icons-016.png，完整生成提示、權利及指紋見[清冊](../../graphics/manifest.json)。

[游標檢查器](../../tools/check_hd_ship_cursor_surfaces.py)新增--profile vehicles，核對本機R71根的18點原版來源、完整游標表面及兩個無來源守門回退；預設ships保留原五船固定收據。[RGBA檢查器](../../tools/check_hd_ship_pixels.py)同加--profile vehicles，搭配--runtime-output指定r73-vehicles-native18-r3重算9張原版固定畫面，加--gui則核對r73-vehicles-gui-r3的60項五語畫面。取樣使用各幀native_content_rect，原版後畫字形、透明處及實際游標都各自保留。

實際GUI採R3建置，正式程式與回歸驗收採R4；R2／R3／R4所有非測試Go來源及二進位全同。R2只計完整通過的載入／啟動測試，R3計修正預期後的新三幀，R4分三個有界行程計舊31來源、五船及小圖像資源。未完成／失敗案例不計通過，初次容量、來源數及500秒套件期限紀錄保留。

| 收據 | SHA-256 |
|---|---|
| r73-vehicles-ready-review-r2.json | 1f01163ee78a7c042f696f9fa8a55a63b382f80dc1f76fea428204658623ebec |
| r73-vehicles-capacity-ready-review-r1.json | aea6ea7dea862cbc8066a6669175461694e61e5129d892eb100cc1bd2f059662 |
| r73-vehicles-conformance-r1.json | ba17a1b0aadbdcb5cb5d535685df0498630e6fdbd969cfbed183afd736844fee |
| r73-vehicles-build-r4.json | 54592b26b04e7efa92e97fb1b9204f65b9bed64e3a940868f3e4f2df871c38b3 |
| r73-vehicles-tests-combined-r4.json | fbea817819c0bdf5ec3c4857d6445b913b979d30d90f5af66bde16736a154c72 |
| r73-vehicles-gui-pixels-r3.json | 0a8867623b5ab0f4954eaac0b554d471ec98d1e6d58bcbfcdd101b7b550cce03 |
| r73-vehicles-replay-r3-check.json | f03929bfc0b6ffad6ff030eb18579678deae1687c9688afed0882a5704b77d82 |
| r73-source-index-formal-r1.json | 8caf646f5200e3b1e0e18f3489d9d8f9e72fb6b4b456b21d8c52acb68d18e68a |


正式二進位為fa4307f1388e3bfd953359b501a0513ea0a62c2ba47214156895fb22a7f4f11f，清冊為336653b647cd381931be990409b71bd0abcfdbb6ebf3d3db0054c6d7ee6b70c8。
[來源索引組裝器](../../tools/build_hd_source_index.py)新增--vehicle-ready-report與--vehicle-conformed-report，核對78張繼承原稿與本批驗收後附加三幀CONFORMED。1552筆原始事實、R71的80種研究及R72五船證據保持；已知未接線的新來源剩41種，未命中來源及其他格式仍未排除全量範圍。

## R74殖民者同頁22幀：READY契約及限定CONFORMED
本節保留實作前READY契約；2026-10-17完成正常殖民者百科同頁22幀的限定CONFORMED。既有81張原稿保持，新增原稿不代表全量HD完成。
原始ICONS.SS、VICEROY.EXE、工具版本及位址空間沿本規格固定表。R71的獨立逐寫檢查已證實本表各幀的唯一來源、完整編碼、三個writer、返回、有效身分及正常可見像素。source call次數不代替可見性；本批採pedia-unit-05的逐點所有權與畫布核對。

既有39槽位保持，在表尾追加22槽位，共61來源。來源與完整逐寫守門、未知後畫含同值撤銷、原版色號與既有標準游標守門保持，不增加觀測器或遊戲寫入。原稿保持單幀PNG與原alpha，alpha至少128只量取樣框；各幀依原版不透明內容矩形縮放，不套完整16格高度。新增清冊338537bytes仍低於512KiB，PNG上限8MiB保持。

| 原始序號 | 原版尺寸／內容框 | 原PNG SHA-256 |
|---|---|---|
| 058 | [6, 16]／[0, 2, 6, 16] | 61743ce80d8c32b180b1cc8c778af73cde0935115f1a83cd0099f2e8cd6179ce |
| 060 | [6, 16]／[0, 2, 6, 16] | 5422ec86e9c250d02fcdfaa731a3d8fdc34fcd3a74ceec5586aae72bd6836224 |
| 066 | [8, 16]／[1, 1, 7, 16] | 2ee09b5d97a813fe09b714f45c6ef302b5a9021ba5b260ce7b7c66976cd930de |
| 081 | [8, 16]／[0, 2, 8, 16] | 860dbb88125bf15711a9cec5f79429de211203f5a25119834200f01557b570f0 |
| 082 | [6, 16]／[0, 2, 6, 16] | 6064d0f3c204d227e3cc202a131b65777a19920f6db007f22889359d412f39c2 |
| 083 | [6, 16]／[0, 2, 6, 16] | daebfb120f397c41f2fc68e1e1ea8edf570a27a1f1dff300553234de119100da |
| 084 | [6, 16]／[0, 2, 6, 16] | 0bc1b2bf46b52a2d038cc4abddcb8617da9b111d6cebabbaeb6dd41336dae201 |
| 085 | [8, 16]／[0, 2, 8, 16] | f19cd765d4b288c2b56af2d20abaa1bdd0fe0c026da11f98088fe85078c5e203 |
| 086 | [8, 16]／[0, 1, 8, 16] | 0eb43567c95ccf81cfcc107db10cacaa67d341b358da2043456a7793da8ef8c2 |
| 087 | [8, 16]／[0, 2, 8, 16] | 9e440f2b86014f715a2ba92a9ab583ff71299d0d00f8e66eb77728c98cf460cd |
| 088 | [8, 16]／[0, 2, 8, 16] | 418541b1e716f9ff84bdc962eaa1f3c927ff5e7f18aab689b07e96eba55431f7 |
| 089 | [8, 16]／[0, 2, 8, 16] | e8c3874a0308134a36a634cd33201d2fc5350fa5fb8d42517e743e8f371733ad |
| 090 | [6, 16]／[0, 3, 6, 16] | 304baa75c942ea22384ccddf23edb50556ce87bc5f0fafa9092a6386478d42b7 |
| 091 | [6, 16]／[0, 3, 6, 16] | 6733d1909558a3d29136749d19c79b47489a9ee01869a55220cbcfdb603ddc53 |
| 092 | [6, 16]／[0, 3, 6, 16] | 9941464e8109e280301c26a6fdcacce810e9caa93931c547d3cb39de4b2b3806 |
| 093 | [8, 16]／[0, 2, 8, 16] | c1a16585d2424e742a00bc77824ebbcb54e98b786a99dce7bcd93331a8bf465d |
| 095 | [8, 16]／[0, 3, 8, 16] | 8103c8a0a1c837df57c1f31fa6c37ff24203684f3f16315b47218ada3b84232e |
| 096 | [7, 16]／[0, 2, 7, 16] | 1d7d88bc8004429571398c5f58e9528967e9565a1c5e5688a11389a7019e683c |
| 097 | [7, 16]／[0, 2, 7, 16] | fc64e8b372dd064311e6e817a6a5b6bfcfdfc6515c8391e83c5297e5e359a38c |
| 098 | [6, 16]／[0, 3, 6, 16] | 5561bf7138e91d27e89698b83431c7dd46bc5708f28b7fc6fe76bf66f26b562d |
| 106 | [6, 16]／[0, 3, 6, 16] | dbae8283bf2236b5b69e457f78d278c2df78f640f6a79010f6b0f33314ae8417 |
| 107 | [8, 16]／[0, 4, 8, 16] | fd6afc141275a481ac18631e86dcf0394c56fbdf8b578e83ba3afc360338dc9b |

內建imagegen完整提示、參考指紋、尺寸及原稿見本機R71根r74-colonists-generation-r1.json，SHA-256為b63e5c9236e4aab8b863bbc1cf5bd6ed5149489cd3ad5372dc33bfed5c558887。READY審查r74-colonists-ready-review-r1.json為27f5d23cd4d57b9842e3ba8fff7147cdb739d40b6c06fc803f759246524596d9；逐格透明量測保存在samples。原稿放入[素材清冊](../../graphics/manifest.json)，原版參考只留本機。

驗收須核對正常載入與百科操作、22幀獨立原版來源模型及每幀20項真實來源反例、五語原版／HD、逐幀游標懸停／返回、原RGBA透明處與旗標保留、區外相同、原版CPU／RAM／索引／DAC／音訊／存檔、缺件回退及封裝白名單。既有39來源須抽測回歸。來源測試可隔離新22幀的繪製；正式GUI仍以完整HD層驗證，不能以隔離圖取代正式畫面。世界移動、戰鬥、動畫與其餘圖像不授予信用。

資源測試分批入口：[Go測試TestHDResourceAndStartupFallback](../../tools/hd_runtime_test.go)可用TEST_HD_RESOURCE_CASE_CATALOG輸出完整案例名；另設TEST_HD_RESOURCE_CASE_CATALOG_ONLY=1只列清單，不授予錯件驗收信用。TEST_HD_RESOURCE_CASE_SELECTION指定JSON字串陣列，拒絕空批次、重複或未知名稱。每批仍先驗完整副本載入，逐案使用原錯件操作、全載入拒絕與原版RAM不變檢查，復原全部暫存檔後才通過；案例全集與完成子案例的聯集必須一致。這些環境變數只用於測試，不進玩家流程。

[本批獨立RGBA檢查器](../../tools/check_hd_colonist_pixels.py)以--root指定本機R71根、--assets指定graphics；--runtime-output指定54點原版測試輸出，加--gui則驗正式五語畫面。它另驗同頁既有59、94及100幀，保留原版旗標、原alpha、實際游標及其餘像素。

## R74正式驗收收據

規格070 R74正常殖民者百科22幀限定CONFORMED。合計103張生成原PNG／清冊104檔，59Go／42綁定；既有81張原稿與清冊紀錄保持。六類Go測試含子案例去重329項完成，計入案例零skip；完整副本逐檔拒絕323項、小圖像資源245項及go vet通過。54點／81輸入、440個真實來源反例及46080000個RGBA全等；既有31來源49點、五船24點、三類18點回歸通過。正式63項GUI中54項為五語原版／HD及22幀游標懸停／返回，驗2405376個來源RGBA、55648個游標RGBA及52737536個區外保留RGBA。97筆實際輸入四側至123800000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。4種啟動回退／恢復、104檔封裝及314項拒絕通過。1381格來源中1353格實際HD繪製，28格沿原alpha透明保留。世界移動、戰鬥與動畫仍待驗，全量HD未完成，沒有新發行。

本批只在既有來源表尾追加22槽，共61來源／60張小圖像美術，第100幀沿人物層。正式程式演算法保持，原PNG、alpha、原版旗標與後畫字形逐點核對。54個原版截點的CPU、完整RAM、索引、DAC及輸入均與實際GUI相同；52點符合完整游標表面，另兩點為無本批來源的載入守門。22次完整來源繪製與26624事件經獨立模型重建。主畫布暫存轉送、RAM保存／還原與游標來源還原皆0，不新增還原信用。

正式GUI採R1，驗收與建置採R2至R6；六版所有非測試Go來源與二進位一致。四個正常來源測試在R2完整通過；小圖像資源測試在R4完整通過。大資源測試計112個已復原完成的R4子案例、R5九批208個剩餘案例、R6補齊地形079的三個案例，聯集等於323個必要案例。中斷父行程、失敗嘗試及僅列名行程不授予通過信用。

歷史資源測試勘誤：舊Go測試副本漏複製部分正式圖像及CUSTOMIZ.PIK，某些逐檔錯件案例可能因無關缺件而拒絕。撤回這類R72／R73逐檔負向信用，保留原紀錄；現行每批先證明完整自有副本能載入，再逐案以新Machine測缺檔、壞檔與連結，通過前逐byte復原全部檔案。103張原稿皆有這三類反例。正常來源、實際GUI、CLI啟動及封裝證據分開保留。

R74第一次測試入口誤指R73舊腳本，失敗紀錄保存在r74-stale-test-entry-r1.jsonl及同名JSON；舊r73-vehicles-tests-r3.jsonl被該失敗輸出覆寫，不能再以歷史雜湊引用該原始log。原R73彙整、正式審查與18點圖像收據保持；本批已重新驗三類18點及9216000個RGBA。這次錯誤不改正式程式或素材。

[全131來源檢查器](../../tools/check_hd_unit_lifecycle.py)的最終可見像素等式不適用本批游標覆蓋截點，R74全點檢查拒絕，未改寬條件也未授予全131重驗信用。正向來源沿R71已證實資料，另外以新22幀RAM模型、完整游標表面、54點來源測試及正式GUI驗收。其他玩家路徑仍待驗。

本機證據根為workplace/reports/goal186-display-hd/hd-sprite-batch-r71；commands-r74.json保存容器、精確命令入口與工具雜湊。[來源索引組裝器](../../tools/build_hd_source_index.py)以--colonist-ready-report及--colonist-conformed-report附加限定驗收，原1552筆事實與R71研究保持。

| 收據 | SHA-256 |
|---|---|
| r74-colonists-ready-review-r1.json | 27f5d23cd4d57b9842e3ba8fff7147cdb739d40b6c06fc803f759246524596d9 |
| r74-colonists-conformance-r1.json | 70349035b3ca433349d4fe3a6fc8219acef55e1231eadb714443f94500adb6f9 |
| r74-colonists-build-r6.json | 80a8d92df3990901c07a7ea52cac4067552d7aaee41405d963137c517b7857c3 |
| r74-colonists-tests-combined-r1.json | c6d5793de57b03ffc5e49d064978e1b74170bf46f6be578fc9f29527478a08db |
| r74-resource-complete-r6-check.json | 6775db636b5a092fa0e60fa12dad7799089254ce2d4fd155192e6f67b499f7d2 |
| colonists-ram-r1/model-r1/check.json | b6da3cef172296ce2abbd900413743d6287678a0cb3def046341112f6c2ba2ea |
| r74-colonists-cursor-surfaces-r1.json | 3ce2ee57799424f3c08acaf6e7c57f9f52c2f93f34dbad2c136bdd681cee3e81 |
| r74-colonists-native-pixels-r1.json | ff935f5064ed3934891e5db468f6125dcf23382166ed2a01c03c47597b31144e |
| r74-colonists-gui-pixels-r1.json | c7ef362b7ab1dbed83191a631bda59f0bfdf825453494fad79ee08bef01143d6 |
| r74-colonists-replay-r1-check.json | db584141f21bcda5d8da06f341790b42a4bae27a42ed1b30143801459e16395a |
| r74-colonists-startup-r3/check.json | 1ae42ee9811dc80b1927b737a69aa4842f489bf1bc358d4f6734241a2a751467 |
| r74-colonists-package-r1-check.json | 1aee1cc36296e75697dbd16b8eb89b35f0f109abec2c2c38bfca5e6930dd2772 |
| r74-source-index-formal-r2.json | 904f7d6f25f16f640cd7382ea3b867c58662e02c326ea3fa3d3f8e225372d0f6 |
| commands-r74.json | e47b9de2dc545f13e5501dbe0704cea579b4504eadfbddff00155267b0654848 |

正式二進位為7a9470f550b7160ff5ee83dcc83d3fc75ffcea5884d578cc58592fed6684903a，清冊為963b67ab9fdbdf02577a063dca488a525f7491cbf9d769c3f9c664117adcb758。

## R75剩餘19幀原稿：DRAFT

R71已知未接線來源現剩065、073至077、101至105、109至112、125、126、128及129，共19幀。原稿已依現行單幀PNG格式與定稿畫風生成，尚未加入graphics或正式來源表。完整提示、參考指紋、原alpha及尺寸保存在本機r75-unit19-generation-r2.json，SHA-256為5e0f75101623cbdc507df727906090300af5fd2786dea1556ef88981cce83f7e。原版參考及候選留本機。

正常百科操作、來源、後畫與逐幀游標驗證接續本節；第112幀原始117格不透明像素只剩116格有效來源，沿R71後畫撤銷證據，不把原始數當成有效所有權。這19幀與其他未命中來源、世界用途及動畫均不計正式完成。

## 升級條件

1. 新幀的完整來源、正常用途、實際寫入、遮擋與撤除有獨立原版證據。
2. 生成素材與取樣方法沿已確認畫風，比例、位置及互動區域依原版。清冊格式與公開範圍已有使用者決定。
3. 每幀的正式來源守門、逐寫指紋、未知後畫撤銷、游標與RAM還原有明確契約及反例。
4. 正常GUI、五語與原版模式、獨立像素、原版狀態／音訊／存檔、缺件回退與封裝白名單驗證通過。

本規格只處理已驗單位幀。百科圖示命中不能取代世界行走、戰鬥、特殊游標或動畫的驗證，也不能宣稱全量HD完成。
