# 《殖民帝國》繁體中文化（Colonization CHT）

《Sid Meier's Colonization》（MicroProse，1994）是經營殖民地、調配資源與貿易，最後爭取獨立的歷史策略遊戲。本專案讓繁體中文玩家能直接讀懂遊戲裡的選單、訊息與說明。

做法是「顯示轉譯層」而不是重製：原版 DOS 程式、規則、資料與存檔都不修改，由 [dosgolem](https://github.com/wicanr2/dosgolem) 模擬執行；本專案在原版把文字畫到畫面的那一刻辨識出是哪一句，再於放大後的畫面上疊上中文。辨識不到或證據不足的地方保留英文，不猜。

## 遊戲背景與《殖民帝國》的起源

《殖民帝國》是 MicroProse 於 1994 年推出的回合制策略遊戲，延續《文明》的經營與策略設計，把焦點放在美洲殖民地的成長與獨立。玩家選擇英國、法國、荷蘭或西班牙，從探索海岸、建立聚落開始，安排居民生產、加工與貿易，再處理原住民關係、歐洲列強競爭及母國的要求，最後爭取獨立。[官方遊戲介紹](https://store.steampowered.com/app/327400/Sid_Meiers_Colonization_Classic/)

遊戲題材源於十五世紀末以後的歐洲跨洋擴張。哥倫布在西班牙王室支持下尋找通往亞洲的西行航路，1492 年的航行促成歐洲與美洲持續接觸，後續發展為探索、征服與殖民。當時美洲已有眾多原住民族、語言與社會；遊戲所稱的「新世界」，反映的是歐洲來者的視角。[美國國會圖書館：哥倫布的航行](https://www.loc.gov/exhibits/1492/columbus.html)、[1492 年以前的美洲](https://www.loc.gov/exhibits/1492/america.html)

## 當年北美移民的情況

十七至十八世紀的移民有不同處境。有人參與商業殖民事業，有人為宗教生活遷徙，也有人為擺脫貧困與債務而遠行。1607 年建立的詹姆斯敦是北美第一個永久英國殖民聚落，由維吉尼亞公司資助；新英格蘭的清教徒聚落及其他宗教群體，則呈現了不同的移居動機。[美國國家公園署：詹姆斯敦簡史](https://www.nps.gov/jame/learn/historyculture/a-short-history-of-jamestown.htm)、[美國國會圖書館：探索與定居](https://www.loc.gov/exhibits/british/brit-1.html)

並非每個人都付得起船費。部分歐洲移民簽下契約，以多年勞動換取渡海機會；也有受判流放者被運往殖民地。抵達之後，生活仍受食物、疾病與補給限制，早期詹姆斯敦曾經歷嚴重飢荒。這些處境有助理解遊戲中的契約僕役、移民與糧食管理。[美國國會圖書館：契約僕役、學徒與流放者](https://guides.loc.gov/indentured-servants)、[詹姆斯敦簡史](https://www.nps.gov/jame/learn/historyculture/a-short-history-of-jamestown.htm)

跨大西洋人口移動也包含被奴役、遭強迫運送的非洲人，不能都視為自願移民。殖民擴張同時改變原住民族的土地與生活，帶來貿易、衝突與剝奪。遊戲把這段歷史簡化成策略系統，背景介紹與實際歷史仍須分開閱讀。[美國國會圖書館：移民與遷徙](https://www.loc.gov/collections/songs-of-america/articles-and-essays/historical-topics/immigration-and-migration/)

## 下載與執行

[完整功能修正版 v.1.0.3-20261010](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.3-20261010)提供 Linux x86_64 AppImage、Windows x86_64 ZIP、macOS Intel／Apple Silicon 通用 ZIP，以及重新製作的90秒推廣影片。本版修復英國新局停止，收錄目前完成的文字重繪、殖民地、港口與貿易接線，以及中文顯示、輸入、音樂與音效功能。部分情境仍保留原文。

需要自己合法取得的 DOS 版 COLONIZE 目錄。公開封包不含原版檔案；程式依包內 `MANIFEST.json` 的 SHA-256 核對版本，不符就拒絕啟動。

| 平台 | 執行方式 | 預設存檔位置 |
|---|---|---|
| Linux | `chmod +x *.AppImage`，再執行 `./colonization-cht-v.1.0.3-20261010-linux-x86_64.AppImage --game /你的路徑/COLONIZE` | `~/.local/share/colonization-cht/save` |
| Windows | 解包後執行 `colonization-cht.bat --game "C:\你的路徑\COLONIZE"` | `%LOCALAPPDATA%\colonization-cht\save` |
| macOS | 解包後在終端執行 `./colonization-cht.sh --game /你的路徑/COLONIZE` | `~/Library/Application Support/colonization-cht/save` |

Linux需要X11、OpenGL與ALSA；FUSE不可用時，在AppImage檔名後先加 `--appimage-extract-and-run`。Windows已以Wine驗證；macOS已驗雙架構建置、臨時簽章資料與封包，尚未真機、Gatekeeper或最低系統驗收。

原版目錄只讀。可用環境變數 `COLONIZATION_CHT_SAVE` 改存檔位置。預設播放音樂與音效，`--audio-mute` 可靜音。鍵盤包含F1～F10及修飾鍵、數字鍵盤與導覽鍵；輸入法及非英數輸入不轉送。遊戲節奏與原版實機不同。舊技術預覽版保留於Releases。

音樂由原版驅動獨立原速播放，供給與主DOS速度分開。即時消費抽樣沒有音樂缺樣；曲目自然結束後仍等待原版下一首指令。數位音效保留原路徑，尚未音效卡或人耳驗收。主選單游標遮擋時會暫時顯示原文，已抽樣的移開操作恢復中文；使用者回報的持續英文仍在追蹤。

## 目前狀態

英國發現者新局停止已修復，正常世界入口、三側同狀態與既有存檔回歸通過。殖民地、歐洲港口、報告與國會的剩餘接線已完成，經代表性正常路徑及回退抽樣驗收，並收進本版三平台封包。[遊玩驗證](docs/goals/185-player-experience.md)保存修復與抽驗範圍；未抽樣的條件訊息與建造換頁仍保留待驗，見[完成範圍](docs/goals/181-colony-remaining.md)。

**畫面上已經是中文的部分**（每一欄都有原版事件或畫面指紋證據，並以中英同輸入重播驗證原版狀態不變）：

- 開場製作名單職稱、主選單、難度頁、國家選擇頁與四張旗卡、姓名提示
- 四國首次國家介紹（各兩頁）
- 英國開局的十張開場字幕、首則教學提示（發現者難度）
- 海上主畫面的選單列、回合訊息與右側狀態欄
- 遊戲選項視窗（標題與八列）、退休確認框
- 對話框正文：原版印出的訊息以模板整句比對 GAME.TXT 譯稿後改排中文，已在正常路徑驗證新大陸命名、登陸詢問與原住民訊息。原住民村落學習的兩列選項已顯示中文，正常接受與完成已抽樣核對；其他選項列與輸入欄標籤也有已驗證的中文覆蓋，輸入內容維持原樣。
- 存讀檔標題、正常空槽與存檔描述清單、成功提示及正常關閉；姓名及檔名保留原值。載入訊息、主選單版本字串、國王接見卷軸、GAME 下拉選單。
- 教學提示：正常路徑已驗發現新陸地、母港新移民、輕帆船、拓荒者與士兵等五則。
- 殖民地畫面首屏（標題、港口欄、離開按鈕）與海上狀態欄的地形、單位、載貨；殖民地名稱顯示「中文（原名）」。
- 歐洲港口標題、按鈕、提示正文與招募／購買／訓練清單的正常取消操作，以及 F1～F10 已抽樣的報表欄位；議會下次會期與反叛加分已補齊。正常500$砲台購入確認及接受、職業清單選漁夫的未建碼頭提示已驗；碼頭單位十種完整選單、取消傳教士身分、移到碼頭最前面與登船切換後的清單復原、購輕帆船後的裝載標題也已驗證；三處報表城名採22px單行及擴大文字區，正常抽樣已通過。其他單位與局勢待驗。
- 殖民百科：正常路徑已驗六類清單的150篇正文，包含百分比與教育建築條列；22個建築先決條件也已逐頁驗證；正常地形21次查詢來源已核對，其他百科入口及八個額外地形段落的情境路徑仍待驗。
- 殖民地畫面內操作：職業選單（含第二頁六項裝備需求與停用灰色）、建造清單、建築與貨物懸停標籤、資金不足與可支付貨車購買正文／兩項選擇；議會五項元勳顧問選項、棄城確認正文與取消返回城市已驗證；右下單位面板的士兵標題、當次三個選項及駐守後的清除命令三列已驗證；正常港口輕帆船標題、空貨艙／載貨／下錨三種已觀測選單、抵港教學與關閉也已驗證；毛皮裝貨標題、按住拖曳提示及移入船隻／城市訊息已驗證，玩家自訂城市名保留原名。其他商品、船型與單位狀態待驗。
- 第一條海上／陸上貿易路線的編輯器、裝卸貨提示與目的地清單；目前源碼另已驗第二條海上路線標題、第三London／第四Jamestown、取消與刪除後重加。玩家路線名保留原字，其他編號與自動跑商待驗。
- 歐洲港口的殖民地居民頂列、木匠職業與食物買賣價格已接入中文；十點正常玩家輸入重播與缺字模回退抽樣通過。其他商品／職業的排版投影與實際畫面驗證分開記錄。
- 事件版畫的「發現新世界」、「遇見原住民」與「進入印地安人村莊」標題已顯示中文。正常輸入抽樣確認原圖不變，關閉後恢復其他中文覆蓋；其餘事件尚未抽樣。
- 輸入欄標籤（名稱、殖民領地、數量）；城市改名提示、姓名編輯與取消已驗證，輸入框內的英文字元保留原樣。
- 頂端下拉選單（遊戲、檢視、命令、報告、貿易、殖民百科），包括已驗證的命令選單灰色停用項目；Jamestown 地圖標籤顯示「詹姆斯敦（Jamestown）」。狀態欄被對話框部分遮擋時整行暫藏，關閉後恢復；正常讀檔後的地圖城名與船隻命令清單也已驗證。
- 音樂與音效：OPL3 FM 音樂（ymfm 移植）與 Sound Blaster 數位音效，前端 `--audio --sb-digital` 播放。

全可達文字的逐畫面普查見 [docs/text-census.md](docs/text-census.md)，分為已顯示、待驗與不可達，並區分可重驗及歷史證據。公開封包與目前源碼的驗收範圍見[目前脈絡](CONTEXT.md)；尚未驗證所有可達畫面。

**譯稿已完成**：全遊戲 TXT 文字共 3,561 行，3,558 行已有繁中譯文，三行英文冠詞刻意省略。來源、占位符與字型覆蓋可由[整批驗證入口](docs/goals/160-corpus-closure.md)重跑。譯文完整與畫面接線分開統計；後續先接入譯稿，最後以代表性正常路徑抽樣對拍，未抽樣欄位保留待驗。

術語以第三波中文版說明書為準，見[定稿譯名表](text/terms.zh-Hant.tsv)。各畫面的驗證結果見[驗證矩陣](docs/verification-matrix.md)，詳細現況見 [CONTEXT.md](CONTEXT.md)。

## 畫面

![殖民百科的繁體中文皮衣廠說明與先決條件](docs/screenshots/colonizopedia-zh.png)

殖民百科的皮衣廠條目：正文與先決條件已顯示中文，保留原版版畫。這是[正常玩家路徑驗證](docs/goals/180-pedia-remaining.md)的實際遊戲截圖。

![Ebitengine 視窗中的繁體中文主選單](docs/screenshots/menu-zh.png)

主選單五列選項由原版印字事件觸發中文；原版大型標題維持英文。

![Ebitengine 視窗中的繁體中文難度頁](docs/screenshots/difficulty-zh.png)

難度頁：兩行標題依原版共同中心線排版，第一張卡片「發現者／最簡單」。

![Ebitengine 視窗中的第一張國家旗卡](docs/screenshots/nation-card-first-zh.png)

國家頁：旗卡兩行依原版字高分別用 21／25px，保留紅字黑影風格。這張截圖拍攝於國名改用說明書譯名之前，現行版本上欄是「英國：」。

四國介紹長文的早期版面對照：[A 頁](docs/screenshots/nation-intro-layout-draft-a.png)、[B 頁](docs/screenshots/nation-intro-layout-draft-b.png)（每列依序為原版與兩種中文候選）。

## 開發與研究入口

所有建置、遊戲執行、分析與抓圖都在 Docker 容器內進行，需要自備合法原版。

- [目前脈絡](CONTEXT.md)、[工作計畫](WORKLIST.md)（由 `docs/worklist.json` 產生）
- [多語系、HD 切換與實際遊玩影片規劃](docs/goals/186-display-settings-and-gameplay-video.md)及可丟棄操作原型；新增功能尚未收進目前發行版。
- [規格](docs/spec/)與[各輪目標](docs/goals/)
- [驗證矩陣](docs/verification-matrix.md)（`tools/verification_matrix.py` 產生）
- [研究證據](RESEARCH-LOG.md)與[工作歷程](WORKLOG.md)
- [字型來源](font/README.md)、[專案規則](AGENTS.md)
- 正式交付與影片：[目標183](docs/goals/183-release-and-promo.md)列出建置、版號、封裝、啟動抽樣、剪輯及彙整入口。[規格044](docs/spec/044-release-and-promo.md)記錄驗證範圍。
- Linux 效能與播放修正、README百科截圖及影片配樂：[目標184](docs/goals/184-linux-player-regressions.md)保存修正版收據與重跑入口；[規格045](docs/spec/045-linux-runtime-performance.md)限定合成與播放邊界的驗證範圍。
- 封裝：以 [字模重烘入口](tools/rebake_release_fonts.sh)綁定現行譯稿，或依[規格044](docs/spec/044-release-and-promo.md)核對已驗正式包的字模、manifest與現行譯稿，再於固定Go1.26.7容器執行 `tools/package_release.py`。工具恢復與重建入口見[遊玩驗證](docs/goals/185-player-experience.md)。AppImage使用`--format appimage`，工具與驗證範圍見[規格041](docs/spec/041-linux-appimage.md)；Windows ZIP使用`--format windows-zip`及[Windows說明](tools/release/README.windows.txt)，見[規格042](docs/spec/042-windows-zip.md)；macOS通用ZIP使用`--format macos-zip`及[macOS說明](tools/release/README.macos.txt)，見[規格043](docs/spec/043-macos-zip.md)。macOS只驗建置、簽章資料與封包，尚未真機執行。各格式都依實際二進位收集Go、模組與dosgolem授權，缺授權或工具版本不符就停止。
- 容器內前端組裝：[tools/build_window_prototype.py](tools/build_window_prototype.py)依已驗來源指紋產生可建置的Go工作目錄；使用下述驗證映像與本專案隔離dosgolem，輸出只放workplace。
- 畫面檢查與前端測試：[驗證工具鏈](tools/Dockerfile.verification)（`colonization-verification:20260930-r1`，含 Pillow、Go、Ebitengine 與 Xvfb）；封存檔盤點與 probe 仍使用專案指定的研究映像。

## 授權、致謝與聲明

本專案採[復古重製 source-available 授權條款 1.0（RRSAL-1.0）](LICENSE)：非商業用途免費，可修改與再散布；遊戲實況、影片、評論與報導明示允許（含平台分潤）。商業用途請先洽 wicanr2@gmail.com，歡迎來談。這是 source-available 授權，不是開放原始碼（open source）授權。

- **不在授權範圍內**：原版遊戲的執行檔、資料、畫面、文字與說明書，屬於 MicroProse 及其權利承繼人或各自的權利人。儲存庫裡的截圖、譯稿中的原版英文對照、量測座標與畫面指紋、第三波說明書術語對照，其中屬於原版的部分依授權第 2 條 (c) 處理。
- **第三方元件**：中文字型[俐方體11號（Cubic 11）](https://github.com/ACh-K/Cubic-11)與以它烘製的字模依其授權（[全文](font/Cubic-11-OFL.txt)）；[Ebitengine](https://github.com/hajimehoshi/ebiten) 依 Apache-2.0。
- 本專案與 MicroProse、其權利承繼人及第三波沒有任何隸屬、合作或授權關係。
