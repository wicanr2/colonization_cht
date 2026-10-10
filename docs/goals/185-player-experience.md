# 目標185：dosgolem遊玩體驗與Issue關閉審查

日期：2026-10-10。狀態：#56完成，追加正常抽驗與新版三平台交付驗收通過；Release準備發布。未宣稱全部情境驗收完成。

## 2026-10-10追加抽驗與重新交付

使用者明確授權本輪抽驗後commit、push、重製推廣影片及三平台完整版加Release。沿規格044、現有封裝與權利邊界，不重新定義中文化完成標準；預定v.1.0.3-20261010，實際版號日期依Asia/Taipei發行日核對。

新正常條件訊息抽驗入口為既有私用根中的 `play_issue56_wagon_sample.py`、`issue56-wagon-seed/`與`issue56-wagon-sample-gui/`；中英及缺字模重播留同名前綴的zh／control／missing目錄。輸入只經正常GUI，不改原版RAM或存檔內容。

本輪打包中間物統一在同根 `release/`，由現有tools/build_release.sh、package_three_platforms.sh、assemble_release.py及build_promo.py重生；正式交付沿dist-all/<版本>/。原版資料完整包留full-local，公開Release僅完整功能包、MP4與雜湊清單。

追加抽驗入口為[貨車與存檔檢查器](../../tools/check_goal185_wagon_sample.py)。15圖四側原版狀態、記憶體、索引、色盤、WAV與兩份存檔全等，中文GUI與中文重播逐像素相同，缺譯回退與原文相同。收據為同根 `issue56-wagon-sample-review.json`。食物教學、貨車資金不足與存檔成功三則中文通過；普查只採食物教學與存檔成功，不將BUY同文模板當成來源證據，不將未觸發的城市條件列為GUI通過。

封裝工具恢復見[規格041](../spec/041-linux-appimage.md)，字模來源恢復見[規格044](../spec/044-release-and-promo.md)。固定工具與字模輸入收據留 `release/tools/`、`release/`；沿用已驗正式包的字模，不冒稱重烘。

矩陣與普查增量入口為同根 `register_wagon_sample.py`、`history-census-102-delta/`。新版影片畫面由 `release/replay_promo_scene.py` 使用本輪正式包與既有正常GUI輸入重生；素材與驗收都留 `release/`。

採用後的普查指紋列由 `finalize_wagon_sample.py` 重驗。正式包字模來源、六個拒絕案例與時間戳由 `release/check_delivery_inputs.py` 核對；影片設定由 `release/prepare_promo_config.py` 核對正常輸入、程式與收據指紋後產生。

交付總檢查入口為 `release/check_final_delivery.py`，摘要留 `release/delivery-review.json` 及正式根的 `smoke/delivery-review.json`。Linux／Windows自帶資料包正常一鍵啟動重播，完整RAM與公開包一致；macOS只驗雙架構、簽章、檔案清冊與shell，沒有真機聲明。

### v.1.0.3-20261010交付驗收

三平台公開包各兩次乾淨重建全等，私用完整版各經清冊與一鍵入口驗證。Linux／Windows正常啟動與同輸入完整RAM為c8032606aaddb6f045b97e16e58ff9057e49421260c75861100f1fb5ca42b3a1，WAV為3062c132ffb18df60e4fe435c9eea613e0aa8f1a41f35b2c7a3c0375983f3f39。Linux／Wine主選單五列及版本的安全區逐像素相同。

| 交付物 | bytes | SHA-256 |
|---|---:|---|
| 公開Linux AppImage | 18606584 | e41a46b5db821e9573bcc42f40e15fea7c905a87e2d17d67b5eccd1ef6d1fffa |
| 公開Windows ZIP | 14073582 | dbfbe605abfcd8ad726f9a270849af9f097e1afdfeb009d369a3fb7b0d40e627 |
| 公開macOS通用ZIP | 14283310 | 653107ac79aa58f83e264930a905ac9bbb579e6221fb7f7bee3aa761d9b84c1d |
| 推廣MP4 | 4006348 | 79014291f5b033442d7896adbbbf53985e7db373c6264eceec54cb23c877fa5b |
| 私用Linux完整版 | 21615333 | 1cd196d67e9b5eb30d0250efecccddd5bb7ebfd16e489ea85ad0bb33b632135e |
| 私用Windows完整版 | 18209135 | c7184c21f02ee17f78e366dd85eb9bbd111d9d09125ec29291c1cc0e34cff324 |
| 私用macOS通用完整版 | 18431758 | fa5098f06fc0bd7a2628cb275d2f3f6360038183dce305f0108ab2f82385593b |

正式根為 `dist-all/v.1.0.3-20261010/`。`patch/`及MP4可公開，`full-local/`含原版資料只留本機；原始存檔未隨包複製。完整交付審查SHA-256為cbe26579b1bb32a7b741102010bd841d0c0b78d8ba878d9070a8af716e9fec68。

影片為90秒、1920×1080、30fps、H.264／AAC；六個現行畫面由正式Linux包及正式Windows正常GUI產生，三段原版終點與原GUI相同。原版連續音樂沿已驗舊收據，音源dosgolem b0bf259與現行畫面82a14b2分別登錄。影片非靜音，平均−20.5dB、峰值−2.5dB，無非預期黑幀；八幀與字幕安全邊界已目視。固定畫面剪輯不冒稱連續遊玩錄影；未新增人耳或音效卡驗收。

封裝映像為eob-remake-release:1.26.7-ebiten2.9.9-20261008-r2，SHA-256 a7c1001218f195867205b5f87d49d79c4cf4f183a465dcee89db6c96a260ea4e。macOS沿hr-osxcross:1.26.7-15.5-r1，SHA-256 8f65ed80db84a005343cfdbaa3cdb3494192bd04d60771f99818d5f3ac9f3873；Wine沿eob-remake-wine-verify:ubuntu-noble-20261008-r2，SHA-256 c047a6a259a1fc9a90babf7c937310fa9df4b3465bf75f3fcaad1bc640099c2f。沒有建立重複映像。

重建時，先在新私用批次使用build_window_prototype.py組裝來源，工作區Go版本為1.26.7，沿build_release.sh產生三平台二進位與inspect-version。容器掛載、原版與字型唯讀、UID/GID及資源限制依本頁既有契約；`/out`須指向新的私用工作根。字模恢復時，在封裝容器設定以下輸入，並依規格041覆掛已核對的工具目錄：

```sh
export COLONIZATION_RELEASE_WORK=/out/release
export COLONIZATION_RELEASE_MASK_BUNDLE=/repo/workplace/reports/goal184-linux/music-independent/release/extracted/appimage/squashfs-root
export COLONIZATION_RELEASE_MASK_MANIFEST_SHA256=b5ef89cf8f894e7e01a45a5c21cd80b5df97b01459e65228d9f5169d982153e2
bash /repo/tools/package_three_platforms.sh v.1.0.3-20261010
```

歷史包不存在時可從保留的v.1.0.2公開AppImage恢復字模；仍須逐項核對manifest與現行譯稿，不以缺失中間物冒稱重烘。重播、影片、彙整與最終檢查入口均在本節前段索引。

