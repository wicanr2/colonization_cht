# 目標110：從遊戲選項查證首則教學提示的正常玩家觸發

狀態：completed（限定選項與方向鍵證據；首則 help 仍未觸發）；日期：2026-09-24。承接
[目標105](105-first-tutorial-player-path.md)的 `@TUTORIAL1` 預讀、
[目標107](107-post-caption-input-and-help-entry.md)的十張英文字幕與海上
畫面，以及[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)；
對應 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與證據起點

英格蘭正常玩家路徑約1,225M步已顯示可操作的海上介面，
但1,200M、1,225M、1,275M、1,325M四個抽樣沒有首則
教學視窗。`GAME.TXT:@TUTORIAL1` 在88,380,281步被 DOS
讀入 RAM，**不**代表顯示。現在原版 `MENU.TXT` 固定
SHA-256 `5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`
於檔案位移 `0xC6` 有 `Game Options`；原版 `GAME.TXT`
固定 SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`
於 `0x4A8` 有 `@GAMEOPTIONS`，`0x566` 有
`~Tutorial Hints`。這只證實檔案文字；「選項預設關閉」
及「勾選後立刻顯示首則教學」都仍是假說。

本輪不修改原版 EXE、TXT、規則、存檔或正式 Ebitengine
中文層；不代選 `@BUILD1` 的38／42px，也不把這個
教學選項的文字來源冒充實際點擊命中。完整原版畫素、
RAM 和重播 JSON 只留已忽略的 `workplace/`。

## 工作與退出條件

1. 核對 Git 作者、PRIVATE 遠端、Issue、原版與十六筆
   正常玩家輸入 SHA，以及隔離 dosgolem 禁推；
   **先推送本目標文件**，才改探針或執行新重播。
   研究工作只用限資源、無網路、非 root Docker，
   合法原版唯讀。
2. 從已驗1,225M海上畫面，以原版滑鼠移動、按下、
   放開操作頂端 `GAME`，觀測選單；再進 `Game Options`
   讀原版核取狀態。以可重播玩家輸入比較「不改選項」
   與「實際點 Tutorial Hints」分支，先做有界探索；
   不注入 RAM、改設定檔或用猜測座標偽稱點選成功。
3. 若教學顯示，閉合固定 `GAME.TXT:@TUTORIAL1` bytes、
   當次 DOS 讀入、實模式逐字印字、320×200原版畫布與
   玩家可見視窗；對關鍵分支各做兩次冷啟動及無讀寫
   監看控制。若未顯示，明列選項畫面、輸入消費、
   有界停止步數和下一個可驗操作，不把預讀當顯示。
4. 建立獨立檢查與負例，固定原版／探針版本、輸入、
   原始畫面及控制狀態；原版缺失回 `SKIP 77`。
   回填規格026、`CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md` 和 `docs/worklist.json`，重生
   `WORKLIST.md`，私有推送並讀回 Issue。
5. 收尾核對沒有原版素材誤入 Git、研究輸出 UID/GID、
   root-owned／誤建 `.md` 目錄及 Docker 容器殘留。

第一個可重播輸入檔為
[頂端 GAME 選單滑鼠事件](../../tools/goal110-game-menu.inputs.json)；
座標 `(23,3)` 是已驗1,225M畫面上 `GAME` 標題的候選中心，
須由後續原版畫面回證點擊結果，不以座標檔本身當命中證據。
下拉選單確實出現後，第二個
[Game Options 事件檔](../../tools/goal110-game-options.inputs.json)
才在已見第一項內點 `(45,16)`；該座標仍須以新畫面驗證。
第三個[教學提示切換事件檔](../../tools/goal110-toggle-tutorial.inputs.json)
在已見選項視窗最後一列內點 `(140,149)`，仍須由點擊前後
的原版畫面和後續輸出確認效果。
為避免誤把選項切換當作教學觸發，另以
[未進選單、海上直接向西的事件檔](../../tools/goal110-first-west.inputs.json)
送 dosgolem 已驗的左方向鍵；是否移動船或出現教學
仍須由原版重播驗證。

## 停止線

`Tutorial Hints` 是可驗的候選開關，未證實其預設值、
效果或適用於哪一則教學。一次選項視窗、DOS 預讀、
單張畫面或遊戲內其他說明頁，都不能替代
`@TUTORIAL1` 的同狀態印字與畫布證據。即使找到首則
提示，也只增加一則原版顯示命中；24則 help 全文、
逐欄字級、中文安全矩形與正式 Ebitengine 覆蓋仍需
各自的 READY 規格與驗收。

## 本輪結果與下個玩家操作

固定十六筆正常玩家輸入從英格蘭開場到1,225M海上介面，
以三次原版滑鼠事件點頂端 `GAME`，1,250M顯示原版下拉選單；
再點第一列 `Game Options`，1,275M顯示原版設定視窗並另開
`GAME.TXT`。其最後一列確為 `Tutorial Hints`；再點該列，
1,325M原版畫面相對1,300M改變，包含該列核取圖示的原始
索引像素。這些是**已證實的畫面反應**；核取圖示所代表的
預設啟用語意、切換後何時觸發 help 仍**未知**，沒有實際
`@TUTORIAL1` 正文印字與視窗收據。

獨立的未進選單分支於1,226M送左方向鍵；原版待取數先由0
升至1，再於1,226,095,616步前回0；1,250M海上原始索引
畫面相對1,225M已變，1,300M再變。本機畫面可見船舶移動，
兩個後續取樣都未見 help 視窗。這不排除檢查點之間的短暫
畫面，也不能由無視窗推論教學預設為關閉。

上述兩條關鍵分支各有兩次完整冷啟動，JSON逐位元組相同；
無記憶體讀寫監看的第三次控制在全部檢查點的 CPU、完整 RAM、
原版畫布／索引、色盤、虛擬時間、開檔與鍵盤狀態一致。
[獨立檢查器](../../tools/check_goal110_tutorial_hints.py) PASS，
[四項正反例](../../tools/test_goal110_tutorial_hints.py) PASS；
錯事件檔、壞畫面與缺原版 `SKIP` 均有驗證。不帶新旗標的
100M探針 JSON 與既有目標105收據逐位元組相同。
原版畫素和完整收據只留忽略版控的
`workplace/reports/goal110-help/`；選項收據 SHA-256
`56b6bbc19ecbfe46a6b0837fa07d869a69d048ff047d542ec9566efb8a474ca4`，
向西收據 SHA-256
`11a99ec088b3c322bb9f2c035b7cbae2e3ea48d50ee8a80221b76899832e55fb`。

下一窄任務應以已見選項視窗為入口，先確認核取圖示啟用／
停用語意，再以正常玩家操作離開選項視窗並嘗試明確的遊戲
動作（例如結束回合），觀測首則教學的原版逐字印字與畫布；
若仍未命中，只記有界嘗試，不把預讀或任意選單文字冒稱
24則 help 已在畫面顯示。`@BUILD1` 的38／42px字級仍待
使用者另行選擇，不屬本輪決定。

## 本機重播入口

先依專案 `AGENTS.md` 驗證所有掛載來源存在與形態；原版
`COLONIZE` 唯讀掛 `/game`，隔離 `workplace/dosgolem`
唯讀掛 `/dosgolem`，本工作樹掛 `/repo`。使用限資源、
無網路、目前使用者 UID/GID 的一次性 Docker 容器，
從 `/dosgolem` 建置 `tools/probe_goal098_intro.go`；選項
分支帶 `-post-caption-audit -follow-until 1350000000`
及 `-game-inputs /repo/tools/goal110-toggle-tutorial.inputs.json`，
方向鍵分支把終點改為 `1300000000` 並使用
`goal110-first-west.inputs.json`。兩者均沿用十六筆
`goal084-window-full.inputs.json`、`-nation england -next-enter
-after-b enter -after-follow enter`；各重跑兩次，再加
`-control` 作第三次。獨立檢查器與正反例的命令列參數
為 `--game`、`--inputs`、`--reports`；原版缺失回 `SKIP 77`。
