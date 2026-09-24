# 目標111：確認教學提示開關並追首則正常玩家顯示

狀態：completed（限定選項切換與有界操作；首則 help 仍未觸發）；日期：2026-09-24。承接[目標110](110-tutorial-hints-player-trigger.md)
已驗的 `GAME` → `Game Options` → `Tutorial Hints` 原版畫面、
海上左方向鍵及[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)
的 `@TUTORIAL1` 預讀；對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與固定起點

使用者要求完整繁體中文顯示，24則 help 雖有可追溯雙語草稿，
目前仍沒有任何一則正常玩家路徑的實際畫面命中。目標110
確認選項最後一列可點、原版圖示與背景變化，但**沒有**確認
圖示代表啟用還是停用，也沒有看到 `@TUTORIAL1` 正文。
本輪要由這個已驗起點找到可重播的首則教學顯示事件，
或以有限玩家操作縮小下一個可驗觸發條件。

固定原版 DOS `MENU.TXT` SHA-256
`5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`，
`GAME.TXT` SHA-256
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
正常英格蘭十六筆玩家輸入 SHA-256
`a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`。
本專案隔離 dosgolem 固定提交
`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，
推送位址 `DISABLED`。所有原版位址／文字來源須區分
檔案位移、DOS 線性 RAM、實模式 `CS:IP`、原版320×200
畫布及四倍輸出畫布。

## 本輪工作與退出條件

1. 核對目前 Git／PRIVATE 遠端／Issue／原版與探針版本，
   **先將本目標 Markdown 推送私人儲存庫**，再做新的
   原版重播或探針變更。所有分析、建置、測試及遊戲執行
   限於無網路、限資源、非 root 的一次性 Docker 容器；
   原版唯讀，完整原文與像素只留已忽略的 `workplace/`。
2. 以目標110的原版設定視窗為起點，取得未點、點一次、
   必要時點兩次的同輸入對照；查核圖示狀態和離開視窗
   後是否持續，不把「圖示變化」直接命名為啟用／停用。
   若需判斷語意，使用玩家可見結果或原版明確資料流，
   不以任意色號猜測。

   第一組有界輸入為[只移入再移開](../../tools/goal111-hover-away.inputs.json)
   與[點擊後移開](../../tools/goal111-click-away.inputs.json)；
   兩者只差同一列的按下／放開事件，移開位置為已見
   選項框外海面 `(20,100)`。先以原版後續畫面驗證
   該位置不另觸發行為，不能以事件檔本身宣稱切換成功。
   若文字列點擊與只移入的核取形狀相同，再以
   [圖示本身點擊後移開](../../tools/goal111-icon-click-away.inputs.json)
   作原版熱區對照；這也是候選輸入，不預設圖示可點。
   若焦點仍停在最後一列，改以[只選第一列](../../tools/goal111-first-row-only.inputs.json)
   和[先選教學再選第一列](../../tools/goal111-tutorial-then-first-row.inputs.json)
   作相同最終焦點的對照，避免把焦點底色當開關值。
3. 由已見原版介面選擇一個明確的正常玩家遊戲動作，
   優先試結束回合；確認原版確實消費該輸入、畫面／
   狀態進入預期相位，再比較未點與兩種選項狀態。
   不注入 RAM、修改原版設定檔或使用測試專用直達路徑
   冒充玩家操作。探索須有界；若玩家動作無效，先修正
   操作座標／鍵值的證據，不反覆盲目加鍵。
   在已證實左方向鍵會移動海上船舶的條件下，先以
   [未改選項、ESC 後向左](../../tools/goal111-untouched-esc-left.inputs.json)
   與[切換選項、ESC 後向左](../../tools/goal111-toggled-esc-left.inputs.json)
   作同時點初探；ESC 是否真的關閉視窗、方向鍵是否
   進入海上操作，均須由原版畫面與待取數回證。
   若方向鍵路徑仍未顯示正文，先以
   [ORDERS 頂端選單候選點擊](../../tools/goal111-orders-menu.inputs.json)
   讀正常玩家可見的命令，不臆測結束回合快捷鍵。
   原版 `ORDERS` 明示 `No Orders (SPACE BAR)`；因此再以
   [未改選項、ESC 後 Space](../../tools/goal111-untouched-esc-space.inputs.json)
   和[切換選項、ESC 後 Space](../../tools/goal111-toggled-esc-space.inputs.json)
   比較，兩分支先把滑鼠移到同一海面座標。探針的 Space
   掃描碼採隔離 dosgolem 既有 `dos.KeyNamed("Space")`
   對應的 `0x39/0x20`；原版是否真的跳過單位／結束回合，
   仍以待取數與畫面驗證。
   若 Space 不觸發首則正文，另以[GAME 選單的 Retire 候選點擊](../../tools/goal111-retire-menu.inputs.json)
   探查正常玩家是否能返回新局入口；先只觀測與記錄，
   不存檔或覆寫原版，下一輪才決定是否可用於開關後
   重開新局的有界對照。
4. 若首則 help 出現，固定 `GAME.TXT:@TUTORIAL1` 的原始
   bytes／SHA、當次 DOS 讀入、`0D21:00C6` 或實際印字
   常式的 RAM 讀取、原版畫布與正常玩家視窗；關鍵分支
   各做雙冷啟動和無監看控制，再建立獨立正反例。若仍
   未出現，明列各選項狀態、實際動作、停止指令數與
   下一個可驗操作，不把預讀當顯示或聲稱 help 已完成。
5. 回填規格026、`CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md` 與唯一 `docs/worklist.json`，重生
   `WORKLIST.md`。正式 Ebitengine 覆蓋仍須另過
   READY、逐欄字級與安全矩形、同狀態顯示及回退閘門；
   本輪不代選 `@BUILD1` 的38／42px。私有 push 後更新
   並回讀 Issue；收尾核對原版素材未入 Git、檔案 UID/GID、
   root-owned／誤建 `.md` 目錄及 Docker 容器清理。

## 停止線

目標110的1,225M–1,350M畫面抽樣只支持已見選項與輸入，
不能排除中途短暫畫面，也不能當作首則 help 不可達證據。
本輪若只得到選項語意或另一個有效玩家動作，須誠實維持
規格 DRAFT、help 正式顯示零則；後續仍以正常玩家路徑
與 dosgolem 原版收據作權威，不深挖與玩家顯示無關的
硬體逐週期時序。

## 本輪結果與下一個可驗入口

原版設定視窗中，單純移到最後一列再移開，與點文字／
點左側圖示再移開的畫面不同；但那時最後選取列也不同，
整列3,407像素的差分**不足以**證實開關。為排除焦點，
對照分支最終都點回第一列 `Show Indian Moves`。在
1,375M／1,400M的原版320×200索引畫面，兩分支只差
`(73,148)`、`(74,148)`、`(73,149)`、`(74,149)`
四點，皆由色號47變149；1,300M點教學前的完整
樣本相同。兩分支各兩次冷啟動 JSON 逐位元組相同，
無讀寫監看的第三次在全部檢查點的 CPU、完整 RAM、
畫布／索引、色盤、時間、開檔與鍵盤狀態一致。
因此**已證實點擊會切換並保留該列的原版圖示狀態**；
圖示空心／填色如何對應實際「啟用」語意仍只屬
**強推論**，尚無首則教學正文的玩家可見反證或正證。

兩條狀態分支以 ESC 於1,351M離開設定、1,401M送
左方向鍵或原版 `ORDERS` 選單明示的 Space。原版
待取鍵數均由1降至0；ESC 後回到海上畫面，左鍵
可使船移動。Space 分支在1,375M、1,425M及1,500M
的兩側索引畫面完全相同，右側仍顯示1492年春季
與船舶資訊；此為**探索性取樣**，不能證明 Space
已結束整回合或兩側完整 RAM 等價。`0D21:00C6`
觀測序列未見首則正文的「carrying a pioneer」片段，
上述取樣也未見 help 視窗；不能排除其他印字路徑、
檢查點間瞬間或「開關需於新局開始前設定」的可能。
另點 `GAME → Retire` 只取得「Do you really want to
quit? Yes／No」確認視窗；本輪**未**按 Yes，故未證實
能返回新局入口或保留選項狀態。

[獨立檢查器](../../tools/check_goal111_tutorial_state.py) PASS，
[五項正反例](../../tools/test_goal111_tutorial_state.py) PASS；
缺原版回 `SKIP 77`、事件檔版本錯、原始畫面被改與
無監看控制狀態分歧都拒絕。目標111的 Space 探針
使用隔離 dosgolem `internal/dos/scancode.go` 已有的
`0x39/0x20` 鍵值；不帶 Space 的舊探針重播仍與
探索收據逐位元組相同。完整原文、畫面和 RAM
收據只留已忽略的 `workplace/reports/goal111-help/`；
同焦點未點／點擊報告 SHA-256 分別為
`6358700bc50ff2b348ba35ac4971932ef371c63cee88eba3ad81dbee1972444e`／
`4e2735445a2f67aa7f001a6a4614474d06813875ebd291f21eb28c5512888778`。

下一窄任務先證實**開關在新局開始前可否設定／保留**：
若正常介面只能在海上切換，須用原版玩家流程查
`Retire` 確認後是否安全回到新局，或尋找其他正式
新局入口；不得改 RAM／原版設定檔冒充觸發。
同時可從本輪已驗 `Game Options` 畫面，為其標題
及八列動態文字建立來源與逐欄繁中候選，讓玩家
實際會看到的英文繼續減少。這些都需各自後續
goal 與 READY／同狀態驗收；本輪正式 Ebitengine
中文仍十七段、help 命中零則、規格026維持 DRAFT。

## 本機重播入口

掛載、UID/GID與權利邊界依本專案 `AGENTS.md`。將
本工作樹掛 `/repo`、隔離 `workplace/dosgolem` 掛
`/dosgolem:ro`、合法原版 `COLONIZE` 掛 `/game:ro`；
以限資源、無網路的一次性 Docker 建置
`tools/probe_goal098_intro.go`。固定十六筆正常玩家
輸入後帶 `-nation england -next-enter -after-b enter
-after-follow enter -post-caption-audit`，同焦點兩分支
再帶 `-follow-until 1400000000` 和對應的
`goal111-first-row-only.inputs.json`／
`goal111-tutorial-then-first-row.inputs.json`；各跑兩次，
第三次加 `-control`。Space 分支終點為1,500M且
僅為探索性單次收據。獨立檢查器與正反例接受
`--game`、`--inputs`、`--reports`；原版缺失時
檢查器回 `SKIP 77`。
