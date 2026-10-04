# 目標179：貨物百科逐篇驗證（Issue #57 第一部分）

狀態：完成（僅本目標貨物範圍）；日期：2026-10-01。對應 [Issue #57](https://github.com/wicanr2/colonization_cht/issues/57)，承接[目標171](171-colonizopedia.md)。目前入口：[CONTEXT.md](../../CONTEXT.md)。

## 範圍與依據

只擴充既有 [規格036](../spec/036-line-list-and-centered-text.md) 與 [規格038](../spec/038-string-overlay-draft.md) 的正常玩家路徑驗證，不新增正式顯示行為。從冷啟動主選單正常讀取原版存檔，再由殖民百科／貨物清單逐篇開啟 `PEDIA.TXT:@CARGO0`～`@CARGO15`。

原版、存檔、畫面與記憶體只留 `workplace/`；公開儲存庫只保存腳本、雜湊與結果摘要。本目標不代表其餘百科已完成。

## 正常玩家路徑

原版正常 GUI 自己存出的 `COLONY00.SAV` SHA-256：`cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e`，24,169 位元組。來源與存讀檔功能對照見 [RESEARCH-LOG.md](../../RESEARCH-LOG.md) 的 2026-10-01 存讀檔條目。

每次關閉百科條目回清單，原版都重設到第一項。第一版探勘只按一次 Down，因而重複開啟第二篇；第二版每次從第一項移動到指定列，實際正常進入全部 16 個不同條目。失敗探勘保留於 `goal178-orders/codex-audit/pedia-cargo-gui/`，成功現場輸入與圖在 `pedia-cargo-gui-v2/`。

## 工具與入口

- 正式前端來源 `tools/live_menu.go` SHA-256：`25a91067d94f22be59fb23325c75c76aea3b055c0f936e56d62f5ad6d5e3a481`；二進位：`25117ab6adeff11d9e687d3767c542046512daaddf61ff13bde2e8d9252415f7`。
- dosgolem 隔離副本：`b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8`，Go 1.26.7；容器入口與掛載要求沿用 [tools/Dockerfile.verification](../../tools/Dockerfile.verification) 及 [README.md](../../README.md)。
- GUI 重產：`tools/probe_goal179_gui.sh`；重播：`tools/probe_goal179_replays.sh`；獨立檢查：`tools/check_goal179_window.py --game /game --reports /repo/workplace/reports/goal179-pedia-cargo`。
- GUI 與重播都可用 `COLONIZATION_GOAL179_OUT` 指定本機收據目錄、`COLONIZATION_WINDOW_BIN` 指定當前前端、`COLONIZATION_GOAL179_SAVE` 指定上述原版正常存檔。缺合法原版或存檔入口時明確 SKIP 77，不以替代資料冒充。
- 印字位置 `0D21:00C6` 是 dosgolem 真實模式 CS:IP；收據 `source_linear` 是線性 RAM，不是原版檔案偏移。原版檔案指紋由各側 `input_hashes` 核對並合併到矩陣。
- 原版 `PEDIA.TXT` SHA-256：`cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`；檢查器另外直接核對 PEDIA 與兩份 EXE 的完整指紋。`tools/check_goal179_window.py` SHA-256：`4ca4e86c745ec14fcd3981f7d02c44a0f1477b77bab70a26db3426ea107440ae`。

## 退出條件

16 篇都以真 GUI 正常進入；中英與缺圖集負例的完整原版終點、輸入、RAM、索引及色盤一致；每篇原版來源事件、中文啟用與安全區 GUI／重播逐像素相同；缺圖集負例不得啟用百科正文。檢查器 PASS 後才接入矩陣、重產普查，僅提高實際驗到的列。

## 目前結果

第二版現場 GUI 正常進入全部 16 個不同貨物條目，現場輸入 SHA-256 `d7caadf47c24570a83571c9a3124bc28990a3a76d5b01424fe9b1f29abee803e`。真 GUI、中英與缺圖集負例的完整終點 RAM 都為 `ffab5a8f69150f76fedca2805c10763be40d33005a68adc2b06dfd2ac27f0e29`；重播各檢查點的完整 RAM、索引與色盤相同。16 篇原版來源事件與中文啟用齊備，每篇正文及 50 個字串欄位安全區真 GUI／中文重播逐像素相同、且與英文控制不同，包含 16 個效率表格標籤；缺圖集負例沒有啟用百科正文。`check_goal179_window.py` PASS，缺原版回 SKIP 77，單一原版 PEDIA 檔案異動時拒絕。正式本機收據位於 `workplace/reports/goal179-pedia-cargo/`，矩陣 PASS 28、普查與三個反向對照 PASS。普查為 1,684 列、453 已顯示、1,135 待接、96 無法正常觸發；增加的 30 列是新觀測的執行期字串，其中一列為待完成的讀檔清單，其餘均有字串安全區驗證。其餘百科仍由 Issue #57 管理，不關閉整項 Issue。
