# 完整語言包與原文快取交換

狀態：CONFORMED。整包載入、原文重建及交換已通過正式入口與正常存讀檔抽驗；全遊戲覆蓋與HD另列目標186。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。
使用者已確認五語及四地區Noto；本規格處理既定切換要求，不變更原版資料格式或玩家操作。

## 接線前基準證據

confirmed：182e911的正式前端仍在啟動時各自讀取13表與67份字模資源。
67份包含64份固定字模及3份海上／對話／字串圖集；各有自己的來源、譯文、
字型及幾何契約。入口為[live_menu.go](../../tools/live_menu.go)，
基準資源盤點收據見下方。此前Noto圖集原型只有對話與字串兩類；
本輪已補齊固定字模及海上圖集候選，完整資源組裝見下文，正式前端尚未讀取。

confirmed：[dialogShown](../../tools/dialog_overlay.go)只保留譯文、逐行原文、
安全區及已繪字模，段落正文的原始字元與字格沒有完整保留。
[stringItem](../../tools/string_overlay.go)保留原文，但沒有保留來源run的完整角色、
描邊、離屏及逐字色號證據。不能從譯文反推原文，也不能從目前字模猜測原版樣式。
海上seaRow保留原文及來源像素，但parts與合成字模已綁定當時語言。

confirmed：[設定後端接點](../../tools/display_ui.go)目前只支援既有繁中與原版英文。
設定交易已依[規格056](056-display-settings-runtime.md)驗證；完整資源交換仍未接線。

## 隔離原型契約

- 準備階段完整載入目標語言的13表、14組句、全部顯示資源及逐欄量測資料。
  核對原版來源指紋、表與譯文綁定、Noto地區、字型、授權、字形及幾何。
  不補繁中、不混用Cubic、不以可點選當成整包完整。
- 準備階段不得推進DOS、修改原版記憶體或存檔，也不得改動目前顯示資源及快取。
  任一缺件或綁定失敗，保留當前設定及畫面，沿既有設定介面回報載入失敗。
- 提交階段只交換已準備的記憶體資料，不讀檔、不烘字、不執行DOS。
  保存失敗沿規格056撤銷；開啟、套用、取消與放開實體輸入的契約維持原樣。
- 原始觀測須與譯文快取分開保存。保留原文、原版字格、色號、基線、
  來源角色證據及安全區的來源像素，不把舊譯文或舊中文墨跡當成輸入。
  觀測仍須有界；失效或被原版覆寫的內容不能因切換重新出現。
- 在暫停狀態以當次原版畫面及保留觀測重建目標語言。切換不依賴原版重啟、
  重印或額外玩家操作；原語言排不下但新語言可排的內容，也須能重新評估。
- 每個欄位仍依其已驗來源、原版字高、基線及安全區選字。
  固定字模、長文分頁、多色、離屏地圖字、玩家輸入與保留英數分別驗證。
- 英文直接顯示原版字體；其他四語的保留英數使用對應Noto地區字型。
  缺譯或未驗欄位回原文並記錄，不隱藏文字。

整包檔案編排與快取實作尚未定稿。優先沿既有13表、字模及圖集格式；
需要新增內部索引時，先以隔離原型證明能完整核對及交換，不改原版檔案。

## READY與驗收閘門

1. 完成64份固定字模及3份動態圖集的四語逐欄量測、最長譯文與ASCII覆蓋。
2. 隔離原型驗完整載入、缺件、錯語言、錯地區、錯綁定及取消／保存失敗，
   失敗前後生效資料與原版完整狀態相同。
3. 保留原文與樣式的獨立觀測可重建目前畫面，包含原語言缺譯或排版失敗的情境。
4. 證據審查後才能升READY並接正式後端；其後以四語及英文正常GUI、
   存讀檔及完整原版同狀態比較驗收，不由字形檔案存在推定通過。

資源盤點本機入口為
workplace/reports/goal186-display-hd/display-phrases-20261011/runtime-resource-inventory.json。
這份收據只列來源及資源鍵，不執行原版、不產生正式語言包，也不增加shown。

資源盤點SHA-256為1c1ace6de7f3ab908adad5fed694f7e5347dd96e21876086bcfee735af6f30ee。
工具為colonization-verification:20261007-runtime-r2內Python3.11.2，
輸入為規格059已綁定的本機bundle。每份資源的字型、資料表雜湊、欄位、字級及尺寸
均保存於收據；未把Cubic尺寸推定為四語Noto排版。

固定欄位的隔離量測入口為[組裝器](../../tools/build_language_resource_probe.py)及
[載入後匯出器](../../tools/language_resource_probe.go)。它在正式來源通過既有綁定後，
匯出64份固定字模的來源身份、原版墨跡、安全區及目前位置；隨即結束，不執行DOS。
輸出只留workplace，不能把其中Cubic字級或字模尺寸當成Noto定案。

## 2026-10-11：64欄量測與完整資源候選

四語各64欄共256欄完成離線量測。工具入口如下：

- [逐欄烘製器](../../tools/preview_noto_fixed_masks.py)：以正式載入後匯出、原版墨跡及安全區
  量測四地區Noto，不把Cubic字級當成新字級。
- [獨立檢查器](../../tools/check_noto_fixed_masks.py)：核對13表、完整譯文、地區、來源綁定、
  Alpha長度、定位、陰影及PNG。長文逐字核對，沒有裁切或省略。
- [候選包組裝器](../../tools/preview_noto_language_bundle.py)：組裝每語13表、64固定字模及
  海上／對話／字串3圖集；英文候選只宣告使用原版顯示，不含替代字形。
- [Go隔離載入器](../../tools/language_bundle_probe.go)與
  [實際資源測試](../../tools/language_bundle_probe_test.go)：讀取完整候選，驗證每檔指紋、
  原版安全區、字模層、字型地區、文本綁定、各級字格及95個ASCII。
  正式組裝器沒有連結這兩檔。

原版欄位墨跡大部分來自正式來源的固定幾何。八列選項另取
[原版逐欄差分](../../tools/prepare_goal113_options_preview.py)；介紹頁標題8列、正文9列及
10列行距依[規格025](025-first-nation-introduction-draft.md)，教學正文7列及10列行距依
[已驗量測](../../tools/preview_goal142_help.py)。製作名單5列及載入訊息7列依
[規格034](034-static-text-overlay-draft.md)。這些來源在烘製器內固定指紋。
包含陰影的原版改色聯集，沒有推定為前景獨立高度。

每欄候選從該欄原文字高的四倍值計算，最低為其2/3且不低於12px；
依完整文字的墨跡、可用寬高及原版對齊選擇最相稱的合格字級。
主選單五列仍量得24／24／20／20／24px，其他欄位分別量測。
問句及開場字幕保留原版雙行上限；介紹及教學分開量標題、正文與行距，
大括號強調另畫一層。每份候選保存原版字高證據、全部試字級、最終字級、
基線、文字行、定位、安全區、實際墨跡及回原文策略。
烘製先畫在額外留白的畫布上核對，避免以裁切後bbox冒充無越界。

候選包是DRAFT內部索引，尚未定為正式發行格式。每份manifest列出語言、字型地區、
來源版本、授權指紋及80個檔案的SHA-256。海上圖集沿既有22至15px八級格式，
字格取完整Noto圖集；海上各欄位的實際排版仍待原文重建後驗證。
準備函式只回傳已載入資料，不存取DOS、設定保存或生效中的前端物件。

Go驗證有30個子測項，含5個實際語言候選及25個錯誤輸入，零skip、go vet通過。
兩次乾淨重生的固定字模565檔、完整候選包326檔逐位元組相同。
反例涵蓋缺檔、錯語言／地區／來源／授權、錯內層文本綁定、錯安全區、
錯Alpha、漏字級及缺ASCII。內層反例重算外層檔案hash，避免只驗到外層指紋。
所有失敗均回傳錯誤及nil候選；尚未驗正式提交、取消及保存失敗後的資源交換。

本機根目錄為workplace/reports/goal186-display-hd/language-resources-20261011/：

| 收據 | SHA-256 |
|---|---|
| fields.json | 2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d |
| noto-fixed/check.json | 93f35b3d28c40256b5e2e622254dccfd5f860401444e062e604b21ac2222fc1f |
| bundles/check.json | b9d3e4874bb5433ebecfbb094697b1b3c5508aed6e4ab9479a7d0f7ccc01b893 |
| bundle-probe-tests.jsonl | bad11a0190acf2628753d9764e3fbee35b8a8bd0a3b67c957e64f34e5cadb453 |

工具鏈為colonization-verification:20261007-runtime-r2的Python3.11.2、Pillow9.4.0、
FreeType2.12.1，以及hr-go-ebiten:1.26.7-2.9.9-r1的Go1.26.7。
字型及授權仍依[固定來源](../../font/README.md)。
重驗時先以逐欄烘製器的--fields、--baseline-masks、--noto、--license與新的--output
生成固定資源，再以候選包組裝器的--fixed、--fields、--baseline-masks、--atlases與
新的--output組裝。--atlases指定規格057最新2022筆的完整四語圖集。
Go測試需將DRAFT_BUNDLE_ROOT設為候選包根目錄，並單獨指定上述兩個Go檔；
不把原型加入正式組裝來源。

規格維持DRAFT。本批尚缺獨立原文觀測、暫停時重建、正式整包交換、四語正常GUI及
完整原版同狀態驗證。沒有新增shown、完整五語或HD完成信用。

## 2026-10-11：獨立原文觀測與暫停重建切片

工具仍由隔離組裝器連結，正式前端及dosgolem未改：

- [原文觀測器](../../tools/language_observations.go)與
  [深拷貝及容量測試](../../tools/language_observations_test.go)：在翻譯前保存完整來源run、
  逐字位置、字色、印前／印後像素、描邊、貨物角色、離屏來源及當次原版畫布。
  字串接點在快捷鍵與描邊合併之後；海上選單等待完整39字序列。
  無模板或排版失敗的原文同樣保留，不由譯文回推。
- [隔離組裝器](../../tools/build_language_observation_probe.py)：固定正式來源指紋，
  僅在新workplace模組插入觀測接點。--with-rebuild另外連結完整包載入及停止後重建切片。
- [四側重播檢查器](../../tools/check_language_observation_replay.py)：比較觀測開啟、關閉、
  前版與原文控制。--bundles指定完整候選根目錄時，另檢查停止DOS後的五語輸出。
- [暫停重建切片](../../tools/language_rebuild_probe.go)與
  [完整安全區測試](../../tools/language_rebuild_probe_test.go)：執行前驗五個完整候選，
  載入既有對話與字串目錄；停止DOS後只用記憶體中的原文與Noto資料重建。
  本切片尚未接入海上、固定欄或正式設定提交。

觀測上限為256筆及32MiB的估算成本預算，超限移除最舊完成事件並計數。
成本不是Go heap實測值。沒有以矩形重疊猜測整段原文已失效；
收據中的visible只證明保留的來源像素仍相同，不授權正式覆蓋。
重建還須驗完整安全區、來源角色、既有模板條件與目前VGA。
歷史VGA同步、部分遮擋及畫面世代仍待補足，不把此切片當成完整生命週期。

第一批只讀觀測以規格059已驗正常GUI的25筆輸入重播至76200000步。
四側CPU、完整RAM、VGA、DAC、WAV與存檔全同；三側繁中合成RGB亦與GUI基準全同。
共保存201筆、拒絕91筆、容量移除0筆；終點53筆的全部來源像素與完整RAM獨立核對相同。
201筆含140字串、30對話、6離屏字串、24海上狀態及1完整選單。
拒絕數不等於缺譯數，包含沒有完整墨跡的片段。沒有新增現場GUI或普查shown信用。

五項新觀測單元測試及既有完整回歸共443項通過，零skip、go vet及建置通過。
初跑缺少唯讀原版及既有字型收據，18項明確skip；補齊相同既有輸入後乾淨重跑。
收據位於本規格上述language-resources-20261011根目錄：

| 收據 | SHA-256 |
|---|---|
| native-tests-full.jsonl | b01f90ccb455d512256654751817f1de1c2e96b3f7b692150ea3f20d51577baa |
| native-replays/check.json | c82b4112d4d194d823130df7724e86e66fbf467f046c019f26e7e98e7e45f237 |

只讀觀測二進位為1ac3949a139ada56ebd6044c89b5f2050f5172305a997dd290a0166b0f0f444c。
這是新增游標及原始byte匯出前的收據；後續重建批次另存新輸出，不覆寫。
重生時以--reference指定既有前端模組的go.sum目錄，不能指定無go.sum的dosgolem根目錄。
建置仍在既有Go工具映像，隔離副本掛載於/dosgolem；正常重播仍用既有驗證映像及有界Xvfb。
完整原文、畫布、字型、圖集及畫面收據只留workplace，不納入Git。

