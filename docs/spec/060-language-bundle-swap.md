# 完整語言包與原文快取交換

狀態：DRAFT。只供隔離原型及證據審查，尚未授權正式後端。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。
使用者已確認五語及四地區Noto；本規格處理既定切換要求，不變更原版資料格式或玩家操作。

## 目前證據

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
