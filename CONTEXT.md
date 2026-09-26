# 目前脈絡

目前真相：[目標152](docs/goals/152-verification-matrix.md)完成 #14：[驗證矩陣](docs/verification-matrix.md)十四列（動態十二、靜態一、回歸一）檢查器全數 PASS，動態與靜態都有原版基線、中文、英文與負例收據；矩陣只重跑檢查器，不重跑模擬。未驗範圍列在矩陣文末。

目前真相：[目標151](docs/goals/151-static-overlay-implementation.md)完成 #13：開場製作名單七個職稱橫幅靜態覆蓋（`--static-credits-a`，規格034 限定 CONFORMED）；真 GUI 不按鍵看完開場，七項各套用一次，人名橫幅與無橫幅畫面不變。

目前真相：[目標150](docs/goals/150-dynamic-overlay-verification.md)完成 #12：海上拼字引擎加入縮字（22～15px）；全部欄位旗標同時開的兩條正常路徑中英同狀態，39 個鍵都套用。

目前真相：[目標149](docs/goals/149-dynamic-overlay-ready.md)完成 #11：規格033 升 READY，涵蓋固定單行、逐字事件列、模板動態行三類。

目前真相：[目標148](docs/goals/148-font-terms-scope-decisions.md)完成 #10，使用者決定：字型維持 Cubic 11；術語以第三波中文版說明書優先；完成範圍為所有可達文字；版面超界時自動縮字到欄位字級 2/3，仍放不下才回原文。

目前真相：[目標147](docs/goals/147-static-overlay-prototype.md)完成 #9：[規格034](docs/spec/034-static-text-overlay-draft.md)靜態覆蓋 DRAFT 與製作名單橫幅原型（正反對照 PASS）。

目前真相：[目標146](docs/goals/146-static-text-inventory.md)完成 #8：靜態內嵌文字清冊六項（開場海圖兩處拉丁字、兩個品牌標誌、製作名單橫幅、未觀測的遊戲標題標誌）；只有製作名單職稱適合覆蓋。普查另發現四處尚未中文化的動態文字（Loading、版本字串、國王接見、GAME 下拉選單）。

目前真相：[目標145](docs/goals/145-coverage-report.md)完成 #7：可重跑的清冊與覆蓋率報表；810 列已抽取且已翻譯（草稿），正常路徑中文實際顯示 73 個鍵，命中但未建檔 17 種字串。

目前真相：[目標144](docs/goals/144-dynamic-text-model.md)完成 #6：[規格033](docs/spec/033-dynamic-text-model-draft.md)動態文字資料模型 DRAFT，三種真實輸出情境驗證通過。其餘大項依 #7→#8→#9→#10→#11→#12→#13→#14→#26→#27 順序處理，#15 封裝最後。

目前真相：[目標143](docs/goals/143-sea-menu-and-status.md)完成 #37：海上選單列、回合訊息與狀態欄在明示 `-sea-status-a` 時以執行期字元圖集拼字顯示中文（規格032 限定 CONFORMED），數值保留原值並隨原版重印更新；詞典目前只含英格蘭開局所見詞，其餘保留原文並記錄缺譯。

目前真相：[目標142](docs/goals/142-first-tutorial-help.md)完成 #36：首則教學提示 `@TUTORIAL1` 只在 Discoverer 難度開局出現；A 版（30px）在明示 `-tutorial-help-a` 時顯示中文（規格026 該則限定 CONFORMED）。正式中文欄位為五十七段。

目前真相：[目標141](docs/goals/141-remaining-build-captions.md)完成 #35：英格蘭十張開場字幕在明示 `-build1-a -build-captions-a` 時全部顯示中文（規格026 字幕部分限定 CONFORMED）；介紹頁後任何按鍵會讓原版在第四張後跳過其餘字幕。`@BUILD1` 撤銷條件已拿掉開檔數（規格029 更正）。正式中文欄位為五十六段。

目前真相：[目標140](docs/goals/140-other-nation-cards-overlay.md)完成 #34：法國、西班牙、荷蘭三張旗卡 A 版在明示 `-nation-cards-rest-a` 時顯示中文（規格022 限定 CONFORMED）。正式中文欄位為四十六段。

目前真相：[目標139](docs/goals/139-third-difficulty-card-overlay.md)完成 #33：第三張難度卡「征服者／普通」A 版在明示 `-third-card-a` 時顯示中文（規格016 第三卡限定 CONFORMED）。正式中文欄位為四十段。

目前真相：[目標138](docs/goals/138-retire-confirmation-overlay.md)完成 #32：退休確認框三欄 A 版在明示 `-retire-a` 時顯示中文（規格028 限定 CONFORMED）。正式中文欄位為三十八段。

目前真相：[目標137](docs/goals/137-options-window-followups.md)完成 #31：遊戲選項九欄在鍵盤快捷鍵、法國／西班牙／荷蘭、讀存檔後開窗三種路徑都正確顯示中文；前端新增預設關閉的 `-scratch` 可寫暫存層供存讀檔。

目前真相：[目標136](docs/goals/136-other-nations-intro-pages-overlay.md)完成 #30：四國首次國家介紹八頁在明示 `-nation-intro-a` 時全部顯示中文（規格025 限定 CONFORMED）。非英格蘭在選國後會停在姓名畫面，需 Enter；真視窗點旗卡要先讓游標停在旗卡上。正式中文欄位為三十五段。

使用者決定（2026-09-25）：姓名欄維持原版英文（#29 完成）；首次國家介紹長文採貼近原版標題34px／正文38px（#30）；退休確認框採 A 三欄34px共同置中（#32）；第三張難度卡與其餘三張旗卡採 A 21／25px（#33、#34）。未完成工作一律以 GitHub Issue 為入口，依編號順序處理。

目前真相：[目標134](docs/goals/134-game-options-rows-ebitengine-overlay.md)已將遊戲選項八列接到正式 Ebitengine，[規格031](docs/spec/031-game-options-rows-a-ready.md)限定 CONFORMED。明示 `-game-options-title-a -game-options-rows-a` 時，英格蘭正常玩家路徑的遊戲選項視窗九欄全部顯示中文；快捷鍵為「(I) 顯示原住民行動」形式。閘門以整組 `0D21:00C6` 268 次讀字事件為權杖，逐列在第一次被改色時擷取當次底圖（奇偶列各兩種），允許 `0CAE:00A8` 在事件中途為尚未印字的列畫反白底圖；游標壓列時暫回英文、不計入同步逾時。中英同輸入原版狀態相同，ESC 撤銷，六項載入負例回英文，真 GUI 真鍵鼠開窗與點擊後的現場截圖和重播逐像素一致。正式中文欄位為二十七段。鍵盤快捷鍵切換、其他國家、存檔後開窗與 help 未驗。

目前真相：[目標132](docs/goals/132-game-options-title-event-and-overlay.md)已將無快捷鍵標記的遊戲選項標題 A／34px「遊戲選項設定」接到明示 `-game-options-title-a` 的 Ebitengine 視窗；[規格030](docs/spec/030-game-options-title-a-ready.md)只在此版、此欄、英格蘭正常玩家路徑限定 CONFORMED。閘門是當次 `0D21:00C6` 32次讀字、`0D21:012C` 319點改色、標題局部印前／印後底圖與真 VGA 同步，不用整張畫布 SHA。1280M 中／英同原版狀態，ESC 離窗撤銷，游標遮擋暫回英文，缺譯／重複鍵／過長／錯字模／缺字模載入回退；真 GUI 真鍵鼠從冷啟動走到標題，1280M 現場 PNG 與重播逐像素一致。此為第十九個**需啟用旗標**的正式中文欄位。[規格027](docs/spec/027-game-options-window-draft.md)其餘八列仍 DRAFT、仍英文；八列 `~` 快捷鍵呈現已由使用者決定（見目標133）。[目標131](docs/goals/131-game-options-title-a-runtime-gate.md)的真 VGA 晚一幀與 ESC 失效證據已由目標132吸收。

