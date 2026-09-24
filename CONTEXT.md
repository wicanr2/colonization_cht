# 目前脈絡

更新：2026-09-24；本檔只記目前真相，逐輪證據見 [RESEARCH-LOG.md](RESEARCH-LOG.md)，歷程見 [WORKLOG.md](WORKLOG.md)。

下一工作入口：沿[目標105](docs/goals/105-first-tutorial-player-path.md)
已驗 `@BUILD1` 字幕，查明開場畫面後續按鍵消費與相位，
再尋找首則真正顯示的教學訊息；`@TUTORIAL1` 目前只證實
DOS 預讀。四國介紹長文版式另待使用者選擇，不能由旗卡字級推定。

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
| 說明雙語語料 | `text/help-bilingual.tsv`另含24則教學／地圖編輯說明的原文及繁中草稿，兩個固定原版檔案與每則位元組指紋可回查；僅限私有repo，未整合正式執行期語料。`@TUTORIAL1` 已有正常路徑 DOS 預讀，仍未取得畫面印字；不可與前列369筆直接相加當顯示完成度。 |
| README 玩家補充語料 | `text/readme-bilingual.tsv`含 DOS ZIP 內 `README.TXT` 的7段版本修正、地圖編輯器與作弊模式原文／繁中草稿。封存檔、成員檔、位元組範圍與片段 SHA 均固定，按鍵／符號／Tab及Cubic 11覆蓋通過，缺字0；它不是執行期鍵，未命中畫面。 |
| 殖民地名稱語料 | `text/colony-bilingual.tsv`含 `COLONY.TXT` 的173筆預設名稱（英36、法66、西39、荷32）；18個年份依使用者決定呈現為「中文名稱（原名，年份）」。ZIP／成員／章節／行與片段 SHA、年份與格式驗證通過，字型字元缺字0；沒有畫面命中、安全矩形或欄位專屬中文字級。 |
| 中文顯示 | 主選單五列、難度頁兩行標題、完成提示、第一及第二張卡片各兩行、國家頁左側兩行、第一張國家旗卡兩行、姓名固定提示一行，共十七段有原版事件與逐幀覆蓋；規格012／014／015／017／018／019／020／021／023為各自限定範圍 CONFORMED。難度標題依使用者 A 版採34／38px共同置中；第一張旗卡依另一個使用者 A 決定採21／25px紅字／黑影。真視窗新舊版及英文控制原版同狀態，旗卡新增差異僅在兩個安全矩形；私有截圖已驗後更新。姓名提示採38px且真視窗原版同狀態；正常玩家路徑已抵達首次國家介紹，仍非正式完整玩家版，Issue #26保持開放。 |
| 第一張難度卡片 | confirmed：稱號從 `NAMES.TXT:0x00000C0C`、副標從 `LABELS.TXT:0x000008A9` 載入，經原版緩衝與格式化印字路徑繪至畫布；`GAME.TXT` 同文不是此路徑稱號來源。規格017限定第一張卡片兩行為 CONFORMED：21／25px 逐欄字模、當次有紋理底圖、原文差分、游標及真實 TSV 缺鍵回退已接正式前端並與同輸入英文控制同狀態；其餘卡片仍屬規格016 DRAFT。 |
| 第二張難度卡片 | confirmed：真 Ebitengine 視窗點擊 `(265,55)` 顯示 `EXPLORER:`／`Easy`，雙次 dosgolem 收據閉合 `NAMES.TXT:0xC18`／`LABELS.TXT:0x8B2` 至 RAM、格式化印字與原始畫布；墨跡高5／6像素、有紋理底圖。規格019限定兩行為 CONFORMED：「探險家／簡單」採21／25px逐欄字模，真視窗中文與英文控制原版同狀態；各欄缺譯／重複鍵及游標回退、錯版本拒絕與第一張卡片回歸均通過。規格016對其餘卡片仍為 DRAFT。 |
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