Release說明草稿保存在 `release/release-notes.md`，只上傳三個`patch/`封包、MP4及根SHA256SUMS.json。公開後遠端附件核對留 `release/published-release.json`、`release/remote-asset-review.json`，不公開本機完整版或原始PNG／WAV。

提交前文件、來源語法、工作清單、TSV格式、索引正對照與擁有權檢查由 `release/final_check.py` 執行，結果留 `release/final-check.json`。普查說明採用後的重生也由此入口處理。

BUY原始來源的輔助觀測留 `release/buy-source-observer/`，使用公開probe_goal181_buy_sources.go，觀測到@BUYME0，但該觀測器完整RAM與正式GUI不同，不宣稱同狀態。初次102批的BUY同文來源歸屬已拒絕，留 `history-census-102-template-alias-rejected/`；現行增量重新從101批合併，只新增已驗食物教學信用。

## 2026-10-10收尾入口

#56完成審查PASS，摘要bd42464d1208d4144dc5efd4c6daf5e795a392efd1d751d3bda01b03c6b9e3cc；矩陣101列中的本批9列PASS，另外56可重驗列及36歷史列沿用。普查1975／931 shown／952 pending／92 unreachable，本批不增加shown。正常新34圖、93圖當前回歸與10列既有範圍檢查通過。#55未完成，#61遠端關閉仍待授權。

#56依既有的「完整接線、代表性正常GUI」決定收尾。公開入口為[完成檢查器](../../tools/check_goal185_colony_completion.py)，完整收據留在 `workplace/reports/goal185-player-experience/issue56-completion-review.json`。288項TXT來源、19種變數模板與19種常數模板分開驗證；三個歷史整段清單鍵與未抽樣情境保留。完整Go測試180項與go vet通過，正式程式SHA-256為73d863baa358dce354bf2d13b232735c2e9109a48d1b1c15a61d88df031e4ee2。

本批矩陣及普查入口為同根 `register_issue56.py`、`issue56-nine-matrix-rows.json`、`merge_census_101_delta.py`與`history-census-101-delta/`。文件採用與負例入口為 `adopt_issue56.py`、`check_issue56_negative.py`及`issue56-negative-review.json`。原版素材、完整事件、RAM、音訊與存檔只留私用根。

採用後由同根 `finalize_issue56.py` 重驗會回報普查指紋的開局收尾列，更新矩陣報表的輸出指紋，並核對65個可重驗列的檢查器與原版收據未變；不重新生成或提高shown。

## 2026-10-10接手時的狀態與探勘索引

下段保存接手過程及私用證據入口；目前狀態以本頁頂部及CONTEXT為準。

本次使用者指定完成#56，完成後commit及push。範圍審查入口為同根 `prepare_issue56_audit.py`、`issue56-source-connection-audit/`及`issue56_source_audit_test.go`；完整來源與欄位消費端審查、正常建造長清單驗證完成前，#56維持進行中。既有#55／57／61修改與驗收保留。

四則新增城市變數與建造清單來源的IDA審查使用同根 `ida_issue56.py`、`ida_issue56_code.py`及`ida-issue56/`，正式資料庫唯讀，查詢在一次性副本執行。

建造換頁的正常人口成長探勘使用同根 `play_issue56_growth.py` 與 `issue56-growth-gui/`，只用原版操作、正常自動／手動存檔，不修改存檔內容或原版記憶體。原版換頁門檻與目前15項清單分開驗證。

本次城市接線的正式建置、完整Go與來源審查收據統一留在 `issue56-source-connection-audit/`；production檔名沿既有建置器的dialog.go／strings.go／adapter.go，測試原始模板及公開函式，不把資料契約稱為正常畫面。

當前候選的既有正常輸入回歸留在 `issue56-tutorial-regression/`、`issue56-build-regression/`、`issue56-compact-regression/`與`issue56-trade-regression/`，逐項核對原始GUI初始存檔集合及雜湊後重播，不沿用結束後已改寫的存檔作起點。

重播批次入口 `run_issue56_regressions.py` 與 `issue56-replay-seeds.json`；`issue56-trade-seed/`只複製原34圖貿易收據中未改寫的03／09兩檔，排除新建的01檔。原正常流程沒有結束回合，自動存檔09未改寫。

正式新正常GUI由既有 `play_trade_fields_formal.py` 驅動，收據為 `issue56-formal-gui/`；四側收據留在 `issue56-formal-zh/`、`issue56-formal-control/`、`issue56-formal-missing/`與`issue56-formal-baseline/`，批次入口 `run_issue56_formal_peers.py`。收尾公開入口為[殖民地範圍完成檢查器](../../tools/check_goal185_colony_completion.py)。

建造與精簡選單的當前來源延續入口為 `check_build_transaction_issue56_retained.py`及`check_orders_compact_issue56_retained.py`，舊檢查器與收據保留。

後續回合入口為 `play_issue56_growth_turns.py` 與 `issue56-growth-turns-gui/`，從前次正常自動存檔載入；舊狀態欄的dialog_text只是最後印字，不用它判定當前有彈窗。

前兩次探勘停在View Pieces／城市，沒有年份進展，保留診斷而不採用。第三次 `issue56-growth-interactive-gui/` 使用有界容器 `colonization-issue56-interactive`，逐步核對Move Pieces、城市退出與正常自動存檔年份。

本次接手的私用貿易原型與量測入口為 `prepare_trade_fields_candidate.py`、`trade_fields_test.go`、`trade-fields-candidate-v5/`，均位於本目標的既有 `workplace/reports/goal185-player-experience/`。先按規格038的DRAFT審查正常22圖，不授權正式放寬。v2保留框頂假設失敗，原版實測為y83。v3標題／網格／刪除成功，但TRADESTART正文沒有逐列items，單列候選須依其真實身份與原版快照守門。

原型完整審查由同根的 `check_trade_fields_candidate.py` 重生 `trade-fields-candidate-review.json`，原版像素只留私用根。

正式正常GUI入口為同根 `play_trade_fields_formal.py`，接續主選單、兩條路線、取消／刪除／恢復第四目的地及GAME手動存檔，不修改原版SAV或注入座標。

目前正式來源與既有教學／百科／開局／四城市槽位契約的延續審查在 `trade-fields-connection-audit/`；`trade-fields-tutorial-regression/` 與 `trade-fields-build-regression/` 保留13／31圖回歸。仍保留各舊版收據，來源指紋不冒充重新錄製GUI。

正式限定驗收入口為[貿易欄位檢查器](../../tools/check_goal185_trade_fields.py)，輸出 `trade-fields-formal-review.json`。缺原版回傳SKIP77，錯版、錯二進位、不同原版狀態、回退或文字安全區外差異均拒絕。

當前建造與精簡選單的私用延續檢查器為 `check_build_transaction_trade_retained.py`、`check_orders_compact_trade_retained.py`。`trade-fields-replay-seeds.json`記錄正常前置存檔指紋；重播器在啟動前核對GUI的初始檔名集合，禁止沿用不相符的結束後存檔。