目前真相：[目標130](docs/goals/130-build1-ready-and-ebitengine-overlay.md)已將固定英格蘭首張 `@BUILD1` A／38px 接到明示 `-build1-a` 的 Ebitengine 視窗；[規格029](docs/spec/029-build1-caption-window-ready.md)只在此版／此欄／此正常玩家路徑限定 CONFORMED。真視窗82M字幕中、86M離頁後、120M後續的中／英文原版狀態一致，缺字模、缺譯、重複鍵、游標遮擋均回退英文；原有十七欄727幀不退步。此為第十八個**需啟用旗標**的正式中文顯示欄位，非整組字幕完成。`Game Options` 九欄 A（標題34px、八列25／28／28／25／28／28／27／28px）已定案，標題已由目標132限定完成，[規格027](docs/spec/027-game-options-window-draft.md)其餘八列仍 DRAFT、仍英文；其餘字幕及 help 所在[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)也仍 DRAFT，help 正式零則。原版像素／字型／完整收據只在忽略的 `workplace/`，不更新正式截圖或對外包。

補驗：以實際開啟的 Ebitengine 玩家視窗、真鍵鼠走到84M時擷取的本機截圖，與已驗82M字幕中文重播圖逐像素相同；[規格029](docs/spec/029-build1-caption-window-ready.md)已納入現場畫面收據。本機圖含原版像素，仍不入Git。

歷史訂正：[目標129](docs/goals/129-build1-runtime-frame-lifecycle.md)證實 `@BUILD1` 61字元與1,040點底層畫布寫入，但其第538幀只證底圖完成；目標130補看真 VGA，首個安全幀是該獨立路徑第544幀。原本「字幕仍英文、正式十七段」是目標129當時狀態，已由本檔首段的新限定 CONFORMED 收據更新，不可反向覆蓋現況。兩條輸入路徑印字步數不同，須各自引用。

更新：2026-09-25；本檔只記目前真相，逐輪證據見 [RESEARCH-LOG.md](RESEARCH-LOG.md)，歷程見 [WORKLOG.md](WORKLOG.md)。

最近完成：[目標128](docs/goals/128-a-layout-decisions-and-build1-runtime-gate.md)已獨立鎖定 `@BUILD1` 開場字幕 A（38px、實際墨跡高35px、共同置中，淡黃字與暗影），排除42px B；`Game Options` 九欄 A（標題34px，八列25／28／28／25／28／28／27／28px），排除較大的 B。現行 TSV 重烘與原版／Ebitengine 本機對照通過；`@BUILD1` 固定雙重播／無監看控制在85M拒絕、90M至195M已驗取樣候選、200M換頁拒絕。此為 DRAFT 守門候選，尚無真視窗逐幀中文、當次事件權杖或缺譯回退；規格026／027均未升 READY，字幕與九欄仍英文，正式中文十七段、help 零則。下一步由字幕事件生命週期與逐幀可逆補片接續，不把本輪 A 套到其他字幕或選項以外畫面。

目前真相：[目標127](docs/goals/127-retire-source-to-print-dataflow.md)以兩種互斥原版監看追退休確認框來源：`GAME.TXT` 三筆32 byte實際被解析器讀取，解析區31／32筆變更寫入、高位址常駐字串35筆寫入、實際印字31個可見字元中30筆近端變更寫入與31筆讀取有可重播配對；雙次冷啟動、無監看控制與獨立正反例通過。同值寫入回呼的兩個 byte 案例及跨重用緩衝完整唯一歸屬不冒稱閉合，[規格028](docs/spec/028-retire-confirmation-overlay-draft.md)仍 DRAFT；退休框 A/B 版式另待使用者選擇，正式中文十七段及 help 零則不變。使用者再次確認的第一張國家旗卡 A（21／25px）已由目標099正式驗收，本輪不重做、不外推。

目前真相：[目標126](docs/goals/126-retire-confirmation-three-field-overlay.md)已把正常玩家 `Retire` 確認框問句／Yes／No 的原版 DOS 讀取、實際印字、逐欄首字前底圖與安全區量成可重播收據；A（34px共同置中）與 B（問句38px、按鈕34px，保留原版左起點）兩套本機 Ebitengine 原型均通過獨立逐像素驗證。這兩版**尚待使用者擇一**；中間搬運的有界新證據見目標127，完整唯一歸屬及真視窗動態守門仍未閉合，[規格028](docs/spec/028-retire-confirmation-overlay-draft.md)保持 DRAFT，三欄仍是英文，正式中文十七段、help 零則。目標125已排除固定 `Retire` 後另開新局作為 help 入口，不把本框原型算成 help 進展。

目前真相：[目標125](docs/goals/125-tutorial-hints-persistence-and-help-entry.md)已檢驗正常玩家切換 `Tutorial Hints`，經 `Retire` 正常退出並另開新局：當局未點／點一次／點兩次的圖示為47／149／47，但三支暫存層檔案逐 byte 相同，第二次冷啟動重開選項時原版完整狀態合流、圖示均為47；固定取樣與監看仍未見首則 help。這只排除該固定跨次路徑的選項可見效果，未證其他入口或存檔讀取語意。[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)仍 DRAFT，正式中文十七段、help 正式顯示零則。下一個安全切片是從其他正常玩家介面或當局可見觸發找首則原版印字，不再假定 `Retire` 是同局重開。

目前真相：[目標124](docs/goals/124-gameplay-keyboard-window-route.md)已把真 Ebitengine 視窗的 Esc／四方向鍵接到 dosgolem 具名 BIOS 鍵佇列。英格蘭海上左移與 `Game Options` Esc 離頁經玩家真鍵盤、英文同輸入控制、完整原版狀態、少一鍵反向對照及失焦負例驗收；[規格024](docs/spec/024-window-keyboard-input.md)僅此輸入通道限定 CONFORMED。右／上／下在遊戲中的效果、首則 help 與新中文覆蓋未驗；正式中文仍十七段，help 正式顯示仍零則。

最近完成：[目標123](docs/goals/123-retire-confirmation-and-help-route.md)已用原版滑鼠分別點 `GAME → Retire` 的 Yes／No：No 返回海上畫面；Yes 進入分數頁，再按 Enter 到名人堂、再按 Enter 使原版正常離開 DOS，不在同一次執行內回到新局。四分支雙次冷啟動、無監看控制及獨立正反例通過。這不證其他路徑沒有 help；[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)仍 DRAFT、help 正式畫面零則。第一張國家旗卡 A（21／25px）已在目標099正式驗收，本次再次選 A 不重做。

最近完成：[目標122](docs/goals/122-game-options-nine-field-state-guard.md)把 `Game Options` 13支原版分支、85個取樣狀態整理為九欄矩陣。第2列點擊時六欄、第8列點擊時七欄在固定1,325M步可做本機部分中文原型；兩狀態各有原文控制與 A／B 真 Ebitengine 圖，四張中文圖逐像素驗證通過。游標遮擋、底圖變動逐欄保留原文，ESC 離頁全失效，按下／放開細相位一律未知。這只完成 DRAFT 證據與可丟棄原型；[規格027](docs/spec/027-game-options-window-draft.md)未升 READY，遊戲選項九欄仍英文、正式中文仍十七段。此視窗 A／B 字級及第三張難度卡 A／B 都待使用者各自決定；第一張旗卡 A 早已正式驗收，不重做。

最近完成：[目標121](docs/goals/121-third-difficulty-card-layout-and-guards.md)以目標120固定原版來源、真譯稿和字型，製作第三張難度卡片「征服者／普通」的本機 Ebitengine A（21／25px）與 B（25／29px）逐欄可逆預覽；原文控制及兩版中文逐像素檢查均通過，錯版／錯鍵／缺字／溢出／底圖變造等負例拒絕。另以 dosgolem 正常滑鼠重播證實只遮上欄、只遮下欄、跨欄及移開三種相位，各雙次冷啟動與無監看控制一致。這是可丟棄版面與 DRAFT 守門候選，**不是**第三卡正式中文：A／B 尚待使用者選定，規格016仍 DRAFT、正式十七段不變。第一張國家旗卡 A（「英格蘭：」21px／「移民」25px）早已由目標099正式驗收，本輪再次回答不重做，也不替 Game Options 定字級。

