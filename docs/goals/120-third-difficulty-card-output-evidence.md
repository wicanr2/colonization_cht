# 目標120：第三張難度卡片的正常玩家輸出證據

狀態：completed（僅第三張卡片原文來源與畫布）；日期：2026-09-24。承接[規格016](../spec/016-difficulty-card-text-draft.md)、
[目標081](081-second-difficulty-card-output-evidence.md)及[目標119](119-game-options-click-phase.md)；
對應既有 [Issue #6](https://github.com/wicanr2/colonization_cht/issues/6)、
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，不另建同義工作項。

## 玩家問題與本輪界線

難度頁第一、二張卡片各兩行已有正式中文；第三至第五張仍顯示英文。
譯稿現有 `NAMES.TXT:0x00000C22`「征服者」及
`LABELS.TXT:0x000008B8`「普通」候選，但檔案中有這些字串不代表
第三張卡片實際使用這兩個來源。本輪沿正常玩家滑鼠路徑，先確認
第三張卡片的選取、當次原版文字、來源與畫布；不沿用前兩張的
背景、座標或中文字級。第一張國家旗卡 A 版 21／25px 已由目標099
完成，本輪不重做；遊戲選項視窗的 A／B 字級仍是獨立待決事項。

## 工作與退出條件

1. 先把本目標推送至已核對為 PRIVATE 的 `origin/main`。固定合法 DOS
   原版雜湊、隔離 `workplace/dosgolem` 提交與九筆已驗真視窗難度頁
   前綴；原版唯讀、研究收據只留已忽略的 `workplace/`。所有分析、
   編譯、遊戲執行與測試都在限資源、無網路、非 root 的一次性 Docker。
2. 從相同難度頁狀態，以原版滑鼠移入、按下、放開、移開第三張卡片。
   保留未點選及僅移入對照，確認實際命中區與顯示原文；不能靠
   版面推測座標。至少雙次冷啟動和同輸入無監看控制，比對 CPU、
   完整 RAM、索引畫面、原始畫布、色盤、虛擬時間與開檔。
3. 若第三張卡片確有兩行新文字，追查 TXT 原始位移／位元組、DOS
   載入、線性 RAM、原始 `CS:IP`、格式化顯示位元組及印前後畫布；
   量測原文墨跡、安全矩形候選和有紋理底圖。每項結論標示
   `confirmed`、強推論、假說或未知，保留工具版本及位址基準。
4. 建立獨立檢查器及錯版、錯事件、同文異來源、控制狀態分歧等
   負例；不足之處明列。更新規格016、`RESEARCH-LOG.md`、
   `CONTEXT.md`、`WORKLOG.md`、唯一工作清單及既有 Issue，推送
   私有儲存庫並回讀遠端。
5. 收尾核對原版素材、字型與原版畫素未入 Git；檢查輸出擁有權、
   root-owned／誤建 `.md` 目錄、隔離 dosgolem 禁推及 Docker 容器清理。

## 停止線

本輪若來源至畫布、當次背景、游標回退及字級尚未構成 READY 規格，
只保留 DRAFT 與英文畫面；不修改正式 `tools/live_menu.go`、不宣稱
第三張卡片已中文化、不更新正式截圖或十七段計數。不得修改原版
EXE／TXT、遊戲規則、存檔或滑鼠命中區。

## 結果與下一閘門

原版畫面確認第三張卡片位在難度頁左下；正常玩家九筆已驗前綴後，
點擊 `(55,145)` 才印出 `CONQUISTADOR:`／`Moderate`，未點選及僅
移鼠對照沒有第三張卡片印字。`NAMES.TXT:0xC22`／
`LABELS.TXT:0x8B8` 的原始 bytes 經 DOS 載入、執行期來源讀取、
格式化印字緩衝及原版畫布事件核對；同文 `GAME.TXT:0xA3C`
不可借作此卡來源。原版兩行墨跡分別是205點、bbox
`(32,141)–(81,145)` 與116點、bbox `(41,149)–(73,154)`；
印前安全矩形候選各有100／80種底圖色盤索引，不能純色抹除。
詳細位址空間、步數與推論等級見[規格016](../spec/016-difficulty-card-text-draft.md)。

雙次 dosgolem 冷啟動報告逐 byte 一致，無監看控制在原版 CPU、
完整 RAM、索引／底層畫布、色盤、時間、開檔與逐時點底圖一致；
`tools/check_goal120_third.py --self-test` 對真原版收據及六種
破壞性負例均 PASS。已更新兩筆真譯稿來源註記，但「征服者／普通」
仍只是 `draft`。本輪沒有正式中文覆蓋、字級定案或新截圖，正式
顯示仍十七段；下一閘門是第三張卡片逐欄 Ebitengine 預覽與
游標／按鍵／回退證據，再決定是否足以升限定 READY。