第100列及七個受影響列由 `register_trade_fields.py` 重跑，輸出 `trade-fields-eight-matrix-rows.json`；未據此宣稱全矩陣重跑。

普查增量入口為 `merge_census_100_delta.py` 與 `history-census-100-delta/`，保留99批的歷史基準，只增加檢查器核准的五個欄位。

本批負例入口為同根 `check_trade_fields_negative.py`，輸出 `trade-fields-negative-review.json`；文件採用入口為 `adopt_trade_fields.py`。兩者只在既有驗證容器執行，不修改原版或既有收據。

採用後的八列重驗及生成稿一致性由同根 `finalize_trade_fields.py` 核對，保留更新後的矩陣輸出指紋。

目前真相以[CONTEXT頂部表格](../../CONTEXT.md)及[唯一工作清單](../worklist.json)為準。工作目標仍為完成#55／56／57／61；下方較早段落只保留歷史。

正式0484e99b…通過169Go／go vet，無skip。路線2標題按原版顯示2，第三London／第四Jamestown、首／次目的地單列與三列刪除選項已依規格035／038限定CONFORMED。新34張正常GUI包含懸停、取消、刪除、重加及GAME手動存檔；四側完整原版、每點RAM／索引／色盤、WAV與存檔一致，只在核准安全區改變16圖，另外18圖不變。原型22圖證據保留，未改原版規則或存檔。

當前來源的教學21、版畫17、開局27、百科164正文／19索引接線摘要保持；教學13／建造31／精簡選單15圖回歸與已驗版全等。BUILT／FULL／INDIANFOREST2／TOONEAR四城市槽位的16真實來源資料契約PASS，四則訊息尚無各自正常GUI，不增shown、不稱畫面CONFORMED。

#55的558項TXT來源初查、173預設城名與62NAMES接線保留。Land組句與Moderate同文來源仍有oracle未知，完整來源及消費端審查未完成。#56真正超出視窗捲動、其他貿易編號／母港與自動跑商尚未驗證，不由本批局部修復關閉Issue。

矩陣設定100列，本批8列PASS，保留56個可重驗列與36歷史列，沒有重跑全部100列。1975／931shown／952pending／92unreachable，318可重驗、613歷史；只新增EXE:0bdf823568ce、EXE:14e2eb76ddb2、EXE:2f863702e02c三個正常命中鍵。346組名稱容量與四城市資料契約不增加正常命中。

正式審查trade-fields-formal-review.json SHA-256 535ee7112cf5198632688e3f3b91df959a15258dbb9eac2d902b2184f5d81960，普查TSV aebb720fa5743006c7673258103ad662e384e966b0b5fbd01523415294bc7318。錯版、錯程式、不同原版狀態、未核准字級及安全區外差異拒絕，缺原版SKIP77。

本機收據均留既有workplace根；原版像素、RAM、WAV與存檔不公開。#57維持完成與遠端CLOSED；#61功能驗收完成、完整審查PASS，遠端仍OPEN，先前自動核准拒絕關閉，明確授權尚待回覆。沒有重試遠端寫入，未commit、push、打包或發行新版。

## 範圍