最近完成：[目標120](docs/goals/120-third-difficulty-card-output-evidence.md)沿已驗真視窗難度頁前綴，以隔離 dosgolem 正常滑鼠點擊左下第三張卡片 `(55,145)`，雙次冷啟動與無監看控制證實原版 `NAMES.TXT:0xC22`／`LABELS.TXT:0x8B8` 的 `Conquistador`／`Moderate` 經載入、執行期讀取與印字畫布呈現；兩行墨跡分別205／116點、原版高5／6像素。僅移鼠／不點選均未印第三張卡。兩筆「征服者／普通」譯稿仍為草稿，逐欄字級、游標／按鍵回退及 Ebitengine 正式中文未驗；規格016仍 DRAFT、正式中文仍十七段。第一張國家旗卡 A 版先前已完成；本次回答不替 Game Options 的 A／B 字級定案。

最近完成：[目標119](docs/goals/119-game-options-click-phase.md)沿正常玩家路徑對遊戲選項第一／第八列的按下與放開插入細相位取樣，各有雙冷啟動及無監看控制。底層畫布在按下後1,302,001,000步仍未改、1,302,100,000步已改；放開後1,303,100,000步仍未新增變化、1,303,500,000步各列圖示中心四點變色。只得到有界窗口，不宣稱精確首條重繪指令、核取啟用語意或全部列。探針預設關閉時與舊目標117報告逐 byte 相同；規格027仍 DRAFT，九欄仍英文、正式中文仍十七段。使用者尚未替此視窗選 A／B 字級。

最近完成：[目標118](docs/goals/118-game-options-remaining-rows.md)沿同一 dosgolem 正常玩家路徑，補齊第2／3／5／6列點回第1列的雙冷啟動、無監看控制及獨立正反例。四列在固定同焦點終點各只剩本列圖示中心四個原版索引像素差異；加上目標117及111，八列已有這個**穩定相位**矩陣，但按鍵瞬間與核取語意未證。規格027仍 DRAFT，`Game Options` 九欄仍英文，正式中文仍十七段；此視窗 A／B 逐欄字級已向使用者呈現候選，尚未代選。

最近完成：[目標117](docs/goals/117-game-options-same-focus-checkmarks.md)以正常玩家路徑完成第4／7列點擊後回第1列的雙冷啟動及無監看控制；同焦點終點各只差原版圖示中心四點，第4列47→149、第7列149→47，其他畫素與原文不變。這只證明固定抽樣的焦點／圖示分離，不能推啟用語意或全部列；[規格027](docs/spec/027-game-options-window-draft.md)仍 DRAFT、九欄仍英文、正式中文仍十七段。使用者再次確認的第一張國家旗卡 A（21／25px）先前已由目標099完成，未重複改動。

最近完成入口：[目標116](docs/goals/116-game-options-selection-and-exit-phases.md)：
沿已驗正常滑鼠開啟 `Game Options` 路徑，第一／末列純移鼠
只改游標合成畫面160點，底層畫布不變；兩者移到同一框外
位置後畫面合流。既有原版實際點擊末列比純移鼠多3,407點
底層畫布差異，含焦點與核取狀態，不能混稱單一選取效果。
ESC 在1,351M由原版取走，1,375M視窗消失、回海上畫面。
三分支各雙冷啟動／無監看控制，獨立正反例通過；九欄仍是
英文，規格027 DRAFT，正式中文仍十七段。

最近完成入口：[目標115](docs/goals/115-game-options-source-chain-correction.md)／
[目標114](docs/goals/114-game-options-print-buffer-dataflow.md)：
目標113的「零筆寫入」是監看器單一 active range 被後設畫布範圍覆蓋，
非原版負證據。修正後九欄150個可見字元均有先前同址、同值的印字
緩衝寫入；九段高位址 RAM 的142個原始正文 byte 各有變更寫入。
雙冷啟動／無監看控制及獨立正反例通過。DOS 解析緩衝至高位址 RAM
的中間邊、1筆格式化來源讀取仍未閉合；[規格027](docs/spec/027-game-options-window-draft.md)
保持 DRAFT，正式中文仍十七段，遊戲選項九欄仍原文。

最近完成入口：[目標113](docs/goals/113-game-options-background-and-preview.md)：
沿目標112的正常玩家九欄來源收據，已由 dosgolem 雙冷啟動擷取各欄
印前底圖，並以固定 Cubic 11 與真 TSV 製作本機可丟棄的 Ebitengine
原文／A／B 對照；逐像素驗證安全區外零變更。解析緩衝至印字緩衝
的中間來源邊、其他反白／游標相位仍未閉合；[規格027](docs/spec/027-game-options-window-draft.md)
維持 DRAFT，正式中文仍十七段，遊戲選項九欄仍為英文。

使用者本輪再次確認第一張國家旗卡選 A（「英格蘭：」21px、
「移民」25px），排除 B 的25／29px；此決定先前已在目標099及
規格021限定實作並驗收，本輪沒有重複改動旗卡或正式截圖。

目前工作入口：[目標112](docs/goals/112-game-options-chinese-display.md)：
沿目標111已驗的正常滑鼠路徑，追 `Game Options` 視窗標題與八列
原版來源、逐欄繁中版面及正式 Ebitengine 顯示閘門。目前尚未
新增正式中文欄位；原有十七段及 help 零則不變。
目前已用隔離 dosgolem 雙冷啟動／無監看控制，驗證九段
`GAME.TXT:0x4CD–0x566` 原始文字由 DOS 讀至線性
`0x2B0CF–0x2B176`，原版 `0E2D:1F76` 隨後逐 byte
讀取168 bytes；`0D21:00C6` 的九段印字及1,300M
索引畫面另經獨立正反例核對。九欄草稿註記已訂正，原版
7／8像素墨跡與候選安全矩形見[規格027](docs/spec/027-game-options-window-draft.md)。
解析緩衝到高位址 RAM 的中間逐 byte 搬運、反白／游標
回退及中文字級尚待驗；印字緩衝最後直接寫入和逐欄印前底圖
已由目標113–115補證。因此規格仍 DRAFT、九欄仍原文。

最近完成入口：[目標111](docs/goals/111-tutorial-hints-state-and-first-help.md)：
`Game Options` 中未點／先點 `Tutorial Hints` 後皆把焦點
移回第一列；1,375M的原版畫面只差最後一列圖示中心
四點，色號47→149。兩條分支各雙冷啟動、無監看
控制與獨立正反例通過，證實選項狀態真正切換，
但空心／填色對「啟用」的語意仍待玩家結果確認。
ESC 後的左方向鍵、`ORDERS` 明示的 Space 都被取走；
取樣至1,500M未見首則 help，Space 尚未證實結束
整回合。`GAME → Retire` 只顯示離開確認，未按 Yes，
不能當新局入口。規格026仍 DRAFT，正式中文十七段，
help 正式顯示零則。

最近完成入口：[目標110](docs/goals/110-tutorial-hints-player-trigger.md)：
從已驗海上玩家畫面，以原版滑鼠實際打開頂端 `GAME` →
`Game Options` 並點最後一列 `Tutorial Hints`；核取圖示與
該列背景在原版索引畫面改變。未進選單的左方向鍵分支
證實按鍵被原版取走，海上船舶畫面隨之改變。兩分支各有
雙次冷啟動與無監看控制，獨立檢查和負例通過；目前
只限1,225M–1,350M的取樣，**未見首則 help 正文視窗**。
核取預設語意和真正觸發仍未知，不把 `@TUTORIAL1` 預讀
或選項點擊當成顯示。規格026維持 DRAFT，正式中文仍十七段。

最近完成入口：[目標109](docs/goals/109-opening-caption-variable-values.md)：
四國正常玩家路徑的 `@BUILD1–7` 原版字幕已各有
雙冷啟動與無監看對照；[24筆變數值草稿](text/build-caption-values.zh-Hant.tsv)
分國保存六處占位符、原始檔案候選與可見值。
荷蘭的 `the Netherlands` 與檔案候選 `Netherlands`
分欄記錄，冠詞來源未知；來源至印字的中間搬運仍
為強推論。[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)
保持 DRAFT，沒有新增正式 Ebitengine 中文畫面。

