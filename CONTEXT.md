# 目前脈絡

更新：2026-09-23；本檔只記目前真相，逐輪證據見 [RESEARCH-LOG.md](RESEARCH-LOG.md)，歷程見 [WORKLOG.md](WORKLOG.md)。

## 已確認決定

- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標。
- 中文化是 dosgolem 輸出階段的繁體中文覆蓋，不是 remake；不修改原版程式、資料、規則或存檔。
- 儲存庫 `wicanr2/colonization_cht` 維持 PRIVATE；原版素材與原始研究快照只保留本機，
  僅下列使用者要求的兩張可見成果截圖為私有儲存庫例外。
- 使用者本輪要求在 README 展示合適截圖；兩張經驗收的 Ebitengine 視窗圖僅在已核對為
  PRIVATE 的儲存庫內保存，公開散布仍未授權。原版輸入、字型與原始快照仍不入 Git。
- dosgolem 只修改 `workplace/dosgolem` 獨立副本；`upstream` 推送位址保持 `DISABLED`。
- 2026-09-22 使用者已確認主選單原型採 Cubic 11、24px 字級（4 倍輸出畫布）。這是該已驗證
  欄位的樣式證據，不是其他畫面的固定字級；不代表術語、完成範圍或字型散布授權已定案。
- 2026-09-23 使用者確認中文覆蓋必須依原版文字字級與欄位安全矩形調整，禁止用全域固定中文字級。
  每個覆蓋欄位須量測原版文字、中文候選字級、基線、最長譯文與回退策略；沒有專屬量測時維持
  原文並記錄命中。
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
| 翻譯草稿 | `text/draft.zh-Hant.tsv` 共368筆：GAME 96、LABELS 40、MENU 68、NAMES 70、PEDIA 19、MAPEDIT 31、MAPMENU 28、WOODCUT 14、OPENING 1、CLOSING 1；原始來源／控制碼（含 `#` 格式記號）及Cubic 11缺字檢查通過。八筆已在正常玩家路徑顯示驗收，其餘仍是候選；18個TXT／4,119粗略資料行不是全遊戲訊息分母。 |
| 百科雙語語料 | `text/pedia-bilingual.tsv` 含 `PEDIA.TXT` 的25篇建國元勳、16篇貨物、24篇單位、29篇地形、27篇職業及42篇建築，合計163篇編號文章的整段原文／繁中草稿；固定來源、控制碼（含一個保留的Tab及由原始`0xF9`正規化的`•`）與Cubic 11覆蓋通過，缺字0。未取得畫面命中或安全矩形。 |
| 說明雙語語料 | `text/help-bilingual.tsv`另含24則教學／地圖編輯說明的原文及繁中草稿，兩個固定原版檔案與每則位元組指紋可回查；僅限私有repo，未整合正式執行期語料，也未取得畫面命中。不可與前列368筆直接相加當顯示完成度。 |
| README 玩家補充語料 | `text/readme-bilingual.tsv`含 DOS ZIP 內 `README.TXT` 的7段版本修正、地圖編輯器與作弊模式原文／繁中草稿。封存檔、成員檔、位元組範圍與片段 SHA 均固定，按鍵／符號／Tab及Cubic 11覆蓋通過，缺字0；它不是執行期鍵，未命中畫面。 |
| 中文顯示 | 主選單五列、難度頁兩行標題及完成提示，共八段有原版事件與逐幀覆蓋；規格012／014／015為限定範圍CONFORMED。Ebitengine／Xvfb真視窗以九筆實際輸入到難度頁，中文、重播與英文控制原版狀態一致；兩張真視窗圖只在已核准安全區變更。仍非正式完整玩家版，Issue #26保持開放。 |
| 完整可玩／正式發行 | 未驗證、未發布；本輪僅驗證至難度選擇。 |

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

## 下一閘門

[目標064](docs/goals/064-translation-first-corpus.md)按使用者新優先順序先擴大
可追溯譯文語料；目前324筆主譯稿與24則help稿都有繁中欄，但原版18份TXT、
EXE及靜態圖像尚未建立完整玩家可見訊息分母，不宣稱全文翻譯完成。
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
最近完成入口：[目標072](docs/goals/072-readme-player-guide-corpus.md)已完成 DOS 版 `README.TXT` 的七則版本修正、
地圖編輯器與作弊模式玩家補充說明草稿；過時的 DOS／音效排錯與客服資料明確排除。固定 ZIP
來源、操作字面值及Cubic 11覆蓋通過，但不增加任何已顯示文字或 runtime 覆蓋聲明。
[目標060](docs/goals/060-help-bilingual-corpus.md)另建立24則遊戲內教學／地圖編輯說明的原文／繁中TSV，
仍是待畫面驗收的草稿。
[目標061](docs/goals/061-next-visible-text-slice.md)已驗收難度頁兩行中文標題，
真視窗圖存於私有 `docs/screenshots/`；圖內有原版像素，不得當公開發行素材。
[目標062](docs/goals/062-difficulty-finish-prompt.md)已驗收難度頁「完成後點此」提示；
限定證據、覆蓋契約與中英文同狀態結果見[規格015](docs/spec/015-difficulty-finish-prompt.md)。
[目標063](docs/goals/063-difficulty-card-text.md)接續難度卡片文字；目前僅在既有
RAM 快照找到原文候選。兩次正常路徑重播確認卡片區畫布差分，但現有讀寫監看
沒有命中候選來源與卡片逐 byte 寫入；[規格016](docs/spec/016-difficulty-card-text-draft.md)
保持 DRAFT，不計入八段完成數。
[目標059](docs/goals/059-ebitengine-display-wiring.md)讓Ebitengine視窗以明確Go介面
接到原版五列顯示，九筆真視窗輸入與中英文同狀態對拍通過。[目標058](docs/goals/058-translation-corpus-and-player-window.md)
保留當時189筆草稿及五筆畫面命中的分母。現有主譯稿已擴至324筆；全遊戲中文化、第三種輸出情境與正式玩家前端仍未完成。

已完成 [目標 054](docs/goals/054-main-menu-text-provenance.md) 的最小證據鏈；
[目標 055](docs/goals/055-first-text-prototype.md) 保存中文原型、測試與重跑入口。
目前原型為 4 倍畫布、使用者已確認 Cubic 11 的 24px 顯示，中文為「在新世界開始遊戲」。
字型僅本機使用，內嵌許可不是 OFL，尚未完成正式散布權利審查。

目標056首列已由[規格012](docs/spec/012-five-menu-lines.md)擴至五列，每列三次事件一致。
滑鼠在(128,110)時前三列的完整安全區受遮擋而回退，後兩列仍中文；移開恢復。
不宣稱游標可跨過中文而不回退。已有以`tools/build_window_prototype.py`組裝的
可撤回Ebitengine視窗，經真視窗點擊與英文控制組對拍；它仍依賴目前有限的五列適配器，尚未抽離成
正式玩家前端，也未驗失焦／關窗。難度頁兩行標題已走不同於 `937C:0538` 的
`0D3A:0015` 來源讀取與 `0D21:012C` 畫布寫入；完成提示另由 `0E2D:11CF`
讀取執行期原文；下一步追難度卡片、
help 或第三種真正不同輸出情境，不把已核准的兩行外推到其他文字。
不得直接移植 psychic-war 的整個 xlate：其 3 倍數縮放與純色抹底假設不符目前原型。
不重新開啟整個開場研究；不以無頭切片關閉要求互動交付的 Issue #26。

術語、完成範圍與授權／公開方式仍需使用者依成果決定，不能把字型大小同意擴張解讀。
