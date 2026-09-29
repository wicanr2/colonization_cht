# 工作計畫

<!-- 由 tools/worklist.py render 從 docs/worklist.json 產生；請勿手動修改。 -->

所有未完成工作以 GitHub Issue 為執行入口；本檔只呈現其機器可讀索引。
尚未自動驗證的條目一律標為人工驗證（manual），代表它們仍未完成；已完成條目必須有可重跑的訊號。

| Issue | 狀態 | 工作項目 | 依賴 | 驗收摘要 |
|---:|---|---|---|---|
| #1 | completed | [建立原始輸入指紋與權利邊界清冊](https://github.com/wicanr2/colonization_cht/issues/1) | — | 可重跑的雜湊與權利清冊，且 Git 未追蹤原版素材。 |
| #2 | completed | [建立可重現的隔離研究工具鏈](https://github.com/wicanr2/colonization_cht/issues/2) | — | Docker 入口可重跑、輸入唯讀、沒有 root-owned 產物或殘留容器。 |
| #3 | completed | [探測 dosgolem 對目標版本的冷啟動能力](https://github.com/wicanr2/colonization_cht/issues/3) | `input-inventory`, `research-toolchain` | 特定雜湊有可重跑的服務缺口報告。 |
| #4 | completed | [建立原版冷啟動至主選單的基線收據](https://github.com/wicanr2/colonization_cht/issues/4) | `dosgolem-probe` | dosgolem 可重生含輸入、快照與索引畫面的基線，或有可重現 blocker。 |
| #5 | completed | [追溯動態文字輸出常式與文字來源](https://github.com/wicanr2/colonization_cht/issues/5) | `normal-gameplay-route` | 至少一條真實玩家路徑的文字輸出事件有原始定位、證據等級與重播 trace。 |
| #6 | completed | [制定動態文字抽取與訊息鍵 DRAFT 規格](https://github.com/wicanr2/colonization_cht/issues/6) | `dynamic-print-re` | DRAFT 規格定義來源鍵、回退和幾何資料模型，並核對至少三種實際輸出情境。 |
| #7 | completed | [建立動態文本清冊與覆蓋率量測](https://github.com/wicanr2/colonization_cht/issues/7) | `dynamic-text-draft` | 可重跑報表列出抽取、翻譯與未知鍵數。 |
| #8 | completed | [普查靜態內嵌文字與覆蓋候選](https://github.com/wicanr2/colonization_cht/issues/8) | `psound-post-profile-control-flow` | 靜態文字清冊可重現候選定位與證據等級。 |
| #9 | completed | [制定靜態文字覆蓋 DRAFT 規格與最小原型](https://github.com/wicanr2/colonization_cht/issues/9) | `static-text-survey` | 一個可丟棄原型具命中與反向條件對照。 |
| #10 | completed | [確認中文字型、術語政策與中文化完成範圍](https://github.com/wicanr2/colonization_cht/issues/10) | `dynamic-coverage`, `static-overlay-draft` | 使用者確認字型、術語與完成門檻並回填 CONTEXT／READY 規格。 |
| #11 | completed | [將動態文字覆蓋設計升為 READY 規格](https://github.com/wicanr2/colonization_cht/issues/11) | `dynamic-text-draft`, `dynamic-coverage`, `l10n-decision` | 所有正式輸出類別有可回查 evidence 與 READY 規格。 |
| #12 | completed | [擴展並驗證動態文字中文疊加](https://github.com/wicanr2/colonization_cht/issues/12) | `first-localized-slice` | 中文、英文、缺譯和最長譯文都有固定快照與玩家路徑驗證。 |
| #13 | completed | [實作並驗證靜態文字圖像中文覆蓋](https://github.com/wicanr2/colonization_cht/issues/13) | `static-overlay-draft`, `l10n-decision` | 每個項目有圖像指紋、反向條件與玩家路徑收據。 |
| #14 | completed | [建立中文化驗證矩陣與正常玩家路徑收據](https://github.com/wicanr2/colonization_cht/issues/14) | `dynamic-overlay-implementation`, `static-overlay-implementation` | 動態與靜態路徑都有原版、中文、英文與反向條件收據。 |
| #15 | completed | [定義封裝、授權與發布界線](https://github.com/wicanr2/colonization_cht/issues/15) | `verification-matrix`, `formal-field-reverify` | 使用者確認授權與發布方式，且可散布包不含原版素材。 |
| #16 | completed | [建立機器可讀工作清單與驗證入口](https://github.com/wicanr2/colonization_cht/issues/16) | — | JSON、render 與 verify 可在 Docker 內重跑，且每筆都連到 Issue。 |
| #17 | completed | [建立專案 README 與第一輪目標文件](https://github.com/wicanr2/colonization_cht/issues/17) | — | README 說明用途、現況與權利邊界；目標 001 保留可驗證的初始範圍與退出條件。README 不列逐輪目標。 |
| #18 | completed | [確認目標版本執行策略](https://github.com/wicanr2/colonization_cht/issues/18) | `boot-baseline` | 使用者確認 DOS 輸入策略，並回填 CONTEXT、目標與受影響工作依賴。 |
| #19 | completed | [盤點固定 Windows 3.x NE 版本的載入、匯入與資源證據](https://github.com/wicanr2/colonization_cht/issues/19) | `input-inventory`, `research-toolchain` | 固定雜湊的 NE header、區段、匯入與資源有 Docker 可重跑清冊、交叉格式核對與未知界線。 |
| #20 | completed | [盤點使用者提供的 DOS 版並建立 dosgolem 冷啟動收據](https://github.com/wicanr2/colonization_cht/issues/20) | `input-inventory`, `research-toolchain`, `win16-execution-decision` | DOS 輸入 manifest、固定啟動入口、Docker probe 收據與下一個可見檢查點都可回查。 |
| #21 | completed | [建立 DOS OPENING.EXE 的第一個可見畫面或轉交收據](https://github.com/wicanr2/colonization_cht/issues/21) | `dos-input-cold-boot-probe` | 正式 OPENING.EXE 冷啟動有可重播的非零畫面、可觀測文字輸出、經確認的 VICEROY.EXE 轉交，或最小具體 blocker。 |
| #22 | completed | [為 Colonization 的 0x220 OPL 相容層建立 DRAFT／READY 規格](https://github.com/wicanr2/colonization_cht/issues/22) | `dos-first-visible-checkpoint` | 以固定埠序列與公開硬體契約完成最小 DRAFT、證據審查與 READY 規格；不實作、不做逐週期音訊考古。 |
| #23 | completed | [依 READY 規格驗證 Colonization 的 OPL 相容層與首畫面](https://github.com/wicanr2/colonization_cht/issues/23) | `colonization-opl-compatibility-spec` | 依 READY 規格最小實作後，正式 OPENING.EXE 冷啟動取得可見／轉交收據，或以新證據縮小 blocker。 |
| #24 | completed | [釐清 PSOUND 後續控制流進入映像外位址的受阻點（blocker）](https://github.com/wicanr2/colonization_cht/issues/24) | `colonization-opl-compatibility-checkpoint` | 正式冷啟動定位第一個進入映像外 offset 的控制轉移／堆疊邊，並以證據判定最小缺口；若足夠只建立 DRAFT。 |
| #25 | completed | [釐清開場滑鼠事件與正常遊戲啟動鏈](https://github.com/wicanr2/colonization_cht/issues/25) | `psound-post-profile-control-flow` | 以同狀態座標對照釐清開場滑鼠的作用，並由 dosgolem 重生至少一條進入實際遊戲畫面的正常玩家路徑，或留下具體服務缺口。 |
| #26 | completed | [建立第一條真實訊息的繁體中文顯示垂直切片](https://github.com/wicanr2/colonization_cht/issues/26) | `dynamic-overlay-ready` | 一則真實動態訊息完成中文顯示、英文／缺譯回退、幾何與正常玩家路徑驗證；靜態候選另依證據資格處理。 |
| #27 | completed | [建立可追溯的全遊戲繁體中文譯文語料](https://github.com/wicanr2/colonization_cht/issues/27) | `dynamic-coverage` | 已辨識玩家可見文字有可追溯譯文、占位符與控制碼驗證、字型覆蓋及分別列出的草稿／正常路徑／顯示驗收量測。 |
| #28 | completed | [重排難度畫面標題並逐欄調整中文字級](https://github.com/wicanr2/colonization_cht/issues/28) | — | 以原版同狀態畫面量測標題及各欄原文字級、對齊與安全矩形；可丟棄版式對照供使用者確認，正式畫面更符合原版風格且每欄中文字級獨立驗證。 |
| #29 | completed | [追查選國後姓名畫面文字來源與安全中文覆蓋](https://github.com/wicanr2/colonization_cht/issues/29) | `normal-gameplay-route`, `dynamic-text-draft` | 正常玩家輸入可重播提示與預設名來源、輸入語意、逐欄安全矩形、原文回退及正式中英文同狀態驗收。 |
| #30 | completed | [追查並中文化首次國家介紹畫面與長文排版](https://github.com/wicanr2/colonization_cht/issues/30) | `player-name-screen`, `dynamic-text-draft` | 正常玩家從姓名畫面進入首次國家介紹；標題與長文有原版來源、可追溯繁中譯稿、逐段安全矩形、溢出／分頁回退及中英文同狀態驗收。 |
| #31 | completed | [遊戲選項視窗：鍵盤快捷鍵、其他國家與存檔後開窗驗證](https://github.com/wicanr2/colonization_cht/issues/31) | `dynamic-overlay-implementation` | 鍵盤快捷鍵切換、其他三國與存檔後開窗各有原版事件證據與中英同輸入收據；不通過的路徑保留英文並記錄原因。 |
| #32 | completed | [退休確認框三欄中文化](https://github.com/wicanr2/colonization_cht/issues/32) | `dynamic-overlay-implementation` | 使用者選定版式後規格028升 READY，正式前端中英同輸入（Yes／No 兩分支、游標遮擋）與真 GUI 驗收後 CONFORMED。 |
| #33 | completed | [第三張難度卡「征服者／普通」中文化](https://github.com/wicanr2/colonization_cht/issues/33) | `dynamic-overlay-implementation` | 使用者選定 A／B 後規格016第三卡升 READY，正式前端中英同輸入與游標／離頁負例、真 GUI 驗收後 CONFORMED，第一二卡不退步。 |
| #34 | completed | [其餘三張國家旗卡紅字中文化](https://github.com/wicanr2/colonization_cht/issues/34) | `dynamic-overlay-implementation` | 其餘三張旗卡逐張有原版事件、底圖、字級候選與使用者確認，升 READY 後正式前端與真 GUI 驗收 CONFORMED。 |
| #35 | completed | [其餘九張開場字幕 @BUILD2～10 中文化](https://github.com/wicanr2/colonization_cht/issues/35) | `dynamic-overlay-implementation` | 九張字幕逐張有當次事件、底圖、真 VGA 同步與換頁撤銷證據，正式前端與真 GUI 驗收後逐張 CONFORMED。 |
| #36 | completed | [觸發並中文化首則教學提示（help）](https://github.com/wicanr2/colonization_cht/issues/36) | `normal-gameplay-route` | 正常玩家可重現觸發首則 help 並有原版印字事件；help 視窗 DRAFT 規格與使用者確認的版面，後續依 READY／CONFORMED 流程接正式前端。 |
| #37 | completed | [海上主畫面選單列與右側狀態欄中文化](https://github.com/wicanr2/colonization_cht/issues/37) | `dynamic-text-draft` | 選單列與狀態欄分類靜態／動態字，逐欄有原版事件、底圖、重印閘門與使用者確認的版面，正式前端與真 GUI 驗收後 CONFORMED。 |
| #38 | completed | [語料定稿後重驗正式欄位](https://github.com/wicanr2/colonization_cht/issues/38) | `translation-corpus` | 目標156改稿影響的欄位（134、135、136、137、141、142、143、150）重跑真 GUI、中英同輸入重播與檢查器 PASS；新全面回歸基準；驗證矩陣無待重驗列。 |
| #39 | completed | [功能鍵、數字鍵盤與組合鍵轉送](https://github.com/wicanr2/colonization_cht/issues/39) | — | 逐鍵單元測試；真 GUI 實按 F1 報告與數字鍵盤移動，中英同輸入重播一致；規格024 擴充段 CONFORMED。 |
| #40 | completed | [GUI 驗證腳本改為步數對齊](https://github.com/wicanr2/colonization_cht/issues/40) | — | 點擊序列以步數對齊；高負載下三國選國各重跑兩次都正確。 |
| #41 | completed | [通用對話框整句中文覆蓋引擎](https://github.com/wicanr2/colonization_cht/issues/41) | `translation-corpus` | READY 規格；至少三類真實訊息正常路徑顯示中文，中英重播一致，負例回原文。 |
| #42 | completed | [國王接見、GAME 下拉選單、載入訊息與版本字串](https://github.com/wicanr2/colonization_cht/issues/42) | `dialog-overlay-engine` | 四處各有 RE 證據、規格、真 GUI 與中英同輸入驗證。 |
| #43 | completed | [其餘 23 則教學提示](https://github.com/wicanr2/colonization_cht/issues/43) | `dialog-overlay-engine` | 各則有正常路徑觸發證據與真 GUI／中英重播驗證，或記錄無法觸發原因。 |
| #44 | completed | [殖民地、歐洲港口、報告與百科畫面](https://github.com/wicanr2/colonization_cht/issues/44) | `function-key-forwarding`, `dialog-overlay-engine` | 逐畫面普查、規格與真 GUI／中英同輸入收據；含目標167 移交的 @TUTORIAL3、4、6～10、12、15～19。 |
| #45 | completed | [全可達文字普查與完成清冊](https://github.com/wicanr2/colonization_cht/issues/45) | — | 機器可讀清冊（畫面×文字來源×機制×狀態）與分類報表；後續畫面 Issue 依此驗收。含 #44 移交：BUY 說明框、武裝面板、多人口殖民地、建造清單捲動、百科其餘條目與 Miscellaneous／Complete 類別、目標167 移交的 @TUTORIAL3、4、6～10、12、15～19。 |
| #46 | completed | [對話框選項列與輸入欄中文化](https://github.com/wicanr2/colonization_cht/issues/46) | `dialog-overlay-engine` | 規格與三種選項框、一種輸入框正常路徑中英同輸入驗證，負例回原文。 |
| #47 | planned | [dosgolem：OPL2／OPL3 FM 合成（移植 ymfm）](https://github.com/wicanr2/colonization_cht/issues/47) | — | 決定性取樣輸出、對 ymfm 單元對拍、BSD-3 授權告知。 |
| #48 | planned | [dosgolem：Sound Blaster DSP 數位音效與混音](https://github.com/wicanr2/colonization_cht/issues/48) | `opl-synthesis` | DMA 播放與混音的決定性取樣；本遊戲音效事件同輸入重現。 |
| #49 | planned | [前端音訊輸出與中英同狀態驗證](https://github.com/wicanr2/colonization_cht/issues/49) | `opl-synthesis`, `sb-dsp-audio` | 真 GUI 可聽見音樂與音效，WAV 與無頭取樣一致；開關音訊原版狀態相同。 |
| #50 | planned | [發行：Linux AppImage](https://github.com/wicanr2/colonization_cht/issues/50) | — | 可重現 AppImage、乾淨容器 smoke、原版不入包。 |
| #51 | planned | [發行：Windows x86_64](https://github.com/wicanr2/colonization_cht/issues/51) | — | 容器內交叉編譯與 Wine smoke，原版不入包。 |
| #52 | planned | [發行：macOS](https://github.com/wicanr2/colonization_cht/issues/52) | — | osxcross universal 編譯、lipo／簽章檢查，記錄驗證層級。 |
| #53 | planned | [完整版封裝與 Release](https://github.com/wicanr2/colonization_cht/issues/53) | `colony-europe-reports-rest`, `dialog-options-inputs`, `frontend-audio`, `general-event-dialogs`, `main-game-screens`, `natives-diplomacy`, `pedia-rest`, `reachable-text-census`, `release-appimage`, `release-macos`, `release-windows`, `remaining-dynamic-spots`, `remaining-tutorial-help`, `sea-menus-names`, `start-save-tutorial-woodcut`, `war-independence-ending` | 依賴全部完成、驗證矩陣全 PASS、三平台封包與 Release。 |
| #54 | planned | [推廣影片（1～2 分鐘）](https://github.com/wicanr2/colonization_cht/issues/54) | `full-release` | 可重現錄製與剪輯腳本、MP4 附在完整版 Release。 |
| #55 | planned | [海上地圖、下拉選單與名稱字串](https://github.com/wicanr2/colonization_cht/issues/55) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |
| #56 | planned | [殖民地、歐洲港口、報告與國會的其餘欄位](https://github.com/wicanr2/colonization_cht/issues/56) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |
| #57 | planned | [百科其餘條目](https://github.com/wicanr2/colonization_cht/issues/57) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |
| #58 | planned | [原住民村落與外交訊息](https://github.com/wicanr2/colonization_cht/issues/58) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |
| #59 | planned | [戰爭、獨立戰爭與結局訊息](https://github.com/wicanr2/colonization_cht/issues/59) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |
| #60 | planned | [一般事件訊息](https://github.com/wicanr2/colonization_cht/issues/60) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |
| #61 | planned | [開局、存讀檔、教學提示其餘與事件版畫](https://github.com/wicanr2/colonization_cht/issues/61) | `reachable-text-census` | docs/text-census.tsv 中本 Issue 範圍的列由「機制已有待接」變為「已顯示中文」或附理由改列「無法正常觸發」；真 GUI、中英同輸入、反向對照。 |

## 驗證

```text
tools/worklist.py verify
```