最近完成入口：[目標108](docs/goals/108-build-opening-caption-translation.md)：
固定原版十張開場字幕的十一個 `^^` 原文行現均有可追溯
繁中草稿；主譯稿由369增至379筆。獨立驗證重新核對
dosgolem 十段印字與雙重播、各行檔案位移／SHA、占位符、
控制碼和固定 Cubic 11 字形，正反例均通過。
[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)
仍 DRAFT：變數值雖有24筆草稿，正式畫面仍是英文；`@BUILD1` 的38／42px
視覺選擇、其餘字幕的個別字級／正式顯示，以及 help
的實際觸發和中文畫面都尚未完成；正式顯示維持十七段。
下一工作從已驗海上玩家畫面查 help 觸發，或分別
處理字幕逐欄版式；兩者不必代選字級。

最近完成入口：[目標107](docs/goals/107-post-caption-input-and-help-entry.md)：
英格蘭正常玩家路徑已驗85M與100M的 Enter 被原版消費；
不加第二鍵亦會依序顯示 `GAME.TXT:@BUILD1–10` 十張開場字幕，
約1,185M後進入可見海上遊戲介面。1,350M雙重播／無監看
控制與獨立負例通過；抽樣畫面未見 `@TUTORIAL1` 視窗，
其實際觸發仍未知，規格026保持 DRAFT、正式中文維持十七段。

下一工作入口：優先接續[規格027](docs/spec/027-game-options-window-draft.md)
九欄的原版解析→高位址 RAM 中間搬運、其餘六列及按下／放開
畫面相位、真 Ebitengine 玩家視窗逐欄回退；固定第一／末列
純移鼠與 ESC 離頁已由目標116有界驗證，九欄印前多色底圖及可丟棄 A／B
預覽已由目標113完成，正式字級尚待此視窗專屬視覺決定，
證據足夠才審查 READY。
教學選項能否在新局開始前以正常玩家介面啟用並保留
亦待查；目標123已證 `Retire → Yes` 到分數頁／名人堂後結束 DOS，
不是同次執行的新局入口。
另需把
`@BUILD2–10` 已有的逐行草稿與四國變數值草稿接到
各字幕的獨立版式；
`@BUILD1` 的38／42px正式字級仍待使用者選擇。

最近工作入口：[目標106](docs/goals/106-build-opening-caption-overlay-gate.md)
已用英格蘭正常玩家路徑補 `GAME.TXT:@BUILD1` 的原版印前
底圖、9px原文墨跡、四倍安全矩形及兩個可丟棄繁中樣本；
雙重播與無監看控制同狀態，獨立負例通過。A 是38px／
35px實際墨跡，B 是42px／39px實際墨跡；使用者尚未選擇，
[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)
仍 DRAFT，未接正式 Ebitengine。這不改變四國長文待決版式、
首則教學只預讀或目前十七段正式中文顯示的狀態。

最近完成入口：[目標105](docs/goals/105-first-tutorial-player-path.md)：
英格蘭介紹 B 後由正常 Enter 到下一頁，85M再按 Enter／ESC
會顯示 `GAME.TXT:@BUILD1` 原版英文字幕；三分支各有雙次
dosgolem 冷啟動、無觀測控制及原始畫布核對。`@TUTORIAL1`
標記與開頭文字確實先被 DOS 讀入 RAM，但沒有當次印字；
[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)
仍 DRAFT。主譯稿新增該字幕一筆草稿，總數369；正式中文
顯示維持十七段，24則 help 沒有畫面命中。

最近完成入口：[目標104](docs/goals/104-nation-introduction-exit-phase.md)：
英格蘭、西班牙與荷蘭介紹 B 頁後無鍵／Enter／ESC 各有雙次
dosgolem 冷啟動及無觀測控制。無鍵留 B 頁，兩鍵到各國
下一可見頁，原版清屏／新頁印字與原始畫布均經獨立核對；
Enter／ESC 完整 RAM 不同，不宣稱後續等價。規格025仍
DRAFT，正式中文顯示仍十七段。

最近完成入口：[目標103](docs/goals/103-font-rebuild-and-mask-parity.md)：
固定 Cubic 11 原始 TTF、合法原版與真實 TSV 已重烘現行十七欄
本機字模；前十五欄整份 JSON 與歷史已驗檔逐位元組相同，
第一張旗卡兩欄 Alpha bytes 完全相同。錯字型、錯 TSV、
缺原版、缺欄及改動 Alpha 都拒絕。此結果不增加正式顯示數，
也不替使用者決定四國介紹長文版面；字型仍不加入 Git。

最近完成入口：[目標102](docs/goals/102-nation-introduction-layout-prototypes.md)：
以已驗四國八節正常玩家路徑，核對重新找到的固定 SHA-256
`Cubic_11.ttf`，取得八頁相同的原版印字前底圖；兩套繁中長文離線
排版逐頁通過字形、安全矩形與零裁切檢查。私有
[A 頁](docs/screenshots/nation-intro-layout-draft-a.png)／
[B 頁](docs/screenshots/nation-intro-layout-draft-b.png)對照每列為原版、
貼近原版字高、較緊湊。字型來源與重取指紋見
[字型入口](font/README.md)。長文版面仍待使用者選擇；
[規格025](docs/spec/025-first-nation-introduction-draft.md)維持 DRAFT，
正式介紹畫面仍顯示原文，Issue #30 OPEN。

