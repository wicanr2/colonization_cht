# 目標084：國家選擇頁兩行標題的執行期守門與限定顯示

狀態：completed（僅國家頁左側兩行）；日期：2026-09-23。承接[目標083](083-post-difficulty-player-path.md)
與[規格020](../spec/020-nation-heading-overlay.md)；對應 Issue
[#7](https://github.com/wicanr2/colonization_cht/issues/7)、
[#12](https://github.com/wicanr2/colonization_cht/issues/12)、
[#14](https://github.com/wicanr2/colonization_cht/issues/14)及
[#26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 範圍與前置證據

目標083已從合法 DOS 冷啟動、主選單、難度頁滑鼠完成區抵達
`NATIONS.PIK`；`LABELS.TXT:0x8D3`／`0x8DB` 的原文
`Select`／`European Power` 已閉合至 RAM、格式化輸出與畫布差分。
四倍畫布的逐欄 38px 候選「選擇／歐洲國家」只通過可丟棄預覽；
正式 Ebitengine 畫面仍顯示英文。這輪不把前輪 DRAFT 當成 READY。

## 工作與退出條件

1. 先推送本目標至已核對為 PRIVATE 的儲存庫。固定原版檔案 SHA-256、
   隔離 dosgolem 提交、真實 TSV、Cubic 11 字型及前輪重播輸入；
   原版唯讀，研究、建置、畫面與測試僅在有界 Docker 容器。
2. 建立可丟棄執行期探針，從同一正常玩家路徑擷取**當次**兩行印字前
   底圖，逐欄核對原文 NUL、來源及格式化讀取、畫布差分點數／bbox、
   安全矩形和原版索引畫面。兩個補片不得互借；在游標進出、滑鼠按鍵、
   場景變更、舊底圖或缺字模時，各欄回退原文且無中文殘影。
3. 雙次重播執行期探針，與同輸入無觀測控制組比較 CPU、完整 RAM、
   原版畫布／索引畫面、色盤及虛擬時間。若證據足夠，審查規格020的
   輸入、狀態、輸出與失敗模式後升為**限定 READY**；否則保持 DRAFT，
   明寫缺口，不修改正式前端。
4. 只有 READY 才能將真實 TSV 唯一譯文與逐欄字模接入既有輸出層。
   隨後以真 Ebitengine 視窗從冷啟動重播中文／英文控制、兩欄各自
   缺鍵／重複鍵、游標進出及錯版本拒絕；比對原版同狀態、安全區外
   零新增差異與原有十二段回歸。全通過才標記規格020限定 CONFORMED。
5. 更新目前脈絡、研究紀錄、工作歷程及相關 GitHub Issue，推送私有
   儲存庫；收尾核對原版素材、字型、快照與含原版像素的 PNG 未入 Git，
   並檢查檔案擁有權與 Docker 容器清理狀態。

## 停止線

不更改原版 EXE／TXT、RAM、規則、滑鼠命中區、存檔或玩家流程。
不擴張至國家旗幟卡片、完成提示、help 或全遊戲完成度；若新證據
推翻既有標題幾何，回到 DRAFT 而非猜補。Issue #28 的難度頁標題
重排仍是獨立的下一階段，這輪不替使用者選 A／B 版式，也不更新
既有含原版像素的私有截圖。

## 本輪結果

雙次 dosgolem 執行期守門與獨立反例通過後，規格020先升限定 READY，
才接入正式 Ebitengine 前端。16筆實際輸入的中文與英文控制原版同狀態；
兩欄真 TSV 缺鍵／重複鍵、游標進出、滑鼠按鍵與切場清除、錯版本拒絕
均通過。正式中文只改各自安全矩形2,611／5,502個輸出像素。
舊版第一／二張難度卡片同輸入逐位元組相同，主選單與難度頁15個
檢查點亦不變。獨立正式驗證收據 SHA-256
`84da4515020fbccddb2c927deeb99d68261ff1da17d74be62dd20e677d30e678`；
證據與限制見[規格020](../spec/020-nation-heading-overlay.md)。
正式顯示段數由十二增至十四；其他國家頁文字、help、完整鍵盤與遊玩
仍未驗收。[Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)
的難度標題排版仍留待下一階段，不在本輪選定 A／B 或更新截圖。