依使用者要求，以現行dosgolem中文前端走正常玩家路徑，審查[Issue #53](https://github.com/wicanr2/colonization_cht/issues/53)及[#55～61](https://github.com/wicanr2/colonization_cht/issues?q=is%3Aissue%20is%3Aopen)能否關閉。
本輪工作隸屬Issue #53及#61，不改原版規則、存檔格式或中文化完成範圍。

## 驗證

- 新局與正常存檔入口，檢查主選單、鍵鼠、移動、殖民地與歐洲港口。
- 正常存檔、關窗、重新啟動及讀回，原版輸入唯讀，存檔使用獨立可寫目錄。
- 檢查中文清晰度、裁切、殘字、遮擋、音訊供給及操作耗時。
- 新正常GUI輸入留存，由相同dosgolem與中文／原文兩側重播。記錄兩側的時鐘、亂數條件與初始資料，不以相同seed數字推定結果相同。
- 原版程式、字型與畫面留在已忽略的`workplace/reports/goal185-player-experience/`。只提交驗證方法、雜湊與審查結論。

## 退出條件

每個Issue有關閉條件、現有證據、這輪抽樣與尚存缺口。遊玩結果限定於實際走過的玩家路徑；中文接線未完成、未抽樣情境及平台限制分開記錄。
發現問題先定位真因，再依既有READY規格修復。需要新行為或版面決策時保留證據，不以猜測補入正式前端。

## 證據入口

回合結束的原背景沿用及封閉彈窗外框保護，正式入口為[check_goal185_reprint_background.py](../../tools/check_goal185_reprint_background.py)。正式b4fe380e…、163Go／go vet無skip，新11正常GUI四側、原始25圖、長建造31圖及職業14／港口10圖驗收通過；來源、字級、READY與限定CONFORMED見[規格038](../spec/038-string-overlay-draft.md)。

15項建造清單的正式來源事務、多次Down／Up、取消與舊12項14圖回歸，入口為[check_goal185_build_transaction.py](../../tools/check_goal185_build_transaction.py)。原版完整來源位址、36,858／38,210步字間停頓、來源快照與VGA快照分離、原型及READY見[規格035](../spec/035-dialog-overlay-draft.md)。正式程式41107b24…、161Go／go vet無skip，新31GUI已取得；四側驗收完成前不稱CONFORMED，不把15項全部可見當成超出視窗的捲動。

單列G母港的正式九GUI／四側与兩列24圖回歸入口：[check_goal185_one_port.py](../../tools/check_goal185_one_port.py)。來源角色与READY見規格035，正式全部依賴完成前不稱CONFORMED。

正常百科類別入口限制由[check_goal185_pedia_boundary.py](../../tools/check_goal185_pedia_boundary.py)核對原版初始化六項命令、MENU查詢、heap鏈与既有31GUI。Miscellaneous／Complete的類別6／7靜態分支存在，但此版正常類別選單没有入口；不把這個結論外推成所有概念情境提示都不可達。

建造面板與清單標題的正式多次導航／取消驗收入口為[check_goal185_build_lifecycle.py](../../tools/check_goal185_build_lifecycle.py)，限定14新GUI／四側与碼頭、職業、地圖回歸。原型与READY見規格035／038，正式14GUI／四側及33圖回歸已PASS、限定CONFORMED，其他列組與長清單不外推。

地圖載入標題正式新GUI／取消与四側入口為[check_goal185_map_title.py](../../tools/check_goal185_map_title.py)，限定唯一GAME.TXT:0x2C8居中標題與自訂六圖回歸；依規格035的READY，正式收據尚未完成前不稱CONFORMED。

### 2026-10-09目前收尾表

接續審查入口：[三種事件版畫收據檢查器](../../tools/check_goal185_woodcut_sample.py)。它只重驗既有三種事件的十一點原版狀態與精確標題像素，不把17個已接線標題當成17次正常命中。六項開局27行、21教學與17版畫的目前來源審查留在本輪`start-current-connection-audit/`，六項原始段落是否實際被卡片路徑讀取仍保留限制。

[#61完成審查檢查器](../../tools/check_goal185_start_completion.py)合併目前來源、既有開局／教學驗收、正常新局存讀、五種失敗、自訂設定、地圖載入與三種版畫證據。須實際通過並更新矩陣／普查後，才能據此完成Issue。

### 2026-10-09完成#61

[完成審查](../../tools/check_goal185_start_completion.py)已PASS。六項開局27行、21教學及17版畫標題的當前正式接線全部核對，既有開局／教學抽樣保留；正常新局存讀、五種失敗、自訂設定八值、地圖載入與三種版畫收據均通過。原始開局段落及其餘教學／版畫情境未全部正常命中，依使用者2026-10-04的代表性抽樣決定保留證據限制，不提高這些來源的shown。

本批矩陣88列中的52個可重驗列全部PASS，另36列僅保留歷史。第89列追加完整收尾審查及已驗美洲選擇兩欄，前52列的設定、檢查器與收據指紋未變；只做兩欄增量普查，沒有冒稱重跑53列。普查1956項／907shown／957pending／92unreachable，286可重驗、621僅歷史，舊shown全保留。WOODCUT段落採三種代表標題，不代表17種事件全數命中。

最終審查`issue61-final-completion-audit.json` SHA-256 `7f193928c3a40e6a8f8884cffc52928d3b7def09273f103ebacc174e8740e80c`，#57回歸摘要`5f002ddd222dbe0827f95a523a764a90f8662c5a282abe103bd1577649eb3a1e`。遠端[#61](https://github.com/wicanr2/colonization_cht/issues/61)已CLOSED，時間2026-10-09T04:46:57Z；#55與#56仍OPEN。新版封包與發行不在此完成聲明內。

#55新正常改名收據確認G兩列London／Quebec仍英文，與已完成單列母港分開。13GUI三側與只讀來源觀測全等，DRAFT見[規格035的名稱變數附記](../spec/035-dialog-overlay-draft.md)。下一步只做這個實際缺口的字級／安全區候選；未建立第二城，不把單位切換探勘當成多城市完成證據。

後續私用候選09e8b2ba…已通過157Go／go vet無skip、13GUI輸入三側及基線，只改一張目的地安全區、30px，其餘12圖不變。172個唯一預設名的固定Quebec矩形投影有166可容納、6回退，不能代替各名稱實際字寬；尚未READY或正式採用。入口`prepare_variable_two_port_candidate.py`、`check_variable_two_port_candidate.py`與摘要ee21d703…。另確認VIEW選Move Pieces後殘留十二項中文，原文側已清除；`check_view_move_residual.py`保存原版一致的失敗證據，根因待145～148M窄觀測。兩個實際缺口均屬#55，已完成#61與#57保留。

接續窄觀測確認1092個原印字位置僅5點存活，MENU卻被重新啟用；原版VGA已回世界。舊正式真實資料與可攜回歸均FAIL，候選157Go、13輸入三側及41回歸PASS，另17新GUI實際懸停／Escape／重開／點選四側PASS，據規格035升READY。正式來源只增加完整MENU存活守門，f8d65786…、157Go／go vet無skip；新正式17GUI與四側仍待完成前不稱CONFORMED。當前來源的`menu-survival-connection-audit/`三項Go審查PASS，PEDIA164／19、開局27、教學21／版畫17的摘要均與原驗收相同；公開#57／#61檢查器只接受內容指紋及當前來源均相符的審查。

正式MENU驗收入口：[check_goal185_menu_survival.py](../../tools/check_goal185_menu_survival.py)。它核對新17GUI四側、只改關框後一區、兩種關閉回原版、41張回歸及明確的原版／輸入／程式指紋。

此項已限定CONFORMED：正式f8d65786…、157Go／go vet、新17GUI四側及41回歸全部PASS，摘要cb4e981e…。第90列與受影響#61列通過後，`extend_verified_census.py`沿89批只做這兩列欄位增量普查，狀態變化0、舊shown全保留；90設定／54可重驗／36歷史，1956／907／957／92，288可重驗與619歷史，沒有冒稱54列重新執行。

長名稱另有New Amsterdam正常13GUI、原文控制與來源觀測：原版內框left62／top77／right257，可沿既有三像素內距到right254。`port-family-candidate/`私用1cead102…按當次內框與完整列位置排版，158Go／go vet無skip、172唯一名容量全部可容納，仍待正常短名／長名三側及33張既有目的地回歸；不冒稱三列正常命中。規格035保存DRAFT與來源指紋。

候選後續26個正常GUI輸入取樣三側及33圖回歸均PASS，入口`check_port_family_candidate.py`；仍DRAFT待READY／正式新GUI。人口加入探勘沒有取得第三居民：底部圖示開現有毛皮獵人選單。交互到期缺完整關窗收據，只留診斷；返歐後木匠預設登下一艘船，已嘗試SailYes，但未存回。下一步用有限腳本重走已知動作，在回世界後直接GAME存檔並關窗，避免多按Escape開退出確認。

目的地族群已依規格035升READY並正式接線6ea4f982…、157Go／go vet無skip；短名／長名各17新GUI、四側與33既有圖均已產生。公開驗收入口為[check_goal185_port_family.py](../../tools/check_goal185_port_family.py)，只登錄原版SAILPORT標題，避免將玩家改名當成原始COLONY行命中。正式完成審查與矩陣／普查尚待採用。

| Issue | 已採用證據 | 尚存工作 |
|---|---|---|
| #55 | 下拉、名稱、View及G两列68／8色分支驗收保留 | 其他母港／目的地形狀接線總審查，河流實際欄位普查歸屬核對。 |
| #56 | BUY、港口、報表與貿易既有驗收；兩居民正常改派與完整兩行職業標題14GUI／四側、21圖回歸。目標181 v49兩居民／50火槍選士兵有七點四側原版操作證據 | 武裝操作既有證據保留，但v49未新增中文欄位；建造清單捲動仍須核對實際畫面與接線，不能由孤立選單取代。 |
| #57 | 六類150篇及先決條件、164正文与19索引接線、31正常GUI／三側、版本限定六項入口、三個不可達分類與完整要求審查PASS | 已完成並遠端CLOSED；同文地形原始來源強推論保留，不改為新正常命中。 |
| #61 | 六項開局27行、21教學與17版畫接線；正常存讀與五種失敗、自訂／地圖載入及三種版畫審查PASS | 已完成並遠端CLOSED；原始段落及其餘情境未抽樣仍保留，不冒稱全部正常命中。 |

目前正式89e63cae…、156Go／go vet無skip；設定85列，最新建造两欄單列PASS，生成報告保存前84列合併的48本輪PASS、36歷史，普查1956／904／963／89，前次shown全保留，待下一批合併。四Issue仍in_progress，未更改完成範圍。

自訂頁四種設定的正常上、下縮圖改選由[check_goal185_start_settings.py](../../tools/check_goal185_start_settings.py)核對十圖／三側與八個實際值。最初在中間卡片點擊後送Escape的start-settings-lists-gui未開清單，後續退出原版，只作無效探勘；不替代正常設定改選收據。

自訂新世界三欄的正式驗收入口為[check_goal185_custom_settings.py](../../tools/check_goal185_custom_settings.py)，限定六張新GUI與四側，以及14張職業回歸；來源、字級及READY見規格038。

完整兩行職業標題的正式切換、取消與單行回歸由[check_goal185_profession_family.py](../../tools/check_goal185_profession_family.py)核對；DRAFT與READY見規格035。自訂開局正常取證另命中標題、Moderate值及完成提示三處實際缺接線，來源與DRAFT見規格038，不由模板已載入判定#61完成。

六類百科與可見河流的31點正常抽驗由[check_goal185_representatives.py](../../tools/check_goal185_representatives.py)核對。第一份remaining-representatives-gui未正常關窗而缺完整輸入，不採驗；第二份有自動關窗與三側完整重播。View座標縮寫與原住民領土列有實際no-template缺口，與玩家名稱、未抽樣來源分開，不由百科PASS關閉#55。後續先補這些實際接線再核對四項完成條件。

View欄位原始字格／顏色／位置與来源觀測已由私用prepare_view_fields.py、view-fields-observer/fields.jsonl及正常輸入重生；完整原版狀態与原先三側相同。DRAFT候選與源指紋見[規格038的View附記](../spec/038-string-overlay-draft.md)，先做欄位量測，不將Locat尾值猜成遊戲欄位。

兩個View欄位現已來源限定CONFORMED，正式11fe199f…、149Go／go vet、新正常10GUI／四側原版、WAV、存檔及回退通過，只改兩欄、其他7圖不變。獨立入口為[check_goal185_view_fields.py](../../tools/check_goal185_view_fields.py)；26部落容量不算26正常命中，原住民土地與座標尾值不改客體資料。檢視模式城名仍有does-not-fit，下一個窄觀測入口為prepare_view_fields.py的VIEW_OBSERVER_BUILD覆寫与view-city-observer/fields.jsonl，沿此10GUI輸入，不重開讀檔或已完成百科正文。

四種讀檔失敗的正式GUI由[check_goal185_load_failures.py](../../tools/check_goal185_load_failures.py)核對。來源與四欄量測、標題保留的DRAFT→READY→限定CONFORMED見規格035；新正式ed5444ea…、149Go／go vet、新16GUI／四側原版、WAV、存檔與回退通過，只改四框、其他12圖不變。既有SAVEERROR8圖與報表10圖回歸全等；#61其他範圍保留，未關閉。

SAVEERROR修正的新正式收據由[check_goal185_save_failure.py](../../tools/check_goal185_save_failure.py)核對，與較早`--profile save-error`保留的英文FAIL分開。規格035現已來源限定CONFORMED：正式f39336c6…、148Go／go vet、新8GUI三側及舊前端同輸入通過；只改錯誤框、其他7圖不變，完整原版／WAV／存檔及回退一致。其他讀檔錯誤仍待驗，不以此關閉整個#61。

接續LOADERROR正常檔案缺失探勘已取得三GUI與三側相同完整原版終點；它也把檔名當術語而仍英文。來源、原始片段與退出行為見[規格035的LOADERROR DRAFT](../spec/035-dialog-overlay-draft.md)。本機play_load_error.py／replay_load_error.py依正常清單檢查點移走並恢復私用副本，check_load_error_gap.py獨立核對；原版按Return後結束，不按腳本預設強行返回選單。存檔標頭無效副本的magic探勘被清單排除，未驗到LOADNOT。下一步處理已證實的LOADERROR檔名與欄位量測，再確認其餘錯誤及三項原範圍。

使用者2026-10-08指定完成#55、#56、#57、#61。這輪先重生必要正常GUI，現行限定檢查器為[check_goal185_remaining.py](../../tools/check_goal185_remaining.py)。`closure-pedia-v1/`的22點與中文／原文／缺字模三側已通過：六項百科選單環繞、單位20正文、F1海洋頁、空槽返回與正常讀COLONY03、關百科後地圖城名恢復。雜項與額外地形仍未完成，不用這22點關閉整個Issue。

報表城名A已由使用者選定，DRAFT→READY→限定CONFORMED見[規格038的2026-10-08附記](../spec/038-string-overlay-draft.md)。`closure-report-prototype/`三欄各173個預設名均容納；三處新增像素限定安全區、其他23圖相同，四側原版狀態／WAV／存檔全等。正式來源完成147項含子項Go測試及go vet，二進位baa1eac772f2bc9cee264942813a8915b6af6faba080f3c0bc70dad93b9beee8；新正常10GUI、三側與舊前端同輸入通過，只改三處城名、其他7圖不變。以`check_goal185_remaining.py --profile reports`重跑。

接著取得#61的新真實缺口：唯讀私用存檔目錄的正常儲存失敗，原版SAVEERROR正常顯示，已載入譯文的檔名變數被當成術語而回英文。三側9GUI、完整原版／WAV／存檔與回退一致，但中文顯示FAIL；`--profile save-error`故意回1。後續先按[規格035的DRAFT](../spec/035-dialog-overlay-draft.md)做來源限定檔名原型與字級量測，再審READY。不重新翻譯已有譯文，不放寬一般變數守門。

接線診斷另已確認708個顯示詞中697個由字串／海上詞典命中；Moderate、Cooperation、Conquest由專屬欄位處理，四個預設玩家名按既定規則保留，三個冠詞刻意省略，Land有兩種語意而只在已驗路線場景處理。實際載入164個百科正文與全部教學模板，存讀檔五種錯誤的模板也已按原始偏移找到。載入模板不證明顯示正確，SAVEERROR即為反例。雜項、額外地形、其他港口單位標題及剩餘正常情境仍待完成。

新局正常手動存檔與新行程讀回的接續檢查器為[check_goal185_newgame_save.py](../../tools/check_goal185_newgame_save.py)，收據留在本輪私用證據根。

接續收尾的同框正文保留問題見[規格048](../spec/048-dialog-choice-body-retention.md)，已限定CONFORMED。

接手後的 EMS 同頁映射修復見[規格047](../spec/047-ems-alias-coherence.md)，已限定 CONFORMED。下方首次 FAIL 與 Issue 審查保留當時證據，最新結果見本頁收尾附記。

本輪入口為`workplace/reports/goal185-player-experience/`；摘要回填[CONTEXT](../../CONTEXT.md)及[WORKLOG](../../WORKLOG.md)。

其餘新收據透過[欄位登錄檢查器](../../tools/check_goal185_registration.py)接入矩陣；它先重跑各項既有驗收，再只回報原驗收已核對的訊息鍵、原文與安全區，不採同文TERRAIN23或伴隨事件提高完成數。

歷史收據缺失時的普查併列依[規格049](../spec/049-census-history.md)審查。42列本輪檢查器PASS與36列僅歷史證據分開，不把檔案缺失當成產品缺接線。
既有[63列驗證矩陣](../verification-matrix.md)及[普查](../text-census.md)保留，不以本輪少數抽樣宣稱全部文字已顯示。

## 遊玩結果

2026-10-09續查多人口：city-more-v18的單居民職業選單不能單獨證明多人口；正常COLONY03新畫面已有100% (2)指標，仍需與原版數值／同狀態核對。屋頂拖放與駐軍拖到工作格沒有觀測到加入，城內反白後回世界仍選船，B命令作用於Caravel而未驗Join Colony，這些探勘不作加入／建第二城完成證據。第二次點駐軍取得職業選單，整則翻譯成功但折行被當兩選項而仍英文；現已依規格035限定CONFORMED。正式4cf2b7d3…、153Go／go vet無skip，新9GUI／四側完整原版、音訊、存檔及回退PASS；只改標題安全区，其餘八圖及選項區相同，正常取消無殘字。入口[check_goal185_profession.py](../../tools/check_goal185_profession.py)，矩陣第80列獨立PASS。此驗收只涵蓋老手級士兵／政治家兩行組合，其他職業與折行形狀仍需接線審查。

2026-10-09接線總審查：現行正式來源的PEDIA載入器以原版完整及片段SHA-256核對164篇正文；19個PEDIA索引／概念名單行均進入字串詞典。私用`connection-audit/pedia-connection-audit.json`PASS，SHA-256 b4a3117552389ef59467ef47425c6fd3eeee11ad6c54e7684cc745de3c813157。正式啟動器呼叫addPedia，正常六類150篇既有驗收與本輪31GUI代表抽樣保留。額外同文地形仍是未觀測原始來源，不能改列shown；Miscellaneous／Complete其他入口仍屬原版oracle未知，正常六類選單邊界已驗，不單凭名稱或缺正文鍵判定不可達。

同輪教學／版畫審查：正式addCorpus呼叫載入19個TUTORIAL及TUTNOLUMBER／TUTNOSPACES，共21模板；字串層已驗來源的WOODCUT表有17個非空標題與譯文。私用`connection-audit/start-connection-audit.json`PASS，SHA-256 3fc1c56f7983aa1bf43c65bdccf85cceca688ff10b16cfc4c6e0e4eb773ea2b1。這是來源與呼叫接線審查，不能算21或17次新GUI命中；正常新局存讀20GUI、五種檔名錯誤及既有教學／三種版畫抽樣仍為畫面證據。

矩陣其餘11列已由欄位登錄檢查器重跑并加入設定，共78列；本輪可重驗42列PASS，35列目錄缺失加上text-model依賴缺失共36列僅歷史證據。報表併列正在依規格049驗證，不把36列記成新PASS，不以收據缺失重開已完成接線。

報表併列隨後依規格049限定CONFORMED：正式42列守門及反例通過，普查1953項／898已顯示／966待驗／89不可達，其中270可重驗、628僅歷史，已回填docs。首次200秒逾時保留為環境失敗，600秒有界重跑通過。新正常離港一格另確認G兩列的Jamestown變為68色可選時，現行限定8色守門回原文；這是實際顏色分支缺口，正補原始字格／色層證據，不由普查數字判定四項Goal已完成。

G兩列可選分支依規格035原型三側與27px量測已READY，正式新GUI懸停／取消驗收入口為[check_goal185_coast.py](../../tools/check_goal185_coast.py)，收據留在`coast-formal-*`，正式驗收前不稱CONFORMED。

2026-10-09返歐文字已按規格035／038限定CONFORMED。新正常14GUI／四側同輸入，只有目的地／航行／抵達三張核准區改變，其餘11張相同，原版、音訊、存檔及回退全等；港口三列11張與四列13張回歸也全等。航程22px、兩列目的地27px，灰色保留；同色同位置重印的偽描邊已限定修正，v1視覺失敗保留。153項含子項Go及go vet通過，無skip。正式入口[check_goal185_voyage.py](../../tools/check_goal185_voyage.py)，私用`voyage-formal-*`與摘要c5963bf0…；其他G清單形狀／名稱仍回原文，192組容量不算正常命中。四個Issue仍待範圍總審查、其餘新收據登錄與普查重算。

2026-10-08返歐文字窄觀測已取得三整串與兩列G目的地的墨跡／cap／色／RAM來源，規格038新增DRAFT，證據`voyage-fields-observer/fields.jsonl`。Go To London為cap5／149，兩個頂列cap5／149且有原版描邊重印；G清單London為正常68、Jamestown停用8，標題Y82與貿易編輯舊欄不同。尚未以此新增正式語意或關閉Issue。

2026-10-08帶貨港口分支已從健康正常存檔與27噸毛皮裝貨／返歐路線取得。重啟COLONY00後，四列完整模板被誤當正文，按規格035完成DRAFT／原型／READY並接正式來源；正常正式入口為[check_goal185_port_four.py](../../tools/check_goal185_port_four.py)，私用收據`port-four-formal-*`。旅程中另命中三個整串缺接線：Sailing For London、Now Arriving In London與Go To London；目前只列實際缺口，未猜補正式行為。原關窗截斷JSON保留為失敗，腳本已補程序退出與完整輸出核對。

2026-10-08碼頭資金不足續驗：正常購船後種子碼頭單位只有搭乘下一艘船預約，拖曳及取消預約未取得帶貨四列，不冒稱登船。取證另發現兩種六列的色8裝備行被辨識器拒絕，規格035由原型、READY至限定CONFORMED。正式入口為[check_goal185_port_dim.py](../../tools/check_goal185_port_dim.py)，新13GUI／四側與新11圖船隻回歸PASS，154Go／go vet通過；原版、WAV、存檔與回退全等，只改五張六列安全區，其餘8圖不變。三項裝備灰色逐行保留，點灰列及取消／返回保持原版行為；八種色層組合與九位數只驗容量。摘要8338305e…，矩陣第65列及欄位守門e673e819…PASS；普查只採完整標題，不把六列子集提升完整12列來源。完整指紋見規格035，全Goal仍在進行。

2026-10-08接續港口正常取證：使用目標181 v192正常購船後存檔，冷啟動至歐洲、選輕帆船並取消，共8張GUI後正常關窗。兩個實際接線缺口為船隻頂列與EUROPESHIPOPTIONS三列操作；譯文已有，分別進規格038及035的DRAFT，再由原型v3審READY及正式限定CONFORMED。正式驗收入口為[check_goal185_port_units.py](../../tools/check_goal185_port_units.py)，新11GUI與四側收據位於`port-unit-formal-*`，摘要816e8374acf82abbb5a2952ff7d4d9327d23c756c46b1074f4a801131e318dbd。155項含子項Go及go vet通過，實際頂列22px／三列30px；僅四张選船／懸停畫面改變，其餘7圖相同。矩陣新增船隻列且單列PASS，欄位守門摘要5b9bf1a1002cdcda6646a45784b9e3bbfdda1d8f912f2ac88b48843cbfda58de，全矩陣／普查尚未重算。三列子集不提升完整四列來源，不把96項容量投影算成96次正常命中。帶貨四列仍未接，四項Goal保持進行。地圖雙語城名在View正常畫面已顯示，不因單色觀測器未收離屏事件而重新開啟。

| 路徑 | 結果 | 證據與限制 |
|---|---|---|
| 既有正常存檔 | PASS | 從主選單載入COLONY03，進歐洲港口、開招募清單及取消、回世界、進Jamestown、開職業清單及選任、返回世界、數字鍵盤向東移動、GAME選單正常存檔。15張同步GUI與中文重播逐像素相同；中文、原文與缺字模三側每點RAM／索引／色盤及終點完整CPU／RAM／VGA相同，回退圖逐像素等於原文。 |
| 存檔後重啟讀回 | PASS | 正常關窗、啟動新行程、載入新COLONY00。實拍仍為1496年春季、1000$、船在(55,30)、行動2。新舊存檔雜湊及原版控制組一致，原始COLONY03未改。 |
| 音樂供給 | 限定PASS | 200M步、24.143秒單調時鐘消費，6個原版音樂命令，音樂缺樣0、丟棄0；48kHz雙聲道24.14秒輸出非靜音。觀測副本與正式程式完整原版狀態及原始WAV全等。數位音效缺樣1322392 bytes另記，尚未音效卡或人耳驗收。 |
| 英國發現者新局 | FAIL | 第一張開場字幕之後，載入LEVN0002.PIK時提前停止，未進入可操作世界。原版DOS未正常退出，CPU進入Halted。中文、原文、診斷副本及已發布v.1.0.2的終點狀態全等；關閉數位音效仍停在相同步數。 |

上述正常操作只涵蓋一次既有存檔會話。沒有以注入座標、修改存檔或跳入內部常式取代正常入口。觀察截圖時暫停自有前端，下一操作恢復；不修改客體記憶體或時間。GUI檢查與連續牆上時鐘音訊驗證分開，操作記錄的等待時間不當作整場即時效能。

兩側均由同一dosgolem冷啟動，DOS.Now預設全0、初始PIT ticks為0，再依相同指令與輸入推進虛擬時間。既有存檔兩側逐位元組相同，保留檔內亂數狀態。沒有重新抽種子、挑選通過結果或假定不同亂數實作的相同seed等價；本輪直接核對相同原版執行器的完整狀態。

### 新遊戲阻塞

工具為`colonization-verification:20260930-r1`、Go 1.26.7、Ebitengine 2.9.9，隔離dosgolem提交`c5953b90a0fc76c57f8dbbe0555f7a85d3198fe8`。位址一律是dosgolem執行時CS:IP或實體記憶體位址，不能當作EXE檔案偏移。

| 等級 | 發現 | 原始定位 |
|---|---|---|
| confirmed | 真視窗新局停止於635086794步，DOS.Exited=false、CPU.Halted=true；原文控制組及已發行版重現同一完整狀態。 | `newgame/gui.inputs.json`、`newgame/gui.json`、`newgame-control/run.json`、`newgame-release/run.json`、`trace-exit-v4.json`。 |
| confirmed | 停止前AH=48h申請0FA1h段，即64016 bytes，回AX=8、CF=1、BX=0C05h。快照中最大空塊49232 bytes，另一空塊36416 bytes，空間不連續。 | 執行時`D27E:015B`；`dos-memory-calls-v4.jsonl`、`before-failure-v4.memory`的MCB鏈。 |
| confirmed | LEAVE後SP指向零值區，RETF跳入0000:0000；後续REP MOVSW覆蓋中斷向量表，最後執行HLT。 | 第635059587步`D036:3F9E`、第635059589步`0000:0000`；第635060009步`0E2D:0FE4`寫實體0x1C起。見`before-copy-ring-v3.json`、`low-writes-v4.jsonl`。 |
| 強推論 | 記憶體申請失敗與後續錯誤流程相關。 | 時序與暫存器收據支持，但尚未證實碎片形成原因、失敗處理與堆疊損毀的完整資料流。 |
| 未知 | 最初原因及修法。 | 尚未證明DOS配置器、客體MCB、原版錯誤流程或其他服務何者有錯。不能任意增加記憶體、忽略HLT、重試亂數或修改原版規則。 |

目前程式SHA-256：`a10dbd94e357d56c8fbaec55ea189ebb6e2ad75cfd14ad58542cc3100aca4f6e`。
原版`OPENING.EXE`：`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`。
原版`VICEROY.EXE`：`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`。
正常操作輸入：`f99dcacd8b737cc0f3ada4089b3959e994f1e5d1a8e7f899b185d653aa5fc0f7`。
新局輸入：`94d02cb2f671058e471281cea937bd63ce036e44fc102475e4e0785bcfb8d4d3`。
新存檔COLONY00：`a7bf94b2d8953f491848dc30dd2c5b972b0244bff6152eeefac4228f3fff2652`。
原始COLONY03：`d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77`。
原版CONFIG.COL：`65855145fba299180f2dd6384d7ab9ceac4ae5dd7594d68772d4c8bad609cf43`。
已發行v.1.0.2二進位：`91c035367143f0d83b5e1e0adc151fc4fdb83f815e31696c2511cafd4e55f4db`。
`source-metadata.json`另列PSOUND.COL、COLDIG.BIN與兩張開場圖的雜湊；`playtest-review.json` SHA-256為`e739439452cbbe98993d76b78e0969ff68da5d3094da78f01090a82e81fa416d`。

## Issue關閉審查

主機`gh auth status`成功後，直接讀遠端八筆OPEN Issue，未以本機鏡像代替遠端現況。依2026-10-04使用者的最新決定，譯稿完成與代表性抽樣分開判定；974筆pending不等於974筆缺譯，也不要求重新開啟已有驗收。

| Issue | 本輪能否關閉 | 尚存缺口 |
|---|---|---|
| [#53](https://github.com/wicanr2/colonization_cht/issues/53) 完整交付 | 否 | #55～61仍未完成；新遊戲停止已在v.1.0.2重現。音效卡、人耳及macOS真機未驗。63列既有中文矩陣PASS不能代表新局遊玩PASS。 |
| [#55](https://github.com/wicanr2/colonization_cht/issues/55) 地圖與名稱 | 否 | 本輪移動與城名抽樣通過，其他名稱、地形與選單情境仍有未驗或接線待確認。 |
| [#56](https://github.com/wicanr2/colonization_cht/issues/56) 殖民地與港口 | 否 | 核心操作及碼頭既有驗收保留；三個報表城市名仍原文，其他港口單位標題與剩餘情境未完成。 |
| [#57](https://github.com/wicanr2/colonization_cht/issues/57) 百科 | 否 | 六類150篇正文及22個先決條件已有驗收；Miscellaneous與額外地形情境仍未完成。本輪不重跑已驗文章。 |
| [#58](https://github.com/wicanr2/colonization_cht/issues/58) 原住民與外交 | 否 | 既有和平／學習抽樣有效；其他外交與局勢分支尚缺代表性正常玩家收據。 |
| [#59](https://github.com/wicanr2/colonization_cht/issues/59) 戰爭與結局 | 否 | 尚無本Issue的戰鬥、獨立戰爭與結局代表性正常玩家驗收。譯稿已完成不等於這些路徑已驗。 |
| [#60](https://github.com/wicanr2/colonization_cht/issues/60) 一般訊息 | 否 | 既有原住民選項與通用接線保留；剩餘事件類型的排版及局勢抽樣未完成。 |
| [#61](https://github.com/wicanr2/colonization_cht/issues/61) 開局與存讀檔 | 否 | 本輪正常存檔、重啟讀回已通過；新局有阻塞，其他存讀檔結果、教學及事件類別仍有未驗範圍。 |

本輪未關閉、建立或留言Issue，未commit、push或發行。先處理新局阻塞，再恢復中文接線收尾；需要新行為時仍走RE→DRAFT→READY閘門。

## 重跑入口

原版、存檔、畫面與音訊只放在已忽略的本機證據根。`probe.py`留存真正X11鍵鼠操作方法，`actions.jsonl`及`gui.inputs.json`記錄這轮輸入，`gui.shots`記錄實際發布畫面的步數。`replay.py`沿正式啟動器參數、相同初始存檔及相同輸入重播。不要以操作時的Update步數代替畫面步數。

在專案驗證容器中，將證據根掛載到`/out`、原版唯讀掛載到`/game`，使用：

```bash
python3 /out/replay.py 新輸出名稱 existing control
python3 /out/replay.py 另一新輸出名稱 existing zh
python3 /out/replay.py 第三新輸出名稱 existing missing
python3 /repo/tools/check_goal185_playtest.py \
  --reports /out --game /game --output /out/playtest-review.json
```

[`tools/check_goal185_playtest.py`](../../tools/check_goal185_playtest.py)核對凍結的三側GUI重播、存檔、重啟讀回、音訊觀測與新局重現。收據完整時仍以退出碼1報告目前新局FAIL；缺原版明確SKIP77。這個檢查器不把已知阻塞轉成PASS，也不取代原版執行或人耳驗收。

## 接手收尾：EMS 修復，2026-10-07

同頁多處映射的合成契約在 dosgolem c5953b9 三項 FAIL；原型修復後通過，跨頁、四處別名、快照、Close 及三套核心回歸也通過。正式通用修復提交82a14b2，補丁與通用規格198保存在規格047入口，shared dosgolem未改，upstream推送DISABLED。

正式程式f4042b3d…已完成新局25張GUI／三側同狀態與原文回退、既有15張GUI／兩側及舊GUI完整狀態／存檔／原始WAV回歸。正式二進位另已在真視窗進世界並移動船隻，完整關窗收據存在；該新會話未成功執行手動存檔，不能採計誤命名的存檔截圖。既有存讀檔回歸不受影響。

修復解除原來635086794步停止，沒有修改原版、亂數或規則。原先「最初原因未知、尚未修復」是首次驗證狀態，現由上述標準EMS契約及同狀態收據補足。記憶體碎片形成未逐段逆向，不再據此開啟全部配置器考古。

公開v.1.0.2仍為舊版，未發行本修復；#53及#55～61仍OPEN，其他接線、版面與未抽樣範圍保留。普查882／1945與既有63列矩陣不增加，也不將舊矩陣宣稱為本次新後端全矩陣重跑。

新檢查器：[check_goal185_ems_repair.py](../../tools/check_goal185_ems_repair.py)。本機彙整為 `ems-repair-review-final.json`；在驗證執行期r2將原版唯讀掛到`/game`、專案唯讀掛到`/repo`、本輪證據根掛到`/out`，執行：

```bash
python3 /repo/tools/check_goal185_ems_repair.py \
  --reports /out --game /game --output /out/ems-repair-review-final.json
```

原Go驗證映像及鎖定基底在重播完成後已不存在，原因未查明。[執行期r2](../../tools/Dockerfile.verification-runtime-r2)已恢復GUI／Pillow與收據驗證，沒有Go編譯器；Go建置工具鏈仍需從原可重建來源恢復。新GUI有界自動關窗，收尾Docker清理見WORKLOG。


## 2026-10-08 接續：建置恢復與新局手動存檔

直接沿用共用主機的固定hr-go-ebiten映像1430a2cf…，Go1.26.7、Ebitengine2.9.9、Xvfb與Pillow9.4.0已核對。`restored-go-build/`由目前正式來源離線組裝，Go／go vet通過；二進位仍為f4042b3db4b808e8d768502b5a6b521dcfbf1e104b3e6cd59f60f3ee4fafa3e6，沒有改正式玩法或為恢復工具另建重複映像。Dockerfile.verification已記錄替代來源。

`newgame-save-20261008/`另有新正常GUI：英國發現者新局、向西移動、用(G)GAME選單手動存為COLONY00、成功提示及回世界，正常關窗後新行程`reload-newgame-20261008/`載入同存檔。滑鼠按下保持兩個Update後才釋放，GAME用實際已驗的(96,12)點擊，未沿用上一輪誤點高海的按鍵腳本。

20張新GUI與正式中文重播逐像素相同；中文／原文／缺字模三側每個取樣RAM／索引／色盤、完整終點CPU／RAM／VGA、原始WAV及COLONY00／09逐位元組相同，缺字模回原文。新COLONY00 SHA-256 a043119cd32ca0c3aa55be48d632f03c6b07e2fca04cdf5caa3d1ed27dadeef4。新行程讀回與原文控制組完整狀態及原始WAV全等，載入前後存檔不變。這補足新局修復後的手動存檔／讀回，不改寫上一輪失敗收據。

彙整`newgame-save-review.json`由[新局存讀檔檢查器](../../tools/check_goal185_newgame_save.py)重生。輸入SHA-256 bfaf3f2caf06d804bdf4d79376eb057c15fa4a5e157cb7df24a187aa2b1a9e74，重啟讀回輸入634d541f9fae710f7906d72ca31f7a4dff72215d8e168c413bc3ed19e03dc67c；原版雜湊沿規格047，DOS初始時鐘／seed條件與先前一致。沒有注入快照、座標或修改原版。

高海正文已有來源命中，選項反覆重繪會撤銷仍可見的正文。接續原型與閘門見[規格048](../spec/048-dialog-choice-body-retention.md)，尚未正式採用。


## 2026-10-08 高海正文保留收尾

規格048依DRAFT、原型及來源／像素審查升READY後正式接入，現已限定CONFORMED。正文的啟用快照保持不變時，相同身份、安全區與完整選項重繪不再撤銷正文；首次2M步身份守門不變。145Go／go vet、新正常10GUI／四側完整原版／WAV／存檔、正常取消無殘字及原始失敗路徑正式重播通過。正式二進位fe58445e…，詳細來源、字級、指紋與退出條件見規格048。

彙整由[check_goal185_choice_retention.py](../../tools/check_goal185_choice_retention.py)重生。圖片初讀誤以為懸停時正文空白，逐像素與正文矩形指紋全部相同；以直接像素證據勘誤，沒有新增合成器修補。首場GUI因建置整合缺bytes匯入未產生二進位，第二場因不可見X11視窗焦點BadMatch；補匯入並等onlyvisible後沿固定映像乾淨重跑成功，均屬驗證環境／整合問題。

來源與譯文／字模沒有新增，普查882／1945不增加，八項Issue仍未完成，沒有遠端寫入或發行。