後續切片在完整載入時發現日韓各155個殖民地名稱缺少既有消費端所需括註。
依[規格053的格式勘誤](053-language-catalogs.md#2026-10-11殖民地名稱的消費端格式勘誤)
補上同列已驗原名，11項文本測試通過。四語字模及圖集重生後，
256欄圖像與152組字形資料和前批相同，只更新兩語文本及相關綁定。
最新五語候選及25反例共30子測項通過，原型446項Go零skip、go vet及建置通過。

同一條25筆正常玩家輸入再次作四側重播，終點76200000步的完整原版狀態、
RAM／VGA／DAC、WAV及存檔全同，三側既有繁中合成RGB與GUI基準全同。
原型在DOS停止後依序重建繁中、簡中、日文、韓文及英文，不重啟或重印。
每語用自己的完整包重新解原文，不沿用前語譯文；重建前後再比CPU與完整RAM。
實際套用欄數為8／8／7／8／0，英文直接使用原版；四語差異只在當次安全區。
日文Jamestown含原名放不下，記錄does-not-fit並保留英文；韓文同欄可用19px重新排出。
這個結果證明同一份原文可以重新評估字級與回退，未驗正式設定交易或所有玩家畫面。
已檢視日韓輸出，頂列、日期及海上組句尚未由這個對話／字串切片接手。

| 最新收據，相對本規格的language-resources-20261011根目錄 | SHA-256 |
|---|---|
| noto-atlases-colony-fix/check.json | 3f18bd32b361e78a1841af379f4aa8dea2450ce2e89512c7df8372f97f105133 |
| noto-fixed-colony-fix/check.json | 64993f8b4e8a961685c6c20376f4f28348d9424693b3f0cb807f196917f7b049 |
| bundles-colony-fix/check.json | 8889384c1a7c209d0f53d779992525e847175851d48e241e7763f25461ee9b85 |
| bundle-colony-fix-tests.jsonl | 98f370aea7bddaabdc8b27b80e70e492008b25667dd579084c5e9e91236f78af |
| native-tests-r5.jsonl | 53c1d2fab4c73413043d76bdde5e9fdfac3c2846e9cceaf7aa638c095ebd8ad7 |
| native-rebuild-replays-r5/check.json | 7d82b01bdc0d161ae765d504658871b678d2b7111418dbde0cd8528df61ff75c |
| native-rebuilder-r5 | 26bb1c3f73c46f55ed82849964c4815f6017887845d3963d5d935fc6f1e38f42 |

實測檢查器逐字副本保存在同根check-language-observation-replay-r5.py，
指紋e00caaf724c4afa27e44d7c3a8e90f45919a71585de5d5f72ff3e0c26ebea141。
受版控版本其後僅修正收據限制的描述，檢查條件未改。
重驗以--with-rebuild組裝新模組，檢查器的--bundles指向bundles-colony-fix，
其餘--binary、--formal、--gui、--launcher、--seed、--game及新的--output均須明確指定。
正式前端未連結這些原型；規格060維持DRAFT，海上與固定欄重建、失效生命週期、
正式整包交換、四語正常GUI及存讀檔仍待完成。沒有新增shown或HD完成信用。

## 2026-10-11：海上頂列與狀態欄的停止重建

接續前節，隔離[重建器](../../tools/language_rebuild_probe.go)已接海上原文事件。
四語候選在執行DOS前載入海上詞典與15至22px圖集，逐詞核對原始檔案、
雜湊、偏移及原文；地區、字型、授權與圖集綁定仍由完整包載入器核對。
正式顯示來源、dosgolem及原版資料沒有修改。

頂列仍要求39字完整來源序列與原版起點，六個欄位各自量寬。
正常GUI基準的六欄起點為四倍座標52、180、308、460、628及1020；
下一欄起點或畫面右界扣除2px陰影空間後，分別可用126、126、150、166、390及258px。
快捷鍵與譯文採同地區Noto，以量得的字寬銜接，保留149及68色號。
本次四語六欄均可用22px；縮字、過長、缺字及不完整來源另有反例，
不能把本次選擇外推到其他欄位。

日期、金額及狀態欄沿[規格032](032-sea-menu-and-status-draft.md)模板與22至15px範圍。
原版日期墨跡為(242,51)至(281,57)，金額為(242,58)至(309,63)。
每個候選依原版墨跡頂端、圖集cjk_ink_top及實際前景／陰影聯集計算安全區。
來源像素、整個安全區或VGA不符時保留原文，已知游標像素最後回貼。
海上行先沿原版位置替換；成功重建的行才阻擋重複的通用字串覆蓋。
找不到海上模板或排版失敗的紀錄包含原文，通用字串仍可按既有規則處理。
這仍未證明畫面世代、歷史同步或部分遮擋的完整生命週期。

[測試](../../tools/language_rebuild_probe_test.go)新增逐欄縮字、快捷鍵顏色、
截斷序列、不同原文、過長譯文、來源覆寫、安全區背景、VGA遮擋、
已知游標及文字色背景守門。自建字模只驗分支，不當作Noto或原版排版證據。
最終448項Go測試零skip、go vet及建置通過。

[四側檢查器](../../tools/check_language_observation_replay.py)使用原有正常GUI的25筆輸入，
觀測開啟、關閉、前版及原文控制均重播至76200000步。
完整原版CPU、RAM、VGA、DAC、WAV及存檔相同，三側既有合成RGB仍與GUI基準全同。
DOS停止後的四語重建分別有12、12、11及12欄，均含頂列、日期及金額；
英文逐像素等於原文控制，四語變動只在宣告安全區。重建前後原版狀態全同。
已檢視四語畫面及繁中相鄰地形／道路的放大區域，未見裁切或相鄰行重疊。
日文Jamestown仍依前節排版回原文並記錄。

本機收據仍位於language-resources-20261011根目錄：

| 收據 | SHA-256 |
| --- | --- |
| native-tests-r7.jsonl | 2677d8e34cf1d62e9685cd6c9acb1eccdebe1017f040af4be49b72c33ba0fc09 |
| native-rebuilder-r7 | defced4f7a4f1f36dbee525faf9e7a5060ad1efcef297dc1cb493be6fc1fd77c |
| native-runtime-r7/observation-sources.json | f13e3311791e45bcced99f30bb6e446b174174a209e1061712a96733ca8a0152 |
| native-rebuild-replays-r7/check.json | 18392b2e4bb4425f0ae0e6dccfda54ab096f06ecbc4c4124e8e7ffe6876d992d |

工具沿用Go1.26.7／Ebitengine2.9.9及Python3.11.2／Pillow9.4的既有容器。
組裝及重驗參數沿前節，輸出改用新的目錄；候選輸入仍為bundles-colony-fix。
本輪只新增隔離重建證據，未新增現場GUI、存讀檔操作、HD或普查shown。
規格060維持DRAFT，固定欄重建、失效生命週期、正式交換及四語正常GUI仍待完成。

## 2026-10-11：固定欄原文快照與停止重建

接續前節，隔離[觀測器](../../tools/language_observations.go)在既有固定欄接受原版輸出時，
另存穩定鍵、安全區、原版印前／印後像素、色號、陰影及游標守門。
不保存舊譯文或舊字模，也不從舊中文字模反推原文。
一般固定欄以20bit線性RAM畫布0x2cae0為來源，靜態欄使用VGA 0xa0000；
來源檔案與事件識別仍沿各欄既有READY／CONFORMED規格及指紋。
快照、完整RAM、原版圖像與存檔只留本機workplace。

每次渲染前核對整個來源安全區。背景、文字或模式改變便單向撤銷快照，
之後相同像素重新出現也不能復用；需要新的已驗原版輸出事件。
同鍵新事件取代舊事件，上限仍為256筆及32MiB估算成本。
這個撤銷只涵蓋固定欄，不代表對話、字串與海上事件的生命週期已完成。
目前接點仍經既有繁中字模初始化與接受條件；正式接線前須把原文接受與目標字型失敗拆開。

隔離[重建器](../../tools/language_rebuild_probe.go)載入四語各64欄的實際Noto字模。
各欄沿已量測位置、字級及安全區，並保留原版前景、陰影與強調色。
顯示文字由包內TSV重解，字幕槽位、控制碼、名稱冒號及教學術語
依現有產生器契約處理，再核對實際顯示文字的SHA-256。
成功重建的固定欄阻擋重複字串覆蓋；來源、VGA、游標、按鈕或排版不符便保留原文並記錄。
完整包驗證仍先於個別字模載入，不能單獨使用draftPrepareFixed略過地區、字型、幾何及資源綁定。

[測試](../../tools/language_rebuild_probe_test.go)新增四語各64欄實際載入、
譯文指紋與缺鍵反例、原文擦除與量測位置、色號、陰影、游標、按鈕、VGA遮擋及越界。
[觀測測試](../../tools/language_observations_test.go)另驗深拷貝、背景改寫、
相同像素返回仍失效、新事件重新啟用、同鍵取代、模式切換與VGA來源。
最終457項Go測試零skip、go vet及建置通過。
初次r8建置因新測試漏匯入bytes而失敗，補齊後以新的r9模組乾淨重跑。

[四側檢查器](../../tools/check_language_observation_replay.py)完整重播原有25筆玩家輸入至76200000步。
觀測開啟、關閉、前版及原文控制的CPU、完整RAM、VGA、DAC、WAV與存檔全同，
三側既有合成RGB仍與原GUI全同。新增16筆固定欄事件後共217筆，容量移除0筆；
終點固定欄全部已撤銷，海上／對話／字串仍重建12／12／11／12欄，
五語RGBA與前節r7全同，英文逐像素等於原版控制。

檢查器新增--checkpoint與可重複的--expect-fixed，只沿已驗GUI輸入的前綴停止。
四側同狀態另作比較，不把新停點冒充歷史GUI終點或新增現場操作。
32000000步的主選單五列均以四語重建，另有一筆版本字串；已檢視四語畫面，未見裁切或重疊。
12000000步的載入訊息也四語通過，字級繁中28、簡中28、日文28、韓文29px。
英文均與原版控制逐像素相同，四語差異只在宣告的安全區。
--checkpoint-source newgame僅接受既有新局GUI輸入及驗證收據的固定指紋，
用於接續難度、選國等抽樣；仍不宣稱與歷史新局程式或GUI同狀態。

新局輸入SHA-256為bfaf3f2caf06d804bdf4d79376eb057c15fa4a5e157cb7df24a187aa2b1a9e74，
既有newgame-save-review.json為a775ea0ef731e80c4fb3f3d4e754c87e2fbcafde3858cc5fa2ebd2e4af330073。
沿該輸入的70290000步難度頁與77550000步選國頁，四側原版狀態全同；
四語各重建五個與四個固定欄，英文逐像素等於原版，差異只在安全區。
八張四語輸出已檢視，未見裁切或重疊。

88770000步的英國介紹頁另驗多層字模，四語各重建一個固定欄。
原版陰影47、正文68及強調149色號保留，四側完整原版狀態全同，
英文逐像素等於原版，四語差異只在完整安全區；四張畫面已檢視。
這個停點接受881筆事件，因256筆上限移除625筆，保留256筆、估算成本19188136bytes。
目前介紹欄完整來源仍保留並與RAM相同；其他歷史事件不因此取得完整重建信用。
正式快取仍須驗目前可見來源的保存策略，不能把本次容量移除當成完整生命週期通過。
預期固定鍵如下：

| 停點 | --expect-fixed，各鍵分別指定 |
| --- | --- |
| 主選單32000000 | GAME.TXT:0x000001B0、0x000001CB、0x000001E4、0x000001F9、0x00000204，各自保留GAME.TXT前綴 |
| 載入12000000 | OPENING.TXT:@MESSAGES:loading |
| 難度70290000 | LABELS.TXT:0x00000888、LABELS.TXT:0x00000890、LABELS.TXT:0x0000086E、NAMES.TXT:0x00000C0C、LABELS.TXT:0x000008A9 |
| 選國77550000 | LABELS.TXT:0x000008D3、LABELS.TXT:0x000008DB、NAMES.TXT:0x000008EA、LABELS.TXT:0x000008F2 |
| 英國介紹88770000 | GAME.TXT:@NATION0A |

本機輸出沿前節language-resources-20261011根目錄，候選仍為bundles-colony-fix：

| 收據 | SHA-256 |
| --- | --- |
| native-rebuilder-r9 | 220995fb91368ad4653e3343bd50f5107d9999a8a996a611d8a25d7acfe9e5af |
| native-tests-r9.jsonl | f4db9ee43df901d05f30dce199e6f1520859fda0c7bdc6e5dea768d3a8ba6ae6 |
| native-runtime-r9/observation-sources.json | faf675cdd2042a5e1d7e98e7ad32a51d4d75043a8098fc1fc18b2bff1f3bcab5 |
| native-rebuild-replays-r9/check.json | c5d146e7f199460f45d1172b2a5b84c0df7574dc98bdcf7b028e7d2232c03e04 |
| native-main-menu-r9/check.json | 984aa3002cb805da44913873176e969202167469e163986030dd61583980c80c |
| native-loading-r9/check.json | 9e58fbf45af0744cee619bb8bef8f3847979a870956c7a27c9be4c20c70a7638 |
| native-difficulty-r9/check.json | 49c9b155289e5096fe572cf047717e8bdf39f926ddb69f7868f69db480c981d7 |
| native-nations-r9/check.json | f63cfdfc045ab0a0d2aa97944c1e3bb32be51d28b88f88694be31f727021f2d6 |
| native-intro-r9/check.json | 775caff1731109599ccdd1cb4dcba693f459539120a46292feec0e59a5c5ff7a |
| check-language-observation-replay-r9.py | 7495ef2a9f85fcdf40f6c463a40b31801ea894a7b8f8fef2997f51a9ea03d279 |
| tools/check_language_observation_replay.py，新局三停點實測版 | 16cefdd62d6605fea13a741003cc8506187cf539e7879f54db6be2ef66f33f03 |

上述檢查器副本是加入新局輸入來源前的逐字實測版本，正式工具其後擴充受指紋約束的來源選擇。
重生沿前節Go1.26.7／Ebitengine2.9.9與既有Python驗證容器。
組裝使用--with-rebuild；重播指定既有--gui、--formal、--launcher及--seed，
--bundles指向完整候選；checkpoint另給明確步數及預期固定欄鍵。
目前沒有正式設定提交、四語現場GUI或HD信用。規格060維持DRAFT，
其他固定欄正常路徑、完整生命週期、畫面重建及整包交換仍待驗收。

## 2026-10-11：字模缺失時的獨立觀測契約

DRAFT隔離範圍：原文讀取、原版改色、來源／畫面指紋及同步判定
不受目標字模是否可用影響，原文模式也持續觀測；實際顯示仍依原設定回退。
原版版本守門、每欄完整來源、字格、改色數量、色號及同步條件維持原契約。
本批仍不接正式後端，不以放寬原版守門換取命中。

confirmed：固定來源2f5ab4b…在live_menu.go的2053至2143、2431、2762、2794及3152之後，
以舊字模／圖集是否可用控制原文讀寫掛鉤與事件收尾；控制模式也略過這些掛鉤。
靜態欄的原版圖檔、畫面指紋、文字帶與原文色號集合先讀取，
但字色在1145從舊字模帶入，3738之後的辨識又受字模是否可用控制。
上述行號以原始受版控來源為準，隔離組裝副本另有新增行數。

靜態原文辨識與底圖重建沿[規格034](034-static-text-overlay-draft.md)，
字色沿[既有烘製器](../../tools/bake_static_masks.py)的已用公式：
ink_indices第一個色號優先；未指定時，在原版文字帶選出至少10像素的最暗常見色，
亮度為DAC三色和，同亮度維持原版掃描首次出現順序。
原版圖檔、幾何、狀態、重複鍵及當次指紋仍須核對，不能從新舊字模猜來源。
缺譯或缺字模不影響原文識別；只有已準備的目標包可以決定新文字與字形。

退出條件：移除舊字模與三類圖集後，以同一原版初始狀態及正常玩家輸入
比較原文觀測、四語重建及英文輸出；CPU、完整RAM、VGA、DAC、WAV與存檔須相同。
缺失資源確實不存在，不能只把有效字模設為nil就宣稱驗過實際缺檔。
快取容量與目前可見來源保存策略另驗，不因本節字型解耦而取得完成信用。

隔離組裝器已把原文讀寫與收尾從舊字模可用性及控制模式分開，
所有原版來源、改色數量、版本與同步守門保留。靜態欄另核對圖檔、
原文指紋、幾何、重複鍵及當次DAC；字色與紋理補回不讀舊字模。
指紋外框或DAC改變即撤銷舊快照；重新命中完整原版指紋才建立新觀測。
因此載入訊息本批有11880000及13365000步兩筆，分別綁定不同DAC，舊筆沒有復用。

最終r11的459項Go測試零skip、go vet及建置通過。
新測試覆蓋沒有字模／舊字色時的靜態來源、重複幀、只改指紋外框、DAC改變，
以及常見色數量與同亮度掃描先後，字色公式與既有烘製器相同。
首跑因未設定DISPLAY而在視窗初始化失敗，補齊既有Xvfb後乾淨重跑，未改產品判定。
r10缺字模重播另揭露海上收尾後仍執行舊字形建構的nil讀取；
r11保留原文收尾，舊字形建構仍要求字模及非控制模式，再重新組裝與完整測試。

檢查器的--fontless把16個舊遊戲字模／圖集參數指向新的不存在路徑，
並在觀測側啟用原文控制；執行前後均核對缺檔，沒有用--missing旗標取代實際缺失。
--rebuild-reference另比較同原版狀態的既有五語RGBA收據。
一般模式與缺字模模式各作四側重播至76200000步，完整原版狀態、
RAM／VGA／DAC、WAV與存檔相同。缺字模觀測畫面逐像素等於原版控制，
既有兩個繁中控制仍與GUI基準RGB全同；五語重建RGBA與r9全同。
兩組各保留218筆、拒絕91筆、容量移除0筆，完整原文觀測檔逐位元組全同，
SHA-256為91bd1dc1530d473dfdf38947cbe8222dc7af30091daffdb9e1a1d5f866e04469。
218筆包含17固定事件、140字串、30對話、6離屏字串、24海上狀態及1完整選單。

缺字模載入12000000步與選國77550000步也各作四側重播，
四語各重建1個與4個固定欄，五語RGBA與r9相應停點全同。
英國介紹88770000步的缺字模四側比較也通過，四語各重建一個完整多層固定欄，
五語RGBA與r9全同。此停點接受882筆，保留256筆、容量移除626筆；
目前介紹來源仍保留，未據此宣稱滿載快取策略已完成。
這些只沿既有正常GUI輸入重播，未新增現場GUI或普查shown。
規格仍為DRAFT；正式後端尚未連結本工具，完整可見來源保存、生命週期與整包交易仍待完成。

本機收據沿language-resources-20261011根目錄：

| 收據 | SHA-256 |
| --- | --- |
| native-rebuilder-r11 | 1d9559a40f03016d9484b011bdfac9ddf565b312b69b3d732ebf74018f6574bc |
| native-tests-r11.jsonl | 87fe766f767f9161c54657a10a67051d4154fc055b3ea104d01df283999eff44 |
| native-runtime-r11/observation-sources.json | a38ac869cd369d7b7d045f91f10c517e2fcee4820889e07d2c2a184b0c653421 |
| native-rebuild-replays-r11/check.json | 96876626d2cb7a176d7b15fc20b9725830b9b690207cc7016e708fc1e575d788 |
| native-fontless-replays-r11/check.json | 79ccca12c77aa7f36750fe78d96bdd09cd9fb776c5e020541fddfcd8d3628398 |
| native-fontless-loading-r11/check.json | 2f3842e4c0bdf23a5a1fa8cf49fcc02cea9bbc4862776080e79a4cff4d9419a7 |
| native-fontless-nations-r11/check.json | 961f3f3869da22cd6e6def7ef318e723ae35dadb591ad29384b0260bf4fc05bf |
| native-fontless-intro-r11/check.json | 27140164b9c7eb983e7c8547866864747b79e4d66abb3a4893a73ddb23979a80 |
| tools/check_language_observation_replay.py，本批實測版本 | 8cef700993f49edb115a1fb0813895e728187b96863a51291f8bcd524bcd1226 |

重生沿前節既有Docker映像、原版唯讀及明確輸出掛載，Go測試須有有界Xvfb。
組裝仍用--with-rebuild；--fontless及--rebuild-reference加在既有檢查器參數上，
固定欄另沿前節的--checkpoint、--checkpoint-source及完整--expect-fixed鍵。
原始圖像、原文、字型、圖集、WAV與存檔只留workplace，不納入Git。

## 2026-10-11：可見來源容量的停留反例契約

DRAFT：以既有設定GUI的完整25筆原版輸入重播，之後不新增輸入，
只延長原版執行終點，觀察游標等原版重印是否會擠掉仍在畫面上的來源。
檢查器入口仍為check_language_observation_replay.py，新增--idle-until；
只能沿設定GUI來源，不能混用前綴停點，最多增加六億步。
四側核對完整原版狀態、RAM、VGA、DAC、音訊與存檔；
非英文重建仍須包含已驗海上頂列、日期及金額。
這是正常輸入後的停留重播，不增加現場GUI或shown信用。
先保留現行FIFO的反例，再決定最小容量修正；本節尚未授權正式快取行為。

## 2026-10-11：記憶體語言包交易切片契約

DRAFT：沿規格056既有applyDisplayPreferences順序，以隔離後端驗證
完整已準備語言包與當次重建畫面的共同提交。實作及測試入口沿
language_rebuild_probe.go與language_rebuild_probe_test.go，不新增正式前端接線。
準備只從已驗記憶體語言包與當次原文觀測建立新畫面，回傳提交函式；
當前語言包、畫面及設定在提交前保持原樣。提交只交換一個包含完整語言包、
畫面及設定的物件，不再讀檔、烘字或推進DOS。
取消時丟棄候選；設定保存失敗時不提交，當前物件及既有設定檔保持原樣。
本切片只處理已驗原版圖像模式，HD仍依自己的規格閘門。
停止重播後依序驗證五語準備、取消、保存失敗及成功提交，再獨立核對
各語RGBA與原版完整狀態。此證據不取代來源生命週期或正式GUI驗收。

2026-10-12 confirmed：隔離後端以單一物件共同提交完整目標包、重建畫面與選項。
實際五語候選的準備、取消、保存失敗、成功提交及七個不完整候選反例通過；
473Go零skip、go vet及建置通過。r12測試誤把冷啟動五檔指紋表當成全部文字檔，
修正為已登錄檔案先核對，其餘沿各表載入器驗來源，再以新r13模組乾淨重測。

25筆既有正常GUI輸入至76200000步的一般與實際缺字模模式各作四側重播。
每語依序準備後取消、製造設定保存失敗，再成功提交；取消及失敗均保留
舊物件、畫面與設定檔。兩組原文觀測逐位元組全同，五語RGBA與r11全同，
完整原版狀態、RAM、VGA、DAC、WAV及存檔全同。
英國介紹88770000步另以缺字模、--transactions及新局GUI輸入前綴作四側比較，
四語各完整一欄及全部五語RGBA與r11全同，五語交易與完整原版狀態通過。
檢查器從完整RAM、VGA及DAC另算交易原文指紋，並核對各語RGBA與設定檔0600權限。
這是停止DOS後的記憶體交易證據，正式前端、現場GUI及完整生命週期仍待驗。

前述停留切片使用r11原型，25筆輸入不變，終點延長至650000000步。
四側完整原版狀態通過；接受368筆、容量移除112筆、保留256筆，
頂列、日期及金額仍能重建。這個停點未重現所懷疑的頂列遺失，
沒有據此更改FIFO或宣稱可見來源保存已完成。
原90秒重播額度不足，改按終點步數相對原GUI終點同比例計算，未改輸入及比較條件。

本機收據沿上述language-resources-20261011根目錄：

| 收據 | SHA-256 |
| --- | --- |
| native-rebuilder-r13 | 21c64a23a3378def0e0b6788b437a71290d0ec707261a08cce28158bb1a9d3df |
| native-tests-r13.jsonl | 8d15ec30b84dfdf8a403c68112a4867a1debacc50854810d21fddb2f867c9f67 |
| native-runtime-r13/observation-sources.json | 68086616caa69f64138707f5b6833d5df24ed98a078669f74c8240d6a3c5a2e8 |
| native-transactions-replays-r13/check.json | c645048213180527e9e77a6d730841ef7d4a4de31ad50a382bc85b4edd70de1a |
| native-transactions-fontless-r13/check.json | c8c1425faa1f50a8a7f46e7b08814c5dffb6fd0fd255989cd4b89f4577388961 |
| language-transactions-world-audit-r13.json | abb95af352a53e452e229e861591b2f2b15a60a04359e715e454f60574e6f47f |
| native-transactions-intro-r13/check.json | ada7ef1de32a8c28eaae8a9d79dfe56a34d9fb8b938dd73a0b34887fb94ac4ac |
| native-idle-fontless-r11-b/check.json | 0bca058bc78710001ffa3024278da22b59286fc3e3043cfaf0328504b4abab28 |

前三組世界及停留重播的檢查器副本為check-language-observation-idle-r13.py，
SHA-256為7bf271faf11ad0112aaef48bb5c0291a56f448bee8cc42812c21e4c8a0d2173e。
後續獨立交易核對及介紹重播使用check-language-observation-transactions-r14.py，
SHA-256為5abbb6823091f9e2da7d659fe72769fcc239db0bac4d3b116e9b6dff0bba434e。
重生沿既有Docker、唯讀原版及--with-rebuild組裝；--transactions要求完整交易收據，
--idle-until另驗延長停留，兩者不增加現場GUI、shown、HD或發行信用。
規格維持DRAFT；私用原文、字型、畫面、WAV、設定及存檔仍只留workplace。

## 2026-10-12：隔離視窗的五語接線契約

DRAFT：在--with-rebuild組裝的副本加入--draft-native-live，正式來源及建置入口不變。
啟用時須同時提供原文觀測、完整語言候選與既有設定列；不得混用原文控制旗標。
設定準備沿已驗記憶體交易，提交共同交換目標包、畫面及語言；取消與保存失敗沿規格056。
每次原版畫面輸出以當次原文觀測、畫布、離屏地圖、VGA、DAC、游標及按鈕重建。
只有上述輸入及觀測計數全同時才重用上一張畫面；不得把舊譯文當來源，
不得因重用而省略原版畫面改變、語言切換或撤銷。記錄重建次數與耗時，先實測效能。
英文沿原版像素；四語維持逐欄守門與缺譯回原文，HD尚不進此切片。
GUI驗證入口為[五語隔離視窗探針](../../tools/probe_language_live_gui.py)，
沿真實X11鍵鼠操作及已驗初始存檔，記錄五語切換的完整原版狀態、設定及遊戲區畫面。
切換後仍須正常進城、返回世界及核對同輸入重播；目前歷史FIFO、部分遮擋與
完整來源生命週期仍是待驗項，不因隔離接線而升READY。
實際GUI輸入交由[隔離視窗重播檢查器](../../tools/check_language_live_replay.py)，
比較五語視窗、觀測模式、正式前版及原文控制的完整狀態、RAM、VGA、DAC、WAV與存檔。
五語視窗終點另須與本次GUI逐像素相同，停止後的五語重建須與觀測模式全同。

重建器的保留英數項目以當次畫布、完成快照及VGA安全區相符作可見性判定。
新建項目沒有舊合成器的顯示階段，不得因其初始waiting-screen狀態略過已驗來源。
原版墨跡、安全區背景或VGA被改寫時仍回原版；字級沿原版字格與目標Noto的實測邊界。
來源安全區改寫、VGA不符與其他欄位占用都須記錄原文及略過原因。

## 2026-10-12：隔離五語現場GUI與英數可見性收據

confirmed，範圍限本節隔離副本：最新隔離視窗505Go零skip、go vet及建置通過。主選單、世界與殖民地共15組現場五語切換通過，正常進城及返回世界均保留原版操作；四語殖民地各重建19至20欄，含已驗保留英數。23筆實際DOS輸入重播至77600000步，四側完整原版狀態、RAM、VGA、DAC、存檔與重播WAV全同，即時重播終點與本次GUI逐像素相同。
五語切換期間按住套用時DOS步數固定；放開後正常恢復，保存設定與目標語言一致。
實際X11遊戲區與當次輸出逐像素相同；非英文差異只在宣告安全區，英文等於原版。
即時與觀測模式停止後的五語RGBA及記憶體交易收據全同，觀測模式原有畫面仍等於正式前版。
四側重播WAV彼此相同；本節未把現場GUI的即時音訊當成同一比較。

保留英數原先已產生字模，卻因新項目的waiting-screen階段被略過。
隔離重建改依完成快照、當次畫布及VGA安全區相符判斷；沒有更改正式英數合成器。
四語實際Noto候選的可見數字、墨跡覆寫、背景改寫與VGA遮擋反例通過。
現場進城四語均含90與10% (0)，日文抽樣為27px與19px，依各自原版字格量得，
不把此字級外推到其他欄。90% (3)、1與4因source-safe-changed維持原版。
日文Jamestown仍因does-not-fit回原文；其餘欄位略過也記錄來源及原因。
已目視日文與繁中殖民地畫面；數字清楚，未見相鄰欄位裁切。

r16是第一批15組現場GUI及四側重播通過的前驅收據。
r14與r15的開場等待使用了不完整輸入前綴，改用既有正常來源的前五筆後才到主選單。
r17加入英數修正後，GUI已顯示90與10% (0)，但檢查器誤把安全區已改寫的90% (3)
也列為必須覆蓋；保留失敗收據，補記略過原因，r18維持原有守門後乾淨重跑。
本批未放寬安全區、字級或原版指紋條件。

本機收據沿language-resources-20261011根目錄；原版資料、字型、畫面與音訊只留workplace。

| 收據 | SHA-256 |
| --- | --- |
| native-rebuilder-r18 | 2d5f1f1e2924f839ec55181f8282ada3e338302d79044fcf392c1e193b20b48f |
| native-tests-r18.jsonl | eeb3e0dea7002adc9e29a578aeac55e9fd9e2fc0e38d8f24a0069af98f3531a8 |
| native-runtime-r18/observation-sources.json | 8f24d77127915e3304e3db1b8c431afc174de6afae27b9bcfac3812868573641 |
| native-live-gui-r18/check.json | 4c325531a89a390d17bdbc26fef8d325d9bd66f1db9af3a7f09aa3d9a9d613ca |
| native-live-replays-r18/check.json | 0976766f91c2726af84f7da0cf67a9acdf4613935dc1a6ace161ff520b390ccb |
| probe-language-live-gui-r18.py | 7008abd19c1e7fba108490fd0973be5f61a25e063d6d73ed89240d7ab0019384 |
| check-language-live-replay-r18.py | c075c5d606816dd75695327d911ccbfb4b68fabaaa492aa8f7ee64bbbfb903bb |

重生沿前節--with-rebuild組裝與--draft-native-live，再以五語隔離視窗探針及重播檢查器驗證。
GUI使用既有issue56-wagon-sample-gui正常輸入來源與COLONY09.SAV，
來源指紋及實際23筆輸入指紋由check.json綁定。
Go 1.26.7／Ebiten 2.9.9映像與Python 3.11.2／Pillow 9.4／FreeType 2.12.1驗證映像均沿用既有版本。
本次484次輸出、171次重建，限額容器中最長116.043ms；只記錄觀察值，尚未作完整效能驗收。
正式live_menu.go、window_prototype.go、display_ui.go及正式建置入口未改。
FIFO容量、可見來源保存、部分遮擋、畫面世代、其他正常流程、正式接線與HD仍待完成，
規格維持DRAFT，不增加shown、完整五語、HD或發行信用。

## 2026-10-12：可見來源容量的長停留反例

DRAFT：既有650000000步收據的頂列原文仍可見，但已位於保留佇列第24筆。
日期與金額也仍是早期來源；目前FIFO會隨新增觀測移除它們，未分辨當次可見性。
本輪預先固定終點900000000步，沿同一25筆正常GUI輸入，之後不加操作。
檢查器的停留測試上限改為比既有終點最多增加十二億步，只增加驗證額度。
先保存現行r18的來源遺失反例及四側完整原版狀態，再修正隔離觀測容量。
修正須優先移除當次原文像素已不符的歷史觀測，保留可見來源與完成事件的相對順序。
容量及成本上限不變，不以譯文、目標字模或矩形相交判斷來源是否可見。
混合緩衝區與尚未複製到畫布的來源另保留既有守門，不能因容量修正取得顯示信用。
這是隔離保存策略的驗證契約，尚未授權正式後端；其他生命週期與HD仍待完成。

滿載時先合併原文、來源位置、角色、逐字幾何、色號、描邊、游標及原版印前／印後像素
完全相同的重印，只忽略完成時刻，保留最近事件的完整原版背景快照與其完成順序。
不能只按文字相同合併，也不能把譯文或字模放進身份鍵。
其餘依當次畫布、地圖、VGA、DAC及顯示模式判定可見性，先移除最早不可見者。
全部來源仍可見時沿有界FIFO保留最新事件，另記可見來源容量移除數；不得靜默宣稱完整。
合併、不可見移除、可見移除與無取樣分類分別記數。取樣不完整時拒絕新觀測並保留原佇列。

## 2026-10-12：容量反例修正與九億步驗證

confirmed，限隔離副本與預先固定的900000000步停留切片：r18接受434筆、
FIFO移除178筆、保留256筆，仍在原版畫布及VGA上的378點頂列來源已被移除，
四語頂列均未重建。四側完整原版狀態、RAM、VGA、DAC、WAV及存檔全同，
故此反例是觀測保存問題，沒有更改原版或降低可見性門檻。

r19依前節DRAFT契約合併完整相同的原文重印；其餘容量壓力先回收當次不可見來源。
上限仍256筆及32MiB，原文像素、模式及DAC守門保持原條件。
本次434筆接受、197筆合併、237筆保留、17372858bytes、零容量移除；
55110000步的頂列來源仍可見。修正前後所有原版狀態、完整RAM、VGA、DAC、WAV及存檔全同。
四語頂列、日期與金額均重建，差異只在各自安全區，英文逐像素等於原版。
全部唯一來源仍可見時的有界FIFO回退只經反例測試，會明記可見來源移除數，
不以本次零移除宣稱所有長流程都能保留來源。

535Go零skip、go vet及建置通過，新增原文位置／樣式差異、取樣失效、模式／DAC、
成本優先、重印順序及全可見容量反例。相同r19另跑15組實際X11五語切換，
主選單、世界及殖民地通過；22筆實際DOS輸入四側重播至76000000步，
完整原版狀態、RAM、VGA、DAC、WAV及存檔全同，即時終點與GUI逐像素相同。
四語殖民地各19至20欄，保留英數仍依逐欄守門。已目視日文與韓文殖民地。
本次474次輸出、174次重建，限額容器內最長293.160214ms，只記實測值，尚未作完整效能驗收。

本機根目錄仍為workplace/reports/goal186-display-hd/language-resources-20261011：

| 收據 | SHA-256 |
| --- | --- |
| native-rebuilder-r19 | 6c245a8160bbeadf3c7f798b5d819333fb22ffa5712dd6108769aa2b8f0bb4a0 |
| native-tests-r19.jsonl | 6276d5262de3b9f7002ddc2a873f2224aacdf8ceaaf4b9576b44928c2e68dd72 |
| native-runtime-r19/observation-sources.json | 5ff78cdeba55ffcd435c527a46e6e830f31c819fb6a2970a5b738043851ade70 |
| native-capacity-loss-r19.json | a36556eab6ad21d46a919e2d7fbf6a2ac9893da57315278ebfb4fb5295a20d18 |
| native-capacity-after-r19/check.json | 52aa40b226b07940475212f6d60386e3dc3d44bdb6b2859953f5b10057bea1f1 |
| native-capacity-fix-audit-r19.json | af78a4d7f44e3e5db90cfddc8f5c12920bf169cda9f6e1122e59470ef45f1375 |
| native-live-gui-r19/check.json | 8bde15c22b070fa7c599944b2d56bd584d1717d7b5f048ce274ffa30e39aa387 |
| native-live-replays-r19/check.json | 38b9dfa5aa93f266d9e6737a4a0740a59882a857531d20e240e5c7a34707d780 |
| check-language-capacity-before-r19.py | 583025a674875812f3a6b3a16399dfe99c621628802ab1e57620f56339128441 |
| check-language-capacity-after-r19.py | c58dac1f5d058e2a13524cd4c2b4058de1f57e9da191c8e10d4eb95eda4e2a5b |

重生沿前節--with-rebuild組裝；停留驗證用--fontless --transactions --idle-until 900000000，
現場切換沿[五語探針](../../tools/probe_language_live_gui.py)與[四側重播](../../tools/check_language_live_replay.py)。
沿用Go1.26.7／Ebiten2.9.9與Python3.11.2／Pillow9.4的既有映像，唯讀原版、
使用者UID、無網路及資源上限不變。正式前端及dosgolem未修改。
其他固定欄正常路徑、完整生命週期、存讀檔與正式整包接線仍待驗，規格維持DRAFT。
不增加shown、完整五語、HD或發行信用，原文快照、字型、畫面、WAV及存檔只留workplace。

## 正常存檔生命週期抽樣契約

DRAFT：沿既有五語GUI正常讀入COLONY09.SAV、進城及返回世界後，
由原版GAME選單開啟Save Game，不注入座標以外的遊戲狀態。
在存檔插槽、成功通知及返回世界各作五語切換，核對暫停原版狀態、
英文原版像素、四語當次來源及安全區。完成原版COLONY00.SAV寫入後正常返回世界。
此初始狀態選槽後直接保存，沒有描述輸入頁；成功判定須使用當次可見原文，
不能沿用已關閉對話的診斷文字。
初始COLONY09.SAV保持不變，新存檔只寫入本次私用目錄。
以實際GUI輸入四側重播，核對完整原版狀態、RAM、VGA、DAC、WAV及兩份存檔。
此切片不代替新行程讀回新存檔、其他遮擋／重畫或正式接線驗收。

## 新行程讀回契約

DRAFT：先核對上一輪正常存檔GUI、四側重播及新存檔指紋，
把兩份已驗存檔與當時保存的顯示設定複製到新的私用輸出，再啟動獨立行程。
原版從主選單開啟Load Game，選第一個COLONY00.SAV插槽。
以當次可見GAME.TXT:0x00000854來源判定成功，關閉通知後要求該來源撤銷。
主選單、讀檔插槽、成功通知、載入後世界及進城各作五語切換，再正常返回世界與關窗。
實際輸入另作四側重播，從同樣兩份存檔開始；完整原版狀態、RAM、VGA、DAC、WAV及存檔須相同。
本次只讀回已正常寫入的存檔，不改存檔內容或原版狀態，不把原始診斷殘留當成可見文字。

## 2026-10-12：正常存檔五語GUI與撤銷收據

confirmed，限既有初始COLONY09.SAV的本次正常路徑：沿已驗r19二進位，
追加--save-cycle，主選單、世界、殖民地、存檔插槽、成功通知及存檔後世界共30組五語切換通過。
35筆實際DOS輸入四側重播至93600000步，CPU、完整RAM、VGA、DAC、WAV及兩份存檔全同。
原版正常產生COLONY00.SAV，SHA-256為9fce2ddeebc0298544ddf06b9ed713e23d51e871b85190f7d4a6e19e34d84def，
初始COLONY09.SAV未變。即時終點與GUI逐像素相同，即時／觀測模式的五語停止重建與交易全同。
120筆設定事件中的原版狀態保持暫停；英文等於原版，四語差異只在當次安全區。
已目視日文成功通知與韓文返回世界，成功通知關閉後未留下舊覆蓋。

初次探針把另一條新局路徑的描述輸入階段套到本次已載入存檔，
實際選槽後已直接保存；額外Enter導致返回檢查失敗。第二次可見性檢查誤讀對話收據
不存在的source欄位；原版已正常存檔，但檢查器未認出成功通知。
回查顯示語意隔離契約、實際對話收據及既有SAVEGOOD來源後，改驗當次可見
GAME.TXT:0x000007B9與新檔案，通知關閉後要求該來源不再顯示。
兩次失敗輸出均保留，沒有修改原版、產品程式或放寬安全區及原版狀態比較。
新GUI及重播各用新的r19-c輸出，不覆寫r19及前兩次證據。

本機根目錄仍為language-resources-20261011，完整指紋如下：

| 收據 | SHA-256 |
| --- | --- |
| native-live-save-gui-r19-c/check.json | 3a128128754234d2e6a0874900a13c96a65a542312c9b4e22c0cebd1ec252cb5 |
| native-live-save-gui-r19-c/gui.inputs.json | 983215db907ac1c91c4da8f92e1120dc33bd4230a1297bfbcdc755fa1e985c32 |
| native-live-save-replays-r19-c/check.json | 402843ce73c805319103a4a709772f17a715697ede4c5ed8233b0063603234a3 |
| probe-language-live-save-gui-r19-c.py | 9cc328c354bf63ce1721b79c51e2fa649a832b9639c7dfa1b38cfa664a1178e9 |
| check-language-live-save-replay-r19-c.py | 98653758e7ba48e16ea923c4492a0ea554fa9cf908d8efd2f267a1620de68d56 |

原型入口仍為[五語GUI探針](../../tools/probe_language_live_gui.py)及[四側重播檢查器](../../tools/check_language_live_replay.py)。
GUI增加--save-cycle；重播沿該GUI的實際輸入，仍從相同初始COLONY09.SAV開始，
由原版自行寫入COLONY00.SAV。535Go及go vet沿用本批未改的r19二進位證據。
新行程讀回新存檔、其餘畫面、完整來源生命週期與正式接線仍待驗，規格維持DRAFT。
不增加shown、完整五語、HD或發行信用；原版、畫面、音訊及存檔只留workplace。

## 2026-10-12：新行程讀回與清單缺口

confirmed，限本次正常路徑：先核對r19-c正常存檔GUI與四側重播，
將原版寫出的COLONY00.SAV、初始COLONY09.SAV及當時保存的設定複製到新目錄。
獨立行程經原版主選單讀回COLONY00.SAV，主選單、讀檔插槽、成功通知、
載入後世界及殖民地共25組五語切換通過；成功通知關閉後來源撤銷。
23筆實際輸入四側重播至46000000步，CPU、完整RAM、VGA、DAC、WAV及兩份存檔全同。
即時終點與GUI逐像素相同，即時及觀測模式的五語停止重建與交易相同。
100筆設定事件中的原版狀態保持暫停，英文等於原版，四語差異只在安全區。
已目視日文讀檔通知及韓文殖民地；535Go及go vet沿用未改的r19二進位證據。

初次進城沿用舊初始存檔已有選取的假設，第一次點擊只選中了船。
第二次改點相鄰格仍停在世界畫面；回查原始正常輸入、原版畫面及側欄後，
確認新讀檔需先正常選船，再按原位置進城。前兩次失敗保留，未改原版或產品程式。
檢查器以當次原文來源鍵GAME.TXT:0x00000854判定通知，沒有使用殘留dialog_text。

同時確認清單仍有接線缺口，不能由25組切換宣稱整頁完成。
原版在25080000及25245000步各輸出162個字元，形成十列存檔描述及空槽。
來源是dosgolem 20bit線性RAM 0x2AA62；此數值只定位本次觀測，不能單獨識別一般清單語意。
原始字格、色號與列順序已保存，無陰影；每字實際墨跡頂端及高度不同，不能假設全域5px。
日文讀檔清單當次只重建標題GAME.TXT:0x00000826與兩個數字6，完整清單因line-no-template保留原文。
下一步處理清單列與輸入欄的來源身份、逐列字級／基線、保留英數Noto及背景守門，
不能只按英文形狀、譯文字串或這個RAM基址猜套。

| 正式接線閘門 | 本次核對結果 |
| --- | --- |
| 四語字形、64固定欄及整包候選 | 既有量測、152組字級及67資源載入證據保留；不因此認定動態清單與輸入欄已完成。 |
| 完整交易及失敗保留 | 既有五語準備、取消、保存失敗與反例證據保留；原版完整狀態不受交換影響。 |
| 原文觀測重建目前畫面 | 主選單、世界、殖民地、存讀檔通知及既有長文抽樣通過；十列動態清單尚未重建，仍未滿足完整欄位契約。 |
| 正式後端及驗收 | 仍待READY審查與實作；本次是隔離副本的讀回證據，沒有正式五語或HD完成信用。 |

本機根目錄仍為language-resources-20261011，完整指紋如下：

| 收據 | SHA-256 |
| --- | --- |
| native-live-reload-gui-r19-c/check.json | ff495c61e31018ceafa2e9f981cd7cd49a445858fc5b939290e3607158b7c9a5 |
| native-live-reload-gui-r19-c/gui.inputs.json | 77768d050d811d2fd11d71af823a6012cd7b28010768ff4252d82b9ff92c94b1 |
| native-live-reload-replays-r19-c/check.json | 5be644f7888162d6191b2962b0d4cc030219010f07a098dfee40f1ec389c242c |
| probe-language-live-reload-gui-r19-c.py | 938ddc40e5a0582937d109dc5e8135ef930cd839fd9fcb12cca0a28a3049ae51 |
| check-language-live-reload-replay-r19-c.py | 2d737d9d180c27ffc35f6b766ea501e6a7d9a99fb97d763c4b7a44c45c1a4938 |
| native-reload-slot-gap-r19-c.json | 8d8077b618b367957b973cbd79b6b4827dcc258759076f933374e44d7ece5c28 |

重生沿[五語GUI探針](../../tools/probe_language_live_gui.py)的--reload-save與--reload-proof，
分別指定前批正常存檔GUI與四側check.json，再沿[重播檢查器](../../tools/check_language_live_replay.py)
從相同兩份存檔重播實際輸入。原版及研究來源唯讀，輸出仍只留workplace。
新行程使用前次保存的繁中設定；本節未聲稱所有語言的啟動偏好均已正常重開抽驗。
規格保持DRAFT，不增加shown；清單列、輸入欄、其餘生命週期及正式接線接續處理。

## 2026-10-12：清單回退根因與隔離修正契約

前節依終點佇列定位到兩次重印。本次短重播補正：首份十列清單早在22440000步已保存，
162字元的來源為20bit線性RAM 0x2A9FA；它能經既有插槽回呼完成四語翻譯。
首份來源在較晚終點已被回收，不能從終點匯出反推首屏沒有觀測。
診斷副本只增加記錄，原版輸入取已驗GUI的前綴，沒有修改遊戲或正式來源。
中間證據位於language-resources-20261011的native-slot-trace-r20、-b及-c，
對應隔離來源為native-slot-trace-runtime-r20、-b及-c；各批保留自己的命令與輸出。

confirmed，限本次正常讀檔清單：

- 首份清單的標題有效，插槽上下文為真；四語均選21px，安全區[68,74,254,137]。
- 實際VGA與邏輯畫布在最後一列y134有十個墨點不同，完整安全區守門拒絕繪製。
  四語Noto的21px實際墨跡都伸到該列，不能直接忽略差異或裁切字模。
- 25080000及25245000步的反白重印已有完整十列來源，但舊清單失效。
  重建器因目前清單已expired而失去插槽上下文，轉入一般line-no-template回退。
- 清單已收尾；先前懷疑的未完成印字段落不是本次根因。十點差異的原版硬體成因仍未知。

以下只授權DRAFT隔離原型驗證，不改正式前端及原版資料：

1. 舊插槽清單失效時，若前一個已驗來源標題仍active、完整畫布快照相同，
   且新來源為不與標題重疊的完整8／10列，可重新使用該標題的插槽回呼。
   其他標題、列數、未知描述或被改寫標題保持回退，不依RAM基址猜清單。
2. 完整安全區VGA守門不符時，只對已識別的插槽清單量測較小的既有Noto候選。
   文字仍由原版字格、cap高度與行距排版，不改原文、列順序或玩家姓名。
3. 覆蓋矩形取實際候選墨跡與原版可見墨跡的聯集。每個原版非空字格須仍有可見墨跡；
   缺失的原版墨點只能位於覆蓋矩形底緣之外。矩形內仍要求完整畫布／VGA相同。
   任一新字模伸入差異區、內部遮擋、整個字格不可見或缺字時，整份清單回原文。
4. 字模與還原操作都限定在已核對矩形，矩形外逐像素保留原版；不裁切候選文字，
   不放寬矩形內守門，不把原版差異點清除成背景。實際字級及矩形另記收據。

驗證須含本次原始字格與四語實際Noto、反白重印、失效標題、內部遮擋、缺字及過長描述。
再用新正常GUI及相同輸入四側重播核對完整原版狀態、畫面、安全區、WAV與存檔。
只有量測可行與程式測試通過仍不足以升READY或宣稱清單已正式完成。

## 2026-10-12：r21插槽清單隔離驗證

回查路由仍命中文化顯示隔離，沿同一入口及既有插槽來源契約。
隔離重建器依前節DRAFT修正標題上下文與底緣量測；正式來源及dosgolem未改。
551項Go、go vet及建置通過，零skip。新增反例涵蓋其他／失效／改寫標題、
未完成來源、錯列數、標題重疊、內部遮擋、不可見字格及候選墨跡伸入差異列。

| 正常GUI | 五語切換 | 實際DOS輸入／終點 | 清單的四語Noto |
| --- | --- | --- | --- |
| 新行程讀回前批原版新存檔 | 25組 | 23筆／44200000步 | 十列各18px，覆蓋區[69,74,252,134]；十個底緣差異點留在區外。 |
| 正常進城、返回世界及存檔 | 30組 | 35筆／92200000步 | 八列各21px，安全區[71,74,101,138]，沒有使用底緣縮排。 |

兩批各自四側重播通過，CPU、完整RAM、VGA、DAC、WAV及存檔全同。
兩個即時重播終點各與其GUI逐像素相同；即時／觀測模式的五語停止重建與交易全同。
220筆設定事件保持原版暫停；英文等於原版，四語差異只在記錄的實際覆蓋區。
GUI探針現在要求四語存讀檔清單實際重建，不能只靠選項切換通過。
讀回來源的舊二進位指紋改與其原有四側證明綁定，允許新顯示版本讀同一已驗存檔；
來源GUI、輸入、狀態及兩份存檔的原有檢查保留。

本次原版字格的獨立四語量測確認18px完整保留8542／8346／8860／7416個非零字模點，
沒有靠裁切Noto字形通過。缺較小候選、未知描述及過長譯文均回原文，原版bytes不變。
該量測自行建立標題上下文，只證明排版；正常來源身份由上表GUI及四側重播供證。
收據的native_clipped_pixels只計覆蓋區外的底緣差異點，不聲稱已解出硬體成因。
已目視日文讀檔及韓文存檔首屏。

本機收據仍以language-resources-20261011為根：

| 收據 | SHA-256 |
| --- | --- |
| native-rebuilder-r21 | 39f84aa8a6b942c3a59a8b1e396365ed5f8fc0a6e4b7f510ce7666bab03e819b |
| native-tests-r21.jsonl | 29d10adb7b12f33b20272f9c568de58e679fb321685657fc5ca1cfc3c8a0e76a |
| native-runtime-r21/observation-sources.json | b6cf2cc79ec932e7a18d7eab87a25c3658b112f796147e9fa305f38d16cafc2d |
| native-live-reload-gui-r21/check.json | 93a5d534231caaa49e58c1723cdf2ce08325f81ea76fbef998b5bfac5ed188aa |
| native-live-reload-gui-r21/gui.inputs.json | f5e1701b6b38880f4229f9922f3542891d7333f2e5b081f069f95a7bea85ea65 |
| native-live-reload-replays-r21/check.json | 87b9523235b7309ab6f1db7d4ab233e908c9cf3bd9cc5bbdee2fa8c6e3286fdd |
| native-live-save-gui-r21/check.json | a83279c70ea17466e5d6966aef2c65f767323cf09f59460b86cef1314dbf55ab |
| native-live-save-gui-r21/gui.inputs.json | 4867fec8bbb69307b83003524951e48cca4125866e53a383b6fb7c17f981b628 |
| native-live-save-replays-r21/check.json | 81c452635e8724f95d40b7ac818fa55ad321009646cec48cc66d037b2fcc7864 |
| native-slot-real-fit-r21.json | 9193387fdc34f1711a44ad2e54d57bbca6affadc36b72d7c7445dfa641abf002 |
| probe-language-live-reload-gui-r21.py／probe-language-live-save-gui-r21.py | 45945a91df897b8b2b5fc60fdcacd3b95eb3d4a5e51b0f2ff8bb71de8fd1b6f2 |
| check-language-live-reload-replay-r21.py／check-language-live-save-replay-r21.py | 2d737d9d180c27ffc35f6b766ea501e6a7d9a99fb97d763c4b7a44c45c1a4938 |

重生沿前節的GUI、重播及隔離組裝入口，採本節r21來源；原版、字型、存檔與畫面只留workplace。
目前完成本次8／10列清單隔離修正，沒有把未知原版行為填入正式程式。
規格060及057仍DRAFT；下一個明確缺口是輸入欄的逐欄Noto與來源守門，再進正式接線審查。

## 2026-10-12：輸入欄字格觀測契約（DRAFT）

正常城市改名基準位於本節既有本機根目錄的`native-live-input-baseline-gui-r21/`。
35次五語切換通過，29筆實際DOS輸入至87400000步；`check.json`的SHA-256為
`57486eee45b734fc89ab044bf4e285e4ac270c10e4195b271b8ac6a6e02d5a23`。
原版重印`Name: Jamestown_`時，未變更的標籤沒有再次寫入；墨跡不能單獨證明完整字格。

隔離觀測器可在既有0D21:00C6原文字元讀取後記錄ES:DI，不改原版記憶體或正式來源。
逐字與零結尾配對各記錄字格起點、終點及是否取得；連續字串不猜補終點。
每次只保留一份待完成段落，最多4096字格，完成時複製到不可變觀測並計入容量。
來源去重必須比較這些定位；停用觀測不得配置或改動資料。
本節只授權隔離取證，尚未授權輸入欄正式覆蓋；字級、安全區及游標仍待實測。

`native-input-cells-r22/`以同一條29筆輸入重播至87400000步，完整CPU／RAM／VGA／DAC及
WAV與基準相同。ES均為2CAE；標籤從(62,103)開始，姓名從(95,103)開始。
原值的游標字格為[146,103,153,119]；刪字後起點為(141,103)，重打後回到(146,103)。
姓名可見墨跡為[95,103,145,112]，最大單字墨跡高度8，底線墨跡[146,109,152,111]。
原版`Name: `後有3像素額外間距，不能把標籤終點當姓名起點。

隔離覆蓋只接受仍存活的GAME.TXT:0x00000F5C改名提示、既定標籤及上述行起點。
姓名與末尾游標須各有完整逐字ES:DI配對，字格連續、在同一列且墨跡位於字格內。
姓名只用可列印ASCII原值逐字繪製，不解析譯文標記；空值、缺字、未知位置或不適合時回原文。
安全區由姓名起點、實際游標起點及該列墨跡計算，不含游標字格。
Noto候選逐級量測，墨跡不超過原版8像素高度放大四倍，另留1原版像素給陰影及游標間距。
基線以原版此欄的111像素位置及Noto大寫H的墨跡下緣對齊，大小寫沿同一基線；
保留原版首寫前背景，陰影沿原版樣式。
整個安全區須與來源畫布及當前VGA一致，取消或離開提示後撤銷。此契約仍只供DRAFT隔離驗證。
每個非空姓名字元須仍有原版主色墨跡，已被其他寫入者抹除的文字不得因切換重新出現。
不增加shown、完整五語、HD或發行信用。

## 2026-10-12：r23d改名姓名隔離驗證

完整558項Go、go vet及建置通過，零skip。四地區實際Noto另驗字格未知、錯ES、
上下文過期、背景改寫、缺字模及來源已抹除的回退；空格、大小寫及大括號保持原值。
結構fixture只證明守門及排版，不當作原版行為證據。

正常GUI沿城市標題開啟改名，刪除末字、重打及取消，七個畫面共35組五語切換通過。
四語姓名各選30px，原值Jamestown安全區[94,102,146,113]，刪字後Jamestow為
[94,102,141,113]，重打恢復，取消後撤銷。英文逐像素保留原版。
候選逐欄量測，30px只適用此欄，不外推其他輸入欄。

30筆實際DOS輸入重播至89000000步，即時／只觀測／正式／原版控制四側的完整CPU、
RAM、VGA、DAC、WAV及存檔全同；即時終點與本次GUI逐像素相同。
即時及只觀測五語重建、暫停交易也全同。沒有修改原版資料、dosgolem、正式前端或譯文。

r23c首輪在重打階段觸及2GiB容器上限，被Docker OOM終止；保留該次畫面及程序紀錄。
原版文字與游標已驗的畫面沒有因此作完成收據。設定GOMEMLIMIT=1200MiB後，
相同2GiB映像及操作乾淨重跑35組通過；r23d再加入已抹除來源守門，重跑35組及四側通過，
該GUI容器峰值1822228480 bytes。重生須沿用此有界回收環境，不以增加上限掩蓋失敗。

重生先用[隔離組裝器](../../tools/build_language_observation_probe.py)的--with-rebuild，
採上述r23d來源及既有Go環境；GUI由[正常視窗探針](../../tools/probe_language_live_gui.py)
追加--input-edit，之後用[四側檢查器](../../tools/check_language_live_replay.py)重播該GUI收據。
原版、字型、存檔及圖片維持本機；基準與候選位於本規格既有語言資源根目錄。

| 本機檔案 | SHA-256 |
|---|---|
| native-rebuilder-r22 | 266563961a5175462c100ccf5aadb914eae7347b9049256838d6b37ddbfdd9a3 |
| native-runtime-r22/observation-sources.json | 18af209d3b335957be7885e8bcf35064a00e065b931ba5e97949a593e92d3cc7 |
| native-input-cells-r22/check.json | a9a96243fda27f4a67ced752425b4ea5e26235a8afd4752ce6ea72c108b62ba1 |
| native-rebuilder-r23d | 9912aa56f19fbe86e960789b544753c7b19197e9b267f5d0c363a668a1b0959a |
| native-runtime-r23d/observation-sources.json | 973768b0f6323b93273f1007193e8415143d3c6da1bd6f9435ab9604cb6989d8 |
| native-tests-r23d-full.jsonl | ff9437f2457ef18697bc4b84b2a7788bc4cc6b7edafeffc8809d8a411fef2acb |
| native-live-input-gui-r23d/check.json | 7d7b3707db4994c8340723f4bfd3fd252abe7d0dbf4589330c19dbebba830c98 |
| native-live-input-gui-r23d/gui.inputs.json | 13f8c12a8281496454fb77c6acc03b3259a1508bfa078f7042778baab8fe190d |
| native-live-input-gui-r23d/resource.json | 4425b76a98b0b80b2d624e65a00dc7969d080771be943a76aedb0e545490c63a |
| native-live-input-replays-r23d/check.json | fbc3682d451f766b2fc2bcff03f087f2d93ae2a2e9af4afcc96ef0720c1d0eb4 |
| probe-language-live-input-gui-r23d.py | 3b3631781d48bbb04649725458e4fd206f6877a5c83931f3040123b2d7e5fc68 |
| check-language-live-input-replay-r23d.py | 7ec3fad00a6e3b8658c18b373cc59f6a43e87299b5c1004309edf0048847beb9 |

規格060及057仍DRAFT。改名姓名切片已驗；其他輸入欄與未知樣式維持原文回退，正式接線另審查。

收尾核對入口為本機`native-input-final-audit-r23d.py`，SHA-256為`19f606fd22e2b67a4dfe331ab2d927c6dcaacc007d8eb34782fadbfe3eaa3eac`。

本機收尾總收據`native-input-final-audit-r23d.json`的SHA-256為`4a2519fd42c6010c9362c2b5c6a48a45e86790e03ae37bc55d652ce91f70ee11`；
35GUI、140筆暫停事件、12組游標逐像素及四側重播核對通過。

## 2026-10-12：可攜可信索引（DRAFT）

正式接線前先移除載入器對`/repo/tools/language-catalogs.json`及候選包旁研究清冊的依賴。
[索引產生器](../../tools/build_language_resource_index.py)只接受本規格已綁定的64欄清冊指紋，
將來源鍵、檔名、安全區、陰影及TSV歸屬產生為
[編譯索引](../../tools/language_resource_index.go)。不複製原版像素、原文或譯文。
13表的既有[公開清冊](../../tools/language-catalogs.json)以Go內嵌，並核對編譯時指紋。

語言包仍使用原manifest及資源格式。預期值來自編譯索引，不由候選包自稱；
原版檔案、字型、授權、文本及字模的守門保持原樣。索引每次回傳獨立資料，不能由候選修改。
隔離組裝器連結索引與既有載入反例測試，並保存全部來源指紋。
須在沒有`/repo`與研究清冊的容器中載入相同五語包，再核對正常GUI、存讀檔、
來源失效及原版完整狀態；未通過前仍DRAFT，不進正式前端。
重生為`tools/build_language_resource_index.py --fields <既有語言資源根>/fields.json`；
加`--check`只核對。既有語言資源根由本規格前節列出，輸入指紋不符即停止。


## 2026-10-12：r24可信索引與正常存檔驗證

編譯索引與已驗64欄清冊完全一致。13表清冊內嵌後，執行期不讀取儲存庫清冊或
候選包旁的fields.json；語言包格式、譯稿、字模與原版資料均未改。
隔離組裝器新增連結原有25個載入反例，來源綁定由10份增至14份。

- 完整592Go零skip、go vet及建置通過。
- 無/repo及研究清冊的Go容器通過34項實際載入、反例及預期值獨立持有檢查。
- 實際程式不提供研究來源，重播r23d的30筆輸入至89000000步；完整原版狀態、
  原文觀測檔、五語重建RGBA、WAV及存檔與基準相同。
- 新正常GUI含改名、刪字、重打、取消及存檔，共50組五語切換、200筆暫停事件通過。
  42筆實際DOS輸入重播至104200000步，四側CPU、完整RAM、VGA、DAC、WAV及兩份存檔全同。
  新COLONY00.SAV由原版正常寫入，SHA-256仍為9fce2ddeebc0298544ddf06b9ed713e23d51e871b85190f7d4a6e19e34d84def。
- 獨立檢查四語256固定欄的全文、英數、字級、基線、陰影及完整墨跡；實際候選的256份字模
  與已驗產物逐位元組相同。來源及字模權利邊界保持原樣。

可攜重播首試只停在前置檢查：驗證映像內建空/repo工作目錄。
核對該目錄無來源檔後，改以來源不可取得作判準；沒有放入研究清冊或修改產品條件。
Go容器的/repo確實不存在。相同程式的正常重播隨後通過，兩種環境於收據分別記錄。

重生以本節14份來源組裝--with-rebuild，索引先以產生器--check核對。
無研究路徑測試只掛模組、候選包、原版、隔離dosgolem及快取；不掛專案根目錄。
實際程式重播另外唯讀掛既有啟動模板、舊字模包、GUI輸入及原版基準，無儲存庫來源。
正常GUI用既有探針追加--input-edit --save-cycle，四側檢查器重播同一輸入。
Go回收沿GOMEMLIMIT=1200MiB，GUI仍限2GiB；峰值1832480768 bytes。

| 本機檔案（沿既有語言資源根） | SHA-256 |
|---|---|
| native-rebuilder-r24 | 35c0179628b7e2169bd41c0c8f4914e6d99e6cd31af5c4e4f9a3a1db3108e413 |
| native-runtime-r24/observation-sources.json | 829342c7ecc0730b47fc9b15d54d6f53c66f9320b30ca00805bdaf5bf63432ab |
| native-tests-r24-full.jsonl | a10b87034549fdec00a28244cf1497a7c320ad37e6535c7bafc8f7e659d48e8d |
| native-index-portable-r24/check.json | bf6949d06ff6acf912c98af661ac6110e64bf9b877fc332f31ae1b897585fe03 |
| native-index-portable-r24/replay/check.json | 464ab823ddb1b0f9a110b025c9b31c536beead005576c3f2ed7ca63b090a3815 |
| native-index-portable-r24/fixed-current-check.json | 5c94e58184292e187ff7401adf3afaf977c20733b70b6ba34df0916090e4afa9 |
| native-live-portable-save-gui-r24/check.json | 411a8d4543e9fd4f1ae2c6be6c1a4f70dd4c84b032cd56278b0e59ddbe16f561 |
| native-live-portable-save-gui-r24/gui.inputs.json | 693f7abd2c9de99d297cf976ddeed800ccc9c12ce323f5fe1bf454ef575bdc45 |
| native-live-portable-save-gui-r24/resource.json | 29d892cc522853ac21f599cd65a4930ec01623c9cd9944d2ea627ee14a647647 |
| native-live-portable-save-replays-r24/check.json | 01832d5f42d5e95d458468ccaca91e93879ea1fcb57e01498d12fe3832de60ea |
| probe-language-live-portable-save-gui-r24.py | 3b3631781d48bbb04649725458e4fd206f6877a5c83931f3040123b2d7e5fc68 |
| check-language-live-portable-save-replay-r24.py | 7ec3fad00a6e3b8658c18b373cc59f6a43e87299b5c1004309edf0048847beb9 |


## 2026-10-12：READY證據審查

| 原有閘門 | 已查驗證據與界線 |
|---|---|
| 四語逐欄、最長文案與英數 | 256固定欄獨立全文與完整墨跡檢查通過，與當前候選字模全同。152組完整字格、95 ASCII及3動態圖集沿規格057與本規格既有原版逐欄契約；清單及改名姓名已有正常GUI量測。未驗欄位不強制覆蓋。 |
| 完整準備與失敗原子性 | 當前592項包含實際五語載入、25種錯誤資源及既有提交、取消、保存失敗回退；34項另在無研究來源環境通過。準備不持有DOS機器或修改生效資料。 |
| 從原文重建當前畫面 | 原文與字模獨立的缺舊資源、長時間容量、缺譯、過長、畫面改寫、清單重印及輸入取消證據保留；可攜正常重播的原文觀測與五語RGBA全同。未知來源及被抹除內容回原文，不由舊譯文猜補。 |
| 正常玩家路徑與正式驗收 | 既有存檔、新行程讀回與改名證據，加本次50GUI／四側正常存檔驗證，足以接正式後端。正式接線後仍須重跑四語與英文GUI、存讀檔及完整原版同狀態驗收，未達CONFORMED。 |

本規格升READY。授權範圍為既定五語整包準備與交換、獨立原文觀測及已驗覆蓋契約。
不變更原版行為、檔案、資料格式、字型決定或顯示設定操作。
未驗欄位、未知樣式及過長譯文依既定契約回原文並記錄，仍是目標186未完成範圍。
正式五語後端、剩餘顯示覆蓋與HD尚未完成，不以READY狀態增加shown或宣稱整個目標完成。

本機收尾核對入口`native-index-final-audit-r24.py`的SHA-256為`70a3697f6da71a36b8eda85885bb98d759f5ae5a11817e8cfc1c41105ae66a0f`。

收尾總收據`native-index-final-audit-r24.json`的SHA-256為`57bc9158eedadedcfaef86777e194c2f785bdf31a2800e6bf1b48ce70c0114cf`，
14來源、592Go、50GUI、四側重播與可攜索引核對通過。

## 2026-10-12：正式五語後端接線與驗收

正式入口為[前端組裝器](../../tools/build_window_prototype.py)。
預設連結已驗的[共用接線](../../tools/build_language_observation_probe.py)、
[整包載入器](../../tools/language_bundle_probe.go)、
[重建後端](../../tools/language_rebuild_probe.go)及可信編譯索引。
原版幾何來源live_menu.go保持原指紋；舊量測探針明示--legacy-source，
避免重複接線或把接線變更當成字模幾何變更。

[正式啟動器](../../tools/release/colonization-cht.sh)以--language-bundles指定五語根目錄，
並啟用既有設定列。非英文使用整包Noto，英文直接顯示原版畫布。
內部觀測隨後端啟用；--native-text-diagnostics才匯出原文觀測與五語重建收據。
舊隔離旗標仍供歷史探針使用，不能混用正式資源旗標。
[正式封裝器](../../tools/package_release.py)新增--language-bundles、--ui-font及--ui-license，
核對五語集合、80檔清冊、字型、授權及檔案指紋後收取資源。
每包沿既有schema與kind識別，不改寫已驗譯稿、字模或manifest。
Windows啟動器沿同一份命令轉換；本批只驗參數，不冒稱Windows或macOS實機通過。

正式本機驗收套件在既有語言資源根的formal-bundle-r25。
它由同一封裝函式收取328檔五語／設定列資源及授權，原版資料另唯讀提供。
這是本機驗收中間物；沒有建立交付版本、tag、Release或改動原版。

| 驗收 | 結果 |
|---|---|
| 正式組裝、資源與設定回歸 | 605Go零skip、go vet及建置通過；正式／隔離旗標的12種組合另有測試。 |
| 正式GUI正常存檔 | 50組五語、200筆暫停事件；42筆實際DOS輸入至103000000步，改名刪字、重打、取消、插槽、成功通知及返回世界通過。 |
| 正式GUI新行程讀回 | 25組五語、100筆暫停事件；23筆實際DOS輸入至51200000步，十列讀檔清單、成功通知、返回世界、選船及進城通過。 |
| 原版同狀態 | 兩路各四側重播，完整CPU、RAM、VGA、DAC、WAV及存檔一致；即時與停止重建的五語RGBA一致，英文與原版逐像素相同。 |
| 正式預設無診斷 | 同一42筆輸入不加隔離或診斷旗標，畫面、完整原版狀態、WAV及存檔一致；原文觀測、重建及設定事件匯出不存在。 |
| 封裝拒絕 | 缺檔、錯地區、不合法路徑、錯字型、錯授權及缺語言六項拒絕通過。 |

COLONY00.SAV由原版正常寫入，指紋仍為
9fce2ddeebc0298544ddf06b9ed713e23d51e871b85190f7d4a6e19e34d84def。
新行程讀回沿已驗存檔與保存偏好，沒有透過座標注入或直接入口取代玩家流程。
四語姓名游標、8列存檔清單21px及10列讀檔清單18px沿先前逐欄契約，不外推其他欄位。
兩路GUI仍限2GiB、GOMEMLIMIT=1200MiB，峰值分別1904087040及1791373312 bytes。

重生以正式組裝器預設模式建立模組並建置；字模及譯稿沿既有已驗候選。
[GUI探針](../../tools/probe_language_live_gui.py)新增--formal-launcher，直接執行套件啟動器，
追加--input-edit --save-cycle；通過四側驗證後，以--reload-save及--reload-proof啟動新行程。
[四側檢查器](../../tools/check_language_live_replay.py)同樣指定--formal-launcher；
其他對照沿既有已驗前端及原版控制組。兩側原版輸入、輸出根及存檔彼此隔離。
工具沿Go1.26.7／Ebiten2.9.9及Python3.11.2／Pillow9.4的固定Docker映像，
每次Xvfb都有有界擁有程序與清理trap。

本規格限定CONFORMED於上述整包與原文重建交換契約及已驗欄位。
日文過長地圖譯名、被原版改寫安全區的90% (3)、1、4，以及其他未驗來源與樣式，
仍回原文並記錄。完整五語覆蓋、HD、影片與三平台新版交付仍是目標186的未完成範圍。

| 本機檔案（沿既有語言資源根） | SHA-256 |
|---|---|
| formal-window-r25 | c44241c9e1ac5869b106b6dff833e9f19766521fe6e71e57a803b5b656a500db |
| formal-runtime-r25/observation-sources.json | 3c1a1d3cfa900161b604cae150eba2f545e8a087f10fe8fca8562e60686b9243 |
| formal-tests-r25-full.jsonl | dc8ea9b3ce0d6821bee5415b276c5da2818cbff29bbe67fe5b83fe65fa4d1360 |
| formal-bundle-r25/stage-check.json | 82131ba5a4dbf6edb5ae97de44b8b17e1c6461ec33146e91dd0a0eb07a4bda1b |
| formal-package-rejections-r25.json | c38922880a94ebd6f0dea31f368b06675e00bebb1fbb4522a872f380a9d4467a |
| formal-production-r25/check.json | 7f782398c9cd83d36a50c94870fccb04c339f661039e5672c1cd52850697bde7 |
| formal-save-gui-r25/check.json | 17e73887e78359947de5a53ddec5f247d40725a076f5bbb900185fa5d4c30147 |
| formal-save-gui-r25/gui.inputs.json | 91bbfa7821c6a5db5d1a11dca6611cbdac998da00cd23ed4439e8aacee9bc3f2 |
| formal-save-gui-r25/resource.json | 983659204808a6881902021d2b7305845793a99277d5bdc6fef9290efc89ef89 |
| formal-save-replays-r25/check.json | d883518eb266126d342141f1390f713dbd932e5af265db72d531bc5e6d28daf7 |
| formal-reload-gui-r25/check.json | f2d4abd71966409a2c0cf077cd8bda519f6db220393a147418a30d59cb0a1394 |
| formal-reload-gui-r25/gui.inputs.json | 3015567bd1d683f27df95f7fa8f8cedcf53fee9650c69985978755ff1a0aa1a9 |
| formal-reload-gui-r25/resource.json | a9934f2fa0e2ce88abed6390901df3184b28941d950899f22a24d9458a099511 |
| formal-reload-replays-r25/check.json | 6ca12001ad57fbab8b7b4c506f402e77f55a1406a2eddedda72ab33c5b6f3587 |
| probe-language-formal-save-gui-r25.py | 42ca01a151a77c40a66812054741d87539605a868629187fca6ae14b1956969a |
| check-language-formal-save-replay-r25.py | 4c0ba813868f03ea00f35fa7c7879f36cddb9becee2442e9bbd5914d70b73d68 |
| probe-language-formal-reload-gui-r25.py | 42ca01a151a77c40a66812054741d87539605a868629187fca6ae14b1956969a |
| check-language-formal-reload-replay-r25.py | 4c0ba813868f03ea00f35fa7c7879f36cddb9becee2442e9bbd5914d70b73d68 |
| formal-final-audit-r25.py | 5b653c552d5141e0558a0d97d3fe61fb0e7a0fd86e0b5553ab29e671649b9a95 |

正式接線收尾總收據formal-final-audit-r25.json為83e82c7d9edb30e296566cf4c3ac4683833fde62a40c1a56a15e94818fa79388，
605Go、75GUI、300筆暫停事件、八次重播、12組原版姓名游標與328檔清冊均通過。

## 2026-10-12：Noto英數透明外緣驗收

前述城內90% (3)、1與4的回退已依[規格052最新附記](052-retained-ascii-font.md)
完成正式修正。整包schema、譯稿、圖集、328檔封裝資源與啟動器均不變。
635Go零skip、go vet及新50組五語GUI通過；42筆實際輸入四側重播至103600000步，
完整原版CPU、RAM、VGA、DAC、WAV及存檔一致，離城無殘影，英文原版精確不變。
本輪證據指紋與逐欄字級由規格052保存，原文重建交換契約仍沿本規格。

地圖城名另有原版墨跡外20點背景差異，日文17px只證明私有排版容量；
新增證據與下一閘門見[規格038最新DRAFT](038-string-overlay-draft.md)。
其他未驗來源、HD、影片及三平台新版交付仍未完成。

## 2026-10-12 四語城名接線的限定驗收

依[規格038最新READY與限定CONFORMED](038-string-overlay-draft.md)，
正式Noto世界城名改以完整文案alpha量測，保留原版來源、後畫像素與其他覆蓋守門。
世界及存檔返回世界的完整雙語Jamestown四語採23／23／17／22px；
英文逐像素原版相同。其他來源與樣式沿既有回退，整包格式及載入契約未改。

676Go零skip、go vet、31份Go來源與十四筆組裝綁定通過。
正式入口新50組五語GUI與42筆實際輸入四側重播至113400000步通過；
完整CPU、RAM、VGA、DAC、WAV及存檔全等，進城撤除及返回世界重建正確。
城內十二個既有數值欄位保留。328個語言資源逐檔等於前輪，沒有重烘字模。
本機入口為`language-resources-20261011/map-source-padding-r27/conformance-review.json`，
指紋`7a5769e5810ae966b764b79ba440803cab59af867c07fd9f491ef54af85383a2`。
完整五語覆蓋、HD、影片與新版交付仍未完成，歷史普查及規格058未知差異不改。

## 2026-10-20 R120 士兵教學正文 READY

狀態：READY。DRAFT檢查已核對既有正常輸入、原始文字、完整人物來源與逐欄Noto量測；正式畫面與回退驗證待實作後執行。此項只補GAME.TXT:@TUTORIAL14，不改原版規則、人物動畫、輸入或存檔。

- 已證實來源：GAME.TXT SHA-256為67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，正文位移0x142EF、442bytes及SHA-256 599eb1ee4bdc1aad85f3c75ae92180c453f2c6bf917124a19f24f7be7070f9db。MSS1.SS指紋7b580f7ebda2e03d34ca88c19942f6fd3707d044fceed2f8626e66aac62da6ea，來源1061與完整SS返回／持有權沿規格069 R98。
- 正常GUI5的67筆輸入重播至258000000步，正式6317097c…與僅加診斷匯出的控制程式，CPU、完整RAM、VGA、DAC及步數完全相同。dosgolem為82a14b266e1b5bc904e2d0fe507daf6bea41a013，地址為real-mode 20-bit線性RAM。正文來源暫存位址0x2AC72，完成觀測255750000步；原版畫布0x2CAE0，VGA為0xA0000。
- 已證實原因：完整正文416個字元已收集，後續MSS1覆蓋其中54個字點。4429個不透明人物點與既有原始來源相同。舊整區相同守門因此回原文，沒有缺譯。
- 原版墨跡為[44,89,255,188)，大寫墨跡高9邏輯像素。原文來源安全區為[42,86,261,190)。譯文使用左側[42,86,208,190)，放大後664乘416，距人物矩形左緣210保留2邏輯像素。保留既有dialogMasks的內距、換行與三層字模，依此欄原版36px墨跡上限量測，四地區字型各選30px，並非全域固定字級。
- 四份完整譯文以各地區Noto圖集實測，含陰影及強調的相對墨跡為繁中[5,2,632,156)、簡中[5,2,623,157)、日文[4,2,637,236)、韓文[5,2,649,196)。首行沿既有字模基線排法，墨跡頂端為放大畫布y346；原版首行墨跡頂端y356。全部文字與陰影皆在安全區內，不裁字、不分頁或截斷。任一譯文放不下即保留原文。
- 僅當正式SS追蹤器仍完整持有人物4429點、原生值與色盤相符、Main與VGA除游標外一致，才允許此已知前景的後畫差異。其餘原文來源安全區逐點相同；未知寫入、錯誤來源、未完成人物、色盤不符或未載入HD來源追蹤器時均回原文，不放寬一般對話守門。
- 原文來源安全區仍完整清除已驗文字。人物點保留當前底圖值，譯文字模只繪於左側；原版與HD圖像模式共用來源證明。英文保持原版字形。
- 驗證：四語完整文案與人物不重疊、未知後畫／錯誤來源與色盤回退、正常GUI設定切換及關頁，代表性同輸入原版狀態核對。只授予實際完成範圍，不外推完整五語或全量HD。

本機來源與量測入口位於既有hd-opening-animation-sources-r84工作根的r120-soldier-evidence-r1/gui.soldier-source.json，SHA-256為f918305b821fac28a5679fc739490cfeba674c1313e4c3ba9c1634638c9e33cf。正常輸入與基準狀態見r120-soldier-baseline-r1及規格069 R98的GUI5收據；原版資料維持本機。

R120來源核對補充：印字完成後，正文安全區有427個人物後畫點，其中54個原屬文字墨跡。427點均有完整MSS1來源及原生值證明；native_occluded_pixels只計54個文字點。來源檢查收據為r120-source-overlap-check-r1.json，仍不接受來源以外的改動。

### R120士兵教學正文限定CONFORMED

四語完整正文均以各地區Noto 30px顯示於左側欄，原版與HD兩模式及四語人物游標往返共16張實拍，另2張英文，合計18張事件實拍通過。當次43張實拍的1280乘800遊戲區與X11相同，正常關頁後士兵來源歸零。36個來源、幾何、色盤、VGA及同值未知寫入反例回退；英文單元畫面保持。當次正常輸入的原版控制組與正式GUI之CPU、完整RAM、VGA、DAC及終點相同。

正式aaffdd177b9da1ff1c52f3e34b2f0a34763d58cdcf49ded805a660974c04749e通過建置與go vet，程式提交4fefd3acd8446c0cf18eb771c3765f41b3102cfb。沿用328個語言資源與既有譯稿，沒有新字模或資料格式。HD圖像來源與既有原圖不變。

收據入口為既有hd-opening-animation-sources-r84工作根的r120-display-close-final.json、r120-soldier-gui-final-check-r1.json、r120-soldier-unit-display-r4/check.json及r120-soldier-control-r1/check.json。此限定驗收只補士兵教學欄位；缺少可驗的完整人物來源時仍回原文，未將其他情境、完整五語或全量HD標為完成。

## 2026-10-20 R121 長正文期間的文字觀測保留 DRAFT

R120正常士兵教學的來源收據顯示，原文觀測上限256筆時，只剩255筆同來源單字元及一筆完整416字元段落。仍可見的頂列選單因此沒有來源可重建。來源為R120的f918305b…完整收據、同一合法原版與dosgolem82a14b2，不新增原版內部調查。

候選只改滿載淘汰順序：先沿既有規則回收不可見觀測，再優先回收由同一原版逐字段落涵蓋的多色陰影單字元，最後才沿原有最舊可見來源規則。單色英數、獨立字串、離屏、描邊、熱鍵、貨物變數及未完成來源關係都不得列為重複字元。256筆與32MiB上限保持，原版、語言包及觀測輸出欄位保持，只增加診斷計數。

本候選仍為DRAFT，待同輸入重播確認選單來源與四語畫面恢復、完整段落及原有單色英數來源保持，再審查READY。

R121候選r1同輸入重播的完整原版狀態與R120相同，但選單尚未恢復，僅3次採用優先回收。前端組裝後的原始碼確認字串層先處理同一次0結尾讀取，段落層稍後才更新；因此合法單字元已完成時，段落readPos仍可能是2N-1。候選r2接受這個已確認的回呼階段，但仍須由已完成的單字元來源、同基址、時間、完整字元墨跡、色彩及原版寫入點證明涵蓋關係。這只修正候選判定，不調整兩層回呼順序或原版資料。

R121候選r2已保留完整選單來源，361次可見來源淘汰全部為已證實的段落單字元；原版完整狀態仍相同。顯示仍因sea-safe-changed回退，另有已驗MSS1火槍進入頂列安全區。候選r3只在完整人物來源證明成立、原選單字點仍存活及其餘安全區完全相同時，允許這些已知前景的背景差異；繪字後恢復人物前景原RGBA。選單字模、字級、位置、快捷鍵及原版資料保持，不套用到動態側欄欄位。此新增遮擋分支仍DRAFT，待來源快照、四語畫面及反例驗證。

### R121長正文選單 READY

DRAFT證據審查通過，狀態為READY。來源仍是R120同一合法原版、相同67筆正常GUI輸入與dosgolem82a14b2；VICEROY／GAME.TXT／MSS1及字型指紋沿R120與規格069。原版地址為real-mode 20-bit線性RAM，主畫布0x2CAE0、VGA 0xA0000，不新增原版行為或資料格式。

- 原型r3的完整CPU、RAM、VGA與DAC等於R120基準8a046c4c…，四語頂列選單與正文均顯示。原觀測仍256筆、成本18590682 bytes，低於32MiB；361次可見淘汰均為同段落已涵蓋的陰影單字元。先回收不可見資料、再回收這些字元，其他情況沿原有最舊可見來源規則。
- 重複字元須為同原版基址與時間範圍、完整單字元來源、相同墨跡及多色色彩，寫入點全部屬原段落；段落長10至4096字元，沒有連續字串拼接或前綴。字串回呼先於段落回呼，允許段落計數2N-1或2N。單色英數、離屏、描邊、熱鍵、貨物變數及不符合來源的字元維持原規則。實作入口為tools/language_observations.go的nativeDialogCoversShadowCharacter及nativeJournal.add。
- 頂列原字點[13,1,306,6)保持完整可見；既有四語選單字模、12個快捷鍵／文案片段的22px、基線與安全區[13,0,306,8)保持。原版SS人物在seaBarRect[0,0,320,8)內佔10個點，其中7個背景點與舊選單快照不同。
- 僅完整MSS1來源4429點的原生值、來源持有權及色盤都成立時，允許此靜態頂列的已知人物背景差異。其他頂列點仍完全相同，原字點可見性與VGA守門保持。只複製已驗來源快照，繪字後恢復那10個前景點的原RGBA，不寫回原版。此分支不授權動態側欄或未知後畫。
- 來源與邊界、既有士兵正文及選單前景測試共108個通過項，無skip；另有原觀測來源21個主測試／60個具名通過項。選單四語的32個未知背景、VGA、色盤、同值未知寫入、原字改動、錯層及錯件反例均回退；完整人物70864個放大RGBA點保持。
- 接續正式建置、正常GUI的四語原版／HD與游標抽樣、關頁後繁中選單及同輸入原版控制組，完成後才授予限定CONFORMED。不新增完整五語或全量HD聲明。

Ready收據為既有hd-opening-animation-sources-r84工作根的r121-ready-review-r1.json。選單原始來源快照gui.sea-bar-sources.json的SHA-256為13f2b60a2414e96cd965d72bbf281de14aff5915cd650b0e95e9b740ef77f4da，只留本機。顯示／語意隔離依Codex對應入口；所有翻譯仍由既有TSV與語言包載入。

### R121長正文選單限定CONFORMED

四語頂列選單與完整教學正文在正常士兵頁同時顯示，原版／HD與四語游標共16張非英文事件實拍，另2張英文。當次44張1280乘800遊戲區與X11相同，正常關頁後選單保持、教學正文撤除且人物來源1061歸零。四語選單沿原22px及12個片段，10個人物點與7個背景差異只在完整來源證明下處理，正文沿R120的30px欄位。

正式23項測試、138個含子項通過且零skip，包含原生觀測既有測試、容量／優先順序及配對反例，並含正文36個、選單32個拒絕案例。正式程式SHA-256為cb5e807dc920d486e24241f4a2d48b0fae92f12d22de383c3992ed66be7f38d2，通過建置與go vet，程式提交b40a645f81027b4cba5751d7cf9317b9af580574。當次78筆正常GUI輸入重播至285600000步，完整CPU、RAM、VGA與DAC等於原版控制組。

收據位於既有hd-opening-animation-sources-r84工作根的r121-display-close-final.json、r121-shadow-menu-gui-final-check-r1.json、r121-formal-unit-display-r1及r121-shadow-menu-control-r1/check.json。原型來源與原始SS fixture只留本機。只增加此靜態頂列在長篇教學中的來源保留；人物後方四個動態狀態欄仍回原文，未擴及部分遮擋的數值欄位。328個語言資源、圖像清冊與HD來源信用保持；完整五語、全量HD、音訊、存檔及新版交付不增加聲明。

## 2026-10-20 R122 人物前景後方的四語狀態欄 DRAFT

正常R121士兵教學實拍顯示，頂列與正文已為四語，右側Gold／Tax、Locat、Moves及Spring四行仍因人物後畫而保留英文。來源與原始指紋沿R120／R121，這是既有前端觀測及畫面接續，不開新原版內部調查。

候選沿規格032與本規格的既有逐行譯文、Noto字模、原版墨跡及選字級規則，只補顯示前景合成。僅接受正式來源1060至1065的完整MSS人物，須有完整原版解碼返回、唯一可證的目的位置、全部不透明點的持有權、原生值、色盤及Main／VGA一致性。任何未知後畫、同值未知寫入、錯色盤或缺件仍回原文。原版及HD兩種圖像模式皆依同一來源證明。

原生海上列須有完整、可翻譯的原文觀測。人物以外的原字點與計算後安全區逐點相同；只允許已驗人物點覆蓋原字及背景。每次只建立暫時觀測副本，人物點替換為當前原生值，再走原有字模範圍、印前底圖與VGA守門。繪字後還原人物原RGBA，譯文仍在原欄並由人物自然遮擋，不移動玩家欄位或互動區。

靜態頂列也可沿同一完整人物證明保留；R121士兵分支及其反例保持。來源快取、328個語言資源與圖像原PNG不改。候選需以既有正常輸入取得四行完整快照，驗四地區排版、可見文字、前景保留、未知差異回退及正常關頁。DRAFT原型不得進正式入口；通過後才審查READY。

R122原型r1已讓春季、金錢／稅率與行動三行恢復四語；座標列仍因計算後安全區碰到教學框上緣回退。原座標墨跡為[260,77,313,83)，高6邏輯像素；y83起有非人物的框線，不能以MSS來源放寬。候選r2按每行原版墨跡高度實測Noto文字與2px陰影，從該行原有寬度候選向下選最大能完整留在原行垂直範圍的字級。選字只依原行幾何與實際字模，不依當前畫素相似度試到通過；原文／背景與人物守門保持。

R122來源測試補充：縮短後的日期與行動譯文可能完整落在人物前景後方，韓文金錢列亦可能全遮住。這些圖層仍須完整生成並清除露出的原英文字；不移動欄位來迴避人物，也不把全遮住的譯文字形記為可見文字正例。測試分別記錄完整字模、人物遮擋與實際未遮字點。六人物各用自己的既有色盤收據；四個R98原版解碼fixture與兩個R101來源fixture分開列證，後者不稱正常玩家路徑。

R122獨立字模量測查明，多數16至22px字模比共用CJK基準上緣高1px；若硬套舊基線且要求原行頂端，會不必要地縮到15px。候選改以每行實際文案與陰影的總墨跡高度選最大字級，並把實際墨跡上緣對齊該行原版上緣。以繁中實測，22px日期總高24px、18px金錢總高20px、18px行動總高20px、21px座標總高24px；各行仍在原版6／5／5／6邏輯像素高度內。基線位移記錄在baseline_shift_px，其他語言依同法獨立量測。這訂正前一候選的過小字級，不以通過守門作選字依據。

### R122人物前景與狀態欄 READY

DRAFT來源及排版審查通過，狀態為READY。來源仍為R120／R121同一合法原版與dosgolem82a14b2，VICEROY.EXE、GAME.TXT與六個MSS的檔名／SHA-256沿本規格及規格069的正式定義；原文鍵與逐行來源依規格032及text/sea-status.zh-Hant.tsv。位址為real-mode 20-bit線性RAM，Main 0x2CAE0、VGA 0xA0000。候選67筆既有正常輸入至258000000步的CPU、完整RAM、VGA及DAC與R120基準相同。

- 原始快照含三份完整頂列及四行側欄。日期墨跡[242,51,281,57)、金錢／稅率[242,58,309,63)、行動[260,70,290,75)、座標[260,77,313,83)，原版墨跡高依序6／5／5／6邏輯像素。來源以完整原文字元及原生墨跡／底圖為準，不從HD圖像或譯文反推原版數值。
- 完整MSS前景只接受正式1060至1065來源，唯一目的位置由持有的原版local像素與畫布位置建立，並逐點核對尺寸、完整opaque數、原生值、local映射、色盤、Main／VGA及游標還原。局部來源、重複目的位置、其他圖像、未完成解碼或未知同值寫入都不產生前景遮罩。四個R98原版解碼fixture與兩個R101來源fixture分列，不把後者當正常路徑。
- 只接受已由既有譯稿辨識的完整sea-panel或頂列。原文來源像素必須等於該次原版快照；人物以外的原字點保持，最終計算的安全區除已驗人物外逐點相同。觀測canvas／after僅建暫時副本，不改journal、原版RAM、來源值、規則、輸入或存檔。其他列後畫在本行安全區外不阻塞本行，不放寬本行未知後畫。
- 四語每行仍依原寬度候選、實際文案與2px陰影量測，選擇總墨跡高度不超過該行原版墨跡高度的最大字級，再將實際墨跡上緣對齊原版上緣。既有Noto圖集15至22px不重烘；繁中日期22、金錢18、行動18、座標21px，其他地區逐欄量測見本機收據。每行記錄baseline_shift_px，所有新墨跡留在原行垂直範圍。
- 先清除可證的原字，再畫譯文，最後還原前景原RGBA。短譯文完全被人物遮住時記為圖層已生成、可見字形為零，不移動欄位、不擴張點擊範圍、不記為可見文字正例。英文模式仍走原版字體。
- 隔離候選4項／218個含子項通過且零skip，含四語16個欄位、112個新拒絕案例、六來源完整與錯件、R120正文及R121頂列守門。四個R98來源通過原版解碼呼叫；MSS2／5只授予來源fixture檢查。正式建置、四語兩模式／游標／關頁及當次輸入原版控制組接續驗證，完成後再記限定CONFORMED。

既有hd-opening-animation-sources-r84工作根的r122-ready-review-r1.json是READY收據入口；來源gui.sea-sources.json的SHA-256為a9baffb1841b256f55074da6614647f8a8bdd2c2152d848ebc51c8f7fd4594c8。實作入口為tools/language_rebuild_probe.go的seaDialogForeground、draftPreserveDialogSea及draftSeaNativeHeight。測試色盤入口為R98的r98-embedded-palette-expectations-r1.json，指紋fa1ae2c74ab6bbffe6ce9e9fe8ce2d9f8dfce6e0a1c813767a82e1c28edec18c。來源fixture與原像素只留本機；翻譯只改顯示，TSV、328個語言資源、382張HD原PNG與941個來源連結保持。

### R122人物前景與狀態欄限定CONFORMED

正式970366ee3d396991e97d76edeb771cbe4f973ecc398e54b220ff484be5532d3d通過建置與go vet，程式提交e9d59bffcbe9744a3105815b544c06e683301b7d。4項／218個含子項通過且零skip，包含四語16個原版欄位、112個新來源反例與既有正文／頂列守門。六人物來源檢查的四個原版解碼fixture及兩個來源fixture分列，後者未新增正常路徑信用。

當次正常GUI共44張，全部1280乘800遊戲區與X11相同。18張事件圖含四語兩種圖像模式、四語游標往返與英文；16張非英文事件有64筆側欄合成，頂列及正文保持。短譯文完全被人物遮住時，只計字模生成與原文清除，不記為可見字形正例。每行實際文字及陰影留在原墨跡垂直範圍，正常關頁後人物來源歸零、正文撤除，四行及頂列恢復正常顯示。

原版控制組重播當次78筆真實GUI輸入至273600000步，完整CPU、RAM、VGA與DAC相同。收據入口位於既有hd-opening-animation-sources-r84工作根的r122-display-close-final.json、r122-panel-gui-final-check-r1.json、r122-formal-unit-display-r1及r122-panel-control-r1/check.json。來源、字模與各地區字級／基線量測保存於上述欄位收據；原版fixture只留本機。328個語言資源、382張生成原圖、941HD來源及已發布版本保持；完整五語、全量HD、音訊、存檔及新版交付沒有新增完成聲明。

## R127 登陸詢問正文與顧問前景 DRAFT

- 範圍限於正常登陸確認的既有GAME.TXT:@LANDFALL:0x00000FAD正文；四語譯文、原版選項、遊戲規則與操作不變。LANDFALL2及其他正文未有本輪正常證據，不外推。
- confirmed：R125正常載入COLONY09.SAV後以實際原生輸入至80800000步，選項中文、正文仍英文。既有原文觀測於76192214步取得完整正文，墨跡[67,122,250,141]；原文字元來源緩衝線性RAM175222，GAME.TXT SHA-256為67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a，0xFAD是檔案偏移。
- 強推論：後畫顧問與正文上緣重疊，導致目前完整安全矩形守門撤銷正文。先用不改動原生事件的私用診斷匯出量測；不能以猜測的座標或寬鬆像素比對接正式路徑。
- 原型須沿已驗MSS來源與完整擁有權證明，只容許已確認人物前景內的後畫；未知後畫、來源／色盤錯誤、正文改印、選項不符或缺字模時維持原文。逐欄補原版cap／baseline、安全矩形、四語Noto候選／最長譯文墨跡及基線後再審READY。
- 需要正常GUI的正文與兩選項、懸停重畫、正常關框；對同一組已記錄原生輸入核對原文／四語顯示，原版RAM／索引／色盤與存檔保持。這是既有文字顯示修正，不擴張HD來源或戰鬥驗收。

### R127 DRAFT 補證

- confirmed：診斷只加匯出欄位，以R125的36筆原生輸入重播至80800000步；完整RAM、VGA索引與色盤雜湊均與原GUI第5個觀測點相同。原觀測的dialog沒有地圖buffer，依既有captureDialog的canvas／nil契約載入，不填造缺少的資料。
- confirmed：正式來源為MSS3／research ID1063，完整5910個原生前景點位於[86,29,234,124]。正文安全區[65,119,254,143]有43個後畫變動，全部屬於此來源，5個為原文字點。首個局部fixture誤選1060，核對實際scene_picture來源後改用1063，沒有改原生輸入或來源指紋。
- confirmed：舊流程在處理選項前先將正文標為expired，隨後丟棄正文指標；僅修正最後繪製仍不能恢復正文。韓文的LANDFALL與LANDFALL2共享英文選項而譯文不同，舊全域逐行查譯另回報line-template-not-unique。不得改譯文來迎合查找。
- DRAFT原型改為保存最新完整LANDFALL原生正文候選。第一次正文／選項建立仍需小於2M步、完整兩列原文與順序相符；已建立配對後的相同選項重畫另以原版完整正文、MSS3來源與目前選項核對。僅對此已驗選項組在該次finish使用來源限定的逐行catalog副本，不更動正式catalog或原始識別值。最後實際覆蓋還須通過目前VGA、完整人物擁有權及原正文其他像素守門；關框或未知後畫維持原文。
- 已量測兩行原文為[67,122,250,131]及[67,132,191,141]，cap為8／9。四語Noto沿此欄候選30至20px，30px均可容納於[65,124,254,143]，不寫入人物前景。量測與下一輪原型的完整拒絕、基線及正常GUI結果通過後才可升READY。

### R127 READY 審查，2026-10-20

- 原型57個含子項檢查零skip，涵蓋四語正文與來源限定選項、初次2M步邊界、已配對的較晚重畫、未配對較晚選項、錯序原文、缺字模、錯正文／位置、未知後畫、VGA／色盤不同、人物來源擁有權遺失及關框。英文畫布完整保持原版。原型9張正常GUI中，繁中與韓文的正文及兩選項都已可見，完整X11遊戲區與正式整合繪圖相同；已目視確認。
- 修正分三段：保存最近一次完整LANDFALL正文候選；只在完整原生正文、MSS3前景、兩列原文／順序／位置及首次小於2M步符合時，為當次finish借用該正文的選項catalog副本；最後依目前完整來源與VGA核對後繪製正文。已配對的相同選項可延續重畫，不改初次2M步上限，不修改正式catalog、原生觀測、原始來源時刻、譯文或遊戲資料。
- 安全區保持[65,119,254,143]以清除完整舊正文；文字排版區為[65,124,254,143]，輸出756乘76點。MSS3完整來源為5910點，原正文43個變動只限已驗前景，其中原文字點5個；所有前景像素保留。
- 原文首行S／Y／E正常色68的墨跡y122至128，第二行墨跡起點相差10。Noto四語在此欄的30至20px候選中均選30px，字模繪製原點y489、ascent35，實際字型基線y524，位於原版首行正常墨跡末列放大後y512下方12點，以避開人物。先前診斷把字模原點標成font_baseline，審查依圖集ascent更正，原圖與繪製沒有改變。
- 無變數的最長現行正文即這一則。相對於原安全區的含陰影墨跡：繁中[6,22,541,56]、簡中[6,22,532,57]、日文[6,22,541,56]、韓文[5,22,449,58]；全部位於下移20點後的排版範圍。沿既有換行／縮字候選；缺字、超界或任何來源守門失敗回原文並記錄原因，不強行顯示。
- 原版檔案：GAME.TXT為67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a；MSS3.SS為10fc6aa8b8f14eb1d1aea35b5bc9addd84cc2b55829d97d2294e7dcff21793ce；VICEROY.EXE為a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3。0xFAD是GAME.TXT偏移；175222是原文字元緩衝的線性RAM，1063是既有研究資產ID，彼此不當成同一地址空間。
- 審查收據為既有hd-opening-animation-sources-r84工作根的r127-prototype-review-r1.json，SHA-256為66874b1c6b8bcb4408caf2309048c878fbe30e0c5720f08d8c2c8a973eaaa67c；36筆R125正常輸入的原生觀測指紋6181a2ef6bc0bc4ea0713c03204ca5de4ffce54f022798820fee1b67166c16d7。工具沿dosgolem82a14b2、Go1.26.7、Ebitengine2.9.9及既有固定Noto字型，不新增原版內部研究。
- 本審查授權將以上限定顯示修正接入正式來源；原型的額外診斷欄位不得搬入正式程式。正式後仍驗四語兩模式、英文、選項懸停與正常關框、當次正常輸入的原生狀態及必要回退。其他正文、全量HD、完整五語、戰鬥、獨立與結局不由此提升完成狀態。

### R127 登陸正文限定CONFORMED

正式d75e56956c2d28c7c23b689cb06b393cbe760fccbb4b8e1319a1a72d99ed01e2的文字來源與已審原型逐byte相同，私用額外觀測匯出未接正式程式。建置、go vet與4項／109個含子項通過，零skip；包含本欄57個、既有士兵正文及選項保留守門。四語正式來源測試圖片與原型相同。

正式23張正常GUI完成四語的原版／HD與英文原版、原生第一／第二／第一選項懸停、選留在船上及正常關框。全部23552000個X11遊戲區RGBA點與輸出畫布相同；15張正文可見畫面另核對34830個Noto實色字點，舊英文缺陷畫面僅511／2546點相符，會被此檢查拒絕。23組設定事件保持完整原生狀態，英文畫面完整等於原版索引與DAC放大。關框後正文、選項與MSS3繪製均撤除。

當次43筆實際原生輸入以修正前fb9c752c…前端的原文模式重播至100600000步，完整CPU狀態、RAM、VGA索引、DAC及存檔相同。RAM為baf72aaf6889b71e2ae0865a0cc661189ba9952678cc0426d825c3452f3d9025。此為目前顯示修正的正常操作驗收，不增加音訊或戰鬥信用。

本機收據為既有hd-opening-animation-sources-r84工作根的r127-landfall-display-close-r1.json，SHA-256為a0cbd64632b60c48bd46aff6e89894f306ae1f6ac1ab8071b34969e64a320d32。原始存檔、觀測與控制組只留本機；公開來源、文字表及現有README截圖依原權利界線處理。385張生成原PNG、386檔清冊、986個HD連結與328個語言資源保持，沒有新增HD來源、LANDFALL2、其他人物或完整五語的驗收信用。

## 2026-10-21 R131 攻擊原住民確認正文 DRAFT

- 範圍限於正常地圖對原住民部隊發出攻擊後的確認框。R128正常實拍顯示兩個選項為中文，正文仍是英文；不改攻擊、部隊、亂數、存檔或確認行為。
- 強推論：可見原文符合既有GAME.TXT:@WHACKINDIANS:0x000038BD，0x38BD是GAME.TXT檔案偏移，來源指紋沿既有corpus的67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a。人物沿已接線的MSS1來源1061；完整原生觀測、實際人物位置與安全矩形由當次正常GUI補證。
- 候選沿R127正文與選項配對機制，只在完整原生正文、來源限定選項、已驗人物及VGA守門均符合時繪製。未知背景變化、缺件、錯位、來源或選項不符時保留原文並記錄，不把其他對話推定為同一欄位。
- 字級、基線與人物外排版區須由這一框的原文字元墨跡及四語Noto實測制定；不外推R127登陸位置。譯文及變數沿現有TSV與328個語言資源，不在程式內放顯示文案。
- 私用診斷只額外匯出既有dialog觀測的來源快照，不新增原版攔截或改寫記憶體。DRAFT候選只放隔離模組；來源、排版與必要反例足夠後才審READY並接正式入口。正常GUI四語、英文、兩模式、選項與關框及當次原文控制組另驗，不由此授予全部戰鬥或全量HD完成。

### R131 READY 審查，2026-10-21

- confirmed：當次正常GUI的76筆原生輸入停在237800000步。只補匯出的重播完整CPU、RAM、VGA、DAC及存檔與正常GUI相同，兩份完整原文觀測SHA-256為72cc4231391979945ace0dbaa2323d04185db5ffbda4d7ca50b8c3934900dad0。這是觀測匯出一致性，不冒稱修正後正式原文控制組。
- confirmed：正文鍵為GAME.TXT:@WHACKINDIANS:0x000038BD，原始字元緩衝為線性RAM175142；其後完整兩列原文選項與正文相差139800步。一般來源會將選項辨識為共用Yes／No；候選只在完整正文與MSS1來源成立時，為這次finish借用該正文的選項catalog，辨識為該正文的#2+list，不改TSV或正式catalog。
- confirmed：完整MSS1來源1061為4429點，目的墨跡範圍[195,34,266,173]。正文安全區[57,114,246,138]內有103個後畫變動，全部屬於已驗人物，其中13點是原文字點；未知後畫維持回退。來源fixture只按當次正常GUI的目的位置移位，局部D46測試不另增加正常路徑或原版行為信用。
- 保留最近一次完整正文候選，首次與選項仍須小於2M步；已配對後只允許同一完整來源的選項重畫。最後覆蓋必須再核對完整MSS1、全部非人物背景、原文來源、選項安全區、VGA及色盤。人物後方的before副本只替換已證實前景，原版RAM及journal保持。
- 原正文兩行墨跡為[59,117,217,136]，原首字S墨跡框[59,117,65,125]，cap為8。清字安全區保持[57,114,246,138]；四語文字排版區改為人物左側[57,117,193,138]。Noto以30px作此欄候選，四語均完整容納。字模原點y461、ascent35，實際基線y496，位於原首字放大墨跡框下緣y500內4px；原文字點仍完整清除。
- R2含陰影的相對安全區墨跡：繁中[6,14,391,48]、簡中[6,14,382,49]、日文[6,14,481,48]、韓文[5,14,399,50]，都在右界544點及完整96點高內。此限定幾何最寬已驗正文為日文；其他名稱若原生墨跡或來源幾何不符仍回原文，不外推驗收。
- 按原墨跡對齊基線後，R2完整相關測試179個含子項零skip，其中新欄位70個；另以未改的R127正式測試程式重檢109個含子項零skip，重檢不稱為歷史stdout復原。四語原型已目視，R2另確認繁中及最寬日文；每語70864個人物放大RGBA點保持，兩個選項同時可見。反例包含錯正文／位置／時刻、未知背景、VGA、色盤、缺來源、錯選項、選項撤除、先後順序與首次2M步邊界。英文完整保持原版。
- GAME.TXT SHA-256為67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a；MSS1.SS為7b580f7ebda2e03d34ca88c19942f6fd3707d044fceed2f8626e66aac62da6ea；VICEROY.EXE為a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3。0x38BD是檔案偏移，175142是real-mode線性RAM，1061是研究資產ID。工具沿dosgolem82a14b2、Go1.26.7、Ebitengine2.9.9及固定Noto；dosgolem的upstream推送位址保持DISABLED。
- 本審查授權以上限定顯示修正接入正式入口。接續正常GUI四語兩模式、英文、選項懸停與取消、當次原文控制組；通過後才記限定CONFORMED。其他正文、全量HD、完整五語、戰鬥結果與結局沒有因此完成。收據為既有hd-opening-animation-sources-r84工作根的r131-ready-review-r2.json；所有原版觀測與原型圖片只留本機。

### R131 正常GUI回退與來源快照時點 DRAFT 補正

正式r1的十組語言／圖像設定已正常擷取，但四語正文仍回原文，未達CONFORMED。當次選項觀測在230835001步收束，MSS1的other_writes只到[195,34,266,129]；先前隔離來源的同一欄已包含完整[195,34,266,173]人物。正常畫面目前的MSS1仍有4429個完整有效來源點。孤立測試沒有覆蓋選項快照先於人物完成的情況，原READY的排版數據保持，來源時點判定回到DRAFT。

候選只將正文／選項來源配對時的人物完整性驗證改用當前原生Main、VGA與色盤，不要求較早的選項快照已含完整人物。原文正文、選項字元與位置、首次小於2M步、完整人物持有權、所有非人物背景及最後實際選項安全區仍須符合。增加選項原字保持而人物下半尚未畫入的來源測試，並重跑正常GUI後才補READY及CONFORMED，不改原版程式或放寬未知後畫。

### R131 來源快照時點補審 READY

183個相關含子項測試零skip，其中四語各有一個「選項原字完整、選項快照中的人物下半尚未完成、當前畫面已有完整人物」案例。該來源快照仍走原文字元與安全區辨識；完整人物、正文非人物背景與VGA則改在當前原生畫面證明。只修改來源限定選項查譯所用的人物證明時點，首次2M步、完整選項、字級、基線、最終覆蓋守門與未知後畫回退均保持。R4四語圖片與前輪已目視R2圖片逐byte相同。

此補審升為READY，收據為既有工作根的r131-ready-review-r4.json。正式r1的實拍保留為未通過樣本，不納入完成度；接續正式r2的正常GUI、懸停、取消與當次原文控制組後才可升CONFORMED。

### R131 攻擊確認限定CONFORMED，2026-10-21

正式r2程式SHA-256為ed5b6a4e1824ab18bd0b100c4f1b5fc9423cf541503519b184f782ba8d2d9a52，非測試文字來源與READY候選相同，私用觀測匯出未進正式入口。建置與go vet通過；5項／183個含子項測試零skip，包含既有109個守門及本欄74個，四語皆涵蓋較早選項快照的人物下半尚未完成、當前畫面已有完整人物的案例。

正常GUI共64張，四語各驗原版／HD，英文驗原版／HD；33張可見正文逐點核對64420個Noto實色字點，全部65536000個X11遊戲區RGBA點與繪圖輸出相同。正文30px、清字安全區[57,114,246,138]與排版區[57,117,193,138]保持READY數據，兩列選項使用正文來源限定catalog。12張HD懸停沿四語第一／第二／第一選項，人物4429點及HD游標均可見；正常點選取消後正文、選項與MSS1繪製撤除。

104筆當次實際原生輸入由修正前fb9c752c…前端的原文模式重播至269200000步，完整CPU、RAM、VGA索引、DAC、原版輸入指紋及存檔相同。最終RAM為a6bcec7741676922a0ad85fbd6a6e60215a43c28a1bd14dbfcfa8d875b11bbc8，輸入SHA-256為3f422b7f55bcefc24c7aff48fc130ade3be41809b797878681661782facca7e6。初始COLONY09.SAV仍為b5e9391c…；原版兩側自動存檔皆更新為6e4ea3a0264df02b517ed1d7354e882636381e195c75c0eaf9f58e1e8da3421d，不把最終存檔冒稱未改變的種子。選單存檔計畫未實際執行，沒有新增手動存檔、音訊或戰鬥結果信用。

正式r1仍顯示英文的實拍保留作反例；檢查器只匹配258／1335個預期繁中字點，會拒絕舊缺陷。該失敗推翻的是較早選項快照已含完整人物的假設，READY來源時點補正後才進正式r2，沒有放寬未知背景、首次2M步、完整原文與選項守門。

公開驗證入口為[攻擊確認檢查器](../../tools/check_goal186_attack_confirmation.py)，以--game指定合法原版、--reports指定既有hd-opening-animation-sources-r84工作根。正式GUI為r131-attack-formal-gui-r2，原文控制為r131-attack-control-r2，建置與測試收據為r131-formal-build-r2.json及r131-formal-test-check-r2.json。R132已將capture紀錄無損封存，檢查器可直接讀取.gz；原版、fixture、存檔與實拍只留本機。

依規格049增量合併後，矩陣設定103列，本輪新增攻擊確認1列PASS；66列沿用已接受收據，36列僅歷史基準。普查1975項／933shown／950pending／92unreachable，唯一狀態變更為GAME.TXT:@WHACKINDIANS；320項有現存收據，613項僅歷史。舊開局完成檢查器受較早來源快照限制，沒有列為本輪新PASS，既有開局驗收保留。完整操作在r133-attack-census-delta/operation.json，並由[文字普查](../text-census.md)及[驗證矩陣](../verification-matrix.md)索引。

本次只授予已觀測Cherokee確認框的正文、完整選項與既有MSS1前景幾何限定CONFORMED；其他名稱或幾何依原守門回原文，未驗分支保持未完成。385張HD原PNG／386檔、986個HD來源連結與328個語言資源未變，不提高HD來源數，也不宣稱完整五語、全量HD或戰鬥結果完成。