最近完成入口：[目標101](docs/goals/101-nation-introduction-player-path.md)：
四張旗卡各由正常滑鼠選取，八節 A／B 原版印字、畫布及頁相位
已有雙次 dosgolem 冷啟動與無觀測控制收據。法國 B 頁的無鍵／
Enter／ESC 分支已量，按鍵後可見畫面相同但內部狀態不同。
中文長文[規格025](docs/spec/025-first-nation-introduction-draft.md)
仍 DRAFT，正式顯示維持十七段，Issue #30 開放。
最近完成入口：[目標100](docs/goals/100-all-nation-introduction-bilingual-corpus.md)：
四國介紹共八節的原版來源固定雙語草稿已建，逐節檔案位移、SHA、
標題、控制標記與強調標記由獨立檢查器通過；目標100當時只有
法國兩節有正常路徑證據，其餘六節已由後續目標101補齊原版
印字與畫布；目標102又補齊兩套離線中文排版驗證，非正式畫面。
Issue #27／#30 繼續開放。
最近完成入口：[目標099](docs/goals/099-first-nation-card-a-overlay.md)：
使用者選定第一張國家旗卡 A 版，「英格蘭：」21px／「移民」25px
已依[規格021](docs/spec/021-nation-card-red-text-draft.md)限定 CONFORMED
接入 Ebitengine，真視窗、英文控制、舊十五欄與逐欄回退通過；本機
正式驗收增至十七段，Issue #12／#26 因其他文字與發行仍保持開放。
先前完成入口：[目標098](docs/goals/098-first-nation-introduction-source.md)：
法國首次介紹的 `GAME.TXT:@NATION1A`／`@NATION1B` 已由正常玩家
路徑、雙次 dosgolem 與無觀測控制追至兩頁實際印字和原版畫布；
[規格025](docs/spec/025-first-nation-introduction-draft.md)與
[雙語草稿](text/nation-introduction.zh-Hant.tsv)已建。第一頁與既有真
Ebitengine 原文圖逐像素一致；目標098當時未驗的法國 B 後按鍵
可見離頁，已由後續目標101補證。第二頁真視窗、中文逐欄
字級／換行及回退仍未驗；規格保持 DRAFT、長文尚未正式顯示，
Issue #30 保持開放。並行待決的
[目標097](docs/goals/097-name-field-display-choice.md)已量得可編輯
預設姓名欄的原版框線、墨跡、安全區及 `x`／退格／Enter 分支，
本機 A 原名／B 中文佔位示意兩圖的 Ebitengine 差分已驗。
B 的文字**不是已確認譯名**，使用者尚未選定是否只在未編輯
預設值顯示中文；正式覆蓋、真實譯名及回退仍待定，Issue #29
保持開放。
前一完成入口：[目標096](docs/goals/096-player-name-prompt-runtime-guard.md)：
姓名固定提示已由完整來源事件、當次多色畫布補片、游標與 Enter
離頁守門接入正式輸出層；[規格023](docs/spec/023-player-name-screen-draft.md)
先升 READY 後經 dosgolem 及真 Ebitengine 視窗同狀態驗收，
限定 CONFORMED。該目標完成時正式中文顯示為十五段，後續目標099
加入第一張旗卡兩段；可編輯姓名與首次國家介紹
仍保持原文。下一工作入口是[Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)
未決的可編輯姓名欄中文顯示界線；[Issue #30](https://github.com/wicanr2/colonization_cht/issues/30)
的長文正式排版與翻頁回退仍待後續目標。開工前另寫並推送目標。
最近完成入口：[目標095](docs/goals/095-player-name-input-and-overlay-gate.md)：
真 Ebitengine 視窗從冷啟動抵達姓名畫面，實際 `x`／退格／Enter、
標點拒絕與失焦不補送已同狀態驗收；鍵盤接線依
[規格024](docs/spec/024-window-keyboard-input.md)限定 CONFORMED。
該輪結束時姓名固定提示尚缺完整來源與正式覆蓋；此限制已由
後續目標096解除，不再作為目前阻塞。
最近完成入口：[目標094](docs/goals/094-player-name-prompt-layout.md)：
姓名固定提示的原版印前多色底圖、415點墨跡、y=98輸入框
負例及38px單欄 Ebitengine 可丟棄原型，三種姓名編輯畫面
逐像素驗收；該輪當時正式視窗字元／退格與提示回退仍缺，規格023
維持 DRAFT，正式中文顯示十四段不變；後續已由目標095／096解除。
最近完成入口：[目標093](docs/goals/093-player-name-source-and-input.md)：
姓名提示與預設名的固定來源及動態印字、字元／退格／Enter 輸入均有
雙次原版及 Ebitengine 控制收據；正式中文安全矩形與回退仍缺，
[規格023](docs/spec/023-player-name-screen-draft.md)保持 DRAFT。
前一完成入口：[目標092](docs/goals/092-neighbor-card-runtime-and-nation-route.md)：
右卡游標／重繪／換卡／離頁負例已有雙次原版及無觀測控制收據；
正常玩家路徑當時已到姓名畫面；其文字來源與輸入行為已由
後續目標093解出，勿再沿用目標092當時的未知結論。
前一完成入口：[目標091](docs/goals/091-neighbor-nation-card-reversible-preview.md)：
相鄰右上旗卡兩欄的原版精確印前底圖與本機 Ebitengine 可逆候選已驗，
尚未定案字級或接正式輸出；前一完成入口：
[目標090](docs/goals/090-neighbor-nation-card-source.md)；
另見[目標089](docs/goals/089-first-nation-card-runtime-guard-evidence.md)：
第一張國家旗卡的兩欄游標遮擋、下欄左鍵與相鄰旗卡重繪已有雙次
dosgolem 重播及無觀測控制。承接[目標088](docs/goals/088-first-nation-card-reversible-preview.md)
兩欄本機 Ebitengine A／B 可逆原型；使用者後續已選第一張旗卡 A，
並由目標099完成規格021的限定 CONFORMED。相鄰右上旗卡
`France`／`Cooperation` 的原始 TXT 至畫布來源鏈已閉合，
[規格022](docs/spec/022-neighbor-nation-card-red-text-draft.md) 仍為 DRAFT。

## 已確認決定

- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標。
- 中文化是 dosgolem 輸出階段的繁體中文覆蓋，不是 remake；不修改原版程式、資料、規則或存檔。
- 儲存庫 `wicanr2/colonization_cht` 維持 PRIVATE；原版素材與原始研究快照只保留本機。
  README 中三張經驗收的 Ebitengine 視窗圖與兩張含原版畫素的四國介紹
  DRAFT 對照圖僅在已核對為 PRIVATE 的儲存庫內保存，公開散布仍未授權。
  原版輸入、字型與原始快照仍不入 Git；兩張 DRAFT 圖不得冒稱正式遊戲畫面。
- dosgolem 只修改 `workplace/dosgolem` 獨立副本；`upstream` 推送位址保持 `DISABLED`。
- 2026-09-22 使用者已確認主選單原型採 Cubic 11、24px 字級（4 倍輸出畫布）。這是該已驗證
  欄位的樣式證據，不是其他畫面的固定字級；不代表術語、完成範圍或字型散布授權已定案。
- 2026-09-23 使用者確認中文覆蓋必須依原版文字字級與欄位安全矩形調整，禁止用全域固定中文字級。
  每個覆蓋欄位須量測原版文字、中文候選字級、基線、最長譯文與回退策略；沒有專屬量測時維持
  原文並記錄命中。
- 2026-09-23 使用者指出私有難度畫面截圖的「選擇難度」標題應重排以符合原版風格，
  並依畫面與欄位調整中文字級；已登記 [Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)
  於目標079後獨立處理。使用者看過原版／目前版／A／B 四格對照後，已明確
  選定 A：兩行分別34／38px、共同置中；排除 B 的左起點。正式實作限於兩欄，
  卡片與完成提示不變；通過同狀態驗證後才更新私有截圖。
- 2026-09-24 使用者已從本機兩版對照選定**第一張國家旗卡** A：
  「英格蘭：」21px、「移民」25px，貼近原版字高；排除 B 的25／29px。
  此決定只涵蓋第一張旗卡；目標099已完成該兩欄 READY 至 CONFORMED
  的同狀態驗收，不自動擴張到相鄰旗卡或其他畫面。
- 2026-09-23 使用者選定 `COLONY.TXT` 殖民地名稱的顯示譯法為「中文名稱（原名，年份）」，
  無年份者為「中文名稱（原名）」。原始名稱、逗號與年份仍是穩定來源資料，不得用譯文參與
  查找、規則或存檔；尚未取得執行期命中或安全矩形。
- 2026-09-22 使用者選定原始控制 Tab 的位元組保留：UTF-8 TSV 以字面 `\\t` 轉義，
  解碼後必須在原文與譯文保留相同控制序列；排除將它正規化成空白或略過文章。
  這只適用翻譯資料的來源忠實度，不授權將 Tab 直接繪上畫面。
- 2026-09-22 使用者選定把 `PEDIA.TXT` 原始 CP437 `0xF9` 正規化成 Cubic 11 已具字形的
  Unicode `•`（U+2022）；原始位元組、位址與 SHA 仍保留作來源證據。排除直接使用
  CP437 對應的 U+2219 及另建字型 fallback；此決定只處理譯稿結構控制符號，未授權畫面覆蓋。

## 目前狀態表

| 項目 | 狀態與證據 |
|---|---|
| 正常 DOS 啟動 | confirmed：原版 `COLONIZE.BAT` 使用 `OPENING.EXE -g`；已轉交 `VICEROY.EXE` 並顯示主選單。 |
| 主選單滑鼠 | confirmed：正常冷啟動後點選「新世界」可到難度畫面，不是 direct-entry 或記憶體改寫。 |
| 快照重播 | confirmed：連續路徑與安全選單快照續跑的索引畫面及色盤一致；無輸入留在主選單。 |
| 平台修正 | BIOS 馬達倒數、`int33 AX=0014` 回呼交換、DOS v4 滑鼠狀態與不安全回呼保存拒絕；規格 006–008。 |
| 動態文字 | confirmed：GAME.TXT 檔案位移 0x1B0 → 執行期 6F16:00DF → 937C:0538 印字 → 180 個畫布像素；兩次冷啟動收據一致。目標 054 完成。 |
| 靜態文字 | 開場海洋標籤等候選仍缺完整來源／可逆背景證據；Issue #8 開放，不阻擋動態路徑。 |
| 翻譯草稿 | `text/draft.zh-Hant.tsv` 共369筆：GAME 97、LABELS 40、MENU 68、NAMES 70、PEDIA 19、MAPEDIT 31、MAPMENU 28、WOODCUT 14、OPENING 1、CLOSING 1；原始來源／控制碼（含 `#` 格式記號）檢查通過。新增 `@BUILD1` 一筆有原版印字證據，但中文字模、安全矩形及正式畫面未驗；正式顯示十七段仍只屬既有欄位。18個TXT／4,119粗略資料行不是全遊戲訊息分母。 |
| 百科雙語語料 | `text/pedia-bilingual.tsv` 含 `PEDIA.TXT` 的25篇建國元勳、16篇貨物、24篇單位、29篇地形、27篇職業及42篇建築，合計163篇編號文章的整段原文／繁中草稿；固定來源、控制碼（含一個保留的Tab及由原始`0xF9`正規化的`•`）與Cubic 11覆蓋通過，缺字0。未取得畫面命中或安全矩形。 |
| 說明雙語語料 | `text/help-bilingual.tsv`另含24則教學／地圖編輯說明的原文及繁中草稿，兩個固定原版檔案與每則位元組指紋可回查；僅限私有repo，未整合正式執行期語料。`@TUTORIAL1` 已有正常路徑 DOS 預讀；目標107再由十張 `@BUILD` 字幕抵達海上畫面，1,200M／1,225M／1,275M／1,325M抽樣仍未見 help 視窗。觸發／印字未知，不可與前列369筆直接相加當顯示完成度。 |
| 英格蘭開場至海上畫面 | [目標107](docs/goals/107-post-caption-input-and-help-entry.md)已驗85M及100M Enter 確實被消費，字幕 `@BUILD1–10` 依序自行前進；原版約1,185M進入海上介面，1,225M後上方選單可見，開啟 `CYCLE.DAT`／`MENU.TXT`。1,350M雙重播及無讀寫監看控制同狀態；僅證實固定英格蘭正常路徑與抽樣，不等於正式 Ebitengine 中文介面或 help 已顯示。 |
| README 玩家補充語料 | `text/readme-bilingual.tsv`含 DOS ZIP 內 `README.TXT` 的7段版本修正、地圖編輯器與作弊模式原文／繁中草稿。封存檔、成員檔、位元組範圍與片段 SHA 均固定，按鍵／符號／Tab及Cubic 11覆蓋通過，缺字0；它不是執行期鍵，未命中畫面。 |
| 殖民地名稱語料 | `text/colony-bilingual.tsv`含 `COLONY.TXT` 的173筆預設名稱（英36、法66、西39、荷32）；18個年份依使用者決定呈現為「中文名稱（原名，年份）」。ZIP／成員／章節／行與片段 SHA、年份與格式驗證通過，字型字元缺字0；沒有畫面命中、安全矩形或欄位專屬中文字級。 |
| 中文顯示 | 主選單五列、難度頁兩行標題、完成提示、第一及第二張卡片各兩行、國家頁左側兩行、第一張國家旗卡兩行、姓名固定提示一行，共十七段有原版事件與逐幀覆蓋；規格012／014／015／017／018／019／020／021／023為各自限定範圍 CONFORMED。難度標題依使用者 A 版採34／38px共同置中；第一張旗卡依另一個使用者 A 決定採21／25px紅字／黑影。真視窗新舊版及英文控制原版同狀態，旗卡新增差異僅在兩個安全矩形；私有截圖已驗後更新。姓名提示採38px且真視窗原版同狀態；正常玩家路徑已抵達首次國家介紹，仍非正式完整玩家版，Issue #26保持開放。 |
| 第一張難度卡片 | confirmed：稱號從 `NAMES.TXT:0x00000C0C`、副標從 `LABELS.TXT:0x000008A9` 載入，經原版緩衝與格式化印字路徑繪至畫布；`GAME.TXT` 同文不是此路徑稱號來源。規格017限定第一張卡片兩行為 CONFORMED：21／25px 逐欄字模、當次有紋理底圖、原文差分、游標及真實 TSV 缺鍵回退已接正式前端並與同輸入英文控制同狀態；其餘卡片仍屬規格016 DRAFT。 |
| 第二張難度卡片 | confirmed：真 Ebitengine 視窗點擊 `(265,55)` 顯示 `EXPLORER:`／`Easy`，雙次 dosgolem 收據閉合 `NAMES.TXT:0xC18`／`LABELS.TXT:0x8B2` 至 RAM、格式化印字與原始畫布；墨跡高5／6像素、有紋理底圖。規格019限定兩行為 CONFORMED：「探險家／簡單」採21／25px逐欄字模，真視窗中文與英文控制原版同狀態；各欄缺譯／重複鍵及游標回退、錯版本拒絕與第一張卡片回歸均通過。規格016對其餘卡片仍為 DRAFT。 |
| 第三張難度卡片 | confirmed（原文及固定滑鼠相位）：正常玩家前綴後點擊 `(55,145)`，`NAMES.TXT:0xC22`／`LABELS.TXT:0x8B8` 經 DOS 載入、`0E2D:11CF` 來源讀取、`0D21:00C6` 印字讀取，在畫布留下205／116點墨跡。目標121以本卡原文5／6像素高度獨立量測 A 21／25px、B 25／29px；Ebitengine 本機兩版預覽及原文控制逐像素 PASS。dosgolem 雙重播／無監看控制證實 `(55,132)` 只遮上欄、`(55,151)` 只遮下欄，按住／放開／移開可各自判斷。完整中間逐 byte 搬運仍為強推論；正式事件／背景守門、真 TSV 失敗回退與真視窗中文未驗，使用者尚未定第三卡 A／B。[規格016](docs/spec/016-difficulty-card-text-draft.md)仍 DRAFT，「征服者／普通」不計入十七段。 |
| 國家選擇頁 | confirmed：正常滑鼠按下／放開難度頁完成區會開啟 `NATIONS.PIK`；16筆真 Ebitengine 視窗輸入抵達此頁，與同輸入英文控制原版同狀態。左側兩行 `Select`／`European Power` 已追溯至 `LABELS.TXT:0x8D3`／`0x8DB`、RAM、實模式輸出及安全矩形；[規格020](docs/spec/020-nation-heading-overlay.md)限定 CONFORMED：「選擇／歐洲國家」各38px，兩欄缺鍵／重複鍵、游標、按鍵及場景切換均逐欄安全回退，錯版在輸出前拒絕。其他國家頁文字仍未驗收。 |
| 第一張國家旗卡紅字 | 目標085／087證實 `NAMES.TXT:0x8EA`／`LABELS.TXT:0x8F2` 各自從 DOS 讀入至原版畫布的動態來源鏈；目標088擷取兩欄印前多色底圖並以[text/nation-card-fragments.zh-Hant.tsv](text/nation-card-fragments.zh-Hant.tsv)固定譯文來源。使用者選 A 的21／25px「英格蘭：／移民」紅字／黑影，排除 B 的25／29px。目標089／099補齊游標、按住、相鄰右卡重繪及直接離頁的原版負例；[規格021](docs/spec/021-nation-card-red-text-draft.md)已限定 CONFORMED：真 Ebitengine 視窗與同輸入英文控制、舊十五欄原版同狀態，只在兩欄安全區新增1,915／2,738輸出像素；缺譯、重複鍵、缺字模、錯字級、游標、換卡、離頁與錯版都逐欄安全回退。目標103找回固定原始 TTF 並直接重烘兩欄，與歷史已驗 Alpha bytes 精確相同；只計入第一張兩欄，右卡與其他國家仍未定案。字型及字模不入 Git，正式散布尚未授權。 |
| 相鄰右上國家旗卡文字 | [目標090](docs/goals/090-neighbor-nation-card-source.md)證實 `NAMES.TXT:0x906` 的 `France` 與 `LABELS.TXT:0x8FF` 的 `Cooperation` 從原始 TXT、DOS／RAM 至右側畫布；[目標091](docs/goals/091-neighbor-nation-card-reversible-preview.md)取得右欄多色底圖、安全區及兩個本機 Ebitengine 候選逐像素 PASS。原版右欄為藍色索引9，不是左卡紅色12。[目標092](docs/goals/092-neighbor-card-runtime-and-nation-route.md)又驗上／下欄游標各自遮擋24／25點、再點右卡的短暫重繪、切回左卡及離頁負例；雙次冷啟動與無觀測控制同狀態。[規格022](docs/spec/022-neighbor-nation-card-red-text-draft.md)仍 DRAFT；字級未定案，正式前端逐欄回退未驗，不計入十七段正式顯示。 |
| 選國後姓名畫面 | confirmed：右卡完成提示 `(65,184)` 由正常滑鼠路徑進入；`GAME.TXT:0xA7A` 完整提示行（可見字串 `0xA7C`）及 `NAMES.TXT:0xB4B` 預設姓名片段各有 DOS／RAM／`0D21:012C` 畫布來源鏈。目標094證實提示415點、多色印前底圖、安全矩形與38px字模；目標095真視窗驗 `x`、退格、Enter、標點拒絕與失焦不補送，[規格024](docs/spec/024-window-keyboard-input.md)限定 CONFORMED。目標096補足完整來源、開檔世代、游標與離頁守門，正式38px中文提示通過真視窗同狀態、缺鍵／缺字／錯版回退；[規格023](docs/spec/023-player-name-screen-draft.md)僅固定提示限定 CONFORMED，計入第十五段。目標097另量到姓名框 `(79,98)–(246,112)`、墨跡 `(82,101)–(164,110)` 及內部安全區 `(80,100)–(245,111)`（原版320×200半開座標）；A原名／B中文佔位示意的本機圖差分只在該區，未接正式前端。可編輯姓名資料、原版記憶體、規則與存檔不改；是否僅顯示譯名、真正譯法及逐欄正式回退尚未定案，[Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)保持開放。 |
| 首次國家介紹長文 | confirmed：目標101從選國頁四張旗卡的正常滑鼠點選，經姓名 Enter 到英、法、西、荷各 A／B 原版介紹；八節均有固定 `GAME.TXT` bytes、DOS 讀取、逐字印字、畫布墨跡、雙次冷啟動及無觀測控制收據。西班牙 B 的來源 `50%%` 實際印為 `50%`。目標104又以英、西、荷三國各三種 B 後分支共27份重播／控制報告，證實無鍵留 B 頁，Enter／ESC 抵達各國後續可見 King 畫面；兩鍵的 RAM 不同，不主張後續等價。目標102以相同 SHA 字型取得八頁印字前底圖，兩套離線中文排版均無缺字、裁切或安全區外改色；這不是執行期覆蓋。八筆繁中 TSV 仍為 draft、沒有中文長文覆蓋；[規格025](docs/spec/025-first-nation-introduction-draft.md)仍 DRAFT，正式長文版面、輸出事件與頁相位守門、真視窗第二頁與回退待驗。[Issue #30](https://github.com/wicanr2/colonization_cht/issues/30) OPEN。 |
| 完整可玩／正式發行 | 未驗證、未發布；正常玩家路徑目前驗至首段國家介紹，尚未確認介紹後操作、help 或實際遊玩。 |

## 工具與重播入口

- 研究映像：`colonization-research:20260920-r2`；分析、建置、測試、遊戲執行均在 Docker 內。
- 隔離 dosgolem 程式提交：`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- 累積補丁：[tools/dosgolem-platform-fixes.patch](tools/dosgolem-platform-fixes.patch)，
  基底為 `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`，包含 SBPro／MCB／滑鼠修正、精確指令前觀測及通用合成器。
- [目標 053](docs/goals/053-mouse-and-gameplay-route-replan.md) 保存 Docker 重播命令、版本與驗收結果。
  `tools/probe_gameplay_route.py` 建立新的 DOS v4 選單快照。
- 舊 v3 快照不能交給現行程式猜補；歷史對照工具 `tools/probe_opening_mouse.py` 在容器暫存目錄
  建置原始 `1435f17`，不切換目前工作樹、不修改原快照。
- `go test ./...` 已通過；不代表所有 DOS 遊戲或任意指令邊界快照全面相容。

## 訂正與證據限制

先前缺少 `-g` 的開場點擊只證明該啟動情境下的退出，不代表主選單操作。
目標 053 固定舊狀態的三個不同座標有相同控制流；不能外推成所有畫面不依賴座標。
撤回「由使用者猜下一個座標」的門檻。舊觀測保留在目標 034–052 與研究紀錄，不再充當目前阻塞點。

DOSBox-X 僅提供啟動鏈及畫面類別的輔助基準，正式收據由 dosgolem 重生。
主選單沒有命中其他遊戲專用的字型 hook，不代表沒有動態文字。
未實作的 DOS 日期／記憶體策略服務另有紀錄，但本輪沒有證據顯示它們阻擋已驗證路徑。

## 下一閘門與歷程索引

目前主譯稿已有369筆，另有24則help稿及旗卡四筆顯示片段草稿，
但原版TXT、EXE及靜態圖像仍未建立完整玩家可見訊息分母。
第一張旗卡已依[目標099](docs/goals/099-first-nation-card-a-overlay.md)
完成 A 版兩欄限定 CONFORMED；目標102恢復相同 SHA 的原始
字型來源，目標103完成十七欄本機字模重烘與舊版對拍；後續仍須
建立工具映像的跨機可重建來源與發行權利檢查，
並另行探勘其他國家；不得將第一張的 A 字級複製到右卡。
相鄰右上旗卡已依[目標091](docs/goals/091-neighbor-nation-card-reversible-preview.md)
驗得可逆底圖與兩組字級候選，[目標092](docs/goals/092-neighbor-card-runtime-and-nation-route.md)
又量得游標、再次點卡、切回左卡及離頁相位；下一步是右卡
正式逐欄回退與版式確認，不能把第一張的 A／B 決定外推。
[規格022](docs/spec/022-neighbor-nation-card-red-text-draft.md)仍 DRAFT。
姓名畫面依[規格023](docs/spec/023-player-name-screen-draft.md)已有
固定提示正式驗收；可編輯姓名欄仍待使用者決定資料隔離顯示界線。
首次國家介紹長文另見 Issue #30，已有八節草稿與離線排版驗證，
但未選正式版式、未接 Ebitengine，不能算中文畫面驗收。
以下舊目標僅供查找當時證據與過程；完成度以本檔上方「目前狀態表」為準。
[目標065](docs/goals/065-pedia-founding-fathers-corpus.md)與[目標066](docs/goals/066-pedia-cargo-corpus.md)
已分別完成25篇「建國元勳」及16篇「貨物」的整段草稿；合計41篇已通過固定來源、
格式及字型驗證，但它與單行主譯稿分開，尚未有畫面事件、版面或正式覆蓋資格。
[目標067](docs/goals/067-pedia-unit-corpus.md)已完成24篇「單位」文章草稿；
[目標068](docs/goals/068-pedia-terrain-corpus.md)已完成29篇「地形」文章草稿；
[目標069](docs/goals/069-pedia-job-corpus.md)已完成27篇「職業」文章草稿；
[目標070](docs/goals/070-pedia-building-corpus.md)已完成42篇「建築」文章草稿。百科163篇編號文章
皆有來源可追溯的草稿及字型覆蓋收據；這仍與全遊戲翻譯、畫面中文化及術語定稿分開計算。
[目標071](docs/goals/071-mapmenu-woodcut-corpus.md)已完成44筆獨立的地圖編輯器選單、過場標題及
載入訊息草稿。`NAMES.TXT`的70條無逗號文字已全數收錄；餘下232列是名稱混合規則／別名資料，
不可套用既有整行候選模型，待有 DRAFT 欄位識別方案才重開。
[目標073](docs/goals/073-colony-name-bilingual-corpus.md)已完成 `COLONY.TXT` 的173個預設殖民地
名稱草稿，採使用者確認的「中文名稱（原名，年份）」格式。解析器將原始名稱與年份分離為穩定
來源欄位，不將其誤作整行覆蓋鍵或原版資料改寫；字型檢查也未設定固定中文字級。
最近完成入口：[目標072](docs/goals/072-readme-player-guide-corpus.md)已完成 DOS 版 `README.TXT` 的七則版本修正、
地圖編輯器與作弊模式玩家補充說明草稿；過時的 DOS／音效排錯與客服資料明確排除。固定 ZIP
來源、操作字面值及Cubic 11覆蓋通過，但不增加任何已顯示文字或 runtime 覆蓋聲明。
[目標060](docs/goals/060-help-bilingual-corpus.md)另建立24則遊戲內教學／地圖編輯說明的原文／繁中TSV，
仍是待畫面驗收的草稿。
[目標061](docs/goals/061-next-visible-text-slice.md)已驗收難度頁兩行中文標題，
真視窗圖存於私有 `docs/screenshots/`；圖內有原版像素，不得當公開發行素材。
[目標062](docs/goals/062-difficulty-finish-prompt.md)已驗收難度頁「完成後點此」提示；
限定證據、覆蓋契約與中英文同狀態結果見[規格015](docs/spec/015-difficulty-finish-prompt.md)。
[目標063](docs/goals/063-difficulty-card-text.md)接續難度卡片文字；
[目標074](docs/goals/074-difficulty-card-observation-repair.md)已修正舊探針重複註冊監看器的缺陷，
兩次正常路徑重播均讀到第一張卡片的 `Discoverer`／`Easiest` 原文字節，且卡片區
`0D21:012C` 有292次畫布寫入。舊「零命中」已訂正；來源讀取與各行畫布寫入的直接
資料流已由[目標075](docs/goals/075-difficulty-card-source-to-pixels.md)閉合：原文經
`0x2A74C` 共用緩衝與 `0x2A6B0` 局部副本，`0D21` 逐字讀取後畫在卡片上。
稱號實際格式為 `DISCOVERER:`；兩行原版墨跡分別5／6像素高，背景各有75／78種色盤索引，
不可純色抹除。當時來源檔載入邊、背景可逆擷取、中文字級／安全矩形與游標守門仍缺，
[規格016](docs/spec/016-difficulty-card-text-draft.md)在該階段保持 DRAFT，當時不計入八段完成數。
[目標076](docs/goals/076-difficulty-card-reversible-prototype.md)已以固定雙次原版收據完成
第一張卡片的本機可逆背景與 Ebitengine 可丟棄對照圖；稱號／副標候選字級分別為
21／25px，逐像素檢查確認安全區外不變、透明字模下恢復原背景。它不是正式
runtime 覆蓋或真視窗正常路徑收據；當時來源檔載入邊、任意時刻的背景／游標守門與
其餘卡片仍缺；規格016在該階段保持 DRAFT，當時八段已顯示中文數不增加。
[目標077](docs/goals/077-difficulty-card-load-provenance.md)已以兩次獨立 dosgolem 冷啟動
閉合原始 TXT → DOS 緩衝 → 中間緩衝 → 第一張卡片 RAM 的載入邊：
`Discoverer` 來自 `NAMES.TXT`，`Easiest` 來自 `LABELS.TXT`；`GAME.TXT`
首次讀取晚於稱號 RAM 寫入。可丟棄預覽已改用 `NAMES.TXT` 候選鍵並重驗
Ebitengine 畫面。穩定顯示鍵、執行期背景／游標回退及其餘卡片仍未過 READY，
不能把這兩筆 `draft` 譯文接進正式覆蓋。
[目標078](docs/goals/078-difficulty-card-runtime-guard.md)已在隔離 dosgolem 建立
第一張卡片的執行期可丟棄守門：兩次正常玩家重播位元組相同，與無觀測控制組
原版 CPU／RAM／畫面一致；卡片游標停留25幀回退原文，移開24幀恢復候選中文。
游標確實改變原版索引畫面並與兩欄安全區相交，但不改底層畫布。
正式格式化鍵、真實缺譯處理、其餘卡片及 Ebitengine 正常玩家前端仍缺，
規格016在該階段保持 DRAFT、當時八段已顯示中文計數不變。
[目標079](docs/goals/079-first-card-formal-overlay.md)已完成第一張卡片的限定 READY
審查、真實 TSV 缺鍵回退與 Ebitengine 前端接線；[規格017](docs/spec/017-first-difficulty-card-overlay.md)
經中英文同狀態、真視窗逐像素與游標變體驗收標為 CONFORMED，現有十段正式顯示中文。
其餘卡片仍依規格016 DRAFT 逐張取證，不能外推。
[目標080](docs/goals/080-difficulty-heading-layout-prototype.md)量得原版標題
兩行共用四倍畫布 x=230 中心、高度32／36px，並製作 A／B 可丟棄
對照。使用者已選 A；[規格018](docs/spec/018-difficulty-heading-layout-draft.md)
的34／38px共同置中版式已限定 CONFORMED，真視窗與同輸入英文控制
同狀態，現行私有截圖已依驗收更新。B 左起點版未接入。
[目標081](docs/goals/081-second-difficulty-card-output-evidence.md)在不依賴
Issue #28 視覺選擇的範圍，已完成第二張難度卡片真視窗點擊與
來源至畫素證據；其正式中文覆蓋仍未核准。
[目標082](docs/goals/082-second-difficulty-card-overlay.md)已完成第二張卡片兩行的
逐欄字級、可逆背景、游標／缺譯反例與正式前端驗收；
[規格019](docs/spec/019-second-difficulty-card-overlay.md)限定 CONFORMED。
當時 Issue #28 的 A／B 版式尚待選擇，現已由目標086完成 A；
第三至第五張卡片、help 與完整玩家路徑另待取證。
[目標084](docs/goals/084-nation-heading-runtime-guard.md)已依規格020的
READY 守門接入國家頁左側兩行；真視窗中文／英文控制、真 TSV
逐欄缺鍵／重複鍵、游標與按鍵回退、錯版拒絕、舊十二段回歸均通過。
該輪當時正式已顯示中文數為十四段。下一步仍須追其他國家選擇文字、help
與更深玩家路徑；難度標題原版風格排版後來由目標086獨立完成。
[目標085](docs/goals/085-nation-card-text-provenance.md)已以兩次原版
收據將國家旗卡兩處紅字的當次繪製分類為動態印字；檔案候選至
RAM 的載入鏈、相鄰狀態與正式守門仍缺，因此繼續進行中，不計入
當時十四段正式顯示。
[目標086](docs/goals/086-difficulty-heading-centered-layout.md)依使用者確認的
A 版完成難度標題限定驗收，真視窗、十五檢查點、兩欄回退與
錯版拒絕通過；已在驗證後更新既有私有截圖，不把它當公開素材。
[目標087](docs/goals/087-nation-card-source-load-edge.md)接續目標085，
只追第一張國家旗卡紅字的原始檔案載入至 RAM 來源邊與相鄰反例；
在完整資料鏈證實前，不增加正式中文段數或寫入覆蓋鍵。
[目標059](docs/goals/059-ebitengine-display-wiring.md)讓Ebitengine視窗以明確Go介面
接到原版五列顯示，九筆真視窗輸入與中英文同狀態對拍通過。[目標058](docs/goals/058-translation-corpus-and-player-window.md)
保留當時189筆草稿及五筆畫面命中的分母。現有主譯稿已擴至369筆；全遊戲中文化、第三種輸出情境與正式玩家前端仍未完成。

已完成 [目標 054](docs/goals/054-main-menu-text-provenance.md) 的最小證據鏈；
[目標 055](docs/goals/055-first-text-prototype.md) 保存中文原型、測試與重跑入口。
目前原型為 4 倍畫布、使用者已確認 Cubic 11 的 24px 顯示，中文為「在新世界開始遊戲」。
字型仍僅本機使用。目標055當時依字型內嵌欄位無法判定 OFL；
目標102後來找到固定原始檔與原作者 OFL-1.1 授權文件，訂正
「不是 OFL」的過度結論；正式套件的授權告知與散布仍待審查。

目標056首列已由[規格012](docs/spec/012-five-menu-lines.md)擴至五列，每列三次事件一致。
滑鼠在(128,110)時前三列的完整安全區受遮擋而回退，後兩列仍中文；移開恢復。
不宣稱游標可跨過中文而不回退。已有以`tools/build_window_prototype.py`組裝的
可撤回Ebitengine視窗，經真視窗點擊與英文控制組對拍；它仍依賴目前有限的五列適配器，尚未抽離成
正式玩家前端，也未驗失焦／關窗。難度頁兩行標題已走不同於 `937C:0538` 的
`0D3A:0015` 來源讀取與 `0D21:012C` 畫布寫入；完成提示另由 `0E2D:11CF`
讀取執行期原文；後續仍須追未驗難度卡片、help及真正不同的輸出情境，
不把已核准的兩行外推到其他文字。
不得直接移植 psychic-war 的整個 xlate：其 3 倍數縮放與純色抹底假設不符目前原型。
不重新開啟整個開場研究；不以無頭切片關閉要求互動交付的 Issue #26。

術語、完成範圍與授權／公開方式仍需使用者依成果決定，不能把字型大小同意擴張解讀。
